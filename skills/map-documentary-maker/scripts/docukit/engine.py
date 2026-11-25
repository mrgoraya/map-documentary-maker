"""docukit engine: dark relief maps, routes, icons, cards, clippings, photos, video.

Everything is drawn with numpy + OpenCV + Pillow into 8-bit RGB frames.
The project folder (env DOC_PROJECT, default: current directory) holds:
  project.json   size, fps, map bounding box
  data/          countries.pkl + relief.npy + relief.json (made by prep_geo.py)
  assets/        photos and clips (fetched by fetch_commons.py) + credits.json
Fonts come from the shared cache made by setup.sh (env DOC_CACHE, default ~/.cache/map-documentary-maker).
"""
import math, pickle, functools, subprocess, os, json
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.abspath(os.environ.get("DOC_PROJECT", os.getcwd()))
CACHE = os.path.expanduser(os.environ.get("DOC_CACHE", "~/.cache/map-documentary-maker"))
D = f"{ROOT}/data"

def _load_json(p, default):
    try: return json.load(open(p))
    except Exception: return default

CFG = _load_json(f"{ROOT}/project.json", {})
W, H, FPS = int(CFG.get("width", 1920)), int(CFG.get("height", 1080)), int(CFG.get("fps", 30))
_RM = _load_json(f"{D}/relief.json", {})
RLON0, RLAT0, RPX = float(_RM.get("lon0", -12.0)), float(_RM.get("lat1", 54.0)), float(_RM.get("px_per_deg", 60.0))
COS = math.cos(math.radians(float(_RM.get("cos_lat", 30.0))))  # equirectangular squash for the map's middle latitude

# palette (RGB 0..255)
TEAL = (31, 181, 168); ORANGE = (240, 138, 36); RED = (226, 65, 58); WHITE = (240, 240, 236)
YELLOW = (255, 214, 64); GREY = (150, 158, 164); NAVY = (90, 140, 210); PAPER = (244, 240, 230); INK = (24, 24, 26)

# ---------------- math ----------------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x):
    x = clamp(x); return 4 * x * x * x if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def eout(x): x = clamp(x); return 1 - (1 - x) ** 3
def lerp(a, b, t): return a + (b - a) * t
def ramp(t, t0, d=0.4): return clamp((t - t0) / d) if d > 0 else float(t >= t0)

# ---------------- data ----------------
@functools.lru_cache(None)
def countries():
    return pickle.load(open(f"{D}/countries.pkl", "rb"))

@functools.lru_cache(None)
def relief():
    a = np.load(f"{D}/relief.npy").astype(np.float32)
    a = (a - 45) / (252 - 45)
    return cv2.GaussianBlur(a, (0, 0), 0.6)

# ---------------- fonts / text ----------------
FONTS = {"bebas": f"{CACHE}/fonts/BebasNeue.ttf", "inter": f"{CACHE}/fonts/Inter.ttf", "serif": f"{CACHE}/fonts/SourceSerif4.ttf"}

@functools.lru_cache(None)
def font(name, size, wght=400):
    f = ImageFont.truetype(FONTS[name], size)
    if name in ("inter", "serif"):
        try:
            axes = f.get_variation_axes()
            vals = []
            for ax in axes:
                nm = ax.get("name", b"")
                nm = nm.decode() if isinstance(nm, bytes) else str(nm)
                if "eight" in nm or nm.lower().startswith("wght"): vals.append(wght)
                else: vals.append(min(max(size, ax["minimum"]), ax["maximum"]))
            f.set_variation_by_axes(vals)
        except Exception:
            pass
    return f

