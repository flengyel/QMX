# QMX Windows WSJT-X FT8 Diagnostic Utilities

Windows 11 utilities for running WSJT-X Improved with the QRP Labs QMX+:

1. keep Windows time accurate enough for FT8; and
2. verify the QMX+ USB receive-audio path before launching WSJT-X.

The QMX+ LCD has an audio-level indicator at the top-left character,
under the `A` VFO symbol. A single dot during transmit or tune means
little or no transmit audio drive is reaching the QMX+ over USB. Typical
causes include wrong WSJT-X output device, USB re-enumeration after a
reconnect, FxSound audio routing, or exclusive-mode contention.

`qmx_audio_check.py` measures receive audio (QMX+ -> PC). It does not
test transmit audio directly, but a missing or silent receive device is
evidence that USB enumeration or device selection must be fixed before
debugging WSJT-X transmit audio.

Operating procedure is in [CHECKLIST.md](CHECKLIST.md). Debugging notes
are in [NOTES.md](NOTES.md).

## Scope

Tuned for one specific configuration:

| Component | Version / detail |
| --- | --- |
| OS | Windows 11 |
| Radio | QRP Labs QMX+ |
| QMX+ firmware | 1.03.002 |
| Software | WSJT-X Improved 3.0.0 |
| Antenna | AlexLoop magnetic loop (2nd floor, urban courtyard) |
| Band / mode | 30 m FT8, 10.136 MHz |
| Other audio software present | FxSound |

## Files

| File | Purpose |
| --- | --- |
| `Ensure-FT8-TimeSync.ps1` | Configures and tests the Windows Time service so FT8 timing is usable after a rebuild, reboot, or failed `w32tm /resync`. |
| `qmx_audio_check.py` | Lists Windows audio devices, identifies likely QMX+/USB audio devices, captures a short sample, and reports where its peak level falls on a measurement scale from `SILENT` through `CLIPPING`. |
| `CHECKLIST.md` | Operating checklist for routine WSJT-X + QMX+ operation, including what not to change. |
| `NOTES.md` | Debugging notes and post-commit validation. |

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

Python virtual environment setup (the `.venv/` directory is gitignored;
create it yourself, do not commit it):

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

For FT8, the final offset should be well under +/-1 second.

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
python .\qmx_audio_check.py --device N
python .\qmx_audio_check.py --duration 5
python .\qmx_audio_check.py --samplerate 48000
```

Use `--device N` when several input candidates are listed. Windows can
enumerate the same physical device through multiple audio APIs (MME,
WDM-KS, WASAPI shared/exclusive). Prefer a 48 kHz QMX+ input when
available.

## Audio interpretation

`qmx_audio_check.py` reports peak level, RMS level, and peak dBFS, and
classifies the result by peak dBFS.

| Label | Peak band | What it tends to indicate |
| --- | --- | --- |
| `SILENT` | peak < -100 dBFS | No useful audio reached the capture device. Check USB cable, device selection, Windows privacy settings, and disabled devices. |
| `VERY QUIET` | peak < -60 dBFS | Usually wrong device selected or exclusive-mode contention. Check device selection first. |
| `QUIET` | peak < -40 dBFS | Low in dBFS terms, but may still decode when the Windows clock is synchronized. |
| `NORMAL` | -40 to -15 dBFS | Operating range observed on this station. WSJT-X typically shows 3-4 green dots. |
| `HOT` | > -15 dBFS | High but not clipping. Consider reducing for headroom. |
| `CLIPPING` | peak > -0.3 dBFS | Near full scale. Reduce QMX+ AF output or Windows input level. |

### Level is not the usual culprit

On this station, FT8 decoded normally at about -40 dBFS peak and -55 dBFS
RMS when the Windows clock was synchronized. A 4-second clock offset
produced zero decodes while the audio path still looked plausible.

If WSJT-X decodes nothing while the band is active, check time before
adjusting audio.

On this setup, USB RX audio from the QMX+ behaved as effectively
fixed-gain. No USB RX gain control was found in the firmware 1.03.002
menu during this session; `SSB -> USB Gain` affected TX only. No
adjustment was needed for this station.

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

Do not make the QMX+ the Windows default output device. System audio
processors such as FxSound target the default output; Windows system
sounds can be routed to the QMX+ audio device. Set speakers or
headphones as the default; select the QMX+ explicitly inside WSJT-X.

## Troubleshooting

### PowerShell says the time-sync script cannot run

Use a process-local execution-policy bypass:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then run the script again from the same Administrator PowerShell session.

### The time-sync script says Administrator rights are required

Open PowerShell as Administrator. The script exits if not elevated.

### `w32tm /resync` reports no time data

Run `Ensure-FT8-TimeSync.ps1` from Administrator PowerShell. It configures
manual NTP peers, restarts `w32time`, and forces a resync.

### The audio script lists multiple possible QMX+ devices

Run again with the specific input index:

```powershell
python .\qmx_audio_check.py --device N
```

### QMX+ LCD shows one dot during transmit/tune

QMX+ LCD top-left character, under the `A` VFO symbol, shows a single
dot. On this station, that indicated little or no transmit audio drive
reaching the QMX+ over USB.

Likely causes:

- WSJT-X output is not set to the QMX+ device;
- Windows default output is FxSound or another non-QMX+ device, and
  WSJT-X is configured to `Default`;
- QMX+ re-enumerated to a new device number since WSJT-X last bound to it;
- another application is holding the device in exclusive mode;
- QMX+ USB audio routing changed after a FxSound or Windows update.

Diagnostic sequence:

1. In WSJT-X, `File -> Settings -> Audio`, confirm Output is set
   explicitly to `Digital Audio Interface (... QMX Transceiver)`, not
   `Default`.
2. Run `python .\qmx_audio_check.py` to check the RX side. If the script
   reports `VERY QUIET` or `SILENT`, fix USB enumeration, device
   selection, and routing before returning to WSJT-X.
3. If the script reports `QUIET` or `NORMAL` but the QMX+ still shows
   one dot, treat the WSJT-X output binding or Windows output routing as
   the live suspect.

A `QUIET` result on its own is not a problem when the clock is synchronized.

### The QMX+ device is absent from WSJT-X

Power-cycle or reconnect the QMX+, then restart WSJT-X. Windows may assign
a new device number.

### Windows Settings -> Sound freezes or shows no devices

Known failure mode when the FxSound APO has been unloaded but not cleanly,
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

## Safety

`Ensure-FT8-TimeSync.ps1` changes only Windows Time service
configuration and queries time status.

`qmx_audio_check.py` is read-only. It captures a short in-memory audio
sample to compute level statistics and changes nothing.

## License

MIT License. See [LICENSE](LICENSE).
