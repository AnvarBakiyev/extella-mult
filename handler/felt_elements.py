"""Felt-style 2d elements: big, simple, rounded shapes in a pastel palette, made to be drawn with look=felt.
Each element is a separate layer, so the felt pass gives every piece its own rounded edge and shadow."""
import math
import numpy as np
from PIL import Image, ImageDraw
FE = {}


def element(name):
    def deco(fn):
        FE[name] = fn
        return fn
    return deco

P = dict(sky='#9fd0ee', sky2='#d8eef8', night='#1d2a5c', night2='#3b4a86', hill='#8fcf6a', hill2='#6fb850', hill3='#b9e28c',
         cloud='#fbfbf6', trunk='#8a5a3a', leaf='#5fae4e', leaf2='#79c45e', sun='#ffe16a', moon='#f6f0d4', sea='#3f7fbf', sea2='#5c9bd6',
         sand='#f1dfae', street='#efe3c4')
HOUSE = ['#f28b6b', '#f6c453', '#8fd3c8', '#b99be0', '#f2a0b8', '#9ccf7a', '#f4b07a', '#7fb6e8']


def _poly(ctx, pts, col):
    ctx.d.polygon([(x * ctx.W, y * ctx.H) for x, y in pts], fill=col)


def _ell(ctx, cx, cy, rx, ry, col):
    """Ellipse with radii as fractions of the frame height (round on screen)."""
    W, H = ctx.W, ctx.H
    ctx.d.ellipse([cx * W - rx * H, cy * H - ry * H, cx * W + rx * H, cy * H + ry * H], fill=col)


def _pc(ctx):
    """A separate felt piece (its own rounded edge and shadow) when the felt pass offers one; else the same canvas."""
    return ctx.piece() if hasattr(ctx, 'piece') else ctx


def _shade_hex(c, k):
    return '#%02x%02x%02x' % tuple(min(255, int(int(c[i:i + 2], 16) * k)) for i in (1, 3, 5))


def _heart(ctx, cx, cy, r, col):
    _ell(ctx, cx - r * 0.5 * ctx.ar, cy - r * 0.2, r * 0.55, r * 0.55, col)
    _ell(ctx, cx + r * 0.5 * ctx.ar, cy - r * 0.2, r * 0.55, r * 0.55, col)
    _poly(ctx, [(cx - r * 1.02 * ctx.ar, cy - r * 0.05), (cx + r * 1.02 * ctx.ar, cy - r * 0.05), (cx, cy + r * 0.95)], col)


@element('felt_sky')
def felt_sky(ctx, t, tl, p):
    """Vertical gradient sky: time=day|night."""
    night = p.get('time', 'day') == 'night'
    a, b = (P['night'], P['night2']) if night else (P['sky'], P['sky2'])
    ca = np.array([int(a[i:i + 2], 16) for i in (1, 3, 5)], np.float32)
    cb = np.array([int(b[i:i + 2], 16) for i in (1, 3, 5)], np.float32)
    g = np.linspace(0, 1, ctx.H, dtype=np.float32)[:, None]
    col = ca[None, :] * (1 - g) + cb[None, :] * g
    arr = np.broadcast_to(col[:, None, :], (ctx.H, ctx.W, 3)).astype(np.uint8)
    ctx.img.paste(Image.fromarray(np.ascontiguousarray(arr), 'RGB'), (0, 0))
    if night:
        r = np.random.default_rng(3)
        for _ in range(140):
            x, y, s = r.random(), r.random() * 0.6, 0.002 + r.random() * 0.003
            _ell(ctx, x, y, s, s, '#fff8e0')


@element('hills')
def hills(ctx, t, tl, p):
    """Two rolling hills; top = horizon height."""
    top = p.get('top', 0.62)
    for k, (col, amp, ph, dy) in enumerate(((P['hill3'], 0.05, 0.3, 0.0), (P['hill'], 0.04, 1.7, 0.06))):
        pts = [(x / 60, top + dy - amp * math.sin(x / 60 * 5.5 + ph) - 0.02 * math.sin(x / 60 * 13 + ph)) for x in range(61)]
        _poly(ctx, pts + [(1, 1), (0, 1)], col)


@element('puff_cloud')
def puff_cloud(ctx, t, tl, p):
    """A puffy cloud: x, y, s; drifts slowly with speed."""
    x = (p.get('x', 0.3) + p.get('speed', 0.004) * t) % 1.3 - 0.15
    y, s = p.get('y', 0.18), p.get('s', 1.0)
    for dx, dy, r in ((-0.1, 0.035, 0.06), (-0.04, -0.015, 0.085), (0.04, -0.03, 0.095), (0.11, 0.02, 0.07), (0.0, 0.045, 0.06)):
        _ell(ctx, x + dx * s * 0.42 * 1.4, y + dy * s, r * s, r * s * 0.9, P['cloud'])


@element('round_tree')
def round_tree(ctx, t, tl, p):
    """A lollipop tree that sways a little: x, y (base), s."""
    x, y, s = p.get('x', 0.75), p.get('y', 0.62), p.get('s', 1.0)
    sway = 0.004 * math.sin(t * 1.3 + x * 9)
    _poly(ctx, [(x - 0.008 * s, y), (x + 0.008 * s, y), (x + 0.006 * s + sway, y - 0.2 * s), (x - 0.006 * s + sway, y - 0.2 * s)], P['trunk'])
    for dx, dy, r, c in ((-0.035, -0.22, 0.08, P['leaf']), (0.035, -0.23, 0.08, P['leaf']), (0, -0.29, 0.09, P['leaf2']), (0, -0.2, 0.07, P['leaf2'])):
        _ell(ctx, x + dx * s * 0.42 + sway, y + dy * s, r * s, r * s, c)


@element('house_row')
def house_row(ctx, t, tl, p):
    """A street of tall colourful houses with windows: base = street line, grey=1 drains the colour."""
    base, grey = p.get('base', 0.78), p.get('grey', 0)
    r = np.random.default_rng(int(p.get('seed', 4)))
    x = -0.02
    k = 0
    while x < 1.02:
        w, h = 0.07 + r.random() * 0.03, 0.32 + r.random() * 0.2
        col = HOUSE[k % len(HOUSE)]
        if grey:
            v = int(sum(int(col[i:i + 2], 16) for i in (1, 3, 5)) / 3 * 0.85)
            col = '#%02x%02x%02x' % (v, v, v + 6)
        _poly(ctx, [(x, base), (x + w, base), (x + w, base - h), (x, base - h)], col)
        roof = '#%02x%02x%02x' % tuple(max(0, int(col[i:i + 2], 16) - 50) for i in (1, 3, 5))
        _poly(ctx, [(x - 0.004, base - h), (x + w + 0.004, base - h), (x + w / 2, base - h - 0.07)], roof)
        for wy in np.arange(base - h + 0.04, base - 0.05, 0.055):
            for wx in (x + w * 0.22, x + w * 0.58):
                _poly(ctx, [(wx, wy), (wx + w * 0.2, wy), (wx + w * 0.2, wy + 0.03), (wx, wy + 0.03)], '#fff7e6' if not grey else '#d9d9de')
        x += w + 0.004
        k += 1
    _poly(ctx, [(0, base), (1, base), (1, 1), (0, 1)], P['street'])


@element('felt_sun')
def felt_sun(ctx, t, tl, p):
    """Sun or moon: x, y, r, kind=sun|moon."""
    col = P['moon'] if p.get('kind', 'sun') == 'moon' else P['sun']
    _ell(ctx, p.get('x', 0.85), p.get('y', 0.18), p.get('r', 0.09), p.get('r', 0.09), col)


@element('felt_sea')
def felt_sea(ctx, t, tl, p):
    """Sea with gentle waves from top down; a sandy shore if shore=1."""
    top = p.get('top', 0.6)
    for k, col in enumerate((P['sea2'], P['sea'])):
        pts = [(x / 80, top + k * 0.05 + 0.012 * math.sin(x / 80 * 30 + t * (1.2 + k) + k)) for x in range(81)]
        _poly(ctx, pts + [(1, 1), (0, 1)], col)
    if p.get('shore', 0):
        _poly(ctx, [(0, 0.86), (0.3, 0.82), (0.55, 0.88), (0.55, 1), (0, 1)], P['sand'])


SKIES = {'day': ('#9fd0ee', '#d8eef8'), 'dawn': ('#f6b48f', '#fde7c8'), 'sunset': ('#e9876f', '#f9d39a'), 'night': ('#1d2a5c', '#3b4a86'),
         'space': ('#120f2e', '#2a1f5a')}


@element('sky')
def sky(ctx, t, tl, p):
    """Gradient sky: time=day|dawn|sunset|night|space; night and space get stars."""
    k = p.get('time', 'day')
    a, b = SKIES.get(k, SKIES['day'])
    felt_sky(ctx, t, tl, {'time': 'day'})
    ca = np.array([int(a[i:i + 2], 16) for i in (1, 3, 5)], np.float32)
    cb = np.array([int(b[i:i + 2], 16) for i in (1, 3, 5)], np.float32)
    g = np.linspace(0, 1, ctx.H, dtype=np.float32)[:, None]
    col = ca[None, :] * (1 - g) + cb[None, :] * g
    arr = np.broadcast_to(col[:, None, :], (ctx.H, ctx.W, 3)).astype(np.uint8)
    ctx.img.paste(Image.fromarray(np.ascontiguousarray(arr), 'RGB'), (0, 0))
    if k in ('night', 'space'):
        r = np.random.default_rng(3)
        for _ in range(220 if k == 'space' else 140):
            x, y, s = r.random(), r.random() * (1.0 if k == 'space' else 0.6), 0.002 + r.random() * 0.003
            tw = 0.6 + 0.4 * math.sin(t * 2 + x * 40)
            _ell(ctx, x, y, s * tw, s * tw, '#fff8e0')


def _col(name, p, default):
    return p.get('color', default)


