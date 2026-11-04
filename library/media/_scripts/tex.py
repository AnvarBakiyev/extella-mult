import json, os, sys, io, zipfile, urllib.request, hashlib
from PIL import Image
OUT = sys.argv[1]; TMP = sys.argv[2]
os.makedirs(OUT, exist_ok=True); os.makedirs(TMP, exist_ok=True)
import subprocess
def get(url):
    return subprocess.run(["curl","-sSfL","-m","300","--retry","3",url],check=True,capture_output=True).stdout
AC = [  # (id, category, what)
 ("Fabric034","felt","grey/white felt"),("Fabric085","wool","orange-red wool"),("Fabric068","wool","orange wool"),
 ("Fabric019","wool","white woven wool"),("Fabric031","wool","grey large-weave wool"),("Fabric032","wool","white wool cloth"),
 ("Fabric018","wool","lime woven wool"),("Fabric016","wool","red woven wool"),("Fabric017","wool","cyan woven wool"),
 ("Fabric084","fleece","blue microfiber/fur"),("Fabric061","fabric","rough fabric"),("Fabric045","fabric","grey rough rug fabric"),
 ("Fabric030","fabric","grey cloth"),("Fabric001","linen","old white cloth"),("Fabric077","denim","white jeans"),
 ("Fabric003","denim","new blue jeans"),("Fabric054","fabric","red tartan"),("Fabric080","fabric","red plaid cotton"),
 ("Fabric011","burlap","light brown weave"),("Fabric013","burlap","brown weave"),
 ("Carpet016","carpet","beige wool carpet"),("Carpet012","carpet","carpet"),("Carpet001","carpet","grey rug"),
 ("Carpet014","carpet","white woven carpet"),("Carpet015","carpet","red carpet"),
 ("Cork001","cork","cork"),("Cork002","cork","cork"),("Cork003","cork","cork"),("Cork004","cork","cork"),
 ("Cardboard001","cardboard","cardboard"),("Cardboard002","cardboard","cardboard"),("Cardboard003","cardboard","cardboard"),("Cardboard004","cardboard","cardboard"),
 ("Paper001","paper","paper"),("Paper002","paper","paper"),("Paper003","paper","paper"),("Paper004","paper","paper"),("Paper005","paper","paper/cardboard"),("Paper006","paper","paper"),
 ("Wood049","wood","wood"),("Wood051","wood","wood"),("Wood066","wood","wood"),("Wood092","wood","wood"),
 ("Wood087","plywood","plywood"),("Wood088","plywood","plywood"),("Wood089","plywood","plywood"),("Chipboard001","plywood","chipboard"),
 ("Plaster001","plaster","plaster"),("Plaster002","plaster","plaster"),("Plaster003","plaster","plaster"),("PaintedPlaster017","plaster","painted plaster"),
 ("Rock030","stone","rock"),("Rock035","stone","rock"),("Rock051","stone","rock"),("Wicker004","fabric","wicker"),
]
PH = [
 ("caban","wool","orange wool fleece coat cloth"),("knitted_fleece","knit","knitted wool fleece"),("wool_boucle","knit","wool boucle knit"),
 ("poly_wool_herringbone","wool","herringbone wool"),("jersey_melange","knit","melange jersey knit"),("jogging_melange","fleece","jogging fleece"),
 ("polar_fleece","fleece","polar fleece"),("terry_cloth","knit","terry cloth"),("hessian_230","burlap","hessian/burlap 230"),
 ("hessian_380","burlap","hessian/burlap 380"),("rough_linen","linen","rough linen"),("denim_fabric","denim","denim"),
 ("denim_fabric_03","denim","light denim"),("denim_fabric_05","denim","dark grey denim"),("ribbed_corduroy","corduroy","ribbed corduroy"),
 ("velour_velvet","velvet","velour velvet"),("curly_teddy_natural","fleece","teddy plush"),("cotton_jersey","knit","cotton jersey"),
 ("waffle_pique_cotton","fabric","waffle pique cotton"),("gingham_check","fabric","gingham check"),("book_pattern","fabric","book-cover cloth"),
 ("dirty_carpet","carpet","dirty carpet"),("plywood","plywood","plywood"),("scuba_suede","velvet","scuba suede"),
 ("clay_plaster","plaster","clay plaster wall"),("beige_wall_001","plaster","beige painted plaster"),
]
idx = []
def save(img, name):
    img = img.convert("RGB"); p = os.path.join(OUT, name); img.save(p, "JPEG", quality=86, optimize=True); return img.size
for aid, cat, what in AC:
    name = f"{cat}_acg_{aid}_2K.jpg"
    if os.path.exists(os.path.join(OUT,name)): idx.append((name,what,f"https://ambientcg.com/view?id={aid}","CC0 1.0",aid)); continue
    try:
        z = zipfile.ZipFile(io.BytesIO(get(f"https://ambientcg.com/get?file={aid}_2K-JPG.zip")))
        cands = [n for n in z.namelist() if "_Color" in n and n.lower().endswith(".jpg")]
        img = Image.open(io.BytesIO(z.read(cands[0]))); sz = save(img, name)
        idx.append((name, what, f"https://ambientcg.com/view?id={aid}", "CC0 1.0", aid)); print("ok", name, sz, flush=True)
    except Exception as e: print("FAIL", aid, e, flush=True)
for aid, cat, what in PH:
    name = f"{cat}_ph_{aid}_2k.jpg"
    if os.path.exists(os.path.join(OUT,name)): idx.append((name,what,f"https://polyhaven.com/a/{aid}","CC0 1.0",aid)); continue
    try:
        f = json.loads(get(f"https://api.polyhaven.com/files/{aid}"))
        url = f["Diffuse"]["2k"]["jpg"]["url"]
        img = Image.open(io.BytesIO(get(url))); sz = save(img, name)
        idx.append((name, what, f"https://polyhaven.com/a/{aid}", "CC0 1.0", aid)); print("ok", name, sz, flush=True)
    except Exception as e: print("FAIL", aid, e, flush=True)
json.dump(idx, open(os.path.join(TMP, "tex_index.json"), "w"), indent=1)
