"""Animated effects. draw(ctx, t, tl, st, f): f = progress 0..1 over the effect's time range."""
import math
import numpy as np
from .draw import mix, ease, bezier
from .lettering import draw_text

EFFECTS = {}


def effect(name):
    def deco(fn):
        EFFECTS[name] = fn
        return fn
    return deco


def _rng(seed):
    return np.random.default_rng(seed)


def sheet(ctx, x, y, w, h, ang, col='#f3ebd6', shade='#d8ccb0'):
    c, s, ar = math.cos(ang), math.sin(ang), ctx.ar
    pts = [(x + (dx * c - dy * s) * ar, y + (dx * s + dy * c)) for dx, dy in ((-w, -h), (w, -h), (w, h), (-w, h))]
    ctx.poly(pts, col)
    if ang % 6.28 > 3.14:
        ctx.poly([pts[0], pts[1], pts[2]], shade)


@effect('paper_bird')
def paper_bird(ctx, t, tl, st, f):
    x0, y0 = st.params.get('start', (0.5, 0.6))
    x1, y1 = st.params.get('end', (0.75, 0.15))
    path = bezier([(x0, y0), (x0 + 0.1, y0 - 0.25), (x1 - 0.1, y1 + 0.05), (x1, y1)], 40)
    i = min(len(path) - 1, int(ease(f) * (len(path) - 1)))
    x, y = path[i]
    s = st.params.get('size', 0.035) * (1 - 0.5 * f)
    flap = math.sin(t * 18) * 0.6
    col = '#f6f0e0'
    L = ctx.local(x, y, s)
    L.poly([(-1, 0), (0.9, -0.2), (1.3, 0.1)], col)
    L.poly([(-0.3, 0), (0.4, 0), (0.1, -(0.9 + flap))], mix(col, '#c8c0a8', 0.3))
    L.poly([(-0.3, 0), (0.4, 0), (0.05, 0.6 - flap * 0.5)], mix(col, '#c8c0a8', 0.5))


@effect('dust')
def dust(ctx, t, tl, st, f):
    r = _rng(int(st.params.get('seed', 5)))
    n = int(st.params.get('count', 150))
    col = st.params.get('color', '#fff0c0')
    for i in range(n):
        x, y = r.random(), r.random()
        ph = r.random() * 6.28
        tw = max(0.0, math.sin(t * 3 + ph))
        y = (y + t * 0.01 * (0.5 + r.random())) % 1
        x = x + 0.01 * math.sin(t + ph)
        if tw > 0.2:
            ctx.circle(x, y, 0.0022 * tw, col)
            if tw > 0.85:
                ctx.line([(x - 0.008, y), (x + 0.008, y)], col, 0.001)
                ctx.line([(x, y - 0.008), (x, y + 0.008)], col, 0.001)


@effect('paper_storm')
def paper_storm(ctx, t, tl, st, f):
    r = _rng(17)
    n = int(st.params.get('count', 400))
    for i in range(n):
        birth = r.random() * 0.8
        if f < birth:
            r.random(); r.random(); r.random(); r.random()
            continue
        age = (f - birth) / (1 - birth)
        sx, sy = r.random(), 0.1 + r.random() * 0.6
        vx, vy = (r.random() - 0.3) * 0.6, -0.3 - r.random() * 0.3
        x = sx + vx * age + 0.03 * math.sin(t * 5 + i)
        y = sy + vy * age * age + 0.02 * math.cos(t * 4 + i)
        s = 0.006 + 0.008 * r.random()
        g = 170 + int(60 * r.random())
        sheet(ctx, x % 1.0, y, s, s * 1.3, t * 3 + i, (g, g, g - 10), (g - 50, g - 50, g - 55))


