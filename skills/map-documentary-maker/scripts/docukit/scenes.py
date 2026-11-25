"""Scene builders. Each returns a function f(t, T) -> RGB frame, where t is the
time inside the scene and T its length. A part is a list of (start_seconds, f).

    PART1 = [
        (0.0, mapscene((45, 30, 40), (51, 31, 72), {"Iran": (TEAL, 0.42)}, draw=my_overlay)),
        (6.4, photoscene("p_khamenei", "ALI KHAMENEI", "Supreme Leader 1989-2026")),
    ]
    PARTS = {1: PART1}
"""
import os, json
import numpy as np, cv2
from .engine import *

A = f"{ROOT}/assets"
CREDIT_OVERRIDE = {}   # asset name -> full credit line, when credits.json is not good enough

def asset(name):
    """Path of assets/<name>.<ext>, or None when it is missing (scenes then use their fallback)."""
    for ext in ("jpg", "jpeg", "png", "webp", "webm", "mp4", "mov"):
        p = f"{A}/{name}.{ext}"
        if os.path.exists(p) and os.path.getsize(p) > 10000: return p
    return None

def credit_for(name):
    if name in CREDIT_OVERRIDE: return CREDIT_OVERRIDE[name]
    try:
        for c in json.load(open(f"{A}/credits.json")):
            if c["file"].split(".")[0] == name:
                art = (c.get("artist") or "").split("\n")[0].strip()[:60] or c.get("source", "Wikimedia Commons")
                return f"{art} · {c['license']} · via {c.get('source', 'Wikimedia Commons')}"
    except Exception:
        pass
    return "Wikimedia Commons"

BOTTOM = np.clip(1.0 - 0.5 * np.clip((np.arange(H, dtype=np.float32) - H * 0.574) / (H * 0.426), 0, 1), 0.5, 1)[:, None] * np.ones((1, W), np.float32)

def mapscene(c0, c1, fills=None, hi=None, draw=None, dim=1.0):
    """Camera moves from c0 to c1 = (lon, lat, pixels_per_degree). fills/hi may be dicts or functions of t.
    draw(fr, cam, t, T) adds routes, pins, labels and cards on top."""
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

def blackcard(big, small=None, bg=(12, 14, 17)):
    def f(t, T):
        fr = np.full((H, W, 3), bg, np.uint8)
        fr = (fr.astype(np.float32) * VIG[..., None]).astype(np.uint8)
        title(fr, t, 0.1, big, small, size=120)
        return fr
    return f

def dark():
    fr = np.full((H, W, 3), (12, 14, 17), np.uint8)
    return (fr.astype(np.float32) * VIG[..., None]).astype(np.uint8)

def cardscene(draw, bgcam=None, dimv=0.35, fills=None):
    """A card (clipping, chart, counter) over a dimmed drifting map, or over plain dark when bgcam is None.
    draw(fr, t, T)."""
    def f(t, T):
        if bgcam:
            c0, c1 = bgcam
            fr = basemap(cam_lerp(c0, c1, t / T), fills, dimv, True, None)
        else:
            fr = dark()
        draw(fr, t, T)
        return fr
    return f

def photoscene(name, nm=None, line=None, fx=0.5, fy=0.36, fallback=None, z0=1.03, z1=1.12, extra=None, desat=0.55, layout=None):
    """Real photo with Ken Burns, name bar and credit. Files named p_* (people) use the portrait layout:
    blurred backdrop, photo on the right with a feathered edge, so heads are never cropped."""
    if layout is None: layout = "portrait" if name.startswith("p_") else "cover"
    def f(t, T):
        p = asset(name)
        if not p:
            return fallback(t, T) if fallback else blackcard(nm or "", line)(t, T)
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
def videoscene(name, start=0.0, lab=None, sub=None, fallback=None, extra=None, crop=None, credit_s=None):
    """Real footage from assets/, starting at `start` seconds, graded to match the maps.
    crop=(x0, y0, x1, y1) fractions removes burned-in borders or redaction boxes. credit_s replaces the credit line
    (put the date and place in it: footage must never pass for a different event)."""
    def f(t, T):
        p = asset(name)
        if not p: return fallback(t, T) if fallback else blackcard(lab or "", sub)(t, T)
        key = (name, start, crop)
        if key not in _vids: _vids[key] = Video(p, start, crop)
        fr = _vids[key].frame(t)
        o = fr.astype(np.float32); g = o.mean(axis=2, keepdims=True)
        fr = np.clip((o * 0.6 + g * 0.4) * 0.82 * VIG[..., None] ** 0.6, 0, 255).astype(np.uint8)
        if lab: lower(fr, t, 0.3, lab, sub, size=84)
        credit(fr, credit_s or credit_for(name))
        if extra: extra(fr, t, T)
        return fr
    return f

def chapter(n, name, c0=(47, 29, 50), c1=(47, 29, 54), fills=None, col=ORANGE):
    """Chapter card ("PART 2" + title) over a dim map. Put it at a negative start time (e.g. -3.0)
    so it plays before the part's voice starts; render.py and audio.py handle the offset."""
    def f(t, T):
        fr = basemap(cam_lerp(c0, c1, t / T), fills, 0.4, True, None)
        text(fr, f"PART {n}", W / 2, H / 2 - 120, "inter", 36, col, 700, ramp(t, 0.2, .4) * (1 - ramp(t, T - .5, .4)), "cm", 8)
        title(fr, t, 0.3, name, None, size=140, t1=T - 0.5)
        return fr
    return f

def overlay(scene, draw):
    """Wrap any scene and draw extra things on it: overlay(mapscene(...), lambda fr, t, T: title(...))."""
    def f(t, T):
        fr = scene(t, T)
        draw(fr, t, T)
        return fr
    return f

def globescene(g0, g1, fills=None, draw=None):
    """Opening globe: camera from g0 to g1 = (lon, lat, radius_px); zoom eases in log space.
    End with R near 2580 and cut (cross-dissolve) to a mapscene at s = 45 on the same spot for a seamless dive."""
    import math
    def f(t, T):
        x = ease(t / T)
        lon = lerp(g0[0], g1[0], x); lat = lerp(g0[1], g1[1], x)
        R = math.exp(lerp(math.log(g0[2]), math.log(g1[2]), ease(clamp(t / T * 1.1 - 0.1))))
        fr = globe(lon, lat, R, fills)
        if draw: draw(fr, t, T)
        return fr
    return f