@functools.lru_cache(4096)
def text_patch(text, fname, size, color=WHITE, wght=400, shadow=True, track=0):
    """RGBA numpy patch of text with soft shadow."""
    f = font(fname, size, wght)
    if track:
        widths = [f.getlength(c) + track for c in text]
        tw = int(sum(widths)) + 2
    else:
        tw = int(f.getlength(text)) + 2
    asc, desc = f.getmetrics()
    pad = 16 if shadow else 2
    im = Image.new("RGBA", (tw + pad * 2, asc + desc + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    def draw(dr, fill):
        if track:
            x = pad
            for c, w in zip(text, widths):
                dr.text((x, pad), c, font=f, fill=fill); x += w
        else:
            dr.text((pad, pad), text, font=f, fill=fill)
    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); draw(ImageDraw.Draw(sh), (0, 0, 0, 200))
        sh = sh.filter(ImageFilter.GaussianBlur(5)); im = Image.alpha_composite(im, sh)
        im2 = Image.new("RGBA", im.size, (0, 0, 0, 0)); im2.paste(im, (0, 3)); im = im2
    draw(ImageDraw.Draw(im), tuple(color) + (255,))
    return np.asarray(im)

def blit(fr, patch, x, y, alpha=1.0, anchor="lt"):
    """Alpha-blend RGBA patch onto uint8 RGB frame. anchor: l/c/r + t/m/b."""
    if alpha <= 0.003 or patch is None: return
    ph, pw = patch.shape[:2]
    if anchor[0] == "c": x -= pw // 2
    elif anchor[0] == "r": x -= pw
    if anchor[1] == "m": y -= ph // 2
    elif anchor[1] == "b": y -= ph
    x, y = int(round(x)), int(round(y))
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + pw, W), min(y + ph, H)
    if x0 >= x1 or y0 >= y1: return
    p = patch[y0 - y:y1 - y, x0 - x:x1 - x]
    a = p[..., 3:4].astype(np.float32) * (alpha / 255.0)
    reg = fr[y0:y1, x0:x1].astype(np.float32)
    fr[y0:y1, x0:x1] = (reg * (1 - a) + p[..., :3].astype(np.float32) * a).astype(np.uint8)

def text(fr, s, x, y, fname="inter", size=36, color=WHITE, wght=500, alpha=1.0, anchor="lt", track=0, shadow=True):
    blit(fr, text_patch(s, fname, size, tuple(color), wght, shadow, track), x, y, alpha, anchor)

def text_w(s, fname, size, wght=400):
    return font(fname, size, wght).getlength(s)

# ---------------- camera / map ----------------
class Cam:
    def __init__(self, lon, lat, s): self.lon, self.lat, self.s = lon, lat, s
    def p(self, lon, lat):
        return ((lon - self.lon) * COS * self.s + W / 2, (self.lat - lat) * self.s + H / 2)
    def pa(self, a):  # array Nx2 lon/lat -> pixels
        out = np.empty_like(a, dtype=np.float32)
        out[:, 0] = (a[:, 0] - self.lon) * COS * self.s + W / 2
        out[:, 1] = (self.lat - a[:, 1]) * self.s + H / 2
        return out

def cam_lerp(c0, c1, t):
    t = ease(t)
    # zoom interpolated in log space
    s = math.exp(lerp(math.log(c0[2]), math.log(c1[2]), t))
    return Cam(lerp(c0[0], c1[0], t), lerp(c0[1], c1[1], t), s)

def _rings(cam, name):
    lod = "fine" if cam.s > 90 else "coarse"
    return countries()[lod].get(name, [])

def _poly_pts(cam, rings):
    out = []
    for r in rings:
        p = cam.pa(r)
        if p[:, 0].max() < -50 or p[:, 0].min() > W + 50 or p[:, 1].max() < -50 or p[:, 1].min() > H + 50: continue
        out.append(np.round(p * 16).astype(np.int32))
    return out

OCEAN = np.array([10, 17, 24], np.float32); LAND_D = np.array([34, 36, 38], np.float32); LAND_L = np.array([92, 96, 98], np.float32)

def basemap(cam, fills=None, dim=1.0, borders=True, border_hi=None):
    """fills: {country: (rgb, alpha)}; border_hi: {country: rgb} bright borders."""
    r = relief()
    sx = RPX / (COS * cam.s); sy = RPX / cam.s
    u0 = (cam.lon - RLON0) * RPX; v0 = (RLAT0 - cam.lat) * RPX
    M = np.array([[sx, 0, u0 - W / 2 * sx], [0, sy, v0 - H / 2 * sy]], np.float32)
    rel = cv2.warpAffine(r, M, (W, H), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REFLECT)
    land = np.zeros((H, W), np.uint8)
    C = countries()["fine" if cam.s > 90 else "coarse"]
    allpts = []
    for name in C:
        allpts += _poly_pts(cam, C[name])
    if allpts: cv2.fillPoly(land, allpts, 255, cv2.LINE_AA, shift=4)
    m = (land.astype(np.float32) / 255.0)[..., None]
    relc = rel[..., None]
    landc = LAND_D + (LAND_L - LAND_D) * np.clip((relc - 0.35) * 1.6, 0, 1)
    oce = OCEAN * (0.55 + 0.9 * relc)
    img = oce * (1 - m) + landc * m
    if fills:
        for name, (col, a) in fills.items():
            if a <= 0.01: continue
            mk = np.zeros((H, W), np.uint8)
            pts = _poly_pts(cam, _rings(cam, name))
            if not pts: continue
            cv2.fillPoly(mk, pts, 255, cv2.LINE_AA, shift=4)
            mm = (mk.astype(np.float32) / 255.0 * a)[..., None]
            img = img * (1 - mm) + (np.array(col, np.float32) * (0.55 + 0.6 * relc)) * mm
    # vignette
    img *= VIG[..., None]
    img *= dim
    fr = np.clip(img, 0, 255).astype(np.uint8)
    if borders:
        bc = (78, 86, 92)
        for name in C:
            pts = _poly_pts(cam, C[name])
            if pts: cv2.polylines(fr, pts, True, bc, 1, cv2.LINE_AA, shift=4)
    if border_hi:
        for name, (col, a) in border_hi.items():
            if a <= 0.02: continue
            pts = _poly_pts(cam, _rings(cam, name))
            if pts:
                ov = fr.copy(); cv2.polylines(ov, pts, True, tuple(int(c) for c in col), 2, cv2.LINE_AA, shift=4)
                cv2.addWeighted(ov, a, fr, 1 - a, 0, fr)
    return fr

