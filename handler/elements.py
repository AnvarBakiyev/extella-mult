"""Background elements and props. Each: draw(ctx, t, tl, p) where t = film time, tl = time inside scene, p = params."""
import math
import numpy as np
from scipy.ndimage import gaussian_filter
from .draw import fbm, rgb, mix, ease

ELEMENTS = {}


def element(name):
    def deco(fn):
        ELEMENTS[name] = fn
        return fn
    return deco


def _rng(seed):
    return np.random.default_rng(seed)


# ------------------------------------------------------------------ skies
@element('night_sky')
def night_sky(ctx, t, tl, p):
    ctx.gradient([(0, '#120c2e'), (0.45, '#2a1d5e'), (1.0, '#5a4a8a')])
    n = fbm(ctx.W, ctx.H, 11, (40, 120), (1, 1))
    ctx.layer((n - 0.4).clip(0, 1) * 0.25, '#6a4fb0')


@element('dawn_sky')
def dawn_sky(ctx, t, tl, p):
    ctx.gradient([(0, '#7fb2e6'), (0.35, '#d6c0e8'), (0.6, '#f6c9a4'), (1.0, '#ffe6b0')])
    n = fbm(ctx.W, ctx.H, 12, (40, 120), (1, 1))
    ctx.layer((n - 0.45).clip(0, 1) * 0.3, '#ffd5c0')


@element('morning_sky')
def morning_sky(ctx, t, tl, p):
    ctx.gradient([(0, '#9ccbf0'), (0.6, '#dfe9f0'), (1.0, '#fff2d6')])


@element('stars')
def stars(ctx, t, tl, p):
    r = _rng(int(p.get('seed', 3)))
    n = int(p.get('count', 260))
    xs, ys, ph = r.random(n), r.random(n) * 0.75, r.random(n) * 6.28
    for i in range(n):
        tw = 0.5 + 0.5 * math.sin(t * 2.3 + ph[i])
        s = (0.0012 + 0.0025 * r.random()) * (0.6 + 0.4 * tw)
        col = mix('#ffffff', '#ffe9b0', r.random())
        ctx.circle(xs[i], ys[i], s, col)


@element('moon')
def moon(ctx, t, tl, p):
    x, y, r = p.get('x', 0.14), p.get('y', 0.2), p.get('r', 0.055)
    ctx.glow(x, y, r * 5, '#cfc2ff', 0.35, 2.5)
    ctx.glow(x, y, r * 1.6, '#fff6dc', 0.8, 1.5)
    ctx.circle(x, y, r, '#fbf4d8')
    ctx.circle(x - r * 0.3, y - r * 0.2, r * 0.22, '#ece4c4')
    ctx.circle(x + r * 0.35, y + r * 0.3, r * 0.15, '#ece4c4')


@element('sun')
def sun(ctx, t, tl, p):
    x, y, r = p.get('x', 0.7), p.get('y', 0.6), p.get('r', 0.05)
    rise = p.get('rise', 0.0)
    y = y - rise * ease(tl / max(p.get('over', 6.0), 0.1))
    ctx.glow(x, y, r * 9, '#ffd9a0', 0.55, 1.6)
    ctx.glow(x, y, r * 3, '#fff3c8', 0.9, 1.2)
    ctx.circle(x, y, r, '#fffbe8')


@element('nebula')
def nebula(ctx, t, tl, p):
    n = fbm(ctx.W, ctx.H, 21, (60, 160), (1, 1))
    ctx.layer((n - 0.45).clip(0, 1) * 0.35, p.get('color', '#8a5fc0'))


# ------------------------------------------------------------------ clouds
PALETTES = {
    'night': ['#2b2256', '#3d3270', '#56488c', '#7a6aa8'],
    'dawn': ['#d8a0b8', '#efbfc0', '#fbd9c2', '#fff0dc'],
    'gold': ['#e8a890', '#f5c8a8', '#fde0c0', '#fff5e4'],
}


