# The Python kit (`docukit`)

`from docukit import *` in the project's `scenes.py`. Frames are 8-bit RGB numpy arrays of `W x H` (from `project.json`). Positions are pixels with (0,0) top left; places on maps are `(lon, lat)`.

## How a part is built

```python
PART1 = [(0.0, scene_a), (4.2, scene_b), ...]   # start time in the part's voice, seconds
PART2 = [(-3.0, chapter(2, "THE BLOCKADE")), (0.0, ...)]
PARTS = {1: PART1, 2: PART2}
```
A scene is any function `f(t, T) -> frame`: `t` = seconds since the scene started, `T` = its length. Take start times from `sentences.json` (a cut lands just before the sentence it illustrates).

Inside a scene, overlays take `t` and a start time `t0` (seconds inside the scene) so they animate in on cue. Most also take `t1` to animate out.

## Scene builders

| Function | What it makes |
|---|---|
| `mapscene(c0, c1, fills, hi=None, draw=None, dim=1.0)` | Map with the camera moving from `c0` to `c1`, each `(lon, lat, pixels_per_degree)`. `fills = {"Iran": (TEAL, 0.42)}` (or a function of t). `draw(fr, cam, t, T)` adds overlays. |
| `cardscene(draw, bgcam=None, dimv=0.35, fills=None)` | A card over a dim drifting map (`bgcam=(c0, c1)`) or plain dark. `draw(fr, t, T)`. |
| `photoscene(name, nm, line, fy=0.36, fallback=None)` | Photo from `assets/<name>.*` with Ken Burns, name bar, credit. `p_*` names use the portrait layout. Falls back if the file is missing. |
| `videoscene(name, start, lab, sub, crop=(x0,y0,x1,y1), credit_s=None, extra=None)` | Footage from `assets/`, from `start` seconds, graded to match. `crop` (fractions) removes burned-in text, borders or redaction boxes; `credit_s` sets the credit line (always with the real date and place). |
| `chapter(n, name, c0, c1, fills)` | "PART n" chapter card; use at a negative start time. |
| `globescene(g0, g1, fills, draw)` | Opening globe, camera `(lon, lat, radius_px)` from g0 to g1. End at radius 2580 and follow with a `mapscene` starting at `(lon, lat, 45)` on the same spot: the dissolve is seamless. `draw(fr, t, T)`. |
| `blackcard(big, small)` | Title on dark. |
| `overlay(scene, draw)` | Draw extra things on top of any scene. |

Zoom guide (`pixels_per_degree` on a 1920 px frame): 25 = Europe to India, 45 = the Middle East, 70 = one large country, 120-200 = a strait or a city region, 300+ = a city.

## Map overlays (inside `draw(fr, cam, t, T)`)

| Function | Use |
|---|---|
| `pin(fr, cam, lonlat, "TEHRAN", t, t0, col=WHITE, dx=18, dy=-14, size=30, anchor="lm", sub=None)` | Pulsing pin with label (and optional grey subline). |
| `label(fr, cam, lonlat, "IRAN", t, t0, size=46, color=WHITE)` | Big spaced country/sea label, centred on the point. |
| `route(fr, cam, [a, b], t, t0, dur, kind="jet", col=WHITE, size=20, curve=0.0)` | Dashed route that draws on with an icon. `kind`: jet, plane, ship, carrier, drone, missile, or None. 3+ waypoints = polyline. |
| `arc(fr, cam, a, b, t, t0, dur, col=RED, h=0.22, width=3, fade_after=None)` | Missile/strike arc. `h` = bow (negative bows the other way). |
| `flash(fr, cam, lonlat, t, t0, col=RED, size=1.0)` | Impact ring. |
| `glow_dot(fr, x, y, col, r)` | Glowing dot at pixel x, y (`cam.p(lon, lat)` converts). |
| `icon(fr, kind, x, y, angle, size, col)` | A single icon. |

