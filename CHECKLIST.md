# WSJT-X Improved + QMX+ + AlexLoop — 30 m FT8 Operating Checklist

Quick reference for routine operation. Assumes the environment described in
README.md. Tuned for WM2D's QTH; values marked *(observed at this QTH)* are
specific-installation data, not generalizable specs.

## Startup / after reboot

1. Power on QMX+.
2. Connect QMX+ USB to the same PC USB port as last time. Windows tracks
   USB audio identity partly by port path; moving ports forces re-enumeration.
3. Start Windows.
4. From elevated PowerShell:

   ```powershell
   cd C:\Users\fleng\vscode\QMX
   Set-ExecutionPolicy -Scope Process Bypass
   .\Ensure-FT8-TimeSync.ps1
   ```

   Offset must be well under ±1 s. Near 0.00 s is normal.

5. Open WSJT-X Improved.
6. `File → Settings → Audio`:

   - Input: `Digital Audio Interface (... QMX Transceiver)`
   - Output: `Digital Audio Interface (... QMX Transceiver)`

   Do not use `Default`, `FxSound`, `CintiqPro24P`, or `Scarlett`.

7. Confirm QMX+ is in `DIGI` mode.
8. Confirm frequency `10.136.000 MHz` for 30 m FT8.
9. Tune AlexLoop. SWR ~1.2–1.3 *(observed at this QTH)* is acceptable.
10. Click `Monitor` in WSJT-X.
11. Confirm receive level. 3-4 green dots is the target; WSJT-X dB readout
    ~34 dB *(observed at this QTH)* is known to decode reliably.
12. Wait one full 15-second FT8 cycle. Confirm decodes appear.
13. Press `Tune` for 1–2 seconds. Confirm QMX+ shows a full transmit drive
    line under VFO A. Stop `Tune`.

## Known good end state

- Clock offset near zero
- WSJT-X input: explicit QMX device
- WSJT-X output: explicit QMX device
- QMX+ mode: DIGI
- SWR: ~1.2–1.3 *(observed at this QTH)*
- Receive: WSJT-X decodes present
- Transmit: QMX+ `Tune` shows full line
- CAT/PTT: working

## If decodes stop but receive level looks normal

**Check clock first.** A 4-second offset silently kills all decoding while
leaving the audio path looking fine.

```powershell
w32tm /stripchart /computer:time.windows.com /samples:5 /dataonly
```

If offset exceeds ±1 s, re-run `Ensure-FT8-TimeSync.ps1`. Do not
troubleshoot audio until clock offset is corrected.

## If QMX audio devices disappear from WSJT-X

1. Close WSJT-X.
2. Power off QMX+.
3. Unplug QMX+ USB.
4. Wait 10 seconds.
5. Power on QMX+.
6. Reconnect QMX+ USB to the same PC USB port.
7. Reopen WSJT-X.
8. Recheck `Settings → Audio`.

## If transmit drive drops to one dot / weak line

In order:

1. WSJT-X `Settings → Audio → Output` is the QMX device.
2. Windows `Settings → System → Sound → Volume mixer → WSJT-X` output is
   the QMX device, not FxSound or default.
3. Reset Volume Mixer if WSJT-X app volume is stuck.
4. Ignore a stuck mixer display at `1` if QMX+ `Tune` still shows a full
   transmit line — the display is lying, not the radio.

## If Windows Settings → Sound freezes

Known failure mode with FXSound's APO. Use the legacy control panel, which
takes a different code path:

```powershell
mmsys.cpl
```

The Playback and Recording tabs in that dialog respond normally when the
Settings app won't.

If even `mmsys.cpl` won't commit changes, restart the audio service:

```powershell
Restart-Service -Name Audiosrv -Force
```

## Do not change unless evidence changes

The following settings are known-correct. Changing them without specific
evidence of a problem produces new failure modes without fixing the current
one.

- CAT baud / COM settings
- PTT method
- Windows default input/output devices (will remain Scarlett/Cintiq; WSJT-X
  must use explicit QMX input/output devices regardless of defaults)
- Audio drivers
- WSJT-X reinstall

## Diagnostic command reference

```powershell
# Pre-flight audio check
python .\qmx_audio_check.py

# Explicit device index if multiple QMX candidates appear
python .\qmx_audio_check.py --device 29

# Force clock resync
.\Ensure-FT8-TimeSync.ps1

# Check clock without reconfiguring
w32tm /query /status
w32tm /stripchart /computer:time.windows.com /samples:5 /dataonly

# Legacy sound control panel
mmsys.cpl

# Restart audio service (drops stale APO hooks)
Restart-Service -Name Audiosrv -Force
```
