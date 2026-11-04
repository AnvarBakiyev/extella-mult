"""Code-generated felt effects library.

Every effect is a function  fx(t, params=None) -> PIL RGBA image (1920x1080 by default, transparent, with
felt drop shadows baked in as semi-transparent black). No AI images, no external assets: every piece is drawn
from code and felted by feltcore (same recipe as handler/felt.py::felt_composite, cached per sprite).

    import effects_lib as E
    img = E.snow_light(1.25, {'seed': 3})          # one frame at t=1.25 s
    E.EFFECTS['snow_light']                         # metadata: about, params, loop, dur, fps, cat
    E.render('fireworks', t, {'W': 960, 'H': 540})  # any size; sizes scale with H

Common params: seed (deterministic), W, H, dur (loop length / one-shot length, s), at=(x, y) anchor in 0..1
for effects that come from a point, count / density, colour overrides where listed.
Looping effects satisfy fx(t) == fx(t + dur).
"""
import math
import zlib
import numpy as np
import feltcore as F  # noqa: E402
from feltcore import (Piece, Canvas, rgb, mix, lighter, darker, xform, ellipse_pts, star_pts, round_star_pts,
                      heart_pts, drop_pts, leaf_pts, rrect_pts, wobble, bezier, arc_pts, cloud_parts)

TAU = 2 * math.pi
EFFECTS = {}
_CACHE = {}


def effect(name, cat, about, dur=3.0, loop=True, fps=24, scale=1.0, **params):
    """Register an effect. scale<1: the stored PNG sequence is rendered smaller (big full-frame effects)."""
    def deco(fn):
        EFFECTS[name] = dict(fn=fn, cat=cat, about=about, dur=dur, loop=loop, fps=fps, scale=scale, params=params)

        def fx(t, params=None):
            return render(name, t, params)
        fx.__name__ = name
        fx.__doc__ = about
        return fx
    return deco


def render(name, t, params=None):
    e = EFFECTS[name]
    p = dict(seed=1, W=1920, H=1080, dur=e['dur'])
    p.update(e['params'])
    if params:
        p.update(params)
    if F.KIND_HINT.get('fx') != name:  # felt v2+: which wool this effect is made of; sprites are cached per kind
        F.KIND_HINT['fx'] = name
        F.KIND_HINT['kind'] = next((k for k, keys in FX_KIND.items() if name in keys), None)
        _CACHE.clear()
    c = C(name, t, p)
    e['fn'](c)
    return c.cv.image()


# felt v2+: effects made of loose carded wool (big fluffy fibres) or snow wool; the rest is plain felt
FX_KIND = {
    'cloud': ('clouds_drift', 'rain_cloud', 'smoke_puffs', 'chimney_smoke', 'steam', 'explosion_puff', 'poof_vanish',
              'dust_cloud', 'thought_bubble', 'grawlix_cloud', 'fog_drift', 'anger_steam', 'lightning_flash'),
    'snow': ('snow_light', 'snow_heavy', 'blizzard'),
}


def clear_cache():
    _CACHE.clear()


def _h(key):
    return zlib.crc32(repr(key).encode()) & 0xffffff


class C:
    """Per-frame context handed to an effect body."""

    def __init__(s, name, t, p):
        s.name, s.p = name, p
        s.D = float(p['dur'])
        s.t = float(t) % s.D if EFFECTS[name]['loop'] else min(float(t), s.D)
        s.f = s.t / s.D
        s.W, s.H = int(p['W']), int(p['H'])
        s.size = float(p.get('size', 1.0))
        s.u = s.H / 1080.0 * s.size
        s.S = s.H / 804.0
        s.seed = int(p['seed'])
        s.cv = Canvas(s.W, s.H)

    # randomness
    def R(s, n, k=0, m=10):
        return np.random.default_rng([s.seed, k]).random((n, m))

    def at(s, default=(0.5, 0.5)):
        x, y = s.p.get('at', default)
        return x * s.W, y * s.H

    # sprites
    def spr(s, key, build):
        k = (s.name, s.W, s.H, s.seed, key)
        if k not in _CACHE:
            if len(_CACHE) > 6000:
                _CACHE.clear()
            pc = build()
            _CACHE[k] = pc.render(s.S, seed=_h(key)) if pc is not None else None
        return _CACHE[k]

    def put(s, key, build, x, y, op=1.0):
        s.cv.put(s.spr(key, build), x, y, op)

    def full(s, piece, op=1.0, key=None):
        """Felt a piece drawn in absolute frame coordinates (big shapes); cached when key is given."""
        if key is not None:
            k = (s.name, s.W, s.H, s.seed, 'full', key)
            if k not in _CACHE:
                _CACHE[k] = piece().render(s.S, frame=(s.W, s.H), seed=_h(key))
            spr = _CACHE[k]
        else:
            spr = piece.render(s.S, frame=(s.W, s.H), seed=_h((s.name, round(s.t, 3))))
        s.cv.put(spr, 0, 0, op)

    # time
    def emit(s, n, life, k=0):
        """Loopable particle stream: n spawns per loop, each living `life` s. Yields (i, age).
        A particle i appears at ages base, base+D, ... so the stream is periodic in D."""
        for i in range(n):
            a = (s.t - (i + 0.5) * s.D / n) % s.D
            while a < life:
                yield i, a
                a += s.D

    def osc(s, cycles=1, ph=0.0):
        """sin wave that loops: `cycles` whole periods per effect duration."""
        return math.sin(TAU * cycles * s.t / s.D + ph)


def qa(a, n=48):
    """Quantise an angle for sprite caching -> (index, angle)."""
    i = int(round(a / TAU * n)) % n
    return i, i * TAU / n


def qv(v, n=8):
    i = int(round(max(0.0, min(1.0, v)) * n))
    return i, i / n


