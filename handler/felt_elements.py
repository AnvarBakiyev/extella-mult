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
    """A planet with continents and an optional ring: x, y, r, ring=1."""
    x, y, r = p.get('x', 0.5), p.get('y', 0.5), p.get('r', 0.2)
    _ell(ctx, x, y, r, r, p.get('color', '#4a86c8'))
    rot = t * 0.02
    for dx, dy, rr in ((-0.35, -0.2, 0.3), (0.3, 0.1, 0.35), (-0.1, 0.45, 0.22)):
        cx = x + ((dx + rot) % 1.4 - 0.7) * r * ctx.ar * 1.2
        if abs(cx - x) < r * ctx.ar * 0.75:
            _ell(ctx, cx, y + dy * r, rr * r, rr * r * 0.8, '#6fbf6a')
    if p.get('ring', 0):
        ctx.ellipse(x, y, r * 1.6, r * 0.25, '#e8c98a', angle=-0.25)


@element('rocket')
def rocket(ctx, t, tl, p):
    """A rocket: x, y (base), s; flying=1 shakes it and adds a flame."""
    x, y, s = p.get('x', 0.5), p.get('y', 0.8), p.get('s', 1.0)
    y -= p.get('rise', 0) * tl  # rise=0.15 lifts it 0.15 of the frame per second
    sh = 0.002 * math.sin(t * 40) if p.get('flying', 0) else 0
    x += sh
    if p.get('flying', 0):
        fl = 0.04 * s * (1 + 0.3 * math.sin(t * 30))
        _poly(ctx, [(x - 0.02 * s, y), (x + 0.02 * s, y), (x, y + fl + 0.03 * s)], '#f6a23e')
    _poly(ctx, [(x - 0.045 * s, y), (x - 0.025 * s, y - 0.06 * s), (x - 0.025 * s, y - 0.01 * s)], '#e05a5a')
    _poly(ctx, [(x + 0.045 * s, y), (x + 0.025 * s, y - 0.06 * s), (x + 0.025 * s, y - 0.01 * s)], '#e05a5a')
    _poly(ctx, [(x - 0.028 * s, y), (x + 0.028 * s, y), (x + 0.028 * s, y - 0.16 * s), (x, y - 0.23 * s), (x - 0.028 * s, y - 0.16 * s)], '#f1f1f5')
    _ell(ctx, x, y - 0.13 * s, 0.018 * s, 0.018 * s, '#6aaee8')


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


@element('room')
def room(ctx, t, tl, p):
    """Inside a home: a wall (color), a wooden floor from floor= down, a window with the sky (time)."""
    wall, fl = p.get('color', '#f4e3c3'), p.get('floor', 0.78)
    _poly(ctx, [(0, 0), (1, 0), (1, fl), (0, fl)], wall)
    _poly(ctx, [(0, fl), (1, fl), (1, 1), (0, 1)], '#c99a6a')
    for k in range(1, 6):
        ctx.line([(0, fl + k * (1 - fl) / 6), (1, fl + k * (1 - fl) / 6)], '#b5875a', 0.002)
    wx, wy = p.get('window', 0.7), 0.18
    sky_c = {'night': '#2a3a78', 'sunset': '#f2a07a'}.get(p.get('time', 'day'), '#a9d8f2')
    _poly(ctx, [(wx - 0.11, wy), (wx + 0.11, wy), (wx + 0.11, wy + 0.3), (wx - 0.11, wy + 0.3)], '#ffffff')
    _poly(ctx, [(wx - 0.1, wy + 0.02), (wx + 0.1, wy + 0.02), (wx + 0.1, wy + 0.28), (wx - 0.1, wy + 0.28)], sky_c)
    ctx.line([(wx, wy + 0.02), (wx, wy + 0.28)], '#ffffff', 0.006)
    ctx.line([(wx - 0.1, wy + 0.15), (wx + 0.1, wy + 0.15)], '#ffffff', 0.006)


@element('table')
def table(ctx, t, tl, p):
    """A round-cornered table: x, y (floor), s."""
    x, y, s = p.get('x', 0.5), p.get('y', 0.86), p.get('s', 1.0)
    _poly(ctx, [(x - 0.13 * s, y - 0.18 * s), (x + 0.13 * s, y - 0.18 * s), (x + 0.13 * s, y - 0.16 * s), (x - 0.13 * s, y - 0.16 * s)], '#a86f45')
    for dx in (-0.11, 0.11):
        ctx.line([(x + dx * s, y - 0.165 * s), (x + dx * s, y)], '#8a5a3a', 0.012 * s)


@element('cake')
def cake(ctx, t, tl, p):
    """A birthday cake with flickering candles: x, y (bottom), s, candles."""
    x, y, s = p.get('x', 0.5), p.get('y', 0.68), p.get('s', 1.0)
    _poly(ctx, [(x - 0.06 * s, y), (x + 0.06 * s, y), (x + 0.06 * s, y - 0.06 * s), (x - 0.06 * s, y - 0.06 * s)], '#f6c6d8')
    _poly(ctx, [(x - 0.045 * s, y - 0.06 * s), (x + 0.045 * s, y - 0.06 * s), (x + 0.045 * s, y - 0.1 * s), (x - 0.045 * s, y - 0.1 * s)], '#fbe3ec')
    n = int(p.get('candles', 3))
    for k in range(n):
        cx = x + (k - (n - 1) / 2) * 0.022 * s
        ctx.line([(cx, y - 0.1 * s), (cx, y - 0.135 * s)], '#7fb6e8', 0.005 * s)
        fl = 1 + 0.25 * math.sin(t * 13 + k)
        _ell(ctx, cx, y - 0.145 * s, 0.006 * s, 0.011 * s * fl, '#f6c453')


@element('gift')
def gift(ctx, t, tl, p):
    """A wrapped present: x, y (bottom), s, color."""
    x, y, s = p.get('x', 0.5), p.get('y', 0.86), p.get('s', 1.0)
    col = p.get('color', '#7fb6e8')
    _poly(ctx, [(x - 0.035 * s, y), (x + 0.035 * s, y), (x + 0.035 * s, y - 0.06 * s), (x - 0.035 * s, y - 0.06 * s)], col)
    ctx.line([(x, y), (x, y - 0.06 * s)], '#f6d353', 0.008 * s)
    _ell(ctx, x - 0.012 * s, y - 0.066 * s, 0.012 * s, 0.008 * s, '#f6d353')
    _ell(ctx, x + 0.012 * s, y - 0.066 * s, 0.012 * s, 0.008 * s, '#f6d353')


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
