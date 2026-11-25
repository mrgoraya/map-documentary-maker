"""Render the documentary with Python + ffmpeg. Run from the project folder (or set DOC_PROJECT).
  python render.py stills 1 3.0,7.5,12        test frames      -> qa/stills/p1_003.00.png ...
  python render.py sheet 1 [2]                one still every 2 s on contact sheets -> qa/p1_sheet_v01_*.png
  python render.py part 1 [--workers 6]       part 1 with sound -> out/part1_v01.mp4 (then v02 ...)
  python render.py full                       newest take of every part joined -> out/full_v01.mp4
Scenes come from the project's scenes.py (PARTS = {1: [(start, scene), ...], ...}).
Times are seconds inside each part's voice file. A scene at a negative time (a chapter card)
plays before the voice starts. Nothing is ever overwritten: every render gets the next version number."""
import os, sys, re, glob, math, json, argparse, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from project import cfg, root, voice, duration, next_version, parts as text_parts
os.environ["DOC_PROJECT"] = root()
sys.path.insert(0, root())
import numpy as np, cv2
from docukit import W, H, FPS, grain
import scenes as S

C = cfg()
TAIL, XF = float(C["tail"]), float(C["crossfade"])

def span(part):
    """(start, end) of a part in voice time. start < 0 when it opens with a chapter card."""
    return min(0.0, S.PARTS[part][0][0]), duration(voice(part)) + TAIL

def scene_at(part, t):
    L = S.PARTS[part]; end = span(part)[1]
    for i, (st, fn) in enumerate(L):
        nxt = L[i + 1][0] if i + 1 < len(L) else end
        if st <= t < nxt: return i, st, nxt
    return len(L) - 1, L[-1][0], end

def frame(part, t, seed=0):
    L = S.PARTS[part]
    i, st, nx = scene_at(part, t)
    fr = L[i][1](t - st, nx - st)
    if i > 0 and t - st < XF:                      # cross-dissolve from the previous scene
        pst = L[i - 1][0]
        prev = L[i - 1][1](t - pst, st - pst)
        a = (t - st) / XF
        fr = cv2.addWeighted(fr, a, prev, 1 - a, 0)
    return grain(fr, seed)

def save(fr, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cv2.imwrite(path, cv2.cvtColor(fr, cv2.COLOR_RGB2BGR))

def stills(part, times):
    out = []
    for t in times:
        p = f"{root()}/qa/stills/p{part}_{t:06.2f}.png"; save(frame(part, t), p); out.append(p)
    return out

def sheet(part, every=2.0):
    t0, t1 = span(part)
    ims = stills(part, list(np.arange(math.ceil(t0), t1, every)))
    tiles = []
    for p in ims:
        im = cv2.resize(cv2.imread(p), (640, 360), interpolation=cv2.INTER_AREA)
        cv2.putText(im, os.path.basename(p)[:-4], (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2, cv2.LINE_AA)
        tiles.append(im)
    base = next_version(f"{root()}/qa/p{part}_sheet_v{{v}}_01.png").rsplit("_", 1)[0]
    outs = []
    for k in range(0, len(tiles), 12):
        chunk = tiles[k:k + 12]
        while len(chunk) % 3: chunk.append(np.zeros_like(tiles[0]))
        img = np.vstack([np.hstack(chunk[i:i + 3]) for i in range(0, len(chunk), 3)])
        p = f"{base}_{k // 12 + 1:02d}.png"; cv2.imwrite(p, img); outs.append(p)
    print("\n".join(outs))

def _chunk(args):
    part, k, n, tmp = args
    t0, t1 = span(part)
    N = int(round((t1 - t0) * FPS)); a, b = N * k // n, N * (k + 1) // n
    out = f"{tmp}_{k:02d}.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for f in range(a, b):
        p.stdin.write(frame(part, t0 + f / FPS, f).tobytes())
    p.stdin.close(); p.wait()
    return out

# ---------------------------------------------------------------- sound
SR = 48000
def _load(p):
    r = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", p, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.float32).copy()
def _whoosh(rng, d=0.55):
    n = int(SR * d); x = rng.normal(0, 1, n).astype(np.float32)
    f = 0.02 + 0.25 * np.sin(np.pi * np.arange(n) / n) ** 2
    out = np.empty_like(x); y = 0.0
    for i in range(n):
        y += f[i] * (x[i] - y); out[i] = y
    return out * np.sin(np.pi * np.linspace(0, 1, n)) ** 2 * 0.9
def _hit(rng, d=1.6):
    n = int(SR * d); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * (48 + 20 * np.exp(-t * 6)) * t) * np.exp(-t * 2.6) + rng.normal(0, 1, n) * np.exp(-t * 18) * 0.25).astype(np.float32)
