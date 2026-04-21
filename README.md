# QMX Windows WSJT-X FT8 Diagnostic Utilities

Small Windows 11 utilities for running WSJT-X Improved with the QRP Labs QMX+.

The project has two diagnostic and utility scripts:

1. keep Windows time accurate enough for FT8; and
2. verify the QMX+ USB audio path before launching WSJT-X.

Operating procedure is documented separately in [CHECKLIST.md](CHECKLIST.md).

## Files

| File | Purpose |
| --- | --- |
| `Ensure-FT8-TimeSync.ps1` | Configures and tests the Windows Time service so FT8 timing is usable after a rebuild, reboot, or failed `w32tm /resync`. |
| `qmx_audio_check.py` | Lists Windows audio devices, identifies likely QMX+/USB audio devices, captures a short sample, and reports whether WSJT-X is likely to see silence, the one-dot condition, low audio, good audio, or clipping. |
| `CHECKLIST.md` | Operating checklist for routine WSJT-X + QMX+ operation, including what not to change. |

## Requirements

### Windows time utility

- Windows 11
- PowerShell
- Administrator PowerShell session
- Network access to public NTP servers

### QMX+ audio diagnostic

- Windows 11
- Python 3
- QRP Labs QMX+ connected by USB
- Python packages:

```powershell
pip install sounddevice numpy
```

Python virtual environment setup:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install sounddevice numpy
```

All commands below assume PowerShell is open at the repository root.

## Usage

### 1. Synchronize Windows time for FT8

Open PowerShell as Administrator at the repository root, then run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\Ensure-FT8-TimeSync.ps1
```

The script:

- requires Administrator privileges;
- sets the Windows Time service to automatic startup;
- starts `w32time` if it is not already running;
- configures manual NTP peers:
  - `time.windows.com`
  - `time.nist.gov`
  - `pool.ntp.org`
- restarts the Windows Time service;
- forces a resync;
- prints `w32tm /query /status`; and
- runs a short stripchart check against `time.windows.com`.

For FT8, the final offset should be well under ±1 second.

### 2. Check the QMX+ receive-audio path

Run from a normal PowerShell session at the repository root:

```powershell
.\.venv\Scripts\Activate.ps1
python .\qmx_audio_check.py
```

Default behavior:

- searches for audio devices whose name matches known radio hints
  (`Digital Audio Interface`, `USB Audio Codec`, `QMX`, `QDX`) or a
  user-supplied `--pattern`;
- lists input and output devices;
- marks likely input candidates;
- prints the Windows default input and output;
- warns if the default Windows output appears to be a radio device; and
- captures 3 seconds of mono audio at 48 kHz from the detected input device.

Useful variants:

```powershell
python .\qmx_audio_check.py --pattern QMX
python .\qmx_audio_check.py --pattern USB
python .\qmx_audio_check.py --device 29
python .\qmx_audio_check.py --duration 5
python .\qmx_audio_check.py --samplerate 48000
```

Use `--device N` when several input candidates are listed. Windows
enumerates the same physical device through multiple audio APIs (MME,
WDM-KS, WASAPI shared/exclusive); all of them capture the same audio.
Prefer the 48 kHz WASAPI instance to match WSJT-X natively.

## Audio interpretation

`qmx_audio_check.py` reports peak level, RMS level, and RMS dBFS. It then
classifies the result.

| Result | RMS band | Meaning | Action |
| --- | --- | --- | --- |
| `SILENT` | peak < -100 dBFS | No usable audio reached the decoder. | Check USB cable, QMX+ AF output, Windows privacy settings, device disabled. |
| `ONE-DOT CONDITION` | peak < -60 dBFS | Signal present but below useful threshold. | Check wrong device selection, exclusive-mode contention, low QMX+ AF output. |
| `Low` | RMS < -50 dBFS | WSJT-X may show 1-2 dots. | Usually decodes if clock is synced. Check time before level. |
| `Marginal` | -50 to -35 dBFS | Decodes likely. | Raise if convenient; not required. |
| `Good` | -35 to -15 dBFS | WSJT-X should show 3-4 green dots. | Proceed. |
| `Hot` | > -15 dBFS | High but not clipping. | Consider reducing for headroom. |
| `CLIPPING` | peak > -0.3 dBFS | Near full scale. | Reduce QMX+ AF output or Windows input level. |

