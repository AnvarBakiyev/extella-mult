"""Full-body felt puppets: a 2D rig renderer, poses and cycles.

    from anim import Puppet, POSES, CYCLES, play
    p = Puppet('aigul', view='q34', scale=0.5)          # loads body/aigul/rig.json + part PNGs
    for i in range(50):
        t = i / 25
        pose = play('walk', t, p)                        # a dict of joint angles at time t (keyframes + easing)
        img = p.render(pose, expr='happy', mouth='A')    # RGBA, transparent, feet on img's ground line
    frame = Scene(1280, 720).frame([(p, pose, 640, 650, False)])   # several puppets on a felt background

Angles are degrees, positive = counter-clockwise on screen; at rest (all zero) arms and legs hang straight down, so a
positive angle swings a limb forward (the puppet faces screen-right; flip=True mirrors it to face left).
_L is the near side, _R the far side.
"""
import json
import math
import os

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

ROOT = os.path.dirname(os.path.abspath(__file__))
BODY = os.path.join(ROOT, 'body')
JOINTS = ['pelvis', 'torso', 'neck', 'head', 'hair_back', 'upper_arm_L', 'lower_arm_L', 'hand_L', 'upper_arm_R',
          'lower_arm_R', 'hand_R', 'thigh_L', 'shin_L', 'foot_L', 'thigh_R', 'shin_R', 'foot_R', 'tail', 'wings']
ARM = {'L': ('upper_arm_L', 'lower_arm_L', 'hand_L'), 'R': ('upper_arm_R', 'lower_arm_R', 'hand_R')}
LEG = {'L': ('thigh_L', 'shin_L', 'foot_L'), 'R': ('thigh_R', 'shin_R', 'foot_R')}
SHADOW_K = 0.3     # strength of the soft shadow each part casts on the parts beneath
FELT_BG = (214, 203, 184)


# ---------------------------------------------------------------- 2D affine helpers (3x3 matrices, y down)
def T(x, y):
    return np.array([[1, 0, x], [0, 1, y], [0, 0, 1]], float)


def Rot(deg):
    """Counter-clockwise on screen (y grows downwards)."""
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, s, 0], [-s, c, 0], [0, 0, 1]], float)


def S(sx, sy=None):
    return np.array([[sx, 0, 0], [0, sy if sy is not None else sx, 0], [0, 0, 1]], float)


def apply(M, x, y):
    return M[0, 0] * x + M[0, 1] * y + M[0, 2], M[1, 0] * x + M[1, 1] * y + M[1, 2]


def angle_of(M):
    """Screen rotation (CCW degrees) encoded in M."""
    return math.degrees(math.atan2(M[0, 1], M[0, 0]))


# ---------------------------------------------------------------- easing
EASE = {
    'linear': lambda u: u,
    'in': lambda u: u * u * u,
    'out': lambda u: 1 - (1 - u) ** 3,
    'inout': lambda u: 4 * u ** 3 if u < 0.5 else 1 - (-2 * u + 2) ** 3 / 2,
    'sine': lambda u: 0.5 - 0.5 * math.cos(math.pi * u),
    'back': lambda u: 1 + 2.7 * (u - 1) ** 3 + 1.7 * (u - 1) ** 2,  # overshoots a little: snappy settle
    'step': lambda u: 0.0 if u < 1 else 1.0,
}


# ---------------------------------------------------------------- loading
class _Sprite:
    __slots__ = ('im', 'pv', 'sh', 'shm', 'hull')

    def __init__(self, im, pivot, hull, scale):
        if scale != 1:
            w, h = max(1, round(im.width * scale)), max(1, round(im.height * scale))
            im = im.resize((w, h), Image.LANCZOS)
        self.im = im.convert('RGBa')
        self.pv = (pivot[0] * scale, pivot[1] * scale)
        self.hull = [((x - pivot[0]) * scale, (y - pivot[1]) * scale) for x, y in hull]
        a = np.asarray(im.getchannel('A'), np.float32) / 255
        m = max(2, int(10 * scale + 2))
        a = np.pad(a, m)
        self.sh = Image.fromarray((gaussian_filter(a, 7 * scale) * 255).astype(np.uint8), 'L')
        self.shm = m


