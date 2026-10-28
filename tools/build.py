#!/usr/bin/env python3
"""Build the South Florida driver license walk-in vs appointment guide into site/. Run: python3 tools/build.py
Office list comes from tools/flhsmv_raw.json, parsed from the FLHSMV county location pages on the check date."""
import json,os,sys,re,shutil,urllib.parse
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE); sys.path.insert(0,HERE)
from sitelib import Site,CSS,D,esc,a,href,slug
BASE="https://south-florida-dmv-walkin-guide.vercel.app"
# Shown near the top of every page and in full in the footer.
DISCLAIMER="For general information only. This independent site is not affiliated with the Florida DHSMV, any county tax collector or any government agency. Information can change and may contain errors; always confirm with the official office before you act. Nothing here is legal or professional advice, and we accept no liability for decisions made using it."
# Optional. A non-empty value emits that meta tag. Leave empty to omit it.
VERIFY={"google-site-verification":"XA7XgB_UwrIRvQyNVsnWpSyTyaU6e3-v4g4RBw8RAVI","msvalidate.01":""}
RELATED=[("https://us-passport-walkin-finder.vercel.app/","South Florida passport walk-in finder"),("https://south-florida-dog-beaches.vercel.app/","South Florida dog beaches")]
S=dict(loc="https://www.flhsmv.gov/locations/",bro="https://www.flhsmv.gov/locations/broward/",mia="https://www.flhsmv.gov/locations/miami-dade/",pbc="https://www.flhsmv.gov/locations/palm-beach/",
 nemo="https://nqapflhsmv.nemoqappointment.com",btc="https://browardtax.org/",btcappt="https://appointments.browardtax.org/",btcloc="https://browardtax.org/locations/",btcnews="https://browardtax.org/news/flow-driver-license-aug-2025/",
 mdc="https://www.mdctaxcollector.gov/",mdcdl="https://www.mdctaxcollector.gov/driver-license-and-id-card-services",mdcloc="https://www.mdctaxcollector.gov/locations",mdcappt="https://app.mdctaxcollector.gov/",
 mdcvw="https://app.mdctaxcollector.gov/virtual-walk-in",mdcvwblog="https://www.mdctaxcollector.gov/blog/miami-dade-county-office-of-the-tax-collector-launches-innovative-virtual-walk-in-system-for-driver-license-and-id-services",
 scalp="https://www.mdctaxcollector.gov/blog/miami-dade-county-tax-collector-dariel-fernandez-takes-action-against-appointment-scalping-and-strengthens-community-services",
 clos="https://www.flhsmv.gov/locations/temporary-office-closures/",
 pbtc="https://www.pbctax.gov/driver-license/",pbres="https://www.pbctax.gov/reservations/",wtb="https://www.flhsmv.gov/driver-licenses-id-cards/what-to-bring/",
 usc="https://www.flhsmv.gov/driver-licenses-id-cards/what-to-bring/u-s-citizen/",imm="https://www.flhsmv.gov/driver-licenses-id-cards/what-to-bring/immigrant/",nonimm="https://www.flhsmv.gov/driver-licenses-id-cards/what-to-bring/non-immigrant/",can="https://www.flhsmv.gov/driver-licenses-id-cards/what-to-bring/canadian/",
 mydmv="https://mydmvportal.flhsmv.gov",passport="https://us-passport-walkin-finder.vercel.app",
 newres="https://www.flhsmv.gov/new-resident/",visit="https://www.flhsmv.gov/driver-licenses-id-cards/visiting-florida-faqs/",
 wtbfaq="https://www.flhsmv.gov/driver-licenses-id-cards/what-to-bring/frequently-asked-questions/",fees="https://www.flhsmv.gov/fees/",
 exam="https://www.flhsmv.gov/driver-licenses-id-cards/licensing-requirements-teens-graduated-driver-license-laws-driving-curfews/class-e-knowledge-exam-driving-skills-test/",
 hand="https://www.flhsmv.gov/pdf/handbooks/englishdriverhandbook.pdf",sb="https://www.flhsmv.gov/driver-licenses-id-cards/visiting-florida-faqs/sb1718/",
 s01="https://www.flsenate.gov/Laws/Statutes/2026/322.01",s03="https://www.flsenate.gov/Laws/Statutes/2026/322.03",s031="https://www.flsenate.gov/Laws/Statutes/2026/322.031",
 s033="https://www.flsenate.gov/Laws/Statutes/2026/322.033",s04="https://www.flsenate.gov/Laws/Statutes/2026/322.04",s08="https://www.flsenate.gov/Laws/Statutes/2026/322.08",
 s12="https://www.flsenate.gov/Laws/Statutes/2026/322.12",s135="https://www.flsenate.gov/Laws/Statutes/2026/322.135",s18="https://www.flsenate.gov/Laws/Statutes/2026/322.18",
 s21="https://www.flsenate.gov/Laws/Statutes/2026/322.21",pbex="https://www.pbctax.gov/driver-license/exchange-out-of-state-driver-license-id-card/",
 pbdl="https://www.pbctax.gov/driver-license/",btdl="https://browardtax.org/driverlicense/")
def src(*k): return ' <span class="src">['+', '.join(a(S[x]) for x in k)+']</span>'
raw=json.load(open(os.path.join(HERE,'flhsmv_raw.json')))
COUNTIES={'broward':('Broward','Broward County','bro'),'miami-dade':('Miami-Dade','Miami-Dade County','mia'),'palm-beach':('Palm Beach','Palm Beach County','pbc')}
VW={'Downtown Miami','Miami Central','Midway Crossings (Suite 82C)'}
recs=[]
for r in raw:
    if 'DL' not in r['group']: continue
    nm=r['name'].lstrip('*'); tc=r['name'].startswith('*')
    links=[l['url'] for l in r['links'] if 'mydmv' not in l['url']]
    book=links[0] if links else ''
    c=r['county']
    if c=='Broward':
        if tc: op='Broward County Tax Collector (tax collector-sponsored)'; pol=f'The Florida Department of Highway Safety and Motor Vehicles links this office to the Broward County Tax Collector appointment page{src("bro")}. Walk-in service is not stated on that county page. A residency limit and a name-match rule could not be reconfirmed on {D}, so they are not stated here.'; st='appt'
        else: op='FLHSMV (state-run)'; pol=f'The Florida Department of Highway Safety and Motor Vehicles links this office to its appointment system and says many offices require appointments{src("loc")}. Walk-in service is not stated on the official page.'; st='unclear'
    elif c=='Miami-Dade':
        op='Miami-Dade County Tax Collector'
        if nm in VW:
            pol=f'The Tax Collector virtual walk-in post names this office. Scan the posted QR code, get a virtual time, and return 15 minutes before it. Appointments booked online have priority{src("mdcvwblog","mdcvw")}. The Tax Collector also says the offices it manages take appointments or walk-in service during operating hours{src("mdcdl")}.'
            st='walk'
        else:
            pol=f'The Tax Collector says the offices it has taken over take appointments or walk-ins during operating hours, and that it has taken over eight offices. It does not name those eight. This office is on the Tax Collector locations list, and the state locations page links it to the Tax Collector booking system. Walk-in service is not stated for this office by name{src("mdcdl","mdcloc","mia")}.'
            st='gap'
    else:
        op='Palm Beach County Tax Collector'; pol=f'"By Reservation Only", Palm Beach County residents only{src("pbc")}. The Tax Collector says a reservation is required for in-person service{src("pbres")}.'; st='appt'
    notes=[x for x in r['comments'] if x and 'MyDMV' not in x and 'mail correspondence' not in x and not x.startswith('PO Box') and 'Residents Only' not in x and 'By Reservation' not in x]
    recs.append(dict(county=c,name=nm,address=r['address'],phone=r['phone'],hours=r['hours'],group=r['group'],op=op,policy=pol,status=st,book=book,notes=notes,tc=tc))
json.dump(recs,open(os.path.join(HERE,'offices_parsed.json'),'w'),indent=1)
G=[("County offices",[('counties/broward/index.html','Broward offices'),('counties/miami-dade/index.html','Miami-Dade offices'),('counties/palm-beach/index.html','Palm Beach offices')]),
 ("Before your visit",[('walk-in-vs-appointment/index.html','Walk-in or appointment'),('what-to-bring/index.html','What to bring'),('new-to-florida/index.html','New to Florida')]),
 ("Stay safe",[('fake-appointment-sites/index.html','Fake appointment sites'),('faq/index.html','Common questions')]),
 ("Using this guide",[('find/index.html','All pages'),('disclaimer/index.html','Disclaimer')])]
