"""Page shell for the South Florida driver license walk-in guide.

Layout, topic menu, search, and checks follow the sister guide's tools, with this
site's own coastal colours, copy, and facts. The generator still owns every fact.
"""
import os, html as H, shutil, re, json
D = "26 Oct 2026"
ISO = "2026-10-26"
HEADER_LINE = "Independent guide. Not a government website."
# Coastal header. Every stop, and the colours between them, stays dark enough
# for white and sand text (WCAG AA, 4.5:1). Checked again in finish().
STOPS = ("#0A4550", "#0E3A58", "#3A3040")
SAND = "#F4EFE4"
GOLD = "#F6D98A"
INK = "#1A1814"
WHITE = "#FFFFFF"

def esc(s):
    return H.escape(s, quote=True)

def a(url, text="source"):
    return f'<a href="{esc(url)}" rel="noopener">{text}</a>'

def slug(t):
    t = H.unescape(re.sub(r"<[^>]+>", "", t))
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")

def href(path):
    if path in ("index.html", "/"):
        return "/"
    if path.endswith("/index.html"):
        return "/" + path[: -len("index.html")]
    return "/" + path

def canon_url(base, path):
    if path == "404.html":
        return base.rstrip("/") + "/404.html"
    return base.rstrip("/") + href(path)

def _lin(c):
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def _lum(h):
    h = h.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)

def contrast(fg, bg):
    hi, lo = max(_lum(fg), _lum(bg)), min(_lum(fg), _lum(bg))
    return (hi + 0.05) / (lo + 0.05)

def _mix(a, b, t):
    def ch(h, i):
        return int(h[i : i + 2], 16)
    a, b = a.lstrip("#"), b.lstrip("#")
    out = ""
    for i in (0, 2, 4):
        out += f"{round(ch(a, i) * (1 - t) + ch(b, i) * t):02x}"
    return "#" + out

def header_samples():
    cols = []
    for i in range(len(STOPS) - 1):
        for k in range(0, 9):
            cols.append(_mix(STOPS[i], STOPS[i + 1], k / 8))
    cols.append(STOPS[-1])
    return cols

def check_contrast():
    """Fail the build if header text drops below WCAG AA at any gradient sample."""
    rows = []
    worst = 99
    worst_at = ""
    for bg in header_samples():
        for fg, name in ((WHITE, "white"), (SAND, "sand")):
            ratio = contrast(fg, bg)
            rows.append((ratio, name, bg))
            if ratio < worst:
                worst, worst_at = ratio, f"{name} on {bg}"
    if worst < 4.5:
        raise SystemExit(f"Header contrast {worst:.2f} at {worst_at} is below 4.5:1")
    pairs = [
        (INK, GOLD, "button text on sand"),
        (INK, "#E2BF62", "button text on sand hover"),
        (WHITE, "#102830", "menu text"),
        (GOLD, STOPS[0], "sand mark on header start"),
        (GOLD, STOPS[-1], "sand mark on header end"),
        ("#0A3D66", "#F4F1EA", "link on paper"),
        ("#0A3D66", WHITE, "link on white"),
        ("#3D2A6B", WHITE, "visited link on white"),
        ("#3D2A6B", "#F4F1EA", "visited link on paper"),
        ("#3E3A34", WHITE, "muted text"),
        ("#3E3A34", "#F4F1EA", "checked line on paper"),
        ("#143024", "#E5F2EA", "checked badge"),
        (INK, "#D8F0DE", "walk-in tag"),
        (INK, "#F8D7D7", "appointment tag"),
        (INK, "#FDEBC8", "mixed tag"),
        (INK, "#EEF4F1", "summary box"),
        (INK, "#FDEEEE", "warning card"),
        (INK, "#FFF8EC", "note card"),
        (INK, "#F6F1FA", "conflict card"),
        ("#0A3D66", "#FDEEEE", "link on warning"),
        ("#0A3D66", "#FFF8EC", "link on note"),
        ("#0A3D66", "#F6F1FA", "link on conflict"),
        ("#0A3D66", "#EEF4F1", "link on summary"),
    ]
    for fg, bg, name in pairs:
        ratio = contrast(fg, bg)
        rows.append((ratio, name, bg))
        if ratio < 4.5:
            raise SystemExit(f"Contrast {ratio:.2f} for {name} ({fg} on {bg}) is below 4.5:1")
    return worst, worst_at, rows

MARK = (
    '<span class="mark" aria-hidden="true"><svg viewBox="0 0 48 32" focusable="false">'
    '<rect width="48" height="32" rx="8" fill="#F6D98A"/>'
    '<circle cx="24" cy="11" r="5" fill="#0A4550"/>'
    '<path d="M4 21.5c4 2.6 8-2.6 12 0s8-2.6 12 0 8-2.6 12 0" fill="none" stroke="#0A4550" stroke-width="2" stroke-linecap="round"/>'
    '<path d="M4 26.5c4 2.6 8-2.6 12 0s8-2.6 12 0 8-2.6 12 0" fill="none" stroke="#0E3A58" stroke-width="2" stroke-linecap="round"/>'
    "</svg></span>"
)

SEARCH_JS = r"""(function(){
  var el=document.getElementById("search-data");
  var input=document.getElementById("q");
  var box=document.getElementById("search-results");
  if(!el||!input||!box) return;
  var pages=[];
  try { pages=JSON.parse(el.textContent); } catch(e){ return; }
  function esc(s){
    return String(s).replace(/[&<>"']/g, function(c){
      return {"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c];
    });
  }
  function activeWords(q){
    var t=String(q||"").trim().toLowerCase();
    if(t.length<2) return [];
    return t.split(/\s+/).filter(function(w){ return w; });
  }
  function match(blob, ws){
    if(!ws.length) return true;
    blob=String(blob).toLowerCase();
    for(var i=0;i<ws.length;i++) if(blob.indexOf(ws[i])<0) return false;
    return true;
  }
  function filterIndex(q){
    var root=document.getElementById("page-index");
    if(!root) return;
    var ws=activeWords(q);
    var items=root.querySelectorAll("li");
    var shown=0;
    for(var i=0;i<items.length;i++){
      var li=items[i];
      var blob=li.textContent+" "+(li.getAttribute("data-keywords")||"");
      var ok=match(blob, ws);
      li.hidden=!ok;
      if(ok) shown++;
    }
    var sections=root.querySelectorAll("section");
    for(var s=0;s<sections.length;s++){
      var sec=sections[s];
      var lis=sec.querySelectorAll("li");
      var any=false;
      for(var k=0;k<lis.length;k++) if(!lis[k].hidden) any=true;
      sec.hidden=!any;
    }
    var status=document.getElementById("index-status");
    if(status){
      if(!ws.length) status.textContent="Showing every page.";
      else if(!shown) status.textContent="No page matches. Try a different word, or clear the search.";
      else status.textContent="Showing "+shown+" of "+items.length+" pages.";
    }
  }
  function show(q){
    var ws=activeWords(q);
    if(!ws.length){
      box.hidden=true;
      box.innerHTML="";
    } else {
      var hits=[];
      for(var i=0;i<pages.length;i++){
        var p=pages[i];
        var blob=p.t+" "+p.s+" "+p.g+" "+(p.k||"");
        if(match(blob, ws)) hits.push(p);
        if(hits.length===8) break;
      }
      if(!hits.length){
        box.innerHTML="<p class=\"search-empty\">No matching page. Open the <a href=\"/find/\">full page list</a>.</p>";
      } else {
        var html="<ul>";
        for(var j=0;j<hits.length;j++){
          var hit=hits[j];
          html+="<li><a href=\""+esc(hit.u)+"\"><strong>"+esc(hit.t)+"</strong><span>"+esc(hit.s)+"</span></a></li>";
        }
        html+="</ul>";
        box.innerHTML=html;
      }
      box.hidden=false;
    }
    filterIndex(q);
  }
  input.addEventListener("input", function(){ show(input.value); });
  input.addEventListener("keydown", function(e){
    if(e.key==="Escape"){ box.hidden=true; box.innerHTML=""; }
  });
  document.addEventListener("click", function(e){
    if(!box.contains(e.target) && e.target!==input){ box.hidden=true; }
  });
  var initial="";
  try { initial=new URLSearchParams(window.location.search).get("q")||""; } catch(err){ initial=""; }
  if(initial){ input.value=initial; show(initial); }
  else filterIndex("");
  var sums=document.querySelectorAll(".grp > summary");
  for(var n=0;n<sums.length;n++){
    sums[n].addEventListener("click", function(){
      var parent=this.parentNode;
      var open=document.querySelectorAll(".grp[open]");
      for(var i=0;i<open.length;i++) if(open[i]!==parent) open[i].removeAttribute("open");
    });
  }
})();"""