@element('cloud_sea')
def cloud_sea(ctx, t, tl, p):
    pal = PALETTES[p.get('palette', 'night')]
    base = p.get('top', 0.55)
    speed = p.get('speed', 0.004)
    yy = np.linspace(0, 1, ctx.H, dtype=np.float32)[:, None]
    for k, col in enumerate(pal):
        y0 = base + k * 0.10
        n = fbm(ctx.W * 2, ctx.H, 100 + k + int(p.get('seed', 0)), (30, 90, 250), (1, 0.7, 0.5))
        off = int((t * speed * (k + 1) * ctx.W) % ctx.W)
        n = n[:, off:off + ctx.W]
        prof = np.clip((yy - y0 + 0.05) / 0.12, 0, 1)
        m = gaussian_filter(np.clip((n * prof - 0.36) * 7, 0, 1), ctx.H * 0.003)
        ctx.layer(m, col)
        rim = np.clip((n * prof - 0.48) * 9, 0, 1)
        ctx.layer(rim * 0.6, mix(col, '#ffffff', 0.4))


@element('mist')
def mist(ctx, t, tl, p):
    n = fbm(ctx.W * 2, ctx.H, 77, (50, 150), (1, 1))
    off = int((t * 0.01 * ctx.W) % ctx.W)
    n = n[:, off:off + ctx.W]
    ctx.layer((n - 0.4).clip(0, 1) * p.get('strength', 0.35), p.get('color', '#d8c8e8'))


# ------------------------------------------------------------------ island / tower
@element('island')
def island(ctx, t, tl, p):
    """Rocky islet in the cloud sea with pines; (x,y) = centre of the rock top, w = half-width in height units."""
    x, y, w = p.get('x', 0.72), p.get('y', 0.66), p.get('w', 0.5)
    L = ctx.local(x, y, w)
    L.poly([(-1, 0.05), (-0.75, -0.06), (-0.3, -0.1), (0.2, -0.09), (0.7, -0.05), (1, 0.06), (0.75, 0.3), (0.2, 0.42), (-0.5, 0.35)], '#1e1a33')
    L.poly([(-0.85, 0.02), (-0.45, -0.07), (0, -0.07), (0.5, -0.05), (0.8, 0.03), (0.3, 0.12), (-0.5, 0.1)], '#2c2748')
    pine(ctx, *L.pt(-0.6, -0.05), w * 0.42, lean=-0.35)
    pine(ctx, *L.pt(0.95, 0.02), w * 0.2, lean=0.45)
    pine(ctx, *L.pt(-0.15, -0.04), w * 0.16, lean=0.1)


def pine(ctx, x, y, h, lean=0.0):
    """Wind-bent pine: trunk with layered boughs; (x,y) = root, h = height."""
    L = ctx.local(x, y, h)
    L.line([(0, 0), (lean * 0.25, -0.55), (lean * 0.5, -1)], '#1a1224', 0.06)
    for i in range(4):
        f = i / 4
        cx, cy = lean * 0.5 * (0.5 + f * 0.5), -(0.45 + 0.5 * f)
        span = 0.5 - 0.33 * f
        L.ellipse(cx, cy, span, 0.08, '#223324')
        L.ellipse(cx - span * 0.6, cy + 0.02, span * 0.45, 0.06, '#1b2a1d')


