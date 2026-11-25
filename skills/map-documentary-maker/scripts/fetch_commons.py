"""Find and download free-licence photos and video from Wikimedia Commons, with their credits.
  python fetch_commons.py search "Strait of Hormuz navy 2026" [--limit 12] [--video]
  python fetch_commons.py get "File:Some photo.jpg" p_name        -> assets/p_name.jpg + credits.json entry
  python fetch_commons.py credits                                  -> credits.txt for the video description
Naming: p_* = a person (portrait layout), i_* = an image, v_* = video.
Only files with a licence that allows reuse (public domain, CC0, CC BY, CC BY-SA) are downloaded.
Commons rate-limits scripts: this tool waits between calls and backs off on HTTP 429."""
import os, sys, json, time, re, html, argparse
import requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import root

API = "https://commons.wikimedia.org/w/api.php"
UA = "map-documentary-maker/1.0 (open-source Claude Code skill; https://github.com/mrgoraya/map-documentary-maker)"
S = requests.Session(); S.headers["User-Agent"] = UA
OK = re.compile(r"public domain|^pd|cc0|cc[- ]by(?![- ]?nc)(?![- ]?nd)", re.I)

def call(params, tries=6):
    params = dict(params, format="json", formatversion=2)
    for i in range(tries):
        r = S.get(API, params=params, timeout=60)
        if r.status_code == 429 or r.status_code >= 500:
            wait = int(r.headers.get("Retry-After", 0)) or 10 * (i + 1); print(f"  Commons busy, waiting {wait}s"); time.sleep(wait); continue
        r.raise_for_status(); time.sleep(1.5); return r.json()
    sys.exit("Commons kept refusing; try again in a few minutes.")

def clean(s): return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()

def info(title, width=1920):
    j = call({"action": "query", "titles": title, "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata|mediatype",
              "iiurlwidth": width})
    pg = j["query"]["pages"][0]
    if "imageinfo" not in pg: return None
    ii = pg["imageinfo"][0]; md = ii.get("extmetadata", {})
    g = lambda k: clean(md.get(k, {}).get("value"))
    return {"title": pg["title"], "url": ii["url"], "thumb": ii.get("thumburl"), "mime": ii["mime"], "w": ii.get("width"), "h": ii.get("height"),
            "size": ii.get("size"), "license": g("LicenseShortName"), "artist": g("Artist"), "credit": g("Credit"),
            "date": g("DateTimeOriginal") or g("DateTime"), "desc": g("ImageDescription")[:160],
            "page": "https://commons.wikimedia.org/wiki/" + pg["title"].replace(" ", "_")}

def search(q, limit, video):
    ft = "filetype:video" if video else "filetype:bitmap"
    j = call({"action": "query", "list": "search", "srsearch": f"{q} {ft}", "srnamespace": 6, "srlimit": limit})
    for hit in j["query"]["search"]:
        i = info(hit["title"])
        if not i: continue
        flag = "OK " if OK.search(i["license"] or "") else "NO "
        print(f"{flag}{i['title']}\n    {i['w']}x{i['h']} {i['mime']} · {i['license']} · {i['artist'][:50]} · {i['date'][:20]}\n    {i['desc']}\n")

def get(title, name):
    i = info(title)
    if not i: sys.exit(f"Not found: {title}")
    if not OK.search(i["license"] or ""):
        sys.exit(f"Licence '{i['license']}' does not allow reuse; pick another file.")
    vid = i["mime"].startswith("video")
    if vid:
        # Commons serves smaller transcodes next to the original: /transcoded/<path>/<name>.1080p.vp9.webm
        orig = i["url"].split("?")[0]                       # Commons adds tracking parameters; drop them
        url = orig.replace("/commons/", "/commons/transcoded/", 1) + "/" + orig.rsplit("/", 1)[1] + ".1080p.vp9.webm"
        ext = "webm"
        tries = [url, url.replace(".1080p.", ".720p."), orig if (i["size"] or 0) < 400e6 else None]
    else:
        url = (i["thumb"] if i["thumb"] and (i["w"] or 0) > 1920 else i["url"]).split("?")[0]
        ext = url.rsplit(".", 1)[-1].lower().replace("jpeg", "jpg")
        tries = [url]
    os.makedirs(f"{root()}/assets", exist_ok=True)
    out = f"{root()}/assets/{name}.{ext}"
    tries = [u for u in tries if u]; k = 0
    while tries and k < 8:
        url = tries[0]; k += 1
        r = S.get(url, timeout=300, stream=True)
        if r.status_code == 404:
            tries.pop(0); continue                           # this size isn't available, try the next one
        if r.status_code == 429:
            time.sleep(15 * k); continue
        r.raise_for_status()
        with open(out, "wb") as f:
            for ch in r.iter_content(1 << 16): f.write(ch)
        break
    else:
        sys.exit("Download kept failing; try again later.")
    cp = f"{root()}/assets/credits.json"
    cr = json.load(open(cp)) if os.path.exists(cp) else []
    cr = [c for c in cr if c["file"].split(".")[0] != name]
    cr.append({"file": os.path.basename(out), "title": i["title"], "license": i["license"], "artist": i["artist"],
               "credit": i["credit"], "date": i["date"], "page": i["page"], "source": "Wikimedia Commons"})
    json.dump(cr, open(cp, "w"), indent=1)
    print(f"{out}  ({os.path.getsize(out) // 1024} KB) · {i['license']} · {i['artist'][:60]}")

def credits():
    cp = f"{root()}/assets/credits.json"
    lines = [f"- {c['file']}: {c['artist'] or 'Unknown'} · {c['license']} · {c['page']}" for c in json.load(open(cp))]
    open(f"{root()}/credits.txt", "w").write("Photos and footage via Wikimedia Commons\n" + "\n".join(lines) + "\n")
    print("\n".join(lines))

ap = argparse.ArgumentParser()
ap.add_argument("cmd", choices=["search", "get", "credits"]); ap.add_argument("args", nargs="*")
ap.add_argument("--limit", type=int, default=10); ap.add_argument("--video", action="store_true")
a = ap.parse_args()
if a.cmd == "search": search(" ".join(a.args), a.limit, a.video)
elif a.cmd == "get": get(a.args[0] if a.args[0].startswith("File:") else "File:" + a.args[0], a.args[1])
else: credits()