class Puppet:
    def __init__(self, name, view='q34', scale=0.5, root=BODY):
        self.name, self.view, self.scale = name, view, scale
        self.dir = os.path.join(root, name)
        with open(os.path.join(self.dir, 'rig.json')) as f:
            self.rig = json.load(f)
        V = self.rig['views'][view]
        self.V = V
        self.parts = {}
        self.sprites = {}
        for n, e in V['parts'].items():
            self.parts[n] = e
            if n == 'head':
                continue
            if 'variants' in e:
                for shp, ve in e['variants'].items():
                    self.sprites[(n, shp)] = self._load(ve)
            else:
                self.sprites[(n, None)] = self._load(e)
        self.order = sorted(self.parts, key=lambda n: self.parts[n]['z'])
        self.head_cache = {}
        self._head_files = {k: v for k, v in V['head_states'].items()}
        self._head_base = Image.open(os.path.join(self.dir, V['parts']['head']['file'])).convert('RGBA')
        self.u = self.rig['px_per_unit']  # rig px per unit (offsets, pivots are in rig px)
        self.ground = V['ground']
        self.soles = V['soles']
        self._resolved = {}

    def _load(self, e):
        im = Image.open(os.path.join(self.dir, e['file'])).convert('RGBA')
        return _Sprite(im, e['pivot'], e['hull'], self.scale)

    def head_sprite(self, expr='neutral', mouth='closed', blink=False):
        key = (expr, mouth, blink)
        if key not in self.head_cache:
            im = self._head_base.copy()
            layers = []
            if expr and expr != 'neutral':
                layers.append('expr_' + expr)
            if mouth and (mouth != 'closed' or expr in (None, 'neutral')):
                layers.append('mouth_' + mouth)
            if blink:
                layers.append('blink')
            for k in layers:
                st = self._head_files.get(k)
                if st:
                    ov = Image.open(os.path.join(self.dir, st['file'])).convert('RGBA')
                    im.alpha_composite(ov, tuple(st['at']))
            e = self.parts['head']
            self.head_cache[key] = _Sprite(im, e['pivot'], e['hull'], self.scale)
        return self.head_cache[key]

    # ------------------------------------------------------------ pose -> world matrices
    def matrices(self, pose):
        """World matrix (rig px) per part, root pivot at the origin before grounding."""
        M = {}
        sc = pose.get('scale', {})
        for n in self.order_by_parent():
            e = self.parts[n]
            par = e.get('parent')
            if par is None:
                m = Rot(pose.get('pelvis', 0.0))
            else:
                ox, oy = e.get('offset', (0, 0))
                m = M[par] @ T(ox, oy) @ Rot(pose.get(n, 0.0) if n != 'hair_back' else 0.0)
            if n in sc:
                m = m @ S(*sc[n])
            if n == 'head' and pose.get('head_sx', 1.0) != 1.0:
                m = m @ S(pose['head_sx'], 1.0)
            M[n] = m
        if 'hair_back' in M:
            M['hair_back'] = M['head']
        return M

    def order_by_parent(self):
        if not hasattr(self, '_obp'):
            out, seen = [], set()

            def visit(n):
                if n in seen:
                    return
                par = self.parts[n].get('parent')
                if par:
                    visit(par)
                seen.add(n)
                out.append(n)
            for n in self.parts:
                visit(n)
            self._obp = out
        return self._obp

    def place(self, pose):
        """Matrices with the root moved so the feet stand on the ground line (y = 0) unless the pose says otherwise."""
        M = self.matrices(pose)
        g = pose.get('ground', 'feet')
        lowest = None
        if g == 'feet':
            for side in 'LR':
                for sx, sy in self.soles:
                    y = apply(M['foot_' + side], sx, sy)[1]
                    lowest = y if lowest is None else max(lowest, y)
        elif g == 'all':
            for n in self.parts:
                for hx, hy in self._hull(n, pose):
                    y = apply(M[n], hx / self.scale, hy / self.scale)[1]
                    lowest = y if lowest is None else max(lowest, y)
        else:
            lowest = self.ground
        rx, ry = pose.get('root', (0.0, 0.0))
        G = T(rx * self.u, ry * self.u - lowest)
        return {n: G @ m for n, m in M.items()}

    def _hull(self, n, pose):
        if n == 'head':
            return self.head_sprite().hull
        return self._sprite(n, pose).hull

    def _sprite(self, n, pose, head=None):
        if n == 'head':
            return head or self.head_sprite()
        if (n, None) in self.sprites:
            return self.sprites[(n, None)]
        side = n[-1]
        shp = pose.get('shape', {}).get(side, 'relaxed')
        return self.sprites.get((n, shp)) or self.sprites[(n, 'relaxed')]

    # ------------------------------------------------------------ IK helpers
    def anchor(self, M, name):
        """World point (rig px) of a named anchor: mouth, eyes, chin, head_top, chest, belly, hip_L/R, shoulder_L/R,
        knee_L/R, hand_L/R (palm centre)."""
        A = self.rig['anchors']
        aw = self.rig['dims']['arm_w']
        if name == 'mouth':
            return apply(M['head'], *self._hp(0, A['mouth'][1]))
        if name == 'eyes':
            return apply(M['head'], *self._hp(0, A['eyes_y']))
        if name == 'chin':
            return apply(M['head'], *self._hp(0, A['mouth'][1] + 0.35 * (A['mouth'][1] - A['eyes_y'])))
        if name == 'head_top':
            return apply(M['head'], *self._hp(0, A['head_top']))
        if name in ('chest', 'belly'):
            h = self.parts['head']['offset'][1]
            return apply(M['torso'], 0, h * (0.62 if name == 'chest' else 0.25))
        if name.startswith('hip_'):  # side of the waist
            return apply(M['torso'], self.V['waist_dx'] * (-1 if name[-1] == 'L' else 1), -0.015 * self.u)
        if name.startswith('shoulder_'):
            return apply(M['upper_arm_' + name[-1]], 0, 0)
        if name.startswith('knee_'):
            return apply(M['shin_' + name[-1]], 0, 0)
        if name.startswith('hand_'):
            return apply(M['hand_' + name[-1]], 0, aw * 0.9)
        raise KeyError(name)

    def _hp(self, x, y):
        return x, y

    def solve_arm(self, pose, side, target, bend=1):
        """Two-bone IK: set upper/lower arm angles so the wrist reaches target (world rig px).
        bend=+1 puts the elbow below/behind the line, -1 the other way."""
        M = self.matrices(pose)
        up, lo, ha = ARM[side]
        sx, sy = apply(M[up], 0, 0)
        a = abs(self.parts[lo]['offset'][1])
        b = abs(self.parts[ha]['offset'][1])
        dx, dy = target[0] - sx, target[1] - sy
        d = max(abs(a - b) + 1e-3, min(a + b - 1e-3, math.hypot(dx, dy)))
        base = math.degrees(math.atan2(dx, dy))  # direction as a 'down-relative' CCW angle
        cosA = (a * a + d * d - b * b) / (2 * a * d)
        A = math.degrees(math.acos(max(-1, min(1, cosA))))
        cosB = (a * a + b * b - d * d) / (2 * a * b)
        B = 180 - math.degrees(math.acos(max(-1, min(1, cosB))))
        par = angle_of(M['torso'])
        upper = base - bend * A
        pose[up] = upper - par
        pose[lo] = bend * B
        return pose

    def resolve(self, pose):
        """Fill IK targets ('reach': {side: (anchor, dx, dy, bend)} with dx, dy in units) into plain angles."""
        if 'reach' not in pose:
            return pose
        p = dict(pose)
        for side, (anc, dx, dy, bend) in pose['reach'].items():
            M = self.matrices(p)
            ax, ay = self.anchor(M, anc)
            for _ in range(2):  # the hand offset depends on the hand angle: iterate a little
                self.solve_arm(p, side, (ax + dx * self.u, ay + dy * self.u), bend)
            p[ARM[side][2]] = p.get(ARM[side][2], 0.0) + pose.get('wrist_' + side, 0.0)
        p.pop('reach')
        return p

    # ------------------------------------------------------------ render
    def render(self, pose, expr=None, mouth=None, blink=None, pad=8):
        """Returns (premultiplied float32 HxWx4 array, (ox, oy)): the puppet drawn with its ground line at y = oy and
        the root at x = ox (scaled px). Use to_image() for a PIL image."""
        expr = expr or pose.get('expr', 'neutral')
        mouth = mouth or pose.get('mouth', 'closed')
        blink = pose.get('blink', False) if blink is None else blink
        head = self.head_sprite(expr, mouth, blink)
        M = self.place(pose)
        s = self.scale
        Ms = {n: S(s) @ m @ S(1 / s) for n, m in M.items()}  # scaled local (from the pivot) -> scaled world
        # bounds
        xs, ys = [], []
        for n in self.parts:
            sp = self._sprite(n, pose, head)
            for hx, hy in sp.hull:
                x, y = apply(Ms[n], hx, hy)
                xs.append(x)
                ys.append(y)
        props = pose.get('props', {})
        x0, y0 = int(math.floor(min(xs))) - pad - 20, int(math.floor(min(ys))) - pad - 20
        x1, y1 = int(math.ceil(max(xs))) + pad + 20, int(math.ceil(max(ys))) + pad + 20
        x1 = max(x1, int(60 * s))
        y1 = max(y1, 4)
        W, H = x1 - x0, y1 - y0
        canvas = np.zeros((H, W, 4), np.float32)
        z = {n: self.parts[n]['z'] for n in self.parts}
        for grp in pose.get('front', []):  # bring the far arm/leg in front of the body
            for n in (ARM.get(grp[-1]) if grp.startswith('arm') else LEG.get(grp[-1])):
                z[n] = z[n] + 20 if grp.startswith('arm') else z[n] + 6
        for grp in pose.get('back', []):  # push the near arm behind the head/torso
            for n in ARM[grp[-1]]:
                z[n] = z[n] - 3.5
        order = sorted(self.parts, key=lambda n: z[n])
        prop_draw = _props_for(self, pose, Ms, z)
        items = [(z[n], 'part', n) for n in order] + [(pz, 'prop', pd) for pz, pd in prop_draw]
        items.sort(key=lambda t: t[0])
        for _z, kind, it in items:
            if kind == 'part':
                sp = self._sprite(it, pose, head)
                m = Ms[it] @ T(-sp.pv[0], -sp.pv[1])
            else:
                sp, m = it
            _blit(canvas, sp, m, x0, y0)
        return canvas, (-x0, -y0)

    def image(self, pose, **kw):
        arr, origin = self.render(pose, **kw)
        return to_image(arr), origin