DOCK_JS = r"""(function(){
  var header=document.getElementById("site-header");
  var slot=document.getElementById("head-slot");
  var toggle=document.querySelector(".search-toggle");
  var search=document.getElementById("site-search");
  var menu=document.querySelector("details.menu");
  if(!header||!slot) return;
  var docked=false;
  var fullH=0;
  function compactPx(){
    var raw=getComputedStyle(document.documentElement).getPropertyValue("--header-compact")||"132px";
    var n=parseFloat(raw);
    if(String(raw).indexOf("rem")>=0){
      n=n*parseFloat(getComputedStyle(document.documentElement).fontSize||"16");
    }
    return n||132;
  }
  function setSearchOpen(open){
    if(!search||!toggle) return;
    if(open && !document.body.classList.contains("is-docked") && !isNarrow()) open=false;
    search.classList.toggle("is-open", open);
    toggle.setAttribute("aria-expanded", open?"true":"false");
    if(open){ if(menu) menu.removeAttribute("open"); closeGroups(); }
    if(open){
      var input=document.getElementById("q");
      if(input) input.focus();
    }
  }
  function measure(){
    if(docked) return;
    if(menu && menu.hasAttribute("open")) return;
    fullH=header.offsetHeight;
  }
  var nav=document.getElementById("site-nav");
  function isNarrow(){
    return window.matchMedia("(max-width: 959px)").matches;
  }
  function closeGroups(){
    var open=document.querySelectorAll(".grp[open]");
    for(var i=0;i<open.length;i++) open[i].removeAttribute("open");
  }
  function updateHint(){
    if(!nav) return;
    var more=(docked || document.body.classList.contains("is-narrow")) && nav.scrollWidth>nav.clientWidth+8;
    var atEnd=nav.scrollLeft+nav.clientWidth>=nav.scrollWidth-8;
    var atStart=nav.scrollLeft<=8;
    document.body.classList.toggle("nav-more-right", !!(more && !atEnd));
    document.body.classList.toggle("nav-more-left", !!(more && !atStart));
  }
  function revealCurrent(){
    if(!nav) return;
    var cur=nav.querySelector(".grp.has-current");
    if(!cur || nav.scrollWidth<=nav.clientWidth+8){ updateHint(); return; }
    var left=cur.offsetLeft-(nav.clientWidth-cur.offsetWidth)/2;
    nav.scrollLeft=left<0?0:left;
    updateHint();
  }
  function dock(){
    if(docked) return;
    if(menu) menu.removeAttribute("open");
    closeGroups();
    setSearchOpen(false);
    measure();
    if(!fullH) fullH=header.offsetHeight;
    slot.style.height=fullH+"px";
    document.body.classList.add("is-docked");
    docked=true;
    revealCurrent();
  }
  function undock(){
    if(!docked) return;
    setSearchOpen(false);
    closeGroups();
    if(menu) menu.removeAttribute("open");
    document.body.classList.remove("is-docked");
    document.body.classList.remove("nav-more-right");
    document.body.classList.remove("nav-more-left");
    slot.style.height="";
    docked=false;
    measure();
  }
  function syncBar(){
    var narrow=isNarrow();
    document.body.classList.toggle("is-narrow", narrow);
    if(header) document.documentElement.style.setProperty("--header-mobile", header.offsetHeight+"px");
    if(narrow && docked) undock();
    updateHint();
  }
  function onScroll(){
    if(isNarrow()){
      if(docked) undock();
      return;
    }
    var y=window.scrollY||document.documentElement.scrollTop||0;
    var line=fullH-compactPx();
    if(!fullH) measure();
    if(!docked){
      measure();
      if(fullH>compactPx() && y>fullH-compactPx()) dock();
    } else if(y<line-24){
      undock();
    }
  }
  if(toggle){
    toggle.addEventListener("click", function(){
      var open=toggle.getAttribute("aria-expanded")==="true";
      setSearchOpen(!open);
    });
  }
  if(menu){
    var sum=menu.querySelector("summary");
    if(sum) sum.addEventListener("click", function(){ setSearchOpen(false); });
  }
  document.addEventListener("keydown", function(e){
    if(e.key!=="Escape") return;
    setSearchOpen(false);
    closeGroups();
    if(menu && menu.hasAttribute("open")) menu.removeAttribute("open");
    var box=document.getElementById("search-results");
    if(box){ box.hidden=true; box.innerHTML=""; }
  });
  document.addEventListener("click", function(e){
    if(!(docked||isNarrow())||header.contains(e.target)) return;
    setSearchOpen(false);
    closeGroups();
    if(menu) menu.removeAttribute("open");
  });
  if(nav){
    nav.addEventListener("scroll", updateHint, {passive:true});
    var topicSums=nav.querySelectorAll(".grp>summary");
    for(var s=0;s<topicSums.length;s++){
      topicSums[s].addEventListener("click", function(){ setSearchOpen(false); });
    }
  }
  document.addEventListener("focusin", function(e){
    var t=e.target;
    var narrow=isNarrow();
    if(!t||(!docked && !narrow)) return;
    if(nav && nav.contains(t) && nav.scrollWidth>nav.clientWidth+8 && t.closest){
      var grp=t.closest(".grp");
      if(grp){
        var pad=16;
        var left=grp.offsetLeft-pad;
        var right=grp.offsetLeft+grp.offsetWidth+pad;
        if(left<nav.scrollLeft) nav.scrollLeft=Math.max(0,left);
        else if(right>nav.scrollLeft+nav.clientWidth) nav.scrollLeft=right-nav.clientWidth;
        updateHint();
      }
    }
    if(header.contains(t)||(t.classList&&t.classList.contains("skip"))) return;
    var edge=(narrow?header.offsetHeight:compactPx())+16;
    var r=t.getBoundingClientRect();
    if(r.bottom>edge && r.top>=edge) return;
    var y=(window.scrollY||0)+r.top-edge;
    window.scrollTo(0, y<0?0:y);
  });
  window.addEventListener("scroll", onScroll, {passive:true});
  window.addEventListener("resize", function(){
    if(docked) undock();
    measure();
    syncBar();
    onScroll();
  });
  measure();
  syncBar();
  onScroll();
})();"""

