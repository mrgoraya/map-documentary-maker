"""The real scenes.py behind "The Iran War Explained (2026)" (Think with MG, 5:55). Times are local to each part's voice. See ../../skills/map-documentary-maker/references/engine_api.md."""
import os, json, math
import numpy as np, cv2
from docukit import *

A = f"{ROOT}/assets"
def asset(name):
    for ext in ("jpg", "png", "webm", "mp4"):
        p = f"{A}/{name}.{ext}"
        if os.path.exists(p) and os.path.getsize(p) > 10000: return p
    return None

CREDIT_OVERRIDE = {
    "i_hormuz_mines": "US Navy photo (NAVCENT), 11 Apr 2026 · Public domain · via Wikimedia Commons",
    "v_epicfury_launch": "US Navy footage, 1 Mar 2026 · Public domain · via Wikimedia Commons",
    "v_lincoln": "US Navy footage, 3 Mar 2026 · Public domain · via Wikimedia Commons",
    "i_riyadh_airport": "Security-camera image, 10 Oct 2026 · Public domain · via Wikimedia Commons",
}
def credit_for(name):
    if name in CREDIT_OVERRIDE: return CREDIT_OVERRIDE[name]
    try:
        for c in json.load(open(f"{A}/credits.json")):
            if c["file"].startswith(name + "."):
                art = c["artist"].split("\n")[0].strip()[:60] or "Wikimedia Commons"
                return f"{art} · {c['license']} · via Wikimedia Commons"
    except Exception: pass
    return "Wikimedia Commons"

# places (lon, lat)
P = dict(TEH=(51.39, 35.69), NAT=(51.73, 33.72), FOR=(50.99, 34.88), ISF=(51.67, 32.65), MINAB=(57.08, 27.15),
         HORM=(56.25, 26.57), QESHM=(55.90, 26.85), BANDAR=(56.27, 27.18), BEIT=(34.99, 31.75), TLV=(34.78, 32.08),
         BEIRUT=(35.50, 33.89), SHUAIBA=(48.16, 29.04), ALISALEM=(47.52, 29.35), MANAMA=(50.61, 26.21), RIFFA=(50.59, 25.92),
         MUWAFFAQ=(36.78, 31.83), RIYADH_AP=(46.70, 24.96), RIYADH=(46.72, 24.71), MUSCAT=(58.41, 23.59), ISB=(73.05, 33.69),
         GENEVA=(6.14, 46.20), DOHA=(51.53, 25.29), ABUDHABI=(54.37, 24.45), KUWAIT=(47.98, 29.37), AMMAN=(35.93, 31.95),
         SANAA=(44.21, 15.35), JASK=(57.77, 25.64), SIRIK=(57.10, 26.52), ISRAEL=(34.9, 31.4), N_ISRAEL=(35.4, 32.9),
         KERMAN=(57.08, 30.28), SHIRAZ=(52.53, 29.59), TABRIZ=(46.29, 38.08), MASHHAD=(59.6, 36.3), AHVAZ=(48.67, 31.32),
         ISFAHANC=(51.67, 32.65), BAGHDAD=(44.36, 33.31))

IRAN_F = {"Iran": (TEAL, 0.42)}
def iran_hi(a=1.0): return {"Iran": (TEAL, a)}
GULF_HOSTS = ["Qatar", "Kuwait", "Bahrain", "United Arab Emirates", "Saudi Arabia", "Jordan"]

# ---------------------------------------------------------------- helpers
def mapscene(c0, c1, fills=None, hi=None, draw=None, dim=1.0):
    def f(t, T):
        cam = cam_lerp(c0, c1, t / T)
        fl = fills(t) if callable(fills) else fills
        h = hi(t) if callable(hi) else hi
        if h is None and fl: h = {k: (v[0], min(1.0, v[1] * 2.4)) for k, v in fl.items()}
        fr = basemap(cam, fl, dim, True, h)
        fr[:] = (fr.astype(np.float32) * BOTTOM[..., None]).astype(np.uint8)
        if draw: draw(fr, cam, t, T)
        return fr
    return f

def photoscene(name, nm, line, fx=0.5, fy=0.36, fallback=None, z0=1.03, z1=1.12, extra=None, desat=0.55, layout=None):
    if layout is None: layout = "portrait" if name.startswith("p_") else "cover"
    def f(t, T):
        p = asset(name)
        if not p:
            return fallback(t, T) if fallback else blackcard(nm, line)(t, T)
        if layout == "portrait":
            fr = portrait(load_img(p), t, T, "right", 1.0, 1.05, fy)
        else:
            fr = kenburns(load_img(p), t, T, z0, z1, fx, fy, desat=desat)
        shade(fr, 0, H - 330, W, 330, 0.35)
        if nm: namebar(fr, t, 0.25, nm, line)
        credit(fr, ("" if name in CREDIT_OVERRIDE else "Photo: ") + credit_for(name))
        if extra: extra(fr, t, T)
        return fr
    return f

_vids = {}
def videoscene(name, start, lab=None, sub=None, fallback=None, extra=None):
    def f(t, T):
        p = asset(name)
        if not p: return fallback(t, T) if fallback else blackcard(lab or "", sub)(t, T)
        key = (name, start)
        if key not in _vids: _vids[key] = Video(p, start)
        fr = _vids[key].frame(t)
        o = fr.astype(np.float32); g = o.mean(axis=2, keepdims=True)
        fr = np.clip((o * 0.6 + g * 0.4) * 0.82 * VIG[..., None] ** 0.6, 0, 255).astype(np.uint8)
        if lab: lower(fr, t, 0.3, lab, sub, size=84)
        credit(fr, credit_for(name))
        if extra: extra(fr, t, T)
        return fr
    return f

def blackcard(big, small=None, bg=(12, 14, 17)):
    def f(t, T):
        fr = np.full((H, W, 3), bg, np.uint8)
        fr = (fr.astype(np.float32) * VIG[..., None]).astype(np.uint8)
        title(fr, t, 0.1, big, small, size=120)
        return fr
    return f

def dark(t, T, base=None):
    fr = np.full((H, W, 3), (12, 14, 17), np.uint8)
    return (fr.astype(np.float32) * VIG[..., None]).astype(np.uint8)

def cardscene(draw, bgcam=None, dimv=0.35, fills=None):
    """Card over a dimmed, slowly drifting map (or plain dark)."""
    def f(t, T):
        if bgcam:
            c0, c1 = bgcam
            fr = basemap(cam_lerp(c0, c1, t / T), fills, dimv, True, None)
        else:
            fr = dark(t, T)
        draw(fr, t, T)
        return fr
    return f

BOTTOM = np.ones((H, W), np.float32)
BOTTOM[:] = np.clip(1.0 - 0.5 * np.clip((np.arange(H, dtype=np.float32) - 620) / 460, 0, 1), 0.5, 1)[:, None]
REGION = (47, 29, 58); WIDE = (42, 29, 40)

# ---------------------------------------------------------------- PART 1
def p1_s1(fr, cam, t, T):
    datecard(fr, t, 0.2, "28 FEBRUARY 2026", "SATURDAY", x=110, y=760)

def p1_s2(fr, cam, t, T):
    for i, (a, b, d) in enumerate([((44, 22), P["TEH"], 0.0), ((40, 30), P["ISF"], 0.25), ((44, 21), P["SHIRAZ"], 0.45), ((40, 31), P["TABRIZ"], 0.6), ((46, 20), P["KERMAN"], 0.8)]):
        route(fr, cam, [a, b], t, d, 1.3, "jet", ORANGE, 18, 0.08, line_alpha=0.6, icon_alpha=1 - ramp(t, d + 1.3, 0.2))
        flash(fr, cam, b, t, d + 1.3, RED, 0.9)
    lower(fr, t, 0.4, "US + ISRAEL STRIKE IRAN", "Operation Epic Fury (US) · Operation Roaring Lion (Israel)")

