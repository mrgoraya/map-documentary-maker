# The Iran War Explained: How It Started and Where It Stands (2026)

The complete project behind the [6-minute documentary](https://youtu.be/TUuvIw6EoIs) on Think with MG, made with this skill in one night.

| File | What it is |
|---|---|
| `research/brief.md` | timeline, conflicting figures, verified quotes, coordinates, 93 sources, fact-check log |
| `script.md` | the approved script in 4 parts of under 90 s, with sources per beat |
| `voice/part1-4.txt` | the spoken text Kokoro read (`am_michael`) |
| `scene_plan.md` | 78 timed shots and the asset checklist |
| `scenes.py` | the actual animation code for every shot |
| `YOUTUBE.md` | title, description with chapters, sources and credits, tags |
| `fetch_assets.sh` | re-downloads the 12 Commons photos and clips with their credits |

To rebuild it:
```bash
PY=~/.cache/map-documentary-maker/venv/bin/python; SK=../../skills/map-documentary-maker/scripts
bash fetch_assets.sh
$PY $SK/prep_geo.py && $PY $SK/narrate.py all && $PY $SK/align.py all
$PY $SK/render.py part 1   # ... then parts 2-4, then: $PY $SK/render.py full
```
New voice takes can be a little longer or shorter than the original, so check the scene start times against `sentences.json`.

The story is as of 24 November 2026. Facts are attributed in the script; casualty figures are each side's own counts.
