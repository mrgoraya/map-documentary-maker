"""Shared helpers for the pipeline scripts: project settings, voice takes, part lengths."""
import os, re, json, glob, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.expanduser(os.environ.get("DOC_CACHE", "~/.cache/map-documentary-maker"))

DEFAULTS = {
    "title": "Untitled documentary",
    "width": 1920, "height": 1080, "fps": 30,
    "bbox": [-12, 0, 82, 54],          # lon0, lat0, lon1, lat1 of every map in the film
    "relief_px_per_deg": 60,
    "voice": "am_michael", "speed": 1.0,
    "tail": 0.6,                        # seconds of picture after the last word of each part
    "crossfade": 0.25,                  # dissolve between scenes
    "loudness": -15,                    # LUFS of the final mix
    "sfx": True,                        # soft whoosh on cuts + low hit under chapter cards
    "music": None,                      # optional path to a music bed (ducked about 20 dB under the voice)
}

def root():
    return os.path.abspath(os.environ.get("DOC_PROJECT", os.getcwd()))

def cfg():
    p = os.path.join(root(), "project.json")
    if not os.path.exists(p):
        sys.exit(f"No project.json in {root()}. Run new_project.py first or set DOC_PROJECT.")
    c = dict(DEFAULTS); c.update(json.load(open(p)))
    return c

def parts():
    """Part numbers that have a narration text file: voice/part1.txt, voice/part2.txt ..."""
    fs = glob.glob(os.path.join(root(), "voice", "part*.txt"))
    return sorted(int(re.findall(r"part(\d+)\.txt$", f)[0]) for f in fs)

def takes(part):
    fs = glob.glob(os.path.join(root(), "voice", f"part{part}_v*.wav"))
    return sorted(fs, key=lambda f: int(re.findall(r"_v(\d+)\.wav$", f)[0]))

def voice(part):
    """The voice file for a part: project.json "voice_takes": {"1": "part1_v2.wav"} pins one,
    otherwise the newest take is used."""
    pin = cfg().get("voice_takes", {}).get(str(part))
    if pin: return os.path.join(root(), "voice", pin)
    t = takes(part)
    if not t: sys.exit(f"No voice for part {part}. Run narrate.py {part} (or put your own recording at voice/part{part}_v1.wav).")
    return t[-1]

def duration(path):
    import soundfile as sf
    return sf.info(path).duration

def next_version(pattern):
    """pattern with {v}: returns the first path that does not exist yet (v01, v02, ...). Nothing is overwritten."""
    v = 1
    while os.path.exists(pattern.format(v=f"{v:02d}")): v += 1
    return pattern.format(v=f"{v:02d}")
