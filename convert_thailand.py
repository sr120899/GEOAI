import sys
import json
from pathlib import Path

def main():
    import geopandas as gpd

    # paths
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("Example/Thailand.shp")
    out_geojson = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_suffix('.geojson')
    out_html = Path(sys.argv[3]) if len(sys.argv) > 3 else src.with_name('Thailand.html')

    print(f"Reading shapefile: {src}")
    gdf = gpd.read_file(src)

    print("CRS:", gdf.crs)
    print("Columns:", list(gdf.columns))
    print("First 5 rows:")
    print(gdf.head().to_string())
    print("Geometry types:", gdf.geometry.geom_type.unique())
    print("Total features:", len(gdf))

    # write geojson
    print(f"Writing GeoJSON to: {out_geojson}")
    gdf.to_file(out_geojson, driver='GeoJSON')

    # embed geojson into HTML (Leaflet viewer)
    print(f"Generating interactive HTML: {out_html}")
    geojson_text = json.dumps(json.loads(out_geojson.read_text()))

    html = f"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Thailand - GeoJSON viewer</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <style>html,body,#map{{height:100%;margin:0;padding:0}}</style>
</head>
<body>
  <div id="map"></div>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script>
    // Paste your Google Maps API key below to enable Google Maps base layer.
    const GOOGLE_API_KEY = ""; // <-- ADD YOUR API KEY HERE if you want Google basemap

    const map = L.map('map').setView([13.7,100.5],6);

    const osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    // GeoJSON data
    const geojson = {geojson_text};

    function onEachFeature(feature, layer){{
      if (feature.properties) {{
        const props = Object.keys(feature.properties).map(k => `<b>${k}</b>: ${feature.properties[k]}`).join('<br>');
        layer.bindPopup(props);
      }}
    }}

    const gj = L.geoJSON(geojson, {{onEachFeature: onEachFeature}}).addTo(map);
    map.fitBounds(gj.getBounds());

    // If user provides Google API key, show a note on how to use it (can't embed Google as a Leaflet tile without extra plugins).
    if (GOOGLE_API_KEY && GOOGLE_API_KEY.length>0) {{
      console.log('Google API key provided. You can create a Google Maps viewer separately using the Maps JavaScript API and map.data.addGeoJson().');
    }}
  </script>
</body>
</html>
"""

    out_html.write_text(html, encoding='utf-8')
    print("Done.")

if __name__ == '__main__':
    main()