@element('tower')
def tower(ctx, t, tl, p):
    """Old stone tower with a green onion dome. (x,y) = base centre, h = height; drawn in a Local frame."""
    x, y, h = p.get('x', 0.74), p.get('y', 0.65), p.get('h', 0.5)
    L = ctx.local(x, y, h)
    w = p.get('w', 0.14)  # half-width as a fraction of height
    stone, dark, shadow = '#7a7494', '#4a4462', '#2e2a40'
    L.poly([(-w, 0), (w, 0), (w * 0.85, -1), (-w * 0.85, -1)], stone)
    L.poly([(w * 0.25, 0), (w, 0), (w * 0.85, -1), (w * 0.25, -1)], dark)
    for i in range(6):
        yy = -0.1 - i * 0.14
        L.poly([(-w, yy), (w, yy), (w, yy + 0.012), (-w, yy + 0.012)], shadow)
        lit = i in (1, 3) and (0.5 + 0.5 * math.sin(t * 7 + i)) > 0.3
        L.poly([(-w * 0.3, yy - 0.07), (w * 0.1, yy - 0.07), (w * 0.1, yy), (-w * 0.3, yy)], '#ffd27a' if lit else '#1a1428')
        if lit:
            L.glow(-w * 0.1, yy - 0.035, 0.12, '#ffd27a', 0.5, 2)
    for i in range(10):
        r = _rng(50 + i)
        L.ellipse(-w * 0.7 + r.random() * w * 1.2, -r.random() * 0.75, w * 0.22, 0.03, '#27402c')
    # gallery, dome and spire
    L.poly([(-w * 1.25, -1.0), (w * 1.25, -1.0), (w * 1.25, -1.06), (-w * 1.25, -1.06)], shadow)
    L.poly([(-w * 1.1, -1.06), (w * 1.1, -1.06), (w * 1.1, -1.12), (-w * 1.1, -1.12)], dark)
    for i in range(5):
        L.poly([(-w * 1.0 + i * w * 0.5, -1.12), (-w * 0.85 + i * w * 0.5, -1.12), (-w * 0.85 + i * w * 0.5, -1.2), (-w * 1.0 + i * w * 0.5, -1.2)], '#1a1428')
    L.poly([(-w * 1.2, -1.2), (w * 1.2, -1.2), (w * 1.2, -1.24), (-w * 1.2, -1.24)], shadow)
    L.curve([(-w * 1.2, -1.24), (-w * 1.35, -1.45), (0, -1.6), (w * 1.35, -1.45), (w * 1.2, -1.24)], '#3f8a5a', 0.02)
    L.poly([(-w * 1.2, -1.24), (-w * 1.3, -1.4), (-w * 0.9, -1.55), (0, -1.6), (w * 0.9, -1.55), (w * 1.3, -1.4), (w * 1.2, -1.24)], '#3f8a5a')
    L.poly([(-w * 0.6, -1.26), (-w * 0.9, -1.4), (-w * 0.5, -1.53), (-w * 0.1, -1.56), (-w * 0.1, -1.26)], '#5fae74')
    L.line([(0, -1.6), (0, -1.72)], '#c0b89a', 0.012)
    L.circle(0, -1.73, 0.012, '#e8d8a0')


@element('grass')
def grass(ctx, t, tl, p):
    r = _rng(9)
    x0, x1 = p.get('x0', 0.0), p.get('x1', 0.3)
    col = p.get('color', '#1b1530')
    for i in range(70):
        bx = x0 + r.random() * (x1 - x0)
        by = 1.0
        h = 0.12 + r.random() * 0.18 * (1 - (bx - x0) / (x1 - x0 + 1e-6))
        sway = 0.02 * math.sin(t * 1.5 + i)
        ctx.curve([(bx, by), (bx + 0.01, by - h * 0.6), (bx + 0.04 + sway, by - h)], col, 0.004)
    ctx.poly([(x0, 1.0), (x1 + 0.1, 1.0), (x1 + 0.05, 0.95), (x0, 0.9)], col)


# ------------------------------------------------------------------ library
BOOK_COLS = ['#5a3b2e', '#3e4a6a', '#6a4a3a', '#48553c', '#7a4a4a', '#3a3a52', '#8a6a3a', '#4a3a5a', '#6a5a4a', '#3a4a4a']


def shelf_wall(ctx, x0, x1, y0, y1, rows, seed, bright=1.0, grey=False, t=0.0):
    """Wall of shelves with books between (x0,x1) and (y0,y1)."""
    r = _rng(seed)
    wood = mix('#2a1c14', '#000000', 1 - bright) if not grey else '#2a2a2e'
    ctx.rect(x0, y0, x1, y1, wood)
    rh = (y1 - y0) / rows
    for row in range(rows):
        ry = y0 + row * rh
        x = x0 + 0.002
        while x < x1 - 0.004:
            bw = 0.004 + r.random() * 0.006
            bh = rh * (0.55 + r.random() * 0.35)
            col = BOOK_COLS[int(r.random() * len(BOOK_COLS))]
            if grey:
                g = 70 + int(r.random() * 80)
                col = (g, g, g + 6)
            col = mix(col, '#000000', 1 - bright)
            ctx.rect(x, ry + rh - bh, x + bw, ry + rh - rh * 0.06, col)
            x += bw + 0.0008
        ctx.rect(x0, ry + rh - rh * 0.07, x1, ry + rh, mix('#4a3222', '#000000', 1 - bright) if not grey else '#3a3a40')