_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = np.clip(1.08 - 0.55 * (((_xx - W / 2) / (W * 0.62)) ** 2 + ((_yy - H / 2) / (H * 0.62)) ** 2), 0.45, 1.0).astype(np.float32)
del _yy, _xx

# ---------------- map elements ----------------
def bez(p0, p1, h=0.22, n=80):
    p0, p1 = np.array(p0, np.float32), np.array(p1, np.float32)
    d = p1 - p0; L = float(np.hypot(*d)) + 1e-6
    nrm = np.array([d[1], -d[0]], np.float32) / L
    if nrm[1] > 0: nrm = -nrm  # arc upward
    c = (p0 + p1) / 2 + nrm * L * h
    t = np.linspace(0, 1, n, dtype=np.float32)[:, None]
    return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * c + t * t * p1

def glow_dot(fr, x, y, col, r=6, a=1.0):
    ov = fr.copy()
    cv2.circle(ov, (int(x), int(y)), int(r * 2.6), tuple(int(c) for c in col), -1, cv2.LINE_AA)
    cv2.addWeighted(ov, 0.25 * a, fr, 1 - 0.25 * a, 0, fr)
    cv2.circle(fr, (int(x), int(y)), int(r), tuple(int(c) for c in col), -1, cv2.LINE_AA)
    cv2.circle(fr, (int(x), int(y)), max(1, int(r * 0.45)), (255, 255, 255), -1, cv2.LINE_AA)

def arc(fr, cam, a, b, t, t0, dur=1.2, col=RED, h=0.22, width=3, head=True, fade_after=None):
    p = ease((t - t0) / dur)
    if p <= 0: return False
    pts = bez(cam.p(*a), cam.p(*b), h)
    k = max(2, int(len(pts) * p))
    al = 1.0 if fade_after is None else 1 - ramp(t, fade_after, 0.6)
    if al <= 0: return p >= 1
    ov = fr.copy()
    cv2.polylines(ov, [np.round(pts[:k] * 16).astype(np.int32)], False, tuple(int(c) for c in col), width, cv2.LINE_AA, shift=4)
    cv2.addWeighted(ov, 0.9 * al, fr, 1 - 0.9 * al, 0, fr)
    if head and p < 1: glow_dot(fr, *pts[k - 1], col, 5, al)
    return p >= 1

def flash(fr, cam, lonlat, t, t0, col=RED, size=1.0):
    dt = t - t0
    if dt < 0 or dt > 2.2: return
    x, y = cam.p(*lonlat)
    ov = fr.copy()
    r = int((10 + 70 * eout(dt / 1.1)) * size)
    a = clamp(1 - dt / 1.6)
    cv2.circle(ov, (int(x), int(y)), r, tuple(int(c) for c in col), 3, cv2.LINE_AA)
    if dt < 0.5: cv2.circle(ov, (int(x), int(y)), int(22 * size * (1 - dt)), (255, 230, 200), -1, cv2.LINE_AA)
    cv2.addWeighted(ov, a, fr, 1 - a, 0, fr)

