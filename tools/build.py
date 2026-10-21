#!/usr/bin/env python3
"""Build the South Florida driver license walk-in vs appointment guide into site/. Run: python3 tools/build.py
Office list comes from tools/flhsmv_raw.json, parsed from the FLHSMV county location pages on the check date."""
import json,os,sys,re
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE); sys.path.insert(0,HERE)
from sitelib import Site,CSS,D,esc,a
BASE="https://south-florida-dmv-walkin-guide.vercel.app"
S=dict(loc="https://www.flhsmv.gov/locations/",bro="https://www.flhsmv.gov/locations/broward/",mia="https://www.flhsmv.gov/locations/miami-dade/",pbc="https://www.flhsmv.gov/locations/palm-beach/",
 nemo="https://nqapflhsmv.nemoqappointment.com",btc="https://browardtax.org/",btcappt="https://appointments.browardtax.org/",btcloc="https://browardtax.org/locations/",btcnews="https://browardtax.org/news/flow-driver-license-aug-2025/",
 mdc="https://www.mdctaxcollector.gov/",mdcdl="https://www.mdctaxcollector.gov/driver-license-and-id-card-services",mdcloc="https://www.mdctaxcollector.gov/locations",mdcappt="https://app.mdctaxcollector.gov/",
 mdcvw="https://app.mdctaxcollector.gov/virtual-walk-in",mdcvwblog="https://www.mdctaxcollector.gov/blog/miami-dade-county-office-of-the-tax-collector-launches-innovative-virtual-walk-in-system-for-driver-license-and-id-services",
 mdcfake="https://www.mdctaxcollector.gov/blog/tax-collector-dariel-fernandez-sounds-the-alarm-on-fake-appointments-targeting-miami-dade-residents",
 pbtc="https://www.pbctax.gov/driver-license/",pbres="https://www.pbctax.gov/reservations/",wtb="https://www.flhsmv.gov/driver-licenses-id-cards/what-to-bring/",
 usc="https://www.flhsmv.gov/driver-licenses-id-cards/what-to-bring/u-s-citizen/",imm="https://www.flhsmv.gov/driver-licenses-id-cards/what-to-bring/immigrant/",nonimm="https://www.flhsmv.gov/driver-licenses-id-cards/what-to-bring/non-immigrant/",can="https://www.flhsmv.gov/driver-licenses-id-cards/what-to-bring/canadian/",
 mydmv="https://mydmvportal.flhsmv.gov",passport="https://us-passport-walkin-finder.vercel.app")
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
        if tc: op='Broward County Tax Collector (tax collector-sponsored)'; pol=f'Appointment system run by the Broward County Tax Collector. Appointments are for Broward County residents only; the name on the appointment must match the ID shown at check-in{src("btcappt")}. Walk-in service is not stated on the official pages.'; st='appt'
        else: op='FLHSMV (state-run)'; pol=f'FLHSMV links this office to its appointment system and says many offices require appointments{src("loc")}. Walk-in service is not stated on the official page.'; st='unclear'
    elif c=='Miami-Dade':
        op='Miami-Dade County Tax Collector'; pol=f'Tax Collector says offices it manages take appointments or walk-in service during operating hours{src("mdcdl")}. Appointments booked online have priority over walk-ins{src("mdcvwblog")}.'; st='walk'
        if nm in VW: pol+=f' This office was named in the Tax Collector virtual walk-in launch (scan the QR code at the office, get a virtual time, return 15 minutes before){src("mdcvwblog","mdcvw")}.'
    else:
        op='Palm Beach County Tax Collector'; pol=f'"By Reservation Only", Palm Beach County residents only{src("pbc")}. The Tax Collector says a reservation is required for in-person service{src("pbres")}.'; st='appt'
    notes=[x for x in r['comments'] if x and 'MyDMV' not in x and 'mail correspondence' not in x and not x.startswith('PO Box') and 'Residents Only' not in x and 'By Reservation' not in x]
    recs.append(dict(county=c,name=nm,address=r['address'],phone=r['phone'],hours=r['hours'],group=r['group'],op=op,policy=pol,status=st,book=book,notes=notes,tc=tc))
