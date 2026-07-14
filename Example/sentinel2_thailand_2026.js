/**
 * Sentinel-2 cloud-free median composite — Thailand, year 2026
 * GEE Cloud Project: tidy-nomad-470808-e1
 *
 * How to run:
 * 1. Go to https://code.earthengine.google.com/
 * 2. Top-right project selector -> choose "tidy-nomad-470808-e1"
 * 3. Paste this whole script into a new script, click "Run"
 * 4. To share as a web app: Apps -> Publish new App -> pick this script
 */

// ---------- 1. AOI: Thailand boundary ----------
var countries = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017');
var thailand = countries.filter(ee.Filter.eq('country_na', 'Thailand'));
var thailandGeom = thailand.geometry();

// ---------- 2. Date range: whole year 2026, capped at "today" ----------
var yearStart = ee.Date('2026-01-01');
var yearEnd = ee.Date('2026-12-31');
var today = ee.Date(Date.now());
// Use whichever is earlier, so the composite is always valid even mid-year.
var rangeEnd = ee.Date(ee.Algorithms.If(today.millis().lt(yearEnd.millis()), today, yearEnd));

// ---------- 3. Sentinel-2 SR + s2cloudless probability ----------
var CLOUD_PROB_THRESHOLD = 40; // 0-100, lower = stricter cloud masking

var s2Sr = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(thailandGeom)
  .filterDate(yearStart, rangeEnd);

var s2Clouds = ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY')
  .filterBounds(thailandGeom)
  .filterDate(yearStart, rangeEnd);

var s2SrWithCloudMask = ee.Join.saveFirst('cloud_mask').apply({
  primary: s2Sr,
  secondary: s2Clouds,
  condition: ee.Filter.equals({leftField: 'system:index', rightField: 'system:index'})
});

function maskClouds(img) {
  var cloudProb = ee.Image(img.get('cloud_mask')).select('probability');
  var isClear = cloudProb.lt(CLOUD_PROB_THRESHOLD);
  return ee.Image(img).updateMask(isClear)
    .divide(10000)
    .copyProperties(img, ['system:time_start']);
}

var s2Masked = ee.ImageCollection(s2SrWithCloudMask).map(maskClouds);

// ---------- 4. Median composite, clipped to Thailand ----------
var median2026 = s2Masked.median().clip(thailandGeom);

// ---------- 5. Visualization ----------
var visTrueColor = {bands: ['B4', 'B3', 'B2'], min: 0, max: 0.3, gamma: 1.1};

Map.setOptions('SATELLITE');
Map.centerObject(thailandGeom, 6);
Map.addLayer(median2026, visTrueColor, 'Sentinel-2 Median 2026 (True Color)');
Map.addLayer(thailand.style({color: 'ffff00', fillColor: '00000000', width: 1.5}), {}, 'Thailand boundary');

// ---------- 6. UI panel ----------
var title = ui.Label('Sentinel-2 Cloud-Free Median Composite — Thailand 2026', {
  fontWeight: 'bold', fontSize: '16px', padding: '8px'
});
var subtitle = ui.Label('Median of S2_SR_HARMONIZED, s2cloudless masked (prob < ' + CLOUD_PROB_THRESHOLD + ')', {
  fontSize: '12px', color: '555555', padding: '0 8px 8px 8px'
});
var panel = ui.Panel([title, subtitle], ui.Panel.Layout.flow('vertical'), {position: 'top-left'});
Map.add(panel);