def pin(fr, cam, lonlat, label, t, t0, col=WHITE, dx=18, dy=-14, size=30, anchor="lm", sub=None, pulse=True):
    a = ramp(t, t0, 0.35)
    if a <= 0: return
    x, y = cam.p(*lonlat)
    if pulse:
        ph = ((t - t0) % 1.6) / 1.6
        ov = fr.copy(); cv2.circle(ov, (int(x), int(y)), int(6 + 22 * ph), tuple(int(c) for c in col), 2, cv2.LINE_AA)
        cv2.addWeighted(ov, a * (1 - ph) * 0.8, fr, 1 - a * (1 - ph) * 0.8, 0, fr)
    cv2.circle(fr, (int(x), int(y)), 6, tuple(int(c) for c in col), -1, cv2.LINE_AA)
    cv2.circle(fr, (int(x), int(y)), 6, (20, 20, 20), 1, cv2.LINE_AA)
    if label:
        text(fr, label, x + dx, y + dy, "inter", size, WHITE, 650, a, anchor)
    if sub:
        text(fr, sub, x + dx, y + dy + size * 1.15, "inter", int(size * 0.7), GREY, 500, a, anchor)

def label(fr, cam, lonlat, s, t, t0, size=46, color=WHITE, fname="bebas", track=4, alpha=1.0):
    a = ramp(t, t0, 0.5) * alpha
    if a <= 0: return
    x, y = cam.p(*lonlat)
    text(fr, s, x, y, fname, size, color, 400, a, "cm", track)

def dashed(fr, pts, p, col, width=2, dash=14, gap=10, alpha=1.0):
    """Draw first p fraction of polyline pts as dashes."""
    seg = np.diff(pts, axis=0); L = np.hypot(seg[:, 0], seg[:, 1]); cum = np.concatenate([[0], np.cumsum(L)])
    tot = cum[-1] * p
    ov = fr.copy() if alpha < 1 else fr
    s = 0.0
    while s < tot:
        e = min(s + dash, tot)
        a, b = np.interp(s, cum, pts[:, 0]), np.interp(s, cum, pts[:, 1])
        c, d = np.interp(e, cum, pts[:, 0]), np.interp(e, cum, pts[:, 1])
        cv2.line(ov, (int(a * 16), int(b * 16)), (int(c * 16), int(d * 16)), tuple(int(x) for x in col), width, cv2.LINE_AA, shift=4)
        s += dash + gap
    if alpha < 1: cv2.addWeighted(ov, alpha, fr, 1 - alpha, 0, fr)
    i = np.searchsorted(cum, tot)
    i = min(max(i, 1), len(pts) - 1)
    x, y = np.interp(tot, cum, pts[:, 0]), np.interp(tot, cum, pts[:, 1])
    ang = math.atan2(pts[i, 1] - pts[i - 1, 1], pts[i, 0] - pts[i - 1, 0])
    return x, y, ang

ICONS = {
    "jet": [(1.0, 0), (0.15, 0.12), (-0.1, 0.62), (-0.28, 0.62), (-0.12, 0.12), (-0.62, 0.1), (-0.8, 0.32), (-0.92, 0.32), (-0.82, 0), (-0.92, -0.32), (-0.8, -0.32), (-0.62, -0.1), (-0.12, -0.12), (-0.28, -0.62), (-0.1, -0.62), (0.15, -0.12)],
    "plane": [(1.0, 0), (0.6, 0.08), (0.1, 0.08), (-0.2, 0.7), (-0.35, 0.7), (-0.15, 0.08), (-0.7, 0.08), (-0.85, 0.3), (-0.95, 0.3), (-0.9, 0), (-0.95, -0.3), (-0.85, -0.3), (-0.7, -0.08), (-0.15, -0.08), (-0.35, -0.7), (-0.2, -0.7), (0.1, -0.08), (0.6, -0.08)],
    "ship": [(1.0, 0), (0.6, 0.28), (-0.9, 0.28), (-1.0, 0.18), (-1.0, -0.18), (-0.9, -0.28), (0.6, -0.28)],
    "carrier": [(1.0, 0.1), (0.8, 0.32), (-1.0, 0.32), (-1.0, -0.26), (0.7, -0.32), (1.0, -0.12)],
    "drone": [(1.0, 0), (-0.6, 0.55), (-0.35, 0), (-0.6, -0.55)],
    "missile": [(1.0, 0), (0.7, 0.1), (-0.8, 0.1), (-1.0, 0.3), (-1.0, -0.3), (-0.8, -0.1), (0.7, -0.1)],
}

