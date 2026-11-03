"""Library actors: every folder assets/sprites/<actor>/<action>/NNNN.png becomes an actor with those actions.
Frames are baked side views (facing left) from CC0 model packs; see assets/bake_sprites.py."""
import os
from PIL import Image
from .actors import actor, _lerp_pos, _facing

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'sprites')
FPS = 24  # frames of the source animation per second of film
_cache = {}


def _frames(name, action):
    key = (name, action)
    if key not in _cache:
        d = os.path.join(ROOT, name, action)
        ims = [Image.open(os.path.join(d, f)).convert('RGBA') for f in sorted(os.listdir(d)) if f.endswith('.png')]
        box = None
        for im in ims:
            b = im.getbbox()
            if b:
                box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
        _cache[key] = [im.crop(box) for im in ims]
    return _cache[key]


def _make(name, actions):
    def draw(ctx, t, tl, st, f):
        action = st.words[1]
        frames = _frames(name, action)
        im = frames[int(tl * FPS * st.params.get('speed', 1.0)) % len(frames)]
        h = max(1, int(st.params.get('size', 0.2) * ctx.H))
        w = max(1, int(im.width * h / im.height))
        im = im.resize((w, h), Image.LANCZOS)
        if _facing(st) > 0:  # baked facing left
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
        x, y = _lerp_pos(st, f, st.params.get('y', 0.85))
        ctx.img.alpha_composite(im, (int(x * ctx.W - w / 2), int(y * ctx.H - h)))
    actor(name, actions)(draw)


if os.path.isdir(ROOT):
    for _name in sorted(os.listdir(ROOT)):
        _acts = sorted(a for a in os.listdir(os.path.join(ROOT, _name)) if os.path.isdir(os.path.join(ROOT, _name, a)))
        if _acts:
            _make(_name, _acts)