def ease_out(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def ease_in(x):
    x = max(0.0, min(1.0, x))
    return x ** 3


def ease_io(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def back_out(x, k=1.9):
    """Overshoot pop: 0 -> ~1.15 -> 1."""
    x = max(0.0, min(1.0, x))
    x -= 1
    return 1 + x * x * ((k + 1) * x + k)


def fade(age, life, fin=0.12, fout=0.25):
    """Opacity envelope over a particle's life (fractions of life)."""
    u = age / life
    a = 1.0
    if fin > 0 and u < fin:
        a = u / fin
    if fout > 0 and u > 1 - fout:
        a = min(a, (1 - u) / fout)
    return max(0.0, min(1.0, a))


def wrap(x, lo, hi):
    return lo + (x - lo) % (hi - lo)


# palette
WHITE = '#f7f3ea'
CREAM = '#efe6cf'
SKY = '#8fc3ec'
BLUE = '#5f9fd8'
DEEP = '#3f6fae'
RED = '#e0543f'
ORANGE = '#f08a3a'
YELLOW = '#f6c94c'
GOLD = '#e9b53a'
PINK = '#f28fb0'
ROSE = '#e8607f'
PURPLE = '#9a74cf'
VIOLET = '#6d55b0'
TEAL = '#4fb8ad'
GREEN = '#7cbf5a'
LEAF = '#5f9e46'
BROWN = '#8a5a3a'
GREY = '#b9b4ad'
DARK = '#4a4450'
INK = '#3a3440'
FESTIVE = ('#e0543f', '#f6c94c', '#5f9fd8', '#7cbf5a', '#f28fb0', '#9a74cf', '#4fb8ad', '#f08a3a')


# ============================================================ shared pieces

def p_blob(r, col, seed=0, amt=0.06, stitch=True, inset=None):
    pts = wobble(ellipse_pts(r), amt, seed)
    p = Piece().poly(pts, col)
    if stitch and r > 22:
        p.stitch_inset(pts, inset or max(5, r * 0.18), lighter(col, 0.45), w=max(1.6, r * 0.035), dash=max(4, r * 0.12), gap=max(3, r * 0.09))
    return p


def p_cloud(w, h, col, seed=0, alpha=1.0, stitch=False, depth=1.0):
    p = Piece()
    p.layer(alpha=alpha, depth=depth)
    for x, y, r in cloud_parts(w, h, seed):
        p.poly(wobble(ellipse_pts(r) + (x, y), 0.03, seed + abs(int(x))), col)
    if stitch:
        pass
    return p


def p_drop(size, col, ang=0.0, stretch=1.0, hi=True):
    pts = xform(drop_pts(), size * 0.62, size * stretch, ang)
    p = Piece().poly(pts, col)
    if hi and size > 9:
        p.layer(depth=0.3, shadow=0)
        p.ellipse(-size * 0.18 * math.cos(ang), size * 0.25 * stretch, size * 0.12, size * 0.22 * stretch, lighter(col, 0.6), ang)
    return p


def p_star(r, col, n=5, inner=0.48, ang=0.0, soft=True, stitch=True):
    pts = round_star_pts(n, r, r * inner, -math.pi / 2 + ang) if soft else star_pts(n, r, r * inner, -math.pi / 2 + ang)
    p = Piece().poly(pts, col)
    if stitch and r > 26:
        p.stitch_inset(pts, max(5, r * 0.2), lighter(col, 0.5), w=max(1.6, r * 0.03), dash=max(4, r * 0.1), gap=max(3, r * 0.08))
    return p


def p_spark(r, col, ang=0.0):
    """Four-point twinkle star."""
    pts = [(0, -1), (0.2, -0.2), (1, 0), (0.2, 0.2), (0, 1), (-0.2, 0.2), (-1, 0), (-0.2, -0.2)]
    return Piece().poly(xform(pts, r, ang=ang), col)


def p_heart(r, col, ang=0.0, stitch=True):
    pts = xform(heart_pts(), r, ang=ang)
    p = Piece().poly(pts, col)
    if stitch and r > 24:
        p.stitch_inset(pts, max(5, r * 0.16), lighter(col, 0.5), w=max(1.6, r * 0.03), dash=max(4, r * 0.11), gap=max(3, r * 0.08))
    return p


def p_leaf(r, col, ang=0.0, sy=1.0, vein=True):
    pts = xform(leaf_pts(), r, r * sy, ang)
    p = Piece().poly(pts, col)
    if vein and r > 14:
        p.layer(depth=0.25, shadow=0)
        p.stroke(xform([(-0.85, 0), (0.85, 0)], r, r * sy, ang), max(1.5, r * 0.07), darker(col, 0.25))
    return p


def p_petal(r, col, ang=0.0, sy=1.0):
    t = np.linspace(0, TAU, 40, endpoint=False)
    x = np.cos(t)
    y = np.sin(t) * 0.55 * (1 + 0.35 * np.cos(t))
    pts = np.stack([x, y], 1)
    pts[:, 0] += 0.12 * (np.abs(np.sin(t)) < 0.25) * (np.cos(t) > 0) * -1  # small notch at the tip
    return Piece().poly(xform(pts, r, r * sy, ang), col)


def p_coin(r, sx=1.0, col=GOLD):
    p = Piece().poly(ellipse_pts(r * max(0.08, sx), r), col)
    if sx > 0.3:
        p.layer(depth=0.45, shadow=0.3)
        p.poly(ellipse_pts(r * 0.68 * sx, r * 0.68), lighter(col, 0.18))
        if r > 16:
            p.stitch(ellipse_pts(r * 0.84 * sx, r * 0.84), darker(col, 0.2), w=max(1.4, r * 0.05), dash=r * 0.18, gap=r * 0.12)
    else:
        p.layer(depth=0.3, shadow=0)
        p.poly(ellipse_pts(r * max(0.05, sx * 0.6), r * 0.92), darker(col, 0.18))
    return p


def p_ring(r, w, col, n=None, ry=None):
    """Closed ring stroke (felt band)."""
    ry = r if ry is None else ry
    pts = ellipse_pts(r, ry, n)
    return Piece().stroke(np.vstack([pts, pts[:1]]), w, col)


def p_bolt(h, col=YELLOW, ang=0.0):
    pts = [(-0.10, -1.0), (0.32, -1.0), (0.08, -0.25), (0.36, -0.25), (-0.22, 1.0), (-0.02, 0.05), (-0.30, 0.05)]
    pts = xform(pts, h, ang=ang)
    p = Piece().poly(pts, col)
    if h > 50:
        p.stitch_inset(pts, h * 0.07, lighter(col, 0.5), w=max(1.6, h * 0.02), dash=h * 0.06, gap=h * 0.05)
    return p


# ============================================================ WEATHER

@effect('rain_light', 'weather', 'Light felt rain: thin blue drops falling straight down.', dur=2.0, density=70)
def _rain_light(c):
    R = c.R(200)
    u = c.u
    for i, age in c.emit(int(c.p['density']), 1.0):
        r = R[i]
        sp = (1300 + 300 * r[1]) * u
        x = r[0] * (c.W + 100 * u) - 50 * u
        y = -40 * u + age * sp
        if y > c.H + 40 * u:
            continue
        sz = int(r[2] * 3)
        c.put(('d', sz), lambda sz=sz: p_drop((10 + 3 * sz) * u, SKY, stretch=1.9, hi=False), x, y, 0.92)


def _splash_crown(c, key, x, y, k, sz, col=SKY):
    """Small splash at the floor: two droplets + flat ellipse ring, k in 0..1."""
    kk, kq = qv(k, 6)
    def b(kq=kq):
        p = Piece()
        w = sz * (0.6 + 1.2 * kq)
        p.poly(ellipse_pts(w, w * 0.28), lighter(col, 0.1))
        p.layer(depth=0.4, shadow=0)
        p.poly(ellipse_pts(w * 0.62, w * 0.16), darker(col, 0.05))
        return p
    c.put((key, kk), b, x, y, 1 - k)
    for side in (-1, 1):
        dx = side * sz * (0.5 + 1.6 * k)
        dy = -sz * 3.2 * k * (1 - k) * 2.2
        c.put((key + 'd',), lambda: Piece().circle(0, 0, sz * 0.32, col), x + dx, y + dy, 1 - k * 0.7)


@effect('rain_heavy', 'weather', 'Heavy felt rain: dense slanted drops with little splash crowns on the floor.', dur=2.0,
        density=340, floor=0.92)
def _rain_heavy(c):
    R = c.R(400)
    u = c.u
    ang = 0.16
    fl = c.p['floor'] * c.H
    for i, age in c.emit(int(c.p['density']), 1.1):
        r = R[i]
        sp = (1650 + 400 * r[1]) * u
        ystop = fl - r[3] * 0.22 * c.H
        tfall = (ystop + 60 * u) / sp
        x0 = r[0] * (c.W + 400 * u) - 100 * u
        if age < tfall:
            y = -60 * u + age * sp
            x = x0 - math.sin(ang) * age * sp
            sz = int(r[2] * 3)
            c.put(('d', sz), lambda sz=sz: p_drop((10 + 3 * sz) * u, SKY, ang=ang, stretch=2.3, hi=False), x, y, 0.95)
        elif age < tfall + 0.22 and r[4] < 0.6:
            x = x0 - math.sin(ang) * tfall * sp
            _splash_crown(c, 'sp', x, ystop, (age - tfall) / 0.22, 9 * u)


@effect('rain_wind', 'weather', 'Wind-driven rain: long drops at a steep angle, gusting.', dur=2.0, density=150)
def _rain_wind(c):
    R = c.R(300)
    u = c.u
    gust = 0.1 * c.osc(1)
    for i, age in c.emit(int(c.p['density']), 1.0):
        r = R[i]
        sp = (1500 + 300 * r[1]) * u
        ang = 0.55 + gust + 0.05 * r[5]
        x = r[0] * (c.W + 1100 * u) - 1000 * u * 0 - 200 * u + age * sp * math.sin(ang)
        y = -60 * u + age * sp * math.cos(ang)
        if y > c.H + 60 * u:
            continue
        sz = int(r[2] * 3)
        ia, a = qa(-ang, 72)
        c.put(('d', sz, ia), lambda sz=sz, a=a: p_drop((9 + 3 * sz) * u, SKY, ang=a, stretch=2.6, hi=False), x, y, 0.9)


def p_flake(r, col=WHITE, ang=0.0, kind=0):
    """Snowflake: kind 0 round felt dot, 1 six-arm crystal, 2 soft star."""
    if kind == 0:
        return Piece().poly(wobble(ellipse_pts(r), 0.05, int(r * 10)), col)
    if kind == 2:
        return Piece().poly(round_star_pts(6, r, r * 0.6, ang), col)
    p = Piece()
    w = max(2.0, r * 0.2)
    for k in range(6):
        a = ang + k * TAU / 6
        ca, sa = math.cos(a), math.sin(a)
        p.stroke([(0, 0), (ca * r, sa * r)], w, col)
        for f in (0.5, 0.75):
            bx, by = ca * r * f, sa * r * f
            for s in (-1, 1):
                b = a + s * 0.8
                p.stroke([(bx, by), (bx + math.cos(b) * r * 0.3, by + math.sin(b) * r * 0.3)], w * 0.85, col)
    p.circle(0, 0, w * 1.3, col)
    return p


@effect('snow_light', 'weather', 'Gentle snowfall: soft round felt flakes swaying as they fall.', dur=4.0, density=70)
def _snow_light(c):
    R = c.R(300)
    u = c.u
    life = 7.0
    for i, age in c.emit(int(c.p['density']), life):
        r = R[i]
        sp = (150 + 120 * r[1]) * u
        depth = 0.5 + r[2]
        x = r[0] * c.W + 22 * u * math.sin(age * (1 + r[3]) + r[4] * 6) + (r[6] - 0.5) * 30 * u * age
        y = -30 * u + age * sp * depth
        if y > c.H + 30 * u:
            continue
        kind = 2 if r[5] > 0.85 else 0
        sz = int(r[2] * 4)
        c.put(('f', sz, kind), lambda sz=sz, kind=kind: p_flake((5 + 3 * sz) * u * (1.6 if kind else 1), WHITE, 0, kind), x, y)


@effect('snow_heavy', 'weather', 'Heavy snow: large six-arm felt crystals turning slowly among many small flakes.',
        dur=4.0, density=110)
def _snow_heavy(c):
    R = c.R(400)
    u = c.u
    for i, age in c.emit(int(c.p['density']), 6.5):
        r = R[i]
        big = r[5] > 0.72
        sp = (170 + 140 * r[1]) * u * (1.25 if big else 1)
        x = r[0] * c.W + 30 * u * math.sin(age * 0.9 + r[4] * 6) + (r[6] - 0.3) * 40 * u * age
        y = -60 * u + age * sp
        if y > c.H + 60 * u:
            continue
        if big:
            ia, a = qa(age * (0.6 if r[7] > 0.5 else -0.6) + r[8] * 6, 30)
            ia %= 10  # six-fold symmetry
            sz = int(r[2] * 3)
            c.put(('c', sz, ia), lambda sz=sz, a=a: p_flake((26 + 8 * sz) * u, WHITE, a, 1), x, y)
        else:
            sz = int(r[2] * 3)
            c.put(('f', sz), lambda sz=sz: p_flake((6 + 3 * sz) * u, WHITE, 0, 0), x, y)


def _haze_strip(c, key, y, h, col, alpha, period, offset, seed):
    """A horizontal band of translucent felt lumps, periodic in x with `period` px; drawn shifted by offset."""
    W = c.W
    reps = int(math.ceil((W + period) / period)) + 1

    def b():
        p = Piece()
        p.layer(alpha=alpha, depth=0.5, shadow=0.4)
        rr = np.random.default_rng(seed)
        nl = max(5, int(period / h * 2.2))
        lumps = [((j + 0.6 * rr.random()) * period / nl, (rr.random() - 0.5) * h * 0.55, h * (0.22 + 0.3 * rr.random()),
                  1.4 + 1.2 * rr.random()) for j in range(nl)]
        for k in range(reps):
            for lx, ly, lr, ex in lumps:
                p.poly(wobble(xform(ellipse_pts(lr * ex, lr), tx=k * period + lx, ty=ly), 0.04, int(lx)), col)
        return p
    x = -period + (offset % period)
    c.put(key, b, x, y)


@effect('blizzard', 'weather', 'Blizzard: dense fast snow driven sideways, wind haze bands and a white veil.', dur=2.0,
        fps=24, density=320)
def _blizzard(c):
    R = c.R(600)
    u = c.u
    c.cv.fill(WHITE, 0.10)
    for j in range(3):
        per = c.W / (1 + j)
        _haze_strip(c, ('hz', j), c.H * (0.25 + 0.3 * j), 140 * u, WHITE, 0.28, per, per * c.t / c.D * (2 - (j % 2)), 40 + j)
    for i, age in c.emit(int(c.p['density']), 1.2):
        r = R[i]
        sp = (1400 + 700 * r[1]) * u
        x = -200 * u + age * sp
        y = r[0] * (c.H + 300 * u) - 300 * u + age * sp * 0.35 + 20 * u * math.sin(age * 9 + r[3] * 6)
        if x > c.W + 40 * u:
            continue
        sz = int(r[2] * 3)
        c.put(('f', sz), lambda sz=sz: Piece().poly(xform(ellipse_pts(1.0), (6 + 3 * sz) * u * 1.6, (6 + 3 * sz) * u, 0.33), WHITE), x, y)


@effect('fog_drift', 'weather', 'Fog: layers of sheer felt mist drifting sideways at different speeds (parallax).',
        dur=6.0, fps=12, scale=0.5)
def _fog(c):
    u = c.u
    layers = [(0.30, 260, 0.30, 1, '#e9e6e0'), (0.55, 300, 0.36, -1, '#f1eee8'), (0.80, 340, 0.45, 2, '#f6f3ee')]
    for j, (y, h, al, sp, col) in enumerate(layers):
        per = c.W / 2
        _haze_strip(c, ('fg', j), c.H * y, h * u, col, al, per, per * c.t / c.D * sp, 70 + j)


@effect('wind_leaves', 'weather', 'Wind with leaves: autumn leaves tumbling across the frame with curly wind strokes.',
        dur=3.0, density=42)
def _wind_leaves(c):
    R = c.R(200)
    u = c.u
    cols = ('#e8833a', '#d9542f', '#f2b64a', '#a8c45a', '#c9772f')
    # wind strokes
    for i, age in c.emit(4, 1.2, k=1):
        r = R[100 + i]
        y = (0.15 + 0.7 * r[0]) * c.H
        x = -500 * u + age * 1900 * u
        op = fade(age, 1.2, 0.2, 0.3) * 0.75
        c.put(('w', i % 2), lambda i=i: _p_wind_stroke(420 * u, 26 * u, i % 2), x, y, op)
    for i, age in c.emit(int(c.p['density']), 2.4):
        r = R[i]
        sp = (900 + 500 * r[1]) * u
        x = -80 * u + age * sp
        y = r[0] * c.H * 0.9 + 60 * u * math.sin(age * 3 + r[3] * 6) + age * 60 * u
        if x > c.W + 80 * u:
            continue
        ia, a = qa(age * (5 + 3 * r[4]) + r[5] * 6, 24)
        iv, sy = qv(abs(math.cos(age * 4 + r[6] * 6)), 4)
        sz = int(r[2] * 2)
        col = cols[i % 5]
        c.put(('l', sz, ia, iv, i % 5), lambda sz=sz, a=a, sy=sy, col=col: p_leaf((26 + 9 * sz) * u, col, a, 0.25 + 0.75 * sy), x, y)


def _p_wind_stroke(L, w, kind=0):
    """A long thin felt strip with a curl at the end (cartoon wind)."""
    xs = np.linspace(-L / 2, L / 2, 30)
    ys = np.sin(np.linspace(0, math.pi * (1.4 if kind else 1.0), 30)) * w * 0.8
    pts = list(zip(xs, ys))
    cx, cy = L / 2 - w * 0.4, ys[-1] - w * 1.4
    for a in np.linspace(math.pi / 2, math.pi / 2 + 1.7 * math.pi, 22):
        rr = w * 1.4 * (1 - 0.35 * (a - math.pi / 2) / (1.7 * math.pi))
        pts.append((cx + math.cos(a) * rr * -1 + w * 0.0, cy + math.sin(a) * rr))
    p = Piece().layer(alpha=0.9, depth=0.6)
    p.stroke(pts, w * 0.45, '#f4f1ea')
    return p


@effect('wind_gusts', 'weather', 'Cartoon wind gusts: curly white felt strokes sweeping across.', dur=2.0)
def _wind_gusts(c):
    R = c.R(50)
    u = c.u
    for i, age in c.emit(7, 1.0):
        r = R[i]
        y = (0.12 + 0.76 * r[0]) * c.H
        x = -400 * u + age * (2400 + 600 * r[1]) * u
        op = fade(age, 1.0, 0.15, 0.3)
        k = i % 2
        sz = int(r[2] * 2)
        c.put(('w', k, sz), lambda k=k, sz=sz: _p_wind_stroke((340 + 120 * sz) * u, (22 + 6 * sz) * u, k), x, y, op)


@effect('lightning_flash', 'weather', 'Thunderstorm: dark felt cloud, a stitched yellow bolt strikes twice with white flashes.',
        dur=3.0, at=(0.5, 0.18))
def _lightning(c):
    u = c.u
    x0, y0 = c.at()
    t = c.t
    strikes = [(0.55, 0.32), (1.95, 0.22)]
    shake = 0.0
    for s, d in strikes:
        if s <= t < s + d:
            k = (t - s) / d
            c.cv.fill('#fffbe8', 0.55 * (1 - k) ** 1.5 * (1 if int((t - s) * 24) % 3 != 1 else 0.4))
            shake = 1 - k
            ib = 0 if s < 1 else 1
            def b(ib=ib):
                p = p_bolt(300 * u, YELLOW, ang=0.12 if ib else -0.1)
                return p
            c.put(('bolt', ib), b, x0 + (60 * u if ib else -120 * u), y0 + 380 * u, min(1, 3 * (1 - k)))
    dx = shake * 10 * u * math.sin(t * 90)
    c.put('cloud2', lambda: p_cloud(520 * u, 200 * u, '#7b7684', seed=3), x0 + 260 * u + dx * 0.5, y0 - 20 * u + 6 * u * c.osc(1))
    c.put('cloud', lambda: p_cloud(680 * u, 260 * u, '#5d5868', seed=8), x0 - 80 * u + dx, y0 + 30 * u + 8 * u * c.osc(1, 1))


@effect('hail', 'weather', 'Hail: pale felt pellets falling hard and bouncing on the floor.', dur=2.0, density=60, floor=0.9)
def _hail(c):
    R = c.R(200)
    u = c.u
    fl = c.p['floor'] * c.H
    life = 1.6
    for i, age in c.emit(int(c.p['density']), life):
        r = R[i]
        g = 2600 * u
        y_hit = fl - r[3] * 0.08 * c.H
        v0 = 700 * u
        t_hit = (-v0 + math.sqrt(v0 * v0 + 2 * g * (y_hit + 30 * u))) / g
        x = r[0] * c.W
        if age < t_hit:
            y = -30 * u + v0 * age + 0.5 * g * age * age
        else:
            ta = age - t_hit
            vb = (v0 + g * t_hit) * 0.28
            b1 = 2 * vb / g
            if ta < b1:
                y = y_hit - (vb * ta - 0.5 * g * ta * ta)
            else:
                ta2 = ta - b1
                vb2 = vb * 0.35
                b2 = 2 * vb2 / g
                y = y_hit - max(0.0, vb2 * ta2 - 0.5 * g * ta2 * ta2) if ta2 < b2 else y_hit
            x += (r[4] - 0.5) * 120 * u * min(1.0, ta / 0.4)
        op = 1.0 if age < life - 0.25 else (life - age) / 0.25
        sz = int(r[2] * 3)
        c.put(('h', sz), lambda sz=sz: p_blob((7 + 3 * sz) * u, '#e6eef2', seed=sz, stitch=False), x, y, op)


@effect('sandstorm', 'weather', 'Sandstorm: ochre grains and dusty felt bands streaming sideways under a sandy veil.', dur=2.0,
        density=260)
def _sandstorm(c):
    R = c.R(500)
    u = c.u
    c.cv.fill('#d8b47a', 0.22)
    for j in range(3):
        per = c.W / (1 + j % 2)
        _haze_strip(c, ('sb', j), c.H * (0.2 + 0.3 * j), 180 * u, ('#d9b27a', '#caa069', '#e2c08c')[j], 0.33, per,
                    per * c.t / c.D * (1 + (j % 2)), 90 + j)
    cols = ('#c79a5c', '#b5844a', '#dcb680', '#a8763f')
    for i, age in c.emit(int(c.p['density']), 1.0):
        r = R[i]
        sp = (1700 + 700 * r[1]) * u
        x = -60 * u + age * sp
        y = r[0] * c.H + 40 * u * math.sin(age * 6 + r[3] * 6) + age * 120 * u
        if x > c.W + 60 * u:
            continue
        sz = int(r[2] * 3)
        c.put(('g', sz, i % 4), lambda sz=sz, i=i: p_blob((3 + 2.2 * sz) * u, cols[i % 4], seed=i % 4, stitch=False), x, y)


def _rain_from(c, x0, x1, ytop, n, life, k=0):
    R = c.R(200, k)
    u = c.u
    for i, age in c.emit(n, life, k):
        r = R[i]
        sp = (1100 + 200 * r[1]) * u
        x = x0 + r[0] * (x1 - x0)
        y = ytop + age * sp
        op = fade(age, life, 0.1, 0.2)
        c.put(('rd', int(r[2] * 2)), lambda s=int(r[2] * 2): p_drop((9 + 3 * s) * u, SKY, stretch=1.8, hi=False), x, y, op)


@effect('rain_cloud', 'weather', 'A single felt rain cloud bobbing at the top with rain falling from it.', dur=2.0,
        at=(0.5, 0.2))
def _rain_cloud(c):
    u = c.u
    x0, y0 = c.at()
    _rain_from(c, x0 - 220 * u, x0 + 220 * u, y0 + 60 * u, 40, 0.75)
    c.put('cl', lambda: p_cloud(560 * u, 230 * u, '#9aa3b0', seed=5), x0, y0 + 10 * u * c.osc(1))


@effect('sun_rays', 'weather', 'Felt sun: a stitched disc with alternating rays slowly turning and breathing.', dur=4.0,
        at=(0.5, 0.45))
def _sun(c):
    u = c.u
    x0, y0 = c.at()
    n = 12
    rot = TAU / n * 2 * c.f  # two ray-steps per loop
    br = 1 + 0.05 * c.osc(2)
    for k in range(n):
        a = rot + k * TAU / n
        col = YELLOW if k % 2 == 0 else ORANGE
        L = (250 if k % 2 == 0 else 205) * u * br
        ia, aq = qa(a, 144)
        def b(L=L, col=col, aq=aq):
            pts = xform([(0, -26 * u), (L, 0), (0, 26 * u)], ang=aq)
            return Piece().poly(pts, col)
        c.put(('r', k % 2, ia), b, x0 + math.cos(aq) * 120 * u, y0 + math.sin(aq) * 120 * u)
    c.put('disc', lambda: p_blob(165 * u, '#f8d65a', seed=2, amt=0.02), x0, y0)
    c.put('cheek', lambda: Piece().layer(depth=0.4).circle(0, 0, 26 * u, '#f6a06a'), x0 - 70 * u, y0 + 40 * u)
    c.put('cheek2', lambda: Piece().layer(depth=0.4).circle(0, 0, 26 * u, '#f6a06a'), x0 + 70 * u, y0 + 40 * u)


@effect('rainbow_grow', 'weather', 'A felt rainbow sweeps across from left to right, puffy clouds pop at its ends.',
        dur=3.0, loop=False, at=(0.5, 0.82))
def _rainbow(c):
    u = c.u
    x0, y0 = c.at()
    k = ease_io(c.t / (c.D * 0.7))
    cols = ('#e0543f', '#f08a3a', '#f6c94c', '#7cbf5a', '#5f9fd8', '#9a74cf')
    R0 = 620 * u
    bw = 46 * u
    if k > 0.01:
        p = Piece()
        for j, col in enumerate(cols):
            r = R0 - j * bw
            a1 = math.pi + k * math.pi
            pts = np.vstack([arc_pts(r, math.pi, a1, 90, x0, y0), arc_pts(r - bw, a1, math.pi, 90, x0, y0)])
            if j:
                p.layer(depth=0.5, shadow=0.4)
            p.poly(pts, col)
        c.full(p)
    for side, tk in ((-1, 0.05), (1, 0.72)):
        s = back_out((c.t / c.D - tk) / 0.18)
        if s > 0.02:
            si = int(s * 20)
            c.put(('cl', side, si), lambda s=si / 20: p_cloud(330 * u * s, 150 * u * s, WHITE, seed=11 + side),
                  x0 + side * (R0 - 3 * bw), y0 - 10 * u)


@effect('clouds_drift', 'weather', 'Puffy white felt clouds drifting across the sky, looping seamlessly.', dur=6.0,
        fps=12, scale=0.5)
def _clouds_drift(c):
    u = c.u
    for j, (y, w, sp) in enumerate(((0.16, 460, 1), (0.34, 340, 2), (0.10, 300, 1))):
        per = c.W * 0.75 if j != 2 else c.W * 0.5
        n = int(math.ceil(c.W / per)) + 2
        off = (per * sp * c.t / c.D) % per
        for k in range(n):
            x = -per + k * per + off + (0.4 * per if j == 2 else 0)
            c.put(('c', j), lambda j=j, w=w: p_cloud(w * u, w * 0.42 * u, WHITE if j != 2 else '#eef2f6', seed=20 + j),
                  x, y * c.H + 6 * u * c.osc(1, j))


# ============================================================ FIRE AND SMOKE

def p_flame(h, seed, cols=(RED, ORANGE, YELLOW), lean=0.0):
    """Three nested felt flame tongues; seed picks one of the flicker shapes."""
    r = np.random.default_rng(seed)
    p = Piece()
    for j, col in enumerate(cols):
        s = 1 - j * 0.3
        t = np.linspace(0, TAU, 70, endpoint=False)
        base_w = 0.42 * s
        x = np.sin(t) * base_w * (1 - 0.15 * np.cos(t))
        y = -np.cos(t)
        up = y < 0
        k = np.clip(-y, 0, 1)
        x = x * np.where(up, (1 - k ** 1.3), 1.0)
        y = np.where(up, y * (1.25 + 0.25 * r.random()), y * 0.45)
        x = x + np.where(up, (lean + 0.15 * (r.random() - 0.5)) * k ** 2 + 0.06 * np.sin(k * 7 + r.random() * 6) * k, 0)
        pts = np.stack([x * h, (y * s + (1 - s) * 0.45) * h], 1)
        if j:
            p.layer(depth=0.6, shadow=0.35)
        p.poly(pts, col)
    return p


def p_log(L, r, col=BROWN, ang=0.0):
    p = Piece()
    p.poly(xform(rrect_pts(L, 2 * r, r * 0.9), ang=ang), col)
    p.layer(depth=0.4, shadow=0.2)
    end = xform(ellipse_pts(r * 0.75, r * 0.85), ang=ang, tx=math.cos(ang) * (L / 2 - r * 0.6), ty=math.sin(ang) * (L / 2 - r * 0.6))
    p.poly(end, '#d6a36a')
    p.stitch(xform(ellipse_pts(r * 0.4, r * 0.48), ang=ang, tx=math.cos(ang) * (L / 2 - r * 0.6), ty=math.sin(ang) * (L / 2 - r * 0.6)),
             '#8a5a3a', w=2, dash=5, gap=4)
    return p


@effect('campfire', 'fire', 'Campfire: crossed felt logs and stones, flickering three-colour flames, rising embers and glow.',
        dur=2.0, at=(0.5, 0.82))
def _campfire(c):
    u = c.u
    x0, y0 = c.at()
    fi = int(c.t * 12) % 8
    c.cv.glow(x0, y0 - 110 * u, 260 * u, '#ffb648', 0.30 + 0.05 * math.sin(c.t * 37))
    for k, dx in enumerate((-150, -75, 0, 75, 150)):
        c.put(('st', k), lambda k=k: p_blob(42 * u, ('#9a948c', '#857f78', '#a8a29a')[k % 3], seed=k, amt=0.1, stitch=False),
              x0 + dx * u, y0 + 40 * u)
    c.put('log1', lambda: p_log(330 * u, 32 * u, BROWN, 0.22), x0, y0)
    for j, (dx, hh, lean) in enumerate(((-55, 170, -0.15), (55, 160, 0.15), (0, 230, 0.0))):
        c.put(('fl', j, (fi + 3 * j) % 8), lambda j=j, hh=hh, lean=lean, s=(fi + 3 * j) % 8: p_flame(hh * u, 100 * j + s, lean=lean),
              x0 + dx * u, y0 - 20 * u)
    c.put('log2', lambda: p_log(330 * u, 32 * u, '#7a4c30', -0.22), x0, y0 + 12 * u)
    R = c.R(60)
    for i, age in c.emit(18, 1.6):
        r = R[i]
        x = x0 + (r[0] - 0.5) * 140 * u + 30 * u * math.sin(age * 5 + r[1] * 6)
        y = y0 - 120 * u - age * (220 + 120 * r[2]) * u
        op = fade(age, 1.6, 0.1, 0.5)
        c.cv.glow(x, y, 14 * u, '#ffcc66', 0.25 * op)
        c.put(('e', i % 3), lambda i=i: p_blob((5 + i % 3 * 2) * u, ('#ffd36a', '#ff9a3a', '#ffb648')[i % 3], seed=i % 3, stitch=False),
              x, y, op)


@effect('candle', 'fire', 'Candle: stitched cream felt candle with a swaying teardrop flame and soft glow.', dur=2.0,
        at=(0.5, 0.62))
def _candle(c):
    u = c.u
    x0, y0 = c.at()
    sway = 0.12 * c.osc(2) + 0.05 * c.osc(5, 1)
    flick = 1 + 0.06 * c.osc(6)
    c.cv.glow(x0, y0 - 40 * u, 170 * u * flick, '#ffd27a', 0.33)

    def body():
        p = Piece()
        pts = rrect_pts(110 * u, 300 * u, 14 * u)
        p.poly(pts, CREAM)
        p.stitch_inset(pts, 11 * u, '#c9b996', w=2.2 * u, dash=8 * u, gap=6 * u)
        p.layer(depth=0.5)
        p.poly(xform(drop_pts(), 14 * u, 30 * u, tx=-30 * u, ty=-110 * u), '#f7f0de')
        return p
    c.put('body', body, x0, y0 + 150 * u)
    c.put('plate', lambda: Piece().poly(ellipse_pts(130 * u, 26 * u), '#b48a5a'), x0, y0 + 300 * u)
    c.put('wick', lambda: Piece().stroke([(0, 0), (0, -26 * u)], 6 * u, INK), x0, y0)
    ia, a = qa(sway, 96)
    def fl(a=a):
        p = Piece()
        p.poly(xform(drop_pts(), 26 * u, 62 * u, a), ORANGE)
        p.layer(depth=0.5, shadow=0.3)
        p.poly(xform(drop_pts(), 15 * u, 38 * u, a, tx=-math.sin(a) * -10 * u, ty=14 * u), YELLOW)
        return p
    c.put(('f', ia, int(flick * 50)), fl, x0 + math.sin(a) * 50 * u, y0 - 70 * u * flick)


@effect('explosion_puff', 'fire', 'Cartoon explosion: spiky orange flash, then grey smoke puffs balloon out and fade, debris flies.',
        dur=2.5, loop=False, at=(0.5, 0.55))
def _explosion(c):
    u = c.u
    x0, y0 = c.at()
    t = c.t
    R = c.R(40)
    # flash
    if t < 0.45:
        k = t / 0.45
        s = back_out(min(1, k * 2.2)) * (1 - ease_in(k) * 0.4)
        si = int(s * 24)
        op = 1 if k < 0.7 else (1 - k) / 0.3
        c.cv.fill('#fff4d6', 0.35 * (1 - k))
        c.put(('fo', si), lambda s=si / 24: p_star(330 * u * s, ORANGE, n=11, inner=0.62, soft=False), x0, y0, op)
        c.put(('fi', si), lambda s=si / 24: p_star(210 * u * s, YELLOW, n=9, inner=0.6, soft=False, ang=0.3), x0, y0, op)
    # smoke puffs
    for i in range(14):
        r = R[i]
        st = 0.08 + 0.15 * r[0]
        if t < st:
            continue
        k = (t - st) / (c.D - st)
        a = r[1] * TAU
        dist = (90 + 230 * r[2]) * u * ease_out(k * 1.4)
        x = x0 + math.cos(a) * dist * 1.25
        y = y0 + math.sin(a) * dist * 0.7 - 120 * u * k
        sz = (60 + 50 * r[3]) * u * (0.4 + ease_out(k * 2) * 0.9)
        si = int(sz / u / 6)
        op = 1 if k < 0.55 else max(0, (1 - k) / 0.45)
        col = ('#9b958e', '#b8b2aa', '#7f7a75')[i % 3]
        c.put(('p', si, i % 3), lambda si=si, col=col, i=i: p_blob(si * 6 * u, col, seed=i % 3, amt=0.07, stitch=si * 6 > 70), x, y, op)
    # debris
    for i in range(10):
        r = R[20 + i]
        a = -math.pi * (0.1 + 0.8 * r[0])
        v = (900 + 600 * r[1]) * u
        x = x0 + math.cos(a) * v * t
        y = y0 + math.sin(a) * v * t + 0.5 * 2200 * u * t * t
        ia, aa = qa(t * 12 + r[2] * 6, 16)
        c.put(('d', i % 3, ia), lambda i=i, aa=aa: Piece().poly(xform([(-1, -0.6), (1, -0.8), (0.6, 0.8), (-0.8, 0.5)], 14 * u, ang=aa),
                                                                ('#5d4a3a', '#8a5a3a', '#6b6b6b')[i % 3]), x, y)


def _puff_stream(c, x0, y0, n, life, rise, spread, drift, size, cols, alpha=1.0, grow=2.2, k=0, sway=30):
    R = c.R(200, k)
    u = c.u
    for i, age in c.emit(n, life, k):
        r = R[i]
        q = age / life
        x = x0 + (r[0] - 0.5) * spread * u + drift * u * age + sway * u * math.sin(age * 2.5 + r[1] * 6)
        y = y0 - rise * u * (q ** 0.85)
        s = size * u * (0.45 + grow * q) * (0.8 + 0.4 * r[2])
        si = max(1, int(s / u / 5))
        op = fade(age, life, 0.12, 0.5) * alpha
        col = cols[i % len(cols)]
        c.put(('pf', k, si, i % len(cols)), lambda si=si, col=col, i=i: p_blob(si * 5 * u, col, seed=i % 4, amt=0.08, stitch=False), x, y, op)


@effect('steam', 'fire', 'Steam: soft white puffs curling up from a point (cup, kettle, pot) and dissolving.', dur=3.0,
        at=(0.5, 0.75))
def _steam(c):
    x0, y0 = c.at()
    _puff_stream(c, x0, y0, 14, 2.4, 460, 60, 0, 40, ('#f7f5f0', '#eeebe4'), alpha=0.85, grow=2.0, sway=35)


@effect('chimney_smoke', 'fire', 'Chimney smoke: grey puffs rising and drifting with the wind, growing as they go.', dur=4.0,
        at=(0.62, 0.62))
def _chimney(c):
    x0, y0 = c.at()
    _puff_stream(c, x0, y0, 12, 3.6, 560, 20, 120, 34, ('#a7a29c', '#bab5ae', '#958f89'), grow=2.4, sway=25)


@effect('dust_cloud', 'fire', 'Dust cloud: beige felt puffs burst out sideways along the ground (skid, landing, stomp).',
        dur=2.0, loop=False, at=(0.5, 0.85))
def _dust(c):
    u = c.u
    x0, y0 = c.at()
    R = c.R(30)
    t = c.t
    for i in range(16):
        r = R[i]
        st = 0.25 * r[0]
        if t < st:
            continue
        k = (t - st) / (c.D - st)
        side = -1 if i % 2 else 1
        d = (80 + 380 * r[1]) * u * ease_out(k * 1.6)
        x = x0 + side * d
        y = y0 - (20 + 80 * r[2]) * u * ease_out(k) - 30 * u * k
        sz = (30 + 40 * r[3]) * u * (0.5 + ease_out(k * 2) * 0.9)
        si = int(sz / u / 5)
        op = 1 if k < 0.5 else max(0, (1 - k) / 0.5)
        col = ('#d9c4a0', '#c9b088', '#e6d5b6')[i % 3]
        c.put(('d', si, i % 3), lambda si=si, col=col, i=i: p_blob(si * 5 * u, col, seed=i % 3, amt=0.08, stitch=False), x, y, op)


@effect('embers', 'fire', 'Embers: tiny glowing orange felt sparks rising and wavering.', dur=3.0, density=70)
def _embers(c):
    u = c.u
    R = c.R(100)
    for i, age in c.emit(int(c.p['density']), 2.8):
        r = R[i]
        x = r[0] * c.W + 40 * u * math.sin(age * 3 + r[1] * 6)
        y = c.H + 20 * u - age * (300 + 200 * r[2]) * u
        op = fade(age, 2.8, 0.1, 0.4) * (0.75 + 0.25 * math.sin(age * 14 + r[3] * 6))
        col = ('#ffd36a', '#ff9a3a', '#ff7a2a')[i % 3]
        c.cv.glow(x, y, 26 * u, '#ffb648', 0.4 * op)
        c.put(('e', i % 3), lambda i=i, col=col: p_blob((8 + 3 * (i % 3)) * u, col, seed=i % 3, stitch=False), x, y, op)


@effect('fire_edge', 'fire', 'A wall of felt flames flickering along the bottom edge of the frame.', dur=2.0)
def _fire_edge(c):
    u = c.u
    n = 11
    fi = int(c.t * 12) % 8
    c.cv.fill('#ff9a3a', 0.06)
    for row in range(2):
        for k in range(n + 1):
            x = (k + 0.5 * row) * c.W / n - 40 * u
            hh = (210 if row == 0 else 290) * u * (0.85 + 0.3 * ((k * 7 + row * 3) % 5) / 4)
            s = (fi + k * 3 + row) % 8
            c.put(('f', row, k % 5, s), lambda hh=hh, s=s, kk=k, row=row: p_flame(hh, 1000 * row + 10 * (kk % 5) + s,
                                                                         lean=0.08 * ((kk % 3) - 1)),
                  x, c.H - 30 * u + (0 if row else 30 * u))
    c.put('base', lambda: Piece().poly(rrect_pts(c.W + 200 * u, 90 * u, 30 * u), '#d2452f'), c.W / 2, c.H + 10 * u)


@effect('smoke_puffs', 'fire', 'Billowing smoke: puffy felt clouds bursting out sideways and up from a point (launch, crash).',
        dur=3.0, at=(0.5, 0.85))
def _smoke_puffs(c):
    u = c.u
    x0, y0 = c.at()
    R = c.R(60)
    for i, age in c.emit(16, 2.6):
        r = R[i]
        side = -1 if i % 2 else 1
        q = age / 2.6
        x = x0 + side * (60 + 360 * r[0]) * u * ease_out(q * 1.3)
        y = y0 - (30 + 200 * r[1]) * u * q
        sz = (45 + 45 * r[2]) * u * (0.5 + q)
        si = int(sz / u / 6)
        op = fade(age, 2.6, 0.08, 0.35)
        col = ('#efebe4', '#dcd7cf', '#f6f3ee')[i % 3]
        c.put(('p', si, i % 3), lambda si=si, col=col, i=i: p_blob(si * 6 * u, col, seed=i % 3, amt=0.07, stitch=False), x, y, op)


@effect('poof_vanish', 'fire', 'Cartoon poof: a ring of white felt puffs and little stars pops out and fades (disappearing).',
        dur=2.0, loop=False, at=(0.5, 0.55))
def _poof(c):
    u = c.u
    x0, y0 = c.at()
    t = c.t
    k = t / c.D
    for i in range(10):
        a = i * TAU / 10 + 0.2
        d = 150 * u * ease_out(k * 2)
        s = 70 * u * back_out(min(1, k * 4)) * (1 - 0.6 * ease_in(k))
        si = int(s / u / 4)
        op = 1 if k < 0.6 else max(0, (1 - k) / 0.4)
        if si > 0:
            c.put(('p', si, i % 2), lambda si=si, i=i: p_blob(si * 4 * u, (WHITE, '#e8e4dc')[i % 2], seed=i % 2, amt=0.06, stitch=False),
                  x0 + math.cos(a) * d * 1.3, y0 + math.sin(a) * d, op)
    s = back_out(min(1, k * 5)) * (1 - ease_in(k * 1.2))
    si = int(s * 20)
    if si > 0:
        c.put(('c', si), lambda si=si: p_blob(120 * u * si / 20, WHITE, seed=5, amt=0.08), x0, y0)
    for i in range(6):
        a = i * TAU / 6
        d = 260 * u * ease_out(k * 1.5)
        ia, aa = qa(k * 6 + i, 16)
        op = max(0, 1 - k * 1.3)
        c.put(('s', ia), lambda aa=aa: p_star(22 * u, YELLOW, ang=aa, stitch=False), x0 + math.cos(a) * d * 1.3, y0 + math.sin(a) * d, op)


# ============================================================ WATER

@effect('splash', 'water', 'Water splash: a felt crown rises and blue drops shoot up and fall back.', dur=2.0, loop=False,
        at=(0.5, 0.8))
def _splash(c):
    u = c.u
    x0, y0 = c.at()
    t = c.t
    R = c.R(40)
    g = 2600 * u
    k = min(1, t / 1.2)
    # ripple
    rk = ease_out(t / c.D)
    c.put(('rp', int(rk * 30)), lambda rk=rk: p_ring(260 * u * (0.3 + rk), 14 * u, lighter(BLUE, 0.3), ry=50 * u * (0.3 + rk)), x0, y0,
          1 - rk)
    # crown
    hgt = 160 * u * math.sin(math.pi * min(1, k * 1.3))
    if hgt > 4 * u:
        hi = int(hgt / u / 8)
        def crown(h=hi * 8 * u):
            pts = []
            n = 7
            for j in range(n * 2 + 1):
                xx = -150 * u + j * 300 * u / (n * 2)
                yy = -h if j % 2 == 1 else -h * 0.45
                pts.append((xx, yy))
            pts += [(160 * u, 0), (-160 * u, 0)]
            p = Piece().poly(pts, BLUE)
            p.layer(depth=0.4, shadow=0.3)
            p.poly(ellipse_pts(150 * u, 30 * u), lighter(BLUE, 0.3))
            return p
        c.put(('cr', hi), crown, x0, y0)
    for i in range(16):
        r = R[i]
        a = -math.pi / 2 + (r[0] - 0.5) * 2.0
        v = (900 + 600 * r[1]) * u
        tt = t - 0.05 * r[2]
        if tt < 0:
            continue
        x = x0 + math.cos(a) * v * tt
        y = y0 - 40 * u + math.sin(a) * v * tt + 0.5 * g * tt * tt
        if y > y0 + 40 * u:
            continue
        vy = math.sin(a) * v + g * tt
        ang = math.atan2(vy, math.cos(a) * v) - math.pi / 2 + math.pi
        ia, aa = qa(ang, 36)
        sz = int(r[3] * 3)
        c.put(('d', sz, ia), lambda sz=sz, aa=aa: p_drop((9 + 4 * sz) * u, SKY, ang=aa, stretch=1.4), x, y)


@effect('ripples', 'water', 'Ripples: concentric felt rings spreading on a water surface and fading.', dur=3.0, at=(0.5, 0.75))
def _ripples(c):
    u = c.u
    x0, y0 = c.at()
    for i, age in c.emit(4, 3.0):
        q = age / 3.0
        ri = int(q * 40)
        op = (1 - q) ** 1.2 * min(1, q * 8)
        c.put(('r', ri), lambda ri=ri: p_ring(40 * u + ri / 40 * 520 * u, 13 * u * (1 - 0.5 * ri / 40), lighter(BLUE, 0.35),
                                              ry=(40 * u + ri / 40 * 520 * u) * 0.24), x0, y0, op)


@effect('bubbles', 'water', 'Bubbles: light blue felt bubbles with a white glint rising and wobbling.', dur=3.0, density=22,
        at=(0.5, 0.95))
def _bubbles(c):
    u = c.u
    x0, y0 = c.at()
    R = c.R(100)
    for i, age in c.emit(int(c.p['density']), 3.0):
        r = R[i]
        x = x0 + (r[0] - 0.5) * 700 * u + 25 * u * math.sin(age * 3 + r[1] * 6)
        y = y0 - age * (240 + 120 * r[2]) * u
        sz = int(r[3] * 4)
        op = fade(age, 3.0, 0.08, 0.15)
        def b(sz=sz):
            rr = (12 + 9 * sz) * u
            p = Piece().poly(ellipse_pts(rr), '#cfeaf8')
            p.layer(depth=0.3, shadow=0)
            p.poly(xform(arc_pts(rr * 0.62, math.pi * 1.05, math.pi * 1.45, 10).tolist() + arc_pts(rr * 0.45, math.pi * 1.45, math.pi * 1.05, 10).tolist()), WHITE)
            return p
        c.put(('b', sz), b, x, y, op)


@effect('drip', 'water', 'Drip: a drop swells under a point, stretches, falls and makes a small splash ring.', dur=3.0,
        at=(0.5, 0.2), floor=0.85)
def _drip(c):
    u = c.u
    x0, y0 = c.at()
    fl = c.p['floor'] * c.H
    per = c.D / 2
    t = c.t % per
    grow = 0.9
    if t < grow:
        k = ease_io(t / grow)
        si = int(k * 12)
        c.put(('g', si), lambda si=si: p_drop((8 + si * 1.6) * u, BLUE, stretch=1 + si / 24), x0, y0 + (6 + si * 2.2) * u)
    else:
        tt = t - grow
        y = y0 + 32 * u + 0.5 * 2600 * u * tt * tt
        if y < fl:
            c.put('f', lambda: p_drop(28 * u, BLUE, stretch=1.25), x0, y)
        else:
            th = math.sqrt(2 * (fl - y0 - 32 * u) / (2600 * u))
            k = (tt - th) / (per - grow - th)
            if 0 <= k <= 1:
                _splash_crown(c, 'sc', x0, fl, min(1, k * 1.6), 16 * u, BLUE)
                ki = int(k * 20)
                c.put(('rr', ki), lambda ki=ki: p_ring((30 + ki * 9) * u, 8 * u, lighter(BLUE, 0.3), ry=(30 + ki * 9) * u * 0.25), x0, fl,
                      1 - k)
    c.put('tap', lambda: Piece().poly(rrect_pts(70 * u, 40 * u, 12 * u), '#9aa4ad'), x0, y0 - 14 * u)


@effect('waves_edge', 'water', 'Sea edge: three layers of felt waves rolling along the bottom with a stitched foam line.',
        dur=3.0, fps=24, scale=0.5)
def _waves(c):
    u = c.u
    layers = ((0.80, 34, 2, '#7fb6e0', 1), (0.86, 30, 3, '#5f9fd8', -1), (0.92, 26, 2, '#3f78b8', 1))
    xs = np.linspace(-20 * u, c.W + 20 * u, 160)
    for j, (yb, amp, cyc, col, dirn) in enumerate(layers):
        ph = dirn * TAU * c.t / c.D
        y = yb * c.H + amp * u * np.sin(xs / c.W * TAU * cyc * 2 + ph + j) + amp * 0.4 * u * np.sin(xs / c.W * TAU * cyc * 5 - ph * 2)
        top = np.stack([xs, y], 1)
        pts = np.vstack([top, [[c.W + 20 * u, c.H + 40 * u], [-20 * u, c.H + 40 * u]]])
        p = Piece().layer(depth=0.8)
        p.poly(pts, col)
        p.stitch(top + (0, 16 * u), lighter(col, 0.6), w=2.6 * u, dash=11 * u, gap=8 * u, closed=False)
        c.full(p)


@effect('fountain', 'water', 'Fountain: a jet of felt water drops arcing up and falling back, endlessly.', dur=2.0,
        at=(0.5, 0.85))
def _fountain(c):
    u = c.u
    x0, y0 = c.at()
    R = c.R(200)
    g = 2400 * u
    for i, age in c.emit(70, 1.25):
        r = R[i]
        a = -math.pi / 2 + (r[0] - 0.5) * 0.7
        v = (1150 + 250 * r[1]) * u
        x = x0 + math.cos(a) * v * age
        y = y0 + math.sin(a) * v * age + 0.5 * g * age * age
        if y > y0 + 10 * u:
            continue
        vy = math.sin(a) * v + g * age
        ia, aa = qa(math.atan2(vy, math.cos(a) * v) + math.pi / 2, 36)
        sz = int(r[2] * 3)
        c.put(('d', sz, ia), lambda sz=sz, aa=aa: p_drop((8 + 3 * sz) * u, SKY if sz else BLUE, ang=aa, stretch=1.3, hi=False), x, y)
    c.put('pool', lambda: Piece().poly(ellipse_pts(280 * u, 46 * u), '#7fb6e0').layer(depth=0.4).stitch(ellipse_pts(250 * u, 34 * u), WHITE,
                                                                                                           w=2.5 * u, dash=10 * u, gap=7 * u),
          x0, y0 + 26 * u)


@effect('puddle_splashes', 'water', 'Rain on the ground: little splash crowns and rings popping up all over the floor.',
        dur=2.0, density=40, floor=0.78)
def _puddle(c):
    u = c.u
    R = c.R(100)
    for i, age in c.emit(int(c.p['density']), 0.45):
        r = R[i]
        x = r[0] * c.W
        y = (c.p['floor'] + r[1] * (0.98 - c.p['floor'])) * c.H
        k = age / 0.45
        s = 0.6 + 0.6 * (y / c.H - c.p['floor']) / (1 - c.p['floor'])
        ki = int(k * 12)
        c.put(('r', ki, int(s * 4)), lambda ki=ki, s=int(s * 4) / 4: p_ring((40 + ki * 14) * u * s, 10 * u, lighter(BLUE, 0.35),
                                                                          ry=(40 + ki * 14) * u * s * 0.3), x, y, 1 - k)
        _splash_crown(c, 'sc%d' % int(s * 4), x, y, min(1, k * 1.5), 22 * u * s, BLUE)


@effect('tears_stream', 'water', 'Cartoon crying: two arcing streams of felt tear drops spurting from the eyes.', dur=1.5,
        at=(0.5, 0.42), gap=0.09)
def _tears(c):
    u = c.u
    x0, y0 = c.at()
    g = 2600 * u
    for side in (-1, 1):
        ex = x0 + side * c.p['gap'] * c.W * c.size
        for i, age in c.emit(16, 0.75, k=side + 2):
            v = 620 * u
            a = -math.pi / 2 + side * 1.05
            x = ex + math.cos(a) * v * age
            y = y0 + math.sin(a) * v * age + 0.5 * g * age * age
            vy = math.sin(a) * v + g * age
            ia, aa = qa(math.atan2(vy, math.cos(a) * v) - math.pi / 2 + math.pi, 36)
            c.put(('t', ia), lambda aa=aa: p_drop(16 * u, '#9fd0f0', ang=aa, stretch=1.2), x, y, fade(age, 0.75, 0.05, 0.25))


# ============================================================ CELEBRATION

def p_confetti(kind, col, sz, ang, sy):
    if kind == 0:
        pts = rrect_pts(sz * 1.6, sz * 0.9, sz * 0.15)
    elif kind == 1:
        pts = ellipse_pts(sz * 0.6)
    elif kind == 2:
        pts = np.array([(0, -0.7), (0.65, 0.5), (-0.65, 0.5)]) * sz
    else:
        pts = star_pts(5, sz * 0.75, sz * 0.36)
    return Piece().poly(xform(pts, 1, max(0.12, sy), ang), col)


def _confetti_piece(c, i, r, x, y, age, op=1.0):
    u = c.u
    kind = int(r[5] * 4)
    col = FESTIVE[i % 8]
    ia, a = qa(age * (2 + 3 * r[6]) + r[7] * 6, 24)
    iv, sy = qv(abs(math.cos(age * (5 + 4 * r[8]) + r[9] * 6)), 5)
    c.put(('c', kind, i % 8, ia, iv), lambda kind=kind, col=col, a=a, sy=sy: p_confetti(kind, col, 22 * u, a, sy), x, y, op)


@effect('confetti_fall', 'celebration', 'Confetti: rectangles, dots, triangles and stars fluttering down in festive colours.',
        dur=3.0, density=120)
def _confetti_fall(c):
    u = c.u
    R = c.R(400)
    for i, age in c.emit(int(c.p['density']), 4.5):
        r = R[i]
        x = r[0] * c.W + 50 * u * math.sin(age * 2 + r[1] * 6)
        y = -40 * u + age * (230 + 120 * r[2]) * u
        if y > c.H + 40 * u:
            continue
        _confetti_piece(c, i, r, x, y, age)


@effect('confetti_burst', 'celebration', 'Confetti cannons: two bursts from the bottom corners shoot confetti up, it flutters down.',
        dur=3.0, loop=False, count=90)
def _confetti_burst(c):
    u = c.u
    R = c.R(300)
    g = 1500 * u
    t = c.t
    for i in range(int(c.p['count'])):
        r = R[i]
        side = i % 2
        sx = c.W * (0.03 if side == 0 else 0.97)
        a = -math.pi / 2 + (0.25 + 0.45 * r[0]) * (1 if side == 0 else -1)
        v = (2600 + 1000 * r[1]) * u
        tt = t - 0.15 * r[2]
        if tt < 0:
            continue
        # ballistic with drag: velocity decays, then terminal flutter fall
        k = 1.8
        vx, vy = math.cos(a) * v, math.sin(a) * v
        e = (1 - math.exp(-k * tt)) / k
        vt = 160 * u
        x = sx + vx * e + 30 * u * math.sin(tt * 4 + r[3] * 6)
        y = c.H + 20 * u + vy * e + vt * (tt - e) + 0.5 * g * e * e
        op = 1 if t < c.D - 0.4 else (c.D - t) / 0.4
        _confetti_piece(c, i, r, x, y, tt, op)


def p_spark_ball(r, col):
    return Piece().poly(wobble(ellipse_pts(r), 0.05, int(r)), col)


@effect('fireworks', 'celebration', 'Fireworks: felt rockets climb on a puff trail and burst into rings of stars and dots that droop and fade.',
        dur=3.0)
def _fireworks(c):
    u = c.u
    shows = [(0.0, 0.3, 0.30, FESTIVE[0], YELLOW), (1.0, 0.68, 0.24, FESTIVE[2], PINK), (2.0, 0.5, 0.36, FESTIVE[3], '#ffffff')]
    for j, (st, fx, fy, col, col2) in enumerate(shows):
        for rep in (0, 1):
            tt = (c.t - st) % c.D + rep * c.D
            if tt > 2.6:
                continue
            bx, by = fx * c.W, fy * c.H
            rise = 0.7
            if tt < rise:
                k = ease_out(tt / rise)
                y = c.H + 20 * u - (c.H + 20 * u - by) * k
                c.put(('rk', j), lambda col=col: Piece().poly(xform(drop_pts(), 10 * u, 22 * u), col), bx, y)
                for q in range(5):
                    yq = y + (q + 1) * 34 * u
                    c.put(('tr', q), lambda q=q: p_blob((9 - q) * u, '#efe6cf', seed=q, stitch=False), bx + 5 * u * math.sin(q * 2 + tt * 20),
                          yq, 1 - q / 5)
            else:
                k = (tt - rise) / (2.6 - rise)
                op = 1 if k < 0.55 else max(0, (1 - k) / 0.45)
                c.cv.glow(bx, by, 220 * u * ease_out(k * 3), col, 0.22 * (1 - k))
                n = 18
                for m in range(n):
                    a = m * TAU / n + j
                    d = 340 * u * ease_out(k * 1.8)
                    x = bx + math.cos(a) * d
                    y = by + math.sin(a) * d + 160 * u * k * k
                    ia, aa = qa(a + k * 2, 20)
                    if m % 2 == 0:
                        c.put(('s', j, ia), lambda col=col, aa=aa: p_star(30 * u, col, ang=aa, stitch=False), x, y, op)
                    else:
                        c.put(('b', j), lambda col2=col2: p_spark_ball(15 * u, col2), x, y, op)
                    d2 = d * 0.55
                    c.put(('b2', j), lambda col2=col2: p_spark_ball(11 * u, col2), bx + math.cos(a + 0.22) * d2,
                          by + math.sin(a + 0.22) * d2 + 120 * u * k * k, op)


def p_balloon(r, col):
    p = Piece()
    p.stroke(bezier((0, r * 1.2), (r * 0.3, r * 2.4), (-r * 0.1, r * 3.6)), max(2, r * 0.05), '#6a6a6a')
    p.layer()
    body = np.vstack([ellipse_pts(r * 0.85, r * 1.05)])
    p.poly(body, col)
    p.poly([(-r * 0.15, r * 1.2), (r * 0.15, r * 1.2), (0, r * 1.0)], col)
    p.layer(depth=0.35, shadow=0)
    p.ellipse(-r * 0.35, -r * 0.45, r * 0.14, r * 0.26, lighter(col, 0.55), 0.5)
    return p


@effect('balloons_rise', 'celebration', 'Balloons: shiny felt balloons on strings rising and swaying.', dur=4.0, density=8)
def _balloons(c):
    u = c.u
    R = c.R(100)
    for i, age in c.emit(int(c.p['density']), 5.5):
        r = R[i]
        x = (0.06 + 0.88 * r[0]) * c.W + 30 * u * math.sin(age * 1.4 + r[1] * 6)
        y = c.H + 200 * u - age * (280 + 80 * r[2]) * u
        ia, a = qa(0.12 * math.sin(age * 1.4 + r[1] * 6 + 0.6), 40)
        sz = int(r[3] * 2)
        col = FESTIVE[i % 8]
        def b(sz=sz, col=col, a=a):
            p = p_balloon((70 + 14 * sz) * u, col)
            for L in p.layers:
                L['parts'] = [(k, xform(pp, ang=a), cc, w) for k, pp, cc, w in L['parts']]
            return p
        c.put(('b', sz, i % 8, ia), b, x, y)


def p_streamer(L, w, col, ph):
    ys = np.linspace(-L / 2, L / 2, 40)
    xs = np.sin(ys / L * TAU * 1.5 + ph) * w * 2.2
    return Piece().stroke(np.stack([xs, ys], 1), w, col)


@effect('streamers_fall', 'celebration', 'Streamers: wavy felt ribbons twisting as they fall.', dur=3.0, density=22)
def _streamers(c):
    u = c.u
    R = c.R(100)
    for i, age in c.emit(int(c.p['density']), 4.0):
        r = R[i]
        x = r[0] * c.W + 40 * u * math.sin(age * 1.5 + r[1] * 6)
        y = -140 * u + age * (280 + 100 * r[2]) * u
        ph = int((age * 6 + r[3] * 6) / TAU * 8) % 8
        ia, a = qa(0.3 * math.sin(age * 1.7 + r[4] * 6), 24)
        col = FESTIVE[i % 8]
        def b(ph=ph, col=col, a=a):
            p = p_streamer(190 * u, 13 * u, col, ph * TAU / 8)
            p.layers[0]['parts'] = [(k, xform(pp, ang=a), cc, w) for k, pp, cc, w in p.layers[0]['parts']]
            return p
        c.put(('s', i % 8, ph, ia), b, x, y)


@effect('sparkle_burst', 'celebration', 'Sparkle burst: four-point felt stars shoot out from a point, twinkle and shrink.',
        dur=2.0, loop=False, at=(0.5, 0.5))
def _sparkle_burst(c):
    u = c.u
    x0, y0 = c.at()
    R = c.R(40)
    k = c.t / c.D
    for i in range(18):
        r = R[i]
        a = i * TAU / 18 + r[0] * 0.3
        d = (180 + 220 * r[1]) * u * ease_out(k * 1.8)
        s = (1 - ease_in(k)) * (0.7 + 0.3 * math.sin(k * 30 + r[2] * 6)) * back_out(min(1, k * 6))
        si = int(s * 12)
        if si <= 0:
            continue
        col = (YELLOW, WHITE, '#ffe48a', PINK)[i % 4]
        c.put(('s', si, i % 4), lambda si=si, col=col: p_spark((26 + 12 * (i % 3)) * u * si / 12, col), x0 + math.cos(a) * d,
              y0 + math.sin(a) * d)
    s = back_out(min(1, k * 5)) * (1 - ease_in(k * 1.4))
    if s > 0.05:
        c.put(('c', int(s * 16)), lambda s=int(s * 16) / 16: p_spark(110 * u * s, '#fff2a8'), x0, y0)


@effect('bunting', 'celebration', 'Bunting: a garland of stitched felt flags across the top, swaying in the breeze.', dur=3.0)
def _bunting(c):
    u = c.u
    n = 13
    sag = 110 * u
    for j in range(n):
        f = (j + 0.5) / n
        x = f * c.W
        y = 40 * u + sag * 4 * f * (1 - f) + 6 * u * c.osc(1, j * 0.4)
        ia, a = qa(0.10 * c.osc(1, j * 0.6) + (f - 0.5) * -0.3, 60)
        col = FESTIVE[j % 8]
        def b(col=col, a=a):
            pts = xform([(-48 * u, 0), (48 * u, 0), (0, 110 * u)], ang=a)
            p = Piece().poly(pts, col)
            p.stitch_inset(pts, 12 * u, lighter(col, 0.5), w=2.2 * u, dash=7 * u, gap=5 * u)
            return p
        c.put(('f', j % 8, ia), b, x, y)
    xs = np.linspace(0, c.W, 60)
    ys = 40 * u + sag * 4 * (xs / c.W) * (1 - xs / c.W) - 4 * u
    key = int(c.t * 0)
    c.full(lambda: Piece().layer(depth=0.4).stroke(np.stack([xs, ys], 1), 6 * u, '#d9cbb0'), key=('rope', key))


@effect('stars_shower', 'celebration', 'Star shower: golden stitched felt stars tumbling down and twinkling.', dur=3.0, density=34)
def _stars_shower(c):
    u = c.u
    R = c.R(100)
    for i, age in c.emit(int(c.p['density']), 4.0):
        r = R[i]
        x = r[0] * c.W + 30 * u * math.sin(age + r[1] * 6)
        y = -60 * u + age * (260 + 120 * r[2]) * u
        ia, a = qa(age * (1.5 if r[3] > 0.5 else -1.5) + r[4] * 6, 30)
        sz = int(r[5] * 3)
        col = (GOLD, YELLOW, '#ffe48a')[i % 3]
        c.put(('s', sz, i % 3, ia % 6), lambda sz=sz, col=col, a=a: p_star((22 + 10 * sz) * u, col, ang=a), x, y)


# ============================================================ COMIC

@effect('speed_lines_radial', 'comic', 'Focus speed lines: felt wedges flicking in from the frame edges toward the centre.',
        dur=1.0, fps=24, scale=0.5, at=(0.5, 0.5))
def _speed_radial(c):
    u = c.u
    x0, y0 = c.at()
    fi = int(c.t * 12) % 12
    r = np.random.default_rng([c.seed, fi])
    p = Piece().layer(depth=0.6)
    n = 46
    Rf = math.hypot(c.W, c.H)
    for k in range(n):
        a = (k + r.random() * 0.6) * TAU / n
        inner = (330 + 170 * r.random()) * u * 1.5
        wa = 0.022 + 0.02 * r.random()
        p.poly([(x0 + math.cos(a) * inner, y0 + math.sin(a) * inner),
                (x0 + math.cos(a - wa) * Rf, y0 + math.sin(a - wa) * Rf),
                (x0 + math.cos(a + wa) * Rf, y0 + math.sin(a + wa) * Rf)], ('#f7f3ea', '#ece4d4')[k % 2])
    c.full(p)


@effect('motion_lines', 'comic', 'Whoosh lines: horizontal felt strips streaking past (something moving fast).', dur=1.0,
        density=16)
def _motion_lines(c):
    u = c.u
    R = c.R(100)
    for i, age in c.emit(int(c.p['density']), 0.5):
        r = R[i]
        L = (200 + 400 * r[0]) * u
        x = c.W + L - age * (4800 + 1200 * r[1]) * u
        y = (0.1 + 0.8 * r[2]) * c.H
        sz = int(r[0] * 3)
        c.put(('l', sz, i % 2), lambda sz=sz, i=i: Piece().layer(depth=0.5).stroke([(-(200 + 133 * sz) * u, 0), ((200 + 133 * sz) * u, 0)],
                                                                                      (9 + 3 * (i % 2)) * u, ('#f7f3ea', '#e7dfcf')[i % 2]),
              x, y, 0.95)


@effect('impact_star', 'comic', 'Impact: a spiky red-yellow felt burst pops with overshoot and shakes, small stars fly off.',
        dur=1.5, loop=False, at=(0.5, 0.5))
def _impact(c):
    u = c.u
    x0, y0 = c.at()
    k = c.t / c.D
    s = back_out(min(1, k * 5)) * (1 - ease_in(max(0, (k - 0.7) / 0.3)))
    sh = (1 - k) * 8 * u * math.sin(c.t * 70)
    if s > 0.02:
        si = int(s * 30)
        def b(s=si / 30):
            r = np.random.default_rng(4)
            n = 12
            pts = []
            for j in range(2 * n):
                rr = (1.0 if j % 2 == 0 else 0.55) * (0.85 + 0.3 * r.random())
                a = j * math.pi / n
                pts.append((math.cos(a) * rr, math.sin(a) * rr * 0.8))
            outer = xform(pts, 300 * u * s)
            p = Piece().poly(outer, RED)
            p.layer(depth=0.7)
            inner = xform(pts, 190 * u * s, ang=0.12)
            p.poly(inner, YELLOW)
            p.stitch_inset(inner, 16 * u * s, '#fff3c0', w=2.5 * u, dash=9 * u, gap=6 * u)
            return p
        c.put(('b', si), b, x0 + sh, y0)
    for i in range(6):
        a = i * TAU / 6 + 0.4
        d = 380 * u * ease_out(k * 1.5)
        op = max(0, 1 - k * 1.2)
        ia, aa = qa(k * 8 + i, 16)
        c.put(('s', ia), lambda aa=aa: p_star(26 * u, YELLOW, ang=aa, stitch=False), x0 + math.cos(a) * d * 1.2, y0 + math.sin(a) * d, op)


@effect('sweat_drops', 'comic', 'Nervous sweat: light-blue felt drops pop off the side of a head and fall.', dur=2.0,
        at=(0.56, 0.36))
def _sweat(c):
    u = c.u
    x0, y0 = c.at()
    g = 2200 * u
    for i, age in c.emit(4, 0.9):
        side = 1 if i != 1 else -1
        a = -math.pi / 2 + side * (0.6 + 0.2 * i)
        v = 520 * u
        x = x0 + side * 40 * u * (i == 1) + math.cos(a) * v * age
        y = y0 + math.sin(a) * v * age + 0.5 * g * age * age
        vy = math.sin(a) * v + g * age
        ia, aa = qa(math.atan2(vy, math.cos(a) * v) + math.pi / 2, 36)
        s = back_out(min(1, age * 6))
        c.put(('d', ia, int(s * 10)), lambda aa=aa, s=int(s * 10) / 10: p_drop(40 * u * s, '#a8dcf6', ang=aa, stretch=1.3), x, y,
              fade(age, 1.0, 0.0, 0.3))


@effect('anger_vein', 'comic', 'Anger mark: a red four-part felt "vein" cross pulsing next to a head.', dur=1.0, at=(0.6, 0.3))
def _anger(c):
    u = c.u
    x0, y0 = c.at()
    s = 1 + 0.18 * max(0, c.osc(2)) ** 2
    si = int(s * 30)
    def b(s=si / 30):
        p = Piece()
        r = 85 * u * s
        for k in range(4):
            a = k * TAU / 4 + math.pi / 4
            ca, sa = math.cos(a), math.sin(a)
            cx, cy = ca * r * 0.9, sa * r * 0.9
            pts = bezier((cx - sa * r * 0.6, cy + ca * r * 0.6), (ca * r * 0.25, sa * r * 0.25), (cx + sa * r * 0.6, cy - ca * r * 0.6), 20)
            p.stroke(pts, 22 * u * s, '#e0443a')
        return p
    c.put(('v', si), b, x0, y0)


def p_qmark(h, col):
    p = Piece()
    arc = arc_pts(h * 0.24, math.pi * 1.05, math.pi * 2.35, 30, 0, -h * 0.22)
    path = np.vstack([arc, bezier(arc[-1], (0, h * 0.0), (0, h * 0.12), 10)])
    p.stroke(path, h * 0.13, col)
    p.circle(0, h * 0.36, h * 0.085, col)
    return p


def p_excl(h, col):
    p = Piece()
    p.poly([(-h * 0.1, -h * 0.5), (h * 0.1, -h * 0.5), (h * 0.05, h * 0.18), (-h * 0.05, h * 0.18)], col)
    p.circle(0, -h * 0.5, h * 0.1, col)
    p.circle(0, h * 0.38, h * 0.09, col)
    return p


@effect('question_marks', 'comic', 'Confusion: felt question marks pop up one by one over a head and bob.', dur=3.0,
        at=(0.5, 0.25))
def _qmarks(c):
    u = c.u
    x0, y0 = c.at()
    for j, (dx, dy, sz, ph) in enumerate(((0, 0, 170, 0.0), (-130, 40, 110, 0.25), (125, 30, 120, 0.5))):
        k = (c.t / c.D - ph) % 1.0
        s = back_out(min(1, k * 5)) * (1 if k < 0.85 else (1 - k) / 0.15)
        if s < 0.03:
            continue
        si = int(s * 20)
        ia, aa = qa(0.15 * math.sin(c.t * 4 + j), 40)
        def b(si=si, sz=sz, aa=aa):
            p = p_qmark(sz * u * si / 20, ('#f6c94c', '#5f9fd8', '#f28fb0')[j])
            p.layers[0]['parts'] = [(kk, xform(pp, ang=aa), cc, w) for kk, pp, cc, w in p.layers[0]['parts']]
            return p
        c.put(('q', j, si, ia), b, x0 + dx * u, y0 + dy * u - 10 * u * math.sin(c.t * 3 + j))


@effect('exclamation', 'comic', 'Surprise: a big felt exclamation mark pops up with overshoot and quivers, with small burst lines.',
        dur=2.0, loop=False, at=(0.5, 0.25))
def _excl(c):
    u = c.u
    x0, y0 = c.at()
    k = c.t / c.D
    s = back_out(min(1, k * 6))
    si = int(s * 24)
    jit = 6 * u * math.sin(c.t * 50) * max(0, 1 - k * 2)
    if si:
        c.put(('e', si), lambda si=si: p_excl(230 * u * si / 24, RED), x0 + jit, y0)
    for i in range(5):
        a = -math.pi / 2 + (i - 2) * 0.45
        d0 = 140 * u
        L = 60 * u * ease_out(min(1, k * 5)) * (1 - ease_in(k))
        if L > 3 * u:
            ia, aa = qa(a, 64)
            c.put(('l', i, int(L / u / 4)), lambda aa=aa, L=L: Piece().stroke([(0, 0), (math.cos(aa) * L, math.sin(aa) * L)], 12 * u, YELLOW),
                  x0 + math.cos(a) * d0, y0 + math.sin(a) * d0 * 1.2 - 10 * u)


def p_z(h, col):
    pts = [(-0.4, -0.42), (0.42, -0.42), (-0.42, 0.42), (0.4, 0.42)]
    return Piece().stroke(xform(pts, h), h * 0.18, col)


@effect('zzz', 'comic', 'Sleeping: felt Z letters drift up and to the side, growing and fading.', dur=3.0, at=(0.55, 0.35))
def _zzz(c):
    u = c.u
    x0, y0 = c.at()
    for i, age in c.emit(3, 3.0):
        q = age / 3.0
        x = x0 + 170 * u * q + 25 * u * math.sin(q * 6)
        y = y0 - 300 * u * q
        s = 0.5 + 0.8 * q
        si = int(s * 10)
        ia, aa = qa(-0.25 + 0.15 * math.sin(q * 5), 40)
        def b(si=si, aa=aa):
            p = p_z(90 * u * si / 10, '#7f8fd0')
            p.layers[0]['parts'] = [(kk, xform(pp, ang=aa), cc, w) for kk, pp, cc, w in p.layers[0]['parts']]
            return p
        c.put(('z', si, ia), b, x, y, fade(age, 3.0, 0.15, 0.3))


@effect('hearts_float', 'comic', 'Love: stitched pink felt hearts float up and sway.', dur=3.0, density=8, at=(0.5, 0.6))
def _hearts(c):
    u = c.u
    x0, y0 = c.at()
    R = c.R(50)
    for i, age in c.emit(int(c.p['density']), 2.6):
        r = R[i]
        q = age / 2.6
        x = x0 + (r[0] - 0.5) * 300 * u + 35 * u * math.sin(age * 3 + r[1] * 6)
        y = y0 - 420 * u * q
        s = back_out(min(1, q * 5)) * (1 - 0.3 * q)
        si = int(s * 12)
        ia, aa = qa(0.2 * math.sin(age * 3 + r[1] * 6), 30)
        col = (ROSE, PINK, '#e0443a')[i % 3]
        c.put(('h', si, ia, i % 3), lambda si=si, aa=aa, col=col: p_heart((44 + 10 * (i % 2)) * u * si / 12, col, aa), x, y,
              fade(age, 2.6, 0.0, 0.3))


@effect('heart_beat', 'comic', 'Heartbeat: one big stitched felt heart thumping lub-dub.', dur=2.0, at=(0.5, 0.5))
def _heart_beat(c):
    u = c.u
    x0, y0 = c.at()
    ph = (c.t % 1.0)
    s = 1 + 0.16 * math.exp(-((ph - 0.08) / 0.05) ** 2) + 0.10 * math.exp(-((ph - 0.3) / 0.05) ** 2)
    si = int(s * 60)
    c.put(('h', si), lambda si=si: p_heart(200 * u * si / 60, '#e0445a'), x0, y0)


@effect('dizzy_stars', 'comic', 'Dizzy: little felt stars circling around a head on a tilted orbit.', dur=1.5, at=(0.5, 0.3))
def _dizzy_stars(c):
    u = c.u
    x0, y0 = c.at()
    items = []
    n = 5
    for k in range(n):
        a = TAU * (c.t / c.D + k / n)
        z = math.sin(a)
        items.append((z, k, a))
    for z, k, a in sorted(items):
        x = x0 + math.cos(a) * 230 * u
        y = y0 + z * 55 * u - math.cos(a) * 25 * u
        s = 0.75 + 0.25 * z
        ia, aa = qa(a * 2, 20)
        si = int(s * 10)
        col = (YELLOW, GOLD)[k % 2]
        c.put(('s', si, ia, k % 2), lambda si=si, aa=aa, col=col: p_star(52 * u * si / 10, col, ang=aa, stitch=False), x, y)


def p_spiral(r, w, col, turns=2.6):
    a = np.linspace(0, TAU * turns, 120)
    rr = r * a / a[-1]
    return Piece().stroke(np.stack([np.cos(a) * rr, np.sin(a) * rr], 1), w, col)


@effect('dizzy_swirl', 'comic', 'Dizzy swirl: felt spirals spinning (over a head or as eyes).', dur=1.0, at=(0.5, 0.35), gap=0.07)
def _swirl(c):
    u = c.u
    x0, y0 = c.at()
    for side in (-1, 1):
        ia, aa = qa(side * TAU * c.t / c.D, 48)
        def b(aa=aa):
            p = p_spiral(80 * u, 13 * u, VIOLET)
            p.layers[0]['parts'] = [(kk, xform(pp, ang=aa), cc, w) for kk, pp, cc, w in p.layers[0]['parts']]
            return p
        c.put(('s', ia), b, x0 + side * c.p['gap'] * c.W * c.size, y0)


def p_bulb(h, lit=1.0):
    p = Piece()
    col = mix('#f3eecf', '#ffe066', lit)
    p.poly(np.vstack([arc_pts(h * 0.45, math.pi * 0.78, math.pi * 2.22, 50, 0, -h * 0.15), [(h * 0.18, h * 0.38), (-h * 0.18, h * 0.38)]]), col)
    p.stitch(arc_pts(h * 0.33, math.pi * 1.1, math.pi * 1.6, 12, 0, -h * 0.15), WHITE, w=h * 0.025, dash=h * 0.05, gap=h * 0.04, closed=False)
    p.layer(depth=0.6)
    p.poly(rrect_pts(h * 0.42, h * 0.26, h * 0.06) + (0, h * 0.5), '#9aa4ad')
    p.stroke([(-h * 0.2, h * 0.47), (h * 0.2, h * 0.47)], h * 0.025, '#7a838c')
    p.stroke([(-h * 0.2, h * 0.55), (h * 0.2, h * 0.55)], h * 0.025, '#7a838c')
    p.layer(depth=0.4, shadow=0.2)
    p.stroke([(-h * 0.1, h * 0.36), (-h * 0.06, h * 0.05), (0, h * 0.15), (h * 0.06, h * 0.05), (h * 0.1, h * 0.36)], h * 0.03, '#c9a23a')
    return p


@effect('idea_bulb', 'comic', 'Idea: a felt light bulb pops up over a head, lights up yellow with flashing rays and a glow.',
        dur=2.0, loop=False, at=(0.5, 0.25))
def _idea(c):
    u = c.u
    x0, y0 = c.at()
    k = c.t / c.D
    s = back_out(min(1, k * 4))
    lit = 1.0 if k > 0.3 else 0.0
    if lit:
        c.cv.glow(x0, y0 - 30 * u, 200 * u, '#ffe066', 0.35 + 0.08 * math.sin(c.t * 20))
        for i in range(8):
            a = -math.pi / 2 + (i - 3.5) * 0.42
            L = 60 * u * (0.7 + 0.3 * math.sin(c.t * 16 + i))
            d = 170 * u
            ia, aa = qa(a, 64)
            Li = int(L / u / 5)
            c.put(('r', ia, Li), lambda aa=aa, Li=Li: Piece().stroke([(0, 0), (math.cos(aa) * Li * 5 * u, math.sin(aa) * Li * 5 * u)], 13 * u, YELLOW),
                  x0 + math.cos(a) * d, y0 - 30 * u + math.sin(a) * d)
    si = int(s * 24)
    if si:
        c.put(('b', si, lit), lambda si=si, lit=lit: p_bulb(240 * u * si / 24, lit), x0, y0)


def p_note(h, col, kind=0):
    p = Piece()
    if kind == 0:
        p.ellipse(0, 0, h * 0.2, h * 0.15, col, -0.4)
        p.stroke([(h * 0.17, -h * 0.04), (h * 0.17, -h * 0.75)], h * 0.07, col)
        p.stroke(bezier((h * 0.17, -h * 0.75), (h * 0.45, -h * 0.6), (h * 0.38, -h * 0.35), 12), h * 0.07, col)
    else:
        for dx in (0, h * 0.55):
            p.ellipse(dx, 0, h * 0.2, h * 0.15, col, -0.4)
            p.stroke([(dx + h * 0.17, -h * 0.04), (dx + h * 0.17, -h * 0.75)], h * 0.07, col)
        p.poly([(h * 0.13, -h * 0.85), (h * 0.76, -h * 0.85), (h * 0.76, -h * 0.68), (h * 0.13, -h * 0.68)], col)
    return p


@effect('music_notes', 'comic', 'Music: felt notes and beamed pairs float up along a wavy path.', dur=3.0, at=(0.5, 0.55))
def _notes(c):
    u = c.u
    x0, y0 = c.at()
    for i, age in c.emit(5, 3.0):
        q = age / 3.0
        x = x0 + (i % 3 - 1) * 90 * u + 70 * u * math.sin(q * 7 + i)
        y = y0 - 420 * u * q
        ia, aa = qa(0.25 * math.sin(q * 8 + i), 30)
        col = ('#5a4a8a', '#3f6fae', '#e0543f', '#4f9a6d', '#9a74cf')[i]
        kind = i % 2
        def b(aa=aa, col=col, kind=kind):
            p = p_note(110 * u, col, kind)
            for L in p.layers:
                L['parts'] = [(kk, xform(pp, ang=aa), cc, w) for kk, pp, cc, w in L['parts']]
            return p
        c.put(('n', i, ia), b, x, y, fade(age, 3.0, 0.1, 0.25))


@effect('shock_lines', 'comic', 'Shock: short felt strokes radiating around a head and vibrating.', dur=1.0, at=(0.5, 0.4))
def _shock(c):
    u = c.u
    x0, y0 = c.at()
    for i in range(10):
        a = -math.pi * 0.95 + i * math.pi * 0.95 * 2 / 9 if False else -math.pi + 0.2 + i * (math.pi - 0.4) / 9
        jit = 10 * u * math.sin(c.t * TAU * 12 / c.D * 0.5 + i * 2.1)
        d = 230 * u + jit
        L = (55 + 20 * (i % 2)) * u
        ia, aa = qa(a, 72)
        c.put(('l', ia, i % 2), lambda aa=aa, L=L: Piece().stroke([(0, 0), (math.cos(aa) * L, math.sin(aa) * L)], 12 * u, INK),
              x0 + math.cos(a) * d * 1.15, y0 + math.sin(a) * d)


@effect('anger_steam', 'comic', 'Fuming: white steam puffs blasting out of both sides of a head in bursts.', dur=1.5, at=(0.5, 0.4),
        gap=0.11)
def _anger_steam(c):
    u = c.u
    x0, y0 = c.at()
    R = c.R(40)
    for side in (-1, 1):
        ex = x0 + side * c.p['gap'] * c.W * c.size
        for i, age in c.emit(6, 0.75, k=side + 5):
            r = R[i]
            q = age / 0.75
            x = ex + side * 200 * u * ease_out(q) + side * 10 * u
            y = y0 - 120 * u * q - 30 * u * r[0]
            s = 0.4 + 0.9 * q
            si = int(s * 8)
            c.put(('p', si), lambda si=si: p_blob(46 * u * si / 8, '#f4f1ea', seed=si, stitch=False), x, y, fade(age, 0.75, 0.05, 0.35))


def p_grawlix(kind, h, col):
    if kind == 0:
        return p_spiral(h * 0.45, h * 0.12, col)
    if kind == 1:
        return p_bolt(h * 0.5, col)
    if kind == 2:
        return p_star(h * 0.5, col, stitch=False, soft=False)
    p = Piece().poly(ellipse_pts(h * 0.42), col)
    p.layer(depth=0.5)
    p.stroke([(-h * 0.22, -h * 0.22), (h * 0.22, h * 0.22)], h * 0.1, WHITE)
    p.stroke([(h * 0.22, -h * 0.22), (-h * 0.22, h * 0.22)], h * 0.1, WHITE)
    return p


@effect('grawlix_cloud', 'comic', 'Cursing: a jittering cluster of felt symbols (spiral, bolt, star, cross) over a head.', dur=1.0,
        at=(0.5, 0.25))
def _grawlix(c):
    u = c.u
    x0, y0 = c.at()
    fi = int(c.t * 12)
    for j, (dx, dy, kind, col) in enumerate(((-150, 0, 0, INK), (-40, -30, 1, YELLOW), (70, 5, 2, RED), (175, -15, 3, '#5a4a8a'))):
        r = np.random.default_rng([c.seed, j, fi % 12])
        jx, jy = (r.random() - 0.5) * 16 * u, (r.random() - 0.5) * 16 * u
        ia, aa = qa((r.random() - 0.5) * 0.4, 20)
        def b(kind=kind, col=col, aa=aa):
            p = p_grawlix(kind, 120 * u, col)
            for L in p.layers:
                L['parts'] = [(kk, xform(pp, ang=aa), cc, w) for kk, pp, cc, w in L['parts']]
            return p
        c.put(('g', j, ia), b, x0 + dx * u + jx, y0 + dy * u + jy)


@effect('shine_glint', 'comic', 'Shine: twinkling four-point glints popping on a shiny object (clean, new, sparkling).',
        dur=2.0, at=(0.5, 0.5), size=2.6)
def _shine(c):
    u = c.u
    x0, y0 = c.at()
    for j, (dx, dy, ph, sz) in enumerate(((-120, -80, 0.0, 70), (90, -20, 0.33, 50), (10, 90, 0.66, 40), (150, 110, 0.15, 30))):
        k = (c.t / c.D - ph) % 1.0
        s = math.sin(math.pi * min(1, k / 0.4)) if k < 0.4 else 0
        if s < 0.03:
            continue
        si = int(s * 16)
        ia, aa = qa(k * 2, 24)
        c.put(('g', si, ia, j), lambda si=si, aa=aa, sz=sz: p_spark(sz * u * si / 16, WHITE, aa), x0 + dx * u, y0 + dy * u)


def p_thought(w, h, col=WHITE):
    p = Piece()
    for x, y, r in cloud_parts(w, h, 3, n=7):
        p.poly(wobble(ellipse_pts(r) + (x, y), 0.03, abs(int(x)) + 1), col)
    return p


@effect('thought_bubble', 'comic', 'Thinking: three small felt circles pop in a trail, then an empty cloud bubble puffs up.',
        dur=2.0, loop=False, at=(0.62, 0.3))
def _thought(c):
    u = c.u
    x0, y0 = c.at()
    k = c.t / c.D
    for j, (dx, dy, r) in enumerate(((-230, 230, 16), (-190, 170, 24), (-130, 105, 34))):
        s = back_out((k - j * 0.1) / 0.15)
        if s > 0.03:
            c.put(('c', j, int(s * 10)), lambda r=r, s=int(s * 10) / 10: p_blob(r * u * s, WHITE, seed=j, stitch=False),
                  x0 + dx * u, y0 + dy * u)
    s = back_out((k - 0.32) / 0.25)
    if s > 0.03:
        si = int(s * 20)
        br = 1 + 0.02 * math.sin(c.t * 4)
        c.put(('b', si), lambda si=si: p_thought(460 * u * si / 20, 260 * u * si / 20), x0 + 60 * u, y0 - 30 * u)


@effect('speech_bubble_pop', 'comic', 'Speech bubble: an empty stitched felt speech bubble with a tail pops in and breathes.',
        dur=2.0, loop=False, at=(0.55, 0.3))
def _speech(c):
    u = c.u
    x0, y0 = c.at()
    k = c.t / c.D
    s = back_out(min(1, k * 3.5)) * (1 + 0.015 * math.sin(c.t * 5))
    si = int(s * 30)
    if not si:
        return
    def b(s=si / 30):
        pts = wobble(ellipse_pts(260 * u * s, 150 * u * s), 0.02, 3)
        p = Piece().poly(pts, WHITE)
        p.poly([(-120 * u * s, 90 * u * s), (-40 * u * s, 120 * u * s), (-190 * u * s, 230 * u * s)], WHITE)
        p.stitch_inset(pts, 18 * u * s, '#cfc6b4', w=2.5 * u, dash=10 * u, gap=7 * u)
        return p
    c.put(('b', si), b, x0, y0)


# ============================================================ MONEY

def p_bill(w, col='#8cc47a', sy=1.0, ang=0.0):
    h = w * 0.5
    outer = rrect_pts(w, h, w * 0.04)
    p = Piece().poly(xform(outer, 1, max(0.1, sy), ang), col)
    if sy > 0.25:
        p.layer(depth=0.35, shadow=0.2)
        p.poly(xform(rrect_pts(w * 0.82, h * 0.7, w * 0.03), 1, sy, ang), lighter(col, 0.25))
        p.layer(depth=0.4, shadow=0.2)
        p.poly(xform(ellipse_pts(h * 0.26), 1, sy, ang), darker(col, 0.12))
        for dx in (-0.32, 0.32):
            p.poly(xform(ellipse_pts(h * 0.1) + (w * dx, 0), 1, sy, ang), darker(col, 0.1))
        if w > 70:
            p.stitch(xform(rrect_pts(w * 0.9, h * 0.82, w * 0.035), 1, sy, ang), darker(col, 0.25), w=1.8, dash=w * 0.05, gap=w * 0.04)
    return p


@effect('bills_fall', 'money', 'Money rain: blank green felt banknotes fluttering and flipping down.', dur=3.0, density=30)
def _bills(c):
    u = c.u
    R = c.R(100)
    for i, age in c.emit(int(c.p['density']), 4.2):
        r = R[i]
        x = r[0] * c.W + 80 * u * math.sin(age * 1.6 + r[1] * 6)
        y = -80 * u + age * (260 + 80 * r[2]) * u
        ia, a = qa(0.6 * math.sin(age * 1.6 + r[1] * 6 + 1) + r[3] * 0.6, 32)
        iv, sy = qv(abs(math.cos(age * (2.5 + 2 * r[4]) + r[5] * 6)), 6)
        c.put(('b', ia, iv), lambda a=a, sy=sy: p_bill(150 * u, '#8cc47a', sy, a), x, y)


@effect('coins_rain', 'money', 'Coin rain: stitched gold felt coins spinning as they fall.', dur=2.0, density=40)
def _coins(c):
    u = c.u
    R = c.R(100)
    for i, age in c.emit(int(c.p['density']), 2.0):
        r = R[i]
        x = r[0] * c.W
        y = -60 * u + age * (620 + 200 * r[2]) * u
        iv, sx = qv(abs(math.cos(age * (5 + 3 * r[4]) + r[5] * 6)), 8)
        sz = int(r[3] * 2)
        c.put(('c', iv, sz), lambda sx=sx, sz=sz: p_coin((34 + 8 * sz) * u, sx), x, y)


@effect('coin_burst', 'money', 'Jackpot: a fountain of spinning gold felt coins bursts up and falls back.', dur=2.5, loop=False,
        at=(0.5, 0.9), count=60)
def _coin_burst(c):
    u = c.u
    x0, y0 = c.at()
    R = c.R(100)
    g = 2400 * u
    for i in range(int(c.p['count'])):
        r = R[i]
        tt = c.t - 1.3 * r[0]
        if tt < 0:
            continue
        a = -math.pi / 2 + (r[1] - 0.5) * 1.1
        v = (1300 + 500 * r[2]) * u
        x = x0 + math.cos(a) * v * tt
        y = y0 + math.sin(a) * v * tt + 0.5 * g * tt * tt
        if y > c.H + 60 * u:
            continue
        iv, sx = qv(abs(math.cos(tt * (8 + 4 * r[3]) + r[4] * 6)), 8)
        c.put(('c', iv), lambda sx=sx: p_coin(36 * u, sx), x, y)


@effect('coin_stack_grow', 'money', 'Savings: gold felt coins drop one by one onto three growing stacks.', dur=3.0, loop=False,
        at=(0.5, 0.85))
def _coin_stack(c):
    u = c.u
    x0, y0 = c.at()
    n = 8
    th = 28 * u
    for s, dx in enumerate((-230, 0, 230)):
        for j in range(n):
            st = (j * 3 + s) * c.D * 0.85 / (n * 3)
            tt = c.t - st
            if tt < 0:
                continue
            ytar = y0 - j * th
            fall = 0.25
            if tt < fall:
                y = ytar - (1 - (tt / fall) ** 2) * 500 * u
            else:
                y = ytar - 10 * u * math.exp(-(tt - fall) * 20) * abs(math.sin((tt - fall) * 40))
            def b():
                p = Piece().poly(rrect_pts(150 * u, th * 1.05, th * 0.45), darker(GOLD, 0.1))
                p.layer(depth=0.4, shadow=0.2)
                p.poly(ellipse_pts(70 * u, th * 0.32) + (0, -th * 0.18), lighter(GOLD, 0.15))
                return p
            c.put('c', b, x0 + dx * u + (j % 2) * 3 * u, y)


def p_gem(r, col, sx=1.0):
    p = Piece()
    pts = np.array([(-1, -0.35), (-0.55, -0.8), (0.55, -0.8), (1, -0.35), (0, 0.95)])
    p.poly(xform(pts, r * sx, r), col)
    p.layer(depth=0.35, shadow=0.15)
    p.poly(xform([(-0.55, -0.8), (0.55, -0.8), (0.35, -0.35), (-0.35, -0.35)], r * sx, r), lighter(col, 0.35))
    p.poly(xform([(-0.35, -0.35), (0.35, -0.35), (0, 0.95)], r * sx, r), lighter(col, 0.15))
    return p


@effect('gems_rain', 'money', 'Treasure: faceted felt gems falling, turning and twinkling.', dur=3.0, density=22)
def _gems(c):
    u = c.u
    R = c.R(100)
    cols = ('#e0445a', '#4fb8ad', '#5f9fd8', '#9a74cf', '#7cbf5a')
    for i, age in c.emit(int(c.p['density']), 3.4):
        r = R[i]
        x = r[0] * c.W
        y = -60 * u + age * (380 + 100 * r[2]) * u
        iv, sx = qv(abs(math.cos(age * 3 + r[4] * 6)), 6)
        col = cols[i % 5]
        c.put(('g', i % 5, iv), lambda col=col, sx=sx: p_gem(52 * u, col, 0.3 + 0.7 * sx), x, y)
        if math.sin(age * 5 + r[5] * 6) > 0.8:
            c.put('tw', lambda: p_spark(30 * u, WHITE), x + 26 * u, y - 26 * u)


# ============================================================ MAGIC

def _path(c, q, x0, y0, rx, ry):
    a = TAU * q
    return x0 + rx * math.sin(a), y0 + ry * math.sin(2 * a)


@effect('glitter_trail', 'magic', 'Glitter trail: a bright felt star flies a figure-eight leaving twinkling sparkles that drift down.',
        dur=3.0, at=(0.5, 0.45))
def _glitter(c):
    u = c.u
    x0, y0 = c.at()
    R = c.R(200)
    life = 1.0
    cols = (YELLOW, PINK, WHITE, '#9fd0ee', '#c9a6f0')
    for i, age in c.emit(110, life):
        r = R[i]
        st = c.t - age
        px, py = _path(c, st / c.D, x0, y0, 600 * u, 200 * u)
        x = px + (r[0] - 0.5) * 50 * u
        y = py + (r[1] - 0.5) * 50 * u + age * 90 * u
        s = (1 - age / life) * (0.6 + 0.4 * math.sin(age * 20 + r[2] * 6))
        si = int(s * 8)
        if si <= 0:
            continue
        col = cols[i % 5]
        if i % 3 == 0:
            c.put(('s', si, i % 5), lambda si=si, col=col: p_spark(36 * u * si / 8, col), x, y)
        else:
            c.put(('d', si, i % 5), lambda si=si, col=col: p_blob(13 * u * si / 8 + 3 * u, col, seed=1, stitch=False), x, y)
    px, py = _path(c, c.t / c.D, x0, y0, 600 * u, 200 * u)
    c.cv.glow(px, py, 70 * u, '#fff2a8', 0.35)
    ia, aa = qa(c.t * 4, 20)
    c.put(('h', ia), lambda aa=aa: p_star(44 * u, YELLOW, ang=aa), px, py)


@effect('stars_swirl', 'magic', 'Star vortex: felt stars spiralling around a centre, those near the middle shrink in.', dur=3.0,
        at=(0.5, 0.5))
def _stars_swirl(c):
    u = c.u
    x0, y0 = c.at()
    cols = (YELLOW, '#c9a6f0', '#9fd0ee', PINK, WHITE)
    for i, age in c.emit(30, 3.0):
        q = age / 3.0
        rad = 480 * u * (1 - q) + 20 * u
        a = i * 2.4 + q * TAU * 1.0
        x = x0 + math.cos(a) * rad * 1.3
        y = y0 + math.sin(a) * rad * 0.75
        s = 0.3 + 0.9 * (1 - q)
        si = int(s * 8)
        ia, aa = qa(a * 2, 20)
        col = cols[i % 5]
        c.put(('s', si, ia, i % 5), lambda si=si, aa=aa, col=col: p_star(34 * u * si / 8, col, ang=aa, stitch=False), x, y,
              fade(age, 3.0, 0.15, 0.2))
    c.cv.glow(x0, y0, 120 * u, '#e8d8ff', 0.3)


@effect('portal', 'magic', 'Magic portal: rotating felt rings in purple and teal with spiral arms, pulsing, sparkles drawn in.',
        dur=3.0, at=(0.5, 0.5))
def _portal(c):
    u = c.u
    x0, y0 = c.at()
    br = 1 + 0.04 * c.osc(2)
    c.cv.glow(x0, y0, 360 * u, '#b48cf0', 0.30)
    ring_cols = ('#4a3a8a', '#6d55b0', '#4fb8ad', '#9a74cf', '#2e2a5a')
    for j, col in enumerate(ring_cols):
        r = (330 - j * 62) * u
        c.put(('r', j), lambda r=r, col=col, j=j: Piece().poly(wobble(ellipse_pts(r, r * 0.92), 0.025, j + 3), col), x0, y0)
    ia, aa = qa(-TAU * c.t / c.D * (2 / 3), 60)  # 3-fold arms: one turn of 120 deg per loop... keeps loop
    def arms(aa=aa):
        p = Piece().layer(depth=0.5)
        for k in range(3):
            a = np.linspace(0, TAU * 0.8, 50)
            rr = 300 * u * (1 - a / a[-1] * 0.85)
            pts = np.stack([np.cos(a + aa + k * TAU / 3) * rr, np.sin(a + aa + k * TAU / 3) * rr * 0.92], 1)
            p.stroke(pts, 16 * u * 1, ('#c9a6f0', '#7fe0d0', '#f2c6ff')[k])
        return p
    c.put(('a', ia % 20), arms, x0, y0)
    for i, age in c.emit(14, 1.5, k=3):
        q = age / 1.5
        a = i * 2.1 - q * 2.0
        rad = 520 * u * (1 - ease_in(q))
        c.put('sp', lambda: p_spark(18 * u, WHITE), x0 + math.cos(a) * rad * 1.1, y0 + math.sin(a) * rad, fade(age, 1.5, 0.2, 0.1))
    c.cv.glow(x0, y0, 70 * u * br, '#ffffff', 0.45)


@effect('magic_dust', 'magic', 'Magic dust: tiny glowing felt motes rising and twinkling in a column.', dur=3.0, at=(0.5, 0.85),
        width=0.35)
def _magic_dust(c):
    u = c.u
    x0, y0 = c.at()
    R = c.R(100)
    cols = ('#fff2a8', '#c9a6f0', '#9fe0f0', '#ffd0e6')
    for i, age in c.emit(60, 2.5):
        r = R[i]
        x = x0 + (r[0] - 0.5) * c.p['width'] * c.W + 30 * u * math.sin(age * 2 + r[1] * 6)
        y = y0 - age * (220 + 100 * r[2]) * u
        tw = 0.5 + 0.5 * math.sin(age * 9 + r[3] * 6)
        op = fade(age, 2.5, 0.15, 0.3)
        col = cols[i % 4]
        c.cv.glow(x, y, 30 * u, col, 0.45 * op * tw)
        if i % 4 == 0:
            c.put(('s', i % 4), lambda col=col: p_spark(30 * u, col), x, y, op * (0.4 + 0.6 * tw))
        else:
            c.put(('d', i % 4), lambda col=col: p_blob(10 * u, col, seed=2, stitch=False), x, y, op)


@effect('orbiting_orbs', 'magic', 'Orbiting orbs: glowing felt balls circling a centre on a tilted orbit, with fading trails.',
        dur=3.0, at=(0.5, 0.5))
def _orbs(c):
    u = c.u
    x0, y0 = c.at()
    cols = ('#7fe0d0', '#f2a6d8', '#ffe28a', '#a8b8ff')
    items = []
    for k in range(4):
        for tr in range(6, -1, -1):
            a = TAU * (c.t / c.D + k / 4) - tr * 0.09
            z = math.sin(a)
            items.append((z, k, tr, a))
    for z, k, tr, a in sorted(items):
        x = x0 + math.cos(a) * 330 * u
        y = y0 + z * 90 * u
        s = (0.75 + 0.25 * z) * (1 - tr * 0.11)
        si = int(s * 12)
        if tr == 0:
            c.cv.glow(x, y, 70 * u * s, cols[k], 0.4)
        c.put(('o', k, si), lambda k=k, si=si: p_blob(34 * u * si / 12, cols[k], seed=k, stitch=False), x, y, 1 if tr == 0 else 0.55 - tr * 0.07)


@effect('shooting_star', 'magic', 'Shooting star: a felt star streaks diagonally across the sky with a tapering dotted tail.',
        dur=2.0)
def _shooting(c):
    u = c.u
    k = c.t / c.D
    x0, y0, x1, y1 = -0.1 * c.W, 0.15 * c.H, 1.1 * c.W, 0.55 * c.H
    for j in range(14):
        kk = k - j * 0.012
        if not 0 <= kk <= 1:
            continue
        x, y = x0 + (x1 - x0) * kk, y0 + (y1 - y0) * kk
        if j == 0:
            c.cv.glow(x, y, 80 * u, '#fff2a8', 0.4)
            ia, aa = qa(c.t * 6, 20)
            c.put(('s', ia), lambda aa=aa: p_star(46 * u, YELLOW, ang=aa), x, y)
        else:
            c.put(('t', j), lambda j=j: p_blob((22 - j * 1.4) * u, ('#fff2a8', '#ffe48a', '#f6c94c')[j % 3], seed=j, stitch=False), x, y,
                  1 - j / 15)


@effect('twinkle_field', 'magic', 'Night twinkle: felt stars across the top of the frame twinkling at different rhythms.',
        dur=3.0, density=40)
def _twinkle(c):
    u = c.u
    R = c.R(100)
    for i in range(int(c.p['density'])):
        r = R[i]
        x, y = r[0] * c.W, r[1] * c.H * 0.6
        cyc = 1 + int(r[2] * 3)
        s = 0.55 + 0.45 * math.sin(TAU * cyc * c.t / c.D + r[3] * 6)
        si = int(s * 8)
        big = r[4] > 0.75
        if big:
            c.put(('b', si), lambda si=si: p_star(46 * u * si / 8, '#ffe48a', stitch=False), x, y)
        else:
            c.put(('s', si), lambda si=si: p_spark(30 * u * si / 8, '#fff6cc'), x, y)


# ============================================================ TECH

@effect('glitch_blocks', 'tech', 'Glitch: felt blocks in cyan, magenta and off-white flicker and jump in horizontal bands.',
        dur=2.0, scale=0.5)
def _glitch(c):
    u = c.u
    fi = int(c.t * 12) % 24
    r = np.random.default_rng([c.seed, fi])
    on = r.random() < 0.75
    if not on:
        return
    p = Piece().layer(depth=0.5)
    cols = ('#4fd0e0', '#e05aa8', '#f2efe6', '#3a3440', '#9be05a')
    nb = int(4 + 10 * r.random())
    for k in range(nb):
        y = r.random() * c.H
        h = (8 + 70 * r.random() ** 2) * u
        x = r.random() * c.W
        w = (80 + 700 * r.random() ** 2) * u
        p.poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], cols[k % 5])
    c.full(p, op=0.92)


