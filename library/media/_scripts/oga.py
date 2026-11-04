# usage: oga.py OUTDIR typeTid kw1 kw2 ...   (13=Sound Effect, 12=Music)
import re, sys, os, json, subprocess, html, time
OUT=sys.argv[1]; TID=sys.argv[2]; KWS=sys.argv[3:]
os.makedirs(OUT,exist_ok=True)
def get(url):
    r=subprocess.run(["curl","-sSL","-m","120","--retry","2",url],capture_output=True); return r.stdout.decode("utf-8","replace")
def search(k, n=8):
    u=f"https://opengameart.org/art-search-advanced?keys={k.replace(' ','+')}&field_art_type_tid%5B%5D={TID}&field_art_license_tid%5B%5D=4&sort_by=count&sort_order=DESC&items_per_page=24"
    h=get(u); slugs=[]
    for m in re.findall(r'<a href="/content/([^"]+)">',h):
        if m not in slugs and m not in ("faq",) and "art-challenge" not in m: slugs.append(m)
    return slugs[:n]
def page(slug):
    h=get("https://opengameart.org/content/"+slug)
    t=re.search(r'<h1[^>]*>(.*?)</h1>',h,re.S) or re.search(r'<title>(.*?)\|',h)
    a=re.search(r'field-name-author-submitter.*?<a href="/users/([^"]+)">(.*?)</a>',h,re.S)
    lic=re.findall(r"<div class='license-name'>(.*?)</div>",h)
    files=re.findall(r'<a href="(https://opengameart.org/sites/default/files/[^"]+)" type="([^";]+)(?:; length=(\d+))?"',h)
    cn=re.search(r'field-name-field-copyright-notice.*?<div class="field-item even">(.*?)</div>',h,re.S)
    return dict(slug=slug,title=html.unescape(re.sub('<[^>]+>','',t.group(1)).strip()) if t else slug,
        author=html.unescape(a.group(2)) if a else "?",author_url=("https://opengameart.org/users/"+a.group(1)) if a else "",
        licenses=lic,files=[(u,ty,int(l or 0)) for u,ty,l in files],notice=html.unescape(re.sub('<[^>]+>','',cn.group(1))).strip() if cn else "",
        url="https://opengameart.org/content/"+slug)
seen=set(json.load(open(OUT+"/_seen.json"))) if os.path.exists(OUT+"/_seen.json") else set()
for k in KWS:
    for slug in ([k[5:]] if k.startswith('slug:') else search(k,12)):
        if slug in seen: continue
        seen.add(slug); p=page(slug); p["kw"]=k
        if "CC0" not in p["licenses"]: print("skip-lic",slug,p["licenses"]); continue
        d=os.path.join(OUT,slug); os.makedirs(d,exist_ok=True); tot=0
        for u,ty,l in p["files"]:
            if not re.search(r'\.(zip|ogg|wav|mp3|flac|7z|rar)$',u,re.I): continue
            if l>60e6 or tot>120e6: print("skip-size",u,l); continue
            fn=os.path.join(d,os.path.basename(u))
            if not os.path.exists(fn): subprocess.run(["curl","-sSfL","-m","600","-o",fn,u])
            tot+=l
        json.dump(p,open(d+"/meta.json","w"),indent=1); print("got",k,slug,p["author"],len(p["files"]),flush=True)
        time.sleep(0.5)
    json.dump(sorted(seen),open(OUT+"/_seen.json","w"))
