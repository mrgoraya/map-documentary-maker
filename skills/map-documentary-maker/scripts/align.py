"""Voiceover analysis: transcribe each part's voice with word timestamps, check it against the script,
and time every script sentence. The voice is the master clock for the whole edit.
  python align.py all [--model large-v3-turbo]
Writes voice/partN_vXX_words.json and sentences.json, and prints:
  - each part's exact length
  - script words the voice skipped or changed (numbers are compared loosely: "28" = "twenty-eighth")
Whisper sometimes "hears" words in silence at the end of a file. If the report lists extra words in a
quiet stretch, check the loudness there before re-recording (see references/narration.md)."""
import os, re, sys, json, argparse, difflib, subprocess
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import root, parts, voice, duration

ap = argparse.ArgumentParser()
ap.add_argument("what", nargs="+"); ap.add_argument("--model", default="large-v3-turbo"); ap.add_argument("--lang", default="en")
a = ap.parse_args()

from faster_whisper import WhisperModel
model = WhisperModel(a.model, device="auto", compute_type="int8")

NUMW = set("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty thirty forty fifty sixty seventy eighty ninety hundred thousand million billion first second third fourth fifth sixth seventh eighth ninth tenth eleventh twelfth thirteenth fourteenth fifteenth sixteenth seventeenth eighteenth nineteenth twentieth thirtieth".split())
def norm(w):
    w = w.lower().replace("’", "'")
    w = re.sub(r"[^a-z0-9'%$-]", "", w).strip("-'")
    return w
def tokens(text):
    out = []
    for w in text.split():
        for x in re.split(r"(?<=[a-z])-(?=[a-z])", norm(w)):
            if x: out.append("#" if (any(ch.isdigit() for ch in x) or x in NUMW or x.rstrip("s") in NUMW) else x)
    return out
def sentences(text):
    text = " ".join(l.strip() for l in text.splitlines() if l.strip())
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z\"“])", text) if s.strip()]

todo = parts() if a.what == ["all"] else [int(x) for x in a.what]
sent_out = []
sp = os.path.join(root(), "sentences.json")
if os.path.exists(sp):
    sent_out = [s for s in json.load(open(sp)) if s["part"] not in todo]
for n in todo:
    wav = voice(n)
    pcm = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", wav, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
                         capture_output=True, check=True).stdout          # decode with ffmpeg (avoids PyAV version clashes)
    segs, _ = model.transcribe(np.frombuffer(pcm, np.float32), language=a.lang, word_timestamps=True, vad_filter=False, beam_size=5)
    words = [{"w": w.word.strip(), "s": round(w.start, 2), "e": round(w.end, 2)} for s in segs for w in s.words]
    dur = duration(wav)
    json.dump({"duration": round(dur, 3), "words": words}, open(wav[:-4] + "_words.json", "w"), indent=1)

    script = open(os.path.join(root(), "voice", f"part{n}.txt")).read()
    sents = sentences(script)
    st_tok, owner = [], []
    for i, s in enumerate(sents):
        tk = tokens(s); st_tok += tk; owner += [i] * len(tk)
    vt, vidx = [], []
    for j, w in enumerate(words):
        for x in tokens(w["w"]): vt.append(x); vidx.append(j)
    sm = difflib.SequenceMatcher(a=st_tok, b=vt, autojunk=False)
    m = {}
    issues = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1): m[i1 + k] = vidx[j1 + k]
        elif tag == "replace" and (i2 - i1) == (j2 - j1):
            for k in range(i2 - i1): m[i1 + k] = vidx[j1 + k]
            if any(st_tok[i1 + k] != "#" and vt[j1 + k] != "#" for k in range(i2 - i1)):
                issues.append(f"changed: script '{' '.join(st_tok[i1:i2])}' -> voice '{' '.join(vt[j1:j2])}' at {words[vidx[j1]]['s']:.1f}s")
        else:
            if tag in ("delete", "replace") and any(x != "#" for x in st_tok[i1:i2]):
                issues.append(f"missing in voice: '{' '.join(st_tok[i1:i2])}' (sentence {owner[i1] + 1})")
            if tag in ("insert", "replace") and any(x != "#" for x in vt[j1:j2]):
                issues.append(f"extra in voice: '{' '.join(vt[j1:j2])}' at {words[vidx[j1]]['s']:.1f}s")
    for i, s in enumerate(sents):
        ks = [k for k in range(len(owner)) if owner[k] == i and k in m]
        if ks:
            sent_out.append({"part": n, "k": i, "s": words[m[ks[0]]]["s"], "e": words[m[ks[-1]]]["e"], "text": s})
        else:
            sent_out.append({"part": n, "k": i, "s": None, "e": None, "text": s})
    print(f"\nPART {n}: {dur:.2f}s  ({os.path.basename(wav)}, {len(words)} words)")
    print("  matches the script" if not issues else "\n".join("  - " + x for x in issues))
sent_out.sort(key=lambda s: (s["part"], s["k"]))
json.dump(sent_out, open(sp, "w"), indent=1)
print(f"\nSentence timings -> {sp}. Time your scenes from these.")
