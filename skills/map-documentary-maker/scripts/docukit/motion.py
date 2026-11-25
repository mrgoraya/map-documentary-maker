"""Kinetic text synced to the voice, and continuous ship/air traffic on maps."""
import os, re, glob, json, functools
import numpy as np, cv2
from .engine import *

# ---------------- word timings ----------------
@functools.lru_cache(None)
def _words(part):
    pin = CFG.get("voice_takes", {}).get(str(part))
    if pin:
        p = os.path.join(ROOT, "voice", pin[:-4] + "_words.json")
    else:
        fs = glob.glob(os.path.join(ROOT, "voice", f"part{part}_v*_words.json"))
        if not fs: return []
        p = max(fs, key=lambda f: int(re.findall(r"_v(\d+)_words\.json$", f)[0]))
    return json.load(open(p))["words"]

def voice_words(part, s0, s1, scene_start):
    """Words the voice speaks between s0 and s1 (seconds in the part), as [(word, time_in_scene)].
    Run align.py first. Use with kinetic() so each word lands exactly when it is said."""
    out = []
    for w in _words(part):
        if not (s0 - 0.05 <= w["s"] < s1): continue
        tok = w["w"].strip()
        if tok.startswith("-") and out:                  # Whisper splits "one-fifth" into "one" + "-fifth"
            tok = tok.lstrip("-")
        out.append((tok, w["s"] - scene_start))
    return out

def fade_edge(fr, h=360, a=0.6, top=True):
    """Soft dark gradient at the top (or bottom) so text reads over footage without a visible band."""
    g = (np.linspace(a, 0, h, dtype=np.float32) if top else np.linspace(0, a, h, dtype=np.float32))[:, None, None]
    sl = slice(0, h) if top else slice(H - h, H)
    fr[sl] = (fr[sl].astype(np.float32) * (1 - g)).astype(np.uint8)

# ---------------- kinetic text ----------------
def kinetic(fr, t, words, x=W / 2, y=H / 2, size=120, col=WHITE, keys=None, key_col=YELLOW, font_name="bebas",
            max_w=W * 0.8, line_h=1.0, upper=True, t1=None, pop=0.22, track=2):
    """Words appear one by one at their own times with a short pop (scale + rise + fade).
    words: [(word, time)] from voice_words(), or a string plus per-word spacing: kinetic(fr, t, ("ONE FIFTH", 0.3, 0.25)).
    keys: words to colour with key_col (compared without punctuation, any case)."""
    if isinstance(words, tuple):
        s, t0, gap = words
        words = [(w, t0 + i * gap) for i, w in enumerate(s.split())]
    if not words: return
    keys = {k.lower() for k in (keys or [])}
    out = 1 - (ramp(t, t1, 0.3) if t1 is not None else 0)
    toks = [(w.upper() if upper else w, at) for w, at in words]
    sp = text_w(" ", font_name, size)
    widths = [text_w(w, font_name, size) + track * len(w) for w, _ in toks]
    lines, cur, cw = [], [], 0
    for i, wd in enumerate(widths):
        if cur and cw + sp + wd > max_w: lines.append(cur); cur, cw = [], 0
        cur.append(i); cw += (sp if len(cur) > 1 else 0) + wd
    if cur: lines.append(cur)
    lh = size * line_h; y0 = y - lh * (len(lines) - 1) / 2
    for li, ln in enumerate(lines):
        tot = sum(widths[i] for i in ln) + sp * (len(ln) - 1); xx = x - tot / 2
        for i in ln:
            w, at = toks[i]
            p = clamp((t - at) / pop)
            if p > 0:
                k = eout(p); sc = 1.0 + 0.35 * (1 - k)
                c = key_col if re.sub(r"[^\w]", "", w).lower() in keys else col
                patch = text_patch(w, font_name, max(8, int(size * sc)), tuple(c), 400, True, track)
                blit(fr, patch, xx + widths[i] / 2, y0 + li * lh + 18 * (1 - k), k * out, "cm")
            xx += widths[i] + sp

# ---------------- traffic ----------------
def lane_pts(cam, way):
    return np.array([cam.p(*w) for w in way], np.float32)

def traffic(fr, cam, lanes, t, n=5, period=9.0, kind="ship", col=WHITE, size=15, show_lane=True, wake=True, alpha=1.0, seed=0):
    """Ships (or planes) running continuously along lanes, evenly spaced, each with a short wake.
    lanes: list of waypoint lists [(lon, lat), ...]; n ships per lane; one ship takes `period` s per lane."""
    rng = np.random.default_rng(seed)
    for li, way in enumerate(lanes):
        P = lane_pts(cam, way)
        seg = np.diff(P, axis=0); L = np.hypot(seg[:, 0], seg[:, 1]); cum = np.concatenate([[0], np.cumsum(L)]); tot = cum[-1]
        if show_lane:
            ov = fr.copy()
            cv2.polylines(ov, [np.round(P * 16).astype(np.int32)], False, tuple(int(c) for c in col), 1, cv2.LINE_AA, shift=4)
            cv2.addWeighted(ov, 0.18 * alpha, fr, 1 - 0.18 * alpha, 0, fr)
        off = rng.random()
        for k in range(n):
            ph = (t / period + k / n + off) % 1.0
            d = ph * tot
            x, y = np.interp(d, cum, P[:, 0]), np.interp(d, cum, P[:, 1])
            i = min(max(np.searchsorted(cum, d), 1), len(P) - 1)
            ang = np.arctan2(P[i, 1] - P[i - 1, 1], P[i, 0] - P[i - 1, 0])
            fade = clamp(ph / 0.06) * clamp((1 - ph) / 0.06) * alpha
            if wake:
                d0 = max(0, d - size * 3.2)
                xs = np.interp(np.linspace(d0, d, 8), cum, P[:, 0]); ys = np.interp(np.linspace(d0, d, 8), cum, P[:, 1])
                ov = fr.copy()
                cv2.polylines(ov, [np.round(np.stack([xs, ys], 1) * 16).astype(np.int32)], False, (200, 220, 235), 2, cv2.LINE_AA, shift=4)
                cv2.addWeighted(ov, 0.35 * fade, fr, 1 - 0.35 * fade, 0, fr)
            if fade > 0.01: icon(fr, kind, x, y, ang, size, col, fade)