@element('library')
def library(ctx, t, tl, p):
    bright = p.get('bright', 1.0)
    grey = bool(p.get('grey', 0))
    floor_y = p.get('floor', 0.74)
    ctx.rect(0, 0, 1, 1, '#07060c')
    # back wall of shelves
    shelf_wall(ctx, 0.0, 1.0, 0.05, floor_y, int(p.get('rows', 9)), 5, bright * 0.75, grey, t)
    # side pillars
    for px in (0.26, 0.56, 0.86):
        ctx.rect(px - 0.012, 0.0, px + 0.012, floor_y, '#1a110c' if not grey else '#222226')
    # floor
    ctx.rect(0, floor_y, 1, 1, '#2a2420' if not grey else '#2a2a2c')
    for i in range(14):
        yy = floor_y + (i / 14) ** 1.4 * (1 - floor_y)
        ctx.rect(0, yy, 1, yy + 0.002, '#3a332c' if not grey else '#3a3a3e')
    for i in range(16):
        xx = i / 15
        ctx.poly([(0.5 + (xx - 0.5) * 0.9, floor_y), (0.5 + (xx - 0.5) * 1.6, 1.0),
                  (0.5 + (xx - 0.5) * 1.6 + 0.002, 1.0), (0.5 + (xx - 0.5) * 0.9 + 0.002, floor_y)], '#3a332c' if not grey else '#3a3a3e')
    # dark foreground pillar left (as in the reference)
    if p.get('pillar', 1):
        ctx.poly([(0, 0), (0.12, 0), (0.14, 1), (0, 1)], '#0a0810')
    ctx.vignette(0.9)


@element('moonbeam')
def moonbeam(ctx, t, tl, p):
    x_top, x_bot = p.get('x_top', 0.72), p.get('x_bot', 0.52)
    w = p.get('w', 0.09)
    ctx.soft_shape(lambda d, c: d.polygon(c.pts([(x_top - w * 0.4, -0.1), (x_top + w * 0.4, -0.1), (x_bot + w * 1.6, 0.78), (x_bot - w * 1.6, 0.78)]), fill=255),
                   '#c8c0ff', 0.02, p.get('strength', 0.22))
    yy, xx = ctx.grid()
    pool = np.clip(1 - np.hypot((xx / ctx.W - x_bot) * 3.5, (yy / ctx.H - 0.77) * 14), 0, 1) ** 1.5
    ctx.layer(pool * 0.45, '#d8d0ff')
    # motes
    r = _rng(31)
    for i in range(60):
        f = (r.random() + t * 0.02 * (0.5 + r.random())) % 1
        x = x_top + (x_bot - x_top) * f + (r.random() - 0.5) * w * 1.2
        y = -0.05 + 0.85 * f
        ctx.circle(x, y, 0.0015, '#ffffff')


@element('floor_light')
def floor_light(ctx, t, tl, p):
    ctx.glow(p.get('x', 0.5), p.get('y', 0.8), p.get('r', 0.2), p.get('color', '#ffe0a0'), p.get('strength', 0.5), 2)