## Cards and text (any scene)

| Function | Use |
|---|---|
| `datecard(fr, t, t0, "28 FEBRUARY 2026", "SATURDAY", x=110, y=760, t1=None)` | Big date that types on. |
| `lower(fr, t, t0, "HEADLINE", "detail line", x=110, y=870, size=76)` | Lower third. |
| `title(fr, t, t0, "BIG TITLE", "subtitle", y=H/2, size=150)` | Centred title. |
| `counter(fr, t, t0, 20.7, decimals=1, lab="MILLION BARRELS A DAY", src="EIA · 2024")` | Counting number; keep the source's precision with `decimals`. |
| `clipping(fr, t, t0, body, outlet, src, hl="phrase to highlight", hl_t=1.2)` | Paper news clipping with a highlight. `body` must be the exact quote. |
| `text(fr, s, x, y, font, size, color, weight, alpha, anchor, track)` | Any text. Fonts: `"bebas"`, `"inter"`, `"serif"`. Anchor = l/c/r + t/m/b. |
| `bar`, `shade` | Solid / dark rectangles. |
| `credit(fr, "Photo: ...")` | Credit line bottom right. |

## Motion (`motion.py`)

| Function | Use |
|---|---|
| `voice_words(part, s0, s1, scene_start)` | The words spoken between s0 and s1 (part time) as `[(word, time_in_scene)]`, from `align.py`. |
| `kinetic(fr, t, words, x, y, size, keys={"fifth"}, max_w, t1)` | Kinetic typography: each word pops in when it is spoken; `keys` words in yellow. `words` can also be `("ONE FIFTH", t0, gap)`. Keep it to one or two lines. |
| `traffic(fr, cam, lanes, t, n=5, period=9, kind="ship", size=15)` | Ships (or planes) running continuously along lanes, with wakes. Pass `t + k` to start mid-flow. |
| `fade_edge(fr, h, a, top=True)` | Soft dark gradient at the top or bottom so text reads over footage or maps, without a hard band. |

```python
def f_words(fr, t, T, t_scene=5.3):          # inside a videoscene(..., extra=f_words) starting at 5.3 s
    fade_edge(fr, 420, 0.75)
    kinetic(fr, t, voice_words(1, 5.4, 7.9, t_scene), y=160, size=124, keys={"20", "million"})
```

## Charts (`charts.py`)

```python
line_chart(fr, t, [dict(x=0, v=72.48, label="~$72", sub="27 FEB"),
                   dict(x=0.05, v=100.46, label="$100.46", sub="12 MAR"),
                   dict(x=0.98, v=92.74, label="$92.74", sub="18 NOV", gap_before=True)],
           "BRENT CRUDE, $ PER BARREL", "Reuters, Bloomberg", vmin=65, vmax=105)
split_bar(fr, t, ("NETANYAHU BLOC", 53), ("OPPOSITION", 48), total=120, needed=61,
          head="ISRAEL VOTES · 27 OCTOBER", source_s="Seats in the 120-seat Knesset · Al Jazeera")
board(fr, t, [("3,400+", "killed in Iran (health ministry)"), ("13", "US troops killed (Pentagon)")], "THE TOLL")
```

## Timing helpers

`ramp(t, t0, d)` 0 to 1 over `d` seconds · `ease(x)`, `eout(x)` easing · `lerp(a, b, x)` · `clamp(x)` · `cam_lerp(c0, c1, x)`.

## Assets and credits

`asset("p_trump")` returns the file path or None. `credit_for(name)` builds "Artist · Licence · via Wikimedia Commons" from `assets/credits.json`. Put exceptions in `CREDIT_OVERRIDE["name"] = "..."` in `scenes.py`.

## Layout notes

Default positions are tuned for 1920x1080. For 9:16 (1080x1920), pass explicit `x`/`y` to cards and keep important things in the middle 60% of the height (UI covers the top and bottom on phones).