# One plain-language line per page. Same meaning as the page itself. Abbreviations are written out.
BLURB={
 'counties/broward/index.html':'Every driver license and identification office in Broward County listed by the Florida Department of Highway Safety and Motor Vehicles, with address, hours, the official walk-in policy, and the booking link.',
 'counties/miami-dade/index.html':'Every driver license and identification office in Miami-Dade County listed by the Florida Department of Highway Safety and Motor Vehicles, with address, hours, the official walk-in policy, and the booking link.',
 'counties/palm-beach/index.html':'Every driver license and identification office in Palm Beach County listed by the Florida Department of Highway Safety and Motor Vehicles, with address, hours, the official walk-in policy, and the booking link.',
 'walk-in-vs-appointment/index.html':'South Florida driver license offices grouped by the official walk-in policy: walk-in accepted, reservation required, or not stated.',
 'what-to-bring/index.html':'The Florida Department of Highway Safety and Motor Vehicles REAL ID document list for United States citizens: identity, Social Security, and two proofs of a Florida address, plus name change rules.',
 'new-to-florida/index.html':'Deadline, documents, exam rules, and fees for transferring an out-of-state or foreign license in Broward, Miami-Dade, or Palm Beach.',
 'fake-appointment-sites/index.html':'Official warning about fake driver license appointment sites in Miami-Dade, and the only official booking pages for Broward, Miami-Dade and Palm Beach.',
 'faq/index.html':'Sourced answers about walk-ins, appointments, residency rules and REAL ID documents at South Florida driver license offices.',
 'find/index.html':'Every page on this guide, listed by topic.',
 'disclaimer/index.html':'Legal limits of this unofficial South Florida driver license walk-in guide: accuracy, no warranty, liability, external links, affiliation, and official sources.'}
ALIAS={
 'counties/broward/index.html':'Broward DMV FLHSMV office hours appointment Lauderdale Lakes',
 'counties/miami-dade/index.html':'Miami-Dade DMV virtual walk-in tax collector offices',
 'counties/palm-beach/index.html':'Palm Beach DMV reservation residents only',
 'walk-in-vs-appointment/index.html':'walk-in versus appointment reservation required',
 'what-to-bring/index.html':'REAL ID documents SSN Social Security proof of address',
 'new-to-florida/index.html':'new resident transfer out of state foreign license fees',
 'fake-appointment-sites/index.html':'fake scam appointment booking official',
 'faq/index.html':'FAQ questions walk-in Saturday holiday renew',
 'find/index.html':'search index all pages',
 'disclaimer/index.html':'disclaimer liability not a government website'}
SEQ=[
 ['counties/broward/index.html','counties/miami-dade/index.html','counties/palm-beach/index.html'],
 ['walk-in-vs-appointment/index.html','what-to-bring/index.html','new-to-florida/index.html']]
READ_NEXT={
 'index.html':['walk-in-vs-appointment/index.html','what-to-bring/index.html','fake-appointment-sites/index.html'],
 'counties/broward/index.html':['counties/miami-dade/index.html','counties/palm-beach/index.html','walk-in-vs-appointment/index.html'],
 'counties/miami-dade/index.html':['counties/broward/index.html','counties/palm-beach/index.html','walk-in-vs-appointment/index.html'],
 'counties/palm-beach/index.html':['counties/broward/index.html','counties/miami-dade/index.html','walk-in-vs-appointment/index.html'],
 'walk-in-vs-appointment/index.html':['what-to-bring/index.html','new-to-florida/index.html','fake-appointment-sites/index.html'],
 'what-to-bring/index.html':['new-to-florida/index.html','walk-in-vs-appointment/index.html','fake-appointment-sites/index.html'],
 'new-to-florida/index.html':['what-to-bring/index.html','walk-in-vs-appointment/index.html','counties/miami-dade/index.html'],
 'fake-appointment-sites/index.html':['walk-in-vs-appointment/index.html','what-to-bring/index.html','faq/index.html'],
 'faq/index.html':['fake-appointment-sites/index.html','walk-in-vs-appointment/index.html','what-to-bring/index.html'],
 'find/index.html':['walk-in-vs-appointment/index.html','faq/index.html','disclaimer/index.html'],
 'disclaimer/index.html':['find/index.html','faq/index.html','fake-appointment-sites/index.html'],
 '404.html':['walk-in-vs-appointment/index.html','find/index.html','faq/index.html']}
FOOT=f'Unofficial, independent guide. Not affiliated with FLHSMV or any county tax collector. We do not sell appointments, and nobody legitimately can: book only on {a(S["loc"],"flhsmv.gov")}, {a(S["mdc"],"mdctaxcollector.gov")}, {a(S["btc"],"browardtax.org")} or {a(S["pbtc"],"pbctax.gov")}. Office data from the FLHSMV county location pages; policies from each tax collector site.'
s=Site(ROOT,BASE,"South Florida DMV Walk-in Guide",G,FOOT,CSS,sequences=SEQ,summaries=BLURB,read_next=READ_NEXT,aliases=ALIAS,related=RELATED,verify=VERIFY,disclaimer=DISCLAIMER)
LABELS={p:t for g,items in G for p,t in items}
grouped=[p for g,items in G for p,t in items]
assert set(BLURB)==set(grouped)
assert set(ALIAS)==set(grouped)
assert set(READ_NEXT)==set(grouped)|{'index.html','404.html'}
for dests in READ_NEXT.values():
    assert len(dests)==3
    for dest in dests:
        assert dest in s.titles, dest
def jump(path):
    return f'<a class="jump" href="{href(path)}"><span class="lt">{esc(LABELS[path])}</span><span class="ls">{esc(BLURB[path])}</span></a>'
def link_list(paths):
    return '<ul class="link-grid">'+''.join(f'<li>{jump(p)}</li>' for p in paths)+'</ul>'
START=[("Check the walk-in rule",['walk-in-vs-appointment/index.html']),
 ("Open your county",['counties/broward/index.html','counties/miami-dade/index.html','counties/palm-beach/index.html']),
 ("Get your documents ready",['what-to-bring/index.html','new-to-florida/index.html']),
 ("Book on an official page",['fake-appointment-sites/index.html'])]
start_here='<h2>Start here</h2><p>Use these steps to find the page you need.</p><ol class="timeline">'+''.join(
 f'<li class="period"><h3>{esc(title)}</h3><ol class="period-pages">'+''.join(f'<li>{jump(p)}</li>' for p in paths)+'</ol></li>' for title,paths in START)+'</ol>'
TOP=['walk-in-vs-appointment/index.html','what-to-bring/index.html','counties/miami-dade/index.html','counties/broward/index.html','counties/palm-beach/index.html','fake-appointment-sites/index.html','new-to-florida/index.html','faq/index.html']
top_tasks='<h2>Top tasks</h2><p>The pages people open most often. Each link goes to one page.</p>'+link_list(TOP).replace('class="link-grid"','class="tasks"',1)
all_topics='<h2>All topics</h2><p>Every page on this guide, grouped by subject.</p>'+''.join(
 f'<section class="topic"><h3 id="{slug(g)}">{esc(g)}</h3>'+link_list([p for p,t in items])+'</section>' for g,items in G)
