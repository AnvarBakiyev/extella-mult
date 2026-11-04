import numpy as np, os, sys, json
from PIL import Image, ImageDraw, ImageFilter
OUT=sys.argv[1]; META=sys.argv[2]; os.makedirs(OUT,exist_ok=True)
W,H=1920,1080; rows=[]
def smooth(rng,scale,w=W,h=H):
    sw,sh=max(2,w//scale),max(2,h//scale)
    a=rng.random((sh,sw)).astype(np.float32)
    im=Image.fromarray((a*255).astype(np.uint8)).resize((w,h),Image.BICUBIC)
    return np.asarray(im).astype(np.float32)/255
def save(rgba,name,what):
    Image.fromarray(np.clip(rgba,0,255).astype(np.uint8),"RGBA").save(os.path.join(OUT,name),optimize=True)
    rows.append(dict(file=name,what=what,source="generated procedurally (numpy/Pillow) by scripts in this branch — no external source",licence="CC0 1.0 (own work, dedicated to public domain)",author="generated"))
def gray_alpha(lum,alpha):
    l=np.clip(lum*255,0,255); return np.dstack([l,l,l,np.clip(alpha*255,0,255)])
# 1) film grain loops: 2 sizes x 8 frames, luminance noise around mid-grey; use with 'overlay'/'soft light' blend or as-is at low opacity
for kind,blur,amp,levels in (("fine",0.0,0.55,24),("coarse",0.9,0.75,24)):
    for i in range(8):
        rng=np.random.default_rng(1000+i+(50 if kind=="coarse" else 0))
        n=rng.normal(0,1,(H,W)).astype(np.float32)
        if blur:
            n=np.asarray(Image.fromarray(((n*40)+128).clip(0,255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur))).astype(np.float32); n=(n-128)/40
            n/=n.std()
        l=0.5+n*0.18*amp; l=np.round(l*levels)/levels
        save(gray_alpha(l,np.full((H,W),0.35)),f"grain_{kind}_loop_f{i:02d}.png",f"film grain loop ({kind}), frame {i+1}/8, mid-grey luminance noise, alpha 0.35; cycle frames 00-07")
# 2) dust & scratches: 6 frames
for i in range(6):
    rng=np.random.default_rng(2000+i); im=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(im)
    for _ in range(rng.integers(25,60)):
        x,y=rng.integers(0,W),rng.integers(0,H); r=rng.uniform(0.8,4); c=int(rng.choice([20,235])); a=int(rng.uniform(80,200))
        d.ellipse([x-r,y-r*rng.uniform(.5,1.2),x+r,y+r],fill=(c,c,c,a))
    for _ in range(rng.integers(3,9)):  # hairs
        x,y=rng.uniform(0,W),rng.uniform(0,H); pts=[(x,y)]; ang=rng.uniform(0,6.28)
        for k in range(rng.integers(6,20)):
            ang+=rng.normal(0,.35); x+=np.cos(ang)*rng.uniform(3,9); y+=np.sin(ang)*rng.uniform(3,9); pts.append((x,y))
        c=int(rng.choice([25,230])); d.line(pts,fill=(c,c,c,int(rng.uniform(90,170))),width=1)
    for _ in range(rng.integers(0,3)):  # vertical scratches
        x=rng.uniform(0,W); y0=rng.uniform(0,H*.5); y1=y0+rng.uniform(H*.2,H)
        d.line([(x,y0),(x+rng.normal(0,6),y1)],fill=(240,240,240,int(rng.uniform(60,140))),width=1)
    im=im.filter(ImageFilter.GaussianBlur(0.6)); im.save(os.path.join(OUT,f"dust_scratches_f{i:02d}.png"),optimize=True)
    rows.append(dict(file=f"dust_scratches_f{i:02d}.png",what=f"dust specks, hairs and film scratches, frame {i+1}/6 (alternate randomly per frame)",source="generated procedurally (numpy/Pillow) — no external source",licence="CC0 1.0 (own work, dedicated to public domain)",author="generated"))
yy,xx=np.mgrid[0:H,0:W].astype(np.float32); xn=xx/W; yn=yy/H
# 3) light leaks: 6 (use 'screen' / 'add' blend)
pal=[((255,120,40),(255,210,90)),((255,60,90),(255,170,60)),((255,180,80),(255,240,180)),((200,80,255),(255,120,160)),((255,90,30),(255,40,80)),((90,170,255),(255,200,120))]
for i,(c1,c2) in enumerate(pal):
    rng=np.random.default_rng(3000+i); a=np.zeros((H,W),np.float32); col=np.zeros((H,W,3),np.float32)
    for k in range(3):
        cx,cy=rng.choice([rng.uniform(-.2,.15),rng.uniform(.85,1.2)]),rng.uniform(-.1,1.1); sx,sy=rng.uniform(.15,.45),rng.uniform(.3,.8)
        g=np.exp(-(((xn-cx)/sx)**2+((yn-cy)/sy)**2)); g*=0.6+0.4*smooth(rng,160)
        t=smooth(rng,300)[...,None]; c=np.array(c1)*(1-t)+np.array(c2)*t
        col+=c*g[...,None]; a+=g
    a=np.clip(a,0,1)*0.85; col=col/np.maximum(np.clip(a/0.85,1e-3,None),1e-3)[...,None]
    save(np.dstack([col,a*255]),f"light_leak_{i+1:02d}.png","warm film light leak from frame edge; blend with screen/add at 40-90% opacity")
# 4) bokeh: 4
for i in range(4):
    rng=np.random.default_rng(4000+i); im=Image.new("RGBA",(W,H),(0,0,0,0))
    hues=[(255,200,120),(255,160,90),(180,220,255),(255,240,200)] if i%2==0 else [(255,120,160),(140,200,255),(255,220,120),(200,160,255)]
    for _ in range(rng.integers(35,70)):
        layer=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(layer)
        r=rng.uniform(15,90); x,y=rng.uniform(0,W),rng.uniform(0,H); c=hues[rng.integers(len(hues))]
        d.ellipse([x-r,y-r,x+r,y+r],fill=c+(int(rng.uniform(25,90)),),outline=c+(int(rng.uniform(60,140)),),width=max(1,int(r*.06)))
        im=Image.alpha_composite(im,layer)
    im=im.filter(ImageFilter.GaussianBlur(2.5+i)); im.save(os.path.join(OUT,f"bokeh_{i+1:02d}.png"),optimize=True)
    rows.append(dict(file=f"bokeh_{i+1:02d}.png",what="out-of-focus bokeh discs (fairy lights / city at night); screen blend",source="generated procedurally (numpy/Pillow) — no external source",licence="CC0 1.0 (own work, dedicated to public domain)",author="generated"))
# 5) vignettes: 3
r=np.sqrt(((xn-.5)/.5)**2+((yn-.5)/.5)**2)
for name,inner,outer,maxa,what in (("vignette_soft",0.55,1.45,0.55,"soft black vignette"),("vignette_strong",0.35,1.25,0.85,"strong black vignette (old TV / documentary)"),("vignette_oval_iris",0.6,0.95,1.0,"oval iris-out mask, nearly opaque edges")):
    t=np.clip((r-inner)/(outer-inner),0,1); t=t*t*(3-2*t)
    save(np.dstack([np.zeros((H,W,3)),t*maxa*255]),name+".png",what+"; normal blend")
# 6) paper fibre: 3
for i in range(3):
    rng=np.random.default_rng(6000+i)
    base=0.5+0.10*(smooth(rng,4)-.5)+0.12*(smooth(rng,40)-.5)+0.08*(smooth(rng,200)-.5)
    im=Image.fromarray(np.clip(base*255,0,255).astype(np.uint8)).convert("RGBA"); d=ImageDraw.Draw(im)
    for _ in range(1500):
        x,y=rng.uniform(0,W),rng.uniform(0,H); ang=rng.uniform(0,6.28); L=rng.uniform(4,28); c=int(rng.choice([95,165]))
        d.line([(x,y),(x+np.cos(ang)*L,y+np.sin(ang)*L)],fill=(c,c,c,255),width=1)
    a=np.asarray(im.filter(ImageFilter.GaussianBlur(0.5))).astype(np.float32)
    l=a[...,0]/255; alpha=np.full((H,W),[0.30,0.45,0.6][i])
    save(gray_alpha(l,alpha),f"paper_fibre_{i+1:02d}.png","paper fibre and grain, mid-grey luminance; overlay/soft-light blend (alpha %.2f)"%alpha[0,0])
# 7) fabric fibre / lint: 3
for i in range(3):
    rng=np.random.default_rng(7000+i); im=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(im)
    for _ in range([2500,5000,9000][i]):
        x,y=rng.uniform(0,W),rng.uniform(0,H); ang=rng.uniform(0,6.28); pts=[(x,y)]
        for k in range(rng.integers(3,9)):
            ang+=rng.normal(0,.5); x+=np.cos(ang)*rng.uniform(1.5,4); y+=np.sin(ang)*rng.uniform(1.5,4); pts.append((x,y))
        c=int(rng.uniform(200,255)) if rng.random()<.6 else int(rng.uniform(20,70))
        d.line(pts,fill=(c,c,c,int(rng.uniform(30,110))),width=1)
    im=im.filter(ImageFilter.GaussianBlur(0.4)); im.save(os.path.join(OUT,f"fabric_fibre_{i+1:02d}.png"),optimize=True)
    rows.append(dict(file=f"fabric_fibre_{i+1:02d}.png",what=["light","medium","heavy"][i]+" stray felt/wool fibres and lint (fuzz over puppets); normal blend",source="generated procedurally (numpy/Pillow) — no external source",licence="CC0 1.0 (own work, dedicated to public domain)",author="generated"))
json.dump(rows,open(META,"w"),indent=1); print(len(rows))
