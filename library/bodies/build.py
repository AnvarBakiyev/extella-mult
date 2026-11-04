"""Render the whole cast: chars/<name>/{base,mouth_<v>,blink,expr_<e>}.png + char.json.

    python3 build.py              # everything, in parallel
    python3 build.py aigul timur  # only these
"""
import json
import os
import sys
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import charlib as L  # noqa: E402
from characters import CAST  # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))


def palette(c):
    p = {'skin' if c.s['kind'] == 'person' else 'fur': c.skin, 'outfit': c.o1, 'outfit2': c.o2, 'accent': c.o3,
         'iris': c.iris, 'lip': c.lip}
    if c.skin2:
        p['fur2'] = c.skin2
    if c.s['hair'] not in ('bald', 'none'):
        p['hair'] = c.hair_col
    return p


def build(spec):
    c, out, _ = L.render_all(spec)
    d = os.path.join(ROOT, 'chars', spec['name'])
    os.makedirs(d, exist_ok=True)
    for k, im in out.items():
        im.save(os.path.join(d, k + '.png'), optimize=True)
    parts = {k: c.s.get(k) for k in ('kit', 'head', 'hair', 'eyes', 'brow', 'nose', 'outfit', 'facial', 'age', 'build')
             if c.s.get(k) is not None}
    parts['accessories'] = [a if isinstance(a, str) else list(a) for a in c.s['acc']]
    meta = {
        'name': spec['name'], 'kind': c.s['kind'] if c.s['kind'] != 'animal' else 'animal:' + c.kit,
        'about': spec['about'], 'default_voice': spec['voice'], 'palette': palette(c), 'parts': parts,
        'size': [L.OUT, L.OUT],
        'frames': {'base': 'base.png', 'visemes': {v: 'mouth_%s.png' % v for v in L.VISEMES}, 'blink': 'blink.png',
                   'expressions': {e: 'expr_%s.png' % e for e in L.EXPRESSIONS}},
        'layering': 'base.png is the full neutral frame. Every other png is a full-size, pixel-aligned overlay of only '
                    'the changed face region (mouth region for visemes, eye region for blink, both for expressions): '
                    'frame = base, then expr_<e>, then mouth_<v>, then blink, each alpha-composited.',
        'anchors': {'mouth': [0.5, round(c.mouth_y, 4)], 'eyes': [[round(x, 4), round(y, 4)] for x, y, _ in c.eye_centers()],
                    'head_center': [0.5, round(c.G.cy, 4)], 'split_y': round(c.split_y, 4)},
    }
    with open(os.path.join(d, 'char.json'), 'w') as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    return spec['name']


if __name__ == '__main__':
    want = set(sys.argv[1:])
    todo = [s for s in CAST if not want or s['name'] in want]
    with Pool(int(os.environ.get('JOBS', os.cpu_count() or 2))) as p:
        for i, n in enumerate(p.imap_unordered(build, todo)):
            print(i + 1, len(todo), n, flush=True)