def _blit(canvas, sp, m, x0, y0):
    """Shadow, then the sprite, through matrix m (sprite px -> scaled world px), into canvas whose (0,0) is (x0, y0)."""
    H, W = canvas.shape[:2]
    w, h = sp.im.size
    corners = [apply(m, cx, cy) for cx, cy in ((0, 0), (w, 0), (0, h), (w, h))]
    bx0 = int(math.floor(min(c[0] for c in corners))) - x0 - 1
    by0 = int(math.floor(min(c[1] for c in corners))) - y0 - 1
    bx1 = int(math.ceil(max(c[0] for c in corners))) - x0 + 1
    by1 = int(math.ceil(max(c[1] for c in corners))) - y0 + 1
    # shadow (offset down-right, light from the top-left), only onto what is already drawn
    off = max(1.0, 9 * _scale_of(m))
    mm = sp.shm
    msh = T(off * 0.5, off) @ m @ T(-mm, -mm)
    _over_shadow(canvas, sp.sh, msh, x0, y0)
    cx0, cy0, cx1, cy1 = max(0, bx0), max(0, by0), min(W, bx1), min(H, by1)
    if cx1 <= cx0 or cy1 <= cy0:
        return
    inv = np.linalg.inv(m) @ T(x0 + cx0, y0 + cy0)
    data = (inv[0, 0], inv[0, 1], inv[0, 2], inv[1, 0], inv[1, 1], inv[1, 2])
    t = sp.im.transform((cx1 - cx0, cy1 - cy0), Image.AFFINE, data, resample=Image.BILINEAR)
    src = np.asarray(t, np.float32) / 255.0
    dst = canvas[cy0:cy1, cx0:cx1]
    dst *= (1 - src[..., 3:4])
    dst += src


def _scale_of(m):
    return math.hypot(m[0, 0], m[1, 0])