@effect('scanlines', 'tech', 'Old screen: dark felt scanlines with a lighter band rolling down the frame.', dur=2.0, scale=0.5)
def _scanlines(c):
    u = c.u
    sp = 12 * u
    def lines():
        p = Piece().layer(depth=0.25, alpha=0.32, shadow=0.3)
        y = 0
        while y < c.H + sp:
            p.poly([(0, y), (c.W, y), (c.W, y + sp * 0.4), (0, y + sp * 0.4)], '#1e1c24')
            y += sp
        return p
    c.full(lines, key='lines')
    yb = -200 * u + (c.H + 400 * u) * c.t / c.D
    c.cv.glow(c.W / 2, yb, 120 * u, '#ffffff', 0.0)
    band = Piece().layer(depth=0.3, alpha=0.18, shadow=0)
    band.poly([(0, yb - 50 * u), (c.W, yb - 50 * u), (c.W, yb + 50 * u), (0, yb + 50 * u)], '#f2f2ea')
    c.full(band)


@effect('loading_spinner', 'tech', 'Loading spinner: a ring of felt dots with a bright dot chasing around (no text).', dur=1.0,
        at=(0.5, 0.5))
def _spinner(c):
    u = c.u
    x0, y0 = c.at()
    n = 10
    head = (c.t / c.D) * n
    for k in range(n):
        a = -math.pi / 2 + k * TAU / n
        d = (head - k) % n
        s = max(0.0, 1 - d / 6)
        si = int(s * 6)
        col = mix('#c9c2b6', '#4fb8ad', s)
        c.put(('d', si), lambda si=si, col=col: p_blob((16 + 10 * si / 6) * u, col, seed=1, stitch=False),
              x0 + math.cos(a) * 110 * u, y0 + math.sin(a) * 110 * u)