@element('pedestal_book')
def pedestal_book(ctx, t, tl, p):
    x, y = p.get('x', 0.5), p.get('y', 0.72)
    w = p.get('w', 0.26)
    # pedestal
    ctx.poly([(x - w * 0.8, y + 0.04), (x + w * 0.8, y + 0.04), (x + w * 0.95, y + 0.26), (x - w * 0.95, y + 0.26)], '#2a2436')
    ctx.rect(x - w * 0.85, y + 0.02, x + w * 0.85, y + 0.06, '#3e3850')
    ctx.rect(x - w * 0.9, y + 0.22, x + w * 0.9, y + 0.26, '#3e3850')
    ctx.glow(x, y + 0.14, 0.12, '#a0c8ff', 0.25, 2)
    # open book
    cream, edge = '#f1e7cf', '#d8ccae'
    ctx.poly([(x - w, y - 0.02), (x - 0.005, y + 0.01), (x - 0.005, y + 0.03), (x - w, y + 0.0)], edge)
    ctx.poly([(x + w, y - 0.02), (x + 0.005, y + 0.01), (x + 0.005, y + 0.03), (x + w, y + 0.0)], edge)
    ctx.poly([(x - w, y - 0.08), (x - 0.005, y - 0.04), (x - 0.005, y + 0.01), (x - w, y - 0.02)], cream)
    ctx.poly([(x + w, y - 0.08), (x + 0.005, y - 0.04), (x + 0.005, y + 0.01), (x + w, y - 0.02)], cream)
    ctx.line([(x, y - 0.04), (x, y + 0.01)], '#c8b890', 0.002)
    # bookmark ribbon
    ctx.line([(x + 0.01, y + 0.02), (x + 0.015, y + 0.12), (x + 0.005, y + 0.2)], '#b0303a', 0.004)
    # faint text lines
    for i in range(5):
        for side in (-1, 1):
            ctx.line([(x + side * w * 0.2, y - 0.065 + i * 0.012), (x + side * w * 0.8, y - 0.065 + i * 0.012)], '#d0c4a8', 0.001)


@element('shelf_closeup')
def shelf_closeup(ctx, t, tl, p):
    ctx.rect(0, 0, 1, 1, '#0c0a10')
    r = _rng(8)
    cols = ['#3a5e8a', '#8a3a3a', '#3a7a5a', '#b08a3a', '#5a3a8a', '#c0c0c0', '#8a5a3a', '#2a4a7a', '#d0a060', '#6a8ab0']
    # shelf plane in perspective: left big, right small
    drift = tl * 0.01
    x = -0.05 + (drift % 0.02)
    i = 0
    while x < 1.1:
        f = x  # perspective factor
        bw = 0.03 * (1 - 0.6 * f) + r.random() * 0.012
        top = 0.12 + 0.45 * f + r.random() * 0.1
        bottom = 0.95 - 0.35 * f
        top = min(top, bottom - 0.05)
        col = cols[int(r.random() * len(cols))]
        col = mix(col, '#000000', 0.25 + 0.3 * f)
        ctx.poly([(x, top), (x + bw, top + 0.01), (x + bw, bottom), (x, bottom)], col)
        ctx.rect(x, top, x + bw * 0.3, bottom, mix(col, '#ffffff', 0.15))
        x += bw + 0.002
        i += 1
    ctx.poly([(0, 0.95), (1, 0.6), (1, 0.66), (0, 1.0)], '#2a1c14')
    ctx.vignette(0.6)


@element('lantern')
def lantern(ctx, t, tl, p):
    x, y, r = p.get('x', 0.42), p.get('y', 0.7), p.get('r', 0.15)
    fl = 0.9 + 0.1 * math.sin(t * 9) * math.sin(t * 13)
    L = ctx.local(x, y, r)
    L.glow(0, 0, 4, '#ffb060', 0.45 * fl, 2.2)
    L.ellipse(0, 1.1, 0.55, 0.12, '#3a2a1a')
    L.circle(0, 0, 1.0, '#ffc878')
    L.circle(0, 0, 0.97, '#ffd58e')
    for i in range(7):
        yy = -1 + 2 * (i + 0.5) / 7
        dx = math.sqrt(max(0, 1 - yy * yy))
        L.line([(-dx, yy), (dx, yy)], '#e8a858', 0.02)
    L.line([(0, -1), (0, 1)], '#d09050', 0.025)
    L.glow(0, 0, 0.6, '#ffffff', 0.5 * fl, 1.5)
    L.poly([(0, -0.35 * fl), (0.12, 0.05), (0, 0.2), (-0.12, 0.05)], '#ffe8a0')
    L.poly([(0, -0.15 * fl), (0.05, 0.08), (0, 0.16), (-0.05, 0.08)], '#ffb040')
    L.poly([(-0.1, -1.12), (0.1, -1.12), (0.1, -0.95), (-0.1, -0.95)], '#3a2a1a')


