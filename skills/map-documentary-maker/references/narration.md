# Narration

## Option A: Kokoro (default, free, runs on your computer)

Kokoro-82M is an open-weight text-to-speech model (Apache 2.0). `narrate.py` reads `voice/partN.txt` and writes `voice/partN_vXX.wav`.

Good documentary voices (try two or three with `narrate.py sample "..." --voice <name>`):

| Voice | Sound |
|---|---|
| `am_michael` | calm US male, the default storyteller |
| `am_fenrir` | deeper US male |
| `bm_george`, `bm_fable` | British male |
| `af_heart`, `af_bella` | US female |
| `bf_emma` | British female |

`--speed 0.95` slows the read for heavy topics; set `"voice"` and `"speed"` in `project.json` to keep it for every part.

### Writing text that a TTS reads well

- **Write numbers as words** the way they should be said: "twenty twenty-six", "February twenty-eighth", "three point four billion dollars", "nineteen seventy-six". Digits get read in odd ways ("2026" can become "two thousand twenty-six").
- Write abbreviations as they are spoken: "U.N." or "the United Nations", "U.S.", "I.R.G.C." (letters with dots are spelled out).
- Short sentences. One idea each. Commas are short pauses; a blank line between paragraphs is a longer pause (0.35 s).
- Attribution in the sentence, not in brackets: "Iran says forty sailors died", not "forty sailors died (Iran)".
- Names that may be mispronounced: test them in a sample first, and respell if needed ("Khamenei" is fine; for others, try a phonetic spelling).

The `script.md` keeps normal written numbers for readers; `voice/partN.txt` is the spoken version.

## Option B: your own voice

Record one file per part (quiet room, phone or USB mic, 30 cm from the mouth). Save as `voice/partN_v01.wav` (convert with `ffmpeg -i in.m4a -ar 48000 voice/part1_v01.wav`). Read the approved text. Then run `align.py` like with Kokoro.

## Checking a take (`align.py`)

`align.py` transcribes with faster-whisper (`large-v3-turbo` by default), times every word, and compares with the script. Numbers count as equal in any form. Read the report:
- **missing in voice:** a skipped line. Re-narrate that part (Kokoro) or re-record it.
- **changed:** usually harmless (Whisper spelling a name differently). Listen before acting.
- **extra in voice** in a quiet stretch at the end or between paragraphs: Whisper can invent words in silence. Check the loudness there (`ffmpeg -ss <s> -t 1 -i take.wav -af volumedetect -f null -`); if it's silence, ignore it.

A new take never overwrites the old one. Pin a specific take in `project.json`: `"voice_takes": {"2": "part2_v01.wav"}`.