@effect('notification_dots', 'tech', 'Notifications: red felt badge dots pop in with a bounce at several spots and pulse.',
        dur=3.0)
def _notif(c):
    u = c.u
    spots = ((0.25, 0.3, 0.0), (0.7, 0.25, 0.2), (0.45, 0.62, 0.4), (0.8, 0.7, 0.55), (0.15, 0.72, 0.7))
    for j, (fx, fy, ph) in enumerate(spots):
        k = (c.t / c.D - ph) % 1.0
        s = back_out(min(1, k * 6)) * (1 + 0.08 * math.sin(k * 20) * (k > 0.2)) * (1 if k < 0.88 else max(0, (1 - k) / 0.12))
        si = int(s * 16)
        if si <= 0:
            continue
        def b(si=si):
            p = p_blob(40 * u * si / 16, '#e0443a', seed=2, stitch=False)
            p.layer(depth=0.4, shadow=0.2)
            p.poly(ellipse_pts(13 * u * si / 16), WHITE)
            return p
        c.put(('n', si), b, fx * c.W, fy * c.H)


@effect('signal_waves', 'tech', 'Signal: felt arcs pulsing outward one after another from a dot (wireless, broadcast).', dur=1.5,
        at=(0.5, 0.6))
def _signal(c):
    u = c.u
    x0, y0 = c.at()
    c.put('dot', lambda: p_blob(28 * u, '#4fb8ad', seed=1, stitch=False), x0, y0)
    for j in range(3):
        k = (c.t / c.D * 3 - j) % 3
        on = 1 - min(1, abs(k - 0.5) / 1.2)
        col = mix('#c9c2b6', '#4fb8ad', max(0, on))
        r = (90 + 75 * j) * u
        ci = int(max(0, on) * 6)
        c.put(('a', j, ci), lambda r=r, col=col: Piece().stroke(arc_pts(r, -math.pi * 0.75, -math.pi * 0.25, 30), 26 * u, col), x0, y0)