@element('parchment')
def parchment(ctx, t, tl, p):
    ctx.gradient([(0, '#efe3c6'), (1, '#e0d0a8')])
    n = fbm(ctx.W, ctx.H, 44, (6, 30, 90), (0.5, 1, 1))
    ctx.layer((n - 0.4).clip(0, 1) * 0.5, '#f8f0da')
    ctx.layer((0.55 - n).clip(0, 1) * 0.5, '#c8b488')
    ctx.vignette(0.35)


# ------------------------------------------------------------------ rooftop
@element('rooftop')
def rooftop(ctx, t, tl, p):
    """Flat stone roof above clouds with a parapet; view=wide|close."""
    view = p.get('view', 'wide')
    if view == 'wide':
        horizon = p.get('horizon', 0.64)
        ctx.rect(0, horizon, 1, 1, '#c9a98a')
        # tile lines in perspective
        for i in range(18):
            yy = horizon + (i / 18) ** 1.6 * (1 - horizon)
            ctx.rect(0, yy, 1, yy + 0.002, '#a8886c')
        for i in range(22):
            xx = i / 21
            ctx.poly([(0.5 + (xx - 0.5) * 0.9, horizon), (0.5 + (xx - 0.5) * 2.0, 1.0),
                      (0.5 + (xx - 0.5) * 2.0 + 0.002, 1.0), (0.5 + (xx - 0.5) * 0.9 + 0.002, horizon)], '#a8886c')
        # parapet
        ctx.rect(0, horizon - 0.045, 1, horizon, '#b9977a')
        ctx.rect(0, horizon - 0.055, 1, horizon - 0.045, '#dcc0a4')
        for i in range(40):
            ctx.rect(i / 40, horizon - 0.045, i / 40 + 0.0015, horizon, '#9a7a60')
        # warm light wash
        yy, xx = ctx.grid()
        ctx.layer(np.clip((yy / ctx.H - horizon) * 2, 0, 1) * 0.18, '#ffd9a8')
        # wall at left edge with ivy
        ctx.poly([(0, 0), (0.05, 0), (0.07, 1), (0, 1)], '#8a6a56')
        for i in range(25):
            r = _rng(300 + i)
            ctx.ellipse(0.0 + r.random() * 0.06, r.random(), 0.02, 0.012, '#4a7a4a')
    else:
        # close view: wooden floor planks under warm light, dark wall far back
        ctx.rect(0, 0, 1, 1, '#6a5244')
        ctx.rect(0, 0.0, 1, 0.26, '#d4b89c')
        ctx.rect(0, 0.26, 1, 0.33, '#8f7560')
        for i in range(60):
            ctx.rect(i / 60, 0.26, i / 60 + 0.004, 0.33, '#6e5a48')
        ctx.rect(0, 0.33, 1, 1, '#d2a77e')
        for i in range(10):
            yy = 0.33 + i * 0.07
            ctx.rect(0, yy, 1, yy + 0.003, '#b88a62')
        for i in range(12):
            ctx.rect(i / 12 + (0.04 * (i % 2)), 0.33, i / 12 + (0.04 * (i % 2)) + 0.003, 1, '#b88a62')
        ctx.layer(np.full((ctx.H, ctx.W), 0.12, np.float32), '#ffe8c0')
        ctx.vignette(0.3)