db = lambda x: 10 ** (x / 20)

def soundtrack(part, out):
    """Voice (master) + optional soft SFX + optional music bed, loudness-normalised."""
    t0, t1 = span(part); N = int(round((t1 - t0) * SR))
    mix = np.zeros(N, np.float32)
    v = _load(voice(part)); o = int(-t0 * SR)
    mix[o:o + len(v)] += v[:N - o]
    if C["sfx"]:
        rng = np.random.default_rng(5); Wh = _whoosh(rng); Hi = _hit(rng)
        for i, (st, fn) in enumerate(S.PARTS[part]):
            k = int((st - t0 - XF) * SR)
            if i and 0 <= k < N - len(Wh): mix[k:k + len(Wh)] += Wh * db(-30)
        if t0 < 0: mix[:len(Hi)] += Hi * db(-20)
    if C.get("music"):
        m = _load(os.path.join(root(), C["music"]))
        m = np.tile(m, N // len(m) + 1)[:N] * db(-22)
        mix += m
    f = int(0.3 * SR); mix[:f] *= np.linspace(0, 1, f); mix[-f:] *= np.linspace(1, 0, f)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                    "-af", f"loudnorm=I={C['loudness']}:TP=-1.5:LRA=11", "-ar", str(SR), "-ac", "2", out], input=mix.tobytes(), check=True)

def render_part(part, workers):
    from multiprocessing import Pool
    os.makedirs(f"{root()}/out", exist_ok=True)
    final = next_version(f"{root()}/out/part{part}_v{{v}}.mp4")
    tmp = final[:-4] + "_tmp"
    with Pool(workers) as pool:
        outs = pool.map(_chunk, [(part, k, workers, tmp) for k in range(workers)])
    open(tmp + ".txt", "w").write("".join(f"file '{o}'\n" for o in outs))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", tmp + ".txt", "-c", "copy", tmp + "_v.mp4"], check=True)
    soundtrack(part, tmp + "_a.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp + "_v.mp4", "-i", tmp + "_a.wav", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k",
                    "-shortest", "-movflags", "+faststart", final], check=True)
    for p in outs + [tmp + ".txt", tmp + "_v.mp4", tmp + "_a.wav"]: os.remove(p)
    print(final)

def full():
    files = []
    for p in sorted(S.PARTS):
        vs = sorted(glob.glob(f"{root()}/out/part{p}_v*.mp4"), key=lambda f: int(re.findall(r"_v(\d+)\.mp4$", f)[0]))
        if not vs: sys.exit(f"Render part {p} first.")
        files.append(vs[-1])
    final = next_version(f"{root()}/out/full_v{{v}}.mp4")
    lst = final[:-4] + ".txt"
    open(lst, "w").write("".join(f"file '{f}'\n" for f in files))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", final], check=True)
    os.remove(lst)
    print("joined:", ", ".join(os.path.basename(f) for f in files)); print(final)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["stills", "sheet", "part", "full"])
    ap.add_argument("part", nargs="?", type=int); ap.add_argument("arg", nargs="?")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 4) - 2))
    a, extra = ap.parse_known_args()        # stills times may start with "-" (chapter cards before the voice)
    if extra and a.arg is None and re.fullmatch(r"-?[\d.,-]+", extra[0]): a.arg = extra[0]
    elif extra: ap.error(f"unrecognized arguments: {' '.join(extra)}")
    if a.cmd == "stills": print("\n".join(stills(a.part, [float(x) for x in a.arg.split(",")])))
    elif a.cmd == "sheet": sheet(a.part, float(a.arg or 2))
    elif a.cmd == "part": render_part(a.part, a.workers)
    else: full()