@effect('typing_dots', 'tech', 'Typing indicator: three felt dots bouncing in turn inside a soft bubble (no text).', dur=1.2,
        at=(0.5, 0.5))
def _typing(c):
    u = c.u
    x0, y0 = c.at()
    def bub():
        pts = rrect_pts(300 * u, 140 * u, 70 * u)
        p = Piece().poly(pts, WHITE)
        p.poly([(-110 * u, 40 * u), (-60 * u, 60 * u), (-150 * u, 110 * u)], WHITE)
        p.stitch_inset(pts, 14 * u, '#d6cfc0', w=2.4 * u, dash=9 * u, gap=6 * u)
        return p
    c.put('b', bub, x0, y0)
    for j in range(3):
        k = (c.t / c.D - j * 0.18) % 1.0
        h = math.sin(math.pi * min(1, k / 0.35)) if k < 0.35 else 0
        col = mix('#b8b0a2', '#6d6577', h)
        c.put(('d', int(h * 6)), lambda col=col: p_blob(20 * u, col, seed=1, stitch=False), x0 + (j - 1) * 70 * u, y0 - h * 26 * u)


@effect('data_blocks', 'tech', 'Data rain: columns of small green felt squares streaming down and fading.', dur=2.0, density=60)
def _data(c):
    u = c.u
    R = c.R(200)
    ncol = 24
    for i, age in c.emit(int(c.p['density']), 1.6):
        r = R[i]
        x = (int(r[0] * ncol) + 0.5) * c.W / ncol
        y0 = -60 * u + age * (700 + 300 * r[1]) * u
        for j in range(6):
            y = y0 - j * 34 * u
            col = ('#c8f0b0', '#7cd65a', '#4fa83a', '#3a8a2e')[min(3, j)]
            c.put(('q', min(3, j)), lambda col=col: Piece().poly(rrect_pts(24 * u, 24 * u, 5 * u), col), x, y, 1 - j / 7)