@element('mountains')
def mountains(ctx, t, tl, p):
    """Soft rounded mountains with snowy tops along the horizon: top = highest peak."""
    top, base = p.get('top', 0.3), p.get('base', 0.65)
    r = np.random.default_rng(int(p.get('seed', 2)))
    x = -0.1
    while x < 1.1:
        w, h = 0.22 + 0.12 * r.random(), (base - top) * (0.6 + 0.4 * r.random())
        _poly(ctx, [(x, base), (x + w * 0.45, base - h), (x + w * 0.55, base - h), (x + w, base)], '#8b97c7')
        _poly(ctx, [(x + w * 0.33, base - h * 0.74), (x + w * 0.45, base - h), (x + w * 0.55, base - h), (x + w * 0.67, base - h * 0.74)], '#f4f4fa')
        x += w * 0.7


@element('pine_tree')
def pine_tree(ctx, t, tl, p):
    """A felt fir tree: x, y (base), s; snow=1 adds white tips."""
    x, y, s = p.get('x', 0.5), p.get('y', 0.7), p.get('s', 1.0)
    _poly(ctx, [(x - 0.008 * s, y), (x + 0.008 * s, y), (x + 0.008 * s, y - 0.06 * s), (x - 0.008 * s, y - 0.06 * s)], P['trunk'])
    for k, (w, y0, h) in enumerate(((0.11, 0.05, 0.16), (0.085, 0.13, 0.15), (0.06, 0.21, 0.13))):
        col = '#3f8f5a' if k % 2 == 0 else '#4ea068'
        _poly(ctx, [(x - w * s * 0.5, y - y0 * s), (x + w * s * 0.5, y - y0 * s), (x, y - (y0 + h) * s)], col)
        if p.get('snow', 0):
            _poly(ctx, [(x - w * s * 0.18, y - (y0 + h * 0.62) * s), (x + w * s * 0.18, y - (y0 + h * 0.62) * s), (x, y - (y0 + h) * s)], '#ffffff')


@element('forest')
def forest(ctx, t, tl, p):
    """A row of round and pine trees along base."""
    base = p.get('base', 0.66)
    r = np.random.default_rng(int(p.get('seed', 6)))
    x = 0.02
    while x < 1.0:
        if r.random() < 0.5:
            pine_tree(ctx, t, tl, {'x': x, 'y': base, 's': 0.8 + 0.4 * r.random(), 'snow': p.get('snow', 0)})
        else:
            round_tree(ctx, t, tl, {'x': x, 'y': base, 's': 0.7 + 0.35 * r.random()})
        x += 0.06 + 0.05 * r.random()


@element('bush')
def bush(ctx, t, tl, p):
    """A round bush, flowers=1 adds blossoms."""
    x, y, s = p.get('x', 0.5), p.get('y', 0.8), p.get('s', 1.0)
    for dx, dy, r in ((-0.04, -0.03, 0.045), (0.0, -0.05, 0.055), (0.045, -0.03, 0.045)):
        _ell(ctx, x + dx * s * 0.6, y + dy * s, r * s, r * s * 0.9, P['leaf'])
    if p.get('flowers', 0):
        for dx, dy in ((-0.03, -0.06), (0.01, -0.09), (0.035, -0.05), (-0.005, -0.04)):
            _ell(ctx, x + dx * s * 0.6, y + dy * s, 0.011 * s, 0.011 * s, '#f28bb0')


@element('flowers')
def flowers(ctx, t, tl, p):
    """A strip of small flowers along y between x0 and x1."""
    y, x0, x1 = p.get('y', 0.85), p.get('x0', 0.0), p.get('x1', 1.0)
    r = np.random.default_rng(int(p.get('seed', 9)))
    cols = ('#f28bb0', '#f6d353', '#ffffff', '#b99be0', '#f28b6b')
    for i in range(int(p.get('count', 26))):
        x = x0 + (x1 - x0) * r.random()
        yy = y + 0.06 * r.random()
        ctx.line([(x, yy + 0.04), (x, yy)], '#4f9a45', 0.004)
        for k in range(5):
            a = k * 1.2566 + t * 0.2
            _ell(ctx, x + 0.006 * math.cos(a) * ctx.ar, yy + 0.006 * math.sin(a), 0.006, 0.006, cols[i % 5])
        _ell(ctx, x, yy, 0.004, 0.004, '#f6c453')


@element('river')
def river(ctx, t, tl, p):
    """A winding river from the horizon to the bottom of the frame."""
    top = p.get('top', 0.62)
    pts_l, pts_r = [], []
    for k in range(21):
        v = k / 20
        y = top + (1 - top) * v
        cx = 0.55 + 0.12 * math.sin(v * 3.5) * (1 - v * 0.3)
        w = 0.02 + 0.18 * v
        pts_l.append((cx - w, y))
        pts_r.append((cx + w, y))
    _poly(ctx, pts_l + pts_r[::-1], '#5c9bd6')
    for k in range(6):
        v = ((t * 0.12 + k / 6) % 1.0)
        y = top + (1 - top) * v
        cx = 0.55 + 0.12 * math.sin(v * 3.5) * (1 - v * 0.3)
        ctx.line([(cx - 0.03 * v, y), (cx + 0.03 * v, y)], '#a9d2f2', 0.004)


@element('bridge')
def bridge(ctx, t, tl, p):
    """A little arched wooden bridge: x, y (deck), s."""
    x, y, s = p.get('x', 0.55), p.get('y', 0.8), p.get('s', 1.0)
    pts = [(x - 0.16 * s + 0.32 * s * k / 20, y - 0.05 * s * math.sin(math.pi * k / 20)) for k in range(21)]
    _poly(ctx, pts + [(x + 0.16 * s, y + 0.025 * s)] + [(px, py + 0.025 * s) for px, py in pts[::-1]][1:-1] + [(x - 0.16 * s, y + 0.025 * s)], '#b07a4a')
    for k in range(0, 21, 4):
        px, py = pts[k]
        ctx.line([(px, py), (px, py - 0.05 * s)], '#8a5a3a', 0.006 * s)
    ctx.line([(px0, py0 - 0.05 * s) for px0, py0 in pts], '#8a5a3a', 0.006 * s)


@element('house')
def house(ctx, t, tl, p):
    """One house with a door and windows: x (centre), y (ground), s, color, lit=1 for warm night windows."""
    x, y, s = p.get('x', 0.5), p.get('y', 0.8), p.get('s', 1.0)
    col = p.get('color', '#f28b6b')
    w, h = 0.11 * s, 0.17 * s
    _poly(ctx, [(x - w, y), (x + w, y), (x + w, y - h), (x - w, y - h)], col)
    _poly(ctx, [(x - w - 0.01 * s, y - h), (x + w + 0.01 * s, y - h), (x, y - h - 0.1 * s)], '#a34a3a')
    win = '#ffe39a' if p.get('lit', 0) else '#fff7e6'
    for dx in (-0.06, 0.06):
        _poly(ctx, [(x + dx * s - 0.025 * s, y - h * 0.75), (x + dx * s + 0.025 * s, y - h * 0.75), (x + dx * s + 0.025 * s, y - h * 0.5), (x + dx * s - 0.025 * s, y - h * 0.5)], win)
    _poly(ctx, [(x - 0.022 * s, y), (x + 0.022 * s, y), (x + 0.022 * s, y - 0.08 * s), (x - 0.022 * s, y - 0.08 * s)], '#7a4a2a')


@element('school')
def school(ctx, t, tl, p):
    """A school with a clock and a flag: x, y (ground), s."""
    x, y, s = p.get('x', 0.5), p.get('y', 0.8), p.get('s', 1.0)
    w, h = 0.22 * s, 0.2 * s
    _poly(ctx, [(x - w, y), (x + w, y), (x + w, y - h), (x - w, y - h)], '#e9b86a')
    _poly(ctx, [(x - 0.06 * s, y - h), (x + 0.06 * s, y - h), (x + 0.06 * s, y - h - 0.08 * s), (x - 0.06 * s, y - h - 0.08 * s)], '#e9b86a')
    _poly(ctx, [(x - 0.075 * s, y - h - 0.08 * s), (x + 0.075 * s, y - h - 0.08 * s), (x, y - h - 0.15 * s)], '#c5583e')
    _ell(ctx, x, y - h - 0.035 * s, 0.025 * s, 0.025 * s, '#ffffff')
    ang = t * 0.5
    ctx.line([(x, y - h - 0.035 * s), (x + 0.015 * s * math.sin(ang) * ctx.ar, y - h - 0.035 * s - 0.015 * s * math.cos(ang))], '#3a2a2a', 0.003 * s)
    for row in (0.35, 0.65):
        for k in range(-3, 4):
            if k == 0 and row == 0.65:
                continue
            cx = x + k * 0.06 * s
            _poly(ctx, [(cx - 0.018 * s, y - h * row - 0.03 * s), (cx + 0.018 * s, y - h * row - 0.03 * s), (cx + 0.018 * s, y - h * row + 0.02 * s), (cx - 0.018 * s, y - h * row + 0.02 * s)], '#cfe8f4')
    _poly(ctx, [(x - 0.03 * s, y), (x + 0.03 * s, y), (x + 0.03 * s, y - 0.07 * s), (x - 0.03 * s, y - 0.07 * s)], '#7a4a2a')
    ctx.line([(x + w * 0.85, y - h), (x + w * 0.85, y - h - 0.13 * s)], '#6a6a6a', 0.003 * s)
    wav = 0.006 * math.sin(t * 4)
    _poly(ctx, [(x + w * 0.85, y - h - 0.13 * s), (x + w * 0.85 + 0.05 * s, y - h - 0.115 * s + wav), (x + w * 0.85, y - h - 0.095 * s)], '#e05a5a')


