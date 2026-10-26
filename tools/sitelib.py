"""Shared helpers: page shell, robots.txt, sitemap.xml, checks. Copied per site so each folder is self-contained."""
import os,html as H,shutil,sys,json
D="26 Oct 2026"
ISO="2026-10-26"
def esc(s): return H.escape(s,quote=True)
def a(url,text='source'): return f'<a href="{esc(url)}" rel="noopener">{text}</a>'
class Site:
    def __init__(s,root,base,brand,nav,footer,css,related=(),verify=None,disclaimer=""):
        s.out=os.path.join(root,'site'); s.base=base.rstrip('/'); s.brand=brand; s.nav=nav; s.footer=footer; s.css=css; s.pages=[]
        s.related=list(related or ()); s.verify=dict(verify or {}); s.disclaimer=disclaimer or ""; s.warns=0
        s.labels={p:t for p,t in s.nav}
        if os.path.exists(s.out): shutil.rmtree(s.out)
        os.makedirs(s.out)
    def _canon(s,path):
        if path=='404.html': return s.base+'/404.html'
        return s.base+'/'+path.replace('index.html','')
    def _warn(s,path,title,desc):
        if not 50<=len(title)<=60:
            s.warns+=1
            print(f'WARNING: title length {len(title)} outside 50-60 for {path}: {title}',file=sys.stderr)
        if not 120<=len(desc)<=160:
            s.warns+=1
            print(f'WARNING: description length {len(desc)} outside 120-160 for {path}: {desc}',file=sys.stderr)
    def _json(s,obj):
        raw=json.dumps(obj,ensure_ascii=False,separators=(',',':'))
        return raw.replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    def _related(s):
        parts=[a(u,t) for u,t in s.related]
        if not parts: return ''
        if len(parts)==1: joined=parts[0]
        elif len(parts)==2: joined=parts[0]+' and '+parts[1]
        else: joined=', '.join(parts[:-1])+' and '+parts[-1]
        return f'<p class="related"><strong>Related guides:</strong> {joined}.</p>'
    def page(s,path,title,desc,body,faq=None,error=False,sitemap=True,crumb=None,checked=None,lastmod=None):
        canon=s._canon(path); s._warn(path,title,desc); is_home=path=='index.html'
        shown=checked or D; modified=lastmod or ISO
        nav=''.join(f'<a href="{esc(p)}">{esc(t)}</a>' for p,t in s.nav)
        verify=''.join(f'<meta name="{esc(k)}" content="{esc(v)}" />' for k,v in s.verify.items() if v)
        robots='<meta name="robots" content="noindex">' if error else ''
        og_type='website' if (is_home or error) else 'article'
        img=s.base+'/og.png'
        if path=='404.html':
            crumbs=[('Home',s.base+'/'),(crumb or 'Page not found',canon)]
        elif is_home:
            crumbs=[('Home',canon)]
        else:
            clean='/'+path.replace('index.html','')
            crumbs=[('Home',s.base+'/'),(crumb or s.labels.get(clean) or title,canon)]
        graph=[]
        if is_home:
            org=s.base+'/#organization'
            graph.append({"@type":"WebSite","@id":s.base+"/#website","name":s.brand,"url":s.base+"/","description":desc,"inLanguage":"en-US","publisher":{"@id":org}})
            graph.append({"@type":"Organization","@id":org,"name":s.brand,"url":s.base+"/","logo":{"@type":"ImageObject","url":s.base+"/apple-touch-icon.png"}})
        graph.append({"@type":"BreadcrumbList","@id":canon+"#breadcrumb","itemListElement":[{"@type":"ListItem","position":i,"name":name,"item":url} for i,(name,url) in enumerate(crumbs,1)]})
        if not is_home and not error:
            graph.append({"@type":"Article","@id":canon+"#article","headline":title,"description":desc,"datePublished":modified,"dateModified":modified,"inLanguage":"en-US","mainEntityOfPage":canon,"image":img,"author":{"@type":"Organization","name":s.brand,"url":s.base+"/"},"publisher":{"@type":"Organization","name":s.brand,"url":s.base+"/","logo":{"@type":"ImageObject","url":s.base+"/apple-touch-icon.png"}}})
        if faq:
            graph.append({"@type":"FAQPage","@id":canon+"#faq","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":ans}} for q,ans in faq]})
        ld=f'<script type="application/ld+json">{s._json({"@context":"https://schema.org","@graph":graph})}</script>'
        top=f'<p class="disclaimer">{esc(s.disclaimer)}</p>' if s.disclaimer else ''
        disc=f'<p>{esc(s.disclaimer)}</p>' if s.disclaimer else ''
        h=f'''<!doctype html><html lang="en-US"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><meta name="description" content="{esc(desc)}">{robots}<link rel="canonical" href="{esc(canon)}"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="/apple-touch-icon.png"><meta property="og:type" content="{og_type}"><meta property="og:site_name" content="{esc(s.brand)}"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{esc(canon)}"><meta property="og:image" content="{esc(img)}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="{esc(s.brand)}"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(desc)}"><meta name="twitter:image" content="{esc(img)}"><meta name="twitter:image:alt" content="{esc(s.brand)}">{verify}{ld}<style>{s.css}</style><script defer src="/_vercel/insights/script.js"></script></head><body>
<header><a class="brand" href="/">{esc(s.brand)}</a><nav>{nav}</nav></header>
<div class="unofficial">Unofficial and independent guide. Not a government website.</div>
{top}
<main><p class="checked">Last checked: {shown}</p>
{body}
</main><footer>{s.footer} {disc}<p><a href="/disclaimer/">Disclaimer</a></p>{s._related()}<p>Last checked: {shown}.</p></footer></body></html>'''
        for bad in ('\u2014','\u2013','&mdash;','&ndash;'): assert bad not in h,(path,bad)
        p=os.path.join(s.out,path); os.makedirs(os.path.dirname(p),exist_ok=True); open(p,'w',encoding='utf-8').write(h)
        if sitemap: s.pages.append((path, modified))
    def finish(s):
        bots=['GPTBot','OAI-SearchBot','ChatGPT-User','PerplexityBot','Bingbot','Googlebot','ClaudeBot','*']
        open(os.path.join(s.out,'robots.txt'),'w',encoding='utf-8').write(''.join(f'User-agent: {b}\nAllow: /\n\n' for b in bots)+f'Sitemap: {s.base}/sitemap.xml\n')
        open(os.path.join(s.out,'sitemap.xml'),'w',encoding='utf-8').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+''.join(f'<url><loc>{s.base}/{p.replace("index.html","")}</loc><lastmod>{mod}</lastmod></url>\n' for p,mod in sorted(s.pages))+'</urlset>\n')
        if s.warns: print(f'{s.warns} SEO length warnings',file=sys.stderr)