def _over_shadow(canvas, sh, m, x0, y0):
    H, W = canvas.shape[:2]
    w, h = sh.size
    corners = [apply(m, cx, cy) for cx, cy in ((0, 0), (w, 0), (0, h), (w, h))]
    cx0 = max(0, int(math.floor(min(c[0] for c in corners))) - x0)
    cy0 = max(0, int(math.floor(min(c[1] for c in corners))) - y0)
    cx1 = min(W, int(math.ceil(max(c[0] for c in corners))) - x0)
    cy1 = min(H, int(math.ceil(max(c[1] for c in corners))) - y0)
    if cx1 <= cx0 or cy1 <= cy0:
        return
    inv = np.linalg.inv(m) @ T(x0 + cx0, y0 + cy0)
    t = sh.transform((cx1 - cx0, cy1 - cy0), Image.AFFINE, (inv[0, 0], inv[0, 1], inv[0, 2], inv[1, 0], inv[1, 1], inv[1, 2]),
                     resample=Image.BILINEAR)
    a = np.asarray(t, np.float32) / 255.0 * SHADOW_K
    dst = canvas[cy0:cy1, cx0:cx1]
    dst[..., :3] *= (1 - a)[..., None]


def to_image(arr):
    a = arr[..., 3:4]
    rgb = np.where(a > 1e-4, arr[..., :3] / np.maximum(a, 1e-4), 0)
    out = np.concatenate([rgb, a], axis=2)
    return Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGBA')


# ---------------------------------------------------------------- props (felt cut-outs, built by charlib.build_props)
_PROPS = {}


def _prop(name, scale):
    key = (name, scale)
    if key not in _PROPS:
        with open(os.path.join(BODY, '_props', 'props.json')) as f:
            meta = json.load(f)[name]
        im = Image.open(os.path.join(BODY, '_props', meta['file'])).convert('RGBA')
        _PROPS[key] = (_Sprite(im, meta['pivot'], meta['hull'], scale), meta)
    return _PROPS[key]


def _props_for(p, pose, Ms, z):
    """Props in the pose: 'props': {'phone': 'R'} (held in a hand), {'stool': True}, {'laptop': True}, {'mic': 'L'}."""
    out = []
    s = p.scale
    aw = p.rig['dims']['arm_w']
    for name, how in pose.get('props', {}).items():
        sp, meta = _prop(name, s * p.u / 1024.0)  # props are drawn at 1024 px per unit
        if how in ('L', 'R'):
            hand = 'hand_' + how
            m = Ms[hand] @ T(0, aw * meta.get('grip', 0.9) * s) @ Rot(meta.get('angle', 0) + pose.get(name + '_angle', 0))
            out.append((z[hand] + 0.5, (sp, m @ T(-sp.pv[0], -sp.pv[1]))))
        elif name == 'stool':  # under the thighs, its legs stretched down to the floor (world y = 0)
            hx, hy = apply(Ms['thigh_L'], 0, 0)
            top = hy + p.rig['dims']['leg_w'] * 0.5 * s
            px = apply(Ms['pelvis'], 0, 0)[0]
            ky = max(0.3, (0 - top) / max(1.0, sp.im.height - sp.pv[1]))
            m = T(px - 0.01 * p.u * s, top) @ S(1, ky) @ T(-sp.pv[0], -sp.pv[1])
            out.append((-1, (sp, m)))
        elif name == 'laptop':
            kx, ky = apply(Ms['shin_L'], 0, 0)
            hx, hy = apply(Ms['thigh_L'], 0, 0)
            top = min(ky, hy) - p.rig['dims']['leg_w'] * 0.5 * s
            m = T(hx + (kx - hx) * 0.62, top) @ T(-sp.pv[0], -sp.pv[1])
            out.append((z['torso'] + 0.5, (sp, m)))
    return out


# ---------------------------------------------------------------- scene: a plain felt background
class Scene:
    def __init__(self, W, H, floor=0.78, wall=FELT_BG, ground=(178, 160, 136), seed=3):
        self.W, self.H = W, H
        self.floor_y = int(H * floor)
        rng = np.random.default_rng(seed)
        g = gaussian_filter(rng.standard_normal((H, W)).astype(np.float32), 0.9)
        g2 = gaussian_filter(rng.standard_normal((H, W)).astype(np.float32), (0.7, 3.0))
        grain = (0.6 * g / g.std() + 0.4 * g2 / g2.std())
        bg = np.zeros((H, W, 3), np.float32)
        bg[:] = np.array(wall, np.float32) / 255
        bg[self.floor_y:] = np.array(ground, np.float32) / 255
        # a soft felt seam where the wall meets the floor and a gentle vignette
        yy = np.arange(H)[:, None]
        seam = np.exp(-((yy - self.floor_y) / (0.012 * H)) ** 2) * 0.12
        xx = np.arange(W)[None, :]
        vig = 1 - 0.18 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H * 0.45) / H) ** 2)
        bg *= (1 - seam)[..., None] * vig[..., None]
        bg *= (1 + 0.04 * grain)[..., None]
        self.bg = np.clip(bg, 0, 1)

    def frame(self, items):
        """items: [(puppet, pose, x, ground_y, flip) or (puppet, pose, x, ground_y, flip, dict(expr=, mouth=, blink=))].
        Returns an RGB uint8 array."""
        out = self.bg.copy()
        for it in items:
            p, pose, x, gy, flip = it[:5]
            kw = it[5] if len(it) > 5 else {}
            arr, (ox, oy) = p.render(pose, **kw)
            if flip:
                arr = arr[:, ::-1]
                ox = arr.shape[1] - ox
            self.paste(out, arr, int(round(x - ox)), int(round(gy - oy)), gy, p.scale)
        return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)

    def paste(self, out, arr, X, Y, gy, scale):
        H, W = out.shape[:2]
        h, w = arr.shape[:2]
        # contact shadow: a soft ellipse on the floor under the puppet
        a = arr[..., 3]
        cols = np.nonzero(a[max(0, int(gy - Y) - int(40 * scale)):int(gy - Y) + 1].max(axis=0) > 0.3)[0] if 0 <= gy - Y <= h else []
        if len(cols):
            cx = X + (cols[0] + cols[-1]) / 2
            rx = (cols[-1] - cols[0]) / 2 + 30 * scale
            ry = 14 * scale + 6
            ys, xs = np.ogrid[0:H, 0:W]
            e = np.clip(1 - ((xs - cx) / rx) ** 2 - ((ys - gy - 2) / ry) ** 2, 0, 1) ** 0.8 * 0.35
            out *= (1 - e)[..., None]
        # drop shadow of the whole cut-out on the wall/floor
        sm = gaussian_filter(a, 8 * scale + 1)
        dx, dy = int(10 * scale) + 2, int(14 * scale) + 2
        self._mul(out, 1 - 0.28 * sm, X + dx, Y + dy)
        # the puppet
        x0, y0, x1, y1 = max(0, X), max(0, Y), min(W, X + w), min(H, Y + h)
        if x1 <= x0 or y1 <= y0:
            return
        src = arr[y0 - Y:y1 - Y, x0 - X:x1 - X]
        out[y0:y1, x0:x1] = out[y0:y1, x0:x1] * (1 - src[..., 3:4]) + src[..., :3]

    @staticmethod
    def _mul(out, m, X, Y):
        H, W = out.shape[:2]
        h, w = m.shape
        x0, y0, x1, y1 = max(0, X), max(0, Y), min(W, X + w), min(H, Y + h)
        if x1 > x0 and y1 > y0:
            out[y0:y1, x0:x1] *= m[y0 - Y:y1 - Y, x0 - X:x1 - X][..., None]


