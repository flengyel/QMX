# Notes

## April 19–20, 2026: the debugging session that produced this repo

**Context.** My Windows 11 SSD failed on Thursday, April 16, 2026. I
replaced it with a 1 TB backward-compatible drive and reinstalled Windows
from scratch. Three days later I sat down to get the QMX+ back on 30 m
FT8 and spent several hours discovering why nothing was decoding.

**Symptoms.** WSJT-X Improved 3.0.0 showed a single dot under the VFO A
audio level indicator. Zero decodes across many 15-second RX windows. The
waterfall looked almost empty. Meanwhile, PSK Reporter showed me being
heard across the continental US, into Canada, the Dominican Republic,
Puerto Rico, the Azores, Canary Islands, France, the UK, Germany, Spain,
Switzerland, and Slovakia. Transmit path was clearly fine. Receive path
was failing silently.

**First hypothesis: audio routing.** FXSound had installed itself as the
default Windows input and output during the rebuild. `Settings → System →
Sound` was frozen. The QMX+'s USB audio was getting grabbed or attenuated
by something in the stack. This was the wrong hypothesis but it looked
right: all the evidence pointed to an audio routing problem.

**Diagnostic script.** I wrote `qmx_audio_check.py` to capture a few
seconds from the QMX+ directly and report peak/RMS levels. The script
confirmed what looked like a low-level condition: peak around −40 dBFS,
RMS around −55 dBFS. The script's classification — "Low. WSJT-X would
show 1-2 dots. Raise level." — matched the symptom.

**What didn't work.** Raising the QMX+'s AF volume to 50 didn't change
the Windows-side level. Windows recording level was already at 100.
Disabling FXSound and setting a non-FXSound default output helped for
correctness but didn't change decoding. The QMX+'s current firmware
(1.03.002) does not expose a USB RX audio gain control in any menu I
could find; `SSB → USB Gain` governs TX only.

**The actual problem.** After about an hour of chasing audio level, I
thought to check the system clock. It was 4 seconds off.
`w32time` was disabled. On a fresh Windows 11 install the Windows Time
service is not started automatically, and my machine had been trusting
its hardware clock without NTP sync since the SSD replacement. FT8
requires clock accuracy within ±1 second; at 4 seconds off, the decoder
starts looking at audio roughly 27% into each transmission and misses
the sync tones entirely.

**The fix.** Enable `w32time`, configure NTP peers, force a resync.
Offset dropped to ~13 ms. Decodes started immediately — at the same
"Low" audio level the diagnostic script had been flagging. Within an
hour I had F5SPJ (France, 3981 mi) and NQ6B (California, 2398 mi) in the
same 30-second window. The audio path had been adequate the whole time.

**Lessons encoded in this repo.**

1. For FT8, clock offset dominates audio level as a failure mode. A
   modest low level still decodes; a 4-second clock offset decodes
   nothing. `qmx_audio_check.py` now says this explicitly on every run.

2. Windows `w32time` is not reliably enabled on fresh installs. Any
   machine rebuilt for digital-mode operation needs its time service
   configured explicitly. `Ensure-FT8-TimeSync.ps1` handles this.

3. Diagnostic tools must acknowledge what they cannot check. The audio
   script measures audio and cannot measure clock offset. Saying so in
   the output prevents the next operator (possibly me) from being led
   down the same wrong path.

4. FXSound and the Windows audio stack are a real problem on this
   machine but they were not the cause of the decode failure. Worth
   documenting — hence the `mmsys.cpl` notes in the checklist — but
   worth separating from the primary lesson.

5. The "Do not change unless evidence changes" section in the checklist
   is the part future-me will most benefit from. All of the settings
   listed there were considered and ruled out during this session. The
   cost of rediscovering that they are not the problem is high.

**What this repo is not.** It is not a general diagnostic toolkit. It is
the residue of one debugging session, preserved so that the next time a
Windows rebuild happens — or the next time decodes fail for reasons I
cannot immediately see — I do not have to reconstruct the lessons from
scratch.

— WM2D, April 20, 2026