@effect('radar_sweep', 'tech', 'Radar: a stitched felt radar disc with a rotating sweep wedge and blips lighting up.', dur=3.0,
        at=(0.5, 0.5))
def _radar(c):
    u = c.u
    x0, y0 = c.at()
    R0 = 300 * u
    def disc():
        p = Piece().poly(ellipse_pts(R0), '#2f5a48')
        p.layer(depth=0.3, shadow=0.1)
        for f in (0.33, 0.66):
            p.stroke(np.vstack([ellipse_pts(R0 * f), ellipse_pts(R0 * f)[:1]]), 5 * u, '#4f8a6a')
        p.stroke([(-R0, 0), (R0, 0)], 4 * u, '#4f8a6a')
        p.stroke([(0, -R0), (0, R0)], 4 * u, '#4f8a6a')
        p.stitch(ellipse_pts(R0 * 0.93), '#7fc49a', w=2.5 * u, dash=10 * u, gap=7 * u)
        return p
    c.put('disc', disc, x0, y0)
    ang = TAU * c.t / c.D
    ia, aa = qa(ang, 96)
    def wedge(aa=aa):
        pts = [(0, 0)] + [tuple(v) for v in arc_pts(R0 * 0.97, aa - 0.6, aa, 20)]
        return Piece().layer(depth=0.2, alpha=0.55, shadow=0).poly(pts, '#8ff0b0')
    c.put(('w', ia), wedge, x0, y0)
    R = c.R(10)
    for j in range(5):
        a = R[j][0] * TAU
        d = (0.25 + 0.65 * R[j][1]) * R0
        since = (ang - a) % TAU
        op = max(0.0, 1 - since / 3.0)
        if op > 0.02:
            c.put('blip', lambda: p_blob(13 * u, '#d8ffb0', seed=1, stitch=False), x0 + math.cos(a) * d, y0 + math.sin(a) * d, op)


