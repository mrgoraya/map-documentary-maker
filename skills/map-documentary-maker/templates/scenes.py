"""Scenes for this documentary, timed to the voice (seconds inside each part's voice file).
Copy the patterns below. Every scene is (start_time, builder). See references/engine_api.md.
Check positions with:  python render.py stills 1 2.0,5.0   before rendering a whole part."""
from docukit import *

# Places as (lon, lat). Look them up; never guess coordinates.
P = dict(TEHRAN=(51.39, 35.69), HORMUZ=(56.25, 26.57))

# Country fills use Natural Earth names exactly (prep_geo.py prints them).
FOCUS = {"Iran": (TEAL, 0.42)}

def opening(fr, cam, t, T):
    datecard(fr, t, 0.2, "1 JANUARY 2026", "THURSDAY")          # big date card, types on
    pin(fr, cam, P["TEHRAN"], "TEHRAN", t, 1.0, WHITE)

def route_demo(fr, cam, t, T):
    route(fr, cam, [(44, 22), P["HORMUZ"]], t, 0.3, 1.6, "ship", NAVY, 20, 0.1)
    label(fr, cam, (56.8, 25.4), "STRAIT OF HORMUZ", t, 1.2, 40, WHITE)

PART1 = [
    (0.0, mapscene((45, 30, 40), (51, 31, 72), FOCUS, draw=opening)),       # camera = (lon, lat, px per degree)
    (4.0, mapscene((55, 27, 120), (56, 26.6, 160), FOCUS, draw=route_demo)),
    (8.0, cardscene(lambda fr, t, T: clipping(fr, t, 0.2,
          "Replace this with the exact sentence from your source article",
          "Outlet name", "outlet.com · 1 Jan 2026", hl="exact sentence", hl_t=1.2),
          bgcam=((53, 30, 60), (53, 30, 56)), fills=FOCUS)),
]

# Part 2 and later can open with a chapter card that plays before the voice:
# PART2 = [(-3.0, chapter(2, "THE BLOCKADE")), (0.0, mapscene(...)), ...]

PARTS = {1: PART1}