@element('rainbow')
def rainbow(ctx, t, tl, p):
    """A felt rainbow arc: x, y (centre of the arc's foot), r."""
    x, y, r = p.get('x', 0.5), p.get('y', 0.7), p.get('r', 0.45)
    for k, col in enumerate(('#ef6b6b', '#f4a34e', '#f6d353', '#8fcf6a', '#6aaee8', '#a58be0')):
        rr = r - k * 0.025
        pts = [(x + rr * math.cos(math.pi * (1 - i / 40)) * ctx.ar, y - rr * math.sin(math.pi * (1 - i / 40))) for i in range(41)]
        inner = [(x + (rr - 0.024) * math.cos(math.pi * (1 - i / 40)) * ctx.ar, y - (rr - 0.024) * math.sin(math.pi * (1 - i / 40))) for i in range(41)]
        _poly(ctx, pts + inner[::-1], col)


@element('planet')
def planet(ctx, t, tl, p):
    """A planet with continents and an optional ring: x, y, r, ring=1, color. The ring passes behind and in front of the ball."""
    x, y, r = p.get('x', 0.5), p.get('y', 0.5), p.get('r', 0.2)
    ring = p.get('ring', 0)
    ang = -0.25

    def band(lo, hi, rx, ry, w):  # part of the ring between angles lo..hi, as a closed strip
        pts, inn = [], []
        for i in range(41):
            a = lo + (hi - lo) * i / 40
            for R, out in ((1.0, pts), (1 - w, inn)):
                u, v = rx * R * math.cos(a), ry * R * math.sin(a)
                out.append((x + (u * math.cos(ang) - v * math.sin(ang)) * ctx.H / ctx.W, y + u * math.sin(ang) + v * math.cos(ang)))
        return pts + inn[::-1]

    if ring:
        _poly(ctx, band(math.pi, 2 * math.pi, r * 1.7, r * 0.32, 0.28), '#c9a868')
    _ell(ctx, x, y, r, r, p.get('color', '#4a86c8'))
    rot = t * 0.02
    for dx, dy, rr in ((-0.35, -0.2, 0.3), (0.3, 0.1, 0.35), (-0.1, 0.45, 0.22)):
        cx = x + ((dx + rot) % 1.4 - 0.7) * r * ctx.ar * 1.2
        if abs(cx - x) < r * ctx.ar * 0.75:
            _ell(ctx, cx, y + dy * r, rr * r, rr * r * 0.8, '#6fbf6a')
    if ring:
        pc = ctx.piece()
        _poly(pc, band(0, math.pi, r * 1.7, r * 0.32, 0.28), '#e8c98a')


def _face(c, P, k, who):
    """A small face for a rocket window: cat, boy, girl, dog, bunny."""
    if who in ('cat', 'fox', 'dog', 'bunny', 'bear'):
        fur = {'cat': '#f0a04b', 'fox': '#e8743b', 'dog': '#c9955c', 'bunny': '#f2ecea', 'bear': '#9a6a45'}[who]
        if who == 'bunny':
            for sx in (-1, 1):
                c.ellipse(*P(0.06 * sx, -0.86), 0.022 * k, 0.06 * k, fur)
        elif who in ('cat', 'fox'):
            for sx in (-1, 1):
                c.d.polygon([P(0.03 * sx, -0.77), P(0.085 * sx, -0.84), P(0.075 * sx, -0.74)], fill=fur)
        else:
            for sx in (-1, 1):
                c.ellipse(*P(0.07 * sx, -0.79), 0.02 * k, 0.025 * k, fur)
        c.ellipse(*P(0, -0.72), 0.075 * k, 0.065 * k, fur)
    else:
        c.ellipse(*P(0, -0.72), 0.068 * k, 0.07 * k, '#f3c9a0')
        hair = '#3b2a20' if who == 'boy' else '#7a3e1e'
        c.ellipse(*P(0, -0.77), 0.07 * k, 0.035 * k, hair)
    for sx in (-1, 1):
        c.ellipse(*P(0.028 * sx, -0.725), 0.012 * k, 0.016 * k, '#1d1a18')
        c.ellipse(*P(0.024 * sx, -0.732), 0.004 * k, 0.005 * k, '#ffffff')
    c.ellipse(*P(0, -0.695), 0.012 * k, 0.008 * k, '#e0607a')


@element('rocket')
def rocket(ctx, t, tl, p):
    """A felt rocket: x, y (base), s (size); flying=1 adds a flickering flame and a shake; rise=0.2 lifts it 0.2 of the
    frame per second; drift=0.1 moves it right per second; tilt=15 leans it (degrees, + to the right), spin=90 turns it
    (degrees per second); pilot=cat|boy|girl|dog|bunny|fox|bear shows who looks out of the window; color=#e05a5a for
    stripes and fins; pad=1 adds a launch tower; sputter=1 makes the flame cough."""
    x, y, s = p.get('x', 0.5), p.get('y', 0.8), p.get('s', 1.0)
    fly = p.get('flying', 0)
    y -= p.get('rise', 0) * tl
    x += p.get('drift', 0) * tl
    a = math.radians(p.get('tilt', 0) + p.get('spin', 0) * tl)
    if fly:
        x += 0.0025 * s * math.sin(t * 47)
        a += 0.02 * math.sin(t * 31)
    h = 0.25 * s
    ca, sa = math.cos(a), math.sin(a)

    def P(u, v):  # u across, v along the rocket (0 at the base, -1 at the nose), in units of the rocket height
        X, Y = u * h, v * h
        return ((x + (X * ca - Y * sa) * ctx.H / ctx.W) * ctx.W, (y + X * sa + Y * ca) * ctx.H)

    col = p.get('color', '#e05a5a')
    k = h * ctx.H  # px per unit, for round parts

    class C:  # a ctx wrapper that draws in pixels
        def __init__(self, c):
            self.d = c.d
        def ellipse(self, cx, cy, rx, ry, colr):
            self.d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=colr)

    if p.get('pad', 0):
        tw = ctx.d
        bx = x + 0.12 * s * ctx.H / ctx.W * 1.0
        tw.rectangle([bx * ctx.W - 0.012 * k * 4, (y - h * 1.05) * ctx.H, bx * ctx.W + 0.012 * k * 4, y * ctx.H], fill='#8d8f99')
        for i in range(7):
            yy = (y - h * (0.1 + i * 0.14)) * ctx.H
            tw.rectangle([bx * ctx.W - 0.15 * k, yy, bx * ctx.W + 0.05 * k, yy + 0.02 * k], fill='#6d6f79')
        tw.rectangle([(x - 0.3 * s * ctx.H / ctx.W) * ctx.W, y * ctx.H - 0.02 * k, (x + 0.3 * s * ctx.H / ctx.W) * ctx.W, y * ctx.H + 0.06 * k], fill='#7d7f88')
    base = C(ctx)
    if fly:
        cough = p.get('sputter', 0) and (math.sin(t * 7) + math.sin(t * 13)) > 0.6
        fl = 0 if cough else (0.55 + 0.12 * math.sin(t * 37) + 0.08 * math.sin(t * 23))
        if fl:
            for w, L, colr in ((0.17, fl, '#f08a2e'), (0.12, fl * 0.75, '#f6c544'), (0.06, fl * 0.45, '#fff6d0')):
                base.d.polygon([P(-w, 0.02), P(-w * 0.6, L * 0.4), P(0, L), P(w * 0.6, L * 0.4), P(w, 0.02)], fill=colr)
        else:
            for i in range(3):
                base.ellipse(*P(0.05 * (i - 1), 0.12 + 0.05 * i), 0.05 * k, 0.05 * k, '#8a8a8a')
    fins = C(ctx.piece())
    for sx in (-1, 1):
        fins.d.polygon([P(0.13 * sx, -0.12), P(0.3 * sx, 0.04), P(0.3 * sx, 0.1), P(0.13 * sx, 0.02)], fill=col)
    body = C(ctx.piece())
    body.d.polygon([P(-0.14, 0.04), P(0.14, 0.04)] + [P(0.14 * math.cos(q * math.pi / 2 / 12), -0.62 - 0.38 * math.sin(q * math.pi / 2 / 12)) for q in range(13)]
                   + [P(-0.14 * math.cos(q * math.pi / 2 / 12), -0.62 - 0.38 * math.sin(q * math.pi / 2 / 12)) for q in range(12, -1, -1)], fill='#f3efe6')
    body.d.polygon([P(-0.14, -0.2), P(0.14, -0.2), P(0.14, -0.28), P(-0.14, -0.28)], fill=col)
    nose = C(ctx.piece())
    nose.d.polygon([P(0.115 * math.cos(q * math.pi / 2 / 10), -0.8 - 0.2 * math.sin(q * math.pi / 2 / 10)) for q in range(11)]
                   + [P(-0.115 * math.cos(q * math.pi / 2 / 10), -0.8 - 0.2 * math.sin(q * math.pi / 2 / 10)) for q in range(10, -1, -1)], fill=col)
    win = C(ctx.piece())
    win.ellipse(*P(0, -0.52), 0.095 * k, 0.095 * k, '#9aa0ad')
    win.ellipse(*P(0, -0.52), 0.075 * k, 0.075 * k, '#7fc2ee')
    who = p.get('pilot')
    if who:
        def Q(u, v):
            return P(u, v + 0.2)
        _face(win, Q, k, who)
    win.ellipse(*P(-0.03, -0.555), 0.018 * k, 0.012 * k, '#e9f6ff')


@element('moon_ground')
def moon_ground(ctx, t, tl, p):
    """Grey cratered ground of the moon from top down."""
    top = p.get('top', 0.72)
    pts = [(k / 30, top - 0.015 * math.sin(k / 30 * 9)) for k in range(31)]
    _poly(ctx, pts + [(1, 1), (0, 1)], '#b9b9c6')
    for cx, cy, r in ((0.2, 0.85, 0.04), (0.55, 0.8, 0.03), (0.8, 0.9, 0.05), (0.38, 0.93, 0.02)):
        ctx.ellipse(cx, cy, r, r * 0.4, '#9a9aaa')


@element('snow_ground')
def snow_ground(ctx, t, tl, p):
    """Snowy rolling ground."""
    top = p.get('top', 0.66)
    pts = [(k / 30, top - 0.02 * math.sin(k / 30 * 6 + 1)) for k in range(31)]
    _poly(ctx, pts + [(1, 1), (0, 1)], '#f2f6fb')


