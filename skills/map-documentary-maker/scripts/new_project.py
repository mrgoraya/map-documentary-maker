"""Create a documentary project folder.
  python new_project.py <folder> "<title>" [--bbox lon0 lat0 lon1 lat1] [--vertical]
Makes project.json, scenes.py (starter), thumbnail.py, YOUTUBE.md, voice/, assets/, research/, out/, qa/."""
import os, sys, json, shutil, argparse
HERE = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(os.path.dirname(HERE), "templates")

ap = argparse.ArgumentParser()
ap.add_argument("folder"); ap.add_argument("title")
ap.add_argument("--bbox", nargs=4, type=float, default=[-12, 0, 82, 54], help="map area: lon0 lat0 lon1 lat1 (default: Middle East + Europe)")
ap.add_argument("--vertical", action="store_true", help="9:16 (1080x1920) for Shorts/Reels")
a = ap.parse_args()

d = os.path.abspath(a.folder)
if os.path.exists(os.path.join(d, "project.json")):
    sys.exit(f"{d} already has a project.json; nothing changed.")
for sub in ("voice", "assets", "research", "out", "qa", "data"):
    os.makedirs(os.path.join(d, sub), exist_ok=True)
cfg = {"title": a.title, "width": 1080 if a.vertical else 1920, "height": 1920 if a.vertical else 1080, "fps": 30,
       "bbox": a.bbox, "relief_px_per_deg": 60, "voice": "am_michael", "speed": 1.0,
       "tail": 0.6, "crossfade": 0.25, "loudness": -15, "sfx": True, "music": None}
json.dump(cfg, open(os.path.join(d, "project.json"), "w"), indent=2)
shutil.copy(os.path.join(TPL, "scenes.py"), os.path.join(d, "scenes.py"))
shutil.copy(os.path.join(TPL, "YOUTUBE.md"), os.path.join(d, "YOUTUBE.md"))
open(os.path.join(d, "thumbnail.py"), "w").write(open(os.path.join(TPL, "thumbnail.py")).read().replace("__SKILL_SCRIPTS__", HERE))
print("Project ready:", d)
print("Next: python prep_geo.py   (with DOC_PROJECT set to the folder, or run from inside it)")
