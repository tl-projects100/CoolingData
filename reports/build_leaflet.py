"""Standalone Leaflet map with a real tile basemap (OpenStreetMap).
Opens in any browser locally (not inside the CSP-sandboxed artifact)."""
import json, pathlib
ROOT = pathlib.Path(__file__).resolve().parent
data = json.load(open(ROOT/"map_data.json"))
pts = data["points"]

HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>UES Legionnaires' Cooling Towers — map</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  html,body{margin:0;height:100%;font-family:system-ui,sans-serif}
  #map{height:100%}
  .legend{background:#fff;padding:10px 12px;border-radius:8px;box-shadow:0 1px 6px rgba(0,0,0,.3);
    font-size:13px;line-height:1.7}
  .legend .k{display:inline-block;width:12px;height:12px;border-radius:50%;margin-right:6px;vertical-align:-1px}
  .legend h4{margin:0 0 6px;font-size:13px}
  .pop b{font-size:14px}
  .pop table{border-collapse:collapse;margin-top:4px;font-size:12px}
  .pop td{padding:1px 8px 1px 0}
</style></head><body>
<div id="map"></div>
<script>
const PTS = __PTS__;
const map = L.map('map');
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
  {maxZoom:19, attribution:'© OpenStreetMap'}).addTo(map);
const CASE='#eb6834', CTRL='#2a78d6';
const layer = L.featureGroup();
for(const p of PTS){
  const m=L.circleMarker([p.lat,p.lon],{radius:p.c?7:6,color:'#fff',weight:1,
     fillColor:p.c?CASE:CTRL,fillOpacity:.9});
  m.bindPopup(`<div class="pop"><b>${p.a}</b><br>`+
    `<span style="color:${p.c?CASE:CTRL}">${p.c?'PCR-positive — ordered to remediate':'registered, not listed'}</span>`+
    `<table><tr><td>ZIP</td><td>${p.zip}</td></tr>`+
    `<tr><td>Cooling towers</td><td>${p.nt}</td></tr>`+
    `<tr><td>Reg age (yrs)</td><td>${p.age??'—'}</td></tr>`+
    `<tr><td>Days since sample</td><td>${p.dls??'—'}</td></tr>`+
    `<tr><td>Violations</td><td>${p.nv}</td></tr></table></div>`);
  layer.addLayer(m);
}
layer.addTo(map);
map.fitBounds(layer.getBounds().pad(0.08));
const lg=L.control({position:'bottomright'});
lg.onAdd=function(){const d=L.DomUtil.create('div','legend');
  d.innerHTML=`<h4>Cooling towers · UES 2026</h4>`+
    `<div><span class="k" style="background:${CASE}"></span>PCR-positive (${PTS.filter(p=>p.c).length})</div>`+
    `<div><span class="k" style="background:${CTRL}"></span>Registered, not listed (${PTS.filter(p=>!p.c).length})</div>`;
  return d;};
lg.addTo(map);
</script></body></html>"""

out = HTML.replace("__PTS__", json.dumps(pts, separators=(",", ":")))
(ROOT/"map_leaflet.html").write_text(out)
print("wrote reports/map_leaflet.html", len(out), "bytes")