CSS='''body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;color:#1a1a1a;line-height:1.55;background:#fafaf7}header{background:#123b5c;color:#fff;padding:.7rem 1rem;display:flex;flex-wrap:wrap;gap:.6rem 1.2rem;align-items:center}header a{color:#fff;text-decoration:none}.brand{font-weight:700}nav{display:flex;flex-wrap:wrap;gap:.3rem .9rem;font-size:.95rem}nav a:hover{text-decoration:underline}.unofficial{background:#fff4d6;border-bottom:1px solid #e6cf8a;padding:.4rem 1rem;font-size:.9rem}.disclaimer{background:#f4f1ea;border-bottom:1px solid #e0d8c8;padding:.45rem 1rem;font-size:.88rem;margin:0}main{max-width:1100px;margin:0 auto;padding:1rem}h1{font-size:1.7rem;line-height:1.25}h2{margin-top:1.8rem}.checked{display:inline-block;background:#e6f2ea;border:1px solid #a9d1b5;border-radius:4px;padding:.15rem .5rem;font-size:.9rem}.card{background:#fff;border:1px solid #ddd;border-radius:6px;padding:.8rem 1rem;margin:.8rem 0}.warn{border-left:6px solid #c0392b;background:#fdeeee}.note{border-left:6px solid #d68910;background:#fff8ec}.conf{border-left:6px solid #8e44ad;background:#f6effa}.wrap{overflow-x:auto}table{border-collapse:collapse;width:100%;background:#fff;font-size:.93rem}th,td{border:1px solid #ddd;padding:.45rem;vertical-align:top;text-align:left}th{background:#eef3f7}.src{font-size:.85rem;color:#555}.tag{display:inline-block;font-size:.78rem;padding:0 .35rem;border-radius:3px;background:#eee;margin-right:.2rem}.tag.ok{background:#d8f0de}.tag.no{background:#f8d7d7}.tag.mix{background:#fdebc8}footer{max-width:1100px;margin:2rem auto;padding:1rem;font-size:.88rem;color:#444;border-top:1px solid #ddd}footer p{margin:.45rem 0}a{color:#0b5394}input#q{width:100%;max-width:420px;padding:.45rem;margin:.5rem 0;font-size:1rem}'''
