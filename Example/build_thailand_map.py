"""
Rebuild Thailand.geojson and Thailand.html from Thailand.shp.

Source shapefile: Example/Thailand.shp
  - CRS: WGS_1984_UTM_Zone_47N (EPSG:32647), read from Thailand.prj
  - 1 feature, MultiPolygon (728 exterior rings, no holes -- mainland + islands)
  - Attribute: Thailand = 1

Pure-Python pipeline (pyshp + pyproj) because this machine's Application
Control policy blocks the GDAL DLL used by pyogrio/fiona/geopandas.read_file.

Run:
    python build_thailand_map.py
Outputs:
    Example/Thailand.geojson
    Example/Thailand.html   (interactive Leaflet map, Google Maps satellite basemap)
"""

import json
import os

import shapefile
from pyproj import Transformer

HERE = os.path.dirname(__file__)
SHP_PATH = os.path.join(HERE, "Thailand.shp")
GEOJSON_PATH = os.path.join(HERE, "Thailand.geojson")
HTML_PATH = os.path.join(HERE, "Thailand.html")

SOURCE_EPSG = 32647  # WGS_1984_UTM_Zone_47N, from Thailand.prj
COORD_PRECISION = 6  # ~0.11 m at the equator


def shp_to_geojson():
    transformer = Transformer.from_crs(SOURCE_EPSG, 4326, always_xy=True)
    sf = shapefile.Reader(SHP_PATH)
    shp = sf.shape(0)
    record = sf.record(0).as_dict()
    part_starts = list(shp.parts) + [len(shp.points)]

    polygons = []
    for i in range(len(part_starts) - 1):
        ring_native = shp.points[part_starts[i] : part_starts[i + 1]]
        ring_lonlat = [transformer.transform(x, y) for x, y in ring_native]
        ring_lonlat = [[round(lon, COORD_PRECISION), round(lat, COORD_PRECISION)] for lon, lat in ring_lonlat]
        # Shapefile exterior rings are clockwise; GeoJSON (RFC 7946) wants
        # exterior rings counterclockwise, so reverse.
        ring_lonlat.reverse()
        polygons.append([ring_lonlat])  # one ring per polygon: no holes

    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": record,
                "geometry": {"type": "MultiPolygon", "coordinates": polygons},
            }
        ],
    }

    with open(GEOJSON_PATH, "w", encoding="utf-8") as f:
        json.dump(geojson, f, separators=(",", ":"))

    print(f"Saved: {GEOJSON_PATH} ({len(polygons)} polygon parts)")
    return geojson


def geojson_to_html(geojson):
    geojson_js = json.dumps(geojson, separators=(",", ":"))

    html = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Thailand — Interactive Map</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<style>html,body,#map{height:100%;margin:0}.title{background:#fff;padding:8px 10px;border-radius:4px;font:600 15px system-ui;box-shadow:0 1px 4px #777}</style>
</head><body>
<div id="map"></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
var thailand = __GEOJSON__;

var googleSatellite = L.tileLayer('https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', {
  maxZoom: 20, attribution: 'Map data &copy; Google'
});
var googleHybrid = L.tileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', {
  maxZoom: 20, attribution: 'Map data &copy; Google'
});
var googleRoadmap = L.tileLayer('https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}', {
  maxZoom: 20, attribution: 'Map data &copy; Google'
});

var map = L.map('map', {layers: [googleSatellite]});

var boundaryLayer = L.geoJSON(thailand, {
  style: {color: '#ffff00', weight: 1.5, fillColor: '#ffff00', fillOpacity: 0.08}
}).addTo(map);
map.fitBounds(boundaryLayer.getBounds());

L.control.layers(
  {'Google Satellite': googleSatellite, 'Google Hybrid': googleHybrid, 'Google Roadmap': googleRoadmap},
  {'Thailand boundary': boundaryLayer}
).addTo(map);

L.control.scale().addTo(map);

var title = L.control({position: 'topleft'});
title.onAdd = function () {
  var div = L.DomUtil.create('div', 'title');
  div.innerHTML = 'Thailand — Interactive Map';
  return div;
};
title.addTo(map);
</script>
</body></html>
"""
    html = html.replace("__GEOJSON__", geojson_js)

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Saved: {HTML_PATH}")


if __name__ == "__main__":
    gj = shp_to_geojson()
    geojson_to_html(gj)