json.dump(recs,open(os.path.join(HERE,'offices_parsed.json'),'w'),indent=1)
NAV=[('index.html','Home')]+[(f'counties/{k}/index.html',v[0]) for k,v in COUNTIES.items()]+[('walk-in-vs-appointment/index.html','Walk-in vs appointment'),('what-to-bring/index.html','What to bring'),('fake-appointment-sites/index.html','Fake appointment sites'),('faq/index.html','FAQ')]
FOOT=f'Unofficial, independent guide. Not affiliated with FLHSMV or any county tax collector. We do not sell appointments, and nobody legitimately can: book only on {a(S["loc"],"flhsmv.gov")}, {a(S["mdc"],"mdctaxcollector.gov")}, {a(S["btc"],"browardtax.org")} or {a(S["pbtc"],"pbctax.gov")}. Office data from the FLHSMV county location pages; policies from each tax collector site.'
s=Site(ROOT,BASE,"South Florida DMV Walk-in Guide",NAV,FOOT,CSS)
FAKE=f'<div class="card warn"><strong>Warning: fake appointment websites.</strong> The Miami-Dade Tax Collector warns residents about unofficial appointment websites issuing invalid confirmations, and says to schedule only through mdctaxcollector.gov and verify any questionable appointment directly with the office{src("mdc","mdcfake")}. Book only on the official sites: {a(S["mdcappt"],"app.mdctaxcollector.gov")} (Miami-Dade), {a(S["btcappt"],"appointments.browardtax.org")} or {a(S["nemo"],"the FLHSMV appointment system")} (Broward), {a(S["pbres"],"pbctax.gov/reservations")} (Palm Beach). Never pay a third party for a slot. {a("{R}fake-appointment-sites/index.html","How to spot a fake")}.</div>'
def fake(r): return FAKE.replace('{R}',r)
CONF=f'''<div class="card conf"><strong>Conflicts and gaps in official sources ({D})</strong><ul>
<li>FLHSMV says standard business hours are 9 a.m. to 12 p.m. and 1 p.m. to 5 p.m., closed for lunch{src("loc")}, but its own Broward office rows list 8:00 a.m. to 5:00 p.m. with no lunch break{src("bro")}. Hours below are the office rows.</li>
<li>Miami-Dade Tax Collector text says it has "assumed control of eight offices", yet its locations page lists 13 offices and FLHSMV links all 13 Miami-Dade driver license offices to the Tax Collector booking system{src("mdcdl","mdcloc","mia")}.</li>
<li>Broward: a Tax Collector news post says it prepares to take over driver license services in summer 2026, while its home page on {D} still says new driver license services are "coming soon"{src("btcnews","btc")}. The Tax Collector locations page lists Fort Lauderdale (115 S. Andrews Ave), Plantation and Lauderdale Lakes{src("btcloc")}; FLHSMV lists Plantation as motor vehicle services only and does not list 115 S. Andrews Ave{src("bro")}.</li>
<li>Virtual walk-in: the Miami-Dade launch post (May 2025) names three offices; we found no current official list of all participating offices{src("mdcvwblog")}.</li></ul></div>'''
TAGS={'walk':'<span class="tag ok">walk-in accepted (official)</span>','appt':'<span class="tag no">appointment or reservation required</span>','unclear':'<span class="tag mix">appointments; walk-in not stated</span>'}
def table(rows):
    t='<input id="q" placeholder="Filter by city or name" oninput="var v=this.value.toLowerCase();document.querySelectorAll(\'table tr\').forEach(function(r){if(r.querySelector(\'td\'))r.style.display=r.textContent.toLowerCase().indexOf(v)>-1?\'\':\'none\'})"><div class="wrap"><table><tr><th>Office</th><th>Address and phone</th><th>Hours (FLHSMV listing)</th><th>Walk-in policy as officially stated</th><th>Official booking</th></tr>'
    for r in rows:
        n=('<br><span class="src">'+esc('; '.join(r['notes']))+'</span>') if r['notes'] else ''
        t+=f'<tr><td><strong>{esc(r["name"])}</strong><br><span class="src">{esc(r["group"])} services. {esc(r["op"])}</span>{n}</td><td>{esc(r["address"])}<br>{esc(r["phone"])}</td><td>{"<br>".join(esc(h) for h in r["hours"])}</td><td>{TAGS[r["status"]]}<br>{r["policy"]}</td><td>{a(r["book"],"Book (official)") if r["book"] else "Not linked"}</td></tr>'
    return t+'</table></div>'