@element('snowman')
def snowman(ctx, t, tl, p):
    """A snowman: x, y (ground), s."""
    x, y, s = p.get('x', 0.5), p.get('y', 0.85), p.get('s', 1.0)
    for dy, r in ((-0.06, 0.065), (-0.16, 0.05), (-0.24, 0.037)):
        _ell(ctx, x, y + dy * s, r * s, r * s, '#ffffff')
    _poly(ctx, [(x, y - 0.245 * s), (x + 0.05 * s, y - 0.235 * s), (x, y - 0.228 * s)], '#f08a3a')
    for ex in (-0.012, 0.012):
        _ell(ctx, x + ex * s, y - 0.255 * s, 0.005 * s, 0.005 * s, '#2a2020')
    _poly(ctx, [(x - 0.04 * s, y - 0.27 * s), (x + 0.04 * s, y - 0.27 * s), (x + 0.03 * s, y - 0.33 * s), (x - 0.03 * s, y - 0.33 * s)], '#3a3a4a')


@element('fence')
def fence(ctx, t, tl, p):
    """A wooden fence along y from x0 to x1."""
    y, x0, x1 = p.get('y', 0.8), p.get('x0', 0.0), p.get('x1', 1.0)
    ctx.line([(x0, y - 0.06), (x1, y - 0.06)], '#d9b48a', 0.008)
    ctx.line([(x0, y - 0.03), (x1, y - 0.03)], '#d9b48a', 0.008)
    x = x0
    while x <= x1:
        _poly(ctx, [(x - 0.007, y), (x + 0.007, y), (x + 0.007, y - 0.09), (x, y - 0.1), (x - 0.007, y - 0.09)], '#e6c79c')
        x += 0.035


@element('boat')
def boat(ctx, t, tl, p):
    """A sailing boat rocking on the water: x, y (waterline), s."""
    x, y, s = p.get('x', 0.5), p.get('y', 0.66), p.get('s', 1.0)
    x += p.get('speed', 0) * tl  # speed=0.03 sails right
    rock = 0.006 * math.sin(t * 1.6)
    _poly(ctx, [(x - 0.09 * s, y - 0.02 * s + rock), (x + 0.09 * s, y - 0.02 * s - rock), (x + 0.06 * s, y + 0.02 * s), (x - 0.06 * s, y + 0.02 * s)], '#c5583e')
    ctx.line([(x, y - 0.02 * s), (x, y - 0.18 * s)], '#7a4a2a', 0.004 * s)
    _poly(ctx, [(x + 0.004, y - 0.17 * s), (x + 0.004, y - 0.04 * s), (x + 0.075 * s, y - 0.04 * s)], '#fbfbf6')


@element('lighthouse')
def lighthouse(ctx, t, tl, p):
    """A striped lighthouse with a turning beam at night: x, y (base), s."""
    x, y, s = p.get('x', 0.8), p.get('y', 0.7), p.get('s', 1.0)
    for k in range(4):
        y0, y1 = y - k * 0.06 * s, y - (k + 1) * 0.06 * s
        w0, w1 = 0.035 - k * 0.004, 0.035 - (k + 1) * 0.004
        _poly(ctx, [(x - w0 * s, y0), (x + w0 * s, y0), (x + w1 * s, y1), (x - w1 * s, y1)], '#e05a5a' if k % 2 == 0 else '#ffffff')
    _poly(ctx, [(x - 0.022 * s, y - 0.24 * s), (x + 0.022 * s, y - 0.24 * s), (x + 0.022 * s, y - 0.28 * s), (x - 0.022 * s, y - 0.28 * s)], '#ffe39a')
    _poly(ctx, [(x - 0.03 * s, y - 0.28 * s), (x + 0.03 * s, y - 0.28 * s), (x, y - 0.32 * s)], '#3a3a4a')


def _door(ctx, t, p, fl):
    """A door in the wall of a room; it swings open over half a second from door_open on."""
    x, w, top, bottom = p['door'], 0.075, fl - 0.46, fl + 0.03
    F = _pc(ctx)
    _poly(F, [(x - w - 0.012, bottom), (x - w - 0.012, top - 0.025), (x + w + 0.012, top - 0.025), (x + w + 0.012, bottom)], '#a8743f')
    _poly(_pc(ctx), [(x - w, bottom), (x - w, top), (x + w, top), (x + w, bottom)], '#ffe2a8')
    k = min(1.0, max(0.0, (t - p.get('door_open', 1e9)) / 0.5))
    D = _pc(ctx)
    left = x - w + 2 * w * k * 0.82
    col = p.get('door_color', '#c98a5a')
    _poly(D, [(left, bottom), (left, top), (x + w, top), (x + w, bottom)], col)
    if k < 0.5:
        _ell(_pc(ctx), left + 0.016, (top + bottom) / 2 + 0.03, 0.016, 0.016, '#f6c453')
        for y0, y1 in ((top + 0.04, top + 0.22), (top + 0.27, bottom - 0.05)):
            _poly(_pc(ctx), [(left + 0.03, y0), (x + w - 0.018, y0), (x + w - 0.018, y1), (left + 0.03, y1)], _shade_hex(col, 0.88))


def _armchair(ctx, p):
    """A soft armchair seen from the front, wide enough for someone to sit in."""
    x, y, s = p['armchair'], p.get('armchair_y', 0.9), p.get('armchair_s', 1.0)
    col = p.get('armchair_color', '#d9a679')
    w = 0.095 * s
    for u in (-0.75, 0.75):
        _poly(_pc(ctx), [(x + u * w - 0.006 * s, y), (x + u * w + 0.006 * s, y), (x + u * w + 0.006 * s, y - 0.05 * s), (x + u * w - 0.006 * s, y - 0.05 * s)], '#7a5a3a')
    _ell(_pc(ctx), x, y - 0.29 * s, 0.13 * s, 0.17 * s, _shade_hex(col, 0.9))
    _poly(_pc(ctx), [(x - w, y - 0.04 * s), (x + w, y - 0.04 * s), (x + w, y - 0.17 * s), (x - w, y - 0.17 * s)], col)
    for u in (-1, 1):
        _ell(_pc(ctx), x + u * w, y - 0.13 * s, 0.05 * s, 0.1 * s, _shade_hex(col, 1.08))


@element('room')
def room(ctx, t, tl, p):
    """Inside a home: a wall (color), a wooden floor from floor= down, a window with the sky (time). snow=1 shows snow falling behind
    the window. door=0.1 adds a door at that x; door_open=9.5 opens it at that second of the film. armchair=0.45 adds an armchair
    at that x, armchair_y (floor line), armchair_s (size): a person who sits there has y about armchair_y - 0.13 * armchair_s."""
    wall, fl = p.get('color', '#f4e3c3'), p.get('floor', 0.78)
    _poly(ctx, [(0, 0), (1, 0), (1, fl), (0, fl)], wall)
    _poly(ctx, [(0, fl), (1, fl), (1, 1), (0, 1)], '#c99a6a')
    for k in range(1, 6):
        ctx.line([(0, fl + k * (1 - fl) / 6), (1, fl + k * (1 - fl) / 6)], '#b5875a', 0.002)
    wx, wy = p.get('window', 0.7), 0.18
    sky_c = {'night': '#2a3a78', 'sunset': '#f2a07a'}.get(p.get('time', 'day'), '#a9d8f2')
    if p.get('cozy', 0):
        # warm wallpaper stripes, a panelled lower wall, a rug: several layers of background, like a felt dollhouse
        for k in range(0, 34, 2):
            _poly(ctx, [(k / 34, 0), ((k + 1) / 34, 0), ((k + 1) / 34, fl), (k / 34, fl)], _shade_hex(wall, 1.035))
        pn = _pc(ctx)
        _poly(pn, [(0, fl - 0.15), (1, fl - 0.15), (1, fl), (0, fl)], p.get('panel', '#f2c4b6'))
        _poly(pn, [(0, fl - 0.165), (1, fl - 0.165), (1, fl - 0.145), (0, fl - 0.145)], '#e3a48f')
        rg = _pc(ctx)
        _ell(rg, 0.5, fl + 0.13, 0.34, 0.07, '#ef9fb0')
        _ell(_pc(ctx), 0.5, fl + 0.13, 0.27, 0.048, '#f8d3da')
        px_, py_ = p.get('picture', 0.2), 0.2
        fr = _pc(ctx)
        _poly(fr, [(px_ - 0.045, py_), (px_ + 0.045, py_), (px_ + 0.045, py_ + 0.15), (px_ - 0.045, py_ + 0.15)], '#c98a5a')
        _poly(_pc(ctx), [(px_ - 0.035, py_ + 0.02), (px_ + 0.035, py_ + 0.02), (px_ + 0.035, py_ + 0.13), (px_ - 0.035, py_ + 0.13)], '#bfe0f0')
        _heart(_pc(ctx), px_, py_ + 0.08, 0.03, '#ef6f8e')
    _poly(ctx, [(wx - 0.11, wy), (wx + 0.11, wy), (wx + 0.11, wy + 0.3), (wx - 0.11, wy + 0.3)], '#ffffff')
    _poly(ctx, [(wx - 0.1, wy + 0.02), (wx + 0.1, wy + 0.02), (wx + 0.1, wy + 0.28), (wx - 0.1, wy + 0.28)], sky_c)
    if p.get('snow', 0):
        for k in range(26):
            fx = wx - 0.095 + 0.19 * ((k * 0.381 + 0.012 * math.sin(t * 1.3 + k)) % 1.0)
            fy = wy + 0.025 + 0.25 * ((k * 0.137 + t * (0.1 + 0.03 * (k % 3))) % 1.0)
            _ell(ctx, fx, fy, 0.006 + 0.002 * (k % 3), 0.006 + 0.002 * (k % 3), '#ffffff')
        _poly(ctx, [(wx - 0.1, wy + 0.28), (wx - 0.1, wy + 0.262), (wx - 0.04, wy + 0.25), (wx + 0.03, wy + 0.262), (wx + 0.1, wy + 0.25), (wx + 0.1, wy + 0.28)], '#ffffff')
    ctx.line([(wx, wy + 0.02), (wx, wy + 0.28)], '#ffffff', 0.006)
    ctx.line([(wx - 0.1, wy + 0.15), (wx + 0.1, wy + 0.15)], '#ffffff', 0.006)
    if 'door' in p:
        _door(ctx, t, p, fl)
    if 'armchair' in p:
        _armchair(ctx, p)
    if p.get('cozy', 0):
        for side in (-1, 1):
            c = _pc(ctx)
            x0 = wx + side * 0.1
            _poly(c, [(x0 - 0.035, wy - 0.02), (x0 + 0.035, wy - 0.02), (x0 + 0.03 + 0.015 * side, wy + 0.34), (x0 - 0.03 + 0.015 * side, wy + 0.34)], p.get('curtain', '#e8708e'))
            _ell(_pc(ctx), x0 + 0.012 * side, wy + 0.2, 0.012, 0.022, '#f6c453')
        _poly(_pc(ctx), [(wx - 0.15, wy - 0.035), (wx + 0.15, wy - 0.035), (wx + 0.15, wy - 0.015), (wx - 0.15, wy - 0.015)], '#a86f45')


