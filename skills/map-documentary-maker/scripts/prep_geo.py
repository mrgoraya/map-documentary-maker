"""Cut the map data for this project's bounding box (project.json "bbox").
Writes data/countries.pkl (two detail levels), data/relief.npy and data/relief.json.
Run once per project, and again if you change the bbox."""
import os, sys, json, pickle, math
import numpy as np, geopandas as gpd, rasterio
from rasterio.windows import from_bounds
from rasterio.enums import Resampling
from shapely.geometry import box
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import cfg, root, CACHE

c = cfg(); BB = tuple(c["bbox"]); PX = float(c["relief_px_per_deg"])
D = os.path.join(root(), "data"); os.makedirs(D, exist_ok=True)
NE = os.path.join(CACHE, "ne")

g = gpd.read_file(f"{NE}/ne_10m_admin_0_countries/ne_10m_admin_0_countries.shp")
g = g[g.intersects(box(*BB))].copy()
g["geometry"] = g.geometry.intersection(box(*BB).buffer(2))
out = {}
for lod, tol in (("fine", 0.002), ("coarse", 0.03)):
    d = {}
    for _, r in g.iterrows():
        geom = r.geometry.simplify(tol, preserve_topology=True)
        polys = [geom] if geom.geom_type == "Polygon" else list(getattr(geom, "geoms", []))
        rings = [np.asarray(p.exterior.coords, dtype=np.float32) for p in polys if p.geom_type == "Polygon" and p.area > tol * tol * 4]
        if rings: d[r["ADMIN"]] = rings
    out[lod] = d
pickle.dump(out, open(f"{D}/countries.pkl", "wb"))

with rasterio.open(f"{NE}/GRAY_HR_SR_OB_DR/GRAY_HR_SR_OB_DR.tif") as src:
    win = from_bounds(*BB, transform=src.transform)
    native = 1.0 / src.transform.a
    shape = (int(round((BB[3] - BB[1]) * PX)), int(round((BB[2] - BB[0]) * PX)))
    a = src.read(1, window=win, out_shape=shape, resampling=Resampling.bilinear) if abs(native - PX) > 0.5 else src.read(1, window=win)
np.save(f"{D}/relief.npy", a)
json.dump({"lon0": BB[0], "lat1": BB[3], "px_per_deg": a.shape[1] / (BB[2] - BB[0]), "cos_lat": c.get("cos_lat") or round((BB[1] + BB[3]) / 2, 1)},
          open(f"{D}/relief.json", "w"), indent=2)
print(f"{len(out['fine'])} countries, relief {a.shape} -> {D}")
print("Country names (use these exact names in fills):", ", ".join(sorted(out["fine"])[:60]), "...")

# World layer for the opening globe: coarse borders of every country + a 8192x4096 relief texture
gw = gpd.read_file(f"{NE}/ne_10m_admin_0_countries/ne_10m_admin_0_countries.shp")
world = {}
for _, r in gw.iterrows():
    geom = r.geometry.simplify(0.04, preserve_topology=True)
    polys = [geom] if geom.geom_type == "Polygon" else list(getattr(geom, "geoms", []))
    rings = [np.asarray(p.exterior.coords, dtype=np.float32) for p in polys if p.geom_type == "Polygon" and p.area > 0.01]
    if rings: world[r["ADMIN"]] = rings
pickle.dump(world, open(f"{D}/world.pkl", "wb"))
with rasterio.open(f"{NE}/GRAY_HR_SR_OB_DR/GRAY_HR_SR_OB_DR.tif") as src:
    wr = src.read(1, out_shape=(4096, 8192), resampling=Resampling.average)
np.save(f"{D}/world_relief.npy", wr)
print(f"globe layer: {len(world)} countries, relief {wr.shape}")
