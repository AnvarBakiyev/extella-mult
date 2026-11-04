import sys, os, re, subprocess, glob
q=sys.argv[2]
def peak(f):
    r=subprocess.run(["ffmpeg","-hide_banner","-i",f,"-af","volumedetect","-f","null","-"],capture_output=True,text=True).stderr
    return float(re.search(r"max_volume: (-?[\d.]+) dB",r).group(1))
bad=0
for f in sorted(glob.glob(os.path.join(sys.argv[1],"*.ogg"))):
    p=peak(f)
    if p>-1.0 or p<-1.6:
        g=-1.15-p; tmp=f+".t.ogg"
        subprocess.run(["ffmpeg","-v","error","-y","-i",f,"-af",f"volume={g}dB","-c:a","libvorbis","-q:a",q,"-ar","44100",tmp],check=True); os.replace(tmp,f)
        p2=peak(f); bad+=1; print(os.path.basename(f),p,"->",p2,flush=True)
print("fixed",bad)
