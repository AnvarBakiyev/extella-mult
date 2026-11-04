"""Felt props drawn with Pillow primitives. Each function takes a Layer and presses one or more felt pieces into it.
Coordinates: x 0..1 of width, y 0..1 of height (y = ground line / base), s = size, 1 is a typical mid-layer size."""
import math

import numpy as np

from plates import AR, shade, mixc


def ridge_fn(seed, base, amp, freqs=(2.1, 5.3, 11.7), weights=(1, 0.45, 0.18), sharp=0.0):
    r = np.random.default_rng(seed)
    ph = r.random(len(freqs)) * 6.28

    def f(x):
        v = sum(w * math.sin(x * fq * 3.1416 + p) for fq, w, p in zip(freqs, weights, ph)) / sum(weights)
        if sharp:
            v = (1 - sharp) * v + sharp * (1 - 2 * abs(math.sin(x * freqs[0] * 1.6 + ph[0])))
        return base - amp * (0.5 + 0.5 * v)
    return f


def hills(L, base, amp, col, seed=1, depth=1.0, freqs=(1.3, 3.1, 7.0)):
    f = ridge_fn(seed, base, amp, freqs)
    with L.piece(depth, kind='ground') as d:
        d.ridge(f, col)
    return f


def mountains(L, base, top, seed=2, col='#8b97c7', snow='#f4f4fa', count=None, snowline=0.42, sharp=True):
    """A range of rounded-peak mountains, each peak its own piece, with snow caps."""
    r = np.random.default_rng(seed)
    x = -0.12 + r.random() * 0.05
    peaks = []
    while x < 1.08:
        w = 0.24 + 0.16 * r.random()
        h = (base - top) * (0.55 + 0.45 * r.random())
        peaks.append((x, w, h))
        x += w * (0.5 + 0.2 * r.random())
    peaks.sort(key=lambda p: -p[2])  # tall ones behind
    for i, (x, w, h) in enumerate(peaks):
        c = shade(col, 0.92 + 0.14 * r.random())
        cx = x + w / 2
        skew = (r.random() - 0.5) * 0.08 * w
        n = 26
        pts = []
        for k in range(n + 1):
            u = k / n
            # a soft peak: steep sides, rounded top, little jags
            prof = (1 - abs(2 * u - 1)) ** (1.25 if sharp else 0.8)
            jag = 0.035 * math.sin(u * 23 + i) * prof
            pts.append((x + w * u + skew * prof, base - h * (prof + jag)))
        with L.piece(0.9) as d:
            d.poly(pts + [(x + w, base + 0.4), (x, base + 0.4)], c)
            # shaded flank on the right
            sh = [(cx + skew, base - h)] + [(px, py) for px, py in pts[n // 2:]] + [(cx + w * 0.05, base + 0.4)]
            d.poly(sh, shade(c, 0.86))
        if snow:
            sn = []
            lim = base - h * (1 - snowline)
            for px, py in pts:
                if py < lim:
                    sn.append((px, py))
            if len(sn) > 2:
                lo = [(sn[-1][0], lim)]
                # a wavy snow line
                m = 8
                for k in range(m + 1):
                    u = 1 - k / m
                    xx = sn[0][0] + (sn[-1][0] - sn[0][0]) * u
                    lo.append((xx, lim + 0.018 * h * (1 + math.sin(k * 2.3 + i)) - 0.02 * h))
                with L.piece(0.6) as d:
                    d.poly(sn + lo, snow)
    return peaks


def cloud_puff(d, x, y, s, c):
    for dx, dy, rr in ((-0.1, 0.03, 0.06), (-0.045, -0.012, 0.08), (0.035, -0.03, 0.095), (0.105, 0.015, 0.068), (0.0, 0.035, 0.065)):
        d.ell(x + dx * s * 0.62, y + dy * s, rr * s, rr * s * 0.88, c)


# ---------------------------------------------------------------- trees and plants

def round_tree(L, x, y, s=1.0, leaf='leaf', leaf2='leaf2', trunk='#8a5a3a', rng=None):
    lean = (rng.random() - 0.5) * 0.01 if rng is not None else 0
    with L.piece(0.8, kind='foliage') as d:
        d.poly([(x - 0.009 * s, y), (x + 0.009 * s, y), (x + 0.005 * s + lean, y - 0.2 * s), (x - 0.005 * s + lean, y - 0.2 * s)], trunk)
        d.line([(x + lean * 0.5, y - 0.12 * s), (x + 0.03 * s, y - 0.17 * s)], trunk, 0.006 * s)
    if L.look.season == 'winter' and leaf == 'leaf':
        with L.piece(0.6, kind='foliage') as d:
            for a in (-0.6, -0.2, 0.25, 0.6):
                d.line([(x + lean, y - 0.18 * s), (x + lean + a * 0.06 * s, y - (0.29 + 0.03 * abs(a)) * s)], trunk, 0.005 * s)
            for a in (-0.6, 0.6):
                d.circ(x + lean + a * 0.06 * s, y - 0.3 * s, 0.006 * s, '#ffffff')
        return
    with L.piece(1.0, kind='foliage') as d:
        for dx, dy, r, c in ((-0.04, -0.22, 0.075, leaf), (0.04, -0.235, 0.075, leaf), (0.0, -0.3, 0.085, leaf2), (0.0, -0.21, 0.07, leaf2)):
            d.circ(x + dx * s / AR * 1.7 + lean, y + dy * s, r * s, c)


def pine(L, x, y, s=1.0, snow=False, col='pine', col2='pine2', depth=1.0):
    snow = snow or L.look.season == 'winter'
    with L.piece(0.7 * depth, kind='foliage') as d:
        d.rect(x - 0.006 * s, y - 0.06 * s, x + 0.006 * s, y, '#7a4f33')
    with L.piece(depth, kind='foliage') as d:
        for k, (w, y0, h) in enumerate(((0.12, 0.04, 0.17), (0.095, 0.12, 0.16), (0.068, 0.2, 0.15), (0.04, 0.28, 0.1))):
            c = col if k % 2 == 0 else col2
            hw = w * s * 0.5 / AR * 1.6
            d.poly([(x - hw, y - y0 * s), (x - hw * 0.3, y - (y0 - 0.012) * s), (x + hw * 0.3, y - (y0 - 0.012) * s), (x + hw, y - y0 * s), (x, y - (y0 + h) * s)], c)
            if snow:
                d.poly([(x - hw * 0.45, y - (y0 + h * 0.52) * s), (x + hw * 0.45, y - (y0 + h * 0.52) * s), (x, y - (y0 + h) * s)], '#ffffff')


def birch(L, x, y, s=1.0, rng=None):
    rng = rng or np.random.default_rng(int(x * 1000))
    winter = L.look.season == 'winter'
    with L.piece(0.7, kind='foliage') as d:
        w = 0.007 * s
        d.poly([(x - w, y), (x + w, y), (x + w * 0.6, y - 0.42 * s), (x - w * 0.6, y - 0.42 * s)], '#f2efe6')
        for k in range(7):
            yy = y - (0.05 + 0.055 * k + 0.02 * rng.random()) * s
            d.rect(x - w * (0.2 + 0.8 * rng.random()), yy, x + w * (0.3 * rng.random()), yy + 0.006 * s, '#3a3330')
        for a in (-1, 1):
            d.line([(x, y - 0.3 * s), (x + a * 0.03 * s, y - 0.38 * s)], '#e8e4da', 0.004 * s)
    if winter:
        return
    with L.piece(0.9, kind='foliage') as d:
        for k in range(7):
            dx = (rng.random() - 0.5) * 0.05 * s
            dy = -0.32 * s - rng.random() * 0.14 * s
            d.ell(x + dx, y + dy, 0.04 * s, 0.055 * s, 'leaf2' if k % 2 else 'leaf')


def palm(L, x, y, s=1.0, rng=None):
    with L.piece(0.7, kind='foliage') as d:
        pts = []
        for k in range(9):
            u = k / 8
            pts.append((x + 0.03 * s * u * u, y - 0.36 * s * u))
        for k in range(len(pts) - 1):
            d.line([pts[k], pts[k + 1]], '#a8794a' if k % 2 else '#946a40', 0.016 * s * (1 - 0.3 * k / 8))
    tx, ty = pts[-1]
    with L.piece(1.0, kind='foliage') as d:
        for a in (-160, -125, -90, -55, -20, 15, 200):
            ang = math.radians(a)
            ln = 0.13 * s
            ex, ey = tx + math.cos(ang) * ln / AR * 1.6, ty + math.sin(ang) * ln * 0.55 + 0.03 * s
            mx, my = (tx + ex) / 2, (ty + ey) / 2 - 0.03 * s
            d.poly([(tx, ty), (mx - 0.01 * s, my - 0.02 * s), (ex, ey), (mx + 0.01 * s, my + 0.015 * s)], 'leaf' if a % 2 else 'leaf2')
        d.circ(tx, ty + 0.01 * s, 0.012 * s, '#7a5530')


def bush(L, x, y, s=1.0, col='leaf', col2='leaf2', flowers=None):
    with L.piece(0.9, kind='foliage') as d:
        for dx, dy, r, c in ((-0.035, -0.025, 0.04, col), (0.0, -0.045, 0.05, col2), (0.04, -0.028, 0.042, col)):
            d.ell(x + dx * s, y + dy * s, r * s, r * s * 0.85, c)
        if flowers:
            for dx, dy in ((-0.03, -0.05), (0.01, -0.08), (0.035, -0.045), (-0.005, -0.035), (0.02, -0.06)):
                d.circ(x + dx * s, y + dy * s, 0.008 * s, flowers)


def grass_tufts(L, y0, y1, n, rng, col='tuft', col2='tuft2', s=1.0):
    with L.piece(0.5, kind='foliage') as d:
        for _ in range(n):
            x, y = rng.random(), y0 + (y1 - y0) * rng.random()
            h = (0.018 + 0.014 * rng.random()) * s
            for k in (-2, -1, 0, 1, 2):
                bx = x + k * 0.0035 * s
                tip = (x + k * 0.008 * s, y - h * (1 - 0.18 * abs(k)))
                d.poly([(bx - 0.0022 * s, y), (bx + 0.0022 * s, y), tip], col if k % 2 else col2)


def patches(L, f, y1, n, rng, cols, rx=(0.04, 0.12), ry=(0.008, 0.02), depth=0.35):
    """Flat felt patches on the ground below the ridge f (a function of x) and above y1."""
    with L.piece(depth, kind='ground') as d:
        for i in range(n):
            x = rng.random()
            a, b = rx[0] + (rx[1] - rx[0]) * rng.random(), ry[0] + (ry[1] - ry[0]) * rng.random()
            top = f(x) + b + 0.006
            if top >= y1:
                continue
            y = top + (y1 - top) * rng.random()
            d.ell(x, y, a, b, cols[i % len(cols)])


def flowers(L, y0, y1, n, rng, s=1.0):
    if L.look.season == 'winter':
        return
    cols = ('#f28bb0', '#f6d353', '#ffffff', '#b99be0', '#f28b6b') if L.look.season != 'autumn' else ('#e9b443', '#c9532e', '#f6d353')
    with L.piece(0.5, kind='foliage') as d:
        for i in range(n):
            x, y = rng.random(), y0 + (y1 - y0) * rng.random()
            r = 0.006 * s
            for k in range(5):
                a = k * 1.2566
                d.circ(x + math.cos(a) * r / AR * 1.6, y + math.sin(a) * r, r * 0.8, cols[i % len(cols)])
            d.circ(x, y, r * 0.6, '#f6c453')


def rock(L, x, y, s=1.0, col='#9a958f', depth=0.9):
    with L.piece(depth) as d:
        d.ell(x, y - 0.02 * s, 0.05 * s, 0.03 * s, col)
        d.ell(x + 0.025 * s, y - 0.035 * s, 0.03 * s, 0.025 * s, shade(col, 1.08))


# ---------------------------------------------------------------- buildings

def house(L, x, y, s=1.0, col='#f28b6b', roof='#a34a3a', rng=None, chimney=True):
    """A cottage: x centre, y ground."""
    rng = rng or np.random.default_rng(int(x * 999))
    w, h = 0.065 * s, 0.11 * s
    with L.piece(0.9) as d:
        d.rect(x - w, y - h, x + w, y, col)
        if chimney:
            d.rect(x + w * 0.45, y - h - 0.075 * s, x + w * 0.7, y - h - 0.02 * s, shade(roof, 0.8))
    with L.piece(0.9) as d:
        d.poly([(x - w - 0.012 * s, y - h), (x + w + 0.012 * s, y - h), (x + w * 0.2, y - h - 0.075 * s), (x - w * 0.2, y - h - 0.075 * s)], roof)
        if L.look.season == 'winter':
            d.poly([(x - w - 0.012 * s, y - h - 0.004), (x + w + 0.012 * s, y - h - 0.004), (x + w * 0.2, y - h - 0.075 * s), (x - w * 0.2, y - h - 0.075 * s)], '#f8fafc')
    with L.piece(0.6) as d:
        d.rect(x - 0.016 * s, y - 0.06 * s, x + 0.016 * s, y, '#7a4a2a', r=0.006 * s)
        for dx in (-0.042, 0.042):
            d.window(x + dx * s - 0.014 * s, y - h * 0.78, x + dx * s + 0.014 * s, y - h * 0.4, rng=rng, r=0.003 * s)


def block(L, x0, x1, y, floors, col, rng, win_cols=None, roof=None, balcony=True, fh=0.045, kind='panel'):
    """A Soviet-style panel apartment block: grid of windows, balconies, a flat roof."""
    h = floors * fh
    with L.piece(0.8) as d:
        d.rect(x0, y - h, x1, y, col)
        d.rect(x0 - 0.004, y - h - 0.01, x1 + 0.004, y - h, roof or shade(col, 0.75))
        if kind == 'panel':  # panel seams
            for k in range(1, floors):
                d.rect(x0, y - k * fh - 0.0012, x1, y - k * fh + 0.0012, shade(col, 0.93))
    n = max(2, int((x1 - x0) / 0.03))
    ww = (x1 - x0) / n
    with L.piece(0.5) as d:
        for f in range(floors):
            for k in range(n):
                wx = x0 + k * ww + ww * 0.25
                wy = y - (f + 1) * fh + fh * 0.25
                if f == 0 and k == n // 2:
                    d.rect(wx - ww * 0.05, y - fh * 0.75, wx + ww * 0.55, y, '#6a4a3a', r=0.003)
                    continue
                d.window(wx, wy, wx + ww * 0.5, wy + fh * 0.5, rng=rng, r=0.002)
    if balcony:
        bc = shade(col, 0.82)
        with L.piece(0.6) as d:
            for f in range(1, floors):
                for k in range(n):
                    if (k + f) % 3 == 0:
                        wx = x0 + k * ww + ww * 0.12
                        wy = y - f * fh
                        d.rect(wx, wy - fh * 0.22, wx + ww * 0.76, wy, bc)


def tower(L, x0, x1, y, h, col, rng, stripe=None, top='flat', fh=0.03):
    """A tall city building with a window grid; top=flat|spire|step|round."""
    with L.piece(0.8) as d:
        d.rect(x0, y - h, x1, y, col)
        cx = (x0 + x1) / 2
        if top == 'step':
            d.rect(x0 + (x1 - x0) * 0.15, y - h - 0.03, x1 - (x1 - x0) * 0.15, y - h + 0.001, col)
            d.rect(x0 + (x1 - x0) * 0.32, y - h - 0.055, x1 - (x1 - x0) * 0.32, y - h - 0.029, col)
        elif top == 'spire':
            d.poly([(cx - (x1 - x0) * 0.2, y - h), (cx + (x1 - x0) * 0.2, y - h), (cx, y - h - 0.08)], col)
            d.line([(cx, y - h - 0.07), (cx, y - h - 0.12)], shade(col, 0.8), 0.003)
        elif top == 'round':
            d.ell(cx, y - h, (x1 - x0) * 0.5 * AR, 0.04, col)
        elif top == 'slant':
            d.poly([(x0, y - h), (x1, y - h), (x1, y - h - 0.05)], col)
    cols = max(2, int((x1 - x0) / 0.017))
    ww = (x1 - x0) / cols
    rows = int(h / fh) - 1
    with L.piece(0.4) as d:
        for rr in range(rows):
            for k in range(cols):
                wx, wy = x0 + k * ww + ww * 0.25, y - h + fh * 0.6 + rr * fh
                if wy > y - fh * 0.5:
                    continue
                d.window(wx, wy, wx + ww * 0.5, wy + fh * 0.55, day=stripe or '#cfe6f2', rng=rng, r=0.0015)


def yurt(L, x, y, s=1.0, col='#f3ead6', band='#c0443a', door='#d9822b'):
    """A Kazakh yurt: a low round wall, a shallow dome roof with a shanyrak ring, an ornamented band, a door."""
    w, h = 0.085 * s / AR * 1.5, 0.05 * s
    with L.piece(0.9) as d:
        d.poly([(x - w, y), (x + w, y), (x + w * 0.98, y - h), (x - w * 0.98, y - h)], col)
        roof = [(x + w * 1.02 * math.cos(math.pi * k / 30), y - h - 0.075 * s * math.sin(math.pi * k / 30) ** 0.8) for k in range(31)]
        d.poly(roof, shade(col, 0.96))
        d.ell(x, y - h - 0.072 * s, w * 0.17 * AR, 0.011 * s, shade(col, 0.8))
    with L.piece(0.5) as d:
        d.rect(x - w * 0.98, y - h - 0.004 * s, x + w * 0.98, y - h + 0.011 * s, band)
        n = 7
        for k in range(n):
            cx = x - w * 0.85 + k * w * 1.7 / (n - 1)
            d.poly([(cx - 0.007 * s, y - h + 0.0035 * s), (cx, y - h - 0.0025 * s), (cx + 0.007 * s, y - h + 0.0035 * s), (cx, y - h + 0.0095 * s)], '#f6d353')
        for k in range(5):  # roof ribs
            a = math.pi * (0.2 + 0.15 * k)
            d.line([(x + w * 0.2 * math.cos(a), y - h - 0.068 * s), (x + w * 0.95 * math.cos(a), y - h - 0.012 * s)], shade(col, 0.88), 0.003 * s)
        d.rect(x - 0.017 * s, y - 0.043 * s, x + 0.017 * s, y, door, r=0.003 * s)
        d.rect(x - 0.021 * s, y - 0.047 * s, x + 0.021 * s, y - 0.041 * s, band)


def horse(L, x, y, s=1.0, col='#8a5a3a', mane='#3a2a20', face=1, graze=False):
    f = face
    k = s / AR  # horizontal unit

    def X(u):
        return x + f * u * k
    with L.piece(0.6) as d:
        for u, ph in ((-0.03, 0), (-0.018, 1), (0.022, 1), (0.034, 0)):
            d.line([(X(u), y - 0.04 * s), (X(u + 0.003 * (1 if ph else -1)), y)], shade(col, 0.85), 0.007 * s)
    with L.piece(0.9) as d:
        d.ell(X(0), y - 0.05 * s, 0.045 * s, 0.022 * s, col)
        if graze:
            d.poly([(X(0.03), y - 0.06 * s), (X(0.045), y - 0.055 * s), (X(0.062), y - 0.01 * s), (X(0.052), y - 0.006 * s)], col)
            d.ell(X(0.06), y - 0.01 * s, 0.009 * s, 0.006 * s, col)
        else:
            d.poly([(X(0.025), y - 0.065 * s), (X(0.045), y - 0.04 * s), (X(0.06), y - 0.095 * s), (X(0.045), y - 0.1 * s)], col)
            d.ell(X(0.064), y - 0.093 * s, 0.014 * s, 0.008 * s, col)
            d.poly([(X(0.045), y - 0.1 * s), (X(0.05), y - 0.112 * s), (X(0.054), y - 0.1 * s)], col)
        d.poly([(X(-0.042), y - 0.058 * s), (X(-0.06), y - 0.03 * s), (X(-0.052), y - 0.028 * s), (X(-0.04), y - 0.048 * s)], mane)
    if not graze:
        with L.piece(0.5) as d:
            d.poly([(X(0.028), y - 0.07 * s), (X(0.044), y - 0.103 * s), (X(0.04), y - 0.08 * s), (X(0.03), y - 0.062 * s)], mane)


def camel(L, x, y, s=1.0, col='#c99a5e', face=1):
    k = s / AR

    def X(u):
        return x + face * u * k
    with L.piece(0.6) as d:
        for u in (-0.03, -0.02, 0.022, 0.032):
            d.line([(X(u), y - 0.055 * s), (X(u), y)], shade(col, 0.85), 0.007 * s)
    with L.piece(0.9) as d:
        d.ell(X(0), y - 0.065 * s, 0.045 * s, 0.022 * s, col)
        d.ell(X(-0.012), y - 0.085 * s, 0.022 * s, 0.022 * s, col)
        d.ell(X(0.016), y - 0.083 * s, 0.018 * s, 0.018 * s, col)
        d.poly([(X(0.032), y - 0.07 * s), (X(0.048), y - 0.06 * s), (X(0.07), y - 0.11 * s), (X(0.058), y - 0.118 * s)], col)
        d.ell(X(0.072), y - 0.113 * s, 0.014 * s, 0.008 * s, col)


def car(L, x, y, s=1.0, col='#e05a5a', face=1, lights=None):
    with L.piece(0.9) as d:
        k = s / AR
        d.rect(x - 0.06 * k, y - 0.035 * s, x + 0.06 * k, y - 0.01 * s, col, r=0.012 * s)
        d.poly([(x - 0.035 * k, y - 0.034 * s), (x + 0.03 * k, y - 0.034 * s), (x + 0.018 * k, y - 0.058 * s), (x - 0.024 * k, y - 0.058 * s)], col)
    with L.piece(0.5) as d:
        d.poly([(x - 0.028 * k, y - 0.037 * s), (x + 0.024 * k, y - 0.037 * s), (x + 0.014 * k, y - 0.053 * s), (x - 0.02 * k, y - 0.053 * s)], '#cfe6f2' if not L.look.night else '#3a4870')
        for u in (-0.035, 0.035):
            d.circ(x + u * k, y - 0.01 * s, 0.012 * s, '#2e2e36')
            d.circ(x + u * k, y - 0.01 * s, 0.005 * s, '#b9b9c6')
        if L.look.lit_share > 0.2:
            d.circ(x + face * 0.058 * k, y - 0.025 * s, 0.005 * s, '#fff2c0', lit=True)
            L.glow_circ(x + face * 0.06 * k, y - 0.025 * s, 0.02 * s)
            d.circ(x - face * 0.058 * k, y - 0.025 * s, 0.004 * s, '#ff5040', lit=True)


def bus(L, x, y, s=1.0, col='#f6c453', face=1, rng=None):
    k = s / AR
    with L.piece(0.9) as d:
        d.rect(x - 0.14 * k, y - 0.085 * s, x + 0.14 * k, y - 0.012 * s, col, r=0.012 * s)
    with L.piece(0.5) as d:
        for i in range(6):
            wx = x - 0.12 * k + i * 0.04 * k
            d.window(wx, y - 0.075 * s, wx + 0.032 * k, y - 0.045 * s, rng=rng, r=0.003 * s)
        d.rect(x - 0.14 * k, y - 0.035 * s, x + 0.14 * k, y - 0.03 * s, shade(col, 0.7))
        for u in (-0.09, 0.09):
            d.circ(x + u * k, y - 0.012 * s, 0.014 * s, '#2e2e36')
            d.circ(x + u * k, y - 0.012 * s, 0.006 * s, '#b9b9c6')


def lamp_post(L, x, y, s=1.0, col='#4a4a58'):
    with L.piece(0.6) as d:
        d.line([(x, y), (x, y - 0.2 * s)], col, 0.006 * s)
        d.line([(x, y - 0.2 * s), (x + 0.012 * s, y - 0.21 * s), (x + 0.025 * s, y - 0.205 * s)], col, 0.005 * s)
        d.rect(x - 0.008 * s, y - 0.004 * s, x + 0.008 * s, y, col)
        d.lamp(x + 0.026 * s, y - 0.198 * s, 0.009 * s)


def bench(L, x, y, s=1.0, col='#b07a4a'):
    k = s / AR
    with L.piece(0.7) as d:
        d.rect(x - 0.06 * k, y - 0.045 * s, x + 0.06 * k, y - 0.037 * s, col, r=0.003)
        d.rect(x - 0.06 * k, y - 0.075 * s, x + 0.06 * k, y - 0.067 * s, col, r=0.003)
        d.rect(x - 0.06 * k, y - 0.062 * s, x + 0.06 * k, y - 0.054 * s, col, r=0.003)
        for u in (-0.05, 0.05):
            d.line([(x + u * k, y), (x + u * k, y - 0.08 * s)], '#3a3a44', 0.005 * s)


def fence(L, x0, x1, y, s=1.0, col='#d9b48a'):
    with L.piece(0.6) as d:
        d.line([(x0, y - 0.05 * s), (x1, y - 0.05 * s)], shade(col, 0.9), 0.007 * s)
        d.line([(x0, y - 0.025 * s), (x1, y - 0.025 * s)], shade(col, 0.9), 0.007 * s)
        x = x0
        while x <= x1:
            d.poly([(x - 0.005 * s, y), (x + 0.005 * s, y), (x + 0.005 * s, y - 0.07 * s), (x, y - 0.08 * s), (x - 0.005 * s, y - 0.07 * s)], col)
            x += 0.026 * s


def pole_line(L, y, s, rng, col='#6a5a4a'):
    xs = [(-0.05 + k * 0.32 + 0.04 * rng.random()) for k in range(5)]
    with L.piece(0.5) as d:
        for x in xs:
            d.line([(x, y), (x, y - 0.2 * s)], col, 0.005 * s)
            d.line([(x - 0.02 * s, y - 0.18 * s), (x + 0.02 * s, y - 0.18 * s)], col, 0.004 * s)
        for a, b in zip(xs, xs[1:]):
            pts = [(a + (b - a) * u / 10, y - 0.18 * s + 0.02 * s * math.sin(math.pi * u / 10)) for u in range(11)]
            d.line(pts, '#3a3a40', 0.0018)


def crane(L, x, y, s=1.0, col='#f2b233', face=1):
    with L.piece(0.6) as d:
        h = 0.5 * s
        for k in range(12):
            yy = y - k * h / 12
            d.line([(x - 0.01 * s, yy), (x + 0.01 * s, yy - h / 12)], col, 0.003 * s)
        d.line([(x - 0.01 * s, y), (x - 0.01 * s, y - h)], col, 0.006 * s)
        d.line([(x + 0.01 * s, y), (x + 0.01 * s, y - h)], col, 0.006 * s)
        jib = 0.32 * s * face
        d.line([(x - 0.08 * s * face, y - h), (x + jib, y - h)], col, 0.007 * s)
        d.line([(x, y - h - 0.05 * s), (x + jib * 0.7, y - h)], col, 0.003 * s)
        d.line([(x, y - h - 0.05 * s), (x - 0.07 * s * face, y - h)], col, 0.003 * s)
        d.rect(x - 0.09 * s * face, y - h - 0.004, x - 0.06 * s * face, y - h + 0.03 * s, '#7a7a86')
        d.rect(x - 0.015 * s, y - h + 0.005, x + 0.02 * s, y - h + 0.03 * s, shade(col, 0.8))
        hx_ = x + jib * 0.65
        d.line([(hx_, y - h), (hx_, y - h + 0.18 * s)], '#3a3a40', 0.002)
        d.rect(hx_ - 0.006 * s, y - h + 0.18 * s, hx_ + 0.006 * s, y - h + 0.19 * s, '#3a3a40')
    with L.piece(0.4) as d:
        d.lamp(x + jib, y - h - 0.008, 0.005, '#ff5a4a')


def ship(L, x, y, s=1.0, hull='#c5483e', cabin='#f3efe6', rng=None, kind='cargo'):
    k = s / AR
    with L.piece(0.9) as d:
        d.poly([(x - 0.2 * k, y - 0.05 * s), (x + 0.22 * k, y - 0.05 * s), (x + 0.18 * k, y), (x - 0.18 * k, y)], hull)
        d.rect(x - 0.2 * k, y - 0.05 * s, x + 0.22 * k, y - 0.04 * s, '#2e2e36')
        if kind == 'cargo':
            cs = ('#3f7fbf', '#e9b443', '#6fb850', '#e05a5a', '#9a7ac8')
            for i in range(7):
                for j in range(2):
                    d.rect(x - 0.15 * k + i * 0.04 * k, y - 0.05 * s - (j + 1) * 0.022 * s, x - 0.112 * k + i * 0.04 * k, y - 0.05 * s - j * 0.022 * s - 0.002, cs[(i * 2 + j) % 5])
        d.rect(x + 0.13 * k, y - 0.13 * s, x + 0.19 * k, y - 0.05 * s, cabin)
        d.rect(x + 0.15 * k, y - 0.17 * s, x + 0.17 * k, y - 0.13 * s, '#2e2e36')
    with L.piece(0.4) as d:
        for i in range(3):
            d.window(x + 0.135 * k + i * 0.018 * k, y - 0.115 * s, x + 0.147 * k + i * 0.018 * k, y - 0.1 * s, rng=rng)


def boat(L, x, y, s=1.0, col='#c5583e', sail='#fbfbf6'):
    with L.piece(0.9) as d:
        k = s / AR
        d.poly([(x - 0.07 * k, y - 0.018 * s), (x + 0.07 * k, y - 0.018 * s), (x + 0.05 * k, y + 0.01 * s), (x - 0.05 * k, y + 0.01 * s)], col)
        d.line([(x, y - 0.018 * s), (x, y - 0.15 * s)], '#7a4a2a', 0.004 * s)
        d.poly([(x + 0.003, y - 0.145 * s), (x + 0.003, y - 0.03 * s), (x + 0.06 * k, y - 0.03 * s)], sail)
        d.poly([(x - 0.003, y - 0.12 * s), (x - 0.003, y - 0.03 * s), (x - 0.04 * k, y - 0.03 * s)], shade(sail, 0.92))


def lighthouse(L, x, y, s=1.0):
    with L.piece(0.9) as d:
        for k in range(5):
            y0, y1 = y - k * 0.06 * s, y - (k + 1) * 0.06 * s
            w0, w1 = (0.04 - k * 0.004) * s, (0.04 - (k + 1) * 0.004) * s
            d.poly([(x - w0, y0), (x + w0, y0), (x + w1, y1), (x - w1, y1)], '#e05a5a' if k % 2 == 0 else '#f6f3ea')
        d.rect(x - 0.03 * s, y - 0.305 * s, x + 0.03 * s, y - 0.295 * s, '#3a3a4a')
    with L.piece(0.6) as d:
        on = L.look.lit_share > 0.2
        d.rect(x - 0.018 * s, y - 0.345 * s, x + 0.018 * s, y - 0.3 * s, '#ffe39a' if on else '#cfe6f2', lit=on)
        d.poly([(x - 0.026 * s, y - 0.345 * s), (x + 0.026 * s, y - 0.345 * s), (x, y - 0.385 * s)], '#3a3a4a')
        if on:
            L.glow_circ(x, y - 0.322 * s, 0.05 * s)
    if L.look.lit_share > 0.5:  # beams
        with L.piece(0.2) as d:
            d.poly([(x, y - 0.33 * s), (x - 0.5, y - 0.42 * s), (x - 0.5, y - 0.3 * s)], (255, 236, 170, 70))


def train(L, x0, y, s, cars, rng, col='#3f8f5a', face=1):
    k = s / AR
    x = x0
    for i in range(cars):
        loco = i == 0
        w = 0.2 * k
        c = col if not loco else '#c5483e'
        with L.piece(0.9) as d:
            d.rect(x, y - 0.08 * s, x + w, y - 0.012 * s, c, r=0.01 * s)
            d.rect(x, y - 0.088 * s, x + w, y - 0.076 * s, shade(c, 0.8), r=0.005 * s)
        with L.piece(0.5) as d:
            for j in range(5 if not loco else 2):
                wx = x + 0.012 * k + j * 0.038 * k
                d.window(wx, y - 0.068 * s, wx + 0.026 * k, y - 0.045 * s, rng=rng, r=0.003 * s)
            d.rect(x, y - 0.04 * s, x + w, y - 0.034 * s, '#f6f3ea')
            for u in (0.03, 0.06, w / k - 0.06, w / k - 0.03):
                d.circ(x + u * k, y - 0.012 * s, 0.009 * s, '#2e2e36')
        x += w + 0.008 * k
    return x