class Site:
    def __init__(s, root, base, brand, groups, footer, css, sequences=(), summaries=None, read_next=None, aliases=None, related=(), verify=None, disclaimer=""):
        s.out = os.path.join(root, "site")
        s.base = base.rstrip("/")
        s.brand = brand
        s.groups = groups
        s.footer = footer
        s.css = css
        s.pages = []
        s.related = list(related or ())
        s.verify = dict(verify or {})
        s.disclaimer = disclaimer or ""
        s.warns = 0
        s.sequences = [list(seq) for seq in (sequences or ())]
        s.summaries = dict(summaries or {})
        s.read_next = dict(read_next or {})
        s.aliases = dict(aliases or {})
        s.sourced = set()
        s.titles = {p: t for g, items in groups for p, t in items}
        s.titles["index.html"] = "Home"
        s.titles["404.html"] = "Page not found"
        s.stage = {p: g for g, items in groups for p, t in items}
        s._search_cache = None
        if os.path.exists(s.out):
            shutil.rmtree(s.out)
        os.makedirs(s.out)

    def _search_json(s):
        if s._search_cache is not None:
            return s._search_cache
        rows = [{"u": "/", "t": "Home", "s": "Start here, top tasks, and every topic.", "g": "Home", "k": "home driver license walk-in appointment DMV"}]
        for g, items in s.groups:
            for p, t in items:
                rows.append({"u": href(p), "t": t, "s": s.summaries.get(p, ""), "g": g, "k": s.aliases.get(p, "")})
        s._search_cache = json.dumps(rows, ensure_ascii=False).replace("<", "\\u003c")
        return s._search_cache

    def _warn(s, path, title, desc):
        if not 50 <= len(title) <= 60:
            s.warns += 1
            print(f"WARNING: title length {len(title)} outside 50-60 for {path}: {title}")
        if not 120 <= len(desc) <= 160:
            s.warns += 1
            print(f"WARNING: description length {len(desc)} outside 120-160 for {path}: {desc}")

    def _json(s, obj):
        raw = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
        return raw.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")

    def _related(s):
        parts = [a(u, t) for u, t in s.related]
        if not parts:
            return ""
        if len(parts) == 1:
            joined = parts[0]
        elif len(parts) == 2:
            joined = parts[0] + " and " + parts[1]
        else:
            joined = ", ".join(parts[:-1]) + " and " + parts[-1]
        return f'<p class="related"><strong>Related guides:</strong> {joined}.</p>'

    def _neighbors(s, path):
        for seq in s.sequences:
            if path in seq:
                i = seq.index(path)
                prev = seq[i - 1] if i else None
                nxt = seq[i + 1] if i + 1 < len(seq) else None
                return prev, nxt
        return None, None

    def _trust(s, shown, checked_against):
        parts = []
        if checked_against:
            links = [a(url, label) for label, url in checked_against]
            if len(links) == 1:
                joined = links[0]
            elif len(links) == 2:
                joined = links[0] + " and " + links[1]
            else:
                joined = ", ".join(links[:-1]) + ", and " + links[-1]
            parts.append(f'<p class="sourced">Checked against {joined} on {esc(shown)}.</p>')
        parts.append(f'<p class="last-checked">Last checked: {esc(shown)}.</p>')
        return "".join(parts)

    def page(s, path, title, desc, body, faq=None, error=False, sitemap=True, crumb=None, checked=None, lastmod=None, checked_against=None):
        canon = canon_url(s.base, path)
        s._warn(path, title, desc)
        shown = checked or D
        modified = lastmod or ISO
        if checked_against:
            s.sourced.add(path)
        kind = "error" if error else ("home" if path == "index.html" else "article")
        summary = s.summaries.get(path, "")
        if "<h1>" in body:
            body = body.replace("<h1>", '<h1 id="page-title">', 1)
        trust = s._trust(shown, checked_against)
        if "<h1" in body:
            body = body.replace("</h1>", "</h1>" + trust, 1)
        if summary and kind == "article" and path != "find/index.html" and "<h1" in body:
            body = body.replace("</h1>" + trust, "</h1>" + trust + '<div class="inshort"><p><strong>In short.</strong> ' + esc(summary) + "</p></div>", 1)
        nav_bits = []
        for g, items in s.groups:
            links = []
            here = False
            for p, t in items:
                cur = ' aria-current="page"' if p == path else ""
                cls = ' class="is-current"' if p == path else ""
                if p == path:
                    here = True
                links.append(f'<a href="{href(p)}"{cls}{cur}>{esc(t)}</a>')
            mark = ' aria-current="true"' if here else ""
            nav_bits.append(f'<details class="grp{" has-current" if here else ""}"><summary{mark}>{esc(g)}</summary><div class="glinks">' + "".join(links) + "</div></details>")
        nav = "".join(nav_bits)
        def addid(m):
            return f'<h2 id="{slug(m.group(1))}">{m.group(1)}</h2>'
        body = re.sub(r"<h2>(.*?)</h2>", addid, body)
        h2pos = body.find("<h2")
        if h2pos == -1:
            head, rest = body, ""
        else:
            head, rest = body[:h2pos], body[h2pos:]
        plain = s.titles.get(path) or (crumb or title)
        if path == "index.html":
            crumbs = '<nav class="crumbs" aria-label="Breadcrumb"><ol><li><span aria-current="page">Home</span></li></ol></nav>'
        else:
            items_html = ['<li><a href="/">Home</a></li>']
            stage = None if error else s.stage.get(path)
            if stage:
                items_html.append(f'<li><a href="/#{slug(stage)}">{esc(stage)}</a></li>')
            items_html.append(f'<li><span aria-current="page">{esc(plain if not error else (crumb or "Page not found"))}</span></li>')
            crumbs = '<nav class="crumbs" aria-label="Breadcrumb"><ol>' + "".join(items_html) + "</ol></nav>"
        prev, nxt = s._neighbors(path)
        def step_link(target, word, cls):
            if not target:
                return ""
            label = s.titles.get(target)
            if not label:
                return ""
            return f'<a class="{cls}" href="{href(target)}"><span class="pn-k">{word}</span><span class="pn-t">{esc(label)}</span></a>'
        pn_prev, pn_next = step_link(prev, "Previous", "prev"), step_link(nxt, "Next", "next")
        pn = f'<nav class="pn" aria-label="Previous and next">{pn_prev}{pn_next}</nav>' if (pn_prev or pn_next) else ""
        step_items = []
        for number, dest in enumerate(s.read_next.get(path) or [], start=1):
            label = s.titles.get(dest)
            if not label:
                continue
            blurb = s.summaries.get(dest, "")
            blurb_html = f'<span class="ls">{esc(blurb)}</span>' if blurb else ""
            step_items.append(f'<li><a class="next-card" href="{href(dest)}"><span class="next-k">Step {number}</span><span class="lt">{esc(label)}</span>{blurb_html}</a></li>')
        nextsteps = '<aside class="nextsteps" aria-labelledby="next-steps"><h2 id="next-steps">Next steps</h2><ol>' + "".join(step_items) + "</ol></aside>" if step_items else ""
        crumbs_ld = [{"@type": "ListItem", "position": 1, "name": "Home", "item": s.base + "/"}]
        if path != "index.html":
            pos = 2
            stage = None if error else s.stage.get(path)
            if stage:
                crumbs_ld.append({"@type": "ListItem", "position": pos, "name": stage, "item": s.base + "/#" + slug(stage)})
                pos += 1
            item = {"@type": "ListItem", "position": pos, "name": crumb or plain}
            if not error:
                item["item"] = canon
            crumbs_ld.append(item)
        graph = []
        if kind == "home":
            org = s.base + "/#organization"
            graph.append({"@type": "WebSite", "@id": s.base + "/#website", "name": s.brand, "url": s.base + "/", "description": desc, "inLanguage": "en-US", "publisher": {"@id": org}})
            graph.append({"@type": "Organization", "@id": org, "name": s.brand, "url": s.base + "/", "logo": {"@type": "ImageObject", "url": s.base + "/apple-touch-icon.png"}})
        graph.append({"@type": "BreadcrumbList", "@id": canon + "#breadcrumb", "itemListElement": crumbs_ld})
        if kind == "article":
            h1m = re.search(r"<h1[^>]*>(.*?)</h1>", body, re.S)
            headline = H.unescape(re.sub(r"<[^>]+>", "", h1m.group(1))) if h1m else title
            img = s.base + "/og.png"
            graph.append({"@type": "Article", "@id": canon + "#article", "headline": title, "description": desc, "datePublished": modified, "dateModified": modified, "inLanguage": "en-US", "mainEntityOfPage": canon, "image": img, "author": {"@type": "Organization", "name": s.brand, "url": s.base + "/"}, "publisher": {"@type": "Organization", "name": s.brand, "url": s.base + "/", "logo": {"@type": "ImageObject", "url": s.base + "/apple-touch-icon.png"}}})
        if faq:
            graph.append({"@type": "FAQPage", "@id": canon + "#faq", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": ans}} for q, ans in faq]})
        ld = f'<script type="application/ld+json">{s._json({"@context": "https://schema.org", "@graph": graph})}</script>'
        verify = "".join(f'<meta name="{esc(k)}" content="{esc(v)}" />' for k, v in s.verify.items() if v)
        robots = '<meta name="robots" content="noindex">' if error else ""
        og_type = "website" if kind != "article" else "article"
        img = s.base + "/og.png"
        disc = f"<p>{esc(s.disclaimer)}</p>" if s.disclaimer else ""
        h = f'''<!doctype html><html lang="en-US"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="{STOPS[0]}"><title>{esc(title)}</title><meta name="description" content="{esc(desc)}">{robots}<link rel="canonical" href="{esc(canon)}"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="/apple-touch-icon.png"><meta property="og:locale" content="en_US"><meta property="og:type" content="{og_type}"><meta property="og:site_name" content="{esc(s.brand)}"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{esc(canon)}"><meta property="og:image" content="{esc(img)}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="{esc(s.brand)}"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(desc)}"><meta name="twitter:image" content="{esc(img)}"><meta name="twitter:image:alt" content="{esc(s.brand)}">{verify}{ld}<style>{s.css}</style><script defer src="/_vercel/insights/script.js"></script></head><body>
<a class="skip" href="#content">Skip to content</a>
<div id="head-slot"><header id="site-header"><div class="shell">
<a class="brand" href="/" aria-label="{esc(s.brand)}">{MARK}<span class="name"><span class="name-main">{esc(s.brand)}</span><span class="name-compact" aria-hidden="true">South Florida DMV</span></span></a>
<button type="button" class="search-toggle" aria-expanded="false" aria-controls="site-search"><svg class="search-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><circle cx="10.5" cy="10.5" r="6.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M15.5 15.5 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg><span class="search-toggle-text">Search</span></button>
<a class="headlink" href="/find/">All pages</a>
<span class="headcta"><a class="action" href="/fake-appointment-sites/"><span class="action-long">Spot fake appointment sites</span><span class="action-short"><span class="action-wide">Fake sites</span><span class="action-mini">Fakes</span></span></a></span>
<div class="search-wrap" id="site-search"><form class="sitesearch" role="search" action="/find/" method="get"><label for="q">Search this guide</label><input id="q" name="q" type="search" autocomplete="off" autocapitalize="off" autocorrect="off" spellcheck="false"><button type="submit">Search</button></form><div id="search-results" class="search-results" hidden role="region" aria-live="polite" aria-label="Matching pages"></div></div>
<details class="menu"><summary aria-controls="site-nav">Topics</summary></details><div class="nav-row"><nav id="site-nav" class="top" aria-label="Topics">{nav}</nav>
<span class="nav-fade nav-fade-left" aria-hidden="true"></span><span class="nav-fade nav-fade-right" aria-hidden="true"></span><span class="nav-hint" aria-hidden="true"></span></div>
<p class="head-note">{esc(HEADER_LINE)} <a href="/disclaimer/">Disclaimer</a></p>
</div></header></div>
<main id="content" tabindex="-1"><div class="shell">{crumbs}<article class="content" aria-labelledby="page-title"><div class="head-block">{head}</div><div class="layout"><div class="rest">{rest}{pn}{nextsteps}</div></div></article></div></main>
<footer><div class="shell"><nav class="footnav" aria-label="About this guide"><a href="/find/">All pages</a><a href="/faq/">Common questions</a><a href="/disclaimer/">Disclaimer</a></nav><p>{s.footer}</p>{disc}<p><a href="/disclaimer/">Disclaimer</a></p>{s._related()}<p>Last checked: {shown}.</p></div></footer>
<script type="application/json" id="search-data">{s._search_json()}</script><script>{SEARCH_JS}</script><script>{DOCK_JS}</script></body></html>'''
        for bad in ("\u2014", "\u2013", "&mdash;", "&ndash;"):
            assert bad not in h, (path, bad)
        p = os.path.join(s.out, path)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w", encoding="utf-8").write(h)
        if sitemap:
            s.pages.append((path, modified))

    def finish(s):
        bots = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "PerplexityBot", "Bingbot", "Googlebot", "ClaudeBot", "*"]
        open(os.path.join(s.out, "robots.txt"), "w", encoding="utf-8").write("".join(f"User-agent: {b}\nAllow: /\n\n" for b in bots) + f"Sitemap: {s.base}/sitemap.xml\n")
        urls = "".join(f"<url><loc>{canon_url(s.base, p)}</loc><lastmod>{mod}</lastmod></url>\n" for p, mod in sorted(s.pages))
        open(os.path.join(s.out, "sitemap.xml"), "w", encoding="utf-8").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + "</urlset>\n")
        worst, worst_at, _rows = check_contrast()
        print(f"Header contrast worst {worst:.2f}:1 ({worst_at})")
        needles = (s.disclaimer, "Last checked:", "/_vercel/insights/script.js", HEADER_LINE, 'href="/disclaimer/"', 'property="og:locale" content="en_US"')
        gsc = s.verify.get("google-site-verification") or ""
        for path in [p for p, _m in s.pages] + ["404.html"]:
            html = open(os.path.join(s.out, path), encoding="utf-8").read()
            for needle in needles:
                if needle and needle not in html:
                    raise SystemExit(f"Missing {needle!r} on {path}")
            if 'class="notice"' in html or "On this page" in html:
                raise SystemExit("Old disclaimer bar or contents box returned on " + path)
            h1_at = html.find("</h1>")
            lc_at = html.find("Last checked:")
            if h1_at < 0 or lc_at < h1_at:
                raise SystemExit("Last checked should sit under the H1 on " + path)
            ca_at = html.find("Checked against ")
            if path in s.sourced:
                if not (h1_at < ca_at < lc_at):
                    raise SystemExit("Checked against should sit under the H1 on " + path)
            elif ca_at != -1:
                raise SystemExit("Unexpected checked-against line on " + path)
            if s.read_next.get(path) and 'id="next-steps"' not in html:
                raise SystemExit("Missing next steps on " + path)
            if gsc and gsc not in html:
                raise SystemExit("Missing Google verification on " + path)
            if path != "404.html":
                if f'rel="canonical" href="{s.base}/' not in html:
                    raise SystemExit("Missing canonical on " + path)
                if "noindex" in html:
                    raise SystemExit("Unexpected noindex on " + path)
            elif "noindex" not in html:
                raise SystemExit("404 should be noindex")
        missing = _check_links(s.out, [p for p, _m in s.pages] + ["404.html"])
        if missing:
            raise SystemExit("Broken internal links:\n" + "\n".join(missing))
        if s.warns:
            print(f"{s.warns} SEO length warnings")