@element('table')
def table(ctx, t, tl, p):
    """A round-cornered table: x, y (floor), s."""
    x, y, s = p.get('x', 0.5), p.get('y', 0.86), p.get('s', 1.0)
    _poly(ctx, [(x - 0.13 * s, y - 0.18 * s), (x + 0.13 * s, y - 0.18 * s), (x + 0.13 * s, y - 0.16 * s), (x - 0.13 * s, y - 0.16 * s)], '#a86f45')
    for dx in (-0.11, 0.11):
        ctx.line([(x + dx * s, y - 0.165 * s), (x + dx * s, y)], '#8a5a3a', 0.012 * s)


@element('cake')
def cake(ctx, t, tl, p):
    """A two-tier birthday cake with soft rounded tiers, cream, strawberries and flickering striped candles: x, y (bottom), s, candles."""
    x, y, s = p.get('x', 0.5), p.get('y', 0.68), p.get('s', 1.0)
    ar = ctx.ar
    P_ = lambda u, v: (x + u * s * ar, y + v * s)
    cream, pink, blue = '#fbf1dc', '#f6c3d4', '#a9c8ec'

    def rrect(c, u0, v0, u1, v1, r, col):
        (a0, b0), (a1, b1) = P_(u0, v0), P_(u1, v1)
        c.d.rounded_rectangle([a0 * c.W, b0 * c.H, a1 * c.W, b1 * c.H], radius=r * s * c.H, fill=col)

    def dot(c, u, v, r, col):
        cx, cy = P_(u, v)
        _ell(c, cx, cy, r * s, r * s, col)
    _ell(_pc(ctx), x, y - 0.004 * s, 0.16 * s, 0.014 * s, '#e9e2f2')
    rrect(_pc(ctx), -0.13, -0.095, 0.13, 0.0, 0.03, cream)
    wave = _pc(ctx)
    for k in range(14):
        dot(wave, -0.12 + k * 0.0185, -0.012, 0.013, pink)
    dots = _pc(ctx)
    for u in (-0.08, -0.027, 0.027, 0.08):
        dot(dots, u, -0.048, 0.013, '#fbe7a1')
    rrect(_pc(ctx), -0.095, -0.165, 0.095, -0.088, 0.028, cream)
    band = _pc(ctx)
    for k in range(13):
        dot(band, -0.125 + k * 0.0208, -0.092, 0.015, blue)
    for u in (-0.075, 0.0, 0.075):
        st_ = _pc(ctx)
        cx, cy = P_(u, -0.096)
        st_.d.polygon([(a * st_.W, b * st_.H) for a, b in (P_(u - 0.022, -0.106), P_(u + 0.022, -0.106), P_(u, -0.07))], fill='#e0526f')
        dot(st_, u, -0.104, 0.021, '#e0526f')
        lf = _pc(ctx)
        for du in (-0.012, 0.0, 0.012):
            dot(lf, u + du, -0.122, 0.008, '#5aa04a')
    drip = _pc(ctx)
    rrect(drip, -0.095, -0.165, 0.095, -0.145, 0.02, pink)
    for k, u in enumerate((-0.072, -0.04, -0.005, 0.03, 0.065)):
        L = 0.018 + 0.012 * (k % 2)
        rrect(drip, u - 0.01, -0.15, u + 0.01, -0.15 + L, 0.01, pink)
    for u in (-0.08, 0.08):
        dot(_pc(ctx), u, -0.172, 0.014, '#d9415c')
    n = max(1, int(p.get('candles', 3)))
    gap = min(0.034, 0.15 / max(1, n - 1)) if n > 1 else 0
    for k in range(n):
        u = (k - (n - 1) / 2) * gap
        cd = _pc(ctx)
        rrect(cd, u - 0.0075, -0.215, u + 0.0075, -0.163, 0.004, '#bcd8f2')
        for j in range(3):
            rrect(cd, u - 0.0075, -0.205 + j * 0.016, u + 0.0075, -0.198 + j * 0.016, 0.002, '#f28bb0')
        fl = 1 + 0.18 * math.sin(t * 13 + k * 1.7)
        fx, fy = P_(u, -0.232)
        fm = _pc(ctx)
        _ell(fm, fx, fy, 0.011 * s, 0.017 * s * fl, '#f6c453')
        _ell(fm, fx, fy + 0.004 * s, 0.005 * s, 0.008 * s * fl, '#f28b3a')


@element('garland')
def garland(ctx, t, tl, p):
    """A string of felt light bulbs sagging across the wall: y (top), x0, x1, sag; bulbs glow gently."""
    y, x0, x1, sag = p.get('y', 0.08), p.get('x0', 0.05), p.get('x1', 0.95), p.get('sag', 0.07)
    n = int(p.get('bulbs', 14))
    cols = ('#5a7fc4', '#9bd27a', '#f6c453', '#f28b3a', '#e0526f')
    pts = [(x0 + (x1 - x0) * k / 40, y + sag * 4 * (k / 40) * (1 - k / 40)) for k in range(41)]
    ctx.line(pts, '#3f7a4a', 0.003)
    for k in range(n):
        f = (k + 0.5) / n
        bx = x0 + (x1 - x0) * f
        by = y + sag * 4 * f * (1 - f)
        b = _pc(ctx)
        _poly(b, [(bx - 0.006, by), (bx + 0.006, by), (bx + 0.006, by + 0.018), (bx - 0.006, by + 0.018)], '#2f6a3a')
        glow = 1 + 0.06 * math.sin(t * 3 + k)
        _ell(b, bx, by + 0.045, 0.019 * glow, 0.032 * glow, cols[k % len(cols)])


@element('balloon_bunch')
def balloon_bunch(ctx, t, tl, p):
    """Three felt balloons tied together, swaying: x, y (where the strings are tied), s."""
    x, y, s = p.get('x', 0.1), p.get('y', 0.7), p.get('s', 1.0)
    cols = p.get('colors', ('#e0526f', '#f6c453', '#5fb0d8'))
    for k, (dx, h) in enumerate(((-0.03, 0.36), (0.0, 0.43), (0.032, 0.34))):
        sw = 0.006 * math.sin(t * 1.3 + k * 1.9)
        bx, by = x + (dx * s + sw) * ctx.ar * 2.2, y - h * s
        ctx.line([(x, y), (bx, by + 0.06 * s)], '#8a8a8a', 0.0025)
        b = _pc(ctx)
        _ell(b, bx, by, 0.045 * s, 0.058 * s, cols[k % len(cols)])
        _poly(b, [(bx - 0.006 * s, by + 0.066 * s), (bx + 0.006 * s, by + 0.066 * s), (bx, by + 0.054 * s)], cols[k % len(cols)])


@element('toys')
def toys(ctx, t, tl, p):
    """Small things on the floor so a room is not empty: wooden blocks, a ball, a party hat, confetti; x0, x1, y (floor)."""
    x0, x1, y = p.get('x0', 0.05), p.get('x1', 0.95), p.get('y', 0.97)
    span = x1 - x0
    for k, (f, col) in enumerate(((0.06, '#f28b3a'), (0.1, '#5fb0d8'))):
        b = _pc(ctx)
        bx = x0 + span * f
        b.d.rounded_rectangle([(bx - 0.014) * b.W, (y - 0.05 - 0.004 * k) * b.H, (bx + 0.014) * b.W, (y - 0.002) * b.H], radius=0.006 * b.H, fill=col)
    bl = _pc(ctx)
    _ell(bl, x0 + span * 0.92, y - 0.03, 0.03, 0.03, '#e0526f')
    _ell(_pc(ctx), x0 + span * 0.92, y - 0.03, 0.03, 0.008, '#fbf1dc')
    hx = x0 + span * 0.56
    _poly(_pc(ctx), [(hx - 0.018, y - 0.003), (hx + 0.018, y - 0.003), (hx + 0.003, y - 0.075)], '#9b7bc4')
    _ell(_pc(ctx), hx + 0.003, y - 0.078, 0.009, 0.009, '#f6c453')
    conf = _pc(ctx)
    r = np.random.default_rng(int(p.get('seed', 5)))
    cols = ('#e0526f', '#f6c453', '#5fb0d8', '#9bd27a', '#b99be0')
    for k in range(int(p.get('confetti', 14))):
        _ell(conf, x0 + span * r.random(), y - 0.012 - 0.03 * r.random(), 0.006, 0.006, cols[k % 5])


