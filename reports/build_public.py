"""Assemble a plain-language, public-facing explainer artifact with an embedded
street-grid map. Independent analysis of NYC Open Data — NOT an official DOH page."""
import json, pathlib
ROOT = pathlib.Path(__file__).resolve().parent
data = json.load(open(ROOT/"map_data.json"))
streets = []
try:
    gj = json.load(open(ROOT.parent/"data"/"raw"/"ues_streets.geojson"))
    for f in gj.get("features", []):
        geom = f.get("geometry") or {}
        nm = (f.get("properties") or {}).get("street_name", "")
        def add(line):
            pts = [[round(x,5),round(y,5)] for x,y in line]
            if len(pts) >= 2: streets.append({"n":nm,"c":pts})
        if geom.get("type") == "LineString": add(geom["coordinates"])
        elif geom.get("type") == "MultiLineString":
            for ln in geom["coordinates"]: add(ln)
except FileNotFoundError: pass

HTML = r"""<title>The Upper East Side's Legionnaires' cooling towers, explained</title>
<style>
:root{
  --bg:#f4f5f3; --surface:#ffffff; --surface-2:#eceef0; --line:#e3e5e4;
  --street:#dcdedd; --street-major:#c7cbc9;
  --ink:#16181b; --ink-2:#4a4f55; --ink-3:#7c828a;
  --case:#c9531f; --control:#2565c4; --safe:#0f7049; --safe-bg:#e7f3ec;
  --case-map:#eb6834; --control-map:#2a78d6;
  --shadow:0 1px 2px rgba(20,22,26,.05),0 10px 30px rgba(20,22,26,.07);
  --serif:ui-serif,Georgia,"Iowan Old Style","Times New Roman",serif;
  --sans:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  --mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
}
@media (prefers-color-scheme:dark){:root{
  --bg:#101214; --surface:#181b1e; --surface-2:#202427; --line:#2b3034;
  --street:#2a2f33; --street-major:#3c4247;
  --ink:#f0f2f3; --ink-2:#bfc5cb; --ink-3:#868d95;
  --case:#f0793f; --control:#5896ec; --safe:#43b183; --safe-bg:#12271e;
  --case-map:#f0793f; --control-map:#3987e5;
  --shadow:0 1px 2px rgba(0,0,0,.4),0 12px 34px rgba(0,0,0,.5);
}}
:root[data-theme="dark"]{
  --bg:#101214; --surface:#181b1e; --surface-2:#202427; --line:#2b3034;
  --street:#2a2f33; --street-major:#3c4247;
  --ink:#f0f2f3; --ink-2:#bfc5cb; --ink-3:#868d95;
  --case:#f0793f; --control:#5896ec; --safe:#43b183; --safe-bg:#12271e;
  --case-map:#f0793f; --control-map:#3987e5;
  --shadow:0 1px 2px rgba(0,0,0,.4),0 12px 34px rgba(0,0,0,.5);
}
:root[data-theme="light"]{
  --bg:#f4f5f3; --surface:#ffffff; --surface-2:#eceef0; --line:#e3e5e4;
  --street:#dcdedd; --street-major:#c7cbc9;
  --ink:#16181b; --ink-2:#4a4f55; --ink-3:#7c828a;
  --case:#c9531f; --control:#2565c4; --safe:#0f7049; --safe-bg:#e7f3ec;
  --case-map:#eb6834; --control-map:#2a78d6;
}
*{box-sizing:border-box}
body{margin:0}
.pg{font-family:var(--sans);background:var(--bg);color:var(--ink);line-height:1.65;
  -webkit-font-smoothing:antialiased;padding:clamp(20px,4vw,64px) 20px 72px}
.col{max-width:680px;margin:0 auto}
.wide{max-width:960px;margin:0 auto}
.eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.16em;
  text-transform:uppercase;color:var(--case);margin:0 0 14px}
h1{font-family:var(--serif);font-weight:600;font-size:clamp(2rem,5.4vw,3.15rem);
  line-height:1.06;letter-spacing:-.02em;margin:0 0 18px;text-wrap:balance}
.dek{font-size:clamp(1.08rem,2.3vw,1.3rem);color:var(--ink-2);margin:0 0 20px;
  text-wrap:pretty}
.meta{font-family:var(--mono);font-size:12px;color:var(--ink-3);
  border-top:1px solid var(--line);border-bottom:1px solid var(--line);
  padding:11px 0;margin:0 0 34px;display:flex;flex-wrap:wrap;gap:6px 18px}
h2{font-family:var(--serif);font-weight:600;font-size:clamp(1.4rem,3.2vw,1.9rem);
  line-height:1.15;letter-spacing:-.015em;margin:52px 0 14px;text-wrap:balance}
p{margin:0 0 18px;font-size:1.06rem}
p.big{font-size:1.14rem}
strong{font-weight:650}
.lede::first-letter{font-family:var(--serif);float:left;font-size:3.3rem;
  line-height:.82;padding:6px 10px 0 0;color:var(--case)}
.callout{background:var(--safe-bg);border:1px solid color-mix(in srgb,var(--safe) 30%,transparent);
  border-radius:14px;padding:18px 20px;margin:26px 0;display:flex;gap:14px}
.callout .ic{flex:none;width:26px;height:26px;border-radius:50%;background:var(--safe);
  color:#fff;display:grid;place-items:center;font-weight:700;font-size:15px}
.callout h3{margin:0 0 5px;font-size:1.05rem;color:var(--safe)}
.callout p{margin:0;font-size:.97rem;color:var(--ink-2)}
.compare{display:flex;gap:14px;flex-wrap:wrap;margin:26px 0 8px}
.cbar{flex:1;min-width:180px;background:var(--surface);border:1px solid var(--line);
  border-radius:14px;padding:16px 18px;box-shadow:var(--shadow)}
.cbar .num{font-family:var(--mono);font-size:2.1rem;font-weight:600;letter-spacing:-.02em;
  font-variant-numeric:tabular-nums}
.cbar.c1 .num{color:var(--case)} .cbar.c0 .num{color:var(--control)}
.cbar .lab{font-size:.9rem;color:var(--ink-2);margin-top:2px}
.cbar .track{height:8px;background:var(--surface-2);border-radius:99px;margin-top:12px;overflow:hidden}
.cbar .fill{height:100%;border-radius:99px}
.cbar.c1 .fill{background:var(--case)} .cbar.c0 .fill{background:var(--control)}
.findings{display:grid;gap:14px;margin:24px 0}
@media(min-width:620px){.findings{grid-template-columns:1fr 1fr}}
.fc{background:var(--surface);border:1px solid var(--line);border-radius:16px;
  padding:20px 22px;box-shadow:var(--shadow)}
.fc .n{font-family:var(--mono);font-size:12px;color:var(--case);letter-spacing:.06em}
.fc h3{font-family:var(--serif);font-size:1.22rem;margin:8px 0 8px;line-height:1.2}
.fc p{font-size:.98rem;color:var(--ink-2);margin:0}
figure{margin:34px 0}
.mapcard{background:var(--surface);border:1px solid var(--line);border-radius:18px;
  box-shadow:var(--shadow);overflow:hidden;position:relative}
.maphd{padding:16px 20px 4px}
.maphd .k{font-family:var(--mono);font-size:11px;letter-spacing:.1em;
  text-transform:uppercase;color:var(--ink-3)}
.maphd h3{font-family:var(--serif);font-size:1.35rem;margin:6px 0 3px}
.leg{display:flex;gap:16px;flex-wrap:wrap;padding:0 20px 12px;font-size:.9rem;color:var(--ink-2)}
.leg span{display:inline-flex;align-items:center;gap:7px}
.leg i{width:12px;height:12px;border-radius:50%;display:inline-block}
.mapwrap{position:relative}
svg{display:block;width:100%;height:auto;aspect-ratio:960/600;touch-action:manipulation;background:var(--surface-2)}
.street{stroke:var(--street);fill:none;stroke-linecap:round}
.street.major{stroke:var(--street-major);stroke-width:2.4}
.slabel{fill:var(--ink-3);font-family:var(--mono);font-size:9px;text-transform:uppercase}
.dot{cursor:pointer;stroke:var(--surface);stroke-width:.8}
.dot.pos{fill:var(--case-map)} .dot.neg{fill:var(--control-map)}
.tip{position:absolute;pointer-events:none;z-index:20;background:var(--ink);
  color:var(--bg);border-radius:10px;padding:8px 11px;font-size:.8rem;max-width:230px;
  opacity:0;transition:opacity .1s;box-shadow:var(--shadow);transform:translate(-50%,calc(-100% - 12px))}
.tip.on{opacity:1}
.tip .ta{font-weight:650;margin-bottom:3px}
.tip .tr{display:flex;justify-content:space-between;gap:14px;opacity:.8}
.tip .tr b{font-family:var(--mono)}
.compass{position:absolute;right:14px;top:12px;font-family:var(--mono);font-size:.7rem;
  color:var(--ink-3);text-align:center}.compass .arr{font-size:1.05rem;color:var(--ink-2)}
figcaption{font-size:.86rem;color:var(--ink-3);margin-top:10px;padding:0 4px}
ul{margin:0 0 18px;padding-left:22px}li{margin:0 0 8px;color:var(--ink-2)}
.symp{background:var(--surface);border:1px solid var(--line);border-radius:16px;
  padding:22px 24px;margin:24px 0;box-shadow:var(--shadow)}
.symp h3{font-family:var(--serif);margin:0 0 10px;font-size:1.25rem}
.limits{background:var(--surface-2);border-radius:16px;padding:22px 24px;margin:24px 0}
.limits h3{font-family:var(--serif);margin:0 0 10px;font-size:1.2rem}
.foot{border-top:1px solid var(--line);margin-top:48px;padding-top:22px;
  font-size:.86rem;color:var(--ink-3)}
.foot b{color:var(--ink-2)}
.disc{font-size:.82rem;color:var(--ink-3);background:var(--surface-2);
  border-radius:12px;padding:14px 16px;margin-top:18px;line-height:1.55}
a{color:var(--case);text-decoration-thickness:1px;text-underline-offset:2px}
@media(prefers-reduced-motion:reduce){*{transition:none!important}}
</style>

<div class="pg">
<div class="col">
  <p class="eyebrow">Independent analysis · NYC Open Data</p>
  <h1>What the data shows about the Upper East Side's Legionnaires' cooling towers</h1>
  <p class="dek">This summer, 76 buildings in Manhattan were ordered to scrub their rooftop
  cooling towers after tests found <em>Legionella</em> bacteria. We compared those buildings
  against their neighbors using the city's public records. Here's what stands out — in plain
  language.</p>
  <div class="meta"><span>Upper East Side · Carnegie Hill &amp; Yorkville</span>
    <span>ZIP 10028 · 10075 · 10128</span><span>Updated July 2026</span></div>

  <div class="callout">
    <div class="ic">&#10003;</div>
    <div><h3>First, the reassuring part</h3>
    <p>The NYC Health Department says it remains <strong>safe to shower, drink tap water, and
    use air conditioners</strong> in the affected ZIP codes. Rooftop cooling towers are part
    of a building's air-conditioning system — separate from the water you drink and bathe in.
    Legionnaires' disease does not spread from person to person.</p></div>
  </div>

  <p class="big lede">In early July 2026, health investigators noticed a cluster of
  Legionnaires' disease — a serious, treatable form of pneumonia — in the Carnegie Hill and
  Yorkville sections of the Upper East Side. They sampled water from more than 180 rooftop
  cooling towers in the area. Where a screening test came back positive for <em>Legionella</em>,
  the building was ordered to clean and disinfect its tower immediately, as a precaution. That
  list has grown to <strong>76 buildings</strong>.</p>

  <p>Cooling towers matter because they release a fine mist into the outdoor air. If
  <em>Legionella</em> is growing inside one, that mist can carry the bacteria to people nearby.
  It's why cooling towers have been the source of past New York outbreaks — and why the city
  regulates, registers, and tests them.</p>

  <h2>What we looked at</h2>
  <p>Every cooling tower in NYC has to be registered, tested for <em>Legionella</em> on a
  schedule, and inspected. All of that is public. We took the <strong>76 buildings whose towers
  tested positive</strong> and compared them against the <strong>other registered cooling-tower
  buildings in the same three ZIP codes</strong> — 183 buildings in all — asking a simple
  question: <em>do the positive buildings have anything different about them?</em></p>
  <p>We didn't stop at one or two things. We tested <strong>about 40 factors</strong> across
  six kinds of public records — testing and inspection history, violations of every type,
  building size and value, energy and water use, ownership and contractors, and location —
  using standard statistics and several study designs. The short version: almost nothing
  a regulator would flag explains which towers came back positive.</p>
</div>

<figure class="wide">
  <div class="mapcard">
    <div class="maphd"><div class="k">The outbreak zone, tower by tower</div>
      <h3>Positive and negative towers sit side by side</h3></div>
    <div class="leg">
      <span><i style="background:var(--case-map)"></i>Tested positive &mdash; ordered to clean (74)</span>
      <span><i style="background:var(--control-map)"></i>Registered tower in the same ZIPs, not on the DOH list (109)</span>
    </div>
    <div class="mapwrap" id="mapwrap">
      <svg id="svg" viewBox="0 0 960 600" role="img"
        aria-label="Map of registered cooling towers in the outbreak ZIP codes over the Upper East Side street grid. Towers that tested positive are mixed in among those that did not; there is no single cluster."></svg>
      <div class="compass"><div class="arr">&#8593;</div>N</div>
    </div>
  </div>
  <figcaption>Each dot is a building's cooling tower, at its real location. Hover (or tap) for
  details. Orange towers tested positive; blue did not. Notice they're mixed together — there is
  no single block or corner that stands out.</figcaption>
</figure>

<div class="col">
  <h2>Four things the data says</h2>
  <div class="findings">
    <div class="fc"><div class="n">01</div><h3>The "40%" is about testing, not risk</h3>
      <p>You'll hear that ~40% of towers in these ZIP codes tested positive vs almost none
      elsewhere. That gap is mostly a <strong>searchlight effect</strong>: these ZIPs are the
      only place the city intensively screened, because that's where people fell ill. The ~0%
      elsewhere reflects <em>not being tested</em> — not being clean; <em>Legionella</em> can
      grow in cooling towers anywhere, especially in summer heat.</p></div>
    <div class="fc"><div class="n">02</div><h3>Not a story of neglect</h3>
      <p>Buildings with more violations, overdue tests, or fewer inspections were <strong>not</strong>
      more likely to test positive — even after matching buildings of similar size. The usual
      signs of a poorly-run building did not predict <em>Legionella</em>.</p></div>
    <div class="fc"><div class="n">03</div><h3>"Tests more" means diligent, not troubled</h3>
      <p>Positives leaned toward larger buildings that test their towers <strong>more often</strong> —
      and those buildings actually had <em>fewer</em> violations. So it looks like careful
      buildings catch more simply because they look more, not that they're worse-run.</p></div>
    <div class="fc"><div class="n">04</div><h3>No single hotspot</h3>
      <p>Positive and negative towers are <strong>intermixed block by block</strong> — no tight
      cluster, even by local hotspot tests. Consistent with bacteria turning up diffusely across
      the area rather than from one point.</p></div>
  </div>

  <div class="callout" style="background:var(--surface-2);border-color:var(--line)">
    <div class="ic" style="background:var(--ink-3)">?</div>
    <div><h3 style="color:var(--ink-2)">One early, unconfirmed hint</h3>
    <p>The positive buildings tended to be slightly <strong>taller than their
    neighbors</strong> and a bit <strong>closer to Central Park</strong> — patterns
    that fit how tower mist drifts in open air. This is preliminary, could be a
    coincidence of small numbers, and would need public-health experts to confirm.
    It does <em>not</em> mean any particular building did something wrong.</p></div>
  </div>

  <h2>Why the "40%" is misleading</h2>
  <p>The eye-catching contrast below is real, but it mostly measures <strong>where the city
  looked</strong>, not where the bacteria are. Investigators drew the testing boundary around
  where people got sick, then intensively sampled towers inside it. Towers elsewhere weren't
  part of this sweep — so they show ~0 "ordered to clean," not because they're clean, but
  because no one ran the same test on them.</p>
  <div class="compare">
    <div class="cbar c1"><div class="num">40%</div><div class="lab">of towers <strong>tested here</strong> came back positive</div>
      <div class="track"><div class="fill" style="width:100%"></div></div></div>
    <div class="cbar c0"><div class="num">~0%</div><div class="lab">elsewhere — but those towers were <strong>never screened</strong> in this sweep</div>
      <div class="track"><div class="fill" style="width:2%"></div></div></div>
  </div>
  <p style="font-size:.9rem;color:var(--ink-3)">So the honest takeaway isn't "these blocks are
  uniquely dangerous" — it's "this is the one place that got a blitz test."</p>

  <h2>The factors that matter most — and aren't public</h2>
  <p>If maintenance records don't explain which towers bloomed, what does? Almost certainly
  the day-to-day condition <em>inside</em> each tower — and none of it is in public data:</p>
  <ul>
    <li><strong>Water temperature</strong> in the tower basin — the single biggest driver of growth.</li>
    <li><strong>Chemical treatment</strong> — the exact biocide schedule, and any lapse in it.</li>
    <li><strong>Stagnation</strong> — a pump cycling off, an idle stretch, a dead leg in the pipes.</li>
    <li><strong>Biofilm and scale</strong>, and the condition of the mist-catching parts.</li>
    <li><strong>The tower's make, model, and age</strong> — some designs spray far more mist than others.</li>
    <li><strong>Lab culture results and patient locations</strong> — kept private, and the key to naming a source.</li>
  </ul>
  <p>Two buildings that look identical on every public record can differ completely on these.
  <strong>That</strong> is where the answer lives — a layer below anything the city publishes.
  Pinning down the exact source needs the Health Department's own lab and treatment data, not
  open records.</p>

  <h2>What this means for you</h2>
  <p>The cleaning orders are a <strong>precaution</strong>: a positive screening test doesn't
  guarantee live, infectious bacteria were present, so the city cleans first and confirms later.
  Our analysis found no evidence pointing at specific "negligent" buildings — so there's little
  to be gained from worrying about which address you live near. The sensible steps are the ordinary
  ones: follow the Health Department's guidance, and take symptoms seriously.</p>

  <div class="symp">
    <h3>Know the signs</h3>
    <p style="font-size:.98rem;color:var(--ink-2);margin-bottom:10px">Legionnaires' disease usually
    appears <strong>2&ndash;10 days</strong> after exposure and is treatable with antibiotics,
    especially when caught early. Symptoms include:</p>
    <ul>
      <li>Fever, chills, cough</li>
      <li>Shortness of breath, chest discomfort</li>
      <li>Muscle aches, headache, sometimes diarrhea or confusion</li>
    </ul>
    <p style="font-size:.98rem;color:var(--ink-2);margin:0">Risk is higher for people
    <strong>50 and older</strong>, smokers, and those with chronic lung conditions or weakened
    immune systems. If you live or spent time in the area and have these symptoms,
    <strong>see a doctor and mention the outbreak</strong>. For questions, call <strong>311</strong>.</p>
  </div>

  <div class="limits">
    <h3>What this analysis can't tell you</h3>
    <ul>
      <li>It's built on <strong>which towers tested positive</strong>, not on where sick people
      live — patient locations are private and never published.</li>
      <li>It can show patterns, but it <strong>can't prove what caused</strong> any individual
      infection.</li>
      <li>It's a snapshot of a fast-moving investigation; the official building list and case
      counts keep changing.</li>
      <li>With 74 positive buildings, the numbers are small — the findings are suggestive, not the
      final word.</li>
    </ul>
  </div>

  <div class="foot">
    <p><b>How we did it.</b> We matched the Health Department's public "clean &amp; disinfect" list
    to NYC's Cooling Tower Registration and Inspection datasets on
    <a href="https://opendata.cityofnewyork.us">NYC Open Data</a>, then compared the positive
    buildings against other registered cooling-tower buildings in the same ZIP codes using standard
    statistics (logistic regression and a spatial clustering test). Building size and value come
    from the city's PLUTO dataset. Street map from NYC's Street Centerline. A full technical writeup
    accompanies this piece.</p>
    <div class="disc"><strong>Independent analysis — not an official record.</strong> This page is
    not affiliated with or endorsed by the NYC Health Department or any government agency. For
    official information, guidance, and the current building list, see
    <a href="https://www.nyc.gov/site/doh/health/health-topics/legionnaires-disease.page">nyc.gov/health</a>
    or call 311. Nothing here is medical advice.</div>
  </div>
</div>
</div>

<script>
const DATA=__DATA__, STREETS=__STREETS__;
const P=DATA.points, svg=document.getElementById('svg');
const NS='http://www.w3.org/2000/svg', VBW=960, VBH=600, PAD=28;
const lats=P.map(p=>p.lat), lons=P.map(p=>p.lon);
const latmid=(Math.min(...lats)+Math.max(...lats))/2, kx=Math.cos(latmid*Math.PI/180);
const xs=lons.map(l=>l*kx), ys=lats.slice();
const xmin=Math.min(...xs),xmax=Math.max(...xs),ymin=Math.min(...ys),ymax=Math.max(...ys);
const ex=(xmax-xmin)*.06, ey=(ymax-ymin)*.06;
const bx0=xmin-ex,bx1=xmax+ex,by0=ymin-ey,by1=ymax+ey,spx=bx1-bx0,spy=by1-by0;
const s=Math.min((VBW-2*PAD)/spx,(VBH-2*PAD)/spy);
const ox=(VBW-spx*s)/2, oy=(VBH-spy*s)/2;
const sx=lon=>ox+(lon*kx-bx0)*s, sy=lat=>VBH-(oy+(lat-by0)*s);
const AVE={'5':'5 Av','3':'3 Av','2':'2 Av','1':'1 Av'}, CROSS=new Set(Array.from({length:40},(_,i)=>String(66+i)));
let tip;
function draw(){
  const base=document.createElementNS(NS,'g'); const lp={};
  for(const st of STREETS){
    const major=AVE[st.n]||CROSS.has(st.n);
    const d=st.c.map((c,i)=>(i?'L':'M')+sx(c[0]).toFixed(1)+' '+sy(c[1]).toFixed(1)).join(' ');
    const p=document.createElementNS(NS,'path');p.setAttribute('d',d);
    p.setAttribute('class','street'+(major?' major':''));
    if(!major)p.setAttribute('stroke-width','1.1');base.appendChild(p);
    if(major){const m=st.c[Math.floor(st.c.length/2)];(lp[st.n]=lp[st.n]||[]).push([sx(m[0]),sy(m[1])]);}
  }
  svg.appendChild(base);
  const lab=document.createElementNS(NS,'g'),placed=[];
  for(const nm in lp){const ave=!!AVE[nm];const pts=lp[nm];
    let a=ave?pts.reduce((x,y)=>y[1]<x[1]?y:x):pts.reduce((x,y)=>y[0]<x[0]?y:x);
    let lx=a[0],ly=a[1]; if(ave)ly=Math.max(ly,PAD+12);else{lx=Math.max(lx,PAD+2);ly-=4;}
    if(lx<PAD-6||lx>VBW-PAD+6||ly<PAD-6||ly>VBH-PAD+8)continue;
    if(placed.some(q=>Math.abs(q[0]-lx)<26&&Math.abs(q[1]-ly)<12))continue;placed.push([lx,ly]);
    const t=document.createElementNS(NS,'text');t.setAttribute('x',lx.toFixed(1));t.setAttribute('y',ly.toFixed(1));
    t.setAttribute('class','slabel');t.setAttribute('text-anchor',ave?'middle':'start');
    t.textContent=ave?AVE[nm]:nm+' St';lab.appendChild(t);}
  svg.appendChild(lab);
  const shown=[...P].sort((a,b)=>a.c-b.c);
  shown.forEach(p=>{
    const c=document.createElementNS(NS,'circle');
    c.setAttribute('cx',sx(p.lon));c.setAttribute('cy',sy(p.lat));c.setAttribute('r',p.c?6:5.2);
    c.setAttribute('fill-opacity',p.c?'.92':'.78');
    c.setAttribute('class','dot '+(p.c?'pos':'neg'));c.setAttribute('pointer-events','none');
    svg.appendChild(c);});
  shown.forEach(p=>{                       // transparent hit targets on top
    const h=document.createElementNS(NS,'circle');
    h.setAttribute('cx',sx(p.lon));h.setAttribute('cy',sy(p.lat));h.setAttribute('r',13);
    h.setAttribute('fill','transparent');h.setAttribute('pointer-events','all');h.style.cursor='pointer';
    h.addEventListener('pointerenter',e=>{if(e.pointerType==='mouse')showTip(e,p,false);});
    h.addEventListener('pointermove',e=>{if(e.pointerType==='mouse'&&!pinned)place(e);});
    h.addEventListener('pointerleave',()=>{if(!pinned)hideTip();});
    h.addEventListener('click',e=>{e.stopPropagation();showTip(e,p,true);});
    svg.appendChild(h);});
}
const wrap=document.getElementById('mapwrap');
let pinned=false;
function showTip(e,p,pin){ if(!tip){tip=document.createElement('div');tip.className='tip';wrap.appendChild(tip);}
  tip.innerHTML=`<div class="ta">${p.a}</div>`+
    `<div class="tr"><span>${p.c?'Tested positive':'Not on DOH list'}</span><b>ZIP ${String(p.zip).split('.')[0]}</b></div>`+
    `<div class="tr"><span>Cooling towers</span><b>${p.nt}</b></div>`;
  tip.classList.add('on'); pinned=pin||pinned; place(e);}
function place(e){const r=wrap.getBoundingClientRect();
  const x=e.clientX-r.left, y=e.clientY-r.top;
  const th=tip.offsetHeight||130, tw=tip.offsetWidth||210;
  const above=y-th-14>=0;
  tip.style.left=Math.max(tw/2+6,Math.min(r.width-tw/2-6,x))+'px';
  tip.style.top=(above?y-12:y+16)+'px';
  tip.style.transform=above?'translate(-50%,-100%)':'translate(-50%,0)';}
function hideTip(){if(tip)tip.classList.remove('on');pinned=false;}
svg.addEventListener('click',hideTip);
draw();
</script>
"""
out=(HTML.replace("__DATA__",json.dumps(data,separators=(",",":")))
        .replace("__STREETS__",json.dumps(streets,separators=(",",":"))))
(ROOT/"public_report.html").write_text(out)
print("wrote reports/public_report.html", len(out), "bytes")