# ============================================================ NATURE

def p_butterfly(r, col, flap):
    p = Piece()
    w = max(0.12, flap)
    for s in (-1, 1):
        p.poly(xform(ellipse_pts(r * 0.55, r * 0.45) + (r * 0.5, -r * 0.25), w * s, 1), col)
        p.poly(xform(ellipse_pts(r * 0.38, r * 0.32) + (r * 0.42, r * 0.32), w * s, 1), darker(col, 0.12))
    p.layer(depth=0.4, shadow=0.2)
    for s in (-1, 1):
        p.poly(xform(ellipse_pts(r * 0.17) + (r * 0.55, -r * 0.3), w * s, 1), lighter(col, 0.5))
    p.layer(depth=0.6)
    p.poly(ellipse_pts(r * 0.1, r * 0.48), '#4a3a3a')
    p.stroke(bezier((0, -r * 0.4), (r * 0.1, -r * 0.7), (r * 0.25, -r * 0.8)), r * 0.04, '#4a3a3a')
    p.stroke(bezier((0, -r * 0.4), (-r * 0.1, -r * 0.7), (-r * 0.25, -r * 0.8)), r * 0.04, '#4a3a3a')
    return p


@effect('butterflies', 'nature', 'Butterflies: felt butterflies with spotted wings flutter along looping paths.', dur=4.0, count=5)
def _butterflies(c):
    u = c.u
    R = c.R(20)
    cols = ('#f2a0c8', '#f6d353', '#9fd0ee', '#f08a3a', '#c39be0')
    for i in range(int(c.p['count'])):
        r = R[i]
        a = TAU * c.t / c.D
        x = (0.15 + 0.7 * r[0]) * c.W + 260 * u * math.sin(a + r[1] * 6)
        y = (0.2 + 0.5 * r[2]) * c.H + 120 * u * math.sin(2 * a + r[3] * 6) + 20 * u * math.sin(TAU * 8 * c.t / c.D + i)
        iv, fl = qv(abs(math.sin(TAU * 10 * c.t / c.D + r[4] * 6)), 6)
        c.put(('b', i % 5, iv), lambda col=cols[i % 5], fl=fl: p_butterfly(70 * u, col, fl), x, y)


@effect('fireflies', 'nature', 'Fireflies: little felt bugs with blinking warm glows wandering in the dusk.', dur=4.0, count=26)
def _fireflies(c):
    u = c.u
    R = c.R(60)
    for i in range(int(c.p['count'])):
        r = R[i]
        a = TAU * c.t / c.D
        x = r[0] * c.W + 90 * u * math.sin(a + r[1] * 6) + 30 * u * math.sin(3 * a + r[5] * 6)
        y = (0.15 + 0.75 * r[2]) * c.H + 60 * u * math.sin(2 * a + r[3] * 6)
        bl = max(0.0, math.sin(TAU * (1 + int(r[4] * 2)) * c.t / c.D + r[6] * 6)) ** 2
        c.cv.glow(x, y, 46 * u, '#e8ff7a', 0.55 * bl)
        c.put(('f', int(bl * 4)), lambda bl=int(bl * 4) / 4: p_blob(8 * u, mix('#8a8a4a', '#f4ff9a', bl), seed=1, stitch=False), x, y)


def p_bird(r, col, flap):
    p = Piece()
    p.poly(ellipse_pts(r * 0.5, r * 0.22), col)
    p.poly([(r * 0.35, -r * 0.12), (r * 0.62, -r * 0.02), (r * 0.35, r * 0.06)], '#f2b64a')
    wy = -r * 0.9 * flap
    p.poly([(-r * 0.2, -r * 0.05), (r * 0.15, -r * 0.05), (-r * 0.35, wy)], darker(col, 0.15))
    p.poly([(-r * 0.45, 0), (-r * 0.85, -r * 0.18), (-r * 0.85, r * 0.12)], col)
    return p


@effect('birds_flock', 'nature', 'Bird flock: small felt birds flapping across the sky in a loose V.', dur=4.0)
def _birds(c):
    u = c.u
    R = c.R(20)
    for i, age in c.emit(2, 4.0):
        x0 = -200 * u + age / 4.0 * (c.W + 400 * u)
        y0 = (0.22 + 0.15 * i) * c.H
        for b in range(7):
            r = R[b + 7 * i]
            row = (b + 1) // 2
            side = 1 if b % 2 else -1
            x = x0 - row * 100 * u
            y = y0 + side * row * 56 * u + 8 * u * math.sin(age * 5 + b)
            iv, fl = qv(0.5 + 0.5 * math.sin(age * 14 + r[0] * 6), 6)
            c.put(('b', iv), lambda fl=fl: p_bird(84 * u, '#4a4a5a', fl * 2 - 1), x, y)


@effect('petals_fall', 'nature', 'Petals: pink cherry petals tumbling and drifting down.', dur=3.0, density=40)
def _petals(c):
    u = c.u
    R = c.R(200)
    for i, age in c.emit(int(c.p['density']), 4.5):
        r = R[i]
        x = r[0] * c.W + 70 * u * math.sin(age * 1.5 + r[1] * 6) + 40 * u * age
        y = -40 * u + age * (220 + 80 * r[2]) * u
        ia, a = qa(age * 2 + r[3] * 6, 24)
        iv, sy = qv(abs(math.cos(age * 3 + r[4] * 6)), 4)
        col = ('#f7b8cc', '#f29ab6', '#fcd6e2')[i % 3]
        c.put(('p', i % 3, ia, iv), lambda col=col, a=a, sy=sy: p_petal(36 * u, col, a, 0.3 + 0.7 * sy), x, y)


def p_apple(r, col=RED):
    p = Piece().poly(wobble(np.vstack([xform(ellipse_pts(1.0), r * 0.55, r * 0.6, tx=-r * 0.32),
                                       ]), 0.0, 1), col) if False else Piece()
    t = np.linspace(0, TAU, 80, endpoint=False)
    x = np.sin(t) * (1 + 0.08 * np.cos(2 * t))
    y = -np.cos(t) * 0.92 + 0.12 * np.cos(2 * t) * (np.cos(t) > 0)
    p.poly(np.stack([x, y], 1) * r, col)
    p.layer(depth=0.3, shadow=0)
    p.ellipse(-r * 0.4, -r * 0.3, r * 0.12, r * 0.22, lighter(col, 0.5), 0.4)
    p.layer(depth=0.6)
    p.stroke([(0, -r * 0.75), (r * 0.1, -r * 1.15)], r * 0.1, BROWN)
    p.poly(xform(leaf_pts(), r * 0.35, r * 0.35, -0.5, tx=r * 0.35, ty=-r * 1.05), LEAF)
    return p


@effect('apples_fall', 'nature', 'Falling apples: shiny felt apples drop, bounce on the ground and roll away.', dur=3.0, floor=0.86)
def _apples(c):
    u = c.u
    R = c.R(20)
    fl = c.p['floor'] * c.H
    g = 2600 * u
    for i, age in c.emit(4, 3.0):
        r = R[i]
        x0 = (0.15 + 0.7 * r[0]) * c.W
        y0 = -60 * u
        rad = 70 * u
        th = math.sqrt(2 * (fl - rad - y0) / g)
        if age < th:
            x, y, rot = x0, y0 + 0.5 * g * age * age, 0
        else:
            ta = age - th
            vb = g * th * 0.35
            tb = 2 * vb / g
            dirn = 1 if r[1] > 0.5 else -1
            vx = dirn * 220 * u
            x = x0 + vx * ta
            y = fl - rad - (max(0.0, vb * ta - 0.5 * g * ta * ta) if ta < tb else 0)
            rot = (x - x0) / rad
        ia, aa = qa(rot, 24)
        def b(aa=aa):
            p = p_apple(rad, RED if i % 3 else '#9bc94a')
            for L in p.layers:
                L['parts'] = [(kk, xform(pp, ang=aa), cc, w) for kk, pp, cc, w in L['parts']]
            return p
        c.put(('a', i % 3 == 0, ia), b, x, y, fade(age, 3.0, 0.0, 0.12))