@effect('paper_vortex')
def paper_vortex(ctx, t, tl, st, f):
    cx, cy = st.params.get('center', (0.5, 0.5))
    r = _rng(23)
    n = int(st.params.get('count', 900))
    ar = ctx.ar
    ctx.glow(cx, cy, 0.9, '#0a0c10', 0.7, 1.0)
    ctx.glow(cx, cy, 0.22 * (0.3 + f), '#50b0a0', 0.6 * f, 2.5)
    ctx.glow(cx, cy, 0.05 * (0.3 + f), '#d0fff0', 0.9 * f, 1.5)
    sheets = []
    for i in range(n):
        arm = i % 3
        rad0 = 0.06 + r.random() ** 0.6 * 0.95
        rad = rad0 * (1 - 0.3 * f)
        a = arm * 2.094 + (r.random() - 0.5) * 0.7 + t * 2.2 + rad0 * 6  # three spiral arms that keep their shape
        depth = 0.5 + 0.5 * math.sin(a)
        x = cx + rad * math.cos(a) * ar * 1.4
        y = cy + rad * math.sin(a) * 0.7
        s = (0.005 + 0.012 * r.random()) * (0.5 + depth) * (0.5 + rad0)
        g = int(90 + 140 * depth)
        sheets.append((depth, x, y, s, a + 1.57 + 0.3 * math.sin(t * 5 + i), g))
    for depth, x, y, s, ang, g in sorted(sheets):
        sheet(ctx, x, y, s, s * 1.35, ang, (g, g, g - 8), (g - 45, g - 45, g - 45))


@effect('light_burst')
def light_burst(ctx, t, tl, st, f):
    cx, cy = st.params.get('center', (0.5, 0.5))
    k = ease(f)
    r = _rng(3)
    for i in range(70):
        a = r.random() * 6.28 + t * 0.2
        wdt = 0.01 + r.random() * 0.03
        L = 1.4 * k * (0.5 + r.random())
        ctx.poly([(cx, cy), (cx + L * math.cos(a - wdt), cy + L * math.sin(a - wdt) * 0.6),
                  (cx + L * math.cos(a + wdt), cy + L * math.sin(a + wdt) * 0.6)], mix('#fff2c0', '#ffffff', r.random()))
    ctx.glow(cx, cy, 0.5 + 1.2 * k, '#fff6dc', 0.4 + 0.6 * k, 1.2)
    ctx.tint('#ffffff', max(0.0, (f - 0.6) / 0.4) ** 2)


@effect('flash')
def flash(ctx, t, tl, st, f):
    ctx.tint(st.params.get('color', '#ffffff'), 1 - ease(f))


def crane_points(n, flap, seed=4):
    """Points filling a flying origami crane seen from the side-rear (local units, body ~1 long). flap in -1..1."""
    r = _rng(seed)
    body = [((-0.25, 0.0), (0.2, -0.05), (0.2, 0.05)), ((0.2, -0.05), (0.42, 0.0), (0.2, 0.05)),
            ((0.38, -0.02), (0.7, -0.28), (0.42, 0.02)), ((0.7, -0.28), (0.84, -0.33), (0.73, -0.2)),
            ((-0.22, -0.02), (-0.6, 0.14), (-0.22, 0.03))]
    up, dn = 0.6 + 0.4 * flap, 0.45 - 0.35 * flap
    wings = [((-0.1, -0.02), (0.18, -0.02), (0.5, -0.95 * up)), ((-0.1, -0.02), (0.5, -0.95 * up), (0.05, -0.6 * up)),
             ((-0.08, 0.02), (0.16, 0.02), (0.42, 0.8 * dn)), ((-0.08, 0.02), (0.42, 0.8 * dn), (0.02, 0.5 * dn))]
    allt = body + wings
    areas = np.array([abs((b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])) for a, b, c in allt])
    areas /= areas.sum()
    pts = []
    for i in range(n):
        k = int(r.choice(len(allt), p=areas))
        (x1, y1), (x2, y2), (x3, y3) = allt[k]
        u, v = r.random(), r.random()
        if u + v > 1:
            u, v = 1 - u, 1 - v
        pts.append((x1 + u * (x2 - x1) + v * (x3 - x1), y1 + u * (y2 - y1) + v * (y3 - y1), 1.0 if k >= len(body) else 0.0))
    return pts, allt