# ================================================================ poses and cycles
# A pose is a dict:
#   <joint>: angle in degrees (pelvis = whole body, torso, head, upper_arm_L, lower_arm_L, hand_L, thigh_L, shin_L,
#            foot_L, ... _R, tail, wings); missing joints are 0 (rest: limbs hang straight down)
#   'reach': {'L': (anchor, dx, dy, bend)}  arm IK: wrist to an anchor (mouth, eyes, chin, head_top, chest, belly,
#            hip_L/R, shoulder_L/R, knee_L/R) + (dx, dy) units; bend=+1/-1 picks the elbow side
#   'wrist_L': extra hand angle on top of the IK result
#   'shape': {'L': 'open'|'fist'|'point'|'flat'|'relaxed'}, 'props': {'phone': 'L', 'stool': True, 'laptop': True}
#   'zset': {part: z}  draw order overrides (torso is 14, head 15, near arm 16-18, far arm 3-5)
#   'root': (dx, dy) units after grounding (dy < 0 lifts), 'ground': 'feet' (default) | 'all' | None
#   'head_sx': head width factor (head shake), 'scale': {part: (sx, sy)}, 'expr', 'mouth', 'blink'
#   'base': another pose name to start from;  'side': {...} overrides used in the side view

POSE = {
    'rest': {},
    'stand': {'upper_arm_L': -5, 'lower_arm_L': 8, 'hand_L': 4, 'upper_arm_R': 5, 'lower_arm_R': 10, 'hand_R': 4,
              'thigh_L': -2, 'thigh_R': 3, 'foot_R': 0,
              'side': {'upper_arm_L': 2, 'upper_arm_R': -3, 'thigh_L': 3, 'thigh_R': -3}},
    'sit': {'base': 'stand', 'thigh_L': 86, 'shin_L': -86, 'thigh_R': 82, 'shin_R': -80, 'torso': 4, 'props': {'stool': True},
            'reach': {'L': ('knee_L', -0.05, -0.035, 1), 'R': ('knee_R', -0.04, -0.035, 1)}, 'shape': {'L': 'flat', 'R': 'flat'}},
    'wave': {'base': 'stand', 'upper_arm_R': 118, 'lower_arm_R': 42, 'hand_R': -6, 'shape': {'R': 'open'}, 'head': 5,
             'expr': 'happy', 'side': {'upper_arm_R': 132, 'lower_arm_R': 30}},
    'point': {'base': 'stand', 'upper_arm_R': 84, 'lower_arm_R': 6, 'hand_R': -4, 'shape': {'R': 'point'}, 'head': -3,
              'torso': -3},
    'shrug': {'base': 'stand', 'upper_arm_L': -22, 'lower_arm_L': -72, 'hand_L': -12, 'upper_arm_R': 24, 'lower_arm_R': 74,
              'hand_R': 12, 'shape': {'L': 'open', 'R': 'open'}, 'head': 9, 'torso': 2, 'mouth': 'MBP',
              'side': {'upper_arm_L': -10, 'lower_arm_L': 70, 'upper_arm_R': 6, 'lower_arm_R': 80}},
    'facepalm': {'base': 'stand', 'torso': -6, 'head': -12, 'reach': {'L': ('eyes', -0.035, 0.05, 1)}, 'wrist_L': 14,
                 'shape': {'L': 'open'}, 'expr': 'angry'},
    'arms_crossed': {'base': 'stand', 'reach': {'L': ('chest', 0.075, 0.05, 1), 'R': ('chest', -0.05, 0.03, -1)},
                     'shape': {'L': 'fist', 'R': 'fist'}, 'wrist_L': 75, 'wrist_R': -60, 'head': 4,
                     'zset': {'lower_arm_R': 14.3, 'hand_R': 14.2}, 'expr': 'angry', 'mouth': 'closed'},
    'hands_on_hips': {'base': 'stand', 'reach': {'L': ('hip_L', -0.005, -0.01, 1), 'R': ('hip_R', 0.005, -0.01, -1)},
                      'shape': {'L': 'fist', 'R': 'fist'}, 'wrist_L': 50, 'wrist_R': -50, 'head': 6, 'thigh_L': -6, 'thigh_R': 7,
                      'expr': 'happy', 'side': {'reach': {'L': ('hip_L', 0.035, 0.0, 1), 'R': ('hip_R', 0.03, 0.0, 1)},
                                                'wrist_L': 40, 'wrist_R': 40}},
    'typing': {'base': 'sit', 'props': {'stool': True, 'laptop': True}, 'head': -10, 'torso': -4,
               'reach': {'L': ('knee_L', -0.04, -0.075, 1), 'R': ('knee_R', -0.02, -0.08, 1)}, 'wrist_L': 70, 'wrist_R': 70,
               'shape': {'L': 'flat', 'R': 'flat'}},
    'holding_phone': {'base': 'stand', 'reach': {'L': ('chest', 0.06, 0.02, 1)}, 'wrist_L': 155, 'shape': {'L': 'fist'},
                      'props': {'phone': 'L'}, 'phone_angle': 180, 'head': -12, 'zset': {}},
    'thinking': {'base': 'stand', 'reach': {'L': ('chin', 0.0, 0.035, 1), 'R': ('belly', -0.02, 0.02, -1)},
                 'wrist_L': 170, 'shape': {'L': 'fist', 'R': 'flat'}, 'wrist_R': -80, 'head': 8,
                 'zset': {'lower_arm_R': 14.3, 'hand_R': 14.2}},
    'jump': {'upper_arm_L': -150, 'lower_arm_L': -15, 'upper_arm_R': 150, 'lower_arm_R': 15, 'shape': {'L': 'open', 'R': 'open'},
             'thigh_L': 40, 'shin_L': -70, 'foot_L': -20, 'thigh_R': 30, 'shin_R': -60, 'foot_R': -20, 'root': (0, -0.2),
             'expr': 'happy', 'mouth': 'A', 'side': {'upper_arm_L': -165, 'upper_arm_R': 150}},
    'fall': {'pelvis': 88, 'ground': 'all', 'upper_arm_L': -60, 'lower_arm_L': -20, 'upper_arm_R': 70, 'lower_arm_R': 30,
             'thigh_L': 20, 'shin_L': -30, 'thigh_R': -10, 'shin_R': -10, 'head': -10, 'expr': 'shocked', 'mouth': 'O',
             'shape': {'L': 'open', 'R': 'open'}},
    'bow': {'base': 'stand', 'torso': -36, 'head': -12, 'upper_arm_L': 32, 'lower_arm_L': 6, 'upper_arm_R': 38, 'lower_arm_R': 8,
            'pelvis': 5, 'thigh_L': -7, 'thigh_R': -5, 'root': (-0.06, 0), 'blink': True},
    'dance': {'pelvis': 6, 'torso': -12, 'head': 10, 'upper_arm_L': -140, 'lower_arm_L': -30, 'upper_arm_R': 60,
              'lower_arm_R': 70, 'shape': {'L': 'point', 'R': 'fist'}, 'thigh_L': 25, 'shin_L': -45, 'thigh_R': -12, 'shin_R': 0,
              'expr': 'happy', 'mouth': 'E'},
}


