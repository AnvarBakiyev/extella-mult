"""Packs the scene language for installation on other devices: handler code, catalog, the 3d models it references
(blend + gltf with their textures, no FBX duplicates), fonts and every licence file. -> dist/extella-mult-<ver>.tar.gz"""
import json, os, sys, tarfile, glob, hashlib
KIND = sys.argv[1] if len(sys.argv) > 1 else '3d'
ROOT = os.path.dirname(os.path.abspath(__file__))
VER = '2'
cat = json.load(open(os.path.join(ROOT, 'assets/lib3d/catalog.json')))
files = set()
for f in glob.glob(os.path.join(ROOT, 'handler/*.py')):
    files.add(f)
files |= {os.path.join(ROOT, p) for p in ('assets/fonts/Caveat.ttf', 'assets/fonts/OFL.txt')}
if KIND == '2d':
    cat = {}
else:
    files |= {os.path.join(ROOT, p) for p in ('assets/lib3d/catalog.json', 'assets/build_catalog.py')}
for e in cat.values():
    f = os.path.join(ROOT, 'assets', e['file'])
    files.add(f)
    if e['fmt'] == 'gltf' and f.endswith('.gltf'):  # the .bin and textures next to it (a .glb is self-contained)
        d = os.path.dirname(f)
        g = json.load(open(f))
        for b in g.get('buffers', []) + g.get('images', []):
            if 'uri' in b and not b['uri'].startswith('data:'):
                files.add(os.path.normpath(os.path.join(d, b['uri'])))
packs = {os.path.join(ROOT, 'assets', *e['file'].split('/')[:2]) for e in cat.values() if e['fmt'] == 'blend'}
for pr in packs:
    for f in glob.glob(pr + '/**/Textures/*', recursive=True) + glob.glob(pr + '/**/*.png', recursive=True):
        if f.lower().endswith(('.png', '.jpg', '.jpeg')) and 'preview' not in f.lower():
            files.add(f)
for lic in glob.glob(os.path.join(ROOT, 'assets/**/*icen*'), recursive=True):
    if KIND == '3d':
        files.add(lic)
missing = [f for f in files if not os.path.exists(f)]
assert not missing, missing[:5]
os.makedirs(os.path.join(ROOT, 'dist'), exist_ok=True)
out = os.path.join(ROOT, 'dist', f'extella-mult-{KIND}.tar.gz')
with tarfile.open(out, 'w:gz') as t:
    for f in sorted(files):
        t.add(f, arcname=os.path.relpath(f, ROOT))
sha = hashlib.sha256(open(out, 'rb').read()).hexdigest()
print(out, round(os.path.getsize(out) / 1e6, 1), 'MB', len(files), 'files sha256', sha)
