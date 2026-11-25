# Output templates

## Research brief (`research/brief.md`)

```
# Research brief: <topic>
As of <date>. <3-5 sentence summary.>

## Timeline
| Date / time | Event | Place (lon, lat) | Key numbers | Sources |
|---|---|---|---|---|
| 28 Feb 2026 | US and Israeli strikes on Iran begin | Tehran (51.39, 35.69) | — | [1][4] |

## Conflicting figures
| Figure | Source A | Source B | Wording in script |
|---|---|---|---|
| Deaths in Iran | 3,400+ (health ministry) [7] | 5,000+ (rights group) [9] | "Iran's health ministry says more than 3,400..." |

## Clipping-worthy quotes (word for word)
1. "<exact sentence>" — <Outlet>, <date>, <URL> [n]

## Places
| Place | lon, lat |

## References
[1] <Outlet>, "<headline>", <date>. <URL>

## Fact-check log
- Script said X; source [n] says Y. Fixed to "...".
```

## Script (`script.md`)

```
# Script: <title> · target <length> · <language> · <voice>

## PART 1: <name> (0:00-1:30, ~215 words)

**Beat 1** (hook)
Narration: "On Saturday, February 28, 2026, American and Israeli jets struck Iran."
Visual: Map zoom from region to Iran; date card 28 FEBRUARY 2026
Sources: [1][4]
```
Put the word count and estimated length per part. The spoken version (numbers as words) goes in `voice/partN.txt`.

## Voice check (from `align.py`)

```
PART 1: 91.80s (part1_v02.wav, 214 words)
  matches the script
PART 3: 87.80s (part3_v01.wav)
  - missing in voice: 'nearly two weeks' (sentence 6) -> re-narrated as part3_v02
```

## Scene plan (`scene_plan.md`)

| # | Start-end | Narration covered | Visual | Type | On-screen text | Asset |
|---|---|---|---|---|---|---|
| 1 | 0.0-3.2 | "On Saturday, February twenty-eighth..." | Zoom from region to Iran, Iran fills teal | Map | 28 FEBRUARY 2026 / SATURDAY | — |
| 2 | 3.2-6.4 | "...American and Israeli jets struck Iran." | Five jet routes into Iranian cities, flashes | Map + route | US + ISRAEL STRIKE IRAN | — |
| 3 | 6.4-11.2 | "Within hours, Iran's Supreme Leader..." | Portrait, name bar | Photo | ALI KHAMENEI | p_khamenei (fallback: name card) |

Type: Map / Route / Clipping / Chart / Counter / Photo / Video / Card / Chapter.

## Asset checklist

```
1. [REQUIRED] Portrait of Ali Khamenei (real photo, credited) - shot 3
   Found: Commons, khamenei.ir, CC BY 4.0 -> assets/p_khamenei.jpg
   Fallback: name card on dark
2. [OPTIONAL] US Navy launch footage, March 2026 - shot 14
   Fallback: map with jet routes
```

## Captions (if asked)

SRT built from the `_words.json` files: one sentence per cue (split long ones at commas), max 2 lines of 42 characters, each cue on screen at least 1 s.