def _check_links(out, pages):
    missing = []
    for path in pages:
        html = open(os.path.join(out, path), encoding="utf-8").read()
        ids = set(re.findall(r'\bid="([^"]*)"', html))
        for href_v in re.findall(r'\bhref="([^"]*)"', html):
            if href_v.startswith(("http://", "https://", "mailto:", "tel:")):
                continue
            url, _, frag = href_v.partition("#")
            if url == "":
                if frag and frag not in ids:
                    missing.append(f"{path} -> {href_v}")
                continue
            if url.startswith("/"):
                rel = url.lstrip("/")
                target = "index.html" if rel == "" else (rel + "index.html" if rel.endswith("/") else rel)
            else:
                target = os.path.normpath(os.path.join(os.path.dirname(path), url)).replace("\\", "/")
            dest = os.path.join(out, target)
            if not os.path.isfile(dest):
                missing.append(f"{path} -> {href_v} (missing {target})")
                continue
            if frag:
                tids = set(re.findall(r'\bid="([^"]*)"', open(dest, encoding="utf-8").read()))
                if frag not in tids:
                    missing.append(f"{path} -> {href_v} (missing #{frag})")
    return missing

CSS = r''':root{
--s12:12px;--s16:16px;--s24:24px;--s32:32px;--s40:40px;
--header-compact:132px;--scroll-pad:148px;
--ink:#1a1814;--paper:#f4f1ea;--link:#0a3d66;--visited:#3d2a6b;--line:#d9d3c7;
--gold:#f6d98a;--sand:#f4efe4;--deep:#102830;
--head-bg:linear-gradient(90deg,#0A4550 0%,#0E3A58 52%,#3A3040 100%);
--font:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif
}
*,*::before,*::after{box-sizing:border-box}
html{scroll-padding-top:0;color-scheme:light}
body{margin:0;color:var(--ink);background:var(--paper);font-family:var(--font);font-size:1.125rem;line-height:1.6}
h1,h2,h3,h4,h5,h6,button,input,textarea,select,summary{font-family:var(--font)}
h1,h2,h3,h4,h5,h6{font-weight:700;line-height:1.25;scroll-margin-top:var(--scroll-pad)}
[id]{scroll-margin-top:var(--scroll-pad)}
[hidden]{display:none!important}
img,svg{max-width:100%}
.shell{max-width:96rem;margin:0 auto;padding-left:var(--s16);padding-right:var(--s16);min-width:0}
.skip{position:absolute;left:var(--s12);top:0;transform:translateY(-120%);background:#fff;color:var(--ink);padding:var(--s12) var(--s16);z-index:50;min-height:48px;font-weight:700}
.skip:focus,.skip:focus-visible{transform:none}
#head-slot{min-width:0}
#site-header{background:var(--head-bg);color:#fff;position:relative;z-index:40}
#site-header a{color:#fff}
#site-header .shell{display:grid;grid-template-columns:minmax(0,1fr) auto;grid-template-areas:"brand searchbtn" "nav nav" "note note";align-items:center;column-gap:var(--s12);row-gap:var(--s12);padding-top:var(--s12);padding-bottom:var(--s12);position:relative}
.brand{grid-area:brand;display:flex;align-items:center;gap:var(--s12);min-width:0;min-height:48px;color:#fff;text-decoration:none;font-weight:700}
.mark{flex:none;display:flex}
.mark svg{display:block;width:36px;height:24px}
.name{display:flex;flex-direction:column;min-width:0}
.name-main{display:none;font-size:1.125rem;line-height:1.3}
.name-compact{display:block;font-size:1rem;line-height:1.2;font-weight:700;white-space:nowrap}
.head-note{grid-area:note;margin:0;font-size:1rem;font-weight:700;line-height:1.35;color:var(--sand)}
#site-header .head-note a,#site-header .head-note a:visited{color:var(--sand)}
.headlink{grid-area:words;display:none;align-items:center;justify-self:end;min-height:48px;padding:var(--s12) 0;font-weight:700;text-decoration:underline;text-underline-offset:.15em}
.headcta{grid-area:cta;display:none;align-items:center;margin-top:0}
.search-toggle{grid-area:searchbtn;display:inline-flex;align-items:center;justify-content:center;gap:var(--s12);min-height:48px;min-width:48px;width:48px;padding:0;font:inherit;font-size:1rem;font-weight:700;line-height:1.2;color:#fff;background:transparent;border:2px solid #fff;border-radius:8px;cursor:pointer;position:relative}
.search-toggle-text{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
.search-icon{width:1.15rem;height:1.15rem;display:block;flex:none}
.search-wrap{grid-area:auto;display:none;margin:0;position:absolute;top:100%;left:0;right:0;z-index:36;background:var(--head-bg);padding:var(--s12) 0 var(--s16);box-shadow:0 12px 24px rgba(0,0,0,.28)}
.search-wrap.is-open{display:block}
.sitesearch{display:flex;flex-wrap:wrap;align-items:center;gap:var(--s12)}
.sitesearch label{flex:1 1 100%;color:#fff;font-weight:700}
.sitesearch input[type="search"]{flex:1 1 12rem;min-width:0;min-height:48px;font:inherit;color:var(--ink);background:#fff;border:2px solid #fff;border-radius:8px;padding:var(--s12) var(--s16)}
.sitesearch button{min-height:48px;min-width:6rem;padding:var(--s12) var(--s16);font:inherit;font-weight:700;color:var(--ink);background:var(--gold);border:2px solid var(--ink);border-radius:8px;cursor:pointer}
.sitesearch button:hover{background:#e2bf62}
.search-results{position:absolute;z-index:35;left:0;right:0;top:100%;margin-top:var(--s12);background:#fff;color:var(--ink);border:2px solid var(--ink);border-radius:8px;max-height:70vh;overflow:auto}
.search-results ul{list-style:none;margin:0;padding:0}
.search-results a{display:flex;flex-direction:column;gap:var(--s12);min-height:48px;justify-content:center;padding:var(--s12) var(--s16);color:var(--link);text-decoration:underline;text-underline-offset:.12em}
.search-results a span{color:var(--ink);font-weight:400}
.search-empty{margin:0;padding:var(--s12);color:var(--ink)}
.action-short,.action-mini{display:none}
a.action{display:inline-flex;align-items:center;justify-content:center;min-height:48px;background:var(--gold);color:var(--ink);font-weight:700;text-decoration:none;border:2px solid var(--ink);border-radius:8px;padding:var(--s12) var(--s16);line-height:1.3;text-align:center}
a.action:hover{background:#e2bf62;color:var(--ink)}
a.action:visited,#site-header a.action{color:var(--ink)}
.headcta a.action{width:100%}
.menu{display:none}
.menu summary{display:flex;align-items:center;justify-content:center;width:100%;min-height:48px;padding:var(--s12) var(--s16);background:#fff;color:var(--ink);border-radius:8px;font-weight:700;cursor:pointer;list-style:none}
.menu summary::-webkit-details-marker,.grp summary::-webkit-details-marker{display:none}
.menu summary::marker,.grp summary::marker{content:""}
.nav-row{grid-area:nav;position:relative;min-width:0}
nav.top{display:flex;flex-direction:row;flex-wrap:nowrap;align-items:center;gap:var(--s12);margin:0;padding:0;border:0;min-width:0;overflow-x:auto;overflow-y:hidden;scroll-snap-type:x proximity;scrollbar-width:thin}
.grp{position:relative;flex:0 0 auto;min-width:0;width:auto}
.grp>summary{display:flex;align-items:center;justify-content:space-between;gap:var(--s12);min-height:48px;padding:var(--s12) var(--s16);color:#fff;font-weight:700;cursor:pointer;list-style:none;white-space:nowrap;scroll-snap-align:start;border:1px solid rgba(255,255,255,.85);border-radius:999px;background:rgba(0,0,0,.18)}
.grp>summary::after{content:"";border:solid #fff;border-width:0 2px 2px 0;width:.45rem;height:.45rem;transform:rotate(45deg);flex:none;margin-top:-.15rem}
.grp[open]>summary::after{transform:rotate(-135deg);margin-top:.25rem}
.grp.has-current>summary{box-shadow:inset 0 -3px 0 var(--gold)}
.glinks{display:flex;flex-direction:column;min-width:0}
.glinks a{display:flex;align-items:center;min-height:48px;padding:var(--s12) var(--s16);color:#fff;text-decoration:underline;text-underline-offset:.15em;border-bottom:1px solid rgba(255,255,255,.28)}
.glinks a.is-current{font-weight:700;background:rgba(255,255,255,.16);border-radius:8px}
.grp[open] .glinks{position:fixed;z-index:46;top:var(--header-mobile,168px);left:0;right:0;background:var(--deep);border:2px solid #fff;border-radius:0 0 12px 12px;padding:var(--s12);box-shadow:0 8px 24px rgba(0,0,0,.35);max-height:min(60vh,22rem);overflow:auto}
@media(min-width:960px){
#site-header{position:relative;z-index:30}
#site-header .shell{grid-template-columns:minmax(0,1fr) auto auto;grid-template-areas:"brand words cta" "note note note" "search search search" "nav nav nav";column-gap:var(--s24);row-gap:0;padding-top:var(--s24);padding-bottom:var(--s24)}
.mark svg{width:48px;height:32px}
.name-main{display:block}
.name-compact{display:none}
.headlink{display:inline-flex}
.headcta{display:flex;justify-self:end}
.headcta a.action{width:auto}
.search-toggle{display:none}
.search-toggle-text{position:static;width:auto;height:auto;margin:0;overflow:visible;clip:auto}
.search-wrap{grid-area:search;display:block;position:relative;top:auto;left:auto;right:auto;margin-top:var(--s16);padding:0;box-shadow:none;background:transparent}
.head-note{margin-top:var(--s12)}
nav.top{overflow:visible;flex-wrap:nowrap;margin-top:var(--s24);padding-top:var(--s16);border-top:1px solid rgba(255,255,255,.35);scroll-snap-type:none}
.grp>summary{border:0;border-radius:0;background:transparent;scroll-snap-align:none}
.glinks{min-width:16rem}
.glinks a{border-bottom:0}
.grp[open] .glinks{position:absolute;z-index:34;top:100%;left:0;right:auto;max-width:min(22rem,92vw);border-radius:8px;max-height:none}
.sitesearch{flex-wrap:nowrap}
.sitesearch label{flex:0 0 auto}
}
@media(max-width:640px){.name-main{font-size:1.05rem}}
@media(max-width:359px){body{font-size:1.0625rem}.shell{padding-left:var(--s12);padding-right:var(--s12)}}
body.is-docked #site-header{position:fixed;top:0;left:0;right:0;height:var(--header-compact);z-index:40;box-shadow:0 2px 12px rgba(0,0,0,.28);overflow:visible}
body.is-docked #site-header .shell{height:100%;padding:var(--s12) var(--s16);column-gap:var(--s12);row-gap:var(--s12);grid-template-columns:minmax(0,1fr) auto auto;grid-template-rows:auto minmax(0,1fr);grid-template-areas:"brand searchbtn cta" "nav nav nav";align-items:center}
body.is-docked .brand{min-height:48px;min-width:0;gap:var(--s12)}
body.is-docked .head-note,body.is-docked .headlink,body.is-docked .menu{display:none}
body.is-docked .name-main{display:block;font-size:1rem;line-height:1.2;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
body.is-docked .name-compact{display:none}
body.is-docked .headcta{margin:0}
body.is-docked .headcta a.action{width:auto;min-height:48px;padding:var(--s12) var(--s16);font-size:1rem;line-height:1.2}
body.is-docked .action-long{display:none}
body.is-docked .action-short,body.is-docked .action-wide{display:inline}
body.is-docked .action-mini{display:none}
body.is-docked .search-toggle{display:inline-flex}
body.is-docked .search-wrap{display:none;margin:0;position:absolute;top:100%;left:0;right:0;z-index:36;background:var(--head-bg);padding:var(--s16) 0;box-shadow:0 12px 24px rgba(0,0,0,.28)}
body.is-docked .search-wrap.is-open{display:block}
body.is-docked .nav-row{grid-area:nav;min-width:0}
body.is-docked nav.top{display:flex;position:relative;margin:0;padding:0;border:0;background:transparent;box-shadow:none;flex-direction:row;flex-wrap:nowrap;align-items:center;justify-content:flex-start;gap:var(--s12);min-width:0;max-height:none;overflow:visible}
body.is-docked .grp{flex:0 0 auto;width:auto}
body.is-docked .grp>summary{min-height:48px;padding:var(--s12) var(--s16);white-space:nowrap;font-size:1rem;gap:var(--s12);border-radius:8px}
body.is-docked .grp.has-current>summary{background:rgba(255,255,255,.14);box-shadow:inset 0 -3px 0 var(--gold)}
body.is-docked .grp[open] .glinks{position:absolute;z-index:46;top:calc(100% + 12px);left:0;right:auto;min-width:16rem;max-width:min(22rem,92vw);background:var(--deep);border:2px solid #fff;border-radius:8px;padding:var(--s12);box-shadow:0 8px 24px rgba(0,0,0,.35);max-height:min(60vh,22rem);overflow:auto}
body.is-docked .grp:nth-last-child(-n+2)[open] .glinks{left:auto;right:0}
.nav-fade,.nav-hint{display:none}
.nav-hint::before{content:"";display:block;width:.5rem;height:.5rem;border:solid var(--gold);border-width:0 3px 3px 0;transform:rotate(-45deg)}
body.is-docked.nav-more-right .nav-fade-right,body.is-docked.nav-more-left .nav-fade-left,body.is-narrow.nav-more-right .nav-fade-right,body.is-narrow.nav-more-left .nav-fade-left{display:block;position:absolute;top:0;bottom:0;width:40px;pointer-events:none;z-index:4}
body.is-docked.nav-more-right .nav-fade-right,body.is-narrow.nav-more-right .nav-fade-right{right:0;background:linear-gradient(90deg,rgba(58,48,64,0),#3A3040 70%)}
body.is-docked.nav-more-left .nav-fade-left,body.is-narrow.nav-more-left .nav-fade-left{left:0;background:linear-gradient(90deg,#0A4550 30%,rgba(10,69,80,0))}
body.is-docked.nav-more-right .nav-hint,body.is-narrow.nav-more-right .nav-hint{display:flex;align-items:center;justify-content:flex-end;position:absolute;right:var(--s12);top:0;bottom:0;width:24px;pointer-events:none;z-index:5}
@media(max-width:959px){
body.is-docked nav.top{overflow-x:auto;overflow-y:hidden;scroll-snap-type:x proximity;scrollbar-width:thin;padding-bottom:0}
body.is-docked .grp>summary{scroll-snap-align:start;border:1px solid rgba(255,255,255,.85);border-radius:999px;background:rgba(0,0,0,.18)}
body.is-docked .grp[open] .glinks,body.is-docked .grp:nth-last-child(-n+2)[open] .glinks{position:fixed;top:var(--header-compact);left:0;right:0;max-width:none;border-radius:0 0 12px 12px}
}
@media(max-width:720px){
body.is-docked #site-header .shell{column-gap:var(--s12);padding-left:var(--s12);padding-right:var(--s12)}
body.is-docked .name-main{display:none}
body.is-docked .name-compact{display:block;font-size:1rem;line-height:1.2;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
body.is-docked .mark svg{width:36px;height:24px}
body.is-docked .search-toggle{padding:0;width:48px}
body.is-docked .search-toggle-text{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
body.is-docked .headcta a.action{padding:var(--s12);font-size:1rem}
body.is-docked .action-wide{display:none}
body.is-docked .action-mini{display:inline}
}
main{min-width:0}
main>.shell{padding-top:var(--s24);padding-bottom:var(--s40)}
main:focus{outline:none}
main:focus-visible{outline:3px solid var(--ink);outline-offset:-3px}
.crumbs ol{display:flex;flex-wrap:wrap;list-style:none;padding:0;margin:0 0 var(--s12);gap:0}
.crumbs li{display:flex;align-items:center;min-height:48px}
.crumbs li:not(:last-child)::after{content:"/";margin:0 var(--s12);color:#3e3a34}
.crumbs a{display:inline-flex;align-items:center;min-height:48px}
.sourced,.last-checked{color:#3e3a34}
article.content{min-width:0}
.head-block{margin:0}
.head-block p{margin:0 0 var(--s16);max-width:66ch}
h1{font-size:clamp(1.85rem,1.2rem + 2vw,2.5rem);margin:0 0 var(--s16)}
h2{font-size:1.5rem;margin:var(--s40) 0 var(--s12)}
h3{font-size:1.28rem;margin:var(--s24) 0 var(--s12)}
.content p,.inshort p,footer p{max-width:66ch}
.inshort{background:#eef4f1;border-left:6px solid #1d4f3e;border-radius:12px;padding:var(--s16) var(--s24);margin:0 0 var(--s24)}
.inshort p{margin:0}
.layout{display:flex;flex-direction:column;gap:var(--s24);min-width:0;margin-top:var(--s32)}
.rest{min-width:0}
.rest>h2:first-child,.rest>h3:first-child{margin-top:0}
.card{background:#fff;border:1px solid var(--line);border-radius:12px;padding:var(--s24);margin:var(--s16) 0}
h2+.card,h3+.card{margin-top:0}
.card>:first-child{margin-top:0}
.card>:last-child{margin-bottom:0}
.card p{margin:0 0 var(--s16)}
.card ul,.card ol{margin:var(--s12) 0 0;padding-left:1.25rem}
.card li+li{margin-top:var(--s12)}
.warn{border-left:6px solid #9b2c2c;background:#fdeeee}
.note{border-left:6px solid #8a5a00;background:#fff8ec}
.conf{border-left:6px solid #5c3d78;background:#f6f1fa}
.card.warn,.card.note,.card.conf{max-width:70ch}
.timeline{list-style:none;margin:var(--s16) 0 0;padding:0;counter-reset:step;display:grid;gap:var(--s16)}
.period{counter-increment:step;background:#fff;border:1px solid var(--line);border-radius:12px;padding:var(--s24);margin:0}
.period>h3{margin:0 0 var(--s16);font-size:1.35rem}
.period>h3::before{content:counter(step) ". "}
.period-pages{list-style:none;padding:0;margin:0;display:grid;gap:var(--s12)}
.tasks,.link-grid,.index-list{list-style:none;padding:0;margin:var(--s16) 0 0;display:grid;gap:var(--s16);grid-template-columns:1fr}
@media(min-width:720px){.tasks,.link-grid,.index-list{grid-template-columns:1fr 1fr}}
.topic{margin:0 0 var(--s32)}
.topic>h3{margin-top:0}
.jump{display:flex;flex-direction:column;justify-content:center;gap:var(--s12);min-height:48px;padding:var(--s16) var(--s24);background:#fff;color:var(--ink);border:1px solid var(--line);border-radius:12px;text-decoration:none}
.jump:hover{border-color:var(--link)}
.jump .lt{color:var(--link);font-weight:700;text-decoration:underline;text-underline-offset:.12em;font-size:1.125rem}
.jump .ls{color:var(--ink);font-size:1rem;text-decoration:none;font-weight:400}
a.jump:visited .lt{color:var(--visited)}
.src{color:#3e3a34;font-size:1rem}
.src,.card,td,th{overflow-wrap:anywhere}
.content ul,.content ol{margin:var(--s12) 0 var(--s16);padding-left:1.25rem}
.content li+li{margin-top:var(--s12)}
.pn{display:grid;gap:var(--s16);margin-top:var(--s40)}
.pn a{display:flex;flex-direction:column;justify-content:center;gap:var(--s12);min-height:48px;padding:var(--s16) var(--s24);background:#fff;border:1px solid var(--line);border-radius:12px;text-decoration:none}
.pn .pn-k{color:#3e3a34;font-size:1rem;font-weight:700}
.pn .pn-t{color:var(--link);font-weight:700;text-decoration:underline;text-underline-offset:.12em}
.pn a:visited .pn-t{color:var(--visited)}
@media(min-width:720px){.pn:has(a.prev):has(a.next){grid-template-columns:1fr 1fr}.pn a.next{align-items:flex-end;text-align:right}}
.nextsteps{margin-top:var(--s40)}
.nextsteps h2{margin-top:0}
.nextsteps ol{list-style:none;padding:0;margin:var(--s16) 0 0;display:grid;gap:var(--s16);grid-template-columns:1fr}
.next-card{display:flex;flex-direction:column;align-items:flex-start;gap:var(--s12);height:100%;min-height:48px;padding:var(--s24);background:#fff;color:var(--ink);border:1px solid var(--line);border-radius:12px;text-decoration:none}
.next-card .next-k{color:#3e3a34;font-size:1rem;font-weight:700}
.next-card .lt{color:var(--link);font-weight:700;text-decoration:underline;text-underline-offset:.12em;font-size:1.25rem}
.next-card .ls{color:var(--ink);font-size:1rem;font-weight:400}
a.next-card:visited .lt{color:var(--visited)}
@media(min-width:960px){.nextsteps ol{grid-template-columns:1fr 1fr 1fr}}
.index-status{font-weight:700;margin:0 0 var(--s16)}
a{color:var(--link)}
a:visited{color:var(--visited)}
.content a{text-decoration:underline;text-underline-offset:.12em}
.content a.next-card,.content a.jump{text-decoration:none}
.content a.next-card .lt,.content a.jump .lt{text-decoration:underline;text-underline-offset:.12em}
table{border-collapse:collapse;width:100%;background:#fff;font-size:1rem}
th,td{border:1px solid var(--line);padding:var(--s12) var(--s16);text-align:left;vertical-align:top}
th{background:#e7efe9;color:var(--ink)}
.wrap{overflow-x:auto;max-width:100%;margin:var(--s16) 0}
.filter-block{margin:var(--s16) 0 var(--s24)}
.filter-block label{display:block;font-weight:700;margin:0 0 var(--s12)}
.office-filter{width:100%;max-width:36rem;min-height:48px;font:inherit;color:var(--ink);background:#fff;border:2px solid var(--ink);border-radius:8px;padding:var(--s12) var(--s16)}
.tag{display:inline-block;font-size:.875rem;line-height:1.3;padding:var(--s12) var(--s12);border-radius:8px;background:#eee;margin:0 var(--s12) var(--s12) 0;color:var(--ink)}
.tag.ok{background:#d8f0de}
.tag.no{background:#f8d7d7}
.tag.mix{background:#fdebc8}
.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
.map-block{margin:var(--s32) 0}
.map-block>p{max-width:66ch}
/* z-index 1 keeps Leaflet panes under the sticky header (30, or 40 when docked). */
.map-frame{position:relative;z-index:1;margin:var(--s16) 0}
.office-map,.office-map.leaflet-container{height:24rem;width:100%;overflow:hidden;background:#fff;border:1px solid var(--line);border-radius:12px;font-family:var(--font);font-size:1rem;line-height:1.5;color:var(--ink)}
.office-map .map-fallback{margin:0;padding:var(--s16) var(--s24)}
.office-map .leaflet-popup-content{margin:var(--s12) var(--s16);font-family:var(--font);font-size:1rem;line-height:1.5;color:var(--ink)}
.office-map .leaflet-popup-content p{margin:0 0 var(--s12);max-width:none}
.office-map .leaflet-popup-content p:last-child{margin-bottom:0}
.office-map .leaflet-popup-content a{color:var(--link)}
.office-map .leaflet-popup-content-wrapper,.office-map .leaflet-popup-tip{background:#fff;color:var(--ink)}
.office-map.leaflet-container a.leaflet-popup-close-button{width:2rem;height:2rem;font:700 1.25rem/2rem var(--font);color:var(--ink);padding:0}
.office-map.leaflet-container .leaflet-bar a{width:48px;height:48px;line-height:48px;font-family:var(--font);font-size:1.25rem;font-weight:700;color:var(--ink)}
.office-map.leaflet-container .leaflet-control-zoom-in,.office-map.leaflet-container .leaflet-control-zoom-out{font-family:var(--font);font-size:1.25rem;font-weight:700;line-height:48px;width:48px;height:48px}
.office-map.leaflet-container .leaflet-control-attribution{font-family:var(--font);font-size:.875rem;line-height:1.4;color:var(--ink);background:rgba(255,255,255,.95);max-width:100%}
.office-map.leaflet-container .leaflet-control-attribution a{color:var(--link);text-decoration:underline;text-underline-offset:.12em}
.office-map .pin-icon{background:transparent;border:0}
.office-map .pin-btn{display:flex;align-items:center;justify-content:center;width:44px;height:44px;border-radius:50%;background:#0A4550;color:#fff;border:3px solid #F6D98A;font-family:var(--font);font-weight:700;font-size:1rem;line-height:1}
.office-map .leaflet-marker-icon:focus-visible,.office-map.leaflet-container a:focus-visible{outline:3px solid var(--ink);outline-offset:2px}
@media(max-width:640px){.office-map,.office-map.leaflet-container{height:20rem}}
footer{border-top:1px solid var(--line);color:var(--ink);margin-top:var(--s32)}
footer .shell{padding-top:var(--s32);padding-bottom:var(--s40)}
footer p{margin:var(--s12) 0}
.footnav{display:flex;flex-wrap:wrap;gap:var(--s12) var(--s24);margin:0 0 var(--s16);padding:0;list-style:none}
.footnav a{display:inline-flex;align-items:center;min-height:48px;font-weight:700}
:focus{outline:3px solid var(--ink);outline-offset:3px}
:focus:not(:focus-visible){outline:none}
:focus-visible{outline:3px solid var(--ink);outline-offset:3px}
#site-header a:focus-visible,#site-header button:focus-visible,#site-header input:focus-visible,#site-header summary:focus-visible{outline-color:var(--gold)}
#site-header a.action:focus-visible,#site-header .sitesearch button:focus-visible{outline-color:#fff}
.menu summary:focus-visible{outline-color:var(--ink)}
body.is-docked .search-toggle:focus-visible{outline-color:var(--gold)}
@media(max-width:959px){
#site-header{position:fixed;top:0;left:0;right:0;width:100%}
#head-slot{height:var(--header-mobile,200px)}
html{scroll-padding-top:var(--header-mobile,200px)}
h1,h2,h3,h4,h5,h6,[id]{scroll-margin-top:calc(var(--header-mobile,200px) + var(--s12))}
.crumbs ol{display:block}
.crumbs li,.crumbs a{min-height:32px}
.crumbs li{display:inline-flex}
}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
@media(forced-colors:active){
.card,.inshort,.jump,.period,.pn a,.next-card,a.action,.search-toggle,.office-map,.head-note{border:1px solid CanvasText}
a.action{background:ButtonFace;color:ButtonText}
}
'''
