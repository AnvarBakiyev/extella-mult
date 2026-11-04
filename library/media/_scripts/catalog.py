import os, json, subprocess, sys
root=sys.argv[1]; out=[]
for slug in sorted(os.listdir(root)):
    d=os.path.join(root,slug)
    if not os.path.isdir(d) or not os.path.exists(d+"/meta.json"): continue
    m=json.load(open(d+"/meta.json"))
    for dp,_,fs in os.walk(d):
        if "__MACOSX" in dp: continue
        for f in fs:
            if not f.lower().endswith((".ogg",".wav",".mp3",".flac")) or f.startswith("._"): continue
            p=os.path.join(dp,f)
            r=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",p],capture_output=True,text=True)
            try: dur=float(r.stdout.strip())
            except: dur=-1
            out.append(dict(slug=slug,kw=m["kw"],author=m["author"],path=os.path.relpath(p,root),dur=round(dur,2)))
json.dump(out,open(sys.argv[2],"w"),indent=0); print(len(out))