FAKE=f'<div class="card warn"><strong>Warning: fake appointment websites.</strong> The Miami-Dade Tax Collector warns residents about unofficial appointment websites issuing invalid confirmations, and says to schedule only through mdctaxcollector.gov and verify any questionable appointment directly with the office{src("mdc")}. Book only on the official sites: {a(S["mdcappt"],"app.mdctaxcollector.gov")} (Miami-Dade), {a(S["btcappt"],"appointments.browardtax.org")} or {a(S["nemo"],"the Florida Department of Highway Safety and Motor Vehicles appointment system")} (Broward), {a(S["pbres"],"pbctax.gov/reservations")} (Palm Beach). Do not pay a third party for a slot. The Tax Collector says an appointment should be free and that residents should not pay an unregulated third party for one{src("scalp")}. {a("/fake-appointment-sites/","How to spot a fake")}.</div>'
def fake(r): return FAKE
CONF=f'''<div class="card conf"><strong>Conflicts and gaps in official sources ({D})</strong><ul>
<li>The Florida Department of Highway Safety and Motor Vehicles says standard business hours are 9 a.m. to 12 p.m. and 1 p.m. to 5 p.m., closed for lunch{src("loc")}, but its own Broward office rows list 8:00 a.m. to 5:00 p.m. with no lunch break{src("bro")}. Hours in the tables are the office rows.</li>
<li>State offices are listed as closed on Veterans Day, Wednesday 11 Nov 2026, Thanksgiving Day, Thursday 26 Nov 2026, the Friday after Thanksgiving, 27 Nov 2026, and Christmas Day, Friday 25 Dec 2026. The same page says county tax collector and license plate agent offices may not follow those closures{src("clos")}.</li>
<li>The Miami-Dade Tax Collector says it has "assumed control of eight offices" and that the state department still manages appointments at offices not yet transferred. It does not name the eight. Its locations page lists 13 offices, and the state locations page links all 13 Miami-Dade driver license offices to the Tax Collector booking system{src("mdcdl","mdcloc","mia")}.</li>
<li>Phone and address mismatches for the same Miami-Dade offices: the state page lists 305-375-5548 for Coral Reef and for Florida City, while the Tax Collector locations page lists 305-375-5448 for both. The state page puts Hialeah Gardens in Hialeah, and the Tax Collector page puts it in Hialeah Gardens. The state page says Richard Gerstein Justice Center is Suite 131-133, and the Tax Collector page says Suite 133{src("mia","mdcloc")}.</li>
<li>Broward: a Tax Collector news post dated 23 May 2026 says the office prepares to take over driver license services in summer 2026{src("btcnews")}. Event notes on its home page on {D} say the office will lead local driver license services beginning 2026. The same home page says its offices will be closed on 28 Oct 2026 for a Professional Development Day, and it also lists an early close that day at 11:30 a.m.{src("btc")}. The Tax Collector locations page lists Fort Lauderdale (115 S. Andrews Ave), Plantation and Lauderdale Lakes{src("btcloc")}. The state page lists Plantation as motor vehicle services only and does not list 115 S. Andrews Ave{src("bro")}.</li>
<li>Virtual walk-in: the Miami-Dade launch post (May 2025) names three offices. No current official list of all participating offices was found{src("mdcvwblog")}.</li></ul></div>'''
TAGS={'walk':'<span class="tag ok">walk-in accepted (official)</span>','appt':'<span class="tag no">appointment or reservation required</span>','unclear':'<span class="tag mix">appointments; walk-in not stated</span>','gap':'<span class="tag mix">walk-in not confirmed by name</span>'}
def load_coords():
    data=json.load(open(os.path.join(HERE,'office_coords.json')))
    found={}
    for row in data['offices']:
        key=(row['county'],row['name'],row['address'])
        if key in found: raise SystemExit('Duplicate coordinate record for '+row['name'])
        lat,lon=row.get('lat'),row.get('lon')
        if lat is None or lon is None:
            if not row.get('reason'): raise SystemExit('Unpinned office needs a reason: '+row['name'])
        else:
            if type(lat) not in (int,float) or type(lon) not in (int,float): raise SystemExit('Bad coordinates for '+row['name'])
            if not (25.2<=float(lat)<=27.3 and -80.95<=float(lon)<=-79.9): raise SystemExit('Coordinates outside South Florida for '+row['name'])
            if not row.get('osm_id') or not row.get('matched'): raise SystemExit('Pinned office needs an OSM id and a match note: '+row['name'])
        found[key]=row
    return found
COORDS=load_coords()
def pin_row(r):
    row=COORDS.get((r['county'],r['name'],r['address']))
    if row is None: raise SystemExit('No coordinate record for '+r['county']+' '+r['name'])
    if row.get('lat') is None or row.get('lon') is None: return None
    return row
for _r in recs: pin_row(_r)
def directions_url(address):
    return 'https://www.google.com/maps/dir/?api=1&destination='+urllib.parse.quote(address,safe='')
def directions_link(r):
    url=directions_url(r['address'])
    return f'<a href="{esc(url)}" target="_blank" rel="noopener">Get directions<span class="sr-only"> to {esc(r["name"])}, {esc(r["address"])} (opens in a new tab)</span></a>'
