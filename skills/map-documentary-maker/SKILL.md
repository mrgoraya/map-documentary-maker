---
name: map-documentary-maker
description: Makes animated, presenter-free documentary explainer videos (dark relief maps, moving jets and ships, date cards, highlighted news clippings, honest charts, real free-licence photos) end to end on your own computer for $0 - brief, cited research with an independent fact-check, script, AI narration with Kokoro (or your own voice), word-level timing with Whisper, scene plan, Python + ffmpeg animation, QA, thumbnail and upload pack. Use when the user wants a documentary-style, history, war, geopolitics or news explainer, a map-animation video, or says "start a documentary video".
---

# Map Documentary Maker

Produce a map-animated documentary explainer like the ones on modern geopolitics channels: no presenter, a calm narrator, dark relief maps, routes that draw on with jets and ships moving along them, big date cards, highlighted news clippings, charts and real photos. Everything runs locally and free: research on the web, Kokoro for the voice, Whisper for timing, Python + ffmpeg for the picture.

## The pipeline at a glance

| Stage | You make | Tool | Wait for the user? |
|---|---|---|---|
| 0. Setup (first time) | Python env, fonts, map data | `scripts/setup.sh` | no |
| 1. Brief | topic, length, voice, style choices | chat | **yes** |
| 2. Research | `research/brief.md` with sources | web search + fact-check subagent | no (continue) |
| 3. Script | `script.md` + `voice/partN.txt` | chat | **yes, approval** |
| 4. Voice | `voice/partN_vXX.wav` + timings | `narrate.py`, `align.py` | only if the voice differs from the script |
| 5. Scene plan + assets | `scene_plan.md`, `assets/` | `fetch_commons.py` | **yes** |
| 6. Animation | `out/partN_vXX.mp4` | `prep_geo.py`, `scenes.py`, `render.py` | **yes, after each part** |
| 7. Thumbnail + upload pack | `out/thumbnail_vXX.png`, `YOUTUBE.md` | `thumbnail.py` | **yes** |

## Core rules

- Work stage by stage. Where the table says wait, **stop and wait** for the user. Never animate before the script and scene plan are approved.
- **Truth first.** Every fact on screen and in the narration must come from the research, backed by two independent sources or clearly marked as one side's claim ("Iran says...", "according to the Pentagon"). Never invent facts, quotes, numbers, maps, or images of real people. Conflicting figures are shown as conflicting.
- **Charts plot only sourced points.** No smoothed lines or invented values between them: a gap is a dashed line labelled "values in between not shown" (`line_chart` does this).
- **Don't colour a map for non-regional results** (elections, polls): a coloured map implies a regional split. Use `split_bar`.
- **The voice is the clock.** Scenes are timed from the voice's word timestamps, never the other way round.
- **Never overwrite or delete.** Every voice, render and thumbnail gets the next version (`_v01`, `_v02` ...). The scripts do this for you.
- **Nothing gets published** (uploaded, posted, sent) without the user's explicit go-ahead.
- Keep chat short. Long things (research, script, shot list) go in files; tell the user the file name.
- If something is impossible here, say so and offer the closest alternative.

Paths below: `$SK` is this skill's `scripts/` folder (the skill's base directory + `/scripts`), `$PY` is `~/.cache/map-documentary-maker/venv/bin/python`, and commands run **inside the project folder**.

---

## Stage 0: Setup (first time only)

If `$PY` does not exist, run `bash $SK/setup.sh` (about 2.5 GB including the voice and speech models, 5-15 minutes; run it in the background). It needs ffmpeg; if ffmpeg is missing, tell the user the one install command for their OS. Use `--no-voice` if the user will record their own voice and has timestamps.

## Stage 1: Brief

Ask in **one** short message, with defaults so the user can just say "defaults":
1. Topic (and the angle: "how it started", "where it stands", "what happened on day X")
2. Length (default 6 min; parts are at most 90 s each)
3. Narration language (default English) and voice: **Kokoro AI voice** (default `am_michael`; the user can hear samples) or **their own recording**
4. Shape: 16:9 YouTube (default) or 9:16 Shorts/Reels
5. Thumbnail and upload pack? (default yes)
6. Extras: burned-in captions (default no), music bed (default none: the voice + soft whooshes only), channel name for the end card

Then create the project: `$PY $SK/new_project.py <folder> "<title>" --bbox lon0 lat0 lon1 lat1` (the bbox must cover the widest shot in the film, not just the places: a zoomed-out camera past its edge shows empty map). Wait.

## Stage 2: Research (with citations)

Research with web search, favouring wire services, official records, the UN, and reputable outlets; note each source's date. Write `research/brief.md` (format in `references/templates.md`):
- a timeline with dates, times, places, numbers and names, each with citation numbers
- conflicting figures flagged, never silently resolved
- 4-8 **clipping-worthy** sentences, quoted exactly, with outlet, date and URL (for on-screen clippings)
- coordinates (lon, lat) for every place the maps will show
- a reference list with URLs

Then run an **independent fact-check**: give a separate subagent the brief (not your conclusions) and ask it to open the sources and confirm or refute every number, date, name and quote. Fix what it finds and log it at the end of the brief. Full method: `references/research_and_factcheck.md`. Continue to Stage 3 unless the topic needs narrowing.

