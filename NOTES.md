# Notes

## April 19–20, 2026: the debugging session that produced this repo

**Context.** Windows 11 SSD failed Thursday, April 16, 2026. Replaced
with a 1 TB drive and reinstalled Windows. Three days later, nothing
decoded on 30 m FT8.

**Symptoms.** QMX+ LCD showed a single dot in the audio-level
indicator at the top-left character, under the 'A' VFO symbol — the
one-dot condition. Zero decodes across many 15-second RX windows. The
waterfall looked almost empty. PSK Reporter showed me being heard
across the continental US, into Canada, the Dominican Republic,
Puerto Rico, the Azores, Canary Islands, France, the UK, Germany, Spain,
Switzerland, and Slovakia. Transmit path was fine when I could get WSJT-X
audio routed to the QMX+. Receive was failing silently.

**First hypothesis: audio routing.** FXSound had installed itself as the
default Windows input and output during the rebuild. `Settings → System →
Sound` was frozen. Wrong hypothesis, but the evidence pointed to audio
routing.

**Diagnostic script.** Wrote `qmx_audio_check.py` to capture a few
seconds from the QMX+ and report peak/RMS levels. Peak around −40 dBFS,
RMS around −55 dBFS. The script flagged this as low, matching the
symptom.

**What didn't work.** Raising the QMX+ AF volume to 50 didn't change
the Windows-side level. Windows recording level was already at 100.
Disabling FXSound and setting a non-FXSound default output helped for
correctness but didn't change decoding. No USB RX gain control was
found in the QMX+ firmware 1.03.002 menu during this session;
`SSB → USB Gain` affected TX only.

**The actual problem.** System clock was 4 seconds off. `w32time` was
disabled on this fresh install; the machine had been running on its
hardware clock since the SSD replacement. FT8 requires clock accuracy
within ±1 second. At 4 seconds off, the decoder misses the sync tones
entirely.

**The fix.** Enable `w32time`, configure NTP peers, force a resync.
Offset dropped to ~13 ms. Decodes started immediately at the same
audio level the diagnostic script had been flagging. Within an hour I
had F5SPJ (France, 3981 mi) and NQ6B (California, 2398 mi) in the same
30-second window.

— WM2D, April 20, 2026

## April 22, 2026: post-commit validation

One evening session with the tools in routine use. PSK Reporter logged
26 unique receivers on 30 m FT8, including EA8/DL1MDS and EA8BFK in the
Canary Islands (3447 miles) spotted in the same 30-second window as
western-US receivers above 2000 miles. Transatlantic and
transcontinental paths open simultaneously on 5 W into an AlexLoop from
a second-floor courtyard.

— WM2D, April 22, 2026


