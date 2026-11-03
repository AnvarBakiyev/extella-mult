# Scans CC0 3D packs and writes assets/lib3d/catalog.json: name -> file, kind (actor|prop), actions, pack
import bpy, os, re, json, glob
Q = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'q')
FARM = os.path.join(os.path.dirname(Q), 'quaternius_farm')
cat = {}
def snake(s):
    s = re.sub(r'(?<=[a-z0-9])(?=[A-Z])', '_', os.path.splitext(os.path.basename(s))[0])
    return re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')
def act_name(a):
    a = a.split('|')[-1]
    a = re.sub(r'[^a-z0-9]+', '_', a.lower()).strip('_')
    return ALIAS.get(a, a)
ALIAS = {'walking': 'walk', 'flying': 'fly', 'running': 'run', 'recievehit': 'hit', 'hitrecieve': 'hit', 'hitrecieve_1': 'hit', 'hitrecieve_2': 'hit2', 'sitdown': 'sit', 'standup': 'stand_up', 'attack2': 'attack2'}
for f in sorted(glob.glob(FARM + '/**/*.blend', recursive=True)) + sorted(glob.glob(Q + '/**/*.blend', recursive=True)):
    pack = 'farm' if f.startswith(FARM) else os.path.relpath(f, Q).split(os.sep)[0]
    n = snake(f)
    if n in ('streets_all', 'base_character'): continue
    if n in cat: n = n + ('_costume' if pack == 'people' else '_' + pack)
    with bpy.data.libraries.load(f) as (src, _):
        amap = {}
        for a in src.actions:
            k = act_name(a)
            base = snake(f)
            if k.startswith(base + '_') and len(k) > len(base) + 1:
                k = ALIAS.get(k[len(base) + 1:], k[len(base) + 1:])
            amap.setdefault(k, a)
        acts = sorted(amap)
    cat[n] = dict(file=os.path.relpath(f, os.path.dirname(Q)), fmt='blend', pack=pack,
                  kind='actor' if acts else 'prop', actions=acts, action_map=amap)
for f in sorted(glob.glob(Q + '/nature/**/*.gltf', recursive=True) + glob.glob(Q + '/**/*.glb', recursive=True)):
    n = snake(f)
    pack = os.path.relpath(f, Q).split(os.sep)[0]
    if n in cat:
        continue
    cat[n] = dict(file=os.path.relpath(f, os.path.dirname(Q)), fmt='gltf', pack=pack, kind='prop', actions=[])
out = os.path.join(os.path.dirname(Q), 'lib3d', 'catalog.json')
json.dump(cat, open(out, 'w'), indent=1)
print('CATALOG', len(cat), sum(v['kind'] == 'actor' for v in cat.values()))