## Stage 3: Script

Write narration sized to the length: about 140-150 spoken words per minute for English (Kokoro at speed 1.0 is about 150). Split into parts of at most 90 s. Format: numbered beats with **Narration**, **Visual** (map / route / clipping / chart / photo / video / card) and **Sources**. Style: hook within 5 seconds, short sentences, concrete dates and numbers, attribution words for claims, each part ending on a cliffhanger or a clear takeaway.

Save it as `script.md`, and save the narration of each part, as it should be **spoken**, in `voice/partN.txt` (years and numbers written as words: "twenty twenty-six", "February twenty-eighth"; see `references/narration.md`). Ask the user to approve or edit. Wait.

## Stage 4: Voice, and checking it

**Kokoro (default):** offer a 10-second sample first if the user hasn't picked a voice: `$PY $SK/narrate.py sample "One sentence from the script." --voice am_michael`. Then `$PY $SK/narrate.py all`.
**Own recording:** ask for one WAV/MP3 per part, saved as `voice/partN_v01.wav` (convert with ffmpeg if needed).

Then always run `$PY $SK/align.py all`. It writes word timings and `sentences.json`, prints each part's exact length, and lists words the voice skipped, changed or added. Before re-recording over an "extra" word near a pause, check that stretch's loudness: Whisper sometimes hears words in silence. If a real line is wrong, fix `voice/partN.txt` and narrate that part again (it becomes the next take). Pause only if there are real differences to resolve; otherwise continue.

## Stage 5: Scene plan and assets

Build `scene_plan.md` from `sentences.json`: one row per shot with start-end time, narration covered, visual, type, on-screen text and asset (format in `references/templates.md`). A new shot every 3-6 s, alternating map/data shots with photo/clipping shots. Chapter cards at the start of parts 2+ play **before** the voice (negative start time).

Then the **asset checklist**, numbered, each with: what it is, which shot uses it, required or optional, and its fallback (map, card, recreated clipping). Fetch real media yourself where you can:
- `$PY $SK/fetch_commons.py search "<query>"` (add `--video` for footage), then `get "File:<name>" p_<person>|i_<image>|v_<video>`. Only reuse-friendly licences download; credits go to `assets/credits.json`.
- Photos of real people must be real photos with a credit line. Never generate a realistic image of a real person, and never present a generated image as archival.

Full rules: `references/media_and_licences.md`. Show the user the plan and what was found, and ask for any of their own assets (named by shot, e.g. `i_scene07_airport.jpg`) or "use fallbacks". Wait.

## Stage 6: Animation

1. `$PY $SK/prep_geo.py` once (cuts the map data to the bbox and prints the exact country names for fills).
2. Write the project's `scenes.py` from the scene plan using the kit (`references/engine_api.md`; every shot type is shown in the repo's `examples/demo/scenes.py`, a full film in `examples/iran-war-2026/scenes.py`). Follow `references/style_guide.md`. A strong hook: globe dive (`globescene`) → labelled map → real footage with kinetic words on the voice (`kinetic` + `voice_words`) → the key number.
3. Test before rendering: `$PY $SK/render.py stills <part> 1.0,4.5,...` (one frame per shot) and look at them.
4. Render a part: `$PY $SK/render.py part <n>` (picture + voice + soft SFX, loudness-normalised).
5. QA: `$PY $SK/render.py sheet <n> 2` makes contact sheets with a still every 2 s. Check every tile against `references/qa_checklist.md` (overlaps, cut-off text, unreadable labels, credits on every photo). Fix and re-render.
6. Show the user the part with a short shot list. Apply their changes to **that part only**, then go to the next part. If the user asks you to finish everything without stopping (e.g. overnight), render all parts, QA all, and say clearly afterwards which review steps were skipped.
7. When every part is approved: `$PY $SK/render.py full`.

Captions (if asked): build an SRT from the `_words.json` files (sentence by sentence, 42 characters per line max) and burn it with ffmpeg's `subtitles` filter, or deliver it as a separate file for upload (better for YouTube).

## Stage 7: Thumbnail and upload pack

- Copy-edit the project's `thumbnail.py`: 3-5 word title, the story's map as the key visual, one accent tag; run it and check the `_phone.png` version (320x180) is still readable. Offer 2-3 options if the user wants a choice.
- `$PY $SK/fetch_commons.py credits` writes `credits.txt`.
- Fill `YOUTUBE.md`: a search-friendly title, description with chapters (from part start times), key sources, photo credits, "Map data: Natural Earth", an AI-voice disclosure when Kokoro was used, tags (YouTube counts commas and adds 2 per multi-word tag: stay under 500), and the "altered or synthetic content" setting.
- Deliver the file paths. Upload or post only if the user explicitly asks.

## Reference files

- `references/style_guide.md`: the look (palette, maps, cards, clippings, pacing, sound)
- `references/engine_api.md`: every function in the Python kit with examples
- `references/templates.md`: research brief, script, voice check, scene plan, asset list formats
- `references/narration.md`: writing for Kokoro, voices, fixing takes, using your own voice
- `references/research_and_factcheck.md`: sources, the two-source rule, the independent fact-check
- `references/media_and_licences.md`: Commons, licences, credits, what never to generate
- `references/qa_checklist.md`: what to check on every contact sheet before showing the user
