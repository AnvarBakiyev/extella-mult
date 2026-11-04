"""Felt engine for code-generated effects.

Every piece of an effect is drawn as vector parts (polygons, strokes, stitches), rasterised with 2x supersampling,
and then turned into a felt cut-out with the same recipe as handler/felt.py::felt_composite:
soft rounded bevel lit from the top-left, darker rim, fibrous grain, fuzzy edge and a soft drop shadow.

The difference from felt_composite is speed: a piece is felted once as a small sprite and cached
(by shape, size class and quantised angle), then pasted into a premultiplied float canvas.
That lets an effect move hundreds of felt pieces per frame at 1920x1080.
The output layer is transparent RGBA and carries the drop shadow as semi-transparent black,
so it can be laid over any scene.
"""
import math
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'feltlook'))
import feltlook as FL  # noqa: E402  felt v2+ shared with plates, props and characters

USE_FELT2 = os.environ.get('FELT', '2') != '1'
KIND_HINT = {'fx': None, 'kind': None}  # set by effects_lib.render(): the wool of the current effect  # FELT=1: the old flat felt (for before/after sheets)

# ---------------------------------------------------------------- colours

def rgb(c):
    """'#rrggbb' or (r,g,b) 0-255 -> float tuple 0-1."""
    if isinstance(c, str):
        c = c.lstrip('#')
        return tuple(int(c[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    if max(c) > 1.0:
        return tuple(v / 255.0 for v in c[:3])
    return tuple(c[:3])


def mix(a, b, f):
    a, b = rgb(a), rgb(b)
    return tuple(a[i] * (1 - f) + b[i] * f for i in range(3))


def lighter(c, f=0.25):
    return mix(c, (1, 1, 1), f)


def darker(c, f=0.25):
    return mix(c, (0, 0, 0), f)


def _c255(c):
    c = rgb(c)
    return tuple(int(round(max(0, min(1, v)) * 255)) for v in c)


# ---------------------------------------------------------------- grain

_GR = {}


def grain():
    """Fine fibre grain + low-frequency mottling, one big tile shared by all sprites."""
    if 'g' not in _GR:
        rng = np.random.default_rng(7)
        h, w = 1200, 2100
        k = 0.67
        fine = gaussian_filter(rng.standard_normal((h, w)).astype(np.float32), 0.8 * k)
        fib = gaussian_filter(rng.standard_normal((h, w)).astype(np.float32), (0.6 * k, 2.5 * k))
        mot = gaussian_filter(rng.standard_normal((h, w)).astype(np.float32), 14)
        g = 0.6 * fine / fine.std() + 0.4 * fib / fib.std()
        _GR['g'] = (g.astype(np.float32), (mot / mot.std()).astype(np.float32))
    return _GR['g']


def _grain_crop(h, w, seed):
    g, m = grain()
    H, W = g.shape
    if h > H or w > W:  # tile
        reps = (h // H + 1, w // W + 1)
        g, m = np.tile(g, reps), np.tile(m, reps)
        H, W = g.shape
    r = np.random.default_rng(seed)
    y = int(r.integers(0, H - h + 1))
    x = int(r.integers(0, W - w + 1))
    return g[y:y + h, x:x + w], m[y:y + h, x:x + w]


def blur(a, sigma):
    """Gaussian blur; big blurs on big arrays are done at reduced resolution (as in felt.py)."""
    if sigma <= 0:
        return a
    h, w = a.shape
    k = 4 if sigma >= 10 else 2
    if sigma < 4 or h * w < 250_000 or h < 8 * k or w < 8 * k:
        return gaussian_filter(a, sigma, mode='constant')
    im = Image.fromarray(a, 'F')
    sm = np.asarray(im.resize((max(1, w // k), max(1, h // k)), Image.BILINEAR), np.float32)
    sm = gaussian_filter(sm, sigma / k, mode='constant')
    return np.asarray(Image.fromarray(sm, 'F').resize((w, h), Image.BILINEAR), np.float32)


# ---------------------------------------------------------------- geometry

def xform(pts, sx=1.0, sy=None, ang=0.0, tx=0.0, ty=0.0):
    p = np.asarray(pts, np.float64).reshape(-1, 2)
    sy = sx if sy is None else sy
    x, y = p[:, 0] * sx, p[:, 1] * sy
    if ang:
        c, s = math.cos(ang), math.sin(ang)
        x, y = x * c - y * s, x * s + y * c
    return np.stack([x + tx, y + ty], 1)


def ellipse_pts(rx, ry=None, n=None):
    ry = rx if ry is None else ry
    n = n or int(max(16, min(160, (rx + ry) * 0.9)))
    a = np.linspace(0, 2 * math.pi, n, endpoint=False)
    return np.stack([np.cos(a) * rx, np.sin(a) * ry], 1)


def star_pts(n=5, r1=1.0, r2=0.45, rot=-math.pi / 2):
    pts = []
    for i in range(2 * n):
        r = r1 if i % 2 == 0 else r2
        a = rot + i * math.pi / n
        pts.append((math.cos(a) * r, math.sin(a) * r))
    return np.array(pts)


def round_star_pts(n=5, r1=1.0, r2=0.5, rot=-math.pi / 2, m=12):
    """Star with soft (rounded) points: radius modulated by a smooth function."""
    k = n * m * 2
    a = np.linspace(0, 2 * math.pi, k, endpoint=False)
    t = (np.cos(n * (a - rot)) + 1) / 2
    r = r2 + (r1 - r2) * t ** 1.6
    return np.stack([np.cos(a) * r, np.sin(a) * r], 1)


def heart_pts(n=80):
    t = np.linspace(0, 2 * math.pi, n, endpoint=False)
    x = 16 * np.sin(t) ** 3
    y = -(13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t))
    return np.stack([x, y + 2], 1) / 17.0


def drop_pts(n=60):
    """Tear drop with the tip up: tip at y=-1, round bottom at y=+1, width ~1.3."""
    t = np.linspace(0, 2 * math.pi, n, endpoint=False)
    x = np.sin(t) * (1 - np.cos(t)) * 0.5 * 1.3
    y = -np.cos(t)
    return np.stack([x, y], 1)


def leaf_pts(n=50, w=0.45):
    t = np.linspace(0, 2 * math.pi, n, endpoint=False)
    x = np.cos(t)
    y = np.sin(t) * w * (1 - 0.25 * np.cos(t)) * np.abs(np.sin(t)) ** 0.15
    return np.stack([x, y], 1)


def rrect_pts(w, h, r, n=8):
    r = min(r, w / 2, h / 2)
    pts = []
    for cx, cy, a0 in ((w / 2 - r, -h / 2 + r, -math.pi / 2), (w / 2 - r, h / 2 - r, 0),
                       (-w / 2 + r, h / 2 - r, math.pi / 2), (-w / 2 + r, -h / 2 + r, math.pi)):
        for i in range(n + 1):
            a = a0 + i * (math.pi / 2) / n
            pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return np.array(pts)


def wobble(pts, amt, seed=0, freq=5):
    """Hand-cut irregularity: push points in/out along the radius by a smooth random function."""
    p = np.asarray(pts, np.float64)
    c = p.mean(0)
    d = p - c
    ang = np.arctan2(d[:, 1], d[:, 0])
    r = np.random.default_rng(abs(int(seed)))
    f = np.zeros(len(p))
    for k in range(1, freq + 1):
        f += r.normal() / k * np.sin(k * ang + r.random() * 6.28)
    return c + d * (1 + amt * f)[:, None]


def bezier(p0, p1, p2, n=24):
    t = np.linspace(0, 1, n)[:, None]
    p0, p1, p2 = (np.asarray(v, float) for v in (p0, p1, p2))
    return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2


def arc_pts(r, a0, a1, n=32, cx=0.0, cy=0.0):
    a = np.linspace(a0, a1, n)
    return np.stack([cx + np.cos(a) * r, cy + np.sin(a) * r], 1)


def cloud_parts(w, h, seed=0, n=6):
    """Circles making a cloud of width w, height h around (0,0): list of (x, y, r)."""
    r = np.random.default_rng(seed)
    out = [(0.0, h * 0.12, h * 0.42)]
    for i in range(n):
        u = (i + 0.5) / n - 0.5
        rr = h * (0.28 + 0.22 * (1 - abs(u) * 1.6)) * (0.85 + 0.3 * r.random())
        out.append((u * (w - rr * 1.2), h * 0.12 - rr * 0.35 * (1 - abs(u) * 1.5) - 0.05 * h * r.random(), rr))
    out.append((-w * 0.3, h * 0.25, h * 0.3))
    out.append((w * 0.3, h * 0.25, h * 0.3))
    return out


# ---------------------------------------------------------------- piece

class Piece:
    """A felt piece made of layers; each layer is felted (bevel+shadow) on top of the previous ones.
    Coordinates are pixels around the piece origin (or absolute frame pixels when rendered with frame=)."""

    def __init__(self):
        self.layers = []
        self.layer()

    def layer(self, depth=1.0, alpha=1.0, bevel=None, shadow=1.0, fuzz=1.0, flat=False, kind=None):
        self.cur = dict(parts=[], depth=depth, alpha=alpha, bevel=bevel, shadow=shadow, fuzz=fuzz, flat=flat, kind=kind)
        self.layers.append(self.cur)
        return self

    def poly(self, pts, col):
        self.cur['parts'].append(('poly', np.asarray(pts, np.float64), _c255(col), 0))
        return self

    def circle(self, x, y, r, col):
        return self.poly(ellipse_pts(r) + (x, y), col)

    def ellipse(self, x, y, rx, ry, col, ang=0.0):
        return self.poly(xform(ellipse_pts(rx, ry), ang=ang, tx=x, ty=y), col)

    def hole(self, pts):
        """Cut a hole (alpha 0) through what this layer has drawn so far."""
        self.cur['parts'].append(('hole', np.asarray(pts, np.float64), (0, 0, 0), 0))
        return self

    def stroke(self, pts, w, col, closed=False):
        p = np.asarray(pts, np.float64)
        if closed:
            p = np.vstack([p, p[:1]])
        self.cur['parts'].append(('line', p, _c255(col), w))
        return self

    def stitch(self, pts, col, w=2.2, dash=7.0, gap=5.0, closed=True):
        """Running stitch along a polyline (light thread on felt)."""
        p = np.asarray(pts, np.float64)
        if closed:
            p = np.vstack([p, p[:1]])
        self.cur['parts'].append(('stitch', p, _c255(col), (w, dash, gap)))
        return self

    def stitch_inset(self, pts, inset, col, **kw):
        """Stitch a copy of a convex-ish outline pulled `inset` px towards its centroid."""
        p = np.asarray(pts, np.float64)
        c = p.mean(0)
        d = p - c
        L = np.hypot(d[:, 0], d[:, 1]) + 1e-6
        q = c + d * np.clip((L - inset) / L, 0, 1)[:, None]
        return self.stitch(q, col, **kw)

    # ---- raster
    def bbox(self):
        xs, ys = [], []
        for L in self.layers:
            for kind, p, col, w in L['parts']:
                ww = (w if kind == 'line' else (w[0] if kind == 'stitch' else 0)) / 2 + 1
                xs += [p[:, 0].min() - ww, p[:, 0].max() + ww]
                ys += [p[:, 1].min() - ww, p[:, 1].max() + ww]
        if not xs:
            return None
        return min(xs), min(ys), max(xs), max(ys)

    def render(self, S=1.343, frame=None, seed=0, ss=2):
        """-> Sprite. S = frame height / 804 (felt sizes are tuned for 804 px).
        frame=(W,H): coordinates are absolute and the sprite is clipped to the frame."""
        bb = self.bbox()
        if bb is None:
            return None
        size = max(4.0, min(bb[2] - bb[0], bb[3] - bb[1]))
        sd = float(np.clip(size / (34 * S), 0.35, 1.0))  # small bits cast smaller shadows
        maxd = max(L['depth'] * L['shadow'] for L in self.layers)
        m = int(math.ceil((6 * S * sd * 2.6 + 7 * S * sd) * maxd + 4 + 26 * S * sd))  # felt v2+: room for fibres and AO
        x0, y0, x1, y1 = int(math.floor(bb[0])) - m, int(math.floor(bb[1])) - m, int(math.ceil(bb[2])) + m, int(math.ceil(bb[3])) + m
        if frame is not None:
            x0, y0, x1, y1 = max(0, x0), max(0, y0), min(frame[0], x1), min(frame[1], y1)
            if x1 - x0 < 2 or y1 - y0 < 2:
                return None
        w, h = x1 - x0, y1 - y0
        P = np.zeros((h, w, 4), np.float32)
        big = w * h > 400_000
        if big:
            ss = 1
        gr, mot = _grain_crop(h, w, seed)
        for li, L in enumerate(self.layers):
            if not L['parts']:
                continue
            first = L['parts'][0][2]
            im = Image.new('RGB', (w * ss, h * ss), first)
            al = Image.new('L', (w * ss, h * ss), 0)
            dr, da = ImageDraw.Draw(im), ImageDraw.Draw(al)
            for kind, p, col, wd in L['parts']:
                q = (p - (x0, y0)) * ss
                pts = [tuple(v) for v in q]
                if kind == 'poly':
                    if len(pts) >= 3:
                        dr.polygon(pts, fill=col)
                        da.polygon(pts, fill=255)
                elif kind == 'hole':
                    da.polygon(pts, fill=0)
                elif kind == 'line':
                    lw = max(1, int(round(wd * ss)))
                    dr.line(pts, fill=col, width=lw, joint='curve')
                    da.line(pts, fill=255, width=lw, joint='curve')
                    r = lw / 2
                    for e in (pts[0], pts[-1]):
                        dr.ellipse((e[0] - r, e[1] - r, e[0] + r, e[1] + r), fill=col)
                        da.ellipse((e[0] - r, e[1] - r, e[0] + r, e[1] + r), fill=255)
                elif kind == 'stitch':
                    sw, dash, gap = wd
                    _draw_stitch(dr, q, col, sw * ss, dash * ss, gap * ss)
            if ss > 1:
                im = im.reduce(ss)
                al = al.reduce(ss)
            c = np.asarray(im, np.float32) / 255.0
            a = np.asarray(al, np.float32) / 255.0
            if big:
                a = gaussian_filter(a, 0.7)
            P = _felt_layer(P, c, a, L, S, sd, gr, mot, seed=seed * 31 + li)
        return Sprite(P, -x0, -y0) if frame is None else Sprite(P, -x0, -y0)


def _draw_stitch(dr, q, col, sw, dash, gap):
    seg = np.diff(q, axis=0)
    L = np.hypot(seg[:, 0], seg[:, 1])
    tot = L.sum()
    if tot < 1:
        return
    cum = np.concatenate([[0], np.cumsum(L)])
    period = dash + gap
    s = gap / 2
    while s < tot:
        e = min(tot, s + dash)
        ts = np.linspace(s, e, 4)
        xs = np.interp(ts, cum, q[:, 0])
        ys = np.interp(ts, cum, q[:, 1])
        dr.line(list(zip(xs, ys)), fill=col, width=max(1, int(round(sw))))
        s += period


def _felt_layer(P, c, a, L, S, sd, gr, mot, seed=0):
    """Felt one layer of a sprite onto the premultiplied sprite array P. felt v2+ (feltlook): fibre edge, stray
    hairs, wool micro-fibres, heather, pillowy volume and AO; the old flat bevel is kept as felt_layer_v1."""
    if L['flat'] or not USE_FELT2:
        return _felt_layer_v1(P, c, a, L, S, sd, gr, mot)
    if a.max() < 0.05:
        return P
    kind = L.get('kind') or ('fine' if L['fuzz'] <= 0.3 else (KIND_HINT['kind'] if sd > 0.5 and KIND_HINT['kind'] else 'felt'))
    R = FL.felt_arrays(c, a, L['depth'] * (0.5 + 0.5 * sd), kind, S, np.random.default_rng(seed + 7), 0, 0,
                       shadow_k=L['shadow'] * 1.05, ao_k=L['shadow'], fibres=sd > 0.3)
    if R is None:
        return P
    k = L['alpha']
    if k < 1:
        R['a'] = R['a'] * k
        R['halo'] = R['halo'] * k
        R['sh'] = R['sh'] * k
        if R['fib'] is not None:
            R['fib'] = (R['fib'][0] * k, R['fib'][1] * k)
    return FL.composite_premult(P, R, shadow_alpha=True)


def _felt_layer_v1(P, c, a, L, S, sd, gr, mot):
    # fuzzy fibrous edge
    if L['fuzz'] > 0:
        edge = 4 * a * (1 - a)
        a = np.clip(a + 0.45 * L['fuzz'] * edge * gr * 0.6, 0, 1)
    ys, xs = np.nonzero(a > 0.5)
    if len(ys):
        span = min(ys.max() - ys.min() + 1, xs.max() - xs.min() + 1)
    else:
        span = 8
    sb = L['bevel'] if L['bevel'] is not None else min(9 * S, 0.3 * span)
    sb = max(1.0, sb)
    hgt = blur(a, sb)
    gy, gx = np.gradient(hgt)
    light = -(gx * 0.7 + gy * 0.7) * 2.45 * sb * depth * (0.45 + 0.55 * sd)
    rim = np.clip(1 - hgt * 1.8, 0, 1) * a
    shade = 1 + np.clip(light, -0.35, 0.35) - 0.18 * rim * depth
    shade *= 1 + 0.06 * gr + 0.03 * mot
    col = np.clip(c * shade[..., None], 0, 1)
    la = a * L['alpha']
    # drop shadow (semi-transparent black under the piece)
    sdep = depth * L['shadow']
    if sdep > 0:
        off = int(round(7 * S * sd * sdep))
        sh = blur(a, 6 * S * sd)
        sh2 = np.zeros_like(sh)
        dx = off // 2
        if off > 0:
            sh2[off:, dx:] = sh[:sh.shape[0] - off, :sh.shape[1] - dx]
        else:
            sh2 = sh
        sa = np.clip(sh2 * 0.38 * min(1.4, sdep) * L['alpha'], 0, 1)
        P[..., :3] *= (1 - sa[..., None])
        P[..., 3] = sa + P[..., 3] * (1 - sa)
    P[..., :3] = col * la[..., None] + P[..., :3] * (1 - la[..., None])
    P[..., 3] = la + P[..., 3] * (1 - la)
    return P


class Sprite:
    __slots__ = ('P', 'ox', 'oy')

    def __init__(self, P, ox, oy):
        self.P, self.ox, self.oy = P, ox, oy


# ---------------------------------------------------------------- canvas

class Canvas:
    """Premultiplied float RGBA frame."""

    def __init__(self, W, H):
        self.W, self.H = W, H
        self.P = np.zeros((H, W, 4), np.float32)

    def put(self, spr, x, y, op=1.0):
        if spr is None or op <= 0.003:
            return
        h, w = spr.P.shape[:2]
        X0 = int(round(x - spr.ox))
        Y0 = int(round(y - spr.oy))
        sx0, sy0 = max(0, -X0), max(0, -Y0)
        dx0, dy0 = max(0, X0), max(0, Y0)
        dx1, dy1 = min(self.W, X0 + w), min(self.H, Y0 + h)
        if dx1 <= dx0 or dy1 <= dy0:
            return
        s = spr.P[sy0:sy0 + (dy1 - dy0), sx0:sx0 + (dx1 - dx0)]
        d = self.P[dy0:dy1, dx0:dx1]
        if op < 1:
            s = s * op
        d *= (1 - s[..., 3:4])
        d += s

    def put_abs(self, spr, op=1.0):
        self.put(spr, 0, 0, op)

    def glow(self, x, y, r, col, strength=0.6):
        """Soft translucent halo (not felt): a gaussian spot of colour."""
        r = max(2.0, r)
        x0, x1 = int(max(0, x - 2.5 * r)), int(min(self.W, x + 2.5 * r + 1))
        y0, y1 = int(max(0, y - 2.5 * r)), int(min(self.H, y + 2.5 * r + 1))
        if x1 <= x0 or y1 <= y0:
            return
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        a = np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * (r * 0.8) ** 2)) * strength
        c = np.array(rgb(col), np.float32)
        d = self.P[y0:y1, x0:x1]
        d *= (1 - a[..., None])
        d[..., :3] += c * a[..., None]
        d[..., 3] += a

    def fill(self, col, alpha):
        c = np.array(rgb(col), np.float32)
        self.P *= (1 - alpha)
        self.P[..., :3] += c * alpha
        self.P[..., 3] += alpha

    def image(self):
        P = self.P
        a = np.clip(P[..., 3:4], 0, 1)
        c = np.where(a > 1e-4, P[..., :3] / np.maximum(a, 1e-4), 0)
        out = np.concatenate([np.clip(c, 0, 1), a], 2)
        return Image.fromarray((out * 255 + 0.5).astype(np.uint8), 'RGBA')


# ---------------------------------------------------------------- background for previews

def felt_background(W, H, col='#a39c90'):
    """Neutral felt cloth (mid-tone, so both white snow and dark smoke read on it)."""
    rng = np.random.default_rng(11)
    c = np.array(rgb(col), np.float32)
    g, m = _grain_crop(H, W, 3) if H <= 1200 and W <= 2100 else _grain_crop(H, W, 3)
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    vign = 1 - 0.12 * ((np.linspace(-1, 1, W, dtype=np.float32)[None, :]) ** 2) - 0.08 * (yy - 0.4) ** 2
    shade = (1 + 0.06 * g + 0.012 * m) * vign
    img = np.clip(c[None, None, :] * shade[..., None], 0, 1)
    # a lighter felt panel for the floor with a stitched seam
    fl = int(H * 0.8)
    img[fl:] = np.clip(img[fl:] * np.array([1.08, 1.06, 1.0]), 0, 1)
    img[fl - 2:fl + 1] *= 0.86
    im = Image.fromarray((img * 255).astype(np.uint8), 'RGB')
    d = ImageDraw.Draw(im)
    st = max(2, int(H / 400))
    for x in range(0, W, 7 * st):
        d.line([(x, fl + 4 * st), (x + 4 * st, fl + 4 * st)], fill=(222, 214, 196), width=st)
    return im