@element('gift')
def gift(ctx, t, tl, p):
    """A wrapped present: x, y (bottom), s, color."""
    x, y, s = p.get('x', 0.5), p.get('y', 0.86), p.get('s', 1.0)
    col = p.get('color', '#7fb6e8')
    _poly(ctx, [(x - 0.04 * s, y), (x + 0.04 * s, y), (x + 0.04 * s, y - 0.15 * s), (x - 0.04 * s, y - 0.15 * s)], col)
    ctx.line([(x, y), (x, y - 0.15 * s)], '#f6d353', 0.018 * s)
    ctx.line([(x - 0.04 * s, y - 0.075 * s), (x + 0.04 * s, y - 0.075 * s)], '#f6d353', 0.018 * s)
    _ell(ctx, x - 0.014 * s, y - 0.165 * s, 0.03 * s, 0.018 * s, '#f6d353')
    _ell(ctx, x + 0.014 * s, y - 0.165 * s, 0.03 * s, 0.018 * s, '#f6d353')


@element('lamp')
def lamp(ctx, t, tl, p):
    """A floor lamp: x, y (floor), s, on=1 glows."""
    x, y, s = p.get('x', 0.2), p.get('y', 0.86), p.get('s', 1.0)
    ctx.line([(x, y), (x, y - 0.3 * s)], '#6a5a4a', 0.006 * s)
    _poly(ctx, [(x - 0.05 * s, y - 0.3 * s), (x + 0.05 * s, y - 0.3 * s), (x + 0.03 * s, y - 0.38 * s), (x - 0.03 * s, y - 0.38 * s)], '#ffe39a' if p.get('on', 1) else '#e9d7b0')
    _ell(ctx, x, y, 0.035 * s, 0.008 * s, '#6a5a4a')


@element('bed')
def bed(ctx, t, tl, p):
    """A bed with a blanket: x, y (floor), s, color."""
    x, y, s = p.get('x', 0.3), p.get('y', 0.88), p.get('s', 1.0)
    col = p.get('color', '#9fc8e8')
    _poly(ctx, [(x - 0.17 * s, y - 0.02 * s), (x + 0.17 * s, y - 0.02 * s), (x + 0.17 * s, y - 0.1 * s), (x - 0.17 * s, y - 0.1 * s)], '#b07a4a')
    _poly(ctx, [(x - 0.19 * s, y), (x - 0.16 * s, y), (x - 0.16 * s, y - 0.2 * s), (x - 0.19 * s, y - 0.2 * s)], '#a86f45')
    _poly(ctx, [(x - 0.12 * s, y - 0.1 * s), (x + 0.17 * s, y - 0.1 * s), (x + 0.17 * s, y - 0.14 * s), (x - 0.12 * s, y - 0.14 * s)], col)
    _ell(ctx, x - 0.12 * s, y - 0.135 * s, 0.035 * s, 0.022 * s, '#ffffff')


@element('ground')
def ground(ctx, t, tl, p):
    """Flat ground from top down: kind=meadow|sand|road|path."""
    top = p.get('top', 0.7)
    col = {'meadow': P['hill'], 'sand': P['sand'], 'road': '#9a9aa6', 'path': '#e6cf9e'}.get(p.get('kind', 'meadow'), P['hill'])
    pts = [(k / 30, top - 0.008 * math.sin(k / 30 * 7)) for k in range(31)]
    _poly(ctx, pts + [(1, 1), (0, 1)], col)
    if p.get('kind', 'meadow') == 'road':
        for k in range(8):
            x = (k / 8 + tl * p.get('speed', 0)) % 1.0
            _poly(ctx, [(x, top + 0.12), (x + 0.05, top + 0.12), (x + 0.05, top + 0.13), (x, top + 0.13)], '#f4f4f4')


def _box(ctx, x0, y0, x1, y1, col):
    _poly(ctx, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], col)


def _indoors(ctx, p, wall, floor_a, floor_b):
    """A wall and a floor of big felt tiles, the base of every indoor place; returns the floor line."""
    fl = p.get('floor', 0.78)
    _box(ctx, 0, 0, 1, fl, p.get('color', wall))
    _box(ctx, 0, fl, 1, 1, floor_a)
    for k in range(12):
        for row in range(2):
            if (k + row) % 2:
                _box(ctx, k / 12, fl + row * (1 - fl) / 2, (k + 1) / 12, fl + (row + 1) * (1 - fl) / 2, floor_b)
    return fl


def _window(ctx, wx, wy, w, h, time):
    F = _pc(ctx)
    _box(F, wx - w, wy, wx + w, wy + h, '#ffffff')
    G = _pc(ctx)
    _box(G, wx - w * 0.9, wy + 0.015, wx + w * 0.9, wy + h - 0.015, {'night': '#2a3a78', 'sunset': '#f2a07a'}.get(time, '#a9d8f2'))
    G.line([(wx, wy + 0.015), (wx, wy + h - 0.015)], '#ffffff', 0.006)


@element('kitchen')
def kitchen(ctx, t, tl, p):
    """A whole kitchen: tiled wall, fridge, cupboards, a stove with a pot, a sink, a window. color (wall), cupboard, window, time, floor."""
    fl = _indoors(ctx, p, '#f6ecd2', '#d9b98c', '#c9a678')
    cup = p.get('cupboard', '#8fc7b8')
    for k in range(20):
        ctx.line([(k / 20, 0.3), (k / 20, fl)], _shade_hex(p.get('color', '#f6ecd2'), 0.96), 0.002)
    _window(ctx, p.get('window', 0.42), 0.14, 0.09, 0.26, p.get('time', 'day'))
    Fr = _pc(ctx)
    _box(Fr, 0.04, 0.2, 0.16, fl + 0.03, '#e9eef2')
    Fr.line([(0.04, 0.42), (0.16, 0.42)], '#b8c4cc', 0.005)
    _box(_pc(ctx), 0.14, 0.3, 0.148, 0.39, '#9aa6b0')
    _box(_pc(ctx), 0.14, 0.46, 0.148, 0.58, '#9aa6b0')
    for x0 in (0.56, 0.7, 0.84):
        U = _pc(ctx)
        _box(U, x0, 0.08, x0 + 0.13, 0.3, cup)
        _ell(_pc(ctx), x0 + 0.1, 0.26, 0.009, 0.009, '#f6c453')
    C = _pc(ctx)
    _box(C, 0.18, 0.56, 0.98, fl + 0.03, cup)
    _box(_pc(ctx), 0.17, 0.53, 0.99, 0.565, '#e8d9b8')
    for x0 in (0.2, 0.33, 0.8):
        _box(_pc(ctx), x0, 0.6, x0 + 0.11, fl - 0.01, _shade_hex(cup, 0.9))
    St = _pc(ctx)
    _box(St, 0.53, 0.53, 0.72, fl + 0.03, '#d7dde2')
    _box(_pc(ctx), 0.56, 0.62, 0.69, fl - 0.01, '#5a6470')
    Pt = _pc(ctx)
    _box(Pt, 0.58, 0.43, 0.67, 0.53, p.get('pot', '#e0605a'))
    _box(_pc(ctx), 0.572, 0.415, 0.678, 0.44, _shade_hex(p.get('pot', '#e0605a'), 0.85))
    _ell(_pc(ctx), 0.625, 0.405, 0.014, 0.012, '#3a3a4a')
    Sk = _pc(ctx)
    _box(Sk, 0.3, 0.52, 0.46, 0.54, '#b8c4cc')
    Sk.line([(0.38, 0.52), (0.38, 0.45), (0.41, 0.45), (0.41, 0.48)], '#9aa6b0', 0.011)


@element('classroom')
def classroom(ctx, t, tl, p):
    """A classroom from inside: a green blackboard with chalk, a clock, a window, a shelf of books, a teacher's table, small desks. color (wall), board, window, time, floor, desks=0 removes the desks."""
    fl = _indoors(ctx, p, '#e6efdc', '#d8b488', '#caa478')
    _box(_pc(ctx), 0.27, 0.1, 0.73, 0.54, '#a8743f')
    B = _pc(ctx)
    _box(B, 0.285, 0.125, 0.715, 0.515, p.get('board', '#3f6e5a'))
    B.line([(0.32, 0.22), (0.44, 0.22)], '#f4f4e8', 0.007)
    B.line([(0.32, 0.3), (0.5, 0.3)], '#f4f4e8', 0.007)
    B.line([(0.32, 0.38), (0.4, 0.38)], '#f4f4e8', 0.007)
    _ell(B, 0.6, 0.3, 0.09, 0.09, '#f4f4e8')
    _ell(B, 0.6, 0.3, 0.075, 0.075, p.get('board', '#3f6e5a'))
    _box(_pc(ctx), 0.27, 0.54, 0.73, 0.56, '#8a5a3a')
    _ell(_pc(ctx), 0.5, 0.06, 0.05, 0.05, '#ffffff')
    Ck = _pc(ctx)
    Ck.line([(0.5, 0.06), (0.5, 0.032)], '#3a3a4a', 0.006)
    Ck.line([(0.5, 0.06), (0.513, 0.07)], '#3a3a4a', 0.006)
    _window(ctx, p.get('window', 0.13), 0.14, 0.09, 0.32, p.get('time', 'day'))
    _box(_pc(ctx), 0.8, 0.26, 0.98, 0.285, '#a8743f')
    Bk = _pc(ctx)
    for k, col in enumerate(HOUSE):
        _box(Bk, 0.81 + k * 0.02, 0.17 + 0.012 * (k % 3), 0.828 + k * 0.02, 0.26, col)
    Td = _pc(ctx)
    _box(Td, 0.78, 0.6, 0.98, 0.64, '#b98a58')
    _box(Td, 0.8, 0.64, 0.82, fl + 0.03, '#a8743f')
    _box(Td, 0.94, 0.64, 0.96, fl + 0.03, '#a8743f')
    if p.get('desks', 1):
        for x0 in (0.06, 0.28, 0.5):
            D = _pc(ctx)
            _box(D, x0, 0.66, x0 + 0.15, 0.69, '#e0c48c')
            _box(D, x0 + 0.015, 0.69, x0 + 0.03, fl + 0.05, '#7f8fa0')
            _box(D, x0 + 0.12, 0.69, x0 + 0.135, fl + 0.05, '#7f8fa0')