def pose(name_or_dict, view='q34'):
    """A pose dict with its base poses and the view's overrides merged in."""
    p = POSE[name_or_dict] if isinstance(name_or_dict, str) else name_or_dict
    out = {}
    if 'base' in p:
        out.update(pose(p['base'], view))
    for k, v in p.items():
        if k in ('base', 'side'):
            continue
        if k in ('shape', 'props', 'zset', 'reach') and isinstance(v, dict):
            out[k] = dict(out.get(k, {}), **v) if k != 'reach' else dict(v)
        else:
            out[k] = v
    if view == 'side' and 'side' in p:
        for k, v in p['side'].items():
            if k in ('shape', 'props', 'zset') and isinstance(v, dict):
                out[k] = dict(out.get(k, {}), **v)
            else:
                out[k] = v
    if 'reach' in out and 'base' in p and 'reach' not in p and 'reach' not in p.get('side', {}):
        pass
    return out


def mirror_legs(p):
    """Swap left and right limb angles (for the second half of walk/run cycles)."""
    q = dict(p)
    for a, b in (('thigh_L', 'thigh_R'), ('shin_L', 'shin_R'), ('foot_L', 'foot_R'), ('upper_arm_L', 'upper_arm_R'),
                 ('lower_arm_L', 'lower_arm_R'), ('hand_L', 'hand_R')):
        q[a], q[b] = p.get(b, 0.0), p.get(a, 0.0)
    return q


class Clip:
    """Keyframes [(time s, pose name or dict, easing into this key)]. loop=(t0, t1) repeats that span after the
    first pass; cycles loop over their whole length. hold = the time that shows the pose best (for contact sheets).
    advance = forward travel per second in units (walk/run), so a scene can move the puppet without foot sliding."""

    def __init__(self, keys, loop=None, hold=None, advance=0.0):
        self.keys = keys
        self.loop = loop
        self.hold = keys[-1][0] if hold is None else hold
        self.advance = advance
        self.length = keys[-1][0]

    def at(self, t, puppet):
        if self.loop:
            t0, t1 = self.loop
            if t > t1:
                t = t0 + (t - t0) % (t1 - t0)
        t = max(0.0, min(t, self.length))
        ks = self.keys
        i = 0
        while i < len(ks) - 2 and ks[i + 1][0] <= t:
            i += 1
        ta, pa, _ = ks[i]
        tb, pb, eb = ks[i + 1] if i + 1 < len(ks) else ks[i]
        u = 0.0 if tb <= ta else min(1.0, max(0.0, (t - ta) / (tb - ta)))
        u = EASE[eb](u)
        A = puppet.resolved(pa)
        B = puppet.resolved(pb)
        return blend(A, B, u)


