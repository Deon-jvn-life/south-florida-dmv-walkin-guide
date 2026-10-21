"""Shared helpers: page shell, robots.txt, sitemap.xml, checks. Copied per site so each folder is self-contained."""
import os,html as H,shutil,re
D="21 Oct 2026"
def esc(s): return H.escape(s,quote=True)
def a(url,text='source'): return f'<a href="{esc(url)}" rel="noopener">{text}</a>'
class Site:
    def __init__(s,root,base,brand,nav,footer,css):
        s.out=os.path.join(root,'site'); s.base=base.rstrip('/'); s.brand=brand; s.nav=nav; s.footer=footer; s.css=css; s.pages=[]
        if os.path.exists(s.out): shutil.rmtree(s.out)
        os.makedirs(s.out)
    def page(s,path,title,desc,body):
        r='../'*path.count('/')
        nav=''.join(f'<a href="{r}{p}">{t}</a>' for p,t in s.nav)
        canon=s.base+'/'+path.replace('index.html','')
        h=f'''<!doctype html><html lang="en-US"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{canon}"><style>{s.css}</style><script defer src="/_vercel/insights/script.js"></script></head><body>
<header><a class="brand" href="{r}index.html">{esc(s.brand)}</a><nav>{nav}</nav></header>
<div class="unofficial">Unofficial and independent guide. Not a government website.</div>
<main><p class="checked">Last checked: {D}</p>
{body}
</main><footer>{s.footer} <p>Last checked: {D}.</p></footer></body></html>'''
        for bad in ('\u2014','\u2013','&mdash;','&ndash;'): assert bad not in h,(path,bad)
        p=os.path.join(s.out,path); os.makedirs(os.path.dirname(p),exist_ok=True); open(p,'w').write(h); s.pages.append(path)
    def finish(s):
        bots=['GPTBot','OAI-SearchBot','ChatGPT-User','PerplexityBot','Bingbot','Googlebot','ClaudeBot','*']
        open(os.path.join(s.out,'robots.txt'),'w').write(''.join(f'User-agent: {b}\nAllow: /\n\n' for b in bots)+f'Sitemap: {s.base}/sitemap.xml\n')
        open(os.path.join(s.out,'sitemap.xml'),'w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+''.join(f'<url><loc>{s.base}/{p.replace("index.html","")}</loc><lastmod>2026-10-21</lastmod></url>\n' for p in sorted(s.pages))+'</urlset>\n')
CSS='''body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;color:#1a1a1a;line-height:1.55;background:#fafaf7}header{background:#123b5c;color:#fff;padding:.7rem 1rem;display:flex;flex-wrap:wrap;gap:.6rem 1.2rem;align-items:center}header a{color:#fff;text-decoration:none}.brand{font-weight:700}nav{display:flex;flex-wrap:wrap;gap:.3rem .9rem;font-size:.95rem}nav a:hover{text-decoration:underline}.unofficial{background:#fff4d6;border-bottom:1px solid #e6cf8a;padding:.4rem 1rem;font-size:.9rem}main{max-width:1100px;margin:0 auto;padding:1rem}h1{font-size:1.7rem;line-height:1.25}h2{margin-top:1.8rem}.checked{display:inline-block;background:#e6f2ea;border:1px solid #a9d1b5;border-radius:4px;padding:.15rem .5rem;font-size:.9rem}.card{background:#fff;border:1px solid #ddd;border-radius:6px;padding:.8rem 1rem;margin:.8rem 0}.warn{border-left:6px solid #c0392b;background:#fdeeee}.note{border-left:6px solid #d68910;background:#fff8ec}.conf{border-left:6px solid #8e44ad;background:#f6effa}.wrap{overflow-x:auto}table{border-collapse:collapse;width:100%;background:#fff;font-size:.93rem}th,td{border:1px solid #ddd;padding:.45rem;vertical-align:top;text-align:left}th{background:#eef3f7}.src{font-size:.85rem;color:#555}.tag{display:inline-block;font-size:.78rem;padding:0 .35rem;border-radius:3px;background:#eee;margin-right:.2rem}.tag.ok{background:#d8f0de}.tag.no{background:#f8d7d7}.tag.mix{background:#fdebc8}footer{max-width:1100px;margin:2rem auto;padding:1rem;font-size:.88rem;color:#444;border-top:1px solid #ddd}a{color:#0b5394}input#q{width:100%;max-width:420px;padding:.45rem;margin:.5rem 0;font-size:1rem}'''
