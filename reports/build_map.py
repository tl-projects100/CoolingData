"""Assemble a self-contained interactive dot-map artifact from map_data.json,
with an authentic NYC street-grid basemap (NYC Open Data CSCL) drawn underneath."""
import json, pathlib
ROOT = pathlib.Path(__file__).resolve().parent
data = json.load(open(ROOT/"map_data.json"))

# --- street basemap: compact [lon,lat] polylines + names ---
streets = []
try:
    gj = json.load(open(ROOT.parent/"data"/"raw"/"ues_streets.geojson"))
    for f in gj.get("features", []):
        geom = f.get("geometry") or {}
        nm = (f.get("properties") or {}).get("street_name", "")
        def add(line):
            pts = [[round(x, 5), round(y, 5)] for x, y in line]
            if len(pts) >= 2:
                streets.append({"n": nm, "c": pts})
        if geom.get("type") == "LineString":
            add(geom["coordinates"])
        elif geom.get("type") == "MultiLineString":
            for ln in geom["coordinates"]:
                add(ln)
except FileNotFoundError:
    pass

HTML = r"""<title>UES Legionnaires' Cooling Towers</title>
<style>
:root{
  --bg:#eceae4; --surface:#faf9f6; --surface-2:#efeee9; --line:#e0ded7;
  --street:#d6d3ca; --street-major:#c3bfb2;
  --ink:#161512; --ink-2:#52514e; --ink-3:#86847c;
  --control:#2a78d6; --case:#eb6834;
  --control-soft:rgba(42,120,214,.14); --case-soft:rgba(235,104,52,.16);
  --shadow:0 1px 2px rgba(0,0,0,.06),0 8px 24px rgba(0,0,0,.06);
  --mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
  --sans:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
}
@media (prefers-color-scheme:dark){:root{
  --bg:#101010; --surface:#1a1a18; --surface-2:#232220; --line:#33322e;
  --street:#2e2d2a; --street-major:#403e39;
  --ink:#f5f4ef; --ink-2:#c3c2b7; --ink-3:#8b897f;
  --control:#3987e5; --case:#f0793f;
  --control-soft:rgba(57,135,229,.18); --case-soft:rgba(240,121,63,.20);
  --shadow:0 1px 2px rgba(0,0,0,.4),0 10px 30px rgba(0,0,0,.5);
}}
:root[data-theme="dark"]{
  --bg:#101010; --surface:#1a1a18; --surface-2:#232220; --line:#33322e;
  --street:#2e2d2a; --street-major:#403e39;
  --ink:#f5f4ef; --ink-2:#c3c2b7; --ink-3:#8b897f;
  --control:#3987e5; --case:#f0793f;
  --control-soft:rgba(57,135,229,.18); --case-soft:rgba(240,121,63,.20);
  --shadow:0 1px 2px rgba(0,0,0,.4),0 10px 30px rgba(0,0,0,.5);
}
:root[data-theme="light"]{
  --bg:#eceae4; --surface:#faf9f6; --surface-2:#efeee9; --line:#e0ded7;
  --street:#d6d3ca; --street-major:#c3bfb2;
  --ink:#161512; --ink-2:#52514e; --ink-3:#86847c;
  --control:#2a78d6; --case:#eb6834;
  --control-soft:rgba(42,120,214,.14); --case-soft:rgba(235,104,52,.16);
}
*{box-sizing:border-box}
body{margin:0}
.wrap{font-family:var(--sans);background:var(--bg);color:var(--ink);
  min-height:100vh;padding:clamp(16px,3vw,40px);line-height:1.5;
  -webkit-font-smoothing:antialiased}
.inner{max-width:1120px;margin:0 auto}
.eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.14em;
  text-transform:uppercase;color:var(--case);margin:0 0 8px}
h1{font-size:clamp(1.5rem,3.4vw,2.3rem);line-height:1.1;margin:0 0 6px;
  letter-spacing:-.02em;text-wrap:balance;font-weight:650}
.sub{color:var(--ink-2);margin:0;max-width:64ch;font-size:.95rem}
.stats{display:flex;flex-wrap:wrap;gap:10px;margin:22px 0}
.stat{background:var(--surface);border:1px solid var(--line);border-radius:12px;
  padding:12px 16px;min-width:118px;box-shadow:var(--shadow)}
.stat .n{font-family:var(--mono);font-size:1.5rem;font-variant-numeric:tabular-nums;
  font-weight:600;letter-spacing:-.01em}
.stat.c1 .n{color:var(--case)} .stat.c0 .n{color:var(--control)}
.stat .l{font-size:.72rem;color:var(--ink-3);text-transform:uppercase;
  letter-spacing:.06em;margin-top:2px}
.toolbar{display:flex;flex-wrap:wrap;gap:8px 18px;align-items:center;
  margin:0 0 12px;padding:12px 14px;background:var(--surface);
  border:1px solid var(--line);border-radius:12px}
.group{display:flex;gap:6px;align-items:center}
.group .cap{font-size:.72rem;color:var(--ink-3);text-transform:uppercase;
  letter-spacing:.06em;margin-right:2px}
.chip{font:inherit;font-size:.82rem;cursor:pointer;border:1px solid var(--line);
  background:var(--surface-2);color:var(--ink-2);padding:5px 11px;border-radius:999px;
  display:inline-flex;align-items:center;gap:6px;transition:.15s}
.chip:hover{color:var(--ink);border-color:var(--ink-3)}
.chip[aria-pressed="true"]{background:var(--ink);color:var(--surface);border-color:var(--ink)}
.chip .dot{width:9px;height:9px;border-radius:50%}
.chip.case .dot{background:var(--case)} .chip.control .dot{background:var(--control)}
.chip[aria-pressed="false"]{opacity:.5}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:8px;overflow:hidden}
.seg button{font:inherit;font-size:.82rem;border:0;background:var(--surface-2);
  color:var(--ink-2);padding:5px 12px;cursor:pointer}
.seg button[aria-pressed="true"]{background:var(--ink);color:var(--surface)}
.card{background:var(--surface);border:1px solid var(--line);border-radius:16px;
  box-shadow:var(--shadow);overflow:hidden;position:relative}
.mapwrap{position:relative}
svg{display:block;width:100%;height:auto;aspect-ratio:960/640;touch-action:none;background:var(--surface-2)}
.street{stroke:var(--street);fill:none;stroke-linecap:round}
.street.major{stroke:var(--street-major);stroke-width:2.4}
.slabel{fill:var(--ink-3);font-family:var(--mono);font-size:9px;
  letter-spacing:.02em;text-transform:uppercase}
.dot{cursor:pointer}
.dot:hover{stroke:var(--ink);stroke-width:1.5}
.tip{position:absolute;pointer-events:none;z-index:20;background:var(--ink);
  color:var(--surface);border-radius:10px;padding:9px 11px;font-size:.8rem;
  max-width:230px;opacity:0;transition:opacity .1s;box-shadow:var(--shadow);
  transform:translate(-50%,calc(-100% - 12px))}
.tip.on{opacity:1}
.tip .ta{font-weight:650;margin-bottom:4px;font-size:.85rem}
.tip .tr{display:flex;justify-content:space-between;gap:14px;color:rgba(255,255,255,.72)}
.tip .tr b{color:#fff;font-family:var(--mono);font-variant-numeric:tabular-nums;font-weight:500}
.tip .badge{display:inline-block;font-size:.68rem;padding:1px 7px;border-radius:999px;
  margin-bottom:5px;font-family:var(--mono);letter-spacing:.03em}
.badge.case{background:var(--case-soft);color:var(--case)}
.badge.control{background:var(--control-soft);color:var(--control)}
.scalebar{position:absolute;left:16px;bottom:14px;font-family:var(--mono);
  font-size:.7rem;color:var(--ink-2);display:flex;flex-direction:column;gap:3px}
.scalebar .bar{height:4px;background:var(--ink-2);border-radius:2px}
.compass{position:absolute;right:16px;top:14px;font-family:var(--mono);
  font-size:.7rem;color:var(--ink-3);text-align:center}
.compass .arr{font-size:1.1rem;color:var(--ink-2);line-height:1}
.tableview{display:none;max-height:520px;overflow:auto}
.tableview.on{display:block}
.mapwrap.off{display:none}
table{border-collapse:collapse;width:100%;font-size:.82rem}
th,td{text-align:left;padding:7px 12px;border-bottom:1px solid var(--line);white-space:nowrap}
th{position:sticky;top:0;background:var(--surface-2);color:var(--ink-2);
  font-weight:600;font-size:.72rem;text-transform:uppercase;letter-spacing:.05em}
td.num{font-family:var(--mono);font-variant-numeric:tabular-nums;text-align:right}
.pill{font-size:.7rem;padding:1px 8px;border-radius:999px;font-family:var(--mono)}
.pill.case{background:var(--case-soft);color:var(--case)}
.pill.control{background:var(--control-soft);color:var(--control)}
.foot{color:var(--ink-3);font-size:.8rem;margin:16px 2px 0;max-width:74ch}
.foot b{color:var(--ink-2);font-weight:600}
@media(prefers-reduced-motion:reduce){*{transition:none!important}}
</style>

<div class="wrap"><div class="inner">
  <p class="eyebrow">NYC Open Data · 2026 Upper East Side cluster</p>
  <h1>Which cooling towers tested positive for Legionella</h1>
  <p class="sub">Every registered cooling-tower building in the outbreak ZIP codes
  (10028 · 10075 · 10128) — the only area the city blitz-tested. Orange = ordered to
  clean &amp; disinfect after a positive PCR screen; blue = registered tower, not on the
  list. Tap or hover a point for its history. Positive and negative towers are
  <strong>intermixed</strong> — no single hotspot; which specific towers came back
  positive isn't explained by their public maintenance records.</p>

  <div class="stats" id="stats"></div>

  <div class="toolbar">
    <div class="group"><span class="cap">Show</span>
      <button class="chip case" id="f-case" aria-pressed="true"><span class="dot"></span>Positive</button>
      <button class="chip control" id="f-ctrl" aria-pressed="true"><span class="dot"></span>Not listed</button>
    </div>
    <div class="group"><span class="cap">Dot size</span>
      <div class="seg"><button id="sz-u" aria-pressed="true">Uniform</button>
      <button id="sz-t" aria-pressed="false">By # towers</button></div>
    </div>
    <div class="group" style="margin-left:auto"><span class="cap">View</span>
      <div class="seg"><button id="v-map" aria-pressed="true">Map</button>
      <button id="v-tab" aria-pressed="false">Table</button></div>
    </div>
  </div>

  <div class="card">
    <div class="mapwrap" id="mapwrap">
      <svg id="svg" viewBox="0 0 960 640" role="img"
        aria-label="Dot map of registered cooling towers in the UES outbreak ZIP codes over the NYC street grid, colored by whether they tested positive."></svg>
      <div class="compass"><div class="arr">&#8593;</div>N</div>
      <div class="scalebar"><div class="bar" id="sbar"></div><span id="sbl"></span></div>
      <div class="tip" id="tip"></div>
    </div>
    <div class="tableview" id="tableview"></div>
  </div>

  <p class="foot"><b>Read with care.</b> A point marks a <em>building's</em> cooling
  tower(s); the outcome is tower positivity during the July 2026 investigation, not
  human illness (patient addresses are private). Within this zone, compliance history
  barely predicts positivity (AUC 0.70) and Moran's I &#8776; 0 — no fine-scale spatial
  clustering. Dots are placed at the building's <b>PLUTO lot-centroid</b> (a point inside
  the lot), not the street-front address geocode. Basemap: NYC Street Centerline
  (<span style="font-family:var(--mono)">inkn-q76z</span>). Points: registrations
  (<span style="font-family:var(--mono)">y4fw-iqfr</span>) + inspections
  (<span style="font-family:var(--mono)">f9wb-g8mb</span>) + NYC DOH list.</p>
</div></div>

<script>
const DATA = __DATA__, STREETS = __STREETS__;
const P = DATA.points, svg = document.getElementById('svg'), tip = document.getElementById('tip');
const NS='http://www.w3.org/2000/svg';
const VBW=960, VBH=640, PAD=30;
const lats=P.map(p=>p.lat), lons=P.map(p=>p.lon);
const latmid=(Math.min(...lats)+Math.max(...lats))/2;
const kx=Math.cos(latmid*Math.PI/180);
P.forEach(p=>{p._x=p.lon*kx; p._y=p.lat;});
const xs=P.map(p=>p._x), ys=P.map(p=>p._y);
// projection bbox from points, expanded slightly so streets frame the dots
const xmin=Math.min(...xs),xmax=Math.max(...xs),ymin=Math.min(...ys),ymax=Math.max(...ys);
const ex=(xmax-xmin)*0.06, ey=(ymax-ymin)*0.06;
const bx0=xmin-ex,bx1=xmax+ex,by0=ymin-ey,by1=ymax+ey;
const spanx=bx1-bx0, spany=by1-by0;
const s=Math.min((VBW-2*PAD)/spanx,(VBH-2*PAD)/spany);
const offx=(VBW-spanx*s)/2, offy=(VBH-spany*s)/2;
const sx=(lon)=>offx+(lon*kx-bx0)*s;
const sy=(lat)=>VBH-(offy+(lat-by0)*s);
function SX(p){return sx(p.lon);} function SY(p){return sy(p.lat);}
const state={case:true,ctrl:true,sizeByTowers:false};
const AVE={'5':'5 Av','3':'3 Av','2':'2 Av','1':'1 Av'};
const CROSS=new Set(['72','76','79','82','86','90','96']);

function draw(){
  svg.innerHTML='';
  // --- street basemap ---
  const base=document.createElementNS(NS,'g');
  const labelPts={};
  for(const st of STREETS){
    const major = AVE[st.n] || CROSS.has(st.n);
    const d = st.c.map((c,i)=>(i?'L':'M')+sx(c[0]).toFixed(1)+' '+sy(c[1]).toFixed(1)).join(' ');
    const path=document.createElementNS(NS,'path');
    path.setAttribute('d',d); path.setAttribute('class','street'+(major?' major':''));
    if(!major) path.setAttribute('stroke-width','1.1');
    base.appendChild(path);
    // collect a labeling anchor for majors
    if(major){
      const mid=st.c[Math.floor(st.c.length/2)];
      (labelPts[st.n]=labelPts[st.n]||[]).push([sx(mid[0]),sy(mid[1])]);
    }
  }
  svg.appendChild(base);
  // --- street labels (edge-anchored, de-duplicated) ---
  const lab=document.createElementNS(NS,'g');
  const placed=[];
  for(const nm in labelPts){
    const isAve = !!AVE[nm];
    const pts = labelPts[nm];
    // avenue: label the topmost point; cross st: leftmost
    let anc = isAve ? pts.reduce((a,b)=>b[1]<a[1]?b:a) : pts.reduce((a,b)=>b[0]<a[0]?b:a);
    let [lx,ly]=anc;
    if(isAve){ ly=Math.max(ly,PAD+14); } else { lx=Math.max(lx,PAD+4); ly=ly-4; }
    if(lx<PAD-6||lx>VBW-PAD+6||ly<PAD-6||ly>VBH-PAD+10) continue;
    if(placed.some(q=>Math.abs(q[0]-lx)<26&&Math.abs(q[1]-ly)<12)) continue;
    placed.push([lx,ly]);
    const t=document.createElementNS(NS,'text');
    t.setAttribute('x',lx.toFixed(1)); t.setAttribute('y',ly.toFixed(1));
    t.setAttribute('class','slabel');
    t.setAttribute('text-anchor', isAve?'middle':'start');
    t.textContent = isAve ? AVE[nm] : (nm+' St');
    lab.appendChild(t);
  }
  svg.appendChild(lab);
  // --- dots ---
  const shown=P.filter(p=>(p.c?state.case:state.ctrl));
  shown.sort((a,b)=>a.c-b.c).forEach(p=>{
    const c=document.createElementNS(NS,'circle');
    let r=5.5; if(state.sizeByTowers) r=4.5+Math.sqrt(p.nt)*2.3;
    c.setAttribute('cx',SX(p));c.setAttribute('cy',SY(p));c.setAttribute('r',r);
    c.setAttribute('fill',p.c?'var(--case)':'var(--control)');
    c.setAttribute('fill-opacity',p.c?'.92':'.78');
    c.setAttribute('stroke','var(--surface)');c.setAttribute('stroke-width','.8');
    c.setAttribute('class','dot');
    c.addEventListener('pointerenter',e=>showTip(e,p));
    c.addEventListener('pointermove',moveTip);
    c.addEventListener('pointerleave',hideTip);
    c.addEventListener('click',e=>{e.stopPropagation();showTip(e,p);});
    svg.appendChild(c);
  });
  drawScale();
}
function drawScale(){
  const m=200, dLat=m/111320, px=dLat*s;
  document.getElementById('sbar').style.width=Math.round(px)+'px';
  document.getElementById('sbl').textContent='200 m';
}
const wrapEl=document.getElementById('mapwrap');
function showTip(e,p){
  const cls=p.c?'case':'control';
  tip.innerHTML=`<span class="badge ${cls}">${p.c?'PCR-positive':'not listed'}</span>`+
    `<div class="ta">${p.a}</div>`+
    `<div class="tr"><span>ZIP</span><b>${p.zip}</b></div>`+
    `<div class="tr"><span>Cooling towers</span><b>${p.nt}</b></div>`+
    `<div class="tr"><span>Reg. age (yrs)</span><b>${p.age??'—'}</b></div>`+
    `<div class="tr"><span>Days since sample</span><b>${p.dls??'—'}</b></div>`+
    `<div class="tr"><span>Violations (all-time)</span><b>${p.nv}</b></div>`;
  tip.classList.add('on'); moveTip(e);
}
function moveTip(e){
  const r=wrapEl.getBoundingClientRect();
  tip.style.left=(e.clientX-r.left)+'px'; tip.style.top=(e.clientY-r.top)+'px';
}
function hideTip(){tip.classList.remove('on');}
function stats(){
  const el=document.getElementById('stats');
  const nc=P.filter(p=>p.c).length, nn=P.length-nc, rate=(nc/P.length*100).toFixed(0);
  el.innerHTML=`
   <div class="stat c1"><div class="n">${nc}</div><div class="l">Positive &mdash; ordered to clean</div></div>
   <div class="stat c0"><div class="n">${nn}</div><div class="l">Registered, not listed</div></div>
   <div class="stat"><div class="n">${P.length}</div><div class="l">Towers in the tested zone</div></div>
   <div class="stat"><div class="n">~0</div><div class="l">Screened outside this zone</div></div>`;
}
function buildTable(){
  const rows=[...P].sort((a,b)=>b.c-a.c||a.a.localeCompare(b.a));
  let h='<table><thead><tr><th>Building</th><th>ZIP</th><th>Status</th>'+
    '<th class="num">Towers</th><th class="num">Reg age (y)</th>'+
    '<th class="num">Days/sample</th><th class="num">Violations</th></tr></thead><tbody>';
  for(const p of rows) h+=`<tr><td>${p.a}</td><td class="num">${p.zip}</td>`+
    `<td><span class="pill ${p.c?'case':'control'}">${p.c?'positive':'not listed'}</span></td>`+
    `<td class="num">${p.nt}</td><td class="num">${p.age??'—'}</td>`+
    `<td class="num">${p.dls??'—'}</td><td class="num">${p.nv}</td></tr>`;
  document.getElementById('tableview').innerHTML=h+'</tbody></table>';
}
function tog(id,key){const b=document.getElementById(id);
  b.addEventListener('click',()=>{state[key]=!state[key];b.setAttribute('aria-pressed',state[key]);draw();});}
tog('f-case','case'); tog('f-ctrl','ctrl');
function seg(a,b,fn){const A=document.getElementById(a),B=document.getElementById(b);
  A.addEventListener('click',()=>{A.setAttribute('aria-pressed','true');B.setAttribute('aria-pressed','false');fn(true);});
  B.addEventListener('click',()=>{B.setAttribute('aria-pressed','true');A.setAttribute('aria-pressed','false');fn(false);});}
seg('sz-u','sz-t',u=>{state.sizeByTowers=!u;draw();});
seg('v-map','v-tab',isMap=>{
  document.getElementById('mapwrap').classList.toggle('off',!isMap);
  document.getElementById('tableview').classList.toggle('on',!isMap);});
stats(); buildTable(); draw();
</script>
"""

out = (HTML.replace("__DATA__", json.dumps(data, separators=(",", ":")))
           .replace("__STREETS__", json.dumps(streets, separators=(",", ":"))))
(ROOT/"map.html").write_text(out)
print(f"wrote reports/map.html {len(out)} bytes  ({len(streets)} street segments)")