@effect('paper_crane')
def paper_crane(ctx, t, tl, st, f):
    n = int(st.params.get('count', 1600))
    r = _rng(9)
    gather = ease(f / 0.45)
    flap = math.sin(t * 2.6)
    cx = 0.2 + 0.6 * ease((f - 0.3) / 0.7) if f > 0.3 else 0.2 + 0.1 * f
    cy = 0.52 - 0.06 * math.sin(f * 3) - 0.04 * flap * (f > 0.4)
    scale = st.params.get('size', 0.55) * (0.6 + 0.4 * f)
    pts, tris = crane_points(n, flap)
    L = ctx.local(cx, cy, scale)
    if gather > 0.6:
        a = (gather - 0.6) / 0.4
        for tri in tris:
            L.poly(tri, mix('#e8d8c0', '#f8f0e0', a))
    starts = r.random((n, 2)) * np.array([1.3, 0.9]) - np.array([0.15, 0.0])
    for i, (px, py, w) in enumerate(pts):
        tx, ty = L.pt(px, py)
        sx, sy = starts[i]
        g = gather
        x = sx + (tx - sx) * g + (1 - g) * 0.05 * math.sin(t * 3 + i)
        y = sy + (ty - sy) * g + (1 - g) * 0.03 * math.cos(t * 2 + i)
        s = 0.004 + 0.006 * (i % 3) / 2
        shade = int(205 + 45 * (1 - w) + 10 * math.sin(i))
        col = (shade, shade - 10, shade - 32)
        sheet(ctx, x, y, s, s * 1.3, t * 2 + i, col, mix(col, '#a08060', 0.4))


@effect('sheet_fall')
def sheet_fall(ctx, t, tl, st, f):
    """A parchment sheet floats down and lands flat at 'land' (x,y) with half-width w; stays after landing."""
    lx, ly = st.params.get('land', (0.62, 0.62))
    w, h = st.params.get('w', 0.2), st.params.get('h', 0.1)
    k = ease(f)
    x = lx + (1 - k) * 0.15 * math.sin(f * 7)
    y = -0.2 + (ly + 0.2) * k
    rock = (1 - k) * 0.5 * math.sin(f * 9)
    persp = 0.35 + 0.65 * k  # flatten as it lands
    c, s = math.cos(rock), math.sin(rock)
    quad = [(-w, -h * persp), (w, -h * persp), (w * 1.12, h * persp), (-w * 1.12, h * persp)]
    pts = [(x + dx * c - dy * s, y + dx * s + dy * c) for dx, dy in quad]
    ctx.poly([(px + 0.006, py + 0.008) for px, py in pts], '#a88a68')
    ctx.poly(pts, '#f2e9d2')
    ctx.poly(pts, None, outline='#d6c8a8', width=0.002)


@effect('confetti')
def confetti(ctx, t, tl, st, f):
    r = _rng(int(st.params.get('seed', 12)))
    n = int(st.params.get('count', 120))
    for i in range(n):
        x0, y0 = r.random(), r.random()
        spd = 0.04 + 0.05 * r.random()
        x = (x0 + 0.02 * math.sin(t * 1.5 + i)) % 1
        y = (y0 + tl * spd) % 1.1 - 0.05
        s = 0.004 + 0.006 * r.random()
        col = ['#f3ebd6', '#e8d8c0', '#d8c8e0', '#f0d8c8'][i % 4]
        sheet(ctx, x, y, s, s * 0.7, t * 2 + i, col, mix(col, '#806040', 0.4))


@effect('quill')
def quill(ctx, t, tl, st, f):
    """A dark fox tail from the top-left writes a flowing ink stroke on the page."""
    pts = bezier([(0.3, 0.55), (0.45, 0.35), (0.55, 0.7), (0.72, 0.5), (0.8, 0.6)], 60)
    k = ease(f)
    n = max(2, int(len(pts) * k))
    ctx.line(pts[:n], '#2a1c14', 0.012)
    tip = pts[n - 1]
    # tail: thick curve from off-screen top-left to the tip
    ctx.curve([(tip[0] - 0.35, tip[1] - 0.7), (tip[0] - 0.22, tip[1] - 0.45), (tip[0] - 0.05, tip[1] - 0.15), tip], '#3a2a24', 0.07)
    ctx.curve([(tip[0] - 0.3, tip[1] - 0.6), (tip[0] - 0.18, tip[1] - 0.36), (tip[0] - 0.06, tip[1] - 0.14)], '#e4772b', 0.04)
    ctx.circle(tip[0] - 0.015, tip[1] - 0.04, 0.03, '#f3ead8')


@effect('handwrite')
def handwrite(ctx, t, tl, st, f):
    """Internal: used by 'text ... handwritten'. Writes text progressively; optional 'pen=tail' draws a fox tail to the tip."""
    x, y = st.pos if isinstance(st.pos, tuple) else (0.5, 0.5)
    size = st.params.get('size', 0.12)
    col = st.params.get('color', '#2a2018')
    tip = draw_text(ctx, st.text, x, y, size, col, ease(f), width=st.params.get('width', 0.07))
    if st.params.get('pen') == 'tail' and tip is not None:
        ax, ay = st.params.get('anchor', (x - 0.25, y + 0.25))
        ctx.curve([(ax, ay), (ax + (tip[0] - ax) * 0.4, ay - 0.12), (tip[0] - 0.03, tip[1] - 0.08), tip], '#e4772b', 0.035)
        ctx.circle(tip[0], tip[1], 0.012, '#2a2018')


