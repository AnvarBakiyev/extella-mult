"""Felt effects: small felt pieces that fall, rise or flutter. Each piece goes on its own felt layer when it is large."""
import math
import numpy as np
from .draw import Local

FX = {}


def effect(name):
    def deco(fn):
        FX[name] = fn
        return fn
    return deco


def _rng(st, k=0):
    return np.random.default_rng(int(st.params.get('seed', 5)) + k)


def _count(st, d):
    return int(st.params.get('count', d))


@effect('snow')
def snow(ctx, t, tl, st, f):
    """Felt snowflakes falling over the whole frame."""
    r = _rng(st)
    for i in range(_count(st, 60)):
        x0, sp, sz, ph = r.random(), 0.04 + 0.05 * r.random(), 0.006 + 0.01 * r.random(), r.random() * 6
        y = (r.random() + tl * sp) % 1.1 - 0.05
        ctx.circle(x0 + 0.02 * math.sin(tl * 1.5 + ph), y, sz, '#ffffff')


@effect('rain')
def rain(ctx, t, tl, st, f):
    """Felt rain drops."""
    r = _rng(st)
    for i in range(_count(st, 70)):
        x, sp = r.random(), 0.5 + 0.3 * r.random()
        y = (r.random() + tl * sp) % 1.1 - 0.05
        ctx.ellipse(x, y, 0.004, 0.012, '#7fb6e8')


@effect('hearts')
def hearts(ctx, t, tl, st, f):
    """Hearts float up from at=x,y."""
    x0, y0 = st.params.get('at', (0.5, 0.6))
    r = _rng(st)
    for i in range(_count(st, 7)):
        d = (tl * 0.6 + i / 7) % 1.0
        x, y, s = x0 + (r.random() - 0.5) * 0.25 + 0.02 * math.sin(tl * 3 + i), y0 - d * 0.45, 0.03 + 0.02 * r.random()
        L = Local(ctx.piece(), x, y, s * (1 - 0.3 * d), 1)
        L.circle(-0.25, -0.1, 0.32, '#f06a8a')
        L.circle(0.25, -0.1, 0.32, '#f06a8a')
        L.poly([(-0.55, 0.0), (0.55, 0.0), (0.0, 0.6)], '#f06a8a')


@effect('sparkles')
def sparkles(ctx, t, tl, st, f):
    """Twinkling four-point stars around at=x,y (radius r)."""
    x0, y0 = st.params.get('at', (0.5, 0.4))
    rad = st.params.get('r', 0.2)
    r = _rng(st)
    for i in range(_count(st, 10)):
        a, d, ph = r.random() * 6.28, rad * math.sqrt(r.random()), r.random() * 6
        s = 0.018 * (0.4 + 0.6 * abs(math.sin(tl * 3 + ph)))
        L = Local(ctx, x0 + d * math.cos(a) * ctx.ar, y0 + d * math.sin(a), s, 1)
        L.poly([(0, -1), (0.25, -0.25), (1, 0), (0.25, 0.25), (0, 1), (-0.25, 0.25), (-1, 0), (-0.25, -0.25)], '#fff2a8')


@effect('leaves')
def leaves(ctx, t, tl, st, f):
    """Autumn leaves drifting down."""
    r = _rng(st)
    cols = ('#e8833a', '#d9542f', '#f2b64a', '#a8c45a')
    for i in range(_count(st, 14)):
        x0, sp, ph = r.random(), 0.06 + 0.05 * r.random(), r.random() * 6
        y = (r.random() + tl * sp) % 1.1 - 0.05
        L = Local(ctx.piece(), x0 + 0.04 * math.sin(tl * 1.3 + ph), y, 0.025, 1)
        L.ellipse(0, 0, 0.6, 0.3, cols[i % 4], angle=math.sin(tl * 2 + ph))