### Important: level is not the usual culprit

Empirically, FT8 decodes reliably at RMS ≈ −55 dBFS *when the Windows clock
is within ±1 s of true time*. A 4-second clock offset produces zero decodes
regardless of audio level. **If WSJT-X decodes nothing while the band is
clearly active, run `Ensure-FT8-TimeSync.ps1` before investigating audio.**

On this QMX+ and current firmware, USB RX audio behaved as effectively
fixed-gain: decode success depended more on clock offset and device
selection than on Windows input-level adjustment. The QMX+ menu items
examined (including `SSB → USB Gain`, which governs TX only) did not
expose an independent USB RX gain control. If the level seems low and
you cannot raise it from the radio, raise the Windows input level via
`mmsys.cpl → Recording → QMX → Properties → Levels`, or accept the low
level — FT8 will usually decode anyway, provided the clock is synced.

## WSJT-X workflow

See [CHECKLIST.md](CHECKLIST.md) for the full operating procedure. In brief:

1. Connect and power the QMX+.
2. Run `Ensure-FT8-TimeSync.ps1` after rebuilds, reboots, or failed syncs.
3. Run `qmx_audio_check.py` before launching WSJT-X.
4. In WSJT-X, explicitly select the QMX+ audio devices rather than relying
   on Windows defaults.
5. If QMX+ audio devices disappear from WSJT-X, power-cycle or reconnect
   the QMX+ and restart WSJT-X.

Typical WSJT-X audio-device names on Windows look like:

```text
Digital Audio Interface (N- QMX Transceiver)
```

The `N` can change after USB reconnects. Recheck WSJT-X audio settings
when Windows renumbers the device.

## Windows default audio warning

The QMX+ should normally not be the Windows default output device. System
audio processors such as FxSound target the default output. If the radio
becomes the default Windows output, ordinary system audio can be routed
toward the radio audio path.

Set speakers or headphones as the Windows default output. Then configure
WSJT-X to use the QMX+ explicitly inside WSJT-X.

## Troubleshooting

### PowerShell says the time-sync script cannot run

Use a process-local execution-policy bypass:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then run the script again from the same Administrator PowerShell session.

### The time-sync script says Administrator rights are required

Open PowerShell as Administrator. The script intentionally exits if not
elevated.

### `w32tm /resync` reports no time data

Run `Ensure-FT8-TimeSync.ps1` from Administrator PowerShell. It configures
manual NTP peers, restarts `w32time`, and forces a resync.

### The audio script lists multiple possible QMX+ devices

Run again with the specific input index:

```powershell
python .\qmx_audio_check.py --device N
```

### The audio script reports the one-dot condition

The input is not fully dead, but it is below useful level. Most likely
causes:

- wrong input device;
- another application holding the device in exclusive mode;
- QMX+ AF output too low; or
- stale device numbering after USB reconnect.

### The QMX+ device is absent from WSJT-X

Power-cycle or reconnect the QMX+, then restart WSJT-X. Windows may assign
a new device number.

### Windows Settings → Sound freezes or shows no devices

Known failure mode when the FXSound APO has been unloaded but not cleanly,
or when the audio stack is in an inconsistent state. Use the legacy
control panel, which bypasses the Settings app entirely:

```powershell
mmsys.cpl
```

The Playback and Recording tabs in that dialog respond normally when the
Settings app won't.

If `mmsys.cpl` also fails to commit changes, restart the audio service
from an elevated PowerShell session:

```powershell
Restart-Service -Name Audiosrv -Force
```

This forces the audio stack to re-initialize and drops stale APO hooks.
Any app currently using audio will briefly lose its connection and
reconnect.

## Scope and safety

`Ensure-FT8-TimeSync.ps1` changes only Windows Time service configuration
and queries time status.

`qmx_audio_check.py` is read-only. It does not change Windows defaults,
WSJT-X settings, device bindings, or QMX+ settings. It captures a short
in-memory audio sample only to compute level statistics.

## Repository notes

This repository is intended as a Windows 11 operating aid for QMX+ FT8
operation. It is especially useful after rebuilding a Windows machine,
reconnecting USB audio devices, or diagnosing WSJT-X receive-audio
failures.

## License

MIT License. See [LICENSE](LICENSE).