def icon(fr, kind, x, y, ang, size=22, col=WHITE, alpha=1.0, outline=(15, 15, 15)):
    pts = np.array(ICONS[kind], np.float32) * size
    c, s = math.cos(ang), math.sin(ang)
    R = np.array([[c, -s], [s, c]], np.float32)
    P = pts @ R.T + np.array([x, y], np.float32)
    P = np.round(P * 16).astype(np.int32)
    ov = fr.copy() if alpha < 1 else fr
    cv2.fillPoly(ov, [P], tuple(int(v) for v in col), cv2.LINE_AA, shift=4)
    cv2.polylines(ov, [P], True, outline, 1, cv2.LINE_AA, shift=4)
    if alpha < 1: cv2.addWeighted(ov, alpha, fr, 1 - alpha, 0, fr)

def route(fr, cam, way, t, t0, dur, kind="jet", col=WHITE, size=20, curve=0.0, dash=True, icon_alpha=1.0, line_alpha=0.85):
    p = ease((t - t0) / dur)
    if p <= 0: return
    pts = bez(cam.p(*way[0]), cam.p(*way[-1]), curve) if len(way) == 2 else np.array([cam.p(*w) for w in way], np.float32)
    x, y, ang = dashed(fr, pts, p, col, 2, alpha=line_alpha)
    if kind and icon_alpha > 0: icon(fr, kind, x, y, ang, size, col, icon_alpha)

# ---------------- screen cards ----------------
def bar(fr, x, y, w, h, col, alpha=1.0):
    x, y, w, h = int(x), int(y), int(w), int(h)
    if w <= 0 or h <= 0: return
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x0 >= x1 or y0 >= y1: return
    reg = fr[y0:y1, x0:x1].astype(np.float32)
    fr[y0:y1, x0:x1] = (reg * (1 - alpha) + np.array(col, np.float32) * alpha).astype(np.uint8)

def shade(fr, x, y, w, h, a=0.55):
    bar(fr, x, y, w, h, (0, 0, 0), a)

def datecard(fr, t, t0, big, small=None, x=110, y=760, col=ORANGE, t1=None):
    """Large date card that types on. Hold it 2-3 s (style guide)."""
    if t < t0: return
    a = ramp(t, t0, 0.25) * (1 - (ramp(t, t1, 0.4) if t1 else 0))
    n = int(len(big) * clamp((t - t0) / 0.6)) or 1
    s = big[:n]
    bar(fr, x - 26, y + 14, 10, 118, col, a)
    text(fr, s, x, y, "bebas", 132, WHITE, 400, a, "lt", 3)
    if small:
        text(fr, small, x + 4, y + 142, "inter", 34, GREY, 600, a * ramp(t, t0 + 0.5, 0.4))

def lower(fr, t, t0, big, small=None, x=110, y=870, col=ORANGE, t1=None, size=76):
    if t < t0: return
    a = ramp(t, t0, 0.35) * (1 - (ramp(t, t1, 0.35) if t1 else 0))
    dx = (1 - eout((t - t0) / 0.5)) * -40
    bar(fr, x - 26 + dx, y + 8, 8, size * 0.9, col, a)
    text(fr, big, x + dx, y, "bebas", size, WHITE, 400, a, "lt", 2)
    if small: text(fr, small, x + 2 + dx, y + size * 1.02, "inter", 30, GREY, 600, a)

def source_tag(fr, s, t, t0, x=W - 60, y=H - 50, alpha=1.0):
    text(fr, s, x, y, "inter", 22, (190, 194, 198), 500, ramp(t, t0, 0.4) * alpha, "rb", 0)

def counter(fr, t, t0, value, prefix="", suffix="", lab="", src="", x=W / 2, y=440, dur=1.2, col=WHITE, size=230, t1=None, decimals=0):
    """A number that counts up. Keep the precision of the source: decimals=1 shows 20.7, not 21."""
    if t < t0: return
    a = ramp(t, t0, 0.3) * (1 - (ramp(t, t1, 0.35) if t1 else 0))
    v = value * eout((t - t0) / dur)
    s = f"{prefix}{v:,.{decimals}f}{suffix}"
    text(fr, s, x, y, "bebas", size, col, 400, a, "cm", 2)
    if lab: text(fr, lab, x, y + size * 0.62, "bebas", 64, WHITE, 400, a * ramp(t, t0 + 0.3, 0.4), "cm", 3)
    if src: text(fr, src, x, y + size * 0.62 + 64, "inter", 28, GREY, 500, a * ramp(t, t0 + 0.5, 0.4), "cm")

def title(fr, t, t0, s, sub=None, y=H / 2, size=150, col=WHITE, t1=None, track=8):
    if t < t0: return
    a = ramp(t, t0, 0.4) * (1 - (ramp(t, t1, 0.4) if t1 else 0))
    sc = 1.06 - 0.06 * eout((t - t0) / 0.8)
    text(fr, s, W / 2, y, "bebas", int(size * sc), col, 400, a, "cm", track)
    if sub: text(fr, sub, W / 2, y + size * 0.62, "inter", 34, GREY, 600, a * ramp(t, t0 + 0.4, 0.4), "cm")

