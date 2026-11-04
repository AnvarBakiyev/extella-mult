import json, os, sys, glob
S=sys.argv[1]; M=sys.argv[2]
order=["textures","sfx","music","fonts","overlays"]
desc={"textures":"Seamless colour (albedo) maps, JPG 2K, re-encoded at q86. Only the Color/Diffuse map was kept from each PBR set.",
"sfx":"Short sound effects, OGG Vorbis 44.1 kHz, leading/trailing silence trimmed, peak-normalised to -1 dBFS.",
"music":"Short loops, jingles and stingers, OGG Vorbis 44.1 kHz, peak-normalised to -1 dBFS.",
"fonts":"OFL fonts with Cyrillic, each family folder carries its OFL.txt.",
"overlays":"1920x1080 PNG/RGBA overlays (and grain loop frames) for compositing over rendered frames."}
def esc(s): return str(s).replace("|","\\|").replace("\n"," ")
out=["# puppet-oss media — INDEX","","Per-folder list of every file: what it is, where it came from, licence.","See ATTRIBUTION.md for credits and README.md for usage.",""]
for f in order:
    p=os.path.join(S,"meta",f+".json")
    if not os.path.exists(p): continue
    rows=json.load(open(p))
    out+=[f"## {f}/ ({len(rows)} files)","",desc[f],"","| file | what | source | licence |","|---|---|---|---|"]
    for r in rows: out.append(f"| `{esc(r['file'])}` | {esc(r['what'])} | {esc(r['source'])} | {esc(r['licence'])} |")
    out.append("")
open(os.path.join(M,"INDEX.md"),"w").write("\n".join(out))
# attribution
a=["# ATTRIBUTION","","Everything here is CC0 / public domain unless listed otherwise below. CC0 needs no credit, but we credit the creators anyway (grouped by source).",""]
for f in order:
    p=os.path.join(S,"meta",f+".json")
    if not os.path.exists(p): continue
    rows=json.load(open(p)); groups={}
    for r in rows: groups.setdefault((r.get('author',''),r['source'],r['licence']),[]).append(r['file'])
    a+=[f"## {f}/",""]
    for (au,src,lic),files in groups.items():
        fl=", ".join(f"`{x}`" for x in files[:6])+(f" … (+{len(files)-6})" if len(files)>6 else "")
        a.append(f"- {esc(au) or 'unknown'} — {src} — **{lic}** — {fl}")
    a.append("")
open(os.path.join(M,"ATTRIBUTION.md"),"w").write("\n".join(a))
