# Notes

## April 19–20, 2026: debugging session

**Context.** Windows 11 SSD failed Thursday, April 16, 2026. Replaced
with a 1 TB drive and reinstalled Windows. Three days later, nothing
decoded on 30 m FT8.

**Symptoms.** QMX+ LCD showed a single dot in the audio-level indicator
at the top-left character, under the `A` VFO symbol. WSJT-X showed zero
decodes across many 15-second RX windows, and the waterfall looked almost
empty. PSK Reporter showed the station being heard across the continental
US, Canada, the Caribbean, the Azores, the Canary Islands, and Europe.
Transmit worked when WSJT-X audio was routed to the QMX+. Local decoding
did not.

**Audio routing.** FxSound had become involved in the Windows audio stack
during the rebuild, and `Settings -> System -> Sound` was frozen. That
made audio routing a live suspect.

**Audio check.** `qmx_audio_check.py` captured audio from the QMX+ USB
receive-audio device and reported peak/RMS levels. The measured level was
about -40 dBFS peak and -55 dBFS RMS. That level is normal for this
station when the Windows clock is synchronized.

**What did not fix decoding.** Raising the QMX+ AF volume to 50 did not
change the Windows-side level. Windows recording level was already at
100. Disabling FxSound and setting a non-FxSound default output cleaned
up the audio environment but did not restore decodes. No USB RX gain
control was found in the QMX+ firmware 1.03.002 menu during this session;
`SSB -> USB Gain` affected TX only.

**Cause.** System clock was about 4 seconds off. `w32time` was disabled
on this fresh install; the machine had been running on its hardware clock
since the SSD replacement. FT8 requires clock accuracy within about one
second. At a 4-second offset, WSJT-X can have usable audio and still
decode nothing.

**Fix.** Enabled `w32time`, configured NTP peers, and forced a resync.
Offset dropped to tens of milliseconds. Decodes started immediately at
the same QMX+ USB audio level measured before the resync.

— WM2D, April 20, 2026

## April 22, 2026: post-commit validation

One evening session with the tools in routine use produced 34 PSK Reporter
spots on 30 m FT8. Reports included EA8/DL1MDS and EA8BFK in the Canary
Islands at 3447 miles, KE6PQV at 2550 miles, KI6MQX at 2495 miles, KI0E
at 2165 miles, N6RW at 2130 miles, and WP4SZA in Puerto Rico at 1626
miles.

This validated the operating chain: Windows time was usable for FT8,
WSJT-X was bound to the QMX+ audio devices, and the QMX+/AlexLoop station
was being heard beyond North America. PSK Reporter validates transmit;
local WSJT-X decodes validate receive.

— WM2D, April 22, 2026