CC={k:[r for r in recs if r['county']==v[0]] for k,v in COUNTIES.items()}
b=f'''<h1>South Florida DMV: walk-in or appointment?</h1><p>Every driver license and ID card office in Broward, Miami-Dade and Palm Beach counties listed by FLHSMV on {D}{src("loc")}, with hours and the walk-in rule as each operator states it. {len(recs)} offices in total.</p>
{fake('')}
<div class="wrap"><table><tr><th>County</th><th>Offices</th><th>Who runs them</th><th>Walk-ins, as officially stated</th></tr>
<tr><td>{a("counties/miami-dade/index.html","Miami-Dade")}</td><td>{len(CC["miami-dade"])}</td><td>County Tax Collector</td><td>Yes at Tax Collector offices during operating hours, plus a virtual walk-in queue; online appointments get priority{src("mdcdl","mdcvwblog")}</td></tr>
<tr><td>{a("counties/broward/index.html","Broward")}</td><td>{len(CC["broward"])}</td><td>FLHSMV (4), Tax Collector (Lauderdale Lakes)</td><td>Not stated. FLHSMV says many offices require appointments{src("loc")}</td></tr>
<tr><td>{a("counties/palm-beach/index.html","Palm Beach")}</td><td>{len(CC["palm-beach"])}</td><td>County Tax Collector</td><td>No. Reservation required, county residents only{src("pbres","pbc")}</td></tr></table></div>
<h2>Skip the office if you can</h2><p>Many renewals and replacements can be done online at {a(S["mydmv"],"MyDMV Portal")}{src("mia","mdcdl")}. You must visit in person with documents for a first license or ID, if your card has no star, or after a legal name change{src("wtb")}. See {a("what-to-bring/index.html","what to bring")}.</p>
{CONF}
<p>Need a U.S. passport instead? See the {a(S["passport"],"South Florida passport walk-in finder")}.</p>
<p class="src">About community reports: we do not publish Reddit or social media wait-time reports, because they could not be verified against official sources.</p>'''
s.page('index.html',"South Florida DMV walk-in vs appointment: Broward, Miami-Dade, Palm Beach","Which South Florida driver license and ID offices take walk-ins and which need appointments, with hours, addresses and official booking links.",b)
for k,(short,full,sk) in COUNTIES.items():
    extra={'miami-dade':f'<div class="card note"><strong>Miami-Dade virtual walk-in.</strong> Arrive at the office, scan the posted QR code, register and receive a virtual appointment time; return 15 minutes before it to check in. Pre-booked online appointments always have priority{src("mdcvwblog")}. The virtual walk-in page asks you to verify your location before continuing{src("mdcvw")}. Hours: most Tax Collector offices Monday to Friday 8:00 a.m. to 5:00 p.m. and Saturday at select locations 8:00 a.m. to 1:00 p.m., except North Dade Justice{src("mdcdl")}. Driving tests and CDL only at selected offices{src("mdcdl")}.</div>',
     'broward':f'<div class="card note"><strong>Broward booking.</strong> State-run offices link to the {a(S["nemo"],"FLHSMV appointment system")}; Lauderdale Lakes links to {a(S["btcappt"],"appointments.browardtax.org")}, which is for Broward residents only and requires the name on the appointment to match your ID{src("bro","btcappt")}. State-run offices accept cash, check, Visa, MasterCard, Discover and American Express; knowledge exams with an interpreter are by appointment only{src("bro")}. The Tax Collector also runs DASH mobile units for select transactions such as standard renewals and replacements{src("btc")}.</div>',
     'palm-beach':f'<div class="card note"><strong>Palm Beach reservations.</strong> All Palm Beach offices are tax collector-sponsored; a tax collector service fee is added{src("pbc")}. A reservation is required for in-person service and is for Palm Beach County residents only; non-residents are pointed to FLHSMV locations{src("pbres")}. Customers who are not REAL ID compliant must schedule a reservation, and the office does not issue licenses or IDs to undocumented immigrants{src("pbtc")}.</div>'}[k]
    b=f'<h1>Driver license and ID offices in {full}: walk-in or appointment</h1><p>{len(CC[k])} offices offering driver license services, from the FLHSMV {full} page{src(sk)}. Motor vehicle only offices and license plate agents are not listed.</p>{fake("../../")}{extra}'+table(CC[k])+CONF
    s.page(f'counties/{k}/index.html',f"{full} DMV offices: walk-in or appointment, hours, booking",f"Every driver license and ID office in {full} with address, hours, official walk-in policy and booking link.",b)
