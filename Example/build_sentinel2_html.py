"""
Build a standalone sentinel2.html — Sentinel-2 cloud-free median composite,
Thailand, year 2026, on a Google Satellite basemap.

GEE Cloud Project: tidy-nomad-470808-e1

First-time setup (once per machine):
    earthengine authenticate
    (or just run this script — ee.Authenticate() will open a browser
    login prompt automatically on first run)

Run:
    python build_sentinel2_html.py
Output:
    Example/sentinel2.html
"""

import os

import ee
import folium

PROJECT_ID = "tidy-nomad-470808-e1"
OUTPUT_HTML = os.path.join(os.path.dirname(__file__), "sentinel2.html")
CLOUD_PROB_THRESHOLD = 40  # 0-100, lower = stricter cloud masking

try:
    ee.Initialize(project=PROJECT_ID)
except Exception:
    ee.Authenticate()
    ee.Initialize(project=PROJECT_ID)

# ---------- 1. AOI: Thailand boundary ----------
countries = ee.FeatureCollection("USDOS/LSIB_SIMPLE/2017")
thailand = countries.filter(ee.Filter.eq("country_na", "Thailand"))
thailand_geom = thailand.geometry()

# ---------- 2. Date range: whole year 2026, capped at "today" ----------
import datetime

year_start = ee.Date("2026-01-01")
today_str = datetime.datetime.utcnow().strftime("%Y-%m-%d")
range_end_str = min(today_str, "2026-12-31")
range_end = ee.Date(range_end_str)

# ---------- 3. Sentinel-2 SR + s2cloudless probability ----------
s2_sr = (
    ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    .filterBounds(thailand_geom)
    .filterDate(year_start, range_end)
)

s2_clouds = (
    ee.ImageCollection("COPERNICUS/S2_CLOUD_PROBABILITY")
    .filterBounds(thailand_geom)
    .filterDate(year_start, range_end)
)

s2_sr_with_cloud_mask = ee.Join.saveFirst("cloud_mask").apply(
    primary=s2_sr,
    secondary=s2_clouds,
    condition=ee.Filter.equals(leftField="system:index", rightField="system:index"),
)


def mask_clouds(img):
    img = ee.Image(img)
    cloud_prob = ee.Image(img.get("cloud_mask")).select("probability")
    is_clear = cloud_prob.lt(CLOUD_PROB_THRESHOLD)
    return img.updateMask(is_clear).divide(10000).copyProperties(
        img, ["system:time_start"]
    )


s2_masked = ee.ImageCollection(s2_sr_with_cloud_mask).map(mask_clouds)

# ---------- 4. Median composite, clipped to Thailand ----------
median_2026 = s2_masked.median().clip(thailand_geom)

# ---------- 5. Map with Google Satellite basemap ----------
vis_true_color = {"bands": ["B4", "B3", "B2"], "min": 0, "max": 0.3, "gamma": 1.1}

map_id_dict = median_2026.getMapId(vis_true_color)
s2_tile_url = map_id_dict["tile_fetcher"].url_format

m = folium.Map(location=[13.7, 100.5], zoom_start=6, tiles=None, control_scale=True)

folium.TileLayer(
    tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
    attr="Google Satellite",
    name="Google Satellite",
    overlay=False,
    control=True,
).add_to(m)

folium.TileLayer(
    tiles=s2_tile_url,
    attr="Google Earth Engine",
    name="Sentinel-2 Median 2026 (True Color)",
    overlay=True,
    control=True,
).add_to(m)

folium.GeoJson(
    thailand_geom.getInfo(),
    name="Thailand boundary",
    style_function=lambda _: {"color": "#ffff00", "weight": 1.5, "fillOpacity": 0},
).add_to(m)

folium.LayerControl(collapsed=False).add_to(m)

m.get_root().html.add_child(
    folium.Element(
        '<div style="position:fixed;top:10px;left:50px;z-index:9999;'
        'background:#fff;padding:8px 12px;border-radius:4px;'
        'box-shadow:0 1px 4px #777;font:600 15px system-ui;">'
        "Sentinel-2 Cloud-Free Median Composite &mdash; Thailand 2026</div>"
    )
)

m.save(OUTPUT_HTML)
print(f"Saved: {OUTPUT_HTML}")
