# Media and licences

## Where real photos and footage come from

**Wikimedia Commons** (`fetch_commons.py`) is the main source: official portraits, government and military photos and video (US government work is public domain), and news photos under Creative Commons.

```
$PY $SK/fetch_commons.py search "Abbas Araghchi 2025"            # candidates with licence, size, date
$PY $SK/fetch_commons.py search "USS Abraham Lincoln 2026" --video
$PY $SK/fetch_commons.py get "File:Abbas Araghchi 2025.jpg" p_araghchi
$PY $SK/fetch_commons.py credits                                   # credits.txt for the description
```

- Lines starting `OK` have a reuse-friendly licence (public domain, CC0, CC BY, CC BY-SA). `NO` lines (non-commercial, no-derivatives, fair use) are refused by `get`.
- Check the date and description: is it really this event, this year? A 2019 photo must not illustrate a 2026 strike. Put the date in the credit.
- Name files by role: `p_` people (portrait layout), `i_` images, `v_` video.
- Commons limits scripts: the tool sends an honest user agent, waits between calls and backs off when told to. Don't spoof a browser.
- If a credit from `credits.json` reads badly (HTML leftovers, "null"), set `CREDIT_OVERRIDE` in `scenes.py`.
- Crop out watermarks or other channels' logos, or don't use the image.

Other free sources: official government photo pages (whitehouse.gov, defense.gov/DVIDS, gov.uk under OGL with credit), UN Photo (check terms), NASA (public domain). Stock sites like Pexels and Pixabay are fine for generic B-roll (oil tankers, desert, city skylines), not for specific events.

## User assets

Article screenshots, archive photos and clips the user owns or has rights to. Ask them to name files by shot (`i_scene07_guardian.png`) and drop them in `assets/`.

## Never

- Never generate a realistic image or video of a real, identifiable person.
- Never present a generated or illustrative image as an archival photo. Generated scenes (if a tool is available) are muted, clearly illustrative, and labelled "Illustration" on screen.
- Never use a photo without its credit on screen.
- Never use media whose licence you couldn't confirm.

## Fallbacks when no real media exists

A map shot, a date card, a recreated clipping with the exact quote and source, a chart, or a name card over a dark background. These are honest and on-style.