@effect('bubbles')
def bubbles(ctx, t, tl, st, f):
    """Bubbles rise from at=x,y."""
    x0, y0 = st.params.get('at', (0.5, 0.9))
    r = _rng(st)
    for i in range(_count(st, 12)):
        d = (tl * 0.25 + r.random()) % 1.0
        s = 0.012 + 0.02 * r.random()
        c = ctx.piece()
        c.circle(x0 + (r.random() - 0.5) * 0.3 + 0.02 * math.sin(tl * 2 + i), y0 - d * 0.8, s, '#cfeaf8')


@effect('balloons')
def balloons(ctx, t, tl, st, f):
    """Balloons rise from the bottom over the effect's time."""
    r = _rng(st)
    cols = ('#f06a6a', '#f6c453', '#7fb6e8', '#9bd27a', '#c39be0')
    for i in range(_count(st, 6)):
        x = 0.1 + 0.8 * r.random()
        y = 1.15 - f * (0.9 + 0.4 * r.random()) - 0.1 * r.random()
        L = Local(ctx.piece(), x + 0.015 * math.sin(tl * 1.4 + i), y, 0.06, 1)
        L.line([(0, 0.55), (0.05, 1.3)], '#6a6a6a', 0.03)
        L.ellipse(0, 0, 0.42, 0.55, cols[i % 5])


@effect('butterflies')
def butterflies(ctx, t, tl, st, f):
    """Butterflies flutter around at=x,y."""
    x0, y0 = st.params.get('at', (0.5, 0.5))
    r = _rng(st)
    cols = ('#f2a0c8', '#f6d353', '#9fd0ee')
    for i in range(_count(st, 3)):
        ph = r.random() * 6
        x = x0 + 0.12 * math.sin(tl * 0.7 + ph) * ctx.ar * 2
        y = y0 + 0.06 * math.sin(tl * 1.1 + ph * 2)
        flap = abs(math.sin(tl * 12 + ph))
        L = Local(ctx.piece(), x, y, 0.035, 1)
        L.ellipse(-0.35 * flap, -0.2, 0.4 * flap + 0.08, 0.35, cols[i % 3])
        L.ellipse(0.35 * flap, -0.2, 0.4 * flap + 0.08, 0.35, cols[i % 3])
        L.ellipse(0, 0, 0.08, 0.35, '#5a4040')


@effect('notes')
def notes(ctx, t, tl, st, f):
    """Music notes float up from at=x,y."""
    x0, y0 = st.params.get('at', (0.5, 0.5))
    for i in range(_count(st, 4)):
        d = (tl * 0.5 + i / 4) % 1.0
        L = Local(ctx.piece(), x0 + 0.08 * math.sin(i * 2 + tl), y0 - d * 0.35, 0.04, 1)
        L.ellipse(0, 0, 0.32, 0.24, '#5a4a8a', angle=-0.4)
        L.line([(0.27, -0.05), (0.27, -1.0)], '#5a4a8a', 0.1)
        L.line([(0.27, -1.0), (0.6, -0.8)], '#5a4a8a', 0.1)


@effect('smoke')
def smoke(ctx, t, tl, st, f):
    """Puffy felt smoke clouds that billow out sideways and up from at=x,y (a rocket launch, a crash, a cough);
    r = how far they spread; color=#efebe4."""
    x0, y0 = st.params.get('at', (0.5, 0.85))
    R = st.params.get('r', 0.25)
    col = st.params.get('color', '#efebe4')
    r = _rng(st, 3)
    g = min(1.0, tl / 1.2)  # grows for the first second
    for i in range(_count(st, 12)):
        side = -1 if i % 2 else 1
        d = r.random()
        x = x0 + side * d * R * g * ctx.H / ctx.W * 1.6
        y = y0 - (0.05 + 0.25 * r.random()) * R * g - 0.01 * tl
        sz = (0.03 + 0.05 * r.random()) * (0.5 + g) * (1 + 0.05 * math.sin(tl * 2 + i))
        pc = ctx.piece()
        pc.circle(x, y, sz, col)
        pc.circle(x + 0.4 * sz * ctx.H / ctx.W, y - 0.3 * sz, sz * 0.7, col)
