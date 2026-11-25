"""Honest charts. Rule: plot ONLY the data points you have a source for.
Where you have no data between two points, the line is dashed and labelled, never smoothed or invented."""
import numpy as np, cv2
from .engine import *

def line_chart(fr, t, points, title_s, source_s, vmin, vmax, x0=360, x1=1560, y0=800, y1=420,
               col=ORANGE, gap_note="Dashed: values in between not shown", t0=0.3, draw_dur=3.6):
    """points: list of dicts {x: 0..1 position along the time axis, v: value, label: "$100.46", sub: "12 MAR",
    gap_before: True if there is no sourced data between the previous point and this one}."""
    yv = lambda v: lerp(y0, y1, (v - vmin) / (vmax - vmin))
    pts = [(x0 + (x1 - x0) * p["x"], yv(p["v"])) for p in points]
    cv2.line(fr, (x0 - 40, y0 + 20), (x1 + 40, y0 + 20), (70, 74, 78), 2, cv2.LINE_AA)
    n = len(pts) - 1
    tot = n * ease((t - t0) / draw_dur)
    for i in range(n):
        q = clamp(tot - i)
        if q <= 0: break
        A_, B_ = np.array(pts[i]), np.array(pts[i + 1]); C_ = A_ + (B_ - A_) * q
        if points[i + 1].get("gap_before"):
            dashed(fr, np.array([A_, C_], np.float32), 1.0, col, 3, 12, 10)
        else:
            cv2.line(fr, (int(A_[0]), int(A_[1])), (int(C_[0]), int(C_[1])), col, 5, cv2.LINE_AA)
    step = draw_dur / max(n, 1)
    for i, p in enumerate(points):
        a = ramp(t, t0 + i * step, .3)
        if a <= 0: continue
        x, y = pts[i]; glow_dot(fr, x, y, col, 6, a)
        text(fr, p.get("label", ""), x, y - 54, "bebas", 60, WHITE, 400, a, "cb")
        if p.get("sub"): text(fr, p["sub"], x, y - 24, "inter", 22, GREY, 600, a, "cb")
    gaps = [i for i, p in enumerate(points) if p.get("gap_before")]
    if gaps:
        i = gaps[0]
        text(fr, gap_note, (pts[i - 1][0] + pts[i][0]) / 2, (pts[i - 1][1] + pts[i][1]) / 2 + 40, "inter", 22, GREY, 500, ramp(t, t0 + 1.3, .4), "ct")
    text(fr, title_s, x0 - 40, 150, "bebas", 64, WHITE, 400, ramp(t, 0.1, .4), "lt", 3)
    text(fr, source_s, x0 - 40, 225, "inter", 26, GREY, 500, ramp(t, 0.4, .4), "lt")

def split_bar(fr, t, left, right, total, needed=None, head=None, sub=None, source_s="",
              left_col=ORANGE, right_col=TEAL, x0=300, x1=1620, y=470):
    """Two sides of one total, e.g. seats in a parliament: left=("NETANYAHU BLOC", 53), right=("OPPOSITION", 48), total=120, needed=61.
    Use this instead of colouring a map when the result is not regional."""
    if head: text(fr, head, W / 2, 190, "bebas", 90, WHITE, 400, ramp(t, 0.1, .4), "cm", 4)
    if sub: text(fr, sub, W / 2, 280, "inter", 36, GREY, 600, ramp(t, 0.4, .4), "cm")
    p = eout((t - 0.6) / 1.2); w = x1 - x0
    bar(fr, x0, y, w, 90, (40, 44, 48), 1)
    bar(fr, x0, y, w * left[1] / total * p, 90, left_col, 1)
    bar(fr, x1 - w * right[1] / total * p, y, w * right[1] / total * p, 90, right_col, 1)
    if needed:
        xm = x0 + w * needed / total; a = ramp(t, 1.6, .4)
        ov = fr.copy(); cv2.line(ov, (int(xm), y - 40), (int(xm), y + 130), WHITE, 3, cv2.LINE_AA); cv2.addWeighted(ov, a, fr, 1 - a, 0, fr)
        text(fr, f"{needed} NEEDED", xm, y + 150, "bebas", 48, WHITE, 400, a, "ct", 2)
    text(fr, f"{left[0]} {left[1]}", x0, y - 20, "bebas", 52, left_col, 400, ramp(t, 0.9, .4), "lb", 2)
    text(fr, f"{right[0]} {right[1]}", x1, y - 20, "bebas", 52, right_col, 400, ramp(t, 0.9, .4), "rb", 2)
    if source_s: text(fr, source_s, W / 2, 760, "inter", 28, GREY, 500, ramp(t, 1.2, .4), "cm")

def board(fr, t, rows, head, source_s="", num_x=None, desc_x=None, y0=300, gap=110, col=RED):
    """A toll/figures board: rows = [("3,400+", "killed in Iran, per the health ministry"), ...].
    Numbers right-aligned in one column, text left-aligned in the next, so rows never collide."""
    num_x = num_x or int(W * 0.635); desc_x = desc_x or num_x + 40
    text(fr, head, W / 2, 170, "bebas", 90, WHITE, 400, ramp(t, 0.1, .4), "cm", 4)
    for i, (num, desc) in enumerate(rows):
        a = ramp(t, 0.5 + i * 0.5, .35); y = y0 + i * gap
        text(fr, num, num_x, y, "bebas", 84, col, 400, a, "rm", 2)
        text(fr, desc, desc_x, y, "inter", 34, WHITE, 500, a, "lm")
    if source_s: text(fr, source_s, W / 2, H - 90, "inter", 24, GREY, 500, ramp(t, 1.0, .4), "cm")
