"""Narrate voice/partN.txt with Kokoro (free, open-weight TTS that runs on your own computer).
  python narrate.py all                     every part
  python narrate.py 2 3 --voice bm_george   only parts 2 and 3, another voice
  python narrate.py sample "Text" --voice af_heart   try a voice -> voice/sample_<voice>.wav
Writes voice/partN_v01.wav, then v02, v03 ... Old takes are never overwritten.

Text tips (see references/narration.md): spell out years and numbers the way they should be said
("twenty twenty-six", "February twenty-eighth"), one sentence per line is fine, a blank line = a longer pause.
Voices: am_michael, am_fenrir, am_puck (US male) · af_heart, af_bella (US female) · bm_george, bm_fable (UK male) · bf_emma (UK female)."""
import os, sys, argparse
import numpy as np, soundfile as sf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import cfg, root, parts, next_version

SR = 24000
ap = argparse.ArgumentParser()
ap.add_argument("what", nargs="+", help='"all", part numbers, or: sample "text"')
ap.add_argument("--voice"); ap.add_argument("--speed", type=float)
a = ap.parse_args()

c = cfg()
voice = a.voice or c["voice"]; speed = a.speed or c["speed"]
from kokoro import KPipeline
pipe = KPipeline(lang_code=voice[0], repo_id="hexgrad/Kokoro-82M")

def speak(paras):
    out = [np.zeros(int(SR * 0.15), np.float32)]
    for p in paras:
        for _, _, audio in pipe(p, voice=voice, speed=speed, split_pattern=None):
            out.append(audio.numpy() if hasattr(audio, "numpy") else np.asarray(audio))
        out.append(np.zeros(int(SR * 0.35), np.float32))
    wav = np.concatenate(out)
    return wav / max(1e-6, np.abs(wav).max()) * 0.89

vd = os.path.join(root(), "voice"); os.makedirs(vd, exist_ok=True)
if a.what[0] == "sample":
    p = os.path.join(vd, f"sample_{voice}.wav")
    sf.write(p, speak([" ".join(a.what[1:])]), SR); print(p); sys.exit()

todo = parts() if a.what == ["all"] else [int(x) for x in a.what]
for n in todo:
    src = os.path.join(vd, f"part{n}.txt")
    paras = [p.strip().replace("\n", " ") for p in open(src).read().split("\n\n") if p.strip()]
    wav = speak(paras)
    out = next_version(os.path.join(vd, f"part{n}_v{{v}}.wav"))
    sf.write(out, wav, SR)
    print(f"part {n}: {len(wav) / SR:.1f}s  {voice} x{speed}  -> {out}")