def p1_s5(fr, cam, t, T):
    for i in range(3):
        arc(fr, cam, P["TLV"], P["TEH"], t, 0.2 + i * 0.9, 1.0, ORANGE, 0.2, 2, fade_after=4.0)
        arc(fr, cam, P["TEH"], P["TLV"], t, 0.6 + i * 0.9, 1.0, RED, -0.2, 2, fade_after=4.0)
    label(fr, cam, (32.4, 31.3), "ISRAEL", t, 0.2, 44, ORANGE)
    label(fr, cam, (54.5, 31.5), "IRAN", t, 0.2, 64)
    day = 1 + int(11 * clamp((t - 0.6) / 4.6))
    datecard(fr, t, 0.1, "JUNE 2025", f"THE 12-DAY WAR · DAY {day}", x=110, y=780)

def p1_s6(fr, cam, t, T):
    route(fr, cam, [(44, 26), P["NAT"]], t, 0.2, 1.6, "plane", WHITE, 20, 0.05, line_alpha=0.5, icon_alpha=1 - ramp(t, 1.8, 0.3))
    for i, (k, lab, dx, dy) in enumerate([("FOR", "FORDOW", 18, -14), ("NAT", "NATANZ", 18, -14), ("ISF", "ISFAHAN", 18, 14)]):
        pin(fr, cam, P[k], lab, t, 1.4 + i * 0.6, RED, dx, dy, 30)
        flash(fr, cam, P[k], t, 1.4 + i * 0.6, RED, 0.6)
    lower(fr, t, 0.4, "US STRIKES THREE NUCLEAR SITES", "22 June 2025")