# clipping card ---------------------------------------------------------
@functools.lru_cache(64)
def _clip_layout(body, src, outlet, width=1060):
    fb = font("serif", 50, 640); fs = font("inter", 24, 600); fo = font("inter", 26, 800)
    words = body.split(); lines = []; cur = []
    for w in words:
        if fb.getlength(" ".join(cur + [w])) > width - 120 and cur: lines.append(cur); cur = [w]
        else: cur.append(w)
    if cur: lines.append(cur)
    lh = 66; hgt = 120 + lh * len(lines) + 80
    return lines, lh, hgt

def clipping(fr, t, t0, body, outlet, src, hl=None, hl_t=None, x=W / 2, y=H / 2, rot=-2.0, t1=None, width=1060):
    """Article clipping on a light card, highlight draws on (style guide)."""
    if t < t0: return
    a = ramp(t, t0, 0.35) * (1 - (ramp(t, t1, 0.35) if t1 else 0))
    lines, lh, hgt = _clip_layout(body, src, outlet, width)
    im = Image.new("RGBA", (width + 80, hgt + 80), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle([46, 52, width + 46, hgt + 52], fill=(0, 0, 0, 170))
    im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(14)))
    d = ImageDraw.Draw(im)
    d.rectangle([40, 40, width + 40, hgt + 40], fill=PAPER + (255,))
    fo = font("inter", 26, 800); fb = font("serif", 50, 640); fs = font("inter", 22, 600)
    d.text((100, 80), outlet.upper(), font=fo, fill=(140, 30, 30, 255))
    d.line([100, 122, width - 20, 122], fill=(200, 196, 186, 255), width=2)
    # highlight
    hp = 0 if hl is None else eout((t - (hl_t if hl_t is not None else t0 + 0.5)) / 1.0)
    hlw = set()
    if hl:
        flat = [w for ln in lines for w in ln]
        hw = hl.split()
        for i in range(len(flat) - len(hw) + 1):
            if [x.strip('".,\'“”’') for x in flat[i:i + len(hw)]] == [x.strip('".,\'“”’') for x in hw]:
                hlw = set(range(i, i + len(hw))); break
    idx = 0; yy = 150
    boxes = []
    for ln in lines:
        xx = 100
        for w in ln:
            wl = fb.getlength(w); sp = fb.getlength(" ")
            if idx in hlw: boxes.append((xx, yy, wl + (sp if idx + 1 in hlw else 0)))
            xx += wl + sp; idx += 1
        yy += lh
    if boxes and hp > 0:
        tot = sum(b[2] for b in boxes); rem = tot * hp
        for bx, by, bw in boxes:
            w = min(bw, rem); rem -= w
            if w > 0: d.rectangle([bx - 4, by + 10, bx + w + 2, by + 60], fill=YELLOW + (255,))
    yy = 150
    for ln in lines:
        d.text((100, yy), " ".join(ln), font=fb, fill=INK + (255,)); yy += lh
    d.text((100, hgt - 20), "Source: " + src, font=fs, fill=(110, 106, 98, 255))
    im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    sc = 1.04 - 0.04 * eout((t - t0) / 0.6)
    if sc != 1: im = im.resize((int(im.width * sc), int(im.height * sc)), Image.BICUBIC)
    blit(fr, np.asarray(im), x, y, a, "cm")

# photo / video --------------------------------------------------------
@functools.lru_cache(16)
def load_img(path):
    im = cv2.imread(path, cv2.IMREAD_COLOR)
    return cv2.cvtColor(im, cv2.COLOR_BGR2RGB)

def kenburns(img, t, T, z0=1.04, z1=1.14, fx=0.5, fy=0.4, desat=0.6, dark=0.85, fit="cover", bg=None):
    h, w = img.shape[:2]
    z = lerp(z0, z1, ease(t / max(T, 0.01)))
    if fit == "cover":
        s = max(W / w, H / h) * z
    else:
        s = min(W / w, H / h) * 0.92 * z
    cx, cy = w * fx, h * fy
    M = np.array([[s, 0, W / 2 - cx * s], [0, s, H / 2 - cy * s]], np.float32)
    if fit == "cover":
        # keep inside image bounds
        M[0, 2] = min(0, max(W - w * s, M[0, 2])); M[1, 2] = min(0, max(H - h * s, M[1, 2]))
    out = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(12, 14, 16))
    o = out.astype(np.float32)
    g = o.mean(axis=2, keepdims=True)
    o = (o * (1 - desat) + g * desat) * dark
    return np.clip(o * VIG[..., None] ** 0.6, 0, 255).astype(np.uint8)