@element('shop')
def shop(ctx, t, tl, p):
    """A small grocery from inside: shelves of boxes, jars and fruit, a striped awning, a counter with scales and a till. color (wall), awning, floor."""
    fl = _indoors(ctx, p, '#fbeed6', '#e4d0ae', '#d6bf98')
    r = np.random.default_rng(int(p.get('seed', 6)))
    for k, y in enumerate((0.3, 0.46, 0.62)):
        Sf = _pc(ctx)
        _box(Sf, 0.05, y, 0.68, y + 0.02, '#a8743f')
        G = _pc(ctx)
        x = 0.06
        while x < 0.6:
            kind, col = r.integers(3), HOUSE[int(r.integers(len(HOUSE)))]
            if kind == 0:
                h = 0.07 + 0.04 * r.random()
                _box(G, x, y - h, x + 0.04, y, col)
                _box(G, x + 0.006, y - h * 0.7, x + 0.034, y - h * 0.35, '#fff7e6')
                x += 0.048
            elif kind == 1:
                _box(G, x + 0.003, y - 0.08, x + 0.03, y, col)
                _box(G, x + 0.008, y - 0.1, x + 0.025, y - 0.08, '#fbfbf6')
                x += 0.04
            else:
                for j in range(3):
                    _ell(G, x + 0.012 + j * 0.026, y - 0.027, 0.027, 0.027, ('#e0605a', '#f6c453', '#8cc26a')[k])
                x += 0.08
    aw = p.get('awning', '#e0605a')
    A = _pc(ctx)
    for k in range(20):
        col = aw if k % 2 == 0 else '#fbfbf6'
        _poly(A, [(k / 20, 0), ((k + 1) / 20, 0), ((k + 1) / 20, 0.09), ((k + 0.5) / 20, 0.125), (k / 20, 0.09)], col)
    C = _pc(ctx)
    _box(C, 0.7, 0.56, 0.99, fl + 0.05, '#c98a5a')
    _box(_pc(ctx), 0.69, 0.53, 1.0, 0.565, '#a8743f')
    Tl = _pc(ctx)
    _box(Tl, 0.9, 0.41, 0.98, 0.53, '#7f8fa0')
    _box(_pc(ctx), 0.91, 0.425, 0.97, 0.465, '#bfe6d0')
    Sc = _pc(ctx)
    _box(Sc, 0.74, 0.5, 0.82, 0.53, '#d7dde2')
    Sc.line([(0.78, 0.5), (0.78, 0.45)], '#9aa6b0', 0.01)
    _ell(Sc, 0.78, 0.44, 0.075, 0.016, '#d7dde2')


@element('ferris_wheel')
def ferris_wheel(ctx, t, tl, p):
    """A big wheel that turns, with hanging cabins: x, y (ground), r (radius, of the frame height), speed (turns a minute), cabins."""
    x, y, r = p.get('x', 0.7), p.get('y', 0.8), p.get('r', 0.3)
    n, a0 = int(p.get('cabins', 8)), t * p.get('speed', 3) * math.pi / 30
    ar = ctx.ar
    cy = y - r * 1.15
    L = _pc(ctx)
    L.line([(x - r * 0.6 * ar, y), (x, cy)], '#8a6a9a', 0.016)
    L.line([(x + r * 0.6 * ar, y), (x, cy)], '#8a6a9a', 0.016)
    R = _pc(ctx)
    pts = [(x + r * ar * math.cos(k * math.pi / 30), cy + r * math.sin(k * math.pi / 30)) for k in range(61)]
    R.line(pts, '#f2a0b8', 0.012)
    for k in range(n):
        a = a0 + 2 * math.pi * k / n
        R.line([(x, cy), (x + r * ar * math.cos(a), cy + r * math.sin(a))], '#f2c4d0', 0.006)
    _ell(_pc(ctx), x, cy, 0.024, 0.024, '#f6c453')
    for k in range(n):
        a = a0 + 2 * math.pi * k / n
        px, py = x + r * ar * math.cos(a), cy + r * math.sin(a)
        C = _pc(ctx)
        C.line([(px, py), (px, py + 0.03)], '#7a6a7a', 0.004)
        _ell(C, px, py + 0.055, 0.042, 0.03, HOUSE[k % len(HOUSE)])
        _box(C, px - 0.0165, py + 0.02, px + 0.0165, py + 0.045, HOUSE[k % len(HOUSE)])


@element('carousel')
def carousel(ctx, t, tl, p):
    """A merry-go-round with a striped roof and horses that go round: x, y (ground), s, speed."""
    x, y, s = p.get('x', 0.3), p.get('y', 0.85), p.get('s', 1.0)
    w, h = 0.17 * s, 0.42 * s
    _ell(_pc(ctx), x, y - 0.02 * s, w / ctx.ar, 0.035 * s, '#d9a860')
    _box(_pc(ctx), x - 0.008 * s, y - h, x + 0.008 * s, y, '#f6c453')
    for k in range(5):
        a = t * p.get('speed', 1.2) + k * 2 * math.pi / 5
        front = math.sin(a) > 0
        px = x + w * 0.82 * math.cos(a)
        bob = 0.015 * s * math.sin(a * 2 + k)
        if not front:
            _carousel_horse(_pc(ctx), px, y, h, s, bob, k, math.sin(a + 1.57) < 0)
    R = _pc(ctx)
    n = 10
    for k in range(n):
        col = '#e0605a' if k % 2 == 0 else '#fbfbf6'
        _poly(R, [(x, y - h - 0.14 * s), (x - w + 2 * w * k / n, y - h), (x - w + 2 * w * (k + 1) / n, y - h)], col)
    _box(_pc(ctx), x - w, y - h, x + w, y - h + 0.03 * s, '#f6c453')
    _ell(_pc(ctx), x, y - h - 0.15 * s, 0.018 * s, 0.018 * s, '#f6c453')
    for k in range(5):
        a = t * p.get('speed', 1.2) + k * 2 * math.pi / 5
        if math.sin(a) > 0:
            _carousel_horse(_pc(ctx), x + w * 0.82 * math.cos(a), y, h, s, 0.015 * s * math.sin(a * 2 + k), k, math.sin(a + 1.57) < 0)


def _carousel_horse(c, px, y, h, s, bob, k, left):
    d = -1 if left else 1
    ar = c.ar
    c.line([(px, y - h), (px, y - 0.03 * s)], '#d9d9de', 0.005 * s)
    by = y - 0.17 * s + bob
    col = HOUSE[k % len(HOUSE)]
    u = 0.07 * s * ar  # half a body, on screen
    for lx, ly in ((-0.75, 0.065), (-0.35, 0.075), (0.35, 0.075), (0.75, 0.065)):
        c.line([(px + d * lx * u, by + 0.015 * s), (px + d * lx * u * 1.15, by + ly * s)], _shade_hex(col, 0.85), 0.014 * s)
    c.line([(px - d * u * 0.9, by - 0.01 * s), (px - d * u * 1.5, by + 0.035 * s)], '#fbfbf6', 0.012 * s)
    _ell(c, px, by, 0.07 * s, 0.036 * s, col)
    c.line([(px + d * u * 0.7, by - 0.01 * s), (px + d * u * 1.15, by - 0.065 * s)], col, 0.03 * s)
    _ell(c, px + d * u * 1.45, by - 0.07 * s, 0.03 * s, 0.021 * s, col)
    _ell(c, px + d * u * 1.45, by - 0.076 * s, 0.005 * s, 0.005 * s, '#2a2020')
    c.line([(px + d * u * 0.55, by - 0.035 * s), (px + d * u * 1.0, by - 0.095 * s)], '#fbfbf6', 0.01 * s)


@element('stall')
def stall(ctx, t, tl, p):
    """A fair stall with a striped canopy and a counter: x, y (ground), s, color."""
    x, y, s, col = p.get('x', 0.5), p.get('y', 0.85), p.get('s', 1.0), p.get('color', '#4f9fd0')
    w = 0.09 * s
    _box(_pc(ctx), x - w, y - 0.3 * s, x + w, y - 0.1 * s, '#fbeed6')
    for u in (-1, 1):
        _box(_pc(ctx), x + u * w - 0.005 * s, y - 0.34 * s, x + u * w + 0.005 * s, y, '#a8743f')
    _box(_pc(ctx), x - w, y - 0.12 * s, x + w, y, col)
    C = _pc(ctx)
    for k in range(8):
        c = col if k % 2 == 0 else '#fbfbf6'
        x0, x1 = x - w * 1.15 + 2.3 * w * k / 8, x - w * 1.15 + 2.3 * w * (k + 1) / 8
        _poly(C, [(x0 + (x - x0) * 0.2, y - 0.44 * s), (x1 + (x - x1) * 0.2, y - 0.44 * s), (x1, y - 0.33 * s), (x0, y - 0.33 * s)], c)


@element('bunting')
def bunting(ctx, t, tl, p):
    """A string of little triangle flags across the frame: y (top), x0, x1, sag, flags."""
    y, x0, x1, n, sag = p.get('y', 0.06), p.get('x0', 0.0), p.get('x1', 1.0), int(p.get('flags', 18)), p.get('sag', 0.05)
    pts = [(x0 + (x1 - x0) * k / 40, y + sag * 4 * (k / 40) * (1 - k / 40)) for k in range(41)]
    ctx.line(pts, '#7a6a5a', 0.003)
    F = _pc(ctx)
    for k in range(n):
        f = (k + 0.5) / n
        fx, fy = x0 + (x1 - x0) * f, y + sag * 4 * f * (1 - f)
        _poly(F, [(fx - 0.014, fy), (fx + 0.014, fy), (fx, fy + 0.07)], HOUSE[k % len(HOUSE)])