b=f'<h1>Walk-in vs appointment at South Florida driver license offices</h1>{fake("../")}<h2>Offices where walk-ins are officially accepted</h2>'+table([r for r in recs if r['status']=='walk'])+'<h2>Appointment or reservation required</h2>'+table([r for r in recs if r['status']=='appt'])+'<h2>Appointment system linked, walk-in not stated</h2>'+table([r for r in recs if r['status']=='unclear'])+CONF
s.page('walk-in-vs-appointment/index.html',"Which South Florida DMV offices take walk-ins","South Florida driver license offices grouped by official walk-in policy: walk-in accepted, reservation required, or not stated.",b)
b=f'''<h1>What to bring for a Florida REAL ID driver license or ID card</h1><p>From the FLHSMV U.S. citizen checklist{src("usc")}. Non-citizens: see the {a(S["imm"],"immigrant")}, {a(S["nonimm"],"non-immigrant")} and {a(S["can"],"Canadian")} lists.</p>
<div class="card"><p>You must visit an office with documents for your first license or ID, if your current card has no star, or if you legally changed your name since your last card{src("wtb")}. Once you have provided them, you only need them again if your information changes{src("wtb")}.</p></div>
<h2>1. Primary identification (one original)</h2><div class="card"><ul><li>U.S. birth certificate (Puerto Rico certificates must be issued after July 1, 2010). Only county health department or CDC Bureau of Vital Statistics certificates; hospital certificates are not accepted.</li><li>Valid U.S. passport or passport card</li><li>Consular Report of Birth Abroad</li><li>Certificate of Naturalization (N-550 or N-570)</li><li>Certificate of Citizenship (N-560 or N-561)</li></ul>Bring marriage certificates, court orders or divorce decrees to link names, unless your valid U.S. passport shows your current name{src("usc")}.</div>
<h2>2. Proof of Social Security number (one original)</h2><div class="card"><ul><li>Social Security card in your current name</li><li>W-2 (not handwritten)</li><li>Any 1099 (not handwritten)</li></ul>The name on your SSN must match the license; allow 24 to 48 hours after changing your name with Social Security{src("usc")}.</div>
<h2>3. Two proofs of Florida residential address</h2><div class="card"><p>Your current license does not count. Printouts are accepted. Out-of-state addresses are not accepted for a Class E license or ID{src("usc")}.</p><ul><li>Deed, mortgage, mortgage statement or lease</li><li>Florida voter registration card</li><li>Florida vehicle registration or title</li><li>Dated within the last 60 days: utility bill, auto payment booklet, selective service card, medical card or bill, home or auto insurance policy or bill, W-2, 1099 or pay stub, bank or credit card statement, government mail, or a shelter or transitional housing letter</li></ul>
<p>If none are in your name, the person you live with can complete a Certification of Address (HSMV 71120) with two of their own proofs, signed in front of an examiner or a notary{src("usc","mdcdl")}. CDL applicants cannot use it{src("usc")}.</p></div>
<h2>Name changes</h2><div class="card">Bring the original or certified marriage certificate, divorce decree or court order; photocopies and church-issued certificates are not accepted{src("usc")}.</div>
<p>Since May 7, 2025, TSA accepts only starred (REAL ID) licenses and IDs at airports; a U.S. passport can be used instead{src("wtb")}.</p>'''
s.page('what-to-bring/index.html',"Florida REAL ID documents: what to bring to the DMV","FLHSMV REAL ID document list for U.S. citizens: identity, Social Security and two proofs of Florida address, plus name change rules.",b)
b=f'''<h1>Fake DMV appointment websites: book only on official sites</h1>{fake("../")}
<h2>Official booking pages</h2><div class="wrap"><table><tr><th>County</th><th>Official booking</th><th>Notes</th></tr>
<tr><td>Miami-Dade</td><td>{a(S["mdcappt"],"app.mdctaxcollector.gov")}</td><td>Login required to book{src("mdcappt")}. Virtual walk-in: {a(S["mdcvw"],"app.mdctaxcollector.gov/virtual-walk-in")}</td></tr>
<tr><td>Broward (Lauderdale Lakes)</td><td>{a(S["btcappt"],"appointments.browardtax.org")}</td><td>Broward residents only; name must match ID{src("btcappt")}</td></tr>
<tr><td>Broward (state-run offices)</td><td>{a(S["nemo"],"nqapflhsmv.nemoqappointment.com")}</td><td>Linked from the FLHSMV Broward page{src("bro")}</td></tr>
<tr><td>Palm Beach</td><td>{a(S["pbres"],"pbctax.gov/reservations")}</td><td>Palm Beach residents only{src("pbres")}</td></tr></table></div>
<h2>How to protect yourself</h2><div class="card"><ul><li>Start from the agency home page ({a(S["loc"],"flhsmv.gov/locations")}, {a(S["mdc"],"mdctaxcollector.gov")}, {a(S["btc"],"browardtax.org")}, {a(S["pbtc"],"pbctax.gov")}) rather than a search ad.</li><li>The official systems above do not charge a booking fee on the pages we checked. If a site asks you to pay just to reserve a slot, leave.</li><li>If a confirmation looks odd, verify it directly with the office, as the Miami-Dade Tax Collector advises{src("mdc")}.</li><li>Use the exact name on your ID: Broward will not honor an appointment whose name does not match{src("btcappt")}.</li></ul></div>'''
s.page('fake-appointment-sites/index.html',"Fake DMV appointment sites in South Florida: book only on official sites","Official warning about fake driver license appointment sites in Miami-Dade, and the only official booking pages for Broward, Miami-Dade and Palm Beach.",b)
faq=[("Can I walk in at a Miami-Dade DMV?",f"Yes at Tax Collector offices during operating hours, but online appointments have priority. Some offices use a virtual walk-in queue by QR code{src('mdcdl','mdcvwblog')}."),
("Can I walk in at a Palm Beach DMV?",f"No. The Palm Beach Tax Collector requires a reservation for in-person service, for county residents only{src('pbres')}."),
("Can I walk in at a Broward DMV?",f"Official pages do not say. FLHSMV links Broward offices to appointment systems and says many offices require appointments{src('loc','bro')}."),
("I live in Broward. Can I book in Palm Beach?",f"No. Palm Beach reservations are for Palm Beach County residents; Broward Tax Collector appointments are for Broward residents{src('pbres','btcappt')}."),
("Is it legal to buy a DMV appointment from someone?",f"No official site sells appointments. The Miami-Dade Tax Collector warns about unofficial appointment sites issuing invalid confirmations{src('mdc')}."),
("Can I renew online?",f"Many renewals and replacements can be done at MyDMV Portal; you can renew up to 18 months before expiry{src('mdcdl')}."),
("Do Saturday hours exist?",f"Yes at most Miami-Dade offices, 8:00 a.m. to 1:00 p.m. at select locations{src('mdcdl','mia')}. Broward and Palm Beach driver license offices list weekdays only{src('bro','pbc')}."),
("What documents do I need for REAL ID?",f"One primary ID, one proof of SSN and two proofs of Florida address. See {a('../what-to-bring/index.html','what to bring')}{src('usc')}.")]
s.page('faq/index.html',"South Florida DMV FAQ: walk-ins, appointments and REAL ID","Sourced answers about walk-ins, appointments, residency rules and REAL ID documents at South Florida driver license offices.",'<h1>South Florida DMV FAQ</h1>'+''.join(f'<div class="card"><strong>{q}</strong><p>{x}</p></div>' for q,x in faq))
s.finish(); print(len(s.pages),'pages',len(recs),'offices',{k:len(v) for k,v in CC.items()})