# ------------------------------------------------------------------ coffee shop (added for film 2)
@element('cafe')
def cafe(ctx, t, tl, p):
    """Cosy cafe interior: warm wall, window with morning light, shelves with jars, wooden table in front."""
    ctx.rect(0, 0, 1, 1, '#c9a885')
    wx0, wx1, wy0, wy1 = 0.56, 0.9, 0.08, 0.5
    ctx.rect(wx0 - 0.015, wy0 - 0.03, wx1 + 0.015, wy1 + 0.03, '#6b4a34')
    ctx.rect(wx0, wy0, wx1, wy1, '#cfe6f6')
    ctx.rect(wx0, wy0 + 0.25, wx1, wy1, '#e6efe0')
    for i in range(6):
        ctx.ellipse(wx0 + 0.05 + i * 0.06, wy0 + 0.1 + 0.03 * (i % 2), 0.05, 0.02, '#f4f8fc')
    ctx.rect((wx0 + wx1) / 2 - 0.006, wy0, (wx0 + wx1) / 2 + 0.006, wy1, '#6b4a34')
    ctx.rect(wx0, (wy0 + wy1) / 2 - 0.01, wx1, (wy0 + wy1) / 2 + 0.01, '#6b4a34')
    for row in range(2):
        sy = 0.22 + row * 0.18
        ctx.rect(0.08, sy, 0.42, sy + 0.015, '#6b4a34')
        r = _rng(400 + row)
        x = 0.1
        while x < 0.4:
            jw, jh = 0.03 + r.random() * 0.02, 0.07 + r.random() * 0.05
            col = ['#b57a4a', '#d8c08a', '#8a6a4a', '#e0a070', '#6a8a7a'][int(r.random() * 5)]
            ctx.rect(x, sy - jh, x + jw, sy, col)
            ctx.rect(x + jw * 0.2, sy - jh - 0.01, x + jw * 0.8, sy - jh, '#4a3a2a')
            x += jw + 0.015
    ty = p.get('table', 0.62)
    ctx.rect(0, ty, 1, 1, '#8a5a3a')
    ctx.rect(0, ty, 1, ty + 0.02, '#a87048')
    for i in range(6):
        ctx.rect(0, ty + 0.1 + i * 0.07, 1, ty + 0.103 + i * 0.07, '#7a4c30')
    yy, xx = ctx.grid()
    beam = np.clip(1 - np.abs((xx / ctx.W - 0.73) - (yy / ctx.H - 0.3) * 0.5) * 2.5, 0, 1)
    ctx.layer(beam * 0.18, '#fff0c0')
    ctx.vignette(0.35)


def draw_cup(ctx, x, y, r, tip=0.0, fill=1.0, color='#f4efe6'):
    """Coffee cup; (x,y) = centre of the rim, r = rim radius; tip = lean angle (radians, positive = falls right)."""
    L = ctx.local(x, y, r)
    c, s = math.cos(tip), math.sin(tip)

    def R(dx, dy):  # rotate about the base-right corner when tipping
        px, py = dx - 0.8 * (tip > 0), dy - 1.6
        return (0.8 * (tip > 0) + px * c - py * s, 1.6 + px * s + py * c)
    body = [R(-1, 0), R(1, 0), R(0.8, 1.6), R(-0.8, 1.6)]
    inner = '#d9d2c6'
    L.poly(body, color)
    hx, hy = R(1.3, 0.75)
    L.circle(hx, hy, 0.45, color)
    L.circle(hx, hy, 0.22, '#8a5a3a')
    L.poly(body, color)
    L.ellipse(*R(0, 0), 1.0, 0.3, inner, angle=tip)
    if fill > 0:
        L.ellipse(*R(0, 0.04), 0.86 * fill ** 0.3, 0.24, '#4a2a18', angle=tip)
    L.poly([R(-0.8, 1.45), R(0.8, 1.45), R(0.8, 1.6), R(-0.8, 1.6)], '#e0d8cc')


@element('cup')
def cup(ctx, t, tl, p):
    draw_cup(ctx, p.get('x', 0.5), p.get('y', 0.6), p.get('r', 0.06), p.get('tip', 0.0), p.get('fill', 1.0), p.get('color', '#f4efe6'))


@element('saucer')
def saucer(ctx, t, tl, p):
    x, y, r = p.get('x', 0.5), p.get('y', 0.7), p.get('r', 0.1)
    L = ctx.local(x, y, r)
    L.ellipse(0, 0, 1.0, 0.25, '#e8e2d6')
    L.ellipse(0, -0.03, 0.6, 0.15, '#d9d2c6')


@element('plant')
def plant(ctx, t, tl, p):
    x, y, s = p.get('x', 0.9), p.get('y', 0.62), p.get('s', 0.12)
    L = ctx.local(x, y, s)
    L.poly([(-0.4, 0), (0.4, 0), (0.3, 0.5), (-0.3, 0.5)], '#b86a46')
    for i in range(7):
        a = -1.9 + i * 0.6
        L.curve([(0, 0), (math.cos(a) * 0.6, -0.5), (math.cos(a) * 1.1, -0.9 - 0.15 * (i % 2))], '#4f8a4a', 0.1)