@element('barn')
def barn(ctx, t, tl, p):
    """A red barn with white crossed doors and a hay loft: x, y (ground), s, color."""
    x, y, s, col = p.get('x', 0.3), p.get('y', 0.8), p.get('s', 1.0), p.get('color', '#c9544a')
    w, h = 0.13 * s, 0.3 * s
    B = _pc(ctx)
    _poly(B, [(x - w, y), (x + w, y), (x + w, y - h), (x + w * 0.6, y - h - 0.12 * s), (x, y - h - 0.2 * s), (x - w * 0.6, y - h - 0.12 * s), (x - w, y - h)], col)
    R = _pc(ctx)
    R.line([(x - w * 1.08, y - h + 0.01 * s), (x - w * 0.6, y - h - 0.12 * s), (x, y - h - 0.2 * s), (x + w * 0.6, y - h - 0.12 * s), (x + w * 1.08, y - h + 0.01 * s)], '#fbfbf6', 0.016 * s)
    D = _pc(ctx)
    _box(D, x - w * 0.42, y - h * 0.62, x + w * 0.42, y, '#fbfbf6')
    _box(_pc(ctx), x - w * 0.36, y - h * 0.57, x + w * 0.36, y, _shade_hex(col, 0.8))
    X = _pc(ctx)
    X.line([(x - w * 0.36, y - h * 0.57), (x + w * 0.36, y)], '#fbfbf6', 0.012 * s)
    X.line([(x + w * 0.36, y - h * 0.57), (x - w * 0.36, y)], '#fbfbf6', 0.012 * s)
    _box(_pc(ctx), x - w * 0.2, y - h - 0.09 * s, x + w * 0.2, y - h + 0.01 * s, '#fbfbf6')
    _box(_pc(ctx), x - w * 0.15, y - h - 0.075 * s, x + w * 0.15, y - h, '#5a3a2a')


@element('haystack')
def haystack(ctx, t, tl, p):
    """A round haystack: x, y (ground), s."""
    x, y, s = p.get('x', 0.6), p.get('y', 0.85), p.get('s', 1.0)
    _ell(_pc(ctx), x, y - 0.1 * s, 0.17 * s, 0.11 * s, '#e8c35a')
    H = _pc(ctx)
    for k in range(9):
        u = (k - 4) / 4
        H.line([(x + u * 0.05 * s, y - 0.17 * s + abs(u) * 0.05 * s), (x + u * 0.062 * s, y - 0.05 * s)], '#cfa63f', 0.005 * s)


@element('tractor')
def tractor(ctx, t, tl, p):
    """A little tractor: x, y (ground), s, color; drive=0.05 moves it right per second, and its wheels turn."""
    x, y, s, col = p.get('x', 0.7), p.get('y', 0.88), p.get('s', 1.0), p.get('color', '#5fae4e')
    x += p.get('drive', 0) * tl
    spin = t * p.get('drive', 0) * 40
    B = _pc(ctx)
    _box(B, x - 0.03 * s, y - 0.17 * s, x + 0.09 * s, y - 0.09 * s, col)
    _box(B, x - 0.055 * s, y - 0.26 * s, x + 0.012 * s, y - 0.09 * s, col)
    _box(_pc(ctx), x - 0.045 * s, y - 0.245 * s, x + 0.002 * s, y - 0.17 * s, '#bfe0f0')
    _box(_pc(ctx), x + 0.065 * s, y - 0.23 * s, x + 0.073 * s, y - 0.17 * s, '#5a5a64')
    for wx, r in ((-0.04, 0.095), (0.075, 0.055)):
        W = _pc(ctx)
        _ell(W, x + wx * s, y - r * s, r * s, r * s, '#3a3a44')
        _ell(W, x + wx * s, y - r * s, r * 0.5 * s, r * 0.5 * s, '#f6c453')
        W.line([(x + wx * s, y - r * s), (x + wx * s + r * 0.2 * s * math.cos(spin), y - r * s + r * 0.45 * s * math.sin(spin))], '#a8843f', 0.008 * s)


@element('underwater')
def underwater(ctx, t, tl, p):
    """The sea from inside: bands of blue water with soft waves of light, a sandy bottom from floor= down, rocks and corals. color (top water). Add seaweed and fish for life."""
    fl, top = p.get('floor', 0.8), p.get('color', '#5cc0d8')
    _box(ctx, 0, 0, 1, 1, top)
    for k in range(1, 6):
        y = k / 6 * fl
        col = _shade_hex(top, 1 - 0.1 * k)
        pts = [(i / 40, y + 0.012 * math.sin(i / 40 * 14 + k * 1.7)) for i in range(41)]
        _poly(ctx, pts + [(1, 1), (0, 1)], col)
    for x0 in (0.08, 0.3, 0.55, 0.78):  # faint rays, straight on the water so they have no felt edge
        for k in range(1, 5):
            y = k / 6 * fl
            _poly(ctx, [(x0 - k * 0.02, y - fl / 6), (x0 + 0.05 - k * 0.02, y - fl / 6), (x0 + 0.03 - k * 0.02, y), (x0 - 0.02 - k * 0.02, y)], _shade_hex(top, 1.05 - 0.1 * (k - 1)))
    S = _pc(ctx)
    pts = [(i / 40, fl + 0.02 * math.sin(i / 40 * 9)) for i in range(41)]
    _poly(S, pts + [(1, 1), (0, 1)], '#e8d6a0')
    r = np.random.default_rng(int(p.get('seed', 5)))
    for x0 in (0.1, 0.36, 0.64, 0.9):
        C = _pc(ctx)
        col = ('#f28b6b', '#f2a0b8', '#f6c453', '#b99be0')[int(r.integers(4))]
        for k in range(5):
            a = -1.57 + (k - 2) * 0.45
            C.line([(x0, fl + 0.03), (x0 + 0.05 * math.cos(a), fl + 0.03 + 0.15 * math.sin(a))], col, 0.02)
            _ell(C, x0 + 0.05 * math.cos(a), fl + 0.03 + 0.15 * math.sin(a), 0.016, 0.016, col)
        _ell(_pc(ctx), x0 + 0.06, fl + 0.06, 0.05, 0.03, '#a8a8b4')


@element('seaweed')
def seaweed(ctx, t, tl, p):
    """Seaweed swaying under water: x, y (bottom), s, color."""
    x, y, s, col = p.get('x', 0.2), p.get('y', 0.85), p.get('s', 1.0), p.get('color', '#4f9a6e')
    for k, dx in enumerate((-0.016, 0.0, 0.016)):
        W = _pc(ctx)
        pts = []
        for i in range(21):
            f = i / 20
            pts.append((x + dx * s + 0.02 * s * f * math.sin(t * 1.3 + f * 4 + k), y - (0.34 + 0.08 * k % 0.16) * s * f))
        W.line(pts, _shade_hex(col, 1 - 0.1 * k), 0.022 * s)


@element('fish')
def fish(ctx, t, tl, p):
    """A few bright fish swimming across: count, y0, y1 (where they swim), seed."""
    n, y0, y1 = int(p.get('count', 6)), p.get('y0', 0.15), p.get('y1', 0.65)
    r = np.random.default_rng(int(p.get('seed', 9)))
    for k in range(n):
        d = 1 if r.random() < 0.5 else -1
        sp, ph, yy, s = 0.03 + 0.03 * r.random(), r.random(), y0 + (y1 - y0) * r.random(), 0.6 + 0.6 * r.random()
        x = (ph + d * sp * t) % 1.2 - 0.1
        y = yy + 0.012 * math.sin(t * 2 + k)
        col = HOUSE[k % len(HOUSE)]
        F = _pc(ctx)
        ar = ctx.ar
        _poly(F, [(x - d * 0.05 * s * ar, y), (x - d * 0.1 * s * ar, y - 0.03 * s), (x - d * 0.1 * s * ar, y + 0.03 * s)], col)
        _ell(F, x, y, 0.06 * s, 0.033 * s, col)
        _ell(_pc(ctx), x + d * 0.032 * s * ar, y - 0.008 * s, 0.008 * s, 0.008 * s, '#2a2020')


@element('city_night')
def city_night(ctx, t, tl, p):
    """A city at night: dark sky with stars and a moon, far and near houses with lit windows, street lamps with a glow, a street from base= down. Lights twinkle slowly. Put no sky with it; heroes get the night light by themselves."""
    base = p.get('base', 0.78)
    sky(ctx, t, tl, {'time': 'night'})
    _ell(_pc(ctx), p.get('moon', 0.82), 0.14, 0.06, 0.06, P['moon'])
    r = np.random.default_rng(int(p.get('seed', 8)))
    for layer_k, (h0, col) in enumerate(((0.5, '#2c3768'), (0.36, '#3c4a80'))):
        L = _pc(ctx)
        x = -0.02
        while x < 1.02:
            w, h = 0.06 + 0.05 * r.random(), h0 * (0.7 + 0.5 * r.random())
            _box(L, x, base - h, x + w, base, col)
            for wy in np.arange(base - h + 0.03, base - 0.04, 0.06):
                for wx in np.arange(x + 0.01, x + w - 0.018, 0.024):
                    if r.random() < 0.55:
                        on = 0.5 + 0.5 * math.sin(t * 0.5 + wx * 90 + wy * 70) > 0.12
                        _box(L, wx, wy, wx + 0.013, wy + 0.03, '#ffd97a' if on else '#54609a')
            x += w + 0.004
    S = _pc(ctx)
    _box(S, 0, base, 1, 1, '#4a4f72')
    for k in range(9):
        _box(S, k / 9 + 0.02, base + 0.12, k / 9 + 0.07, base + 0.13, '#d8c86a')
    for x0 in p.get('lamps', (0.14, 0.5, 0.86)):
        _ell(_pc(ctx), x0, base - 0.29, 0.08, 0.08, '#5f6496')
        Lp = _pc(ctx)
        Lp.line([(x0, base + 0.04), (x0, base - 0.27)], '#20264e', 0.012)
        _ell(_pc(ctx), x0, base - 0.29, 0.03, 0.03, '#ffe9a0')
