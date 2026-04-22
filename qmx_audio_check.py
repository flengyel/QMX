"""
qmx_audio_check.py - Pre-flight diagnostic for the QMX+ audio chain on Windows.

Purpose
-------
Answer "is my audio path working right now?" deterministically, before
launching WSJT-X and discovering the answer via the one-dot indicator.

Usage
-----
    pip install sounddevice numpy
    python qmx_audio_check.py                      # auto-detect, 3s capture
    python qmx_audio_check.py --pattern QMX        # different name match
    python qmx_audio_check.py --device 7           # specific device index
    python qmx_audio_check.py --duration 5         # longer capture

The script is read-only. It does not change Windows defaults, device
bindings, or anything else. Diagnosis is the intervention.

Important: low audio level alone does NOT explain FT8 decode failure.
A 4-second Windows clock offset will silently prevent all decodes while
the audio path looks fine. If WSJT-X decodes nothing, check time first
with Ensure-FT8-TimeSync.ps1 before chasing audio levels.
"""

import argparse
import sys

import numpy as np
import sounddevice as sd

# Substrings that identify a QMX+ or similar radio device in Windows.
# 'digital audio interface' is how the QMX+ enumerates on observed systems;
# the others are historical or cover related QRP Labs radios.
RADIO_HINTS = (
    'digital audio interface',
    'usb audio codec',
    'qmx',
    'qdx',
)


def list_devices(pattern):
    devices = sd.query_devices()
    print(f"\n{'Idx':<4} {'I/O':<7} {'Ch(i/o)':<9} {'SR':<7} Name")
    print("-" * 72)
    input_candidates = []
    pattern_l = pattern.lower() if pattern is not None else ''
    match_all = pattern == ''
    for idx, d in enumerate(devices): 
        io = []
        if d['max_input_channels'] > 0:
            io.append('in')
        if d['max_output_channels'] > 0:
            io.append('out')
        io_s = '/'.join(io)
        ch = f"{d['max_input_channels']}/{d['max_output_channels']}"
        sr = f"{int(d['default_samplerate'])}"
        marker = ''
        name_l = d['name'].lower()
        # Match every device when the user passes --pattern '', otherwise
        # match the user-supplied pattern or any known radio hint. The hint
        # list means the default case finds the QMX+ without requiring
        # --pattern.
        matches = (
            match_all
            or (pattern_l and pattern_l in name_l)
            or any(h in name_l for h in RADIO_HINTS)
        )
        if matches:
            if d['max_input_channels'] > 0:
                marker = '  <-- input candidate'
                input_candidates.append(idx)
            else:
                marker = '  <-- output match'
        print(f"{idx:<4} {io_s:<7} {ch:<9} {sr:<7} {d['name']}{marker}")
    return input_candidates


def check_default_devices():
    print()
    try:
        di = sd.query_devices(kind='input')
        do = sd.query_devices(kind='output')
        print(f"Windows default input:  {di['name']}")
        print(f"Windows default output: {do['name']}")
        if any(h in do['name'].lower() for h in RADIO_HINTS):
            print()
            print("  WARNING: default OUTPUT looks like a radio device.")
            print("  FXSound and other system audio processors target the")
            print("  default output. Set speakers/headphones as default in")
            print("  Windows Sound settings; WSJT-X will still find the")
            print("  radio by explicit device selection.")
        if any(h in di['name'].lower() for h in RADIO_HINTS):
            print()
            print("  Note: default INPUT is a radio device. Harmless for")
            print("  WSJT-X if explicitly selected, but any app that grabs")
            print("  the default input (Teams, browser, voice assistants)")
            print("  will contend for it.")
    except Exception as e:
        print(f"Could not query default devices: {e}")


