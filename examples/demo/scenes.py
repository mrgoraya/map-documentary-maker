"""Demo: 'Why the Strait of Hormuz matters' (~26 s, one part). Facts: research/brief.md (EIA).
Shows every kind of shot: globe dive, labelled map, real footage, kinetic text on the voice's own word
timings, live ship traffic, a counter, a source clipping with a highlight, and pipeline routes.
Start times come from sentences.json (align.py)."""
from docukit import *

P = dict(HORMUZ=(56.25, 26.57), ABQAIQ=(49.67, 25.94), YANBU=(38.06, 24.09), HABSHAN=(53.6, 23.85), FUJAIRAH=(56.34, 25.12))
IRAN = {"Iran": (TEAL, 0.35)}
BYPASS = {"Saudi Arabia": (ORANGE, 0.28), "United Arab Emirates": (ORANGE, 0.45)}
SEA = (150, 190, 220)
# inbound and outbound tanker lanes through the strait (illustrative, following the traffic separation scheme)
LANES = [[(50.2, 27.9), (53.0, 26.9), (55.6, 26.6), (56.45, 26.45), (57.2, 25.75), (58.6, 24.9), (60.5, 24.2)],
         [(60.4, 23.9), (58.5, 24.6), (57.05, 25.6), (56.35, 26.3), (55.5, 26.4), (52.8, 26.6), (50.0, 27.5)]]

# 1 -- globe dive, title words land as they are spoken
def g_title(fr, t, T):
    kinetic(fr, t, voice_words(1, 0.0, 1.5, 0.0), y=150, size=110, keys={"hormuz"}, t1=T - 0.6)

# 2 -- the strait
def s_strait(fr, cam, t, T):
    label(fr, cam, (55.0, 29.6), "IRAN", t, 0.0, 64)
    label(fr, cam, (52.4, 25.6), "PERSIAN GULF", t, 0.1, 32, SEA, track=6)
    label(fr, cam, (59.2, 24.2), "GULF OF OMAN", t, 0.5, 30, SEA, track=6)
    traffic(fr, cam, LANES, t + 3, n=4, period=10, kind="ship", size=13, alpha=ramp(t, 0.2, 0.6))
    pin(fr, cam, P["HORMUZ"], "STRAIT OF HORMUZ", t, 0.3, YELLOW, 26, -46, 32)

# 3 -- real footage, numbers typed on the words
def f_words(fr, t, T, t_scene=5.3):
    fade_edge(fr, 420, 0.75)
    kinetic(fr, t, voice_words(1, 5.4, 7.9, t_scene), y=160, size=124, keys={"20", "million"})

# 4 -- live traffic + counter
def s_traffic(fr, cam, t, T):
    traffic(fr, cam, LANES, t + 5, n=7, period=9, kind="ship", size=17)
    fade_edge(fr, 460, 0.7, top=False)
    counter(fr, t, 0.05, 20.7, "", "", "MILLION BARRELS OF OIL A DAY", "2024 · U.S. Energy Information Administration",
            x=W * 0.3, y=780, size=170, dur=1.2, decimals=1)

# 5 -- one fifth, word by word
def c_fifth(fr, t, T, t_scene=10.5):
    kinetic(fr, t, voice_words(1, 10.6, 14.3, t_scene), y=420, size=118, keys={"one", "fifth"}, max_w=W * 0.7, line_h=1.05)
    for i in range(5):
        a = ramp(t, 1.4 + i * 0.1, .3)
        bar(fr, W / 2 - 330 + i * 136, 690, 112, 120, YELLOW if i == 0 else (52, 56, 60), a)
    text(fr, "EIA: about 20% of global petroleum liquids consumption, 2024", W / 2, 860, "inter", 28, GREY, 500, ramp(t, 1.8, .4), "cm")

# 6 -- the source, highlighted
def c_clip(fr, t, T):
    clipping(fr, t, 0.1, "Saudi Arabia and the UAE have some infrastructure in place that can bypass the Strait of Hormuz, "
             "which may somewhat mitigate any transit disruptions through the strait.",
             "U.S. Energy Information Administration", "eia.gov · Today in Energy · 16 Jun 2025",
             hl="Saudi Arabia and the UAE have some infrastructure in place that can bypass the Strait of Hormuz", hl_t=0.9, y=H / 2 + 20)

# 7 -- the pipelines, and how little they carry
def s_bypass(fr, cam, t, T, t_scene=19.8):
    traffic(fr, cam, LANES, t + 8, n=5, period=9, kind="ship", size=11)
    route(fr, cam, [P["ABQAIQ"], (44.0, 25.2), P["YANBU"]], t, 0.1, 1.4, None, ORANGE, line_alpha=0.95)
    route(fr, cam, [P["HABSHAN"], (55.2, 24.4), P["FUJAIRAH"]], t, 0.5, 1.0, None, ORANGE, line_alpha=0.95)
    pin(fr, cam, P["YANBU"], "YANBU", t, 1.4, ORANGE, 18, -14, 28)
    pin(fr, cam, P["FUJAIRAH"], "FUJAIRAH", t, 1.5, ORANGE, 18, 16, 28)
    label(fr, cam, (45.5, 23.2), "SAUDI ARABIA", t, 0.0, 48)
    label(fr, cam, (54.0, 22.9), "UAE", t, 0.2, 40)
    fade_edge(fr, 420, 0.8, top=False)
    kinetic(fr, t, voice_words(1, 21.0, 24.3, t_scene), y=H - 170, size=84, keys={"fraction"}, max_w=W * 0.94)
    text(fr, "EIA: 2.6 to 4.7 million b/d of bypass capacity vs about 20 million b/d through the strait · routes illustrative",
         W / 2, H - 70, "inter", 24, GREY, 500, ramp(t, 1.6, .4), "cm")

CREDIT_TANKER = "Oil tanker in the Strait of Hormuz, 3 May 2023 · U.S. Navy (NAVCENT) · Public domain · via Wikimedia Commons"

PART1 = [
    (0.0, globescene((5, 18, 330), (55.5, 26.6, 2580), IRAN, draw=g_title)),
    (3.2, mapscene((55.5, 26.6, 45), (56.2, 26.4, 105), IRAN, draw=s_strait)),
    (5.3, videoscene("v_niovi", 6.0, crop=(0.08, 0.1, 0.85, 0.83), credit_s=CREDIT_TANKER, extra=f_words)),
    (7.9, mapscene((56.4, 26.2, 150), (56.6, 26.1, 172), IRAN, draw=s_traffic)),
    (10.5, cardscene(c_fifth, bgcam=((50, 27, 45), (50, 27, 42)), fills=IRAN)),
    (15.0, cardscene(c_clip, bgcam=((48, 25, 50), (48, 25, 47)), fills=BYPASS)),
    (19.8, mapscene((49.5, 26.0, 52), (48.5, 25.3, 58), dict(IRAN, **BYPASS), draw=s_bypass)),
]
PARTS = {1: PART1}