def portrait(img, t, T, side="right", z0=1.0, z1=1.06, fy=0.4):
    """Documentary portrait layout: blurred dark backdrop + photo on one side, feathered edge."""
    h, w = img.shape[:2]
    bg = cv2.GaussianBlur(cv2.resize(img, (W // 4, int(W / 4 * h / w))), (0, 0), 6)
    bg = cv2.resize(bg, (W, int(W * h / w)))
    y0 = max(0, int((bg.shape[0] - H) * fy)); bg = bg[y0:y0 + H]
    if bg.shape[0] < H: bg = cv2.resize(bg, (W, H))
    out = (bg.astype(np.float32) * 0.28)
    z = lerp(z0, z1, ease(t / max(T, .01)))
    ph = int(H * 1.0 * z); pw = int(w * ph / h)
    fg = cv2.resize(img, (pw, ph), interpolation=cv2.INTER_AREA).astype(np.float32)
    x = W - pw + int(40 * (z - 1) * 10) if side == "right" else 0
    x = min(max(x, W // 2 - 200), W - pw // 2) if side == "right" else x
    yy = (H - ph) // 2
    # feather mask on inner edge
    m = np.ones((ph, pw), np.float32)
    f = int(pw * 0.35)
    ramp_ = np.linspace(0, 1, f, dtype=np.float32)
    if side == "right": m[:, :f] *= ramp_[None, :]
    else: m[:, -f:] *= ramp_[::-1][None, :]
    xs0, ys0 = max(x, 0), max(yy, 0); xs1, ys1 = min(x + pw, W), min(yy + ph, H)
    fgc = fg[ys0 - yy:ys1 - yy, xs0 - x:xs1 - x]; mc = m[ys0 - yy:ys1 - yy, xs0 - x:xs1 - x][..., None]
    out[ys0:ys1, xs0:xs1] = out[ys0:ys1, xs0:xs1] * (1 - mc) + fgc * 0.92 * mc
    g = out.mean(axis=2, keepdims=True); out = out * 0.6 + g * 0.4
    return np.clip(out * VIG[..., None] ** 0.5, 0, 255).astype(np.uint8)

class Video:
    """Footage reader. crop=(x0, y0, x1, y1) as fractions of the source frame cuts away borders,
    burned-in captions or redaction boxes before the frame is scaled to fill the screen."""
    def __init__(self, path, start=0.0, crop=None):
        self.path, self.start, self.crop = path, start, crop
        self.cap = None; self.idx = -1; self.last = None
    def frame(self, t):
        if self.cap is None:
            self.cap = cv2.VideoCapture(self.path); self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
            self.cap.set(cv2.CAP_PROP_POS_MSEC, self.start * 1000); self.idx = int(self.start * self.fps) - 1
        want = int((self.start + t) * self.fps)
        while self.idx < want:
            ok, f = self.cap.read()
            if not ok: break
            self.last = f; self.idx += 1
        f = self.last
        if f is None: return np.zeros((H, W, 3), np.uint8)
        f = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
        if self.crop:
            hh, ww = f.shape[:2]; x0, y0, x1, y1 = self.crop
            f = f[int(y0 * hh):int(y1 * hh), int(x0 * ww):int(x1 * ww)]
        h, w = f.shape[:2]; s = max(W / w, H / h)
        f = cv2.resize(f, (int(w * s + 0.5), int(h * s + 0.5)), interpolation=cv2.INTER_LINEAR)
        y0 = (f.shape[0] - H) // 2; x0 = (f.shape[1] - W) // 2
        return f[y0:y0 + H, x0:x0 + W].copy()

def credit(fr, s, alpha=1.0):
    text(fr, s, W - 40, H - 34, "inter", 20, (205, 205, 205), 500, alpha * 0.9, "rb")

def namebar(fr, t, t0, name, line, col=ORANGE):
    lower(fr, t, t0, name, line, x=110, y=830, col=col, size=92)

def grain(fr, seed):
    rng = np.random.default_rng(seed)
    n = rng.normal(0, 4.0, (H // 2, W // 2)).astype(np.float32)
    n = cv2.resize(n, (W, H), interpolation=cv2.INTER_LINEAR)[..., None]
    return np.clip(fr.astype(np.float32) + n, 0, 255).astype(np.uint8)


# ---------------- globe ----------------
@functools.lru_cache(None)
def _world():
    return pickle.load(open(f"{D}/world.pkl", "rb"))

@functools.lru_cache(8)
def _globe_tex(fills_key):
    """Equirectangular world texture (8192x4096): dark relief land, near-black sea, accent fills, borders."""
    r = np.load(f"{D}/world_relief.npy").astype(np.float32)
    r = cv2.GaussianBlur((r - 45) / (252 - 45), (0, 0), 0.8)[..., None]
    th, tw = r.shape[:2]
    sx, sy = tw / 360.0, th / 180.0
    def pts(rings):
        return [np.round(np.stack([(g[:, 0] + 180) * sx, (90 - g[:, 1]) * sy], 1) * 16).astype(np.int32) for g in rings]
    land = np.zeros((th, tw), np.uint8)
    allp = [p for rings in _world().values() for p in pts(rings)]
    cv2.fillPoly(land, allp, 255, cv2.LINE_AA, shift=4)
    m = (land.astype(np.float32) / 255)[..., None]
    img = (OCEAN * (0.55 + 0.9 * r)) * (1 - m) + (LAND_D + (LAND_L - LAND_D) * np.clip((r - 0.35) * 1.6, 0, 1)) * m
    for name, col, a in fills_key:
        if name not in _world(): continue
        mk = np.zeros((th, tw), np.uint8); cv2.fillPoly(mk, pts(_world()[name]), 255, cv2.LINE_AA, shift=4)
        mm = (mk.astype(np.float32) / 255 * a)[..., None]
        img = img * (1 - mm) + (np.array(col, np.float32) * (0.55 + 0.6 * r)) * mm
    img = np.clip(img, 0, 255).astype(np.uint8)
    cv2.polylines(img, allp, True, (78, 86, 92), 1, cv2.LINE_AA, shift=4)
    for name, col, a in fills_key:
        if name in _world(): cv2.polylines(img, pts(_world()[name]), True, tuple(int(c) for c in col), 2, cv2.LINE_AA, shift=4)
    return img

_gy, _gx = np.mgrid[0:H, 0:W].astype(np.float32)

def globe(lon0, lat0, R, fills=None, cx=W / 2, cy=H / 2):
    """Orthographic globe centred on (lon0, lat0) with radius R pixels, lit from the upper left, with an
    atmosphere glow. Pixels per degree at the centre = R * pi / 180, so R = 2580 matches a flat map at s = 45."""
    key = tuple(sorted((k, tuple(v[0]), float(v[1])) for k, v in (fills or {}).items()))
    tex = _globe_tex(key); th, tw = tex.shape[:2]
    X = (_gx - cx) / R; Y = -(_gy - cy) / R
    rho = np.sqrt(X * X + Y * Y); inside = rho < 1.0
    c = np.arcsin(np.clip(rho, 0, 1)); sc, cc = np.sin(c), np.cos(c)
    p0, l0 = math.radians(lat0), math.radians(lon0)
    with np.errstate(invalid="ignore", divide="ignore"):
        lat = np.arcsin(np.clip(cc * math.sin(p0) + np.where(rho > 0, Y * sc * math.cos(p0) / rho, 0), -1, 1))
        lon = l0 + np.arctan2(X * sc, rho * cc * math.cos(p0) - Y * sc * math.sin(p0))
    u = (((np.degrees(lon) + 180) % 360) / 360 * tw).astype(np.float32)
    v = ((90 - np.degrees(lat)) / 180 * th).astype(np.float32)
    img = cv2.remap(tex, u, v, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP).astype(np.float32)
    light = np.clip(0.35 + 0.75 * cc - 0.18 * (X - Y), 0.25, 1.1)[..., None]       # limb darkening + soft key light
    img = img * light
    bg = np.full((H, W, 3), (8, 10, 14), np.float32)
    halo = np.clip(1 - (rho - 1) / 0.08, 0, 1) * (rho >= 1)                        # thin blue atmosphere
    bg += np.array([70, 130, 190], np.float32) * (halo ** 2 * 0.55)[..., None]
    rim = np.clip(1 - np.abs(rho - 1) / 0.012, 0, 1)[..., None]
    a = np.clip((1 - rho) * R / 1.5, 0, 1)[..., None]                               # anti-aliased edge
    out = img * a + bg * (1 - a)
    out = out * (1 - rim * 0.3) + np.array([120, 170, 220], np.float32) * rim * 0.3
    return np.clip(out * VIG[..., None], 0, 255).astype(np.uint8)