def blend(A, B, u):
    out = {}
    for k in set(A) | set(B):
        a, b = A.get(k), B.get(k)
        if k in ('root',):
            a, b = a or (0.0, 0.0), b or (0.0, 0.0)
            out[k] = (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
        elif k == 'head_sx':
            a, b = 1.0 if a is None else a, 1.0 if b is None else b
            out[k] = a + (b - a) * u
        elif k == 'scale':
            a, b = a or {}, b or {}
            out[k] = {n: tuple((a.get(n, (1, 1))[i] + (b.get(n, (1, 1))[i] - a.get(n, (1, 1))[i]) * u) for i in (0, 1))
                      for n in set(a) | set(b)}
        elif isinstance(a, (int, float)) or isinstance(b, (int, float)):
            if isinstance(a, bool) or isinstance(b, bool):
                out[k] = (a if u < 0.5 else b) or False
            else:
                a, b = a or 0.0, b or 0.0
                out[k] = a + (b - a) * u
        else:
            out[k] = (a if u < 0.5 else b) if (a is not None and b is not None) else (b if b is not None and u >= 0.5 else
                                                                                       (a if a is not None else None))
            if out[k] is None:
                out.pop(k)
    if 'ground' not in out and ('ground' in A or 'ground' in B):
        pass
    return out


def _resolved(self, p):
    """Pose name/dict -> plain angles for this puppet and view (IK solved); cached."""
    key = p if isinstance(p, str) else id(p)
    if key not in self._resolved:
        self._resolved[key] = self.resolve(pose(p, self.view))
    return self._resolved[key]


Puppet.resolved = _resolved


def _walk_keys(stride=24, knee=42, arm=22, lean=-3, period=1.0, bob_head=2):
    c0 = {'thigh_L': stride, 'shin_L': -4, 'foot_L': 12, 'thigh_R': -stride * 0.8, 'shin_R': -18, 'foot_R': -14,
          'upper_arm_L': -arm, 'lower_arm_L': 10, 'upper_arm_R': arm, 'lower_arm_R': 26, 'torso': lean, 'head': bob_head,
          'hand_L': 4, 'hand_R': 4}
    p0 = {'thigh_L': -2, 'shin_L': -6, 'foot_L': 2, 'thigh_R': stride * 0.6, 'shin_R': -knee, 'foot_R': 4,
          'upper_arm_L': -2, 'lower_arm_L': 12, 'upper_arm_R': 2, 'lower_arm_R': 14, 'torso': lean, 'head': -bob_head,
          'hand_L': 4, 'hand_R': 4}
    c1, p1 = mirror_legs(c0), mirror_legs(p0)
    q = period / 4
    return [(0, c0, 'linear'), (q, p0, 'sine'), (2 * q, c1, 'sine'), (3 * q, p1, 'sine'), (4 * q, c0, 'sine')]


def _run_keys(period=0.62):
    c0 = {'thigh_L': 40, 'shin_L': -18, 'foot_L': 10, 'thigh_R': -30, 'shin_R': -50, 'foot_R': -20,
          'upper_arm_L': -45, 'lower_arm_L': 85, 'upper_arm_R': 45, 'lower_arm_R': 85, 'torso': -12, 'head': 6,
          'shape': {'L': 'fist', 'R': 'fist'}}
    f0 = {'thigh_L': 10, 'shin_L': -70, 'foot_L': -10, 'thigh_R': 35, 'shin_R': -100, 'foot_R': 0,
          'upper_arm_L': 10, 'lower_arm_L': 80, 'upper_arm_R': -10, 'lower_arm_R': 80, 'torso': -14, 'head': 8,
          'root': (0, -0.05), 'ground': 'feet', 'shape': {'L': 'fist', 'R': 'fist'}}
    c1, f1 = mirror_legs(c0), mirror_legs(f0)
    q = period / 4
    return [(0, c0, 'linear'), (q, f0, 'out'), (2 * q, c1, 'in'), (3 * q, f1, 'out'), (4 * q, c0, 'in')]


def _wave_keys():
    up = pose('wave')
    a = dict(up, lower_arm_R=up['lower_arm_R'] + 26, hand_R=up['hand_R'] + 12)
    b = dict(up, lower_arm_R=up['lower_arm_R'] - 12, hand_R=up['hand_R'] - 10)
    return [(0, 'stand', 'linear'), (0.45, up, 'back'), (0.75, a, 'sine'), (1.05, b, 'sine'), (1.35, a, 'sine'),
            (1.65, b, 'sine')]


def _dance_keys(beat=0.42):
    d = POSE['dance']
    a = dict(d)
    b = dict(d, pelvis=-6, torso=12, head=-10, upper_arm_L=-60, lower_arm_L=-70, upper_arm_R=140, lower_arm_R=30,
             shape={'L': 'fist', 'R': 'point'}, thigh_L=-12, shin_L=0, thigh_R=25, shin_R=-45, mouth='A')
    mid = dict(d, pelvis=0, torso=0, head=0, upper_arm_L=-100, lower_arm_L=-50, upper_arm_R=100, lower_arm_R=50,
               thigh_L=12, shin_L=-30, thigh_R=12, shin_R=-30, mouth='closed')
    return [(0, 'stand', 'linear'), (beat, a, 'back'), (2 * beat, mid, 'sine'), (3 * beat, b, 'back'),
            (4 * beat, mid, 'sine'), (5 * beat, a, 'back')]


def _typing_keys():
    t = POSE['typing']
    a = dict(t, wrist_L=t['wrist_L'] + 14, wrist_R=t['wrist_R'] - 6)
    b = dict(t, wrist_L=t['wrist_L'] - 8, wrist_R=t['wrist_R'] + 14)
    return [(0, 'sit', 'linear'), (0.5, t, 'inout'), (0.62, a, 'sine'), (0.74, b, 'sine'), (0.86, a, 'sine'), (0.98, b, 'sine')]


def _enter(name, dur=0.5, ease='back'):
    return Clip([(0, 'stand', 'linear'), (dur, name, ease)])


POSES = {
    'stand': Clip([(0, 'stand', 'linear'), (0.4, 'stand', 'linear')]),
    'sit': Clip([(0, 'stand', 'linear'), (0.6, 'sit', 'inout')]),
    'wave': Clip(_wave_keys(), loop=(0.75, 1.35), hold=0.75),
    'point': _enter('point', 0.45),
    'shrug': _enter('shrug', 0.4),
    'facepalm': _enter('facepalm', 0.35, 'out'),
    'arms_crossed': _enter('arms_crossed', 0.6, 'inout'),
    'hands_on_hips': _enter('hands_on_hips', 0.5, 'inout'),
    'typing': Clip(_typing_keys(), loop=(0.62, 0.86), hold=0.62),
    'holding_phone': _enter('holding_phone', 0.6, 'inout'),
    'thinking': _enter('thinking', 0.6, 'inout'),
    'jump': Clip([(0, 'stand', 'linear'),
                  (0.25, {'base': 'stand', 'thigh_L': 40, 'shin_L': -75, 'foot_L': 35, 'thigh_R': 40, 'shin_R': -75, 'foot_R': 35,
                          'upper_arm_L': 30, 'upper_arm_R': -30 + 60, 'lower_arm_L': 40, 'lower_arm_R': 40, 'torso': -14},
                   'inout'),
                  (0.55, 'jump', 'out'),
                  (0.85, {'base': 'stand', 'thigh_L': 30, 'shin_L': -55, 'foot_L': 25, 'thigh_R': 30, 'shin_R': -55,
                          'foot_R': 25, 'upper_arm_L': -40, 'upper_arm_R': 40, 'torso': -8, 'expr': 'happy'}, 'in'),
                  (1.2, 'stand', 'back')], hold=0.55),
    'fall': Clip([(0, 'stand', 'linear'),
                  (0.25, {'base': 'stand', 'pelvis': 18, 'upper_arm_L': -80, 'upper_arm_R': 90, 'expr': 'shocked',
                          'mouth': 'O', 'shape': {'L': 'open', 'R': 'open'}, 'ground': 'all'}, 'out'),
                  (0.6, 'fall', 'in'), (0.75, dict(POSE['fall'], pelvis=82, head=-4), 'out'), (0.9, 'fall', 'sine')],
                 hold=0.9),
    'bow': Clip([(0, 'stand', 'linear'), (0.6, 'bow', 'inout'), (1.1, 'bow', 'linear'), (1.6, 'stand', 'inout')], hold=0.6),
    'dance': Clip(_dance_keys(), loop=(0.42, 2.1), hold=0.42),
}


def _cycle(keys, **kw):
    return Clip(keys, loop=(0, keys[-1][0]), hold=keys[0][0], **kw)


def _nod_keys():
    return [(0, 'stand', 'linear'), (0.25, {'base': 'stand', 'head': -13, 'torso': -2}, 'sine'),
            (0.5, {'base': 'stand', 'head': 3}, 'sine'), (0.75, {'base': 'stand', 'head': -11, 'torso': -1}, 'sine'),
            (1.0, 'stand', 'sine')]


def _shake_keys():
    a = {'base': 'stand', 'head': 5, 'head_sx': 0.9, 'expr': 'angry'}
    b = {'base': 'stand', 'head': -5, 'head_sx': 0.9, 'expr': 'angry'}
    return [(0, 'stand', 'linear'), (0.15, a, 'sine'), (0.35, b, 'sine'), (0.55, a, 'sine'), (0.75, b, 'sine'),
            (0.9, 'stand', 'sine')]


def _laugh_keys():
    base = {'base': 'stand', 'reach': {'L': ('belly', 0.03, 0.03, 1)}, 'wrist_L': -40, 'shape': {'L': 'flat'}, 'expr': 'happy'}
    up = dict(base, torso=9, head=12, thigh_L=-2, shin_L=0, thigh_R=3, shin_R=0, mouth='A')
    dn = dict(base, torso=3, head=4, thigh_L=12, shin_L=-22, thigh_R=14, shin_R=-24, mouth='E')
    return [(0, up, 'linear'), (0.18, dn, 'sine'), (0.36, up, 'sine')]


def _breath_keys():
    a = {'base': 'stand', 'scale': {'torso': (1.0, 1.0)}, 'head': 0}
    b = {'base': 'stand', 'scale': {'torso': (1.012, 1.018)}, 'head': 1.5, 'upper_arm_L': -7, 'upper_arm_R': 7}
    c = dict(a, blink=True)
    return [(0, a, 'linear'), (1.5, b, 'sine'), (2.9, a, 'sine'), (3.0, c, 'step'), (3.12, a, 'step')]


CYCLES = {
    'walk': _cycle(_walk_keys(), advance=None),
    'run': _cycle(_run_keys(), advance=None),
    'nod': _cycle(_nod_keys()),
    'head_shake': _cycle(_shake_keys()),
    'laugh': _cycle(_laugh_keys()),
    'idle': _cycle(_breath_keys()),
}


def clip(name):
    return POSES.get(name) or CYCLES[name]


def play(name, t, puppet):
    """The pose of clip `name` at time t (seconds) for this puppet (angles resolved for its body and view)."""
    return clip(name).at(t, puppet)


def stride(puppet, name='walk'):
    """Forward travel per cycle (rig px) for walk/run: twice the distance between the ankles at the contact key, so a
    scene moving the puppet at stride/period keeps the planted foot still."""
    c = clip(name)
    p = puppet.resolved(c.keys[0][1])
    M = puppet.matrices(p)
    xl = apply(M['foot_L'], 0, 0)[0]
    xr = apply(M['foot_R'], 0, 0)[0]
    return 2 * abs(xl - xr)