def map_block(rows,title,label):
    pins=[]
    for r in rows:
        row=pin_row(r)
        if not row: continue
        pins.append({'name':r['name'],'address':r['address'],'lat':row['lat'],'lon':row['lon'],'directions':directions_url(r['address'])})
    if not pins: return ''
    note_id=slug(title)+'-note'
    payload=json.dumps(pins,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    note='The list above is the full set of addresses. The map is an extra view. A pin is shown only when the official street address could be placed. Offices that are very close share one pin until you zoom in, and that pin lists each office. Choose a pin to read the name and address. Scrolling the page does not zoom the map. Click the map if you want the scroll wheel to zoom.'
    return (f'<section class="map-block"><h2>{esc(title)}</h2><p id="{note_id}">{esc(note)}</p>'
        f'<div class="map-frame"><div class="office-map" role="region" tabindex="-1" aria-label="{esc(label)}" data-label="{esc(label)}" aria-describedby="{note_id}" data-pins="{esc(payload)}">'
        f'<p class="map-fallback">The map is not available. Every address is in the list above.</p></div></div></section>'
        f'<script src="/map.js" defer></script>')
_filter_n=0
def table(rows):
    global _filter_n
    _filter_n+=1
    fid=f'office-filter-{_filter_n}'
    t=f'<div class="filter-block"><label for="{fid}">Filter by city or name</label><input id="{fid}" class="office-filter" type="search" autocomplete="off" oninput="var v=this.value.toLowerCase();this.closest(\'.filter-block\').querySelectorAll(\'table tr\').forEach(function(r){{if(r.querySelector(\'td\'))r.style.display=r.textContent.toLowerCase().indexOf(v)>-1?\'\':\'none\'}})"><div class="wrap"><table><tr><th>Office</th><th>Address and phone</th><th>Hours (FLHSMV listing)</th><th>Walk-in policy as officially stated</th><th>Official booking</th></tr>'
    for r in rows:
        n=('<br><span class="src">'+esc('; '.join(r['notes']))+'</span>') if r['notes'] else ''
        t+=f'<tr><td><strong>{esc(r["name"])}</strong><br><span class="src">{esc(r["group"])} services. {esc(r["op"])}</span>{n}</td><td>{esc(r["address"])}<br>{directions_link(r)}<br>{esc(r["phone"])}</td><td>{"<br>".join(esc(h) for h in r["hours"])}</td><td>{TAGS[r["status"]]}<br>{r["policy"]}</td><td>{a(r["book"],"Book (official)") if r["book"] else "Not linked"}</td></tr>'
    return t+'</table></div></div>'
CC={k:[r for r in recs if r['county']==v[0]] for k,v in COUNTIES.items()}
b=f'''<h1>South Florida DMV: walk-in or appointment?</h1><p>Every driver license and ID card office in Broward, Miami-Dade and Palm Beach counties listed by FLHSMV on {D}{src("loc")}, with hours and the walk-in rule as each operator states it. {len(recs)} offices in total.</p>
{fake('')}
{start_here}
{top_tasks}
<div class="wrap"><table><tr><th>County</th><th>Offices</th><th>Who runs them</th><th>Walk-ins, as officially stated</th></tr>
<tr><td>{a("/counties/miami-dade/","Miami-Dade")}</td><td>{len(CC["miami-dade"])}</td><td>County Tax Collector</td><td>Stated for offices the Tax Collector has taken over. It says that is eight offices and does not name them. A May 2025 post names three offices for a virtual walk-in queue. Online appointments have priority{src("mdcdl","mdcvwblog")}</td></tr>
<tr><td>{a("/counties/broward/","Broward")}</td><td>{len(CC["broward"])}</td><td>State department (4), Tax Collector (Lauderdale Lakes)</td><td>Not stated. The state department says many offices require appointments{src("loc")}</td></tr>
<tr><td>{a("/counties/palm-beach/","Palm Beach")}</td><td>{len(CC["palm-beach"])}</td><td>County Tax Collector</td><td>No. Reservation required, county residents only{src("pbres","pbc")}</td></tr></table></div>
<h2>Skip the office if you can</h2><p>Many renewals and replacements can be done online at {a(S["mydmv"],"MyDMV Portal")}{src("mia","mdcdl")}. You must visit in person with documents for a first license or ID, if your card has no star, or after a legal name change{src("wtb")}. See {a("/what-to-bring/","what to bring")}.</p>
<p>Moving from another state or country? {a("/new-to-florida/","Transferring an out-of-state or foreign license")} covers the deadline, documents, tests, and fees, including where the official sources disagree.</p>
{CONF}
<p>Need a U.S. passport instead? See the {a(S["passport"],"South Florida passport walk-in finder")}.</p>
<p class="src">About community reports: we do not publish Reddit or social media wait-time reports, because they could not be verified against official sources.</p>
{all_topics}'''
s.page('index.html',"South Florida DMV walk-in vs appointment, by county","Which South Florida driver license and ID offices take walk-ins and which need appointments, with hours, addresses and official booking links.",b)
for k,(short,full,sk) in COUNTIES.items():
    extra={'miami-dade':f'<div class="card note"><strong>Miami-Dade virtual walk-in.</strong> Arrive at the office, scan the posted QR code, register and receive a virtual appointment time, and return 15 minutes before it to check in. Pre-booked online appointments always have priority{src("mdcvwblog")}. The virtual walk-in page says to verify your location to continue{src("mdcvw")}. Hours: most Tax Collector offices Monday to Friday 8:00 a.m. to 5:00 p.m. and Saturday at select locations 8:00 a.m. to 1:00 p.m., except North Dade Justice{src("mdcdl")}. Driving tests and commercial driver licenses only at selected offices{src("mdcdl")}.</div>',
     'broward':f'<div class="card note"><strong>Broward booking.</strong> State-run offices link to the {a(S["nemo"],"Florida Department of Highway Safety and Motor Vehicles appointment system")}. Lauderdale Lakes links to {a(S["btcappt"],"appointments.browardtax.org")}{src("bro")}. A residency limit and a name-match rule on that appointment page could not be reconfirmed on {D}, so they are not stated here. State-run offices accept cash, check, Visa, MasterCard, Discover Card, and American Express. A knowledge exam with an interpreter is by appointment only and is limited to one attempt per day{src("bro")}. On the Tax Collector home page, Driver Assistance Service Hub (DASH) events list these select transactions: standard driver license renewals, replacement licenses for lost, stolen, or damaged cards, address updates, name changes, and identification card issuance. Those notes say no walk-ins are accepted and the service is reserved for Broward County residents only{src("btc")}. That home page also says its offices will be closed on 28 Oct 2026 for a Professional Development Day, and it lists an early close that day at 11:30 a.m.{src("btc")}.</div>',
     'palm-beach':f'<div class="card note"><strong>Palm Beach reservations.</strong> All Palm Beach offices are tax collector-sponsored; a tax collector service fee is added{src("pbc")}. A reservation is required for in-person service and is for Palm Beach County residents only; non-residents are pointed to FLHSMV locations{src("pbres")}. Customers who are not REAL ID compliant must schedule a reservation, and the office does not issue licenses or IDs to undocumented immigrants{src("pbtc")}.</div>'}[k]
    b=f'<h1>Driver license and ID offices in {full}: walk-in or appointment</h1><p>{len(CC[k])} offices offering driver license services, from the FLHSMV {full} page{src(sk)}. Motor vehicle only offices and license plate agents are not listed.</p>{fake("../../")}{extra}'+table(CC[k])+map_block(CC[k],f'Map of these {short} County offices',f'Map of {full} driver license offices')+CONF
    s.page(f'counties/{k}/index.html',f"{full} DMV offices: walk-in or appointment",f"Every driver license and ID office in {full} listed by FLHSMV, with address, hours, official walk-in policy and booking link.",b)
b=f'<h1>Walk-in vs appointment at South Florida driver license offices</h1>{fake("../")}<h2>Offices where walk-ins are officially accepted</h2>'+table([r for r in recs if r['status']=='walk'])+'<h2>Walk-in not confirmed for this office by name</h2><p>The Miami-Dade Tax Collector states walk-in service for the offices it has taken over, says that is eight offices, and does not name them{src("mdcdl")}.</p>'+table([r for r in recs if r['status']=='gap'])+'<h2>Appointment or reservation required</h2>'+table([r for r in recs if r['status']=='appt'])+'<h2>Appointment system linked, walk-in not stated</h2>'+table([r for r in recs if r['status']=='unclear'])+map_block(recs,'Map of the offices on this page','Map of the driver license offices listed on this page')+CONF
s.page('walk-in-vs-appointment/index.html',"Which South Florida DMV offices take walk-in visits","South Florida driver license offices grouped by official walk-in policy: walk-in accepted, reservation required, or not stated.",b)
b=f'''<h1>What to bring for a Florida REAL ID driver license or ID card</h1><p>From the FLHSMV U.S. citizen checklist{src("usc")}. Non-citizens: see the {a(S["imm"],"immigrant")}, {a(S["nonimm"],"non-immigrant")} and {a(S["can"],"Canadian")} lists.</p>
<div class="card"><p>You must visit an office with documents for your first license or ID, if your current card has no star, or if you legally changed your name since your last card{src("wtb")}. Once you have provided them, you only need them again if your information changes{src("wtb")}.</p></div>
<h2>1. Primary identification (one original)</h2><div class="card"><ul><li>U.S. birth certificate (Puerto Rico certificates must be issued after July 1, 2010). Only county health department or CDC Bureau of Vital Statistics certificates; hospital certificates are not accepted.</li><li>Valid U.S. passport or passport card</li><li>Consular Report of Birth Abroad</li><li>Certificate of Naturalization (N-550 or N-570)</li><li>Certificate of Citizenship (N-560 or N-561)</li></ul>Bring marriage certificates, court orders or divorce decrees to link names, unless your valid U.S. passport shows your current name{src("usc")}.</div>
<h2>2. Proof of Social Security number (one original)</h2><div class="card"><ul><li>Social Security card in your current name</li><li>W-2 (not handwritten)</li><li>Paycheck or pay stub</li><li>Social Security Administration 1099 (SSA-1099)</li><li>Any 1099 (not handwritten)</li></ul>The name on your Social Security number must match the license. Allow 24 to 48 hours after changing your name with Social Security{src("usc")}.</div>
<h2>3. Two proofs of Florida residential address</h2><div class="card"><p>Your current license or identification card does not count. Printouts and faxes are accepted. The state list says these documents include, but are not limited to, the items below. Out-of-state addresses are not accepted for a Class E license or identification card{src("usc")}.</p><ul><li>Deed, mortgage, mortgage statement or lease</li><li>Florida voter registration card</li><li>Florida vehicle registration or title</li><li>Dated within the last 60 days: utility bill, auto payment booklet, selective service card, medical card or bill, home or auto insurance policy or bill, W-2, 1099 or pay stub, bank or credit card statement, government mail, or a shelter or transitional housing letter</li></ul>
<p>If none are in your name, the person you live with can complete a Certification of Address (HSMV 71120) with two of their own proofs, signed in front of an examiner or a notary{src("usc","mdcdl")}. CDL applicants cannot use it{src("usc")}.</p></div>
<h2>Name changes</h2><div class="card">Bring the original or certified marriage certificate, divorce decree or court order; photocopies and church-issued certificates are not accepted{src("usc")}.</div>
<p>Since May 7, 2025, TSA accepts only starred (REAL ID) licenses and IDs at airports; a U.S. passport can be used instead{src("wtb")}.</p>'''
s.page('what-to-bring/index.html',"Florida REAL ID documents: what to bring to the DMV","FLHSMV REAL ID document list for U.S. citizens: identity, Social Security and two proofs of Florida address, plus name change rules.",b)
b=f'''<h1>New to Florida: transferring an out-of-state or foreign driver license</h1>
<p>For people who have just moved to Broward, Miami-Dade, or Palm Beach and already hold a driver license from another U.S. state or from another country. The rules below come from the Florida Department of Highway Safety and Motor Vehicles (FLHSMV), the 2026 Florida Statutes, the Official Florida Driver License Handbook (revised August 2023), and the county tax collector sites. Where those sources do not match, this page says so. No wait times or tips from social media are included.</p>
<p>A first Florida license is issued in person. Document lists are on {a("/what-to-bring/","what to bring")}, and on the FLHSMV checklists for a {a(S["usc"],"U.S. citizen")}, an {a(S["imm"],"immigrant")}, a {a(S["nonimm"],"non-immigrant")}, and a {a(S["can"],"Canadian")}{src("wtb")}.</p>
<h2>When a Florida license is required</h2>
<p>FLHSMV's new-resident page says you must get a valid Florida driver license within 30 days of establishing residency to drive on Florida roads. It says you may be considered a resident when you start work or a trade in Florida, enroll your children in a Florida public school, register to vote, file for a homestead exemption, or live in Florida for more than six consecutive months{src("newres")}. The visiting-Florida questions page uses the same 30-day sentence and the same five triggers{src("visit")}.</p>
<p>The statute reads differently. Section 322.01 defines a resident as a person whose principal place of domicile has been in Florida for more than six consecutive months, who has registered to vote, who has made a statement of domicile under section 222.17, or who has filed for a homestead tax exemption. Employment and public school enrollment are not in that definition{src("s01")}. Section 322.031 is the 30-day rule, and it applies to a nonresident, other than a migrant or seasonal farm worker, who accepts employment or engages in a trade, profession, or occupation in Florida, or who enters children in a Florida public school. That person must get a Florida driver license within 30 days after the employment or education begins, if he or she drives on Florida highways. A spouse or dependent child must do the same within those 30 days before driving{src("s031")}.</p>
<div class="card conf"><strong>The 30-day clock is not stated the same way.</strong> FLHSMV's new-resident and visiting pages start the 30 days when residency is established, and they treat a job, public school, voter registration, homestead, or six months in Florida as residency. Section 322.031 starts the 30 days when a nonresident begins work or public school and drives here. Section 322.01 does not call employment or school enrollment residency. The August 2023 handbook follows the statute on this split: a resident must have a Florida license to drive, and a nonresident who takes a job or enrolls a child has 30 days in order to drive. The handbook also says it is not a legal authority and does not reflect legislative changes after August 2023{src("newres","visit","s01","s031","hand")}.</div>
<p>Section 322.031 has exemptions. An active-duty member of the United States Armed Forces in Florida, and a spouse or dependent living with that member, do not have to get a Florida license because of a job or public school if the person has a valid military identification card and either a valid driver license or learner permit from another state, or a valid military driving permit. A nonresident who lives in another state, commutes into Florida for work, and holds a valid license from that state does not need a Florida license only because of the job. A nonresident full-time student at a college or university is exempt during that enrollment. A nonresident in Florida for up to six months in a work-study program is also exempt for that program, when the academic credit comes from a college whose credits or degrees are accepted by at least three accredited institutions. Those student exemptions require a valid license from another state{src("s031")}. The handbook states the military, commuter, and college exemptions in shorter form, and it also lists a U.S. government employee on official business and a 60-day exemption for some contract workers{src("hand")}.</p>
<p>Once you are a resident, section 322.03 says that, except as the chapter allows, you may not drive on a highway in Florida without a valid Florida driver license{src("s03")}.</p>
<p>If you are still a nonresident and section 322.031 does not apply to you, section 322.04 lets you drive without a Florida license while you have a valid noncommercial license from your home state or country with you. The age cutoff is 16 for a vehicle that needs a Class E license in Florida, and 18 for another noncommercial vehicle. The home license must not be invalid under section 322.033. This exemption does not apply to a person section 322.031 covers{src("s04","s033")}. The handbook instead says a nonresident from another country needs an International Driving Permit plus a valid license from that country. Section 322.04 does not mention an International Driving Permit{src("hand","s04")}.</p>
<p>Palm Beach County's transfer page states a narrower deadline: a Florida license within 30 days of accepting employment, engaging in a trade, profession, or occupation, or enrolling a child in public school. That page does not mention voter registration, homestead, or six months of residence{src("pbex")}.</p>
<h2>Transferring a license from another U.S. state</h2>
<p>Apply in person at an office that issues driver licenses. FLHSMV says you will take a vision test, and that you may be eligible for a license without a written test or a road test{src("newres")}. Its document questions page says a valid out-of-state license is accepted in exchange for the written and driving exams, that every out-of-state driver takes the vision test, and that other testing may be required if there is a reason to think the person cannot drive safely. That answer also says an out-of-state license is not accepted as primary identification{src("wtbfaq")}.</p>
<p>Section 322.12 says every applicant for an original license is to pass an examination, and that the department may waive the knowledge, endorsement, and skills tests for an otherwise qualified applicant who surrenders a valid license from another state, a province of Canada, or the United States Armed Forces and who applies for an equal or lesser class. The Class E examination in that section still includes an eyesight test and a hearing test. Those two tests are not in the waiver sentence{src("s12","s18")}. The questions page and the handbook tell transferring drivers to expect a vision test. They do not say whether the hearing test is given on a transfer{src("wtbfaq","hand")}.</p>
<div class="card"><strong>REAL ID documents for a first Florida card.</strong> The REAL ID Act requires original documents for identity, a Social Security number (SSN), and residential address the first time the credential is issued in an office. Bring them for a first Florida license or ID card, if your current card has no star, or after a legal name change. After they are on file, bring them again only if your information changes{src("wtb","usc")}.</div>
<h2>Identity</h2>
<p>For a U.S. citizen, bring one original primary document: a U.S. birth certificate (a Puerto Rico certificate must be issued after July 1, 2010, and a hospital certificate is not accepted), a valid U.S. passport or passport card, a Consular Report of Birth Abroad, a Certificate of Naturalization (N-550 or N-570), or a Certificate of Citizenship (N-560 or N-561). If the name differs, bring the marriage certificates, court orders, or divorce decrees that link the names, unless your valid U.S. passport shows your current name{src("usc")}.</p>
<p>The questions page says an out-of-state driver license is not primary identification. Section 322.08 lists, as one acceptable proof of identity, a driver license record or identification card record from another jurisdiction that complies with the REAL ID Act and that was issued only after a similar identity document. The plastic card and that record are not described the same way. Bring a primary document from the checklist for your status, and bring the out-of-state license as well{src("wtbfaq","s08")}.</p>
<h2>Social Security number</h2>
<p>Bring one original with your complete name and complete SSN: a Social Security card in your current name, a W-2 that is not handwritten, a pay stub, an SSA-1099, or any 1099 that is not handwritten. The name on the SSN must match the name that will be on the license. After a name change with the Social Security Administration, the citizen checklist says to wait 24 to 48 hours{src("usc")}. U.S. citizens and immigrants must have proof of an SSN. A non-immigrant must provide that proof as well, unless the immigration status does not authorize work in the United States. A non-immigrant who presents work-authorized documents but is not authorized to work must bring a Social Security Administration letter of ineligibility, and the reason on that letter cannot be a failure to bring documents{src("wtbfaq")}. The non-immigrant checklist says a non-immigrant in the country without a work visa does not have to bring the letter that says an SSN was never issued. The two pages do not explain how those rules fit together{src("wtbfaq","nonimm")}.</p>
<h2>Two proofs of a Florida residential address</h2>
<p>Bring two different documents that show your Florida residential address. Your current license or ID card does not count. Printouts and faxes are accepted. An out-of-state or U.S. territory address is not accepted for a Class E license or an ID card{src("usc")}. The citizen checklist includes a deed, mortgage, mortgage statement, or lease; a Florida voter registration card; a Florida vehicle registration or title; and, dated within the last 60 days, items such as a utility bill, an insurance bill, a pay stub, a bank statement, or government mail. If nothing is in your name, the person you live with can complete a Certification of Address (HSMV 71120) with two proofs of their own, signed in front of an examiner or a notary. A commercial learner's permit or commercial driver license (CDL) applicant cannot use that form{src("usc")}. Full lists: {a("/what-to-bring/","what to bring")}.</p>
<p>If you cannot produce the documents, the visiting page says you may be issued a 60-day temporary driving permit when the out-of-state license is valid or has been expired for 60 days or less{src("visit")}. That permit is separate from the paper permit for non-U.S. citizens described below.</p>
<p>The handbook says a license from another state or a U.S. territory must be surrendered when the Florida license is issued. Section 322.03 says a person may not have more than one valid driver license at any time{src("hand","s03")}.</p>
<h2>A license from another country</h2>
<p>Section 322.12 says the department shall examine every applicant, including a person licensed in another state or country, except as the chapter provides. The waiver in that section names only another U.S. state, a province of Canada, or the United States Armed Forces, and only when that license is surrendered and the Florida license is an equal or lesser class. France, Germany, Taiwan, and South Korea are not named{src("s12")}.</p>
<p>The August 2023 handbook says the Class E knowledge exam and the driving skills exam are waived for a valid license from a U.S. state, territory, or possession; the U.S. military; Canada; France; Germany (driving skills test only); the Republic of China (Taiwan); or South Korea. A vision exam is still required. It says state and U.S. territory licenses must be surrendered. It says a Canadian driver can have the exams waived by surrendering the Canadian license, and that keeping the Canadian license means the Class E exams are required{src("hand")}.</p>
<p>Palm Beach County says it will waive the Class E knowledge and skills exams for a license from any U.S. state; a U.S. territory or possession, including the Panama Canal Zone if issued before January 1, 2000; Canada; Germany (skills exam only); France; the Republic of China (Taiwan); the Republic of Korea (South Korea); or the United States Armed Forces, whether the military license is for on-base or off-base driving. Its Canada note matches the handbook. Palm Beach also requires the REAL ID documents{src("pbex")}.</p>
<div class="card conf"><strong>Foreign exam waivers conflict.</strong> Section 322.12 does not authorize a waiver for France, Germany, Taiwan, South Korea, or a U.S. territory. The 2023 handbook and the Palm Beach transfer page do. The handbook says it is not itself the law and that it stops at its August 2023 revision. Confirm a waiver with the office before you rely on it. A country that is on neither the statute's waiver nor the handbook's list is not described as exempt by either source{src("s12","hand","pbex")}.</div>
<p>If you have never been issued a driver license in any state or country, FLHSMV requires a Traffic Law and Substance Abuse Education (TLSAE) course before you apply. A license already issued in another country means that sentence does not apply{src("exam")}.</p>
<p>The Class E knowledge exam is 50 questions. A passing score is 40 correct, which is 80 percent. FLHSMV says that exam is available in English only{src("exam")}. After a failed first knowledge test, each later attempt is $10. After a failed first skills test, each later attempt is $20. When the tax collector gives the retest, the tax collector keeps that fee, less the general revenue service charge{src("s12","fees")}.</p>
<p>The Broward County Tax Collector says that, effective February 6, 2026, all driver license knowledge and driving exams in Florida are given in English only, and that translation devices, interpreters, and other language assistance are not allowed on the written test or the road test{src("btdl")}. FLHSMV's Broward locations page still says a knowledge exam requested with an interpreter is by appointment only and limited to one attempt per day{src("bro")}. The FLHSMV knowledge-exam page says the exam is available in English only and does not mention interpreters or the road test{src("exam")}.</p>
<p>Canadian citizens use the Canadian checklist: an original valid Canadian passport or, if that passport is not presented, a United States Citizenship and Immigration Services (USCIS) document showing legal presence, plus SSN proof and two Florida address documents. A Canadian citizen classified as a non-immigrant is not eligible for a commercial learner's permit or a CDL{src("can")}.</p>
<h2>Refugees and other lawfully present people</h2>
<p>Section 322.033 says the department may not issue a driver license or identification card to a person who is an unauthorized alien or an undocumented immigrant. Palm Beach states the same limit for its office{src("s033","pbdl")}. A class of out-of-state license issued only to people who could not prove lawful presence is invalid in Florida and does not authorize driving here. FLHSMV keeps the list on its Senate Bill 1718 page and says the list can change{src("s033","sb","visit")}.</p>
<p>Use the checklist for the status FLHSMV assigns. There is not one list for every non-citizen.</p>
<div class="card"><strong>Immigrant checklist.</strong> One original: a valid alien registration receipt card (green card, Form I-551); an I-551 stamp in a passport or on Form I-94; an immigration judge's order granting asylum, with the A-number and a valid passport; an I-797 granting asylum, with the A-number and a valid passport; or an I-797 or other USCIS form, with the A-number, stating that a refugee application is approved, plus a valid passport. Then one SSN proof and two Florida address proofs. A legal name change has to be on the USCIS documents{src("imm")}.</div>
<div class="card"><strong>Non-immigrant checklist.</strong> One original: a valid employment authorization card (Form I-688B or I-766), or unexpired proof of non-immigrant classification on Form I-94 with the supporting papers. An I-94 must come with a valid passport, a U.S. visa, and an entry stamp. F-1 and M-1 status also need Form I-20. J-1 and J-2 need Form DS-2019. The page says refugee, asylee, and parolee classifications need more documents, and it lists Form I-571 (refugee travel document) with a valid passport, Form I-512 (parole letter) with a valid passport, or an immigration judge's order granting asylum or cancellation of removal with a valid passport{src("nonimm")}.</div>
<p>Approved refugee status is on the immigrant checklist. Refugee, asylee, and parolee papers are also on the non-immigrant checklist. Bring the USCIS documents you have, and follow the checklist that matches the status on those documents{src("imm","nonimm")}.</p>
<p>How long the Florida credential lasts depends on which document was used, and the sources do not draw that line in the same place.</p>
<ul>
<li>Section 322.08 says a driver license or temporary permit issued from an employment authorization card, or from the proof of nonimmigrant classification listed in that section, is valid for a period that does not go past the expiration date of the document presented and does not go past one year{src("s08")}.</li>
<li>The questions page says a Class E license for a citizen or an immigrant is valid for eight years under age 80 and for six years over age 79. It says a non-immigrant credential is issued for the time USCIS approved, not longer than one year. The Class E renewal fee it states for that shorter license is still $48{src("wtbfaq")}.</li>
<li>The non-immigrant checklist says the immigration documents must be valid for more than 60 days from the date of issuance. A non-U.S. citizen applying for an original driver license receives a 60-day temporary paper permit with no photo, plus a receipt. After identity and legal status are verified, the card is mailed within 60 days and is issued for the period on the USCIS document, not longer than one year. If status or identity is not verified, a denial letter is mailed{src("nonimm")}.</li>
<li>Broward says immigration documents must generally be valid for more than 30 days, and that a Florida license or ID card generally expires with the authorized stay and may be limited to one year in some cases{src("btdl")}. Thirty days does not match FLHSMV's 60 days. Broward's "generally" is also wider than section 322.08, which attaches the one-year cap to an employment authorization card or to proof of nonimmigrant classification, not to a green card{src("nonimm","s08")}.</li>
</ul>
<p>Palm Beach's driver license page says a license or ID card lasts eight years at age 79 and under, and six years at age 80 and older. That sentence does not mention the shorter non-immigrant period{src("pbdl","wtbfaq","s08")}.</p>
<h2>Fees</h2>
<p>Section 322.21 sets an original Class E license at $48, an original or renewal commercial driver license at $75, each endorsement at $7, an original, renewal, or replacement identification card at $25, and a replacement driver license at $25. A renewal made within 12 months after expiration adds a $15 delinquent fee{src("s21")}. The FLHSMV fee schedule publishes those amounts and says an additional $6.25 service fee may apply when a tax collector office issues the credential. The new-resident page states the same $48, $75, $7, and $25 figures and says most tax collector offices charge the $6.25{src("fees","newres")}.</p>
<p>Section 322.135 requires that $6.25 on top of the other driver license fees for services the tax collector provides. It is charged no more than once per customer during one visit. It is not charged to a veteran who presents a DD Form 214, a veteran health identification card, a veteran identification card issued under the Veterans Identification Card Act of 2015, or another form the Department of Veterans' Affairs specifies{src("s135")}. The fee schedule says a veteran who provides, or has previously provided, evidence of veteran status is not charged the $6.25. "Previously provided" is wider than the statute's requirement to present the document{src("fees","s135")}.</p>
<p>Palm Beach publishes combined totals: Class E original or renewal, if not expired, $54.25; a CDL at $81.25 plus $7 per endorsement; a state identification card at $31.25; a replacement at $31.25; and $15 extra when the license or ID card is expired. $54.25, $81.25, and $31.25 are the state fee plus $6.25. Palm Beach also lists no fee to replace a stolen license or ID card when its required documentation is provided, and no fee for an ID card for a homeless person{src("pbex")}. The statute already removes the identification card fee for a homeless applicant who presents evidence that meets the statutory definition{src("s21")}. The FLHSMV fee schedule lists a $25 replacement and does not list a no-fee stolen replacement{src("fees")}.</p>
<p>On the FLHSMV Broward locations page, an asterisk marks a tax collector-sponsored office, and the page says a tax collector service fee is added there. The driver license offices without an asterisk are described as state-sponsored{src("bro")}.</p>
<div class="wrap"><table>
<tr><th>Item</th><th>Amount as published</th><th>Where it is published</th></tr>
<tr><td>Original Class E, including a learner license</td><td>$48. Add the $6.25 tax collector service fee where section 322.135 applies. Palm Beach lists $54.25</td><td>{a(S["s21"],"section 322.21")}, {a(S["fees"],"FLHSMV fees")}, {a(S["pbex"],"Palm Beach")}</td></tr>
<tr><td>Original or renewal commercial driver license</td><td>$75, plus $7 for each standard endorsement. Palm Beach lists $81.25 plus $7 per endorsement</td><td>{a(S["s21"],"section 322.21")}, {a(S["pbex"],"Palm Beach")}</td></tr>
<tr><td>Identification card</td><td>$25 for an original, renewal, or replacement. Palm Beach lists $31.25. No fee when the homeless exemption applies</td><td>{a(S["s21"],"section 322.21")}, {a(S["pbex"],"Palm Beach")}</td></tr>
<tr><td>Replacement driver license</td><td>$25 on the state schedule. Palm Beach lists $31.25, and no fee for a stolen card when its documents are provided</td><td>{a(S["fees"],"FLHSMV fees")}, {a(S["s21"],"section 322.21")}, {a(S["pbex"],"Palm Beach")}</td></tr>
<tr><td>Renewal within 12 months after expiration</td><td>Add $15</td><td>{a(S["s21"],"section 322.21")}</td></tr>
<tr><td>Knowledge retest, then skills retest</td><td>$10, then $20</td><td>{a(S["s12"],"section 322.12")}, {a(S["fees"],"FLHSMV fees")}</td></tr>
</table></div>
<p>The Miami-Dade driver license page and the Broward driver license page do not publish their own fee table. When that county's tax collector issues the credential, section 322.135 still requires the $6.25 service fee{src("mdcdl","btdl","s135")}.</p>
<h2>Broward, Miami-Dade, and Palm Beach offices</h2>
<p>Miami-Dade County's tax collector says it issues driver licenses and identification cards for county residents. It says the offices it has taken over take an appointment or a walk-in during operating hours, that it has taken over eight offices, and that it does not name them. An appointment booked online has priority{src("mdcdl")}. See {a("/counties/miami-dade/","Miami-Dade offices")} and {a("/walk-in-vs-appointment/","walk-in vs appointment")}.</p>
<p>Palm Beach County's tax collector issues REAL ID driver licenses and state ID cards as an agent for FLHSMV. A person moving there from another state or country must make a reservation for in-person service{src("pbdl","pbex")}. See {a("/counties/palm-beach/","Palm Beach offices")} and {a("/walk-in-vs-appointment/","walk-in vs appointment")}.</p>
<p>Broward is split. On the FLHSMV Broward page, Lauderdale Lakes is the tax collector-sponsored driver license office. Margate, Sunrise, Pembroke Pines, and Pompano Citi Centre are listed as state-sponsored driver license offices, and those rows say appointments{src("bro")}. The Broward County Tax Collector also publishes its own driver license document rules{src("btdl")}. See {a("/counties/broward/","Broward offices")} and {a("/walk-in-vs-appointment/","walk-in vs appointment")}.</p>
<p>FLHSMV's Broward page tells a new resident to get the Florida driver license first, then automobile insurance from a company licensed to do business in Florida, then the title, registration, and license plate{src("bro")}. The new-resident page says that Florida insurance is required in order to title and register a vehicle, vessel, or mobile home within 10 days of establishing residency{src("newres")}.</p>
<p class="src">Community reports: none. This page does not use forums, social media, or unofficial appointment sites.</p>'''
s.page('new-to-florida/index.html',"New to Florida: transfer an out-of-state driver license","Deadline, documents, exam rules, and fees for transferring an out-of-state or foreign license in Broward, Miami-Dade, or Palm Beach.",b)
b=f'''<h1>Fake DMV appointment websites: book only on official sites</h1>{fake("../")}
<h2>Official booking pages</h2><div class="wrap"><table><tr><th>County</th><th>Official booking</th><th>Notes</th></tr>
<tr><td>Miami-Dade</td><td>{a(S["mdcappt"],"app.mdctaxcollector.gov")}</td><td>Login required to book{src("mdcappt")}. Virtual walk-in: {a(S["mdcvw"],"app.mdctaxcollector.gov/virtual-walk-in")}</td></tr>
<tr><td>Broward (Lauderdale Lakes)</td><td>{a(S["btcappt"],"appointments.browardtax.org")}</td><td>Linked from the state Broward page. A residency limit and a name-match rule could not be reconfirmed on {D}{src("bro")}</td></tr>
<tr><td>Broward (state-run offices)</td><td>{a(S["nemo"],"nqapflhsmv.nemoqappointment.com")}</td><td>Linked from the FLHSMV Broward page{src("bro")}</td></tr>
<tr><td>Palm Beach</td><td>{a(S["pbres"],"pbctax.gov/reservations")}</td><td>Palm Beach residents only{src("pbres")}</td></tr></table></div>
<h2>How to protect yourself</h2><div class="card"><ul><li>Start from the agency home page ({a(S["loc"],"flhsmv.gov/locations")}, {a(S["mdc"],"mdctaxcollector.gov")}, {a(S["btc"],"browardtax.org")}, {a(S["pbtc"],"pbctax.gov")}) rather than a search ad.</li><li>The Miami-Dade booking page and the Palm Beach reservation page do not show a fee to reserve a slot{src("mdcappt","pbres")}. If a site asks you to pay just to reserve a slot, leave.</li><li>If a confirmation looks odd, verify it directly with the office, as the Miami-Dade Tax Collector advises{src("mdc")}.</li></ul></div>'''
s.page('fake-appointment-sites/index.html',"Fake DMV appointment sites: book only on official sites","Official warning about fake driver license appointment sites in Miami-Dade, and the only official booking pages for Broward, Miami-Dade and Palm Beach.",b)
faq=[("Can I walk in at a Miami-Dade driver license office?",f"The Tax Collector says the offices it has taken over take walk-ins during operating hours, and that online appointments have priority. It says it has taken over eight offices and does not name them. A May 2025 post names Downtown Miami, Miami Central, and Midway Crossings for a virtual walk-in queue by QR code{src('mdcdl','mdcvwblog')}."),
("Can I walk in at a Palm Beach driver license office?",f"No. The Palm Beach Tax Collector requires a reservation for in-person service, for county residents only{src('pbres')}."),
("Can I walk in at a Broward driver license office?",f"Official pages do not say. The Florida Department of Highway Safety and Motor Vehicles links Broward offices to appointment systems and says many offices require appointments{src('loc','bro')}."),
("I live in Broward. Can I book in Palm Beach?",f"No. Palm Beach reservations are for Palm Beach County residents. Non-residents are pointed to state driver license locations{src('pbres')}."),
("Are offices closed on upcoming holidays?",f"State offices are listed as closed on Veterans Day, Wednesday 11 Nov 2026, Thanksgiving Day, Thursday 26 Nov 2026, the Friday after Thanksgiving, 27 Nov 2026, and Christmas Day, Friday 25 Dec 2026. County tax collector offices may not follow that list{src('clos')}. The Broward County Tax Collector says its offices will be closed on 28 Oct 2026 for a Professional Development Day, and the same page also lists an early close that day at 11:30 a.m.{src('btc')}."),
("Is it legal to buy a DMV appointment from someone?",f"No official site sells appointments. The Miami-Dade Tax Collector warns about unofficial appointment sites issuing invalid confirmations{src('mdc')}."),
("Can I renew online?",f"Many renewals and replacements can be done at MyDMV Portal; you can renew up to 18 months before expiry{src('mdcdl')}."),
("Do Saturday hours exist?",f"Yes at most Miami-Dade offices, 8:00 a.m. to 1:00 p.m. at select locations{src('mdcdl','mia')}. Broward and Palm Beach driver license offices list weekdays only{src('bro','pbc')}."),
("What documents do I need for REAL ID?",f"One primary ID, one proof of SSN and two proofs of Florida address. See {a('/what-to-bring/','what to bring')}{src('usc')}.")]
def plain(h): return re.sub(r'\s+',' ',re.sub(r'<[^>]+>','',h)).strip()
def font(size,bold=False):
    from PIL import ImageFont
    names=["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf","/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"] if bold else ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf","/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"]
    for n in names:
        if os.path.exists(n): return ImageFont.truetype(n,size)
    raise SystemExit('No sans font found for the social image')
def write_assets(out):
    from PIL import Image,ImageDraw
    svg='''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="6" fill="#0A4550"/><circle cx="16" cy="11" r="4.2" fill="#F6D98A"/><path d="M3 21c3.2 2.2 6.4-2.2 9.6 0s6.4-2.2 9.6 0 6.4-2.2 9.6 0" fill="none" stroke="#F6D98A" stroke-width="1.7" stroke-linecap="round"/><path d="M3 26c3.2 2.2 6.4-2.2 9.6 0s6.4-2.2 9.6 0 6.4-2.2 9.6 0" fill="none" stroke="#F4EFE4" stroke-width="1.7" stroke-linecap="round"/></svg>'''
    open(os.path.join(out,'favicon.svg'),'w',encoding='utf-8').write(svg)
    og=Image.new('RGB',(1200,630),'#0A4550'); d=ImageDraw.Draw(og)
    px=og.load()
    def mix(a,b,t):
        def ch(h,i): return int(h[i:i+2],16)
        return tuple(round(ch(a,i)*(1-t)+ch(b,i)*t) for i in (0,2,4))
    for x in range(1200):
        t=x/1199
        rgb=mix('0A4550','0E3A58',t/0.52) if t<0.52 else mix('0E3A58','3A3040',(t-0.52)/0.48)
        for y in range(630): px[x,y]=rgb
    d.rectangle((0,0,16,630),fill='#F6D98A')
    fb,fs,fm=font(72,True),font(32),font(22)
    d.text((72,150),'South Florida',font=fb,fill='#ffffff')
    d.text((72,240),'DMV Walk-in Guide',font=fb,fill='#ffffff')
    d.rectangle((72,360,420,366),fill='#F6D98A')
    d.text((72,400),'Broward, Miami-Dade and Palm Beach',font=fs,fill='#F4EFE4')
    d.text((72,470),'Unofficial independent guide',font=fm,fill='#F6D98A')
    for text,fnt in (('DMV Walk-in Guide',fb),('Broward, Miami-Dade and Palm Beach',fs)):
        box=d.textbbox((0,0),text,font=fnt)
        if box[2]-box[0]>1080: raise SystemExit('og text too wide: '+text)
    og.save(os.path.join(out,'og.png'),'PNG')
    ic=Image.new('RGB',(180,180),'#0A4550'); c=ImageDraw.Draw(ic)
    c.ellipse((66,28,114,76),fill='#F6D98A')
    c.arc((22,86,158,150),200,340,fill='#F6D98A',width=10)
    c.arc((22,112,158,176),200,340,fill='#F4EFE4',width=10)
    ic.save(os.path.join(out,'apple-touch-icon.png'),'PNG')
s.page('faq/index.html',"South Florida DMV FAQ: walk-ins, appointments and REAL ID","Sourced answers about walk-ins, appointments, residency rules and REAL ID documents at South Florida driver license offices.",'<h1>South Florida DMV FAQ</h1>'+''.join(f'<div class="card"><strong>{q}</strong><p>{x}</p></div>' for q,x in faq),faq=[(q,plain(x)) for q,x in faq])
s.page('disclaimer/index.html',"Disclaimer for the South Florida DMV walk-in guide","Legal limits of this unofficial South Florida DMV walk-in guide: accuracy, no warranty, liability, external links, affiliation and official sources.",f'''<h1>Disclaimer</h1>
<p>{esc(DISCLAIMER)}</p>
<h2>Accuracy</h2>
<p>Office names, addresses, hours, walk-in rules and booking links come from the official pages linked in each section, as of the check date at the top of the page. Official pages can change without notice. This guide can be incomplete, out of date or wrong.</p>
<h2>No warranty</h2>
<p>This guide is provided as is and as available. There is no warranty of any kind, express or implied, including any warranty of accuracy, completeness, timeliness or fitness for a particular purpose.</p>
<h2>Limitation of liability</h2>
<p>To the fullest extent allowed by law, we accept no liability for any loss, cost or inconvenience that results from using this site, or from being unable to use it. That includes a wasted trip, a missed reservation, a fee paid to anyone, a rejected document, or a decision you make from these pages.</p>
<h2>External links are not endorsed</h2>
<p>Links to agency sites, booking systems and other websites are provided for convenience. We do not run those sites and we do not endorse them. A link is not a promise that the other site is accurate, current or safe. Related guides in the footer are separate sites.</p>
<h2>Not affiliated</h2>
<p>This independent site is not affiliated with the Florida DHSMV, any county tax collector or any government agency. It is not an official booking channel. Agency names are used only so you can find the public source.</p>
<h2>Check official sources</h2>
<p>Always confirm hours, documents, residency rules, fees and booking steps with the official office before you act. Use only the official booking pages named in this guide.</p>
<h2>Contact and corrections</h2>
<p>This site has no contact form, phone line or appointment desk. We cannot book, change or cancel a visit for you. If something here looks wrong, treat the official page linked from that section as the source. Corrections to this guide are made by checking those official sources again.</p>''',crumb='Disclaimer')
find_title="Find a page in the South Florida DMV walk-in guide"
find_desc="Search or browse every page in this independent South Florida driver license walk-in guide, including county offices, documents, and booking warnings."
find_body='<h1>All pages</h1><p>Type in the search box at the top of this page. The list below stays complete if search is not available.</p><p id="index-status" class="index-status" aria-live="polite">Showing every page.</p><div id="page-index">'+''.join(
 f'<section><h2>{esc(g)}</h2><ul class="index-list">'+''.join(
  f'<li data-keywords="{esc(ALIAS[p])}"><a class="jump" href="{href(p)}"><span class="lt">{esc(t)}</span><span class="ls">{esc(BLURB[p])}</span></a></li>' for p,t in items)+'</ul></section>' for g,items in G)+'</div>'
s.page('find/index.html',find_title,find_desc,find_body)
hubs='<li><a href="/">Home</a></li>'+''.join(f'<li><a href="{href(p)}">{esc(t)}</a></li>' for g,items in G for p,t in items)
s.page('404.html',"Page not found on the South Florida DMV walk-in guide","This address is not a page in the South Florida DMV walk-in guide. Choose the home page, a county, walk-in rules, documents, fake sites or the FAQ.",f'<h1>Page not found</h1><p>That address is not a page on this guide. Try one of these:</p><ul>{hubs}</ul>',error=True,sitemap=False,crumb='Page not found')
write_assets(s.out)
def copy_map_assets(out):
    vend=os.path.join(out,'vendor','leaflet')
    shutil.copytree(os.path.join(HERE,'vendor','leaflet'),vend)
    shutil.copy(os.path.join(HERE,'map.js'),os.path.join(out,'map.js'))
    js=open(os.path.join(out,'map.js'),encoding='utf-8').read()
    if 'https://www.openstreetmap.org/copyright' not in js: raise SystemExit('Map script is missing the OpenStreetMap attribution link')
    if 'tile.openstreetmap.org' not in js: raise SystemExit('Map script is missing OpenStreetMap tiles')
    if 'scrollWheelZoom: false' not in js: raise SystemExit('Map script must keep scroll zoom off until a click')
    for rel in ('leaflet.js','leaflet.css','images/marker-icon.png','images/marker-icon-2x.png','images/marker-shadow.png','LICENSE'):
        if not os.path.isfile(os.path.join(vend,rel)): raise SystemExit('Missing Leaflet file '+rel)
def check_maps(out):
    pages={'counties/broward/index.html':CC['broward'],'counties/miami-dade/index.html':CC['miami-dade'],'counties/palm-beach/index.html':CC['palm-beach'],'walk-in-vs-appointment/index.html':recs}
    for path,rows in pages.items():
        html=open(os.path.join(out,path),encoding='utf-8').read()
        n=html.count('>Get directions<')
        if n!=len(rows): raise SystemExit(f'Directions count {n} != {len(rows)} on {path}')
        if 'class="office-map"' not in html or 'src="/map.js"' not in html: raise SystemExit('Missing map on '+path)
        if 'scroll wheel' not in html: raise SystemExit('Missing scroll wheel note on '+path)
        if 'https://www.google.com/maps/dir/?api=1&amp;destination=' not in html: raise SystemExit('Missing directions URL on '+path)
        pins=html.count('&quot;lat&quot;:')
        expect=sum(1 for r in rows if pin_row(r))
        if pins!=expect: raise SystemExit(f'Pin count {pins} != {expect} on {path}')
    for path in [p for p,_m in s.pages]+['404.html']:
        if path in pages: continue
        html=open(os.path.join(out,path),encoding='utf-8').read()
        if 'class="office-map"' in html or '>Get directions<' in html: raise SystemExit('Unexpected map markup on '+path)
copy_map_assets(s.out)
check_maps(s.out)
pinned=sum(1 for r in recs if pin_row(r))
s.finish(); print(len(s.pages),'pages',len(recs),'offices',pinned,'pins',len(recs)-pinned,'unpinned',{k:len(v) for k,v in CC.items()})
