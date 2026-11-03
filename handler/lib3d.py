"""3D style: vocabulary from the CC0 model catalog (assets/lib3d/catalog.json) and shot rendering in Blender."""
import json
import os
import subprocess
import tempfile

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets')
CATALOG = json.load(open(os.path.join(ASSETS, 'lib3d', 'catalog.json'))) if os.path.exists(os.path.join(ASSETS, 'lib3d', 'catalog.json')) else {}
from .config import blender as _blender
BLENDER = _blender()
SETS = ('day', 'dawn', 'sunset', 'night')
GROUNDS = ('meadow', 'road', 'sand', 'snow')
ELEMENTS3D = set(SETS) | set(GROUNDS) | {n for n, e in CATALOG.items() if e['kind'] == 'prop'}
ACTORS3D = {n: e['actions'] for n, e in CATALOG.items() if e['kind'] == 'actor'}
# default height in metres when the program gives no size=
HEIGHT = {'farm': 1.3, 'animals2': 0.7, 'people': 1.8}
HEIGHT_BY_NAME = {'cat': 0.45, 'eagle': 0.9, 'horse': 1.9, 'zebra': 1.8, 'llama': 1.8, 'pig': 0.8, 'pug': 0.5, 'sheep': 1.0}


def _x(pos, default=0.5):
    from .actors import POSITIONS
    if pos is None:
        return default
    return pos[0] if isinstance(pos, tuple) else POSITIONS[pos][0]


def shot_plan(prog, sc, out_dir, first, size):
    actors = []
    for st in prog.stmts:
        if st.kind != 'actor' or st.scene is not sc:
            continue
        name = st.words[0]
        if st.pos is not None:
            x0 = x1 = _x(st.pos)
        else:
            x0, x1 = _x(st.frm), _x(st.to)
        size_m = st.params.get('size', HEIGHT_BY_NAME.get(name, HEIGHT.get(CATALOG[name]['pack'], 1.2)))
        actors.append(dict(name=name, action=st.words[1], t0=st.t0, t1=st.t1, x0=x0, x1=x1,
                           z=float(st.params.get('z', 0.0)), size=float(size_m), lift=float(st.params.get('lift', 0.0)),
                           facing=(1 if str(st.params.get('facing')) == 'front' else int(st.params['facing'])) if 'facing' in st.params else 0,
                           speed=float(st.params.get('speed', 1.0)), turn=float(st.params.get('turn', 0)) - (90 if str(st.params.get('facing')) == 'front' else 0)))
    camera = []
    for st in prog.stmts:
        if st.kind == 'camera' and st.scene is sc and st.words[0] in ('pan', 'zoom'):
            c = dict(move=st.words[0], t0=st.t0, t1=st.t1, amount=st.params.get('amount', 0.12))
            if st.words[0] == 'pan':
                c['dir'] = st.words[1]
            else:
                c['range'] = list(st.params['range'])
            camera.append(c)
    return dict(lib=ASSETS, catalog={n: CATALOG[n] for n in {a['name'] for a in actors} | {e for e, _ in sc.elements if e in CATALOG}},
                elements=[[n, p] for n, p in sc.elements], actors=actors, camera=camera,
                t0=sc.t0, t1=sc.t1, fps=prog.fps, look='toon' if prog.style == 'toon' else 'real', size=list(size), out=out_dir, first=first)


def render_backgrounds(prog, out_dir, size):
    """Render every shot in Blender into out_dir/NNNNN.png, numbered over the whole film."""
    os.makedirs(out_dir, exist_ok=True)
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'blender_scene.py')
    for sc in prog.scenes:
        first = int(round(sc.t0 * prog.fps))
        plan = shot_plan(prog, sc, out_dir, first, size)
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f:
            json.dump(plan, f)
        r = subprocess.run([BLENDER, '-b', '--factory-startup', '--disable-autoexec', '--python', script, '--', f.name],
                           capture_output=True, text=True)
        os.unlink(f.name)
        if 'SHOT_DONE' not in r.stdout:
            raise RuntimeError('Blender failed on scene %g-%gs: %s' % (sc.t0, sc.t1, (r.stdout + r.stderr)[-1500:]))
        print(f'  shot {sc.t0:g}-{sc.t1:g}s rendered', flush=True)