def p1_s7(fr, cam, t, T):
    x, y = cam.p(53.5, 32.8)
    a = ramp(t, 0.3, 0.6)
    ph = 0.5 + 0.5 * math.sin(t * 3)
    for r, rot in ((60, 0), (60, 60), (60, 120)):
        ov = fr.copy()
        cv2.ellipse(ov, (int(x), int(y)), (r, r // 3), rot + t * 20, 0, 360, TEAL, 2, cv2.LINE_AA)
        cv2.addWeighted(ov, a * 0.9, fr, 1 - a * 0.9, 0, fr)
    glow_dot(fr, x, y, TEAL, 8 + 3 * ph, a)
    lower(fr, t, 0.2, "CEASEFIRE · 24 JUNE 2025", "The nuclear dispute remained")

def p1_s9(fr, cam, t, T):
    rng = np.random.default_rng(7)
    pts = [(P[k][0] + rng.normal(0, .15), P[k][1] + rng.normal(0, .15)) for k in ("TEH", "TEH", "ISF", "SHIRAZ", "TABRIZ", "MASHHAD", "AHVAZ", "KERMAN")]
    for i, p in enumerate(pts):
        a = ramp(t, 0.3 + i * 0.25, 0.4)
        if a > 0: glow_dot(fr, *cam.p(*p), (255, 190, 90), 5, a)
    if t > 3.5:
        shade(fr, 0, 0, W, H, 0.45 * ramp(t, 3.5, 0.4))
        counter(fr, t, 3.6, 2000, "", "+", "KILLED IN THE CRACKDOWN", "Source: HRANA rights group, 13 Jan 2026", y=430, dur=1.4)
    lower(fr, t, 0.2, "JANUARY 2026 · PROTESTS", "Protest locations are illustrative", t1=3.4)

def p1_s10(t, T):
    def ex(fr, t, T):
        if t > 0.6:
            clipping(fr, t, 0.7, "Iranian Patriots, KEEP PROTESTING ... HELP IS ON ITS WAY", "Truth Social post", "Donald Trump, 13 Jan 2026 (via RNZ, SBS)", hl="HELP IS ON ITS WAY", hl_t=1.3, x=600, y=480, rot=-2, width=900)
    return photoscene("p_trump", None, None, fx=0.5, fy=0.3, extra=ex, z0=1.02, z1=1.08, desat=0.5)(t, T)

def p1_s11(fr, cam, t, T):
    route(fr, cam, [(72, 8), (64, 18), (61.5, 21.5)], t, 0.2, 3.2, "carrier", WHITE, 26)
    route(fr, cam, [(36, 25), (38.5, 18), (44, 12.2), (52, 13), (60, 18.6)], t, 0.6, 3.6, "carrier", WHITE, 26)
    if t > 3.4:
        text(fr, "USS ABRAHAM LINCOLN", *cam.p(62.5, 22.6), "inter", 26, WHITE, 650, ramp(t, 3.4, 0.4), "lb")
    lower(fr, t, 0.2, "TWO US AIRCRAFT CARRIERS", "USS Abraham Lincoln (Arabian Sea, from late Jan) · USS Gerald R. Ford (ordered 13 Feb)")

def p1_s12(fr, cam, t, T):
    pin(fr, cam, P["MUSCAT"], "MUSCAT", t, 0.2, WHITE, 18, -14)
    pin(fr, cam, P["GENEVA"], "GENEVA", t, 0.5, WHITE, 18, -14)
    route(fr, cam, [P["MUSCAT"], P["GENEVA"]], t, 0.5, 2.6, None, WHITE, 0, 0.18)
    lower(fr, t, 0.3, "OMAN-MEDIATED TALKS", "Muscat and Geneva · February 2026")

def p1_s13(t, T):
    if t < 2.9:
        return photoscene("p_albusaidi", "BADR ALBUSAIDI", "Oman's foreign minister", fy=0.32, fallback=blackcard("OMAN'S FOREIGN MINISTER", "Badr Albusaidi"))(t, 2.9)
    fr = dark(t, T)
    clipping(fr, t, 2.95, "Peace 'within reach' as Iran agrees no nuclear material stockpile: Oman FM", "Al Jazeera", "aljazeera.com · 28 Feb 2026", hl="within reach", hl_t=6.1, rot=-1.5)
    return fr

def p1_s15(fr, cam, t, T):
    route(fr, cam, [(-60, 38), (-20, 44), (2, 46)], t, 0.0, 4.6, "plane", WHITE, 24)
    datecard(fr, t, 0.3, "27 FEB · 3:38 PM ET", "Final order, per Gen. Dan Caine (Pentagon briefing, 2 Mar)", x=110, y=760)

def p1_s16(t, T):
    def ex(fr, t, T):
        shade(fr, 0, H // 2 - 170, W, 300, 0.45 * ramp(t, 0.1, 0.3))
        title(fr, t, 0.15, "OPERATION EPIC FURY", "Began 28 Feb 2026", y=H / 2 - 40, size=140)
    fb = mapscene((53, 32, 90), (53, 32, 100), IRAN_F, draw=lambda fr, cam, t, T: [flash(fr, cam, P[k], t, 0.2 + i * 0.3) for i, k in enumerate(("TEH", "ISF", "SHIRAZ", "TABRIZ", "KERMAN"))])
    return videoscene("v_epicfury_launch", 2.0, None, None, fallback=lambda t, T: (lambda fr: (ex(fr, t, T), fr)[1])(fb(t, T)), extra=ex)(t, T)

def p1_s17(fr, cam, t, T):
    for i in range(4):
        arc(fr, cam, (P["TEH"][0] - i * .8, P["TEH"][1] - i * .9), P["TLV"], t, 0.1 + i * 0.35, 1.6, RED, 0.24, 2)
    flash(fr, cam, P["TLV"], t, 1.8, RED, 1.0)
    label(fr, cam, (32.6, 31.4), "ISRAEL", t, 0.0, 44, ORANGE)

def p1_s18(fr, cam, t, T):
    tg = [("KUWAIT", "Kuwait", 0.0, (45.7, 29.9)), ("MANAMA", "Bahrain", 0.3, (49.4, 26.9)), ("DOHA", "Qatar", 0.55, (51.2, 24.2)), ("ABUDHABI", "United Arab Emirates", 0.8, (55.2, 23.2)), ("RIYADH", "Saudi Arabia", 1.05, (44.6, 23.4)), ("AMMAN", "Jordan", 1.3, (37.3, 30.4))]
    for k, cn, d, lp in tg:
        arc(fr, cam, (52.5, 31.5), P[k], t, d, 1.2, RED, 0.2, 2)
        flash(fr, cam, P[k], t, d + 1.2, RED, 0.7)
    for k, cn, d, lp in tg:
        nm = {"United Arab Emirates": "UAE"}.get(cn, cn).upper()
        text(fr, nm, *cam.p(*lp), "bebas", 34, WHITE, 400, ramp(t, d + 1.2, 0.4), "cm", 2)
    lower(fr, t, 0.3, "IRAN STRIKES BACK", "At Israel and at Arab states that host US troops")

def p1_s19(fr, cam, t, T):
    x, y = W / 2, H / 2 - 60
    a = ramp(t, 0.3, 0.4) * (1 - ramp(t, 3.4, 0.4))
    if a > 0:
        icon(fr, "missile", x, y, -0.4, 110, WHITE, a)
        ov = fr.copy(); cv2.line(ov, (int(x - 120), int(y + 90)), (int(x + 120), int(y - 90)), RED, 9, cv2.LINE_AA)
        cv2.addWeighted(ov, a * ramp(t, 2.6, 0.3), fr, 1 - a * ramp(t, 2.6, 0.3), 0, fr)

def p1_s20(fr, cam, t, T):
    label(fr, cam, (56.6, 26.25), "STRAIT OF HORMUZ", t, 0.3, 64, WHITE)

def fills_strike(t):
    return {"Iran": (TEAL, 0.42)}

def p1_s18_fills(t):
    f = {"Iran": (TEAL, 0.42), "Israel": (ORANGE, 0.5)}
    for i, c in enumerate(GULF_HOSTS):
        f[c] = (RED, (0.18 if c == "Saudi Arabia" else 0.38) * ramp(t, 1.2 + i * 0.25, 0.4))
    return f

PART1 = [
    (0.0, mapscene((45, 30, 40), (51, 31, 72), IRAN_F, draw=p1_s1)),
    (3.2, mapscene((52, 32, 80), (52, 32, 95), {"Iran": (TEAL, 0.42), "Israel": (ORANGE, 0.5)}, draw=p1_s2)),
    (6.4, photoscene("p_khamenei", "ALI KHAMENEI", "Supreme Leader 1989–2026 · killed 28 Feb (confirmed by Iranian state media 1 Mar)", fy=0.33,
                     fallback=blackcard("ALI KHAMENEI", "Supreme Leader 1989–2026"))),
    (11.2, lambda t, T: (lambda fr: (title(fr, t, 0.4, "THE 2026 IRAN WAR", "How did we get here?", size=150), fr)[1])(mapscene((47, 29, 70), (47, 29, 50), IRAN_F, dim=0.55)(t, T))),
    (15.5, mapscene((43.5, 33, 62), (43.5, 33, 68), {"Iran": (TEAL, 0.42), "Israel": (ORANGE, 0.55)}, draw=p1_s5)),
    (21.8, mapscene((51.5, 33.6, 160), (51.5, 33.8, 210), IRAN_F, draw=p1_s6)),
    (27.7, mapscene((53.5, 32.5, 95), (53.5, 32.5, 88), IRAN_F, draw=p1_s7)),
    (31.6, cardscene(lambda fr, t, T: (clipping(fr, t, 0.2, "Iranians fear more economic pain, war as UN sanctions snapback", "Al Jazeera", "aljazeera.com · 28 Sep 2025", hl="UN sanctions snapback", hl_t=1.4),
                                      text(fr, "UN SANCTIONS RETURN · 28 SEP 2025", W / 2, 150, "bebas", 64, WHITE, 400, ramp(t, 0.6, .4), "cm", 3)), bgcam=((53, 32, 80), (53, 32, 70)), fills=IRAN_F)),
    (38.4, mapscene((53.5, 32.4, 92), (53.5, 32.4, 104), IRAN_F, draw=p1_s9)),
    (45.6, p1_s10),
    (49.4, mapscene((50, 20, 34), (54, 21, 44), IRAN_F, draw=p1_s11)),
    (54.0, mapscene((32, 36, 24), (36, 35, 26), {"Oman": (ORANGE, 0.4), "Switzerland": (ORANGE, 0.6)}, draw=p1_s12)),
    (58.5, p1_s13),
    (67.4, mapscene((-28, 42, 22), (-22, 42, 24), None, draw=p1_s15)),
    (72.4, p1_s16),
    (76.6, mapscene((43, 32, 70), (41.5, 32, 76), {"Iran": (TEAL, 0.42), "Israel": (ORANGE, 0.55)}, draw=p1_s17)),
    (80.3, mapscene((46, 28, 66), (47, 28, 72), p1_s18_fills, draw=p1_s18)),
    (84.6, mapscene((52, 29, 70), (55.5, 27, 130), IRAN_F, draw=p1_s19)),
    (89.1, mapscene((56.3, 26.6, 170), (56.3, 26.6, 300), IRAN_F, draw=p1_s20)),
]

# ---------------------------------------------------------------- PART 2
def chapter(n, name):
    def f(t, T):
        fr = basemap(cam_lerp((47, 29, 50), (47, 29, 54), t / T), IRAN_F, 0.4, True, None)
        text(fr, f"PART {n}", W / 2, H / 2 - 120, "inter", 36, ORANGE, 700, ramp(t, 0.2, .4) * (1 - ramp(t, T - .5, .4)), "cm", 8)
        title(fr, t, 0.3, name, None, size=140, t1=T - 0.5)
        return fr
    return f

def p2_s21(fr, cam, t, T):
    x0, y0 = cam.p(56.12, 27.1); x1, y1 = cam.p(56.36, 26.4)
    p = ease((t - 0.4) / 1.2)
    if p > 0:
        ov = fr.copy(); cv2.line(ov, (int(x0), int(y0)), (int(lerp(x0, x1, p)), int(lerp(y0, y1, p))), RED, 7, cv2.LINE_AA)
        cv2.addWeighted(ov, 0.9, fr, 0.1, 0, fr)
    lower(fr, t, 0.3, "IRGC DECLARES HORMUZ CLOSED", "Early March 2026")

def p2_s22(fr, cam, t, T):
    lane = [(52.5, 25.8), (55.4, 26.2), (56.35, 26.45), (57.2, 25.9), (59.0, 24.8)]
    pts = np.array([cam.p(*q) for q in lane], np.float32)
    seg = np.diff(pts, axis=0); L = np.hypot(seg[:, 0], seg[:, 1]); cum = np.concatenate([[0], np.cumsum(L)])
    speed = 160 * (1 - ramp(t, 2.6, 0.8))
    for i in range(7):
        s = (i * cum[-1] / 7 + 160 * min(t, 2.6) + speed * max(0, t - 2.6) * 0.5) % cum[-1]
        x, y = np.interp(s, cum, pts[:, 0]), np.interp(s, cum, pts[:, 1])
        j = min(max(np.searchsorted(cum, s), 1), len(pts) - 1)
        icon(fr, "ship", x, y, math.atan2(pts[j, 1] - pts[j - 1, 1], pts[j, 0] - pts[j - 1, 0]), 15, WHITE)
    counter(fr, t, 0.5, 20, "≈", "%", "OF THE WORLD'S OIL", "Normally passes through · US EIA", x=1450, y=300, size=170)

def p2_s24(fr, cam, t, T):
    arc(fr, cam, (40.5, 33.5), P["BEIT"], t, 0.1, 1.4, RED, 0.25, 3)
    flash(fr, cam, P["BEIT"], t, 1.5, RED, 1.2)
    pin(fr, cam, P["BEIT"], "BEIT SHEMESH", t, 1.5, RED, 22, 30, 32)
    datecard(fr, t, 0.3, "1 MARCH", "9 killed by an Iranian missile", x=110, y=780)

def p2_s25(fr, cam, t, T):
    route(fr, cam, [(50.5, 31.0), P["SHUAIBA"]], t, 0.1, 1.8, "drone", RED, 16, 0.1)
    flash(fr, cam, P["SHUAIBA"], t, 1.9, RED, 1.0)
    pin(fr, cam, P["SHUAIBA"], "PORT SHUAIBA, KUWAIT", t, 1.9, RED, 18, 18, 30)
    lower(fr, t, 0.3, "6 US SOLDIERS KILLED", "Drone strike, 1 March")

def p2_s26(fr, t, T):
    a = ramp(t, 0.2, 0.5)
    for i in range(6):
        x = W / 2 + (i - 2.5) * 70
        ai = ramp(t, 0.3 + i * 0.15, 0.3)
        pts = []
        for k in range(10):
            r = 22 if k % 2 == 0 else 9; an = -math.pi / 2 + k * math.pi / 5
            pts.append((x + r * math.cos(an), 400 + r * math.sin(an)))
        ov = fr.copy(); cv2.fillPoly(ov, [np.round(np.array(pts) * 16).astype(np.int32)], WHITE, cv2.LINE_AA, shift=4)
        cv2.addWeighted(ov, ai, fr, 1 - ai, 0, fr)
    title(fr, t, 0.4, "FIRST US COMBAT DEATHS OF THE WAR", "Port Shuaiba, Kuwait · 1 March 2026", y=560, size=96)

def p2_s27(fr, cam, t, T):
    pin(fr, cam, P["MINAB"], "MINAB", t, 0.4, WHITE, 18, -14, 34, pulse=False)
    lower(fr, t, 0.5, "MINAB · GIRLS' SCHOOL", "Strike on 28 February 2026")

def p2_s28(fr, t, T):
    title(fr, t, 0.2, "AT LEAST 165 DEAD", None, y=H / 2 - 40, size=150)
    text(fr, "MOSTLY CHILDREN", W / 2, H / 2 + 60, "bebas", 64, WHITE, 400, ramp(t, 0.9, .5), "cm", 4)
    text(fr, "Figure from Iranian officials (Al Jazeera, NPR)", W / 2, H / 2 + 140, "inter", 28, GREY, 500, ramp(t, 1.2, .5), "cm")

def p2_s30(fr, cam, t, T):
    for i in range(3):
        arc(fr, cam, (35.6, 33.3), (35.3 + i * .25, 32.75 + i * .1), t, 0.2 + i * 0.3, 0.9, RED, 0.35, 2)
    arc(fr, cam, (34.9, 32.4), P["BEIRUT"], t, 1.4, 0.9, ORANGE, 0.3, 2)
    flash(fr, cam, P["BEIRUT"], t, 2.3, ORANGE, 0.8)
    label(fr, cam, (35.95, 33.75), "LEBANON", t, 0.1, 44, WHITE)
    lower(fr, t, 0.2, "HEZBOLLAH ENTERS · 2 MARCH", "Israel strikes Beirut's southern suburbs")

def p2_s32(fr, t, T):
    # only sourced points: 27 Feb close $72.48, 12 Mar close $100.46 (Bloomberg, World Oil)
    x0, x1, y0, y1 = 420, 1500, 800, 380
    yv = lambda v: lerp(y0, y1, (v - 65) / 40)
    A, B = np.array([x0, yv(72.48)]), np.array([x1, yv(100.46)])
    p = ease((t - 0.4) / 3.0)
    cv2.line(fr, (x0 - 60, y0 + 20), (x1 + 60, y0 + 20), (70, 74, 78), 2, cv2.LINE_AA)
    yy = yv(100)
    for xx in range(x0 - 60, x1 + 60, 24): cv2.line(fr, (xx, int(yy)), (xx + 12, int(yy)), (110, 114, 118), 1, cv2.LINE_AA)
    text(fr, "$100", x0 - 80, yy, "inter", 26, GREY, 600, 1, "rm")
    C = A + (B - A) * p
    cv2.line(fr, (int(A[0]), int(A[1])), (int(C[0]), int(C[1])), ORANGE, 5, cv2.LINE_AA)
    glow_dot(fr, *A, ORANGE, 7); glow_dot(fr, *C, ORANGE, 7)
    text(fr, "$72.48", A[0], A[1] + 24, "bebas", 64, WHITE, 400, 1, "ct")
    text(fr, "27 FEB", A[0], y0 + 40, "inter", 26, GREY, 600, 1, "ct")
    a2 = ramp(t, 3.2, .3)
    text(fr, "$100.46", B[0], B[1] - 24, "bebas", 80, WHITE, 400, a2, "cb")
    text(fr, "12 MAR", B[0], y0 + 40, "inter", 26, GREY, 600, a2, "ct")
    text(fr, "BRENT CRUDE, $ PER BARREL (CLOSING PRICE)", x0 - 60, 150, "bebas", 64, WHITE, 400, ramp(t, 0.1, .4), "lt", 3)
    text(fr, "First close above $100 since August 2022 · Bloomberg, World Oil", x0 - 60, 225, "inter", 28, GREY, 500, ramp(t, 0.5, .4), "lt")

def p2_s33(fr, cam, t, T):
    pin(fr, cam, P["ISB"], "ISLAMABAD", t, 0.3, WHITE, 18, -14, 32)
    datecard(fr, t, 0.4, "7 APRIL", "Two-week ceasefire, brokered by Pakistan", x=110, y=760)

def p2_s34(t, T):
    nm = "J.D. VANCE"
    if asset("i_islamabad_talks") and t < 2.2:
        return photoscene("i_islamabad_talks", "ISLAMABAD TALKS", "11–12 April 2026", fx=0.62, fy=0.25, z0=1.32, z1=1.38)(t, 2.2)
    return photoscene("p_vance", "J.D. VANCE", "Led ~21 hours of talks · no deal", fy=0.3, fallback=blackcard("ISLAMABAD TALKS", "Led by J.D. Vance · no deal"))(t, T)

def blockade_ring(fr, cam, t, t0, alpha=1.0):
    ring = [(48.6, 29.0), (50.3, 27.6), (52.2, 26.3), (54.3, 26.0), (56.0, 26.2), (57.4, 25.3), (59.3, 24.6), (61.5, 24.6)]
    pts = np.array([cam.p(*q) for q in ring], np.float32)
    p = ease((t - t0) / 2.0)
    if p <= 0: return
    dashed(fr, pts, p, NAVY, 3, 16, 10, alpha)
    seg = np.diff(pts, axis=0); L = np.hypot(seg[:, 0], seg[:, 1]); cum = np.concatenate([[0], np.cumsum(L)])
    for i in range(6):
        s = cum[-1] * (i + 0.5) / 6
        if s > cum[-1] * p: continue
        x, y = np.interp(s, cum, pts[:, 0]), np.interp(s, cum, pts[:, 1])
        icon(fr, "ship", x, y - 16, 0, 15, NAVY, alpha * ramp(t, t0 + i * 0.25, 0.3))

def p2_s35(fr, cam, t, T):
    blockade_ring(fr, cam, t, 0.3)
    lower(fr, t, 0.4, "US NAVAL BLOCKADE", "Of ships using Iran's ports · from 13 April 2026")

def doc_card(fr, t, t0, tear=None):
    a = ramp(t, t0, 0.4)
    if a <= 0: return
    im = np.full((560, 820, 3), PAPER, np.uint8)
    cv2.rectangle(im, (0, 0), (819, 559), (200, 196, 186), 2)
    pil = Image.fromarray(im); d = ImageDraw.Draw(pil)
    d.text((60, 50), "ISLAMABAD MEMORANDUM", font=font("bebas", 70), fill=INK)
    d.text((60, 130), "14 points · signed 17 June 2026", font=font("inter", 30, 600), fill=(90, 86, 80))
    for i, s in enumerate(["STOP FIGHTING", "REOPEN HORMUZ", "LIFT THE BLOCKADE"]):
        al = ramp(t, t0 + 5.3 + i * 1.1, 0.3) if tear is None or t < tear else 1
        if al > 0:
            y = 220 + i * 95
            d.line([(70, y + 32), (88, y + 50), (120, y + 10)], fill=(30, 140, 80), width=7)
            d.text((150, y), s, font=font("bebas", 64), fill=INK)
    im = np.asarray(pil)
    x0, y0 = W // 2 - 410, H // 2 - 280
    if tear is not None and t >= tear:
        q = eout((t - tear) / 0.6)
        L, R = im[:, :410], im[:, 410:]
        blit(fr, np.dstack([L, np.full(L.shape[:2], 255, np.uint8)]), x0 - 140 * q, y0 + 40 * q, a * (1 - q * 0.6))
        blit(fr, np.dstack([R, np.full(R.shape[:2], 255, np.uint8)]), x0 + 410 + 140 * q, y0 + 70 * q, a * (1 - q * 0.6))
    else:
        blit(fr, np.dstack([im, np.full(im.shape[:2], 255, np.uint8)]), x0, y0, a)

PART2 = [
    (-3.0, chapter(2, "FIRE, AND A FRAGILE TRUCE")),
    (0.0, mapscene((56.3, 26.6, 260), (56.3, 26.6, 300), IRAN_F, draw=p2_s21)),
    (4.5, mapscene((55.5, 26.2, 150), (56.0, 26.2, 170), IRAN_F, draw=p2_s22)),
    (8.5, cardscene(lambda fr, t, T: clipping(fr, t, 0.1, "Iran says will attack any ship trying to pass through Strait of Hormuz: \"…set those ships ablaze\"", "Al Jazeera", "aljazeera.com · 2 Mar 2026 · quoting IRGC adviser Ebrahim Jabbari", hl="set those ships ablaze", hl_t=0.9), bgcam=((56.3, 26.6, 200), (56.3, 26.6, 190)), fills=IRAN_F)),
    (13.5, mapscene((36.5, 32.4, 120), (35.4, 31.9, 200), {"Israel": (ORANGE, 0.5)}, draw=p2_s24)),
    (19.7, mapscene((48.5, 29.6, 170), (48.3, 29.3, 210), {"Kuwait": (ORANGE, 0.45), "Iran": (TEAL, 0.42)}, draw=p2_s25)),
    (24.4, cardscene(p2_s26)),
    (28.2, mapscene((57.0, 27.4, 150), (57.08, 27.2, 190), IRAN_F, draw=p2_s27, dim=0.8)),
    (33.0, cardscene(p2_s28)),
    (38.6, cardscene(lambda fr, t, T: clipping(fr, t, 0.1, "Pentagon probe points to U.S. missile hitting Iranian school", "NPR", "npr.org · 11 Mar 2026 · preliminary findings, per officials", hl="U.S. missile", hl_t=1.0), bgcam=((57.0, 27.3, 160), (57.0, 27.3, 150)), fills=IRAN_F)),
    (43.6, mapscene((35.6, 33.2, 180), (35.6, 33.3, 220), {"Lebanon": (RED, 0.4), "Israel": (ORANGE, 0.5)}, draw=p2_s30)),
    (46.6, photoscene("p_mojtaba", "MOJTABA KHAMENEI", "Named Supreme Leader, 8 March 2026", fy=0.3, fallback=blackcard("MOJTABA KHAMENEI", "Named Supreme Leader, 8 March 2026"))),
    (52.5, cardscene(p2_s32)),
    (59.0, mapscene((62, 29, 40), (66, 30, 46), {"Pakistan": (ORANGE, 0.4), "Iran": (TEAL, 0.42)}, draw=p2_s33)),
    (63.6, p2_s34),
    (67.7, mapscene((54, 26.8, 72), (54, 26.6, 82), IRAN_F, draw=p2_s35)),
    (73.6, cardscene(lambda fr, t, T: doc_card(fr, t, 0.1), bgcam=((47, 29, 50), (47, 29, 54)), fills=IRAN_F)),
    (82.6, cardscene(lambda fr, t, T: doc_card(fr, t + 9.0, 0.0, tear=9.0 + 1.6), bgcam=((47, 29, 54), (47, 29, 55)), fills=IRAN_F)),
]

# ---------------------------------------------------------------- PART 3
def p3_s39(fr, cam, t, T):
    x, y = cam.p(56.9, 25.95)
    icon(fr, "ship", x - 40 * ease(t / 2), y, 3.3, 22, WHITE)
    flash(fr, cam, (56.9 - 0.15 * ease(t / 2), 25.95), t, 1.6, RED, 1.0)
    datecard(fr, t, 0.2, "7 JULY", "Qatari LNG tanker Al Rekayyat hit near Hormuz", x=110, y=780)

def p3_s42(fr, cam, t, T):
    blockade_ring(fr, cam, t, 0.2)
    lower(fr, t, 0.3, "THE BLOCKADE RETURNS", "14 July 2026")

def p3_s43(fr, cam, t, T):
    arc(fr, cam, (51, 30.5), P["ALISALEM"], t, 0.1, 1.2, RED, 0.25, 2)
    arc(fr, cam, (51.5, 29.5), P["MANAMA"], t, 0.3, 1.2, RED, 0.25, 2)
    flash(fr, cam, P["ALISALEM"], t, 1.3); flash(fr, cam, P["MANAMA"], t, 1.5)

def p3_s44(fr, cam, t, T):
    arc(fr, cam, (46.5, 33.0), P["MUWAFFAQ"], t, 0.1, 1.4, RED, 0.25, 3)
    flash(fr, cam, P["MUWAFFAQ"], t, 1.5, RED, 1.2)
    pin(fr, cam, P["MUWAFFAQ"], "MUWAFFAQ SALTI AIR BASE", t, 1.5, RED, 18, -14, 30)
    lower(fr, t, 0.3, "3 US SOLDIERS KILLED", "Jordan · 17 July 2026 (third soldier identified 21 July)")

def p3_s45(fr, cam, t, T):
    rng = np.random.default_rng(3)
    tg = [(rng.uniform(49, 60), rng.uniform(26, 36)) for _ in range(14)]
    n = int(clamp(t / 4.6) * 14)
    for i in range(14):
        tt = 0.33 * i
        flash(fr, cam, tg[i], t, tt, RED, 0.5)
    shade(fr, 0, 0, W, H, 0.4 * ramp(t, 4.8, 0.6))
    text(fr, f"NIGHT {min(14, max(1, n))}", 110, 120, "bebas", 80, WHITE, 400, ramp(t, 0.1, .3) * (1 - ramp(t, 4.6, .3)), "lt", 3)
    title(fr, t, 4.9, "PAUSE · LATE JULY", "After nearly two weeks of nightly US strikes", size=110)

def p3_s46(fr, cam, t, T):
    lane = [(55.4, 26.75), (56.2, 26.62), (56.6, 26.35), (57.3, 25.8)]
    a = 1 - 0.65 * ramp(t, 5.8, 0.8)
    route(fr, cam, lane, t, 0.4, 2.6, "ship", YELLOW, 18, line_alpha=0.9 * a, icon_alpha=a)
    blockade_ring(fr, cam, t, 5.6, 0.9)
    lower(fr, t, 0.3, "A TEMPORARY SHIPPING LANE?", "Iran says it agreed one with Oman (August) · Oman said it was \"hopeful\"")

def p3_s49(fr, cam, t, T):
    for i, (a, b) in enumerate([((57.2, 26.9), (58.6, 24.4)), ((57.6, 26.6), (59.2, 24.2))]):
        arc(fr, cam, a, b, t, 0.1 + i * 0.3, 1.0, RED, 0.3, 2)
    icon(fr, "ship", *cam.p(58.7, 24.3), 0.2, 20, NAVY); icon(fr, "ship", *cam.p(59.3, 24.1), 0.2, 20, NAVY)
    for i, q in enumerate([(56.8, 25.6), (57.6, 25.2), (58.0, 25.9)]):
        icon(fr, "ship", *cam.p(*q), 3.0, 18, WHITE)
        flash(fr, cam, q, t, 2.8 + i * 0.5, ORANGE, 0.8)
    lower(fr, t, 0.3, "5 SEPTEMBER", "CENTCOM says it hit 3 Iranian oil tankers after Iran fired missiles at US warships")

def p3_s50b(fr, cam, t, T):
    rng = np.random.default_rng(11)
    for i in range(25):
        q = (rng.uniform(55.6, 57.6), rng.uniform(25.4, 26.9))
        a = ramp(t, 0.1 + i * 0.05, 0.2) * (1 - ramp(t, 1.7 + i * 0.02, 0.4))
        if a > 0: cv2.circle(fr, tuple(int(v) for v in cam.p(*q)), 5, (230, 230, 230), -1, cv2.LINE_AA)
    shade(fr, 0, 0, W, H, 0.35 * ramp(t, 2.0, .5))
    counter(fr, t, 2.3, 25, "", "", "SEAFARERS KILLED SINCE FEBRUARY", "At least 25, in and around Hormuz · United Nations", y=430)

def p3_s51(fr, t, T):
    x0 = 260
    for i in range(7):
        a = ramp(t, 0.2 + i * 0.18, 0.25)
        x = x0 + i * 205
        bar(fr, x, 380, 180, 200, (40, 44, 48) if i < 6 else (31, 120, 112), a)
        text(fr, f"DAY {i + 1}", x + 90, 430, "bebas", 54, WHITE, 400, a, "cm", 2)
    text(fr, "HORMUZ", x0 + 6 * 205 + 90, 500, "bebas", 40, WHITE, 400, ramp(t, 1.6, .3), "cm", 2)
    text(fr, "REOPENS", x0 + 6 * 205 + 90, 540, "bebas", 40, WHITE, 400, ramp(t, 1.6, .3), "cm", 2)
    text(fr, "IRAN'S SEVEN-DAY PLAN", W / 2, 260, "bebas", 80, WHITE, 400, ramp(t, 0.1, .3), "cm", 4)
    text(fr, "In exchange: lift the blockade, waive oil sanctions, a ceasefire that includes Lebanon", W / 2, 660, "inter", 30, GREY, 500, ramp(t, 1.8, .4), "cm")
    if t > 4.3:
        q = eout((t - 4.3) / 0.4)
        ov = fr.copy()
        cv2.line(ov, (240, 360), (W - 240, 600), RED, 14, cv2.LINE_AA); cv2.line(ov, (240, 600), (W - 240, 360), RED, 14, cv2.LINE_AA)
        cv2.addWeighted(ov, q, fr, 1 - q, 0, fr)
        text(fr, "REJECTED · 26 SEP", W / 2, 800, "bebas", 110, RED, 400, q, "cm", 4)

def p3_s54(fr, cam, t, T):
    arc(fr, cam, P["SANAA"], P["RIYADH_AP"], t, 0.3, 1.8, RED, 0.25, 3)
    flash(fr, cam, P["RIYADH_AP"], t, 2.1, RED, 1.2)
    pin(fr, cam, P["RIYADH_AP"], "KING KHALID AIRPORT, RIYADH", t, 2.1, RED, 18, -14, 30)
    label(fr, cam, (48.6, 15.6), "YEMEN", t, 0.1, 44, WHITE)
    datecard(fr, t, 0.2, "10 OCTOBER", "Houthi missile hits Riyadh's main airport", x=110, y=70)

def p3_s55(t, T):
    def ex(fr, t, T):
        shade(fr, 0, 0, W, H, 0.35)
        counter(fr, t, 0.2, 12, "", "", "KILLED", "Saudi authorities · other reports say 13–14", y=430)
    return photoscene("i_riyadh_airport", None, None, fy=0.5, extra=ex,
                      fallback=cardscene(lambda fr, t, T: counter(fr, t, 0.2, 12, "", "", "KILLED", "Saudi authorities · other reports say 13–14", y=430), bgcam=((46.7, 24.9, 160), (46.7, 24.9, 170))))(t, T)

def p3_s56(fr, cam, t, T):
    lower(fr, t, 0.3, "ISRAEL VOTES · 27 OCTOBER", "No clear winner · 53 vs 48 seats (61 needed)")

def p3_s57(fr, cam, t, T):
    flash(fr, cam, P["QESHM"], t, 0.4, RED, 1.0); flash(fr, cam, P["MANAMA"], t, 1.2, RED, 0.8)
    datecard(fr, t, 0.2, "NOVEMBER", None, x=110, y=800)

def seats(fr, t, T):
    x0, x1, y = 300, 1620, 470
    tot = 120
    text(fr, "ISRAEL VOTES · 27 OCTOBER", W / 2, 190, "bebas", 90, WHITE, 400, ramp(t, 0.1, .4), "cm", 4)
    text(fr, "No clear winner", W / 2, 280, "inter", 36, GREY, 600, ramp(t, 0.4, .4), "cm")
    p = eout((t - 0.6) / 1.2)
    w = (x1 - x0)
    bar(fr, x0, y, w, 90, (40, 44, 48), 1)
    bar(fr, x0, y, w * 53 / tot * p, 90, ORANGE, 1)
    bar(fr, x1 - w * 48 / tot * p, y, w * 48 / tot * p, 90, TEAL, 1)
    xm = x0 + w * 61 / tot
    a = ramp(t, 1.6, .4)
    ov = fr.copy(); cv2.line(ov, (int(xm), y - 40), (int(xm), y + 130), WHITE, 3, cv2.LINE_AA); cv2.addWeighted(ov, a, fr, 1 - a, 0, fr)
    text(fr, "61 NEEDED", xm, y + 150, "bebas", 48, WHITE, 400, a, "ct", 2)
    text(fr, "NETANYAHU BLOC 53", x0, y - 20, "bebas", 52, ORANGE, 400, ramp(t, 0.9, .4), "lb", 2)
    text(fr, "OPPOSITION 48", x1, y - 20, "bebas", 52, TEAL, 400, ramp(t, 0.9, .4), "rb", 2)
    text(fr, "Seats in the 120-seat Knesset · Al Jazeera, JTA", W / 2, 760, "inter", 28, GREY, 500, ramp(t, 1.2, .4), "cm")

def israel_split(t):
    return {"Israel": (ORANGE, 0.55 * (1 - ramp(t, 1.0, .5)) + 0.0)}

def p3_s56_draw(fr, cam, t, T):
    # two-colour split over Israel (illustrative of a divided result)
    pts = _israel_pts(cam)
    if pts:
        a = ramp(t, 1.0, 0.6)
        for side, col in ((0, ORANGE), (1, TEAL)):
            mk = np.zeros((H, W), np.uint8); cv2.fillPoly(mk, pts, 255, cv2.LINE_AA, shift=4)
            xm = int(cam.p(35.0, 31.5)[0])
            if side == 0: mk[:, xm:] = 0
            else: mk[:, :xm] = 0
            m = (mk.astype(np.float32) / 255 * 0.55 * a)[..., None]
            fr[:] = (fr * (1 - m) + np.array(col, np.float32) * m).astype(np.uint8)
    p3_s56(fr, cam, t, T)

def _israel_pts(cam):
    from docukit.engine import _rings, _poly_pts
    return _poly_pts(cam, _rings(cam, "Israel"))

PART3 = [
    (-3.0, chapter(3, "THE BLOCKADE WAR")),
    (0.0, mapscene((56.6, 26.2, 220), (56.6, 26.1, 250), IRAN_F, draw=p3_s39)),
    (4.8, cardscene(lambda fr, t, T: clipping(fr, t, 0.1, "Iranian state TV said an oil tanker was attacked \"after ignoring repeated warnings\"", "The National", "thenationalnews.com · 7 Jul 2026", hl="ignoring repeated warnings", hl_t=0.9), bgcam=((56.6, 26.2, 200), (56.6, 26.2, 190)), fills=IRAN_F)),
    (9.0, photoscene("p_trump", "THE DEAL IS \"OVER\"", "Trump, 8 July 2026 (Axios)", fy=0.3, fallback=blackcard("THE DEAL IS \"OVER\"", "Trump, 8 July 2026"))),
    (12.5, mapscene((54, 26.8, 72), (54, 26.6, 80), IRAN_F, draw=p3_s42)),
    (16.0, mapscene((49.5, 28.5, 110), (49.5, 28.3, 120), {"Iran": (TEAL, 0.42), "Kuwait": (ORANGE, 0.4), "Bahrain": (ORANGE, 0.6)}, draw=p3_s43)),
    (18.4, mapscene((40, 32, 90), (37.5, 31.9, 130), {"Jordan": (ORANGE, 0.4)}, draw=p3_s44)),
    (22.2, mapscene((53.5, 31.5, 80), (53.5, 31.5, 86), IRAN_F, draw=p3_s45, dim=0.7)),
    (28.5, mapscene((56.4, 26.3, 190), (56.4, 26.2, 210), {"Iran": (TEAL, 0.42), "Oman": (ORANGE, 0.35)}, draw=p3_s46)),
    (39.4, lambda t, T: (lambda fr: (datecard(fr, t, 0.1, "SEPTEMBER", "Fighting flares again"), fr)[1])(mapscene((56, 26, 90), (56.5, 25.8, 110), IRAN_F, draw=lambda fr, cam, t, T: [flash(fr, cam, q, t, 0.4 + i * 0.5) for i, q in enumerate([(57.2, 25.9), (50.3, 29.24), (57.77, 25.64)])])(t, T))),
    (43.0, mapscene((57.8, 25.4, 170), (58.0, 25.2, 190), IRAN_F, draw=p3_s49)),
    (50.6, photoscene("i_hormuz_mines", "STRAIT OF HORMUZ", "US Navy destroyers in the strait, 11 April 2026", fy=0.5, fallback=mapscene((56.4, 26.3, 220), (56.4, 26.3, 240), IRAN_F))),
    (55.0, mapscene((56.6, 26.2, 200), (56.6, 26.2, 215), IRAN_F, draw=p3_s50b)),
    (60.4, cardscene(p3_s51)),
    (68.2, mapscene((50, 25, 55), (47, 21, 52), {"Yemen": (RED, 0.35), "Saudi Arabia": (ORANGE, 0.3), "Iran": (TEAL, 0.42)})),
    (70.4, mapscene((45.5, 20.5, 70), (46.2, 22, 80), {"Yemen": (RED, 0.35), "Saudi Arabia": (ORANGE, 0.3)}, draw=p3_s54)),
    (75.3, p3_s55),
    (78.7, cardscene(lambda fr, t, T: seats(fr, t, T), bgcam=((35.1, 31.4, 160), (35.1, 31.4, 170)), fills={"Israel": (ORANGE, 0.4)})),
    (84.0, mapscene((53, 27.5, 90), (55.5, 26.8, 140), IRAN_F, draw=p3_s57)),
]

# ---------------------------------------------------------------- PART 4
def p4_s58(fr, cam, t, T):
    from docukit.engine import _rings, _poly_pts
    a = ramp(t, 0.4, 0.6)
    pts = _poly_pts(cam, _rings(cam, "Iran"))
    ov = fr.copy(); cv2.polylines(ov, pts, True, YELLOW, 4, cv2.LINE_AA, shift=4); cv2.addWeighted(ov, a * (0.6 + 0.4 * math.sin(t * 4) ** 2), fr, 1 - a * (0.6 + 0.4 * math.sin(t * 4) ** 2), 0, fr)
    label(fr, cam, (51.0, 41.3), "CASPIAN SEA", t, 0.8, 40, WHITE)
    lower(fr, t, 0.3, "TASK FORCE IRON GATE · 7 NOV", "Targets Iran's land borders and Caspian routes")

def p4_s59(fr, t, T):
    for i in range(10):
        a = ramp(t, 0.4 + i * 0.12, 0.25)
        icon(fr, "ship", 560 + (i % 5) * 200, 720 + (i // 5) * 90, 0, 30, (120, 126, 132), a)
    counter(fr, t, 0.2, 25, "$", " BN+", "OF IRANIAN OIL BLOCKED", "US Central Command (Adm. Brad Cooper), October", y=380, dur=1.6)

def p4_s61(fr, cam, t, T):
    for i, d in enumerate(("13", "15", "17")):
        route(fr, cam, [(52.0 + i * .3, 28.2 + i * .2), P["MANAMA"] if i != 1 else P["RIFFA"]], t, 0.2 + i * 1.4, 1.4, "drone", RED, 14, 0.2, icon_alpha=1 - ramp(t, 1.6 + i * 1.4, .2))
        flash(fr, cam, P["MANAMA"] if i != 1 else P["RIFFA"], t, 1.6 + i * 1.4, RED, 0.7)
        text(fr, f"{d} NOV", 110 + i * 190, 120, "bebas", 76, WHITE if t < 1.6 + i * 1.4 else RED, 400, ramp(t, 0.2 + i * 1.4, .3), "lt", 2)
    label(fr, cam, (50.55, 26.45), "BAHRAIN", t, 0.1, 36, WHITE)

def p4_s62(fr, cam, t, T):
    route(fr, cam, [(54.0, 24.6), P["QESHM"]], t, 0.0, 1.3, "jet", ORANGE, 18, 0.1, icon_alpha=1 - ramp(t, 1.3, .2))
    flash(fr, cam, P["QESHM"], t, 1.3, RED, 1.0)
    pin(fr, cam, P["QESHM"], "QESHM ISLAND · 17 NOV", t, 1.3, RED, 18, 20, 30)

def p4_s63(fr, cam, t, T):
    arc(fr, cam, (50.5, 30.8), P["ALISALEM"], t, 0.0, 1.3, RED, 0.25, 3)
    flash(fr, cam, P["ALISALEM"], t, 1.3, RED, 1.0)
    pin(fr, cam, P["ALISALEM"], "ALI AL SALEM AIR BASE · 18 NOV", t, 1.3, RED, -18, -14, 30, anchor="rm")

def split_card(fr, t, T):
    a = ramp(t, 0.1, 0.4)
    bar(fr, 140, 240, 780, 520, (20, 24, 28), a * 0.85); bar(fr, 1000, 240, 780, 520, (20, 24, 28), a * 0.85)
    bar(fr, 140, 240, 780, 8, ORANGE, a); bar(fr, 1000, 240, 780, 8, TEAL, a)
    text(fr, "US + ISRAEL", 530, 330, "bebas", 80, ORANGE, 400, a, "cm", 4)
    text(fr, "Weighing new strikes", 530, 430, "inter", 40, WHITE, 600, a, "cm")
    text(fr, "Reports: NYT (18 Nov), CBS (20 Nov)", 530, 500, "inter", 26, GREY, 500, a, "cm")
    b = ramp(t, 4.8, 0.4)
    text(fr, "IRAN", 1390, 330, "bebas", 80, TEAL, 400, b, "cm", 4)
    for i, s in enumerate(["\"…will use all available", "means to counter", "US aggression\""]):
        text(fr, s, 1390, 420 + i * 52, "serif", 42, WHITE, 600, b, "cm")
    text(fr, "Foreign ministry spokesman Baghaei, 23 Nov (Al Jazeera)", 1390, 610, "inter", 24, GREY, 500, b, "cm")

def toll_board(fr, t, T):
    rows = [(2.1, "IRAN", "3,000+", "dead by April (Iran's own count)"), (6.0, "LEBANON", "4,300+", "killed (health ministry)"),
            (9.4, "US MILITARY", "23", "service members dead (Pentagon)"), (12.6, "DISPLACED IN IRAN", "UP TO 3.2M", "early in the war (UNHCR, March)")]
    text(fr, "THE COST SO FAR", 200, 140, "bebas", 96, WHITE, 400, ramp(t, 0.1, .4), "lt", 4)
    bar(fr, 200, 250, 1520 * eout(t / 0.8), 3, ORANGE, 1)
    for i, (t0, a_, b_, c_) in enumerate(rows):
        y = 300 + i * 165; a = ramp(t, t0, 0.4)
        text(fr, a_, 200, y + 20, "bebas", 64, GREY, 400, a, "lt", 3)
        text(fr, b_, 1220, y, "bebas", 110, WHITE, 400, a, "rt", 2)
        text(fr, c_, 1260, y + 40, "inter", 32, WHITE, 500, a, "lt")

def oil_line(fr, t, T):
    # sourced points only: 27 Feb $72.48, 12 Mar $100.46, 18 Nov $92.74, 24 Nov "below $90"
    x0, x1, y0, y1 = 360, 1560, 800, 420
    yv = lambda v: lerp(y0, y1, (v - 65) / 40)
    days = lambda d: x0 + (x1 - x0) * d / 270.0   # days since 27 Feb (24 Nov = day 270)
    pts = [(days(0), yv(72.48)), (days(13), yv(100.46)), (days(264), yv(92.74)), (days(270), yv(89.5))]
    cv2.line(fr, (x0 - 40, y0 + 20), (x1 + 40, y0 + 20), (70, 74, 78), 2, cv2.LINE_AA)
    p = ease((t - 0.3) / 3.6)
    seg = [(0, 1, False), (1, 2, True), (2, 3, False)]
    tot = 3 * p
    for i, (u, v, dashd) in enumerate(seg):
        q = clamp(tot - i)
        if q <= 0: break
        A, B = np.array(pts[u]), np.array(pts[v]); C = A + (B - A) * q
        if dashd: dashed(fr, np.array([A, C], np.float32), 1.0, ORANGE, 3, 12, 10)
        else: cv2.line(fr, (int(A[0]), int(A[1])), (int(C[0]), int(C[1])), ORANGE, 5, cv2.LINE_AA)
    for i, (lab, sub, anc, dy) in enumerate([("~$72", "27 FEB · before the war", "rm", 0), ("$100.46", "12 MAR", "cb", -24), ("$92.74", "18 NOV", "cb", -24), ("UNDER $90", "24 NOV", "lt", 24)]):
        a = ramp(t, 0.3 + i * 1.1, .3)
        if a <= 0: continue
        x, y = pts[i]; glow_dot(fr, x, y, ORANGE, 6, a)
        if anc == "rm":
            text(fr, lab, x - 24, y - 18, "bebas", 60, WHITE, 400, a, "rm"); text(fr, sub, x - 24, y + 28, "inter", 22, GREY, 600, a, "rm")
        elif anc == "lt":
            text(fr, lab, x - 10, y + dy, "bebas", 60, WHITE, 400, a, "rt"); text(fr, sub, x - 10, y + dy + 64, "inter", 22, GREY, 600, a, "rt")
        else:
            text(fr, lab, x, y + dy - 30, "bebas", 60, WHITE, 400, a, "cb"); text(fr, sub, x, y + dy, "inter", 22, GREY, 600, a, "cb")
    text(fr, "Dashed: prices in between not shown", (pts[1][0] + pts[2][0]) / 2, (pts[1][1] + pts[2][1]) / 2 + 40, "inter", 22, GREY, 500, ramp(t, 1.6, .4), "ct")
    text(fr, "BRENT CRUDE, $ PER BARREL", x0 - 40, 150, "bebas", 64, WHITE, 400, ramp(t, 0.1, .4), "lt", 3)
    text(fr, "Reuters-based reports, Bloomberg, CNBC, CBS", x0 - 40, 225, "inter", 26, GREY, 500, ramp(t, 0.4, .4), "lt")

def p4_s73(fr, cam, t, T):
    lane = [(52.5, 25.8), (55.4, 26.2), (56.35, 26.45), (57.2, 25.9), (59.0, 24.8)]
    pts = np.array([cam.p(*q) for q in lane], np.float32)
    seg = np.diff(pts, axis=0); L = np.hypot(seg[:, 0], seg[:, 1]); cum = np.concatenate([[0], np.cumsum(L)])
    for i in range(3):
        s = (i * cum[-1] / 3 + 40 * t) % cum[-1]
        x, y = np.interp(s, cum, pts[:, 0]), np.interp(s, cum, pts[:, 1])
        j = min(max(np.searchsorted(cum, s), 1), len(pts) - 1)
        icon(fr, "ship", x, y, math.atan2(pts[j, 1] - pts[j - 1, 1], pts[j, 0] - pts[j - 1, 0]), 15, WHITE)
    blockade_ring(fr, cam, t, -5, 0.45)
    lower(fr, t, 0.3, "NINE MONTHS IN", "Hormuz is still not open the way it was")

def p4_s74(fr, t, T):
    a = ramp(t, 0.1, 0.4)
    shade(fr, 0, 0, W, H, 0.35 * a)
    text(fr, "A DEAL?", W / 2, H / 2 - 95, "bebas", 160, TEAL, 400, a, "cm", 6)
    text(fr, "OR A NEW WAR?", W / 2, H / 2 + 95, "bebas", 160, RED, 400, ramp(t, 1.2, .4), "cm", 6)

def endcard(fr, t, T):
    lg = asset_logo()
    if lg is not None: blit(fr, lg, W / 2, H / 2 - 120, ramp(t, 0.1, .5), "cm")
    title(fr, t, 0.3, "THINK WITH MG", "Subscribe for what comes next", y=H / 2 + 110, size=110)

_logo = None
def asset_logo():
    global _logo
    if _logo is None:
        p = f"{A}/logo.png"   # your channel logo (PNG with transparency) in assets/
        if os.path.exists(p):
            im = Image.open(p).convert("RGBA"); s = 260 / max(im.size); im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
            _logo = np.asarray(im)
        else: _logo = False
    return _logo if _logo is not False else None

PART4 = [
    (-3.0, chapter(4, "WHERE IT STANDS")),
    (0.0, mapscene((55, 34, 56), (55, 34.5, 62), IRAN_F, draw=p4_s58)),
    (6.0, cardscene(p4_s59, bgcam=((54, 26.6, 80), (54, 26.6, 76)), fills=IRAN_F)),
    (13.3, photoscene("p_trump", None, None, fy=0.3, extra=lambda fr, t, T: clipping(fr, t, 0.4, "Trump calls Iran war 'effectively over': \"Iran militarily is effectively over\"", "Al Jazeera", "aljazeera.com · 9 Nov 2026", hl="effectively over", hl_t=1.4, x=640, y=500, width=980),
                      fallback=cardscene(lambda fr, t, T: clipping(fr, t, 0.4, "Trump calls Iran war 'effectively over': \"Iran militarily is effectively over\"", "Al Jazeera", "aljazeera.com · 9 Nov 2026", hl="effectively over", hl_t=1.4)))),
    (19.0, mapscene((51.0, 26.8, 190), (50.8, 26.4, 230), {"Bahrain": (ORANGE, 0.6), "Iran": (TEAL, 0.42)}, draw=p4_s61)),
    (24.9, mapscene((55.8, 26.4, 230), (55.9, 26.8, 280), IRAN_F, draw=p4_s62)),
    (27.3, mapscene((48.5, 29.6, 160), (48.0, 29.4, 200), {"Kuwait": (ORANGE, 0.45), "Iran": (TEAL, 0.42)}, draw=p4_s63)),
    (29.8, cardscene(lambda fr, t, T: split_card(fr, t, T), bgcam=((47, 29, 55), (47, 29, 58)), fills=IRAN_F)),
    (39.4, cardscene(toll_board)),
    (58.4, cardscene(oil_line)),
    (63.8, cardscene(lambda fr, t, T: clipping(fr, t, 0.1, "\"We'll see what happens after the new year starts\"", "CBS News", "cbsnews.com · Trump to Israel's Channel 12, 19 Nov 2026", hl="after the new year starts", hl_t=0.8), bgcam=((47, 29, 55), (47, 29, 57)), fills=IRAN_F)),
    (67.8, mapscene((56.3, 26.5, 140), (56.3, 26.5, 200), IRAN_F, draw=p4_s73)),
    (71.7, cardscene(p4_s74, bgcam=((47, 29, 48), (47, 29, 52)), fills=IRAN_F)),
    (75.0, cardscene(endcard)),
]

PARTS = {1: PART1, 2: PART2, 3: PART3, 4: PART4}
