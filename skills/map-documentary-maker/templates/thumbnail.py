"""Thumbnail in the documentary style: the story's map as the key visual, darkened on the text side,
a 3-5 word title in Bebas Neue, one accent tag. Copy into the project and edit.
  python thumbnail.py  -> out/thumbnail_v01.png (1280x720) + _phone.png (320x180, the size most people see)
Check the phone version: if the title is not readable there, make it shorter or bigger."""
import os, sys
SKILL_SCRIPTS = "__SKILL_SCRIPTS__"          # filled in by new_project.py
os.environ.setdefault("DOC_PROJECT", os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SKILL_SCRIPTS)
from docukit import *
from project import next_version

LINE1, LINE2, TAG = "THE IRAN WAR", "EXPLAINED", "FEB–NOV 2026"
cam = Cam(48.8, 29.5, 72)
fr = basemap(cam, {"Iran": (TEAL, 0.55)}, 1.0, True, {"Iran": (TEAL, 1)})
for i, tg in enumerate([(50.61, 26.21), (51.53, 25.29), (54.37, 24.45)]):
    arc(fr, cam, (54.6 - i * 0.5, 32.3), tg, 9, 0, 1, RED, 0.22, 5, head=False)
    glow_dot(fr, *cam.p(*tg), RED, 9)

# darken the left side smoothly so the title reads (no visible seam)
xx = np.arange(W, dtype=np.float32)[None, :, None]; yy = np.arange(H, dtype=np.float32)[:, None, None]
fr = np.clip(fr.astype(np.float32) * np.clip(0.18 + 0.82 * (xx / (W * 0.57)) ** 1.5, 0, 1) * np.clip(1.15 - 0.5 * (yy / H), 0.6, 1), 0, 255).astype(np.uint8)

text(fr, LINE1, 70, 430, "bebas", 210, WHITE, 400, 1, "lt", 4)
text(fr, LINE2, 74, 640, "bebas", 210, YELLOW, 400, 1, "lt", 4)
tw = text_w(TAG, "bebas", 84) + 3 * len(TAG)
bar(fr, 78, 880, tw + 44, 96, RED, 1)
text(fr, TAG, 100, 884, "bebas", 84, WHITE, 400, 1, "lt", 3, shadow=False)

out = next_version(f"{ROOT}/out/thumbnail_v{{v}}.png")
os.makedirs(os.path.dirname(out), exist_ok=True)
cv2.imwrite(out, cv2.cvtColor(cv2.resize(fr, (1280, 720), interpolation=cv2.INTER_AREA), cv2.COLOR_RGB2BGR))
cv2.imwrite(out[:-4] + "_phone.png", cv2.cvtColor(cv2.resize(fr, (320, 180), interpolation=cv2.INTER_AREA), cv2.COLOR_RGB2BGR))
print(out)