def test_capture(device_idx, duration, samplerate):
    d = sd.query_devices(device_idx)
    print()
    print(f"Capturing {duration}s from device {device_idx}: {d['name']}")
    dev_sr = int(d['default_samplerate'])
    if samplerate != dev_sr:
        print(f"Requested {samplerate} Hz, device default {dev_sr} Hz "
              f"(WSJT-X expects 48000).")

    try:
        audio = sd.rec(
            int(duration * samplerate),
            samplerate=samplerate,
            channels=1,
            device=device_idx,
            dtype='float32',
        )
        sd.wait()
    except Exception as e:
        print(f"  CAPTURE FAILED: {e}")
        print("  Causes: device in use by another app (exclusive mode),")
        print("  device disappeared between enumeration and capture,")
        print("  sample rate not supported.")
        return

    audio = audio.flatten()
    peak = float(np.max(np.abs(audio)))
    rms = float(np.sqrt(np.mean(audio ** 2)))
    peak_db = 20 * np.log10(peak) if peak > 0 else float('-inf')
    rms_db = 20 * np.log10(rms) if rms > 0 else float('-inf')

    print(f"  Peak: {peak:.5f}  ({peak_db:+.1f} dBFS)")
    print(f"  RMS:  {rms:.5f}  ({rms_db:+.1f} dBFS)")

    # DC offset check — occasionally reveals a broken audio path
    dc = float(np.mean(audio))
    if abs(dc) > 0.01:
        print(f"  DC offset: {dc:+.4f} (unusual; possible driver issue)")

    # Classification. Labels describe the measurement, not a judgment about
    # operational fitness, because WSJT-X decodes reliably at absolute audio
    # levels the dBFS scale would call low. The accompanying notes explain
    # what each band tends to indicate; the operator interprets in context.
    # Bands are on peak dBFS so the thresholds match the meter WSJT-X users
    # intuitively compare against.
    print("\n  Interpretation:")
    if peak < 1e-5:
        print(f"    SILENT (peak {peak_db:+.1f} dBFS).")
        print("    No audio reaching the decoder. Path is broken.")
        print("    Check: USB cable, radio AF output, Windows privacy")
        print("    settings (microphone access), device not disabled.")
    elif peak < 1e-3:
        print(f"    VERY QUIET (peak {peak_db:+.1f} dBFS).")
        print("    Usually indicates wrong device selected, or another")
        print("    process holding the device in exclusive mode. Check")
        print("    device selection before anything else.")
    elif peak > 0.97:
        print(f"    CLIPPING (peak {peak_db:+.1f} dBFS).")
        print("    Reduce radio AF output or Windows input level. FT8")
        print("    decoder tolerates some clipping but prefers headroom.")
    elif peak < 1e-2:
        # Roughly -40 dBFS peak. Observed to decode FT8 reliably on this
        # setup once the Windows clock was synced.
        print(f"    QUIET (peak {peak_db:+.1f} dBFS, RMS {rms_db:+.1f} dBFS).")
        print("    Low in absolute dBFS terms, but this level has been")
        print("    observed to decode FT8 reliably when the Windows clock")
        print("    is synchronized. The QMX+ may not expose an independent")
        print("    USB RX gain on current firmware, so this may simply be")
        print("    the level your radio provides. Windows input-level")
        print("    adjustment may raise it; Windows-internal processing")
        print("    cannot. If decodes fail, check clock offset FIRST.")
    elif peak < 0.178:  # ~ -15 dBFS peak
        print(f"    NORMAL (peak {peak_db:+.1f} dBFS, RMS {rms_db:+.1f} dBFS).")
        print("    Comfortable operating range. WSJT-X typically shows 3-4")
        print("    green dots at this level.")
    else:
        print(f"    HOT (peak {peak_db:+.1f} dBFS, RMS {rms_db:+.1f} dBFS).")
        print("    High but not clipping. Consider reducing for headroom,")
        print("    especially if you see occasional clipping on peaks.")

    # Diagnostic reminder the script itself cannot check.
    print()
    print("  NOTE: if WSJT-X shows no decodes despite an active band, the")
    print("  most common cause is a Windows clock offset, not audio level.")
    print("  Run Ensure-FT8-TimeSync.ps1 and confirm offset is under 1 sec.")


def main():
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument(
        '--pattern', default='Digital Audio Interface',
        help="name substring to match (default matches observed QMX+ naming; "
             "try 'QMX', 'USB', 'CODEC' if your device enumerates differently)",
    )
    ap.add_argument('--duration', type=float, default=3.0)
    ap.add_argument('--samplerate', type=int, default=48000,
                    help='48000 matches WSJT-X')
    ap.add_argument('--device', type=int, default=None,
                    help='skip auto-detect, test this device index')
    args = ap.parse_args()

    print("QMX+ audio-chain diagnostic")
    candidates = list_devices(args.pattern)
    check_default_devices()

    if args.device is not None:
        test_capture(args.device, args.duration, args.samplerate)
        return

    if len(candidates) == 1:
        test_capture(candidates[0], args.duration, args.samplerate)
    elif len(candidates) > 1:
        print(f"\nMultiple input candidates matched: {candidates}. "
              f"Re-run with --device N to test one specifically.")
        print("Windows enumerates the same physical device through multiple")
        print("audio APIs (MME, WDM-KS, WASAPI); any of them should work.")
        print("Prefer the 48000 Hz instance to match WSJT-X natively.")
    else:
        print(f"\nNo input device matched pattern '{args.pattern}' "
              f"or known radio hints {RADIO_HINTS}.")
        print("Try --pattern with a substring from the device list above,")
        print("or --pattern '' to match every device.")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