@effect('steam')
def steam(ctx, t, tl, st, f):
    """Soft steam wisps rising from (x,y)."""
    x, y = st.params.get('at', st.pos or (0.5, 0.5))
    h = st.params.get('h', 0.25)
    r = _rng(int(st.params.get('seed', 2)))
    for i in range(int(st.params.get('count', 5))):
        ph = r.random() * 6.28
        sway = 0.02 + 0.02 * r.random()
        pts = []
        for k in range(8):
            u = k / 7
            pts.append((x + (r.random() - 0.5) * 0.02 + sway * math.sin(t * 1.5 + ph + u * 4) * ctx.ar * 3, y - u * h - 0.02 * i))
        ctx.soft_shape(lambda d, c, pts=pts, i=i: d.line(c.pts(pts), fill=255, width=int(c.H * (0.012 + 0.004 * i))), '#ffffff', 0.012, 0.35 * (0.6 + 0.4 * math.sin(t * 2 + ph)))


@effect('cup_knock')
def cup_knock(ctx, t, tl, st, f):
    """The cup tips over to the right and coffee spills: a splash, then a spreading puddle."""
    from .elements import draw_cup
    x, y, r = st.params.get('at', st.pos or (0.5, 0.6))[0], st.params.get('at', st.pos or (0.5, 0.6))[1], st.params.get('r', 0.06)
    tip = 1.5 * ease(f / 0.25)
    fill = max(0.0, 1 - ease((f - 0.1) / 0.3))
    if f > 0.15:
        k = ease((f - 0.15) / 0.6)
        L = ctx.local(x, y, r)
        L.ellipse(2.2 + 1.5 * k, 1.75, (0.5 + 3.5 * k), (0.15 + 0.9 * k), '#4a2a18')
        L.ellipse(2.2 + 1.5 * k, 1.72, (0.3 + 2.8 * k), (0.1 + 0.55 * k), '#6b3f24')
    draw_cup(ctx, x, y, r, tip, fill)
    if 0.12 < f < 0.6:
        g = (f - 0.12) / 0.48
        rr = _rng(31)
        L = ctx.local(x, y, r)
        for i in range(40):
            a = -1.2 + rr.random() * 1.6
            v = 2 + 4 * rr.random()
            px = 1.8 + math.cos(a) * v * g
            py = 1.2 + math.sin(a) * v * g + 9 * g * g
            if py < 1.75:
                L.circle(px, py, 0.08 + 0.08 * rr.random(), '#5a3220')


_FONTS = {}


@effect('font_text')
def font_text(ctx, t, tl, st, f):
    """Internal: used by 'text ... font'. Any letters (Latin, Cyrillic, digits, punctuation) in the open Caveat font (OFL),
    revealed left to right like a pen; centred at x,y; size = letter height as a fraction of the frame."""
    import os
    from PIL import Image, ImageDraw, ImageFont
    x, y = st.pos if isinstance(st.pos, tuple) else (0.5, 0.5)
    px = max(8, int(st.params.get('size', 0.12) * ctx.H * 1.25))
    key = px
    if key not in _FONTS:
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'fonts', 'Caveat.ttf')
        fnt = ImageFont.truetype(path, px)
        try:
            fnt.set_variation_by_axes([600])
        except Exception:
            pass
        _FONTS[key] = fnt
    fnt = _FONTS[key]
    l, tp, r, b = fnt.getbbox(st.text)
    w, h = r - l, b - tp
    layer = Image.new('RGBA', (w + 8, h + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.text((4 - l + 2, 4 - tp + 2), st.text, font=fnt, fill=(0, 0, 0, 90))
    d.text((4 - l, 4 - tp), st.text, font=fnt, fill=st.params.get('color', '#2a2018'))
    reveal = int(layer.width * min(1.0, ease(f) * 1.05))
    if reveal <= 0:
        return
    layer = layer.crop((0, 0, reveal, layer.height))
    ctx.img.alpha_composite(layer, (int(x * ctx.W - (w + 8) / 2), int(y * ctx.H - (h + 8) / 2)))