def p_seed(r):
    p = Piece().layer(depth=0.5)
    p.stroke([(0, 0), (0, r * 1.1)], r * 0.06, '#d8d0bc')
    for k in range(9):
        a = -math.pi / 2 + (k - 4) * 0.32
        p.stroke([(0, 0), (math.cos(a) * r, math.sin(a) * r)], max(2.5, r * 0.06), WHITE)
        p.circle(math.cos(a) * r, math.sin(a) * r, r * 0.07, WHITE)
    p.layer()
    p.ellipse(0, r * 1.15, r * 0.08, r * 0.16, '#8a7a5a')
    return p


@effect('dandelion_seeds', 'nature', 'Dandelion seeds: fluffy felt-and-thread parachutes floating up and across on the breeze.',
        dur=4.0, density=16)
def _seeds(c):
    u = c.u
    R = c.R(60)
    for i, age in c.emit(int(c.p['density']), 6.0):
        r = R[i]
        x = -60 * u + age * (300 + 120 * r[0]) * u
        y = (0.35 + 0.6 * r[1]) * c.H - age * (60 + 40 * r[2]) * u + 40 * u * math.sin(age * 1.3 + r[3] * 6)
        ia, aa = qa(0.3 * math.sin(age * 1.3 + r[3] * 6) + 0.3, 30)
        def b(aa=aa):
            p = p_seed(60 * u)
            for L in p.layers:
                L['parts'] = [(kk, xform(pp, ang=aa), cc, w) for kk, pp, cc, w in L['parts']]
            return p
        c.put(('s', ia), b, x, y)


def p_bee(r, flap):
    p = Piece()
    p.layer(depth=0.4, alpha=0.85)
    for s in (-1, 1):
        p.poly(xform(ellipse_pts(r * 0.35, r * 0.5 * max(0.2, flap)) + (s * r * 0.15, -r * 0.55), 1), '#e8f4fa')
    p.layer()
    p.poly(ellipse_pts(r * 0.7, r * 0.48), '#f6c94c')
    p.layer(depth=0.3, shadow=0)
    for dx in (-0.25, 0.15):
        p.poly([(r * dx, -r * 0.46), (r * (dx + 0.18), -r * 0.44), (r * (dx + 0.18), r * 0.44), (r * dx, r * 0.46)], INK)
    p.poly([(r * 0.62, -r * 0.08), (r * 0.9, 0), (r * 0.62, r * 0.08)], INK)
    p.circle(-r * 0.48, -r * 0.1, r * 0.08, INK)
    return p


@effect('bees', 'nature', 'Bees: striped felt bees buzzing around in loops with blurry flapping wings.', dur=3.0, count=4,
        at=(0.5, 0.45))
def _bees(c):
    u = c.u
    x0, y0 = c.at()
    R = c.R(10)
    for i in range(int(c.p['count'])):
        r = R[i]
        a = TAU * c.t / c.D * (1 if i % 2 else -1) + r[0] * 6
        x = x0 + math.cos(a) * (220 + 120 * r[1]) * u + 15 * u * math.sin(TAU * 9 * c.t / c.D + i)
        y = y0 + math.sin(2 * a) * (90 + 60 * r[2]) * u + 10 * u * math.sin(TAU * 13 * c.t / c.D + i)
        dx = -math.sin(a) * (1 if i % 2 else -1)
        iv, fl = qv(abs(math.sin(TAU * 18 * c.t / c.D + i)), 4)
        def b(fl=fl, flip=dx > 0):
            p = p_bee(46 * u, fl)
            if flip:
                for L in p.layers:
                    L['parts'] = [(kk, pp * (-1, 1), cc, w) for kk, pp, cc, w in L['parts']]
            return p
        c.put(('b', iv, dx > 0), b, x, y)


@effect('autumn_leaves', 'nature', 'Autumn leaves: veined felt leaves drifting down, swaying and flipping.', dur=4.0, density=22)
def _autumn(c):
    u = c.u
    R = c.R(200)
    cols = ('#e8833a', '#d9542f', '#f2b64a', '#a8c45a', '#c9772f')
    for i, age in c.emit(int(c.p['density']), 6.0):
        r = R[i]
        x = r[0] * c.W + 90 * u * math.sin(age * 1.2 + r[1] * 6)
        y = -50 * u + age * (190 + 60 * r[2]) * u
        ia, a = qa(0.9 * math.sin(age * 1.2 + r[1] * 6 + 0.8) + r[3], 32)
        iv, sy = qv(abs(math.cos(age * 1.5 + r[4] * 6)), 4)
        col = cols[i % 5]
        c.put(('l', i % 5, ia, iv), lambda col=col, a=a, sy=sy: p_leaf(56 * u, col, a, 0.35 + 0.65 * sy), x, y)


@effect('grass_edge', 'nature', 'Grass: a fringe of felt grass blades along the bottom, swaying in a breeze wave.', dur=3.0)
def _grass(c):
    u = c.u
    R = c.R(200)
    n = 70
    cols = ('#6fae4a', '#5f9e46', '#86c25a', '#4f8a3a')
    for k in range(n):
        r = R[k]
        x = (k + r[0]) * c.W / n - 10 * u
        h = (110 + 90 * r[1]) * u
        sw = 0.18 * math.sin(TAU * c.t / c.D - x / c.W * TAU * 1.0) + 0.05 * r[2]
        ia, aa = qa(sw, 120)
        hv = int(r[1] * 3)
        col = cols[k % 4]
        def b(aa=aa, hv=hv, col=col):
            hh = (110 + 45 * hv) * u
            base = 16 * u
            sa = aa - TAU if aa > math.pi else aa
            pts = []
            for j in range(9):
                f = j / 8
                bend = sa * f * f * hh
                pts.append((-base * (1 - f) + bend, -hh * f))
            for j in range(8, -1, -1):
                f = j / 8
                bend = sa * f * f * hh
                pts.append((base * (1 - f) + bend, -hh * f))
            return Piece().poly(pts, col)
        c.put(('g', ia, hv, k % 4), b, x, c.H + 10 * u)


def p_flower(r, col, open_=1.0):
    p = Piece()
    n = 6
    for k in range(n):
        a = k * TAU / n
        p.poly(xform(ellipse_pts(r * 0.5 * open_ + 1, r * 0.3 * open_ + 1) + (r * 0.55 * open_, 0), ang=a), col)
    p.layer(depth=0.6)
    p.poly(ellipse_pts(r * 0.32 * max(0.4, open_)), YELLOW)
    return p


@effect('flowers_pop', 'nature', 'Flowers: stems grow up from the ground and felt blossoms pop open one after another.', dur=3.0,
        loop=False, floor=0.95)
def _flowers(c):
    u = c.u
    R = c.R(20)
    cols = (PINK, '#f28f6a', '#c39be0', WHITE, '#f6d353', '#9fd0ee')
    n = 7
    for i in range(n):
        r = R[i]
        x = (i + 0.5) / n * c.W + (r[0] - 0.5) * 80 * u
        st = i * 0.18 + 0.1 * r[1]
        k = (c.t - st) / 1.0
        if k <= 0:
            continue
        hh = (220 + 160 * r[2]) * u * ease_out(min(1, k))
        yb = c.p['floor'] * c.H
        hi = int(hh / u / 10)
        c.put(('st', hi), lambda hi=hi: Piece().stroke(bezier((0, 0), (12 * u, -hi * 5 * u), (0, -hi * 10 * u), 12), 11 * u, LEAF)
              .layer(depth=0.6).poly(xform(leaf_pts(), 34 * u, 34 * u, -0.6, tx=26 * u, ty=-hi * 4 * u), '#7cbf5a'), x, yb)
        s = back_out((c.t - st - 0.7) / 0.4)
        if s > 0.03:
            si = int(s * 16)
            c.put(('f', i % 6, si), lambda col=cols[i % 6], si=si: p_flower(60 * u * si / 16, col), x, yb - hh)


# ============================================================ TRANSITIONS

def _curtain(c, k):
    """k=0 open, 1 closed."""
    u = c.u
    W, H = c.W, c.H
    for side in (-1, 1):
        w = (W / 2 + 30 * u) * k
        if w < 2:
            continue
        x_edge = w if side == -1 else W - w  # inner edge
        p = Piece().layer(depth=1.2)
        nf = 7
        xs_outer = 0 if side == -1 else W
        p.poly([(xs_outer, -10), (x_edge, -10), (x_edge, H + 10), (xs_outer, H + 10)], '#a8243a')
        p.layer(depth=0.5, shadow=0.4)
        for j in range(nf):
            f = (j + 0.5) / nf
            fx = xs_outer + (x_edge - xs_outer) * f
            fw = abs(x_edge - xs_outer) / nf * 0.32
            p.poly([(fx - fw, -10), (fx + fw, -10), (fx + fw * 0.7, H + 10), (fx - fw * 0.7, H + 10)], '#8c1c30')
        p.layer(depth=0.7)
        hem = np.array([(xs_outer + (x_edge - xs_outer) * f, H - 40 * u + 14 * u * math.sin(f * TAU * nf)) for f in np.linspace(0, 1, 60)])
        p.poly(np.vstack([hem, [[x_edge, H + 10], [xs_outer, H + 10]]]), '#e9b53a')
        p.stitch(hem + (0, 14 * u), '#fff0b8', w=2.5 * u, dash=10 * u, gap=7 * u, closed=False)
        c.full(p)
    # valance
    p = Piece().layer(depth=1.0)
    pts = [(0, -10), (W, -10), (W, 90 * u)] + [(W - f * W, 90 * u + 26 * u * abs(math.sin(f * math.pi * 8))) for f in np.linspace(0, 1, 80)] + [(0, 90 * u)]
    p.poly(pts, '#8c1c30')
    p.stitch([(x, 70 * u) for x in np.linspace(0, W, 40)], '#e9b53a', w=3 * u, dash=12 * u, gap=8 * u, closed=False)
    c.full(lambda: p, key='valance')


@effect('curtain_close', 'transition', 'Theatre curtain closes: red velvet felt drapes with gold stitched hems slide in from both sides.',
        dur=2.0, loop=False, scale=0.5)
def _curtain_close(c):
    _curtain(c, ease_io(c.t / (c.D * 0.85)))


@effect('curtain_open', 'transition', 'Theatre curtain opens: red felt drapes part to reveal the scene.', dur=2.0, loop=False,
        scale=0.5)
def _curtain_open(c):
    _curtain(c, 1 - ease_io((c.t - c.D * 0.1) / (c.D * 0.85)))


def _iris(c, k):
    """k = hole radius fraction (1 full open, 0 closed)."""
    u = c.u
    x0, y0 = c.at()
    Rm = max(math.hypot(x0 - cx, y0 - cy) for cx in (0, c.W) for cy in (0, c.H)) + 30 * u
    r = Rm * k
    p = Piece().layer(depth=1.0)
    outer = [(-50, -50), (c.W + 50, -50), (c.W + 50, c.H + 50), (-50, c.H + 50), (-50, -50)]
    if r > 2:
        hole = wobble(ellipse_pts(r, r, 160), 0.006, 3) + (x0, y0)
        ring = np.vstack([hole, hole[:1]])[::-1]
        p.poly(outer, '#2e2a36')
        p.hole(hole)
        st = wobble(ellipse_pts(r + 16 * u, r + 16 * u, 160), 0.006, 3) + (x0, y0)
        p.stitch(st, '#d9cbb0', w=3 * u, dash=12 * u, gap=8 * u)
    else:
        p.poly(outer, '#2e2a36')
    c.full(p)


@effect('iris_close', 'transition', 'Iris out: a dark felt mask with a hand-stitched edge closes in a circle (focus at at=).',
        dur=2.0, loop=False, scale=0.5, at=(0.5, 0.5))
def _iris_close(c):
    _iris(c, 1 - ease_in(c.t / (c.D * 0.9)) if c.t < c.D * 0.9 else 0)


@effect('iris_open', 'transition', 'Iris in: the stitched felt mask opens from a point to reveal the scene.', dur=2.0, loop=False,
        scale=0.5, at=(0.5, 0.5))
def _iris_open(c):
    _iris(c, ease_in(max(0, c.t - 0.2) / (c.D * 0.85)))


@effect('page_tear', 'transition', 'Page tear: a felt sheet covering the frame rips along a jagged line and both halves fall away.',
        dur=2.5, loop=False, scale=0.5)
def _page_tear(c):
    u = c.u
    W, H = c.W, c.H
    r = np.random.default_rng(c.seed + 3)
    n = 26
    xs = np.linspace(-20, W + 20, n)
    ys = H * 0.5 + (xs - W / 2) * 0.25 + r.normal(0, 22 * u, n) + np.where(np.arange(n) % 2, 18 * u, -18 * u)
    tear = np.stack([xs, ys], 1)
    t = c.t
    rip = ease_io(t / 0.8)  # rip progress along the line
    sep = ease_in(max(0, (t - 0.7) / (c.D - 0.7)))
    col_top, col_bot = '#e8dfcc', '#ddd2bb'
    cut = int(rip * (n - 1))
    for half in (0, 1):
        if half == 0:
            pts = [(-30, -30), (W + 30, -30)] + [tuple(v) for v in tear[::-1]]
            dy = -sep * H * 0.9
            ang = -0.15 * sep
            col = col_top
        else:
            pts = [tuple(v) for v in tear] + [(W + 30, H + 30), (-30, H + 30)]
            dy = sep * H * 0.9
            ang = 0.12 * sep
            col = col_bot
        P = xform(np.array(pts) - (W / 2, H / 2), ang=ang, tx=W / 2, ty=H / 2 + dy)
        p = Piece().layer(depth=1.0)
        p.poly(P, col)
        edge = xform(tear - (W / 2, H / 2) + (0, -16 * u if half == 0 else 16 * u), ang=ang, tx=W / 2, ty=H / 2 + dy)
        p.layer(depth=0.4, shadow=0.2)
        fl = xform(tear - (W / 2, H / 2), ang=ang, tx=W / 2, ty=H / 2 + dy)
        band = np.vstack([fl, edge[::-1]])
        p.poly(band, WHITE)
        c.full(p)
    if sep == 0 and cut < n - 1:
        # still-joined part: cover the gap
        p = Piece().layer(depth=0.0, shadow=0)
        p.poly([tuple(v) for v in tear[cut:]] + [(W + 30, tear[-1][1] + 40), (tear[cut][0], tear[cut][1] + 40)], col_bot)
        p.poly([tuple(v) for v in tear[cut:]] + [(W + 30, tear[-1][1] - 40), (tear[cut][0], tear[cut][1] - 40)], col_top)
        c.full(p)


@effect('wipe_stitched', 'transition', 'Felt wipe: a felt panel with a zig-zag stitched leading edge slides across and covers the frame.',
        dur=1.5, loop=False, scale=0.5)
def _wipe(c):
    u = c.u
    k = ease_io(c.t / (c.D * 0.85))
    x = -80 * u + (c.W + 160 * u) * k
    if x < -60 * u:
        return
    p = Piece().layer(depth=1.0)
    edge = [(x + (14 * u if j % 2 else -14 * u), y) for j, y in enumerate(np.linspace(-20, c.H + 20, 40))]
    p.poly([(-30, -30)] + [(x, -30)] + edge + [(x, c.H + 30), (-30, c.H + 30)], '#5f8fb8')
    p.stitch([(x - 40 * u, y) for y in np.linspace(0, c.H, 30)], '#e6eef6', w=3 * u, dash=12 * u, gap=8 * u, closed=False)
    c.full(p)


@effect('patches_cover', 'transition', 'Patchwork cover: stitched felt squares drop in tile by tile until the frame is covered.',
        dur=2.5, loop=False, scale=0.5)
def _patches(c):
    u = c.u
    cols = ('#e8a07a', '#9fc4d8', '#c9b6e0', '#a8d08a', '#f2cf7a', '#e8a3b8')
    nx, ny = 8, 5
    tw, th = c.W / nx, c.H / ny
    R = c.R(nx * ny)
    p = Piece().layer(depth=0.8)
    order = np.argsort(R[:, 0] * 0.5 + (np.arange(nx * ny) % nx + np.arange(nx * ny) // nx) / (nx + ny))
    rank = np.empty(nx * ny, int)
    rank[order] = np.arange(nx * ny)
    any_ = False
    for idx in range(nx * ny):
        i, j = idx % nx, idx // nx
        st = rank[idx] / (nx * ny) * c.D * 0.75
        k = (c.t - st) / 0.3
        if k <= 0:
            continue
        s = min(1.0, back_out(k))
        dy = (1 - ease_out(min(1, k))) * -120 * u
        cx, cy = (i + 0.5) * tw, (j + 0.5) * th + dy
        pts = rrect_pts(tw * s + 2, th * s + 2, 8 * u) + (cx, cy)
        p.poly(pts, cols[(i + 2 * j) % 6])
        p.stitch_inset(pts, 14 * u, lighter(cols[(i + 2 * j) % 6], 0.5), w=2.5 * u, dash=10 * u, gap=7 * u)
        any_ = True
    if any_:
        c.full(p)


# Point effects (things that happen around a head or an object) are drawn bigger by default; size= scales them.
for _n in ('sweat_drops', 'anger_vein', 'question_marks', 'exclamation', 'zzz', 'hearts_float', 'heart_beat', 'dizzy_stars',
           'dizzy_swirl', 'idea_bulb', 'music_notes', 'shock_lines', 'anger_steam', 'grawlix_cloud', 'shine_glint', 'tears_stream',
           'loading_spinner', 'signal_waves', 'typing_dots', 'bees', 'orbiting_orbs', 'butterflies', 'steam', 'drip', 'candle',
           'campfire', 'thought_bubble', 'speech_bubble_pop', 'poof_vanish', 'sparkle_burst', 'impact_star'):
    EFFECTS[_n]['params'].setdefault('size', 1.25 if _n in ('heart_beat', 'thought_bubble', 'speech_bubble_pop', 'impact_star',
                                                           'poof_vanish', 'campfire', 'butterflies', 'candle') else 1.6)


def _public(name):
    def fx(t, params=None):
        return render(name, t, params)
    fx.__name__ = name
    fx.__doc__ = EFFECTS[name]['about']
    return fx


# every effect is also a module-level function: effects_lib.snow_light(t, params) -> RGBA image
for _n in EFFECTS:
    globals()[_n] = _public(_n)
