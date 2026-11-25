# Demo: why the Strait of Hormuz matters (26 s)

A short project that uses every kind of shot the kit has, so you can see and copy each one:

| Time | Shot | Kit |
|---|---|---|
| 0.0 | Globe spins and dives into the Gulf; the title types on word by word with the voice | `globescene`, `kinetic` + `voice_words` |
| 3.2 | Labelled map of the strait, tankers moving in both lanes | `mapscene`, `label`, `pin`, `traffic` |
| 5.3 | Real U.S. Navy footage of a tanker in the strait (2023, credited), numbers typed on the words | `videoscene(crop=...)`, `kinetic` |
| 7.9 | Close-up: live tanker traffic + counter 20.7 | `traffic`, `counter(decimals=1)` |
| 10.5 | "One fifth" word by word + 1-in-5 bars | `cardscene`, `kinetic` |
| 15.0 | The EIA sentence on a clipping, highlight draws on | `clipping` |
| 19.8 | Bypass pipelines draw on; closing line typed on | `route`, `kinetic` |

All facts are from the U.S. Energy Information Administration: see `research/brief.md`, including the fact-check that corrected the first draft.

```bash
PY=~/.cache/map-documentary-maker/venv/bin/python; SK=../../skills/map-documentary-maker/scripts
$PY $SK/fetch_commons.py get "File:Oil tanker Niovi seized by Iran's Islamic Revolutionary Guard Corps Navy.webm" v_niovi
$PY $SK/prep_geo.py && $PY $SK/narrate.py all && $PY $SK/align.py all
$PY $SK/render.py stills 1 1.5,4.5,6.5,9,13,17,24     # quick look
$PY $SK/render.py part 1                               # -> out/part1_v01.mp4
```
If your voice take's timing differs, adjust the start times in `scenes.py` from `sentences.json` (the kinetic words follow the voice automatically).
