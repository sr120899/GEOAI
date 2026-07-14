"""Create a GeoJSON and self-contained Leaflet map from Thailand.shp."""
from __future__ import annotations

import json
import struct
from math import cos, radians, sin, sqrt, tan
from pathlib import Path


HERE = Path(__file__).resolve().parent
EXAMPLE = HERE / "Example"


def utm47n_to_wgs84(easting: float, northing: float) -> tuple[float, float]:
    """Convert EPSG:32647 (the CRS declared in Thailand.prj) to longitude/latitude."""
    a, e2, k0 = 6378137.0, 0.0066943799901413165, 0.9996
    ep2 = e2 / (1 - e2)
    x, y = easting - 500000.0, northing
    mu = y / (a * k0 * (1 - e2 / 4 - 3 * e2**2 / 64 - 5 * e2**3 / 256))
    e1 = (1 - sqrt(1 - e2)) / (1 + sqrt(1 - e2))
    phi1 = (mu + (3 * e1 / 2 - 27 * e1**3 / 32) * sin(2 * mu)
            + (21 * e1**2 / 16 - 55 * e1**4 / 32) * sin(4 * mu)
            + (151 * e1**3 / 96) * sin(6 * mu))
    n1 = a / sqrt(1 - e2 * sin(phi1)**2)
    t1, c1 = tan(phi1)**2, ep2 * cos(phi1)**2
    r1 = a * (1 - e2) / (1 - e2 * sin(phi1)**2)**1.5
    d = x / (n1 * k0)
    latitude = phi1 - (n1 * tan(phi1) / r1) * (d**2 / 2 - (5 + 3*t1 + 10*c1 - 4*c1**2 - 9*ep2) * d**4 / 24 + (61 + 90*t1 + 298*c1 + 45*t1**2 - 252*ep2 - 3*c1**2) * d**6 / 720)
    longitude = radians(99) + (d - (1 + 2*t1 + c1) * d**3 / 6 + (5 - 2*c1 + 28*t1 - 3*c1**2 + 8*ep2 + 24*t1**2) * d**5 / 120) / cos(phi1)
    return (longitude * 180 / 3.141592653589793, latitude * 180 / 3.141592653589793)


def read_polygons(path: Path) -> list[dict]:
    """Read Polygon/PolygonZ records from a Shapefile using only stdlib."""
    features = []
    with path.open("rb") as shp:
        shp.seek(100)
        while header := shp.read(8):
            _, words = struct.unpack(">2i", header)
            body = shp.read(words * 2)
            shape_type = struct.unpack("<i", body[:4])[0]
            if shape_type == 0:
                continue
            if shape_type not in {5, 15, 25}:
                raise ValueError(f"Unsupported Shapefile shape type: {shape_type}")
            num_parts, num_points = struct.unpack("<2i", body[36:44])
            parts = struct.unpack(f"<{num_parts}i", body[44:44 + num_parts * 4])
            point_offset = 44 + num_parts * 4
            points = [utm47n_to_wgs84(*struct.unpack("<2d", body[point_offset + i * 16:point_offset + (i + 1) * 16]))
                      for i in range(num_points)]
            rings = [points[start: parts[index + 1] if index + 1 < num_parts else num_points]
                     for index, start in enumerate(parts)]
            # Each source part is an individual Thailand polygon (e.g., islands).
            features.append({"type": "Feature", "properties": {"Thailand": 1},
                             "geometry": {"type": "MultiPolygon", "coordinates": [[ring] for ring in rings]}})
    return features


def main() -> None:
    geojson = {"type": "FeatureCollection", "features": read_polygons(EXAMPLE / "Thailand.shp")}
    geojson_path = EXAMPLE / "Thailand.geojson"
    geojson_text = json.dumps(geojson, ensure_ascii=False, separators=(",", ":"))
    geojson_path.write_text(geojson_text, encoding="utf-8")

    html = f"""<!doctype html>
<html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
<title>Thailand — Interactive Map</title>
<link rel=\"stylesheet\" href=\"https://unpkg.com/leaflet@1.9.4/dist/leaflet.css\">
<style>html,body,#map{{height:100%;margin:0}}.title{{background:#fff;padding:8px 10px;border-radius:4px;font:600 15px system-ui;box-shadow:0 1px 4px #777}}</style>
</head><body><div id=\"map\"></div><script src=\"https://unpkg.com/leaflet@1.9.4/dist/leaflet.js\"></script>
<script>const thailand={geojson_text};const thailandMap=L.map('map',{{preferCanvas:true}}).setView([13.4,101.0],6);
L.tileLayer('https://{{s}}.google.com/vt/lyrs=m&x={{x}}&y={{y}}&z={{z}}',{{subdomains:['mt0','mt1','mt2','mt3'],maxZoom:20,attribution:'© Google'}}).addTo(thailandMap);
const layer=L.geoJSON(thailand,{{renderer:L.canvas({{padding:.5}}),style:{{color:'#0057b8',weight:2,fillColor:'#35a854',fillOpacity:.28}},onEachFeature:(f,l)=>l.bindPopup('<b>Thailand</b><br>Geometry: MultiPolygon')}}).addTo(thailandMap);
thailandMap.fitBounds(layer.getBounds(),{{padding:[20,20],maxZoom:7}});const title=L.control({{position:'topright'}});title.onAdd=()=>{{const d=L.DomUtil.create('div','title');d.textContent='Thailand boundary';return d}};title.addTo(thailandMap);
</script></body></html>"""
    (EXAMPLE / "Thailand.html").write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
