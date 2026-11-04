"""Outdoor biomes. Each function fills the layers of a Scene (sky, far, mid, near, fg) and returns a one-line
description. Variants (S.variant) change the composition; the seed changes placement."""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from plates import AR, shade, mixc, sky, weather_fx, sky_gradient, hx, to255, W, H
from props import (hills, mountains, round_tree, pine, birch, palm, bush, grass_tufts, flowers, rock, house, block, tower,
                   yurt, horse, camel, car, bus, lamp_post, bench, fence, pole_line, crane, ship, boat, lighthouse, train,
                   ridge_fn, patches, cloud_puff)

BIOMES = {}


def biome(name, interior=False, about=''):
    def deco(fn):
        BIOMES[name] = (fn, interior)
        fn.about = about
        return fn
    return deco


def winter(S):
    return S.season == 'winter'


def flat(y, amp=0.004, seed=0):
    return ridge_fn(seed, y, amp, freqs=(1.1, 2.7, 6.1))


# ---------------------------------------------------------------- extra props

def poplar(L, x, y, s=1.0):
    """A tall pyramidal poplar, the street tree of Almaty."""
    with L.piece(0.7, kind='foliage') as d:
        d.rect(x - 0.004 * s, y - 0.06 * s, x + 0.004 * s, y, '#6a4a33')
    if winter(L.scene):
        with L.piece(0.6, kind='foliage') as d:
            for k in range(6):
                d.line([(x, y - 0.05 * s), (x + (k - 2.5) * 0.006 * s, y - (0.28 + 0.03 * (k % 2)) * s)], '#6a5546', 0.003 * s)
        return
    with L.piece(0.9, kind='foliage') as d:
        d.ell(x, y - 0.17 * s, 0.028 * s, 0.13 * s, 'leaf')
        d.ell(x + 0.004 * s, y - 0.2 * s, 0.018 * s, 0.09 * s, 'leaf2')


def haystack(L, x, y, s=1.0):
    with L.piece(0.9) as d:
        d.ell(x, y - 0.035 * s, 0.05 * s, 0.045 * s, '#e3c25e')
        d.rect(x - 0.05 * s / AR * AR, y - 0.035 * s, x + 0.05 * s / AR * AR, y, '#e3c25e')
        if winter(L.scene):
            d.ell(x, y - 0.065 * s, 0.035 * s, 0.018 * s, '#ffffff')


def cow(L, x, y, s=1.0, face=1, col='#f6f3ea', spot='#3a302a'):
    k = s / AR

    def X(u):
        return x + face * u * k
    with L.piece(0.6) as d:
        for u in (-0.03, -0.02, 0.022, 0.032):
            d.line([(X(u), y - 0.03 * s), (X(u), y)], shade(col, 0.8), 0.008 * s)
    with L.piece(0.9) as d:
        d.rect(X(-0.045) if face > 0 else X(0.04), y - 0.06 * s, X(0.04) if face > 0 else X(-0.045), y - 0.025 * s, col, r=0.012 * s)
        d.ell(X(0.05), y - 0.055 * s, 0.016 * s, 0.013 * s, col)
        d.ell(X(0.058), y - 0.05 * s, 0.009 * s, 0.007 * s, '#f0b0a8')
        d.ell(X(-0.015), y - 0.048 * s, 0.012 * s, 0.009 * s, spot)
        d.ell(X(0.015), y - 0.04 * s, 0.009 * s, 0.007 * s, spot)
        d.line([(X(0.042), y - 0.067 * s), (X(0.036), y - 0.074 * s)], '#e8dcc0', 0.004 * s)


def barn(L, x, y, s=1.0, col='#c5483e'):
    w, h = 0.09 * s / AR * AR, 0.12 * s
    w = 0.09 * s
    with L.piece(0.9) as d:
        d.rect(x - w, y - h, x + w, y, col)
        d.poly([(x - w - 0.01, y - h), (x - w * 0.55, y - h - 0.06 * s), (x + w * 0.55, y - h - 0.06 * s), (x + w + 0.01, y - h)], shade(col, 0.7) if not winter(L.scene) else '#f8fafc')
    with L.piece(0.6) as d:
        d.rect(x - 0.035 * s, y - 0.08 * s, x + 0.035 * s, y, '#f3efe6')
        d.line([(x - 0.035 * s, y - 0.08 * s), (x + 0.035 * s, y)], col, 0.006 * s)
        d.line([(x + 0.035 * s, y - 0.08 * s), (x - 0.035 * s, y)], col, 0.006 * s)
        d.window(x - 0.015 * s, y - h + 0.01, x + 0.015 * s, y - h + 0.035 * s, force=L.look.lit_share > 0.5)


def silo(L, x, y, s=1.0):
    with L.piece(0.9) as d:
        d.rect(x - 0.025 * s, y - 0.2 * s, x + 0.025 * s, y, '#c9cfd6')
        d.ell(x, y - 0.2 * s, 0.025 * s, 0.025 * s, '#aab2bc')
        for k in range(1, 6):
            d.rect(x - 0.025 * s, y - k * 0.035 * s, x + 0.025 * s, y - k * 0.035 * s + 0.003, '#b2b9c2')


def well(L, x, y, s=1.0):
    with L.piece(0.9) as d:
        d.rect(x - 0.035 * s, y - 0.045 * s, x + 0.035 * s, y, '#9a958f', r=0.006 * s)
        for k in range(3):
            d.rect(x - 0.035 * s, y - 0.045 * s + k * 0.015 * s, x + 0.035 * s, y - 0.043 * s + k * 0.015 * s, '#86817a')
        d.line([(x - 0.03 * s, y - 0.045 * s), (x - 0.03 * s, y - 0.11 * s)], '#7a4a2a', 0.006 * s)
        d.line([(x + 0.03 * s, y - 0.045 * s), (x + 0.03 * s, y - 0.11 * s)], '#7a4a2a', 0.006 * s)
        d.poly([(x - 0.045 * s, y - 0.105 * s), (x + 0.045 * s, y - 0.105 * s), (x, y - 0.14 * s)], '#a34a3a')


def stall(L, x0, x1, y, s, awning, rng, goods=True):
    """A bazaar stall: posts, a striped awning, a counter heaped with fruit."""
    h = 0.17 * s
    with L.piece(0.7) as d:
        for x in (x0 + 0.004, x1 - 0.004):
            d.line([(x, y), (x, y - h)], '#7a5a3a', 0.006 * s)
    with L.piece(0.9) as d:
        n = max(3, int((x1 - x0) / (0.022 * s)))
        ww = (x1 - x0 + 0.02) / n
        for k in range(n):
            xa = x0 - 0.01 + k * ww
            d.poly([(xa, y - h - 0.03 * s), (xa + ww, y - h - 0.03 * s), (xa + ww, y - h + 0.02 * s), (xa, y - h + 0.02 * s)], awning if k % 2 == 0 else '#f6f3ea')
            d.ell(xa + ww / 2, y - h + 0.02 * s, ww / 2 * AR, 0.012 * s, awning if k % 2 == 0 else '#f6f3ea')
    with L.piece(0.9) as d:
        d.rect(x0 - 0.005, y - 0.07 * s, x1 + 0.005, y, '#b07a4a', r=0.004)
        d.rect(x0 - 0.005, y - 0.07 * s, x1 + 0.005, y - 0.06 * s, '#8a5a3a')
    if goods:
        fruit = [('#f08a2e', 0.012), ('#e0403a', 0.011), ('#f6d353', 0.012), ('#7cc45e', 0.011), ('#8a3a6a', 0.009), ('#e9c46a', 0.03)]
        with L.piece(0.7) as d:
            x = x0 + 0.01
            while x < x1 - 0.02:
                c, r = fruit[int(rng.integers(len(fruit)))]
                r *= s
                if r > 0.02 * s:  # a melon
                    d.ell(x + r * 0.6, y - 0.07 * s - r * 0.6, r, r * 0.7, c)
                    x += r * 1.4 / AR + 0.008
                    continue
                for row in range(3):
                    for k in range(3 - row):
                        d.circ(x + (k + row * 0.5) * r * 2 / AR, y - 0.07 * s - r - row * r * 1.7, r, c)
                x += r * 6 / AR + 0.008


def dune(L, base, amp, col, seed, depth=1.0):
    f = ridge_fn(seed, base, amp, freqs=(0.9, 2.3, 4.1), weights=(1, 0.35, 0.1))
    with L.piece(depth) as d:
        d.ridge(f, col)
        # the shaded lee side of each crest
        pts = []
        for i in range(161):
            x = -0.03 + 1.06 * i / 160
            pts.append((x, f(x)))
        for i in range(1, 160):
            if pts[i][1] < pts[i - 1][1] and pts[i][1] <= pts[i + 1][1]:  # a crest
                cx, cy = pts[i]
                d.poly([(cx, cy), (cx + 0.12, f(cx + 0.12) + 0.004), (cx + 0.05, cy + amp * 0.9)], shade(col, 0.86))
    return f


def saxaul(L, x, y, s=1.0):
    with L.piece(0.6) as d:
        for a in (-0.7, -0.3, 0.1, 0.5, 0.8):
            ex, ey = x + a * 0.025 * s, y - (0.04 + 0.02 * abs(math.sin(a * 5))) * s
            d.line([(x, y), (ex, ey)], '#7a6450', 0.004 * s)
            d.ell(ex, ey, 0.012 * s, 0.008 * s, '#8a9a5a')


def reeds(L, x0, x1, y, s, rng, col='#8aa85a'):
    with L.piece(0.6) as d:
        x = x0
        while x < x1:
            h = (0.06 + 0.06 * rng.random()) * s
            lean = (rng.random() - 0.5) * 0.015 * s
            d.line([(x, y), (x + lean, y - h)], col, 0.003 * s)
            if rng.random() < 0.4:
                d.ell(x + lean, y - h + 0.012 * s, 0.004 * s, 0.014 * s, '#7a5235')
            x += 0.004 + 0.008 * rng.random()


def water(L, top, col='#4f8fca', col2='#6aa6dc', seed=0, waves=True, bottom=1.02):
    with L.piece(0.6) as d:
        d.rect(-0.02, top, 1.02, bottom, col)
    if waves:
        r = np.random.default_rng(seed)
        with L.piece(0.35) as d:
            for k in range(26):
                y = top + 0.01 + (bottom - top) * (k / 26) ** 1.5
                x = r.random()
                w = 0.02 + 0.06 * (y - top) / max(bottom - top, 0.01)
                d.rect(x, y, x + w, y + 0.003 + 0.004 * (y - top) / max(bottom - top, 0.01), col2, r=0.002)


def reflection(L, x, top, w, col, n=8):
    with L.piece(0.3) as d:
        for k in range(n):
            y = top + 0.006 + k * 0.012
            ww = w * (1 - k / n) * (0.6 + 0.4 * ((k * 7) % 3) / 2)
            d.rect(x - ww, y, x + ww, y + 0.005, col, r=0.002)


def sign(L, x, y, s=1.0, col='#2f7a4a', w=0.12):
    with L.piece(0.7) as d:
        d.line([(x - w * 0.35, y), (x - w * 0.35, y - 0.16 * s)], '#8a8f99', 0.006 * s)
        d.line([(x + w * 0.35, y), (x + w * 0.35, y - 0.16 * s)], '#8a8f99', 0.006 * s)
        d.rect(x - w / 2, y - 0.24 * s, x + w / 2, y - 0.15 * s, col, r=0.008 * s)
        d.rect(x - w / 2 + 0.006, y - 0.235 * s + 0.004, x + w / 2 - 0.006, y - 0.155 * s - 0.004, shade(col, 1.15), r=0.006 * s)
    with L.piece(0.4) as d:  # blank arrow and bars, no words
        d.poly([(x + w * 0.25, y - 0.195 * s), (x + w * 0.38, y - 0.195 * s), (x + w * 0.38, y - 0.21 * s), (x + w * 0.44, y - 0.19 * s), (x + w * 0.38, y - 0.17 * s), (x + w * 0.38, y - 0.185 * s), (x + w * 0.25, y - 0.185 * s)], '#ffffff')
        for k in range(2):
            d.rect(x - w * 0.4, y - 0.215 * s + k * 0.03 * s, x + w * (0.1 - 0.15 * k), y - 0.205 * s + k * 0.03 * s, '#ffffff', r=0.003)


# ---------------------------------------------------------------- Kazakhstan

@biome('steppe')
def steppe(S):
    v = S.variant % 4
    hz = 0.6 + S.r(-0.03, 0.03)
    sky(S, horizon=hz)
    far = S.L('far')
    if v in (0, 2):
        mountains(far, hz + 0.02, hz - 0.2, seed=S.seed, col='#9aa3cf', snowline=0.5)
    else:
        hills(far, hz + 0.01, 0.06, '#b2b6cc', seed=S.seed, freqs=(0.8, 2.2, 5.0))
    mid = S.L('mid')
    hills(mid, hz + 0.035, 0.035, 'steppe2', seed=S.seed + 5, freqs=(0.9, 2.4, 5.0))
    f = hills(mid, hz + 0.08, 0.05, 'steppe', seed=S.seed + 1, freqs=(0.7, 1.9, 4.0))
    rng = S.rng
    patches(mid, f, 0.9, 10, rng, ['steppe2', 'steppe2', 'grass2'] if S.season == 'spring' else ['steppe2'])
    if v in (0, 1):  # a yurt camp
        xs = sorted(S.r(0.08, 0.9) for _ in range(3 + v))
        xs = [x for i, x in enumerate(xs) if i == 0 or x - xs[i - 1] > 0.09]
        for x in xs:
            yurt(mid, x, f(x) + 0.035, 0.85 + 0.3 * S.r(), band=S.pick(['#c0443a', '#2f6fb0', '#c0443a', '#3d8a5a']))
    if v in (1, 2, 3):  # a herd of horses
        n = 4 + int(S.r(0, 4))
        cx = S.r(0.25, 0.7)
        for i in range(n):
            x = cx + S.r(-0.18, 0.18)
            horse(mid, x, f(x) + 0.08 + S.r(0, 0.05), 1.5 + 0.3 * S.r(), col=S.pick(['#8a5a3a', '#5a3a2a', '#c9955c', '#f0ece4', '#3a2a24']),
                  face=S.pick([-1, 1]), graze=S.r() < 0.5)
    near = S.L('near')
    g = hills(near, 0.84, 0.05, 'steppe', seed=S.seed + 2, freqs=(0.6, 1.4, 3.3))
    patches(near, g, 1.0, 6, rng, ['steppe2'])
    if v == 3:
        yurt(near, 0.76, g(0.76) + 0.05, 1.9, band='#c0443a')
        horse(near, 0.5, g(0.5) + 0.08, 2.0, col='#8a5a3a', face=1)
    elif v == 2:
        with near.piece(0.5) as d:  # a dirt track
            pts = [(0.3 + 0.25 * u + 0.05 * math.sin(u * 5), g(0.3 + 0.25 * u) + 0.01 + (1.02 - g(0.3)) * u) for u in np.linspace(0, 1, 20)]
            d.line(pts, '#c8a77a', 0.03)
    fg = S.L('fg')
    grass_tufts(fg, 0.93, 1.0, 26, rng, col='steppe2', col2='steppe', s=2.2)
    if S.season == 'spring':  # red tulips in the spring steppe
        flowers(fg, 0.9, 0.99, 22, rng, s=1.8)
    weather_fx(S, ground=hz + 0.06)
    return {0: 'Kazakh steppe with a yurt camp under far mountains', 1: 'steppe yurt camp with a horse herd',
            2: 'open steppe, horses grazing, mountains far away', 3: 'a yurt and a horse close up on the steppe'}[v]


@biome('mountains')
def tianshan(S):
    v = S.variant % 4
    hz = 0.56
    sky(S, horizon=hz, cloud_y=(0.05, 0.3))
    far = S.L('far')
    mountains(far, hz + 0.08, 0.1, seed=S.seed, col='#8f9ccc', snowline=0.62)
    mid = S.L('mid')
    mountains(mid, hz + 0.2, hz - 0.12, seed=S.seed + 7, col='#6f8bb0' if v != 2 else '#7f8f9f', snowline=0.3 if not winter(S) else 0.8)
    f = hills(mid, hz + 0.22, 0.04, 'grass2', seed=S.seed + 3)
    near = S.L('near')
    g = hills(near, 0.82, 0.06, 'grass', seed=S.seed + 4)
    rng = S.rng
    patches(near, g, 1.0, 5, rng, ['grass2', 'grass3'])
    if v == 1:  # a lake in the valley
        with mid.piece(0.6) as d:
            d.ell(0.5, f(0.5) + 0.05, 0.5, 0.045, '#5c9bd6' if not winter(S) else '#cfe0ee')
    xs = sorted(S.r(0, 1) for _ in range(9))
    for x in xs:  # Tian Shan spruce on the slopes
        if v == 3 and 0.45 < x < 0.75:
            continue
        pine(near, x, g(x) + 0.02, 0.9 + 0.5 * S.r(), depth=0.9)
    if v == 3:
        yurt(near, 0.6, g(0.6) + 0.04, 1.2)
        horse(near, 0.7, g(0.7) + 0.06, 1.0, face=-1, graze=True)
    fg = S.L('fg')
    with fg.piece() as d:
        d.ridge(ridge_fn(S.seed + 9, 0.98, 0.04), 'grass2')
    rock(fg, 0.08, 1.0, 2.6)
    grass_tufts(fg, 0.95, 1.0, 18, rng, s=2.0)
    weather_fx(S, ground=hz + 0.15)
    return {0: 'Tian Shan-like snowy peaks over spruce slopes', 1: 'mountain valley with a lake and snowy peaks',
            2: 'high grey rock mountains with snow and spruce', 3: 'a yurt on a mountain pasture'}[v]


@biome('almaty')
def almaty(S):
    """A city at the foot of a big snowy range: mid-rise blocks and towers, poplar streets. No real landmarks."""
    v = S.variant % 3
    hz = 0.6
    sky(S, horizon=0.5, cloud_y=(0.04, 0.2))
    far = S.L('far')
    mountains(far, hz, 0.08, seed=S.seed + 11, col='#8d9bd0', snowline=0.55)
    mid = S.L('mid')
    rng = S.rng
    base = 0.66 if v != 2 else 0.6
    x = -0.02
    cols = ['#e9dcc6', '#d8c9b4', '#f0e2c8', '#c9d3dc', '#e6d2c0', '#d9e0e6']
    items = []
    while x < 1.02:
        w = 0.04 + 0.05 * rng.random()
        tall = rng.random() < 0.22
        h = 0.26 + 0.12 * rng.random() if tall else 0.08 + 0.1 * rng.random()
        items.append((x, w, h, tall))
        x += w + 0.002
    for x, w, h, tall in sorted(items, key=lambda t: -t[2]):
        if tall:
            tower(mid, x, x + w, base, h, S.pick(['#c9d6e2', '#d8dee6', '#b9cbd9', '#e0d6c8']), rng, top=S.pick(['flat', 'step', 'slant', 'flat']))
        else:
            block(mid, x, x + w, base, max(2, int(h / 0.035)), S.pick(cols), rng, fh=0.035, balcony=rng.random() < 0.5)
    near = S.L('near')
    if v == 2:  # panorama from a hillside park
        g = hills(near, 0.8, 0.07, 'grass', seed=S.seed)
        for k in range(6):
            xx = S.r(0, 1)
            round_tree(near, xx, g(xx) + 0.03, 1.1 + 0.4 * S.r(), rng=rng)
        bench(near, 0.5, g(0.5) + 0.06, 1.3)
        lamp_post(near, 0.62, g(0.62) + 0.06, 1.2)
    else:
        with near.piece(0.5) as d:
            d.rect(-0.02, base + 0.005, 1.02, 1.02, '#9a9aa6')
            d.rect(-0.02, base + 0.005, 1.02, base + 0.04, '#c9c1b0')
            for k in range(9):
                d.rect(k * 0.12, 0.84, k * 0.12 + 0.06, 0.85, '#f2f2f2')
        for k in range(8):
            poplar(near, 0.03 + k * 0.135 + S.r(-0.02, 0.02), base + 0.04, 1.2 + 0.2 * S.r())
        for k in range(3):
            car(near, S.r(0.05, 0.95), 0.83 if k % 2 else 0.9, 1.6, col=S.pick(['#e05a5a', '#f2f2f2', '#3f7fbf', '#2e2e36', '#f6c453']), face=1 if k % 2 else -1)
        if v == 1:
            bus(near, 0.6, 0.88, 1.4, col='#e9b443', rng=rng)
        for k in range(4):
            lamp_post(near, 0.12 + k * 0.26, base + 0.04, 1.1)
    fg = S.L('fg')
    if v == 2:
        grass_tufts(fg, 0.95, 1.0, 20, rng, s=2.0)
        bush(fg, 0.92, 1.03, 2.2)
    else:
        with fg.piece() as d:
            d.rect(-0.02, 0.965, 1.02, 1.02, '#c9c1b0')
        bush(fg, 0.05, 1.0, 2.0)
        bush(fg, 0.95, 1.0, 1.8)
    weather_fx(S, ground=base)
    return {0: 'Almaty-like city street with poplars under a snowy range', 1: 'city avenue with a bus and mountains behind',
            2: 'city panorama from a hillside park with mountains'}[v]


@biome('courtyard')
def courtyard(S):
    """A Soviet courtyard between panel blocks: playground, benches, birches, laundry."""
    v = S.variant % 3
    sky(S, horizon=0.55, cloud_y=(0.04, 0.18))
    rng = S.rng
    far = S.L('far')
    for k in range(4):
        x = -0.05 + k * 0.28 + S.r(0, 0.05)
        block(far, x, x + 0.22, 0.5, 9, S.pick(['#d6d2c8', '#c9cdd2', '#e0d8c4']), rng, fh=0.034, balcony=False)
    mid = S.L('mid')
    block(mid, -0.03, 0.46, 0.66, 5, '#e8dcc0' if v != 1 else '#d9c9b4', rng, fh=0.07)
    block(mid, 0.54, 1.03, 0.66, 5, '#cfd6dc' if v != 2 else '#e6d2bc', rng, fh=0.07)
    with mid.piece(0.5) as d:
        d.rect(-0.02, 0.655, 1.02, 1.02, '#a9a39a')
    near = S.L('near')
    with near.piece(0.5) as d:
        d.ell(0.5, 0.86, 0.75, 0.13, 'grass' if not winter(S) else '#eef3f8')
        d.rect(-0.02, 0.69, 1.02, 0.72, '#8f8a82')
    for x in (0.08, 0.3, 0.92):
        birch(near, x + S.r(-0.02, 0.02), 0.74, 1.0 + 0.3 * S.r(), rng)
    if v == 0:  # playground
        with near.piece(0.8) as d:
            d.line([(0.45, 0.86), (0.48, 0.72), (0.58, 0.72), (0.61, 0.86)], '#e05a5a', 0.007)
            d.line([(0.5, 0.72), (0.5, 0.82)], '#3a3a44', 0.002)
            d.line([(0.56, 0.72), (0.56, 0.82)], '#3a3a44', 0.002)
            d.rect(0.49, 0.82, 0.51, 0.83, '#f6c453')
            d.rect(0.55, 0.82, 0.57, 0.83, '#3f7fbf')
            d.line([(0.68, 0.87), (0.68, 0.76)], '#3f7fbf', 0.006)
            d.rect(0.66, 0.75, 0.71, 0.765, '#3f7fbf')
            d.poly([(0.705, 0.76), (0.715, 0.76), (0.79, 0.87), (0.77, 0.875)], '#f6c453')
        with near.piece(0.6) as d:  # sandbox
            d.rect(0.18, 0.86, 0.3, 0.9, '#c99a6a')
            d.ell(0.24, 0.87, 0.06, 0.012, '#f1dfae')
    elif v == 1:  # laundry lines and benches
        with near.piece(0.6) as d:
            d.line([(0.4, 0.86), (0.4, 0.7)], '#6a6a72', 0.004)
            d.line([(0.75, 0.86), (0.75, 0.7)], '#6a6a72', 0.004)
            d.line([(0.4, 0.71), (0.575, 0.725), (0.75, 0.71)], '#3a3a40', 0.0015)
            for k, c in enumerate(['#e05a5a', '#f6f3ea', '#3f7fbf', '#f6d353', '#9fd0ee', '#f2a0b8']):
                x = 0.43 + k * 0.05
                yy = 0.716 + 0.01 * math.sin((x - 0.4) / 0.35 * math.pi)
                d.rect(x, yy, x + 0.03, yy + 0.04 + 0.01 * (k % 2), c, r=0.002)
        bench(near, 0.25, 0.86, 1.2)
    else:  # garages
        with near.piece(0.8) as d:
            for k in range(5):
                x = 0.4 + k * 0.1
                d.rect(x, 0.74, x + 0.095, 0.84, S.pick(['#8a98a8', '#a89a88', '#7f8f80']))
                d.rect(x + 0.01, 0.76, x + 0.085, 0.84, shade('#8a98a8', 0.8))
        bench(near, 0.25, 0.88, 1.2)
    fg = S.L('fg')
    fence(fg, -0.02, 0.32, 1.0, 1.5, col='#7f9a5a')
    bush(fg, 0.9, 1.02, 2.4)
    bush(fg, 0.72, 1.03, 1.6, flowers='#f2a0b8' if S.season == 'spring' else None)
    weather_fx(S, ground=0.7)
    return {0: 'Soviet courtyard: panel blocks, birches, a playground', 1: 'courtyard with laundry lines and a bench',
            2: 'courtyard with garages and birches'}[v]


@biome('bazaar')
def bazaar(S):
    v = S.variant % 3
    sky(S, horizon=0.5, cloud_y=(0.04, 0.2))
    rng = S.rng
    far = S.L('far')
    if v == 2:
        mountains(far, 0.5, 0.12, seed=S.seed, col='#8d9bd0')
    else:
        for k in range(5):
            x = -0.03 + k * 0.22
            block(far, x, x + 0.18, 0.5, 6, S.pick(['#e0d6c4', '#d4ccc0']), rng, fh=0.04, balcony=False)
    mid = S.L('mid')
    with mid.piece(0.8) as d:  # a long market hall roof behind
        d.rect(-0.02, 0.38, 1.02, 0.6, '#d8c3a0')
        for k in range(12):
            d.ell(0.04 + k * 0.085, 0.38, 0.045, 0.04, '#c9b08a')
        for k in range(12):
            d.rect(0.02 + k * 0.085, 0.44, 0.06 + k * 0.085, 0.56, '#b9a07a', r=0.02)
    awn = ['#c0443a', '#2f6fb0', '#3d8a5a', '#e9a23a', '#8a3a6a']
    x = 0.0
    while x < 1.0:
        w = 0.14 + 0.05 * rng.random()
        stall(mid, x, x + w, 0.68, 0.85, S.pick(awn), rng)
        x += w + 0.02
    near = S.L('near')
    with near.piece(0.4) as d:
        d.rect(-0.02, 0.7, 1.02, 1.02, '#c9b391')
        for k in range(14):
            d.ell(S.r(0, 1), S.r(0.75, 0.98), 0.03, 0.006, '#b9a07a')
    stall(near, 0.02, 0.36, 0.86, 1.4, S.pick(awn), rng)
    stall(near, 0.64, 0.98, 0.86, 1.4, S.pick(awn), rng)
    if v == 1:  # hanging carpets
        with near.piece(0.7) as d:
            for k, c in enumerate(('#a83a3a', '#2f5f9a', '#8a5a2a')):
                x0 = 0.4 + k * 0.075
                d.rect(x0, 0.5, x0 + 0.065, 0.74, c)
                d.rect(x0 + 0.008, 0.515, x0 + 0.057, 0.725, shade(c, 1.3))
                d.poly([(x0 + 0.0325, 0.55), (x0 + 0.055, 0.62), (x0 + 0.0325, 0.69), (x0 + 0.01, 0.62)], c)
            d.line([(0.38, 0.5), (0.63, 0.5)], '#6a4a2a', 0.004)
    fg = S.L('fg')
    with fg.piece() as d:  # crates
        for x0, c in ((0.0, '#b07a4a'), (0.82, '#a86f45')):
            d.rect(x0, 0.9, x0 + 0.18, 1.02, c, r=0.006)
            for k in range(3):
                d.rect(x0, 0.92 + k * 0.035, x0 + 0.18, 0.926 + k * 0.035, shade(c, 0.8))
    with fg.piece(0.8) as d:
        for x0 in (0.0, 0.82):
            c = S.pick(['#e0403a', '#f08a2e', '#f6d353', '#7cc45e'])
            for k in range(9):
                d.circ(x0 + 0.02 + k * 0.018, 0.895 - 0.008 * (k % 2), 0.018, c)
    weather_fx(S, ground=0.7)
    return {0: 'bazaar row with striped awnings and fruit', 1: 'bazaar row with hanging carpets',
            2: 'open-air bazaar with mountains behind'}[v]


@biome('desert')
def desert(S):
    v = S.variant % 3
    hz = 0.58
    sky(S, horizon=hz, clouds=0 if S.weather == 'clear' else None)
    rng = S.rng
    far = S.L('far')
    dune(far, hz + 0.02, 0.06, '#e9c48a', S.seed)
    mid = S.L('mid')
    f = dune(mid, hz + 0.1, 0.09, '#e6b878', S.seed + 1)
    near = S.L('near')
    g = dune(near, 0.82, 0.08, '#efc98c', S.seed + 2)
    if v == 0:  # a caravan along the mid crest
        x = S.r(0.12, 0.3)
        for k in range(4):
            camel(mid, x + k * 0.15, f(x + k * 0.15) + 0.04, 2.0, face=1)
    elif v == 1:  # an oasis
        with mid.piece(0.6) as d:
            d.ell(0.6, f(0.6) + 0.06, 0.18, 0.03, '#4f8fca')
        for x in (0.45, 0.52, 0.7, 0.76):
            palm(mid, x, f(x) + 0.05, 1.0 + 0.3 * S.r(), rng)
        camel(near, 0.25, g(0.25) + 0.06, 3.0, face=1)
    else:
        camel(near, 0.66, g(0.66) + 0.07, 3.2, face=-1)
        camel(near, 0.84, g(0.84) + 0.09, 2.6, face=-1)
        for x in (0.15, 0.4):
            saxaul(near, x, g(x) + 0.03, 1.6)
    fg = S.L('fg')
    dune(fg, 1.0, 0.06, '#f2d29a', S.seed + 3)
    for x in (0.08, 0.9):
        saxaul(fg, x, 1.0, 2.6)
    weather_fx(S, ground=hz + 0.05)
    return {0: 'desert dunes with a camel caravan', 1: 'desert oasis with palms and a camel', 2: 'camels on the dunes, saxaul shrubs'}[v]


# ---------------------------------------------------------------- forests, water

def forest_floor(S, L, y, col='grass', amp=0.02):
    return hills(L, y, amp, col, seed=S.seed + 7 * len(L.name))


@biome('birch_forest')
def birch_forest(S):
    v = S.variant % 3
    sky(S, horizon=0.6)
    rng = S.rng
    far = S.L('far')
    f0 = hills(far, 0.58, 0.04, mixc('#7fa66a', '#9aa8c0', 0.4), seed=S.seed)
    with far.piece(0.6) as d:
        x = -0.02
        while x < 1.02:
            r = 0.02 + 0.02 * rng.random()
            d.ell(x, f0(x) - r * 0.5, r * 1.3, r * 1.4, mixc('#6f9a5a', '#9aa8c0', 0.4) if not winter(S) else '#b9b4c0')
            x += 0.02 + 0.02 * rng.random()
    mid = S.L('mid')
    f = forest_floor(S, mid, 0.7)
    for k in range(14):
        x = k / 13 + S.r(-0.03, 0.03)
        birch(mid, x, f(x) + 0.01, 0.75 + 0.2 * S.r(), rng)
    near = S.L('near')
    g = forest_floor(S, near, 0.86, 'grass2', 0.03)
    patches(near, g, 1.0, 5, rng, ['grass', 'grass3'])
    for x in ([0.1, 0.35, 0.82] if v != 1 else [0.2, 0.7]):
        birch(near, x + S.r(-0.03, 0.03), g(x) + 0.02, 1.6 + 0.3 * S.r(), rng)
    if v == 1:  # a path
        with near.piece(0.4) as d:
            d.poly([(0.42, 0.86), (0.48, 0.86), (0.62, 1.02), (0.3, 1.02)], '#d9c08f' if not winter(S) else '#dfe6ee')
    if v == 2 and not winter(S):  # mushrooms
        with near.piece(0.7) as d:
            for x in (0.5, 0.56, 0.6):
                y = g(x) + 0.06
                d.rect(x - 0.005, y - 0.03, x + 0.005, y, '#f3ead6')
                d.pie(x, y - 0.03, 0.022, 180, 360, '#d9443a')
                d.circ(x - 0.006, y - 0.04, 0.004, '#ffffff')
    fg = S.L('fg')
    grass_tufts(fg, 0.95, 1.0, 26, rng, s=2.4)
    flowers(fg, 0.93, 0.99, 10 if S.season != 'summer' else 18, rng, s=1.6)
    weather_fx(S, ground=0.72)
    return {0: 'birch grove', 1: 'birch grove with a path', 2: 'birch grove with mushrooms'}[v]


@biome('pine_forest')
def pine_forest(S):
    v = S.variant % 3
    sky(S, horizon=0.55)
    rng = S.rng
    far = S.L('far')
    if v == 2:
        mountains(far, 0.56, 0.18, seed=S.seed, col='#8f9ccc')
    f0 = hills(far, 0.6, 0.03, mixc('#357f4e', '#9aa8c0', 0.5), seed=S.seed)
    with far.piece(0.6) as d:
        x = -0.02
        while x < 1.02:
            h = 0.05 + 0.04 * rng.random()
            d.poly([(x - 0.012, f0(x) + 0.01), (x + 0.012, f0(x) + 0.01), (x, f0(x) - h)], mixc('#3a7a50', '#9aa8c0', 0.45))
            x += 0.012 + 0.01 * rng.random()
    mid = S.L('mid')
    f = forest_floor(S, mid, 0.72, 'grass2')
    xs = sorted(S.r(0, 1) for _ in range(16))
    for x in xs:
        pine(mid, x, f(x) + 0.01, 0.7 + 0.3 * S.r(), depth=0.9)
    near = S.L('near')
    g = forest_floor(S, near, 0.88, 'grass', 0.03)
    for x in (0.06, 0.28, 0.9):
        pine(near, x + S.r(-0.03, 0.03), g(x) + 0.03, 1.7 + 0.4 * S.r())
    if v == 1:  # a campfire clearing
        with near.piece(0.7) as d:
            for a in range(6):
                d.circ(0.56 + 0.025 * math.cos(a), 0.94 + 0.008 * math.sin(a), 0.01, '#8a857c')
            d.line([(0.54, 0.94), (0.58, 0.925)], '#6a4a2a', 0.008)
            d.line([(0.54, 0.925), (0.58, 0.94)], '#6a4a2a', 0.008)
            d.poly([(0.548, 0.93), (0.56, 0.87), (0.572, 0.93)], '#f08a2e', lit=True)
            d.poly([(0.554, 0.93), (0.56, 0.895), (0.566, 0.93)], '#f6d353', lit=True)
        near.glow_circ(0.56, 0.91, 0.03)
        near.glow_circ(0.56, 0.91, 0.06)
        with near.piece(0.7) as d:
            d.rect(0.66, 0.92, 0.74, 0.95, '#8a5a3a', r=0.01)
    fg = S.L('fg')
    with fg.piece(0.8) as d:  # ferns
        for x in (0.02, 0.15, 0.78, 0.96):
            for a in range(-3, 4):
                ang = math.radians(-90 + a * 22)
                d.line([(x, 1.01), (x + math.cos(ang) * 0.06, 1.01 + math.sin(ang) * 0.1)], 'leaf' if a % 2 else 'leaf2', 0.012)
    grass_tufts(fg, 0.96, 1.0, 16, rng, s=2.2)
    weather_fx(S, ground=0.72)
    return {0: 'pine forest', 1: 'pine forest clearing with a campfire', 2: 'pine forest under mountains'}[v]


@biome('lake')
def lake(S):
    v = S.variant % 3
    hz = 0.52
    sky(S, horizon=hz)
    rng = S.rng
    far = S.L('far')
    mountains(far, hz + 0.02, 0.18, seed=S.seed, col='#8f9ccc', snowline=0.55)
    mid = S.L('mid')
    skyc = mixc(S.look.T['mid'], '#4f8fca', 0.5)
    water(mid, hz + 0.02, col=skyc, col2=shade(skyc, 1.2), seed=S.seed, bottom=0.82)
    if winter(S):
        with mid.piece(0.4) as d:
            d.rect(-0.02, hz + 0.02, 1.02, 0.82, '#dbe7f0')
    f = ridge_fn(S.seed + 3, hz + 0.04, 0.02)
    with mid.piece(0.8) as d:  # far shore with a tree line
        d.ridge(f, 'grass2', bottom=hz + 0.06)
    for k in range(18):
        x = k / 17 + S.r(-0.02, 0.02)
        pine(mid, x, f(x) + 0.015, 0.35 + 0.15 * S.r(), depth=0.6)
    if S.look.time in ('golden', 'dusk', 'night') and S.weather == 'clear':
        sx = S.look.T['sun'][0]
        reflection(mid, sx, hz + 0.07, 0.03, S.look.T['sun'][2] if S.time != 'night' else '#f6efd2')
    if v == 1:
        boat(mid, 0.62, 0.7, 1.3, col='#c5583e')
    near = S.L('near')
    g = hills(near, 0.86, 0.04, 'grass', seed=S.seed + 1)
    if v == 2:  # a wooden pier
        with near.piece(0.8) as d:
            d.poly([(0.42, 0.74), (0.5, 0.74), (0.56, 0.9), (0.36, 0.9)], '#b07a4a')
            for k in range(6):
                y = 0.75 + k * 0.025
                d.rect(0.42 - (y - 0.74) * 0.37, y, 0.5 + (y - 0.74) * 0.37, y + 0.003, '#8a5a3a')
            for x in (0.43, 0.49):
                d.line([(x, 0.74), (x, 0.79)], '#6a4a2a', 0.006)
    reeds(near, 0.0, 0.25, g(0.1) + 0.02, 1.3, rng)
    reeds(near, 0.75, 1.0, g(0.9) + 0.02, 1.3, rng)
    fg = S.L('fg')
    reeds(fg, -0.02, 0.12, 1.02, 2.4, rng)
    reeds(fg, 0.9, 1.02, 1.02, 2.4, rng)
    weather_fx(S, ground=hz + 0.1)
    return {0: 'mountain lake with a pine shore', 1: 'lake with a sailing boat', 2: 'lake with a wooden pier and reeds'}[v]


@biome('sea_coast')
def sea_coast(S):
    v = S.variant % 3
    hz = 0.55
    sky(S, horizon=hz)
    rng = S.rng
    far = S.L('far')
    seac = '#3f7fbf'
    water(far, hz, col=mixc(seac, S.look.T['bot'], 0.25), col2='#6aa6dc', seed=S.seed, bottom=0.75)
    ship(far, S.r(0.15, 0.45), hz + 0.02, 0.45, rng=rng)
    if S.look.time in ('golden', 'dusk', 'night') and S.weather == 'clear':
        reflection(far, S.look.T['sun'][0], hz + 0.005, 0.04, S.look.T['sun'][2] if S.time != 'night' else '#f6efd2', n=10)
    mid = S.L('mid')
    if v != 2:  # a cliff with the lighthouse
        with mid.piece(0.9) as d:
            pts = [(0.62, 0.8), (0.66, 0.6), (0.72, 0.56), (0.86, 0.54), (0.98, 0.56), (1.03, 0.58), (1.03, 0.82)]
            d.poly(pts, '#a89a88')
            d.poly([(0.66, 0.6), (0.72, 0.55), (0.86, 0.53), (0.98, 0.55), (1.03, 0.57), (1.03, 0.6), (0.7, 0.62)], 'grass2')
        lighthouse(mid, 0.84, 0.56, 1.2)
    else:
        boat(mid, 0.7, 0.7, 1.3)
    with mid.piece(0.5) as d:
        d.rect(-0.02, 0.72, 1.02, 0.8, '#5c9bd6')
        for k in range(12):
            x = k / 11
            d.ell(x, 0.79, 0.06, 0.012, '#f3f7fa')
    near = S.L('near')
    g = ridge_fn(S.seed, 0.8, 0.02)
    with near.piece(0.6) as d:
        d.ridge(g, '#f1dfae')
    if v == 1:
        with near.piece(0.8) as d:  # beach umbrella and towel
            d.line([(0.3, 0.92), (0.33, 0.72)], '#8a5a3a', 0.006)
            d.pie(0.33, 0.74, 0.1, 180, 360, '#e05a5a')
            d.pie(0.33, 0.74, 0.1, 200, 230, '#f6f3ea')
            d.pie(0.33, 0.74, 0.1, 260, 290, '#f6f3ea')
            d.pie(0.33, 0.74, 0.1, 320, 350, '#f6f3ea')
            d.rect(0.38, 0.9, 0.5, 0.93, '#3f7fbf', r=0.006)
    with near.piece(0.6) as d:  # shells and pebbles
        for k in range(14):
            d.ell(S.r(0, 1), S.r(0.86, 0.98), 0.006, 0.004, S.pick(['#f6e7d8', '#e9c8b0', '#c9c1b0']))
    fg = S.L('fg')
    with fg.piece() as d:
        rf = ridge_fn(S.seed + 2, 0.93, 0.05, freqs=(1.4, 3.3, 7.0))
        d.ridge(lambda x: 1.03 - (1.03 - rf(x)) * min(1, max(0, (x - 0.55) / 0.2)) ** 0.7, '#efd9a2')
    with fg.piece(0.7) as d:  # dune grass
        for k in range(20):
            x = S.r(0.68, 1.0)
            d.line([(x, 1.0), (x + S.r(-0.02, 0.02), 0.9 + S.r(0, 0.05))], '#9aa85a', 0.004)
    weather_fx(S, ground=0.7)
    return {0: 'sea coast with a lighthouse on a cliff', 1: 'beach with an umbrella and a lighthouse', 2: 'sandy beach with a sailing boat'}[v]


# ---------------------------------------------------------------- country

@biome('village')
def village(S):
    v = S.variant % 3
    sky(S, horizon=0.58)
    rng = S.rng
    far = S.L('far')
    hills(far, 0.58, 0.07, mixc('#8fb07a', '#a9b4c8', 0.35) if not winter(S) else '#e0e6ee', seed=S.seed)
    mid = S.L('mid')
    f = hills(mid, 0.7, 0.04, 'grass2', seed=S.seed + 1)
    cols = ['#f28b6b', '#f6c453', '#8fd3c8', '#b99be0', '#f2a0b8', '#9ccf7a', '#f4b07a', '#7fb6e8', '#f3ead6']
    xs = [0.08 + k * 0.17 + S.r(-0.03, 0.03) for k in range(6)]
    for i, x in enumerate(xs):
        if i % 2 == 1 or v == 2:
            round_tree(mid, x + 0.07, f(x + 0.07) + 0.02, 0.6, rng=rng)
        house(mid, x, f(x) + 0.02, 0.85 + 0.2 * S.r(), col=S.pick(cols), roof=S.pick(['#a34a3a', '#3f6f8f', '#6a8a4a', '#8a5a3a']), rng=rng)
    near = S.L('near')
    g = hills(near, 0.85, 0.03, 'grass', seed=S.seed + 2)
    with near.piece(0.5) as d:  # a dirt road
        d.poly([(-0.02, g(0) + 0.03), (1.02, g(1) + 0.02), (1.02, g(1) + 0.07), (-0.02, g(0) + 0.08)], '#d9c08f' if not winter(S) else '#e6ecf2')
    if v == 0:
        fence(near, 0.0, 0.45, g(0.2) + 0.03, 1.3)
        well(near, 0.7, g(0.7) + 0.03, 1.5)
    elif v == 1:
        house(near, 0.78, g(0.78) + 0.03, 2.2, col='#8fd3c8', roof='#a34a3a', rng=rng)
        fence(near, 0.0, 0.55, g(0.3) + 0.03, 1.3)
    else:
        for x in (0.2, 0.55):
            round_tree(near, x, g(x) + 0.03, 1.5, rng=rng)
        cow(near, 0.8, g(0.8) + 0.06, 1.8)
    fg = S.L('fg')
    grass_tufts(fg, 0.95, 1.0, 18, rng, s=2.2)
    flowers(fg, 0.93, 0.99, 14, rng, s=1.8)
    weather_fx(S, ground=0.72)
    return {0: 'village street with a well and a fence', 1: 'village with a cottage close up', 2: 'village with trees and a cow'}[v]


@biome('farm')
def farm(S):
    v = S.variant % 3
    sky(S, horizon=0.56)
    rng = S.rng
    far = S.L('far')
    f0 = hills(far, 0.56, 0.06, mixc('#8fb07a', '#a9b4c8', 0.35) if not winter(S) else '#e0e6ee', seed=S.seed)
    mid = S.L('mid')
    f = hills(mid, 0.68, 0.05, 'field', seed=S.seed + 1, freqs=(0.8, 1.9, 3.0))
    with mid.piece(0.4) as d:  # field furrows
        for k in range(7):
            y0 = 0.7 + k * 0.025
            d.line([(x, f(x) + 0.02 + k * 0.025) for x in np.linspace(-0.02, 1.02, 40)], shade('#d8b450', 0.9) if not winter(S) else '#dfe6ee', 0.004)
    barn(mid, 0.68, f(0.68) + 0.03, 1.2)
    silo(mid, 0.8, f(0.8) + 0.03, 1.1)
    near = S.L('near')
    g = hills(near, 0.86, 0.03, 'grass', seed=S.seed + 2)
    fence(near, -0.02, 1.02, g(0.5) + 0.02, 1.2)
    if v == 0:
        for x in (0.2, 0.32, 0.5):
            haystack(near, x, g(x) + 0.05, 1.4)
    elif v == 1:
        for x, fc in ((0.25, 1), (0.42, -1), (0.6, 1)):
            cow(near, x, g(x) + 0.08, 1.7, face=fc)
    else:
        with near.piece(0.9) as d:  # a tractor
            d.rect(0.3, 0.82, 0.42, 0.88, '#e05a5a', r=0.008)
            d.rect(0.38, 0.77, 0.43, 0.83, '#e05a5a', r=0.006)
            d.rect(0.385, 0.78, 0.425, 0.81, '#cfe6f2')
            d.circ(0.32, 0.89, 0.03, '#2e2e36')
            d.circ(0.32, 0.89, 0.012, '#f6c453')
            d.circ(0.41, 0.9, 0.02, '#2e2e36')
            d.circ(0.41, 0.9, 0.008, '#f6c453')
            d.line([(0.33, 0.82), (0.33, 0.79)], '#3a3a40', 0.006)
        haystack(near, 0.7, g(0.7) + 0.05, 1.5)
    fg = S.L('fg')
    grass_tufts(fg, 0.95, 1.0, 20, rng, s=2.2)
    weather_fx(S, ground=0.7)
    return {0: 'farm with a barn, silo and haystacks', 1: 'farm pasture with cows', 2: 'farm with a tractor and a barn'}[v]


# ---------------------------------------------------------------- cities

def skyline(L, base, rng, hmin, hmax, wmin=0.04, wmax=0.09, cols=None, tall_share=0.5):
    x = -0.03
    items = []
    cols = cols or ['#8a94b0', '#9aa2bc', '#7d88a8', '#a3a9c0']
    while x < 1.03:
        w = wmin + (wmax - wmin) * rng.random()
        h = hmin + (hmax - hmin) * (rng.random() if rng.random() < tall_share else rng.random() * 0.4)
        items.append((x, w, h))
        x += w + 0.003
    for x, w, h in sorted(items, key=lambda t: -t[2]):
        tower(L, x, x + w, base, h, cols[int(rng.integers(len(cols)))], rng, top=['flat', 'step', 'spire', 'slant', 'round', 'flat'][int(rng.integers(6))])


@biome('downtown')
def downtown(S):
    """Big city downtown: glass towers, avenue, cars; best at dusk and night."""
    v = S.variant % 3
    sky(S, horizon=0.45, cloud_y=(0.04, 0.16))
    rng = S.rng
    far = S.L('far')
    skyline(far, 0.62, rng, 0.2, 0.5, cols=['#7f8aa8', '#8f97b5', '#737e9e'])
    mid = S.L('mid')
    skyline(mid, 0.72, rng, 0.25, 0.62, 0.07, 0.13, cols=['#6f86a8', '#5f6f8f', '#8a9ab8', '#a0a6b8', '#7aa0b8'], tall_share=0.7)
    near = S.L('near')
    with near.piece(0.5) as d:
        d.rect(-0.02, 0.72, 1.02, 1.02, '#5a5a66')
        d.rect(-0.02, 0.72, 1.02, 0.76, '#9a968c')
        for k in range(10):
            d.rect(k * 0.11, 0.86, k * 0.11 + 0.06, 0.87, '#f2f2e0')
    for k in range(5):
        lamp_post(near, 0.06 + k * 0.22, 0.76, 1.3)
    cs = ['#e05a5a', '#f2f2f2', '#3f7fbf', '#2e2e36', '#f6c453', '#7f8a96']
    for k in range(4 if v != 1 else 2):
        car(near, S.r(0.02, 0.98), 0.84 if k % 2 else 0.93, 1.7, col=S.pick(cs), face=1 if k % 2 else -1)
    if v == 1:
        bus(near, 0.5, 0.92, 1.6, col='#3f8f5a', rng=rng)
    fg = S.L('fg')
    if v == 2:  # shop fronts on the left edge
        with fg.piece() as d:
            d.rect(-0.02, 0.0, 0.16, 1.02, '#5f5a66')
            d.rect(0.16, 0.0, 0.175, 1.02, '#4a4652')
        on = S.look.lit_share > 0.4
        with fg.piece(0.6) as d:
            d.rect(0.015, 0.56, 0.145, 0.88, '#ffe2a0' if on else '#9fc6dc', lit=on)
            if on:
                fg.glow_rect(0.015, 0.56, 0.145, 0.88)
            d.rect(0.0, 0.48, 0.16, 0.54, '#c0443a')
            for k in range(5):  # striped awning edge
                d.circ(0.016 + k * 0.032, 0.54, 0.016, '#c0443a' if k % 2 else '#f3efe6')
        with fg.piece(0.5) as d:  # window bars, a shelf with goods, a plant
            d.rect(0.015, 0.555, 0.145, 0.565, '#3a3640')
            d.rect(0.076, 0.56, 0.084, 0.88, '#3a3640')
            d.rect(0.015, 0.875, 0.145, 0.89, '#3a3640')
            d.rect(0.02, 0.76, 0.14, 0.77, '#6a4a3a')
            for k in range(6):
                d.rect(0.025 + k * 0.019, 0.72, 0.038 + k * 0.019, 0.76, ['#e05a5a', '#3f7fbf', '#6fb850', '#f6c453'][k % 4], r=0.003)
            d.circ(0.05, 0.83, 0.025, '#4f9e48')
            d.rect(0.04, 0.84, 0.06, 0.875, '#c5583e')
    else:
        with fg.piece() as d:
            d.rect(-0.02, 0.97, 1.02, 1.02, '#9a968c')
    weather_fx(S, ground=0.75)
    return {0: 'big city downtown with towers and traffic', 1: 'downtown avenue with a bus', 2: 'downtown street with a lit shop front'}[v]


@biome('suburb')
def suburb(S):
    v = S.variant % 3
    sky(S, horizon=0.58)
    rng = S.rng
    far = S.L('far')
    f0 = hills(far, 0.6, 0.04, mixc('#7fa66a', '#a9b4c8', 0.4) if not winter(S) else '#dfe5ec', seed=S.seed)
    with far.piece(0.6) as d:
        x = -0.02
        while x < 1.02:
            r = 0.02 + 0.015 * rng.random()
            d.ell(x, f0(x) - r * 0.4, r * 1.4, r * 1.2, mixc('#5f8f50', '#a9b4c8', 0.4) if not winter(S) else '#c9c4cc')
            x += 0.03 + 0.03 * rng.random()
    mid = S.L('mid')
    with mid.piece(0.5) as d:
        d.rect(-0.02, 0.7, 1.02, 1.02, 'grass')
    cols = ['#f3ead6', '#d9e6f0', '#f6e0c4', '#e6d6e8', '#e0ecd8']
    for k in range(4):
        x = 0.12 + k * 0.25 + S.r(-0.02, 0.02)
        house(mid, x, 0.71, 1.25, col=S.pick(cols), roof=S.pick(['#5a6a7a', '#8a5a3a', '#a34a3a', '#4a5a4a']), rng=rng)
        bush(mid, x + 0.1, 0.72, 0.8)
    near = S.L('near')
    with near.piece(0.5) as d:
        d.rect(-0.02, 0.78, 1.02, 0.86, '#c9c4bc')
        d.rect(-0.02, 0.86, 1.02, 1.02, '#6a6a74')
        for k in range(10):
            d.rect(k * 0.11, 0.94, k * 0.11 + 0.06, 0.948, '#f2f2e0')
    for k in range(3):
        round_tree(near, 0.05 + k * 0.4 + S.r(0, 0.05), 0.8, 1.5, rng=rng)
    if v != 2:
        car(near, 0.62, 0.84, 1.6, col=S.pick(['#3f7fbf', '#e05a5a', '#f2f2f2']), face=-1)
    with near.piece(0.7) as d:  # mailbox
        d.line([(0.32, 0.82), (0.32, 0.76)], '#6a5a4a', 0.005)
        d.rect(0.31, 0.74, 0.34, 0.765, '#3f7fbf', r=0.006)
    fg = S.L('fg')
    with fg.piece() as d:
        d.rect(-0.02, 0.975, 1.02, 1.02, '#9a968c')
    if v == 1:
        fence(fg, 0.6, 1.02, 1.0, 2.0, col='#f6f3ea')
    weather_fx(S, ground=0.72)
    return {0: 'suburb street with cottages and lawns', 1: 'suburb with a white picket fence', 2: 'quiet suburb street with trees'}[v]


@biome('highway')
def highway(S):
    v = S.variant % 3
    hz = 0.56
    sky(S, horizon=hz)
    rng = S.rng
    far = S.L('far')
    if v == 0:
        mountains(far, hz + 0.02, 0.22, seed=S.seed, col='#8f9ccc')
    else:
        hills(far, hz + 0.02, 0.06, mixc('#8fb07a', '#a9b4c8', 0.4) if not winter(S) else '#dfe5ec', seed=S.seed)
    mid = S.L('mid')
    f = hills(mid, 0.66, 0.03, 'grass2' if v != 2 else 'steppe', seed=S.seed + 1)
    pole_line(mid, 0.66, 0.8, rng)
    near = S.L('near')
    with near.piece(0.5) as d:
        d.rect(-0.02, 0.7, 1.02, 1.02, '#5f5f6a')
        d.rect(-0.02, 0.7, 1.02, 0.715, '#d8d0c0')
        d.rect(-0.02, 0.84, 1.02, 0.85, '#f6d353')
        for lane in (0.77, 0.92):
            for k in range(8):
                d.rect(k * 0.14 + 0.02, lane, k * 0.14 + 0.1, lane + 0.007, '#f2f2f2')
    with near.piece(0.7) as d:  # guard rail
        d.rect(-0.02, 0.67, 1.02, 0.685, '#b9bec6')
        for k in range(16):
            d.rect(k * 0.07, 0.685, k * 0.07 + 0.006, 0.71, '#8a8f99')
    sign(near, 0.82, 0.69, 1.3, w=0.16)
    cs = ['#e05a5a', '#f2f2f2', '#3f7fbf', '#2e2e36', '#f6c453', '#7f8a96', '#6fb850']
    for k, x in enumerate((0.06, 0.3, 0.52, 0.72, 0.9)):
        if v == 1 and k % 2 and 0.35 < x < 0.7:
            continue
        car(near, x + S.r(-0.03, 0.03), 0.8 if k % 2 else 0.95, 1.5 + 0.3 * (k % 2 == 0), col=S.pick(cs), face=1 if k % 2 else -1)
    if v == 1:
        with near.piece(0.9) as d:  # a truck
            d.rect(0.4, 0.69, 0.6, 0.79, '#e9e4d8', r=0.006)
            d.rect(0.6, 0.72, 0.66, 0.79, '#3f7fbf', r=0.01)
            d.rect(0.615, 0.73, 0.65, 0.755, '#cfe6f2')
            for x in (0.44, 0.48, 0.63):
                d.circ(x, 0.795, 0.016, '#2e2e36')
    fg = S.L('fg')
    with fg.piece() as d:
        d.ridge(ridge_fn(S.seed + 4, 1.0, 0.03), 'grass2' if v != 2 else 'steppe2', x0=-0.03, x1=0.3)
    grass_tufts(fg, 0.97, 1.0, 8, rng, s=2)
    weather_fx(S, ground=0.7)
    return {0: 'highway under mountains', 1: 'highway with a truck and a road sign', 2: 'steppe highway with power lines'}[v]


@biome('railway')
def railway(S):
    v = S.variant % 3
    hz = 0.58
    sky(S, horizon=hz)
    rng = S.rng
    far = S.L('far')
    if v == 1:
        mountains(far, hz + 0.02, 0.24, seed=S.seed)
    else:
        hills(far, hz + 0.02, 0.06, mixc('#8fb07a', '#a9b4c8', 0.4) if not winter(S) else '#dfe5ec', seed=S.seed)
    mid = S.L('mid')
    hills(mid, 0.68, 0.025, 'grass2' if v != 2 else 'steppe', seed=S.seed + 1)
    with mid.piece(0.7) as d:  # embankment and rails
        d.poly([(-0.02, 0.7), (1.02, 0.7), (1.02, 0.66), (-0.02, 0.66)], '#a89a88')
        d.rect(-0.02, 0.655, 1.02, 0.662, '#6a6a72')
    pole_line(mid, 0.66, 0.85, rng)
    if v != 2:
        train(mid, S.r(-0.1, 0.2), 0.658, 1.1, 5, rng, col=S.pick(['#3f8f5a', '#3f6fa8', '#8a5a9a']))
    near = S.L('near')
    g = hills(near, 0.82, 0.02, 'grass', seed=S.seed + 2)
    with near.piece(0.6) as d:  # near track with sleepers
        d.rect(-0.02, 0.86, 1.02, 0.95, '#a89a88')
        for k in range(30):
            d.rect(k * 0.036, 0.875, k * 0.036 + 0.02, 0.94, '#7a5a3a')
        d.rect(-0.02, 0.88, 1.02, 0.888, '#8a8f99')
        d.rect(-0.02, 0.925, 1.02, 0.933, '#8a8f99')
    if v == 2:
        with near.piece(0.9) as d:  # a small station shelter and a signal
            d.rect(0.6, 0.66, 0.8, 0.8, '#e9dcc0')
            d.poly([(0.58, 0.66), (0.82, 0.66), (0.78, 0.62), (0.62, 0.62)], '#a34a3a')
            d.rect(0.67, 0.72, 0.71, 0.8, '#7a4a2a')
            d.line([(0.9, 0.86), (0.9, 0.62)], '#4a4a58', 0.006)
            d.rect(0.885, 0.6, 0.915, 0.67, '#2e2e36', r=0.008)
            d.circ(0.9, 0.618, 0.008, '#e05a5a', lit=S.look.lit_share > 0.2)
            d.circ(0.9, 0.65, 0.008, '#6fb850')
        with near.piece(0.6) as d:
            d.window(0.74, 0.69, 0.78, 0.74, rng=rng)
    fg = S.L('fg')
    grass_tufts(fg, 0.97, 1.0, 16, rng, s=2.0)
    weather_fx(S, ground=0.7)
    return {0: 'railway with a passing train', 1: 'mountain railway with a train', 2: 'country railway halt with a signal'}[v]


@biome('port')
def port(S):
    v = S.variant % 3
    hz = 0.6
    sky(S, horizon=hz)
    rng = S.rng
    far = S.L('far')
    water(far, hz, col='#4a7fb0', col2='#6aa6dc', seed=S.seed, bottom=0.8)
    ship(far, 0.2, hz + 0.01, 0.9, rng=rng)
    mid = S.L('mid')
    with mid.piece(0.6) as d:
        d.rect(-0.02, 0.66, 1.02, 0.7, '#9a968c')
    with mid.piece(0.8) as d:  # a warehouse on the quay
        d.rect(0.02, 0.56, 0.3, 0.66, '#b9a48a')
        d.poly([(0.01, 0.56), (0.31, 0.56), (0.25, 0.52), (0.07, 0.52)], '#8a6a5a')
        for k in range(3):
            d.rect(0.05 + k * 0.09, 0.6, 0.11 + k * 0.09, 0.66, '#7a6a5a')
    cs = ['#3f7fbf', '#e9b443', '#6fb850', '#e05a5a', '#9a7ac8', '#e9e4d8']
    heights = [int(S.r(2, 6)) for _ in range(9)]
    with mid.piece(0.8) as d:  # container stacks
        for k in range(9):
            x = 0.38 + k * 0.07
            for j in range(heights[k]):
                c = S.pick(cs)
                d.rect(x, 0.66 - (j + 1) * 0.042, x + 0.066, 0.66 - j * 0.042 - 0.004, c, r=0.002)
    with mid.piece(0.4) as d:  # container ribs
        for k in range(9):
            x = 0.38 + k * 0.07
            for i in range(1, 6):
                d.rect(x + i * 0.011, 0.66 - heights[k] * 0.042 + 0.004, x + i * 0.011 + 0.002, 0.656, (0, 0, 0, 40))
    for x in (0.35, 0.75):
        crane(mid, x, 0.66, 0.85, col=S.pick(['#e9b443', '#e05a5a']), face=-1 if x > 0.5 else 1)
    near = S.L('near')
    water(near, 0.74, col='#3f6f9f', col2='#5c8fc0', seed=S.seed + 1, bottom=0.85)
    if v in (0, 1):
        ship(near, 0.45 if v == 1 else 0.6, 0.8, 1.5, hull='#2e4a6a' if v == 1 else '#c5483e', rng=rng)
    with near.piece(0.7) as d:  # the pier in front
        d.rect(-0.02, 0.84, 1.02, 1.02, '#8f8a82')
        d.rect(-0.02, 0.84, 1.02, 0.855, '#e0c040')
        for k in range(4):
            x = 0.12 + k * 0.26
            d.rect(x - 0.012, 0.82, x + 0.012, 0.85, '#3a3a44', r=0.006)
            d.ell(x, 0.82, 0.016, 0.006, '#3a3a44')
    if v == 2:
        with near.piece(0.9) as d:
            d.rect(0.55, 0.78, 0.8, 0.86, '#e05a5a')
            d.rect(0.81, 0.73, 0.98, 0.86, '#3f7fbf')
    fg = S.L('fg')
    with fg.piece(0.8) as d:  # coiled rope and bollard
        d.ell(0.08, 0.97, 0.05, 0.02, '#c9a868')
        d.ell(0.08, 0.96, 0.034, 0.012, '#b08a50')
    weather_fx(S, ground=0.7)
    return {0: 'port with cranes and container stacks', 1: 'port with a ship at the quay', 2: 'container port quay'}[v]


@biome('park')
def park(S):
    v = S.variant % 3
    sky(S, horizon=0.55)
    rng = S.rng
    far = S.L('far')
    skyline(far, 0.6, rng, 0.08, 0.28, cols=['#a3aac4', '#b2b8cc', '#9aa2bc'])
    mid = S.L('mid')
    f = hills(mid, 0.66, 0.025, 'grass2', seed=S.seed)
    for k in range(9):
        x = k / 8 + S.r(-0.03, 0.03)
        (round_tree if k % 3 else pine)(mid, x, f(x) + 0.02, 0.9, **({'rng': rng} if k % 3 else {}))
    if v == 1:  # pond with a fountain
        with mid.piece(0.6) as d:
            d.ell(0.5, 0.74, 0.2, 0.035, '#5c9bd6' if not winter(S) else '#d6e4ee')
        with mid.piece(0.8) as d:
            d.ell(0.5, 0.73, 0.04, 0.01, '#c9c1b0')
            d.rect(0.495, 0.66, 0.505, 0.73, '#c9c1b0')
            if not winter(S):
                for a in (-1, -0.5, 0.5, 1):
                    d.line([(0.5, 0.66), (0.5 + a * 0.02, 0.645), (0.5 + a * 0.035, 0.7)], '#cfe6f2', 0.004)
    near = S.L('near')
    g = hills(near, 0.8, 0.02, 'grass', seed=S.seed + 1)
    with near.piece(0.5) as d:  # a curving path
        d.poly([(-0.02, 0.84), (0.3, 0.82), (0.7, 0.84), (1.02, 0.83), (1.02, 0.92), (0.6, 0.93), (0.3, 0.91), (-0.02, 0.93)], '#e6cf9e' if not winter(S) else '#e6ecf2')
    bench(near, 0.35, 0.84, 1.5)
    bench(near, 0.72, 0.85, 1.5)
    for x in (0.1, 0.55, 0.9):
        lamp_post(near, x, 0.84, 1.4)
    fg = S.L('fg')
    bush(fg, 0.05, 1.02, 2.6, flowers='#f2a0b8' if S.season in ('spring', 'summer') else None)
    bush(fg, 0.97, 1.02, 2.2)
    flowers(fg, 0.95, 1.0, 16, rng, s=1.8)
    if v == 2:
        round_tree(fg, 0.85, 1.05, 3.4, rng=rng)
    weather_fx(S, ground=0.7)
    return {0: 'city park with benches and lamp posts', 1: 'park pond with a fountain', 2: 'park path under a big tree'}[v]


@biome('school_yard')
def school_yard(S):
    v = S.variant % 3
    sky(S, horizon=0.55)
    rng = S.rng
    far = S.L('far')
    for k in range(4):
        x = -0.04 + k * 0.28
        block(far, x, x + 0.2, 0.46, 9, S.pick(['#d6d2c8', '#c9cdd2']), rng, fh=0.03, balcony=False)
    mid = S.L('mid')
    with mid.piece(0.9) as d:  # a three-storey school
        d.rect(0.1, 0.38, 0.9, 0.66, '#e9c88a' if v != 1 else '#d9dfe6')
        d.rect(0.08, 0.36, 0.92, 0.385, '#b05a44')
        d.rect(0.42, 0.3, 0.58, 0.66, '#e0bc7a' if v != 1 else '#cad2da')
        d.rect(0.41, 0.285, 0.59, 0.31, '#b05a44')
        d.rect(0.46, 0.57, 0.54, 0.66, '#7a4a2a')
        d.circ(0.5, 0.34, 0.025, '#f6f3ea')
    with mid.piece(0.5) as d:
        for row in range(3):
            for k in range(14):
                x = 0.13 + k * 0.055
                if 0.4 < x < 0.58:
                    continue
                d.window(x, 0.41 + row * 0.08, x + 0.03, 0.46 + row * 0.08, rng=rng)
        d.line([(0.5, 0.34), (0.51, 0.325)], '#3a3a40', 0.003)
        d.line([(0.5, 0.34), (0.5, 0.32)], '#3a3a40', 0.003)
    near = S.L('near')
    with near.piece(0.5) as d:
        d.rect(-0.02, 0.66, 1.02, 1.02, '#b9b2a4' if v != 2 else '#c96a4a')
        if v == 2:  # sports ground with lines
            d.rect(0.1, 0.72, 0.9, 0.725, '#f2f2f2')
            d.rect(0.1, 0.95, 0.9, 0.955, '#f2f2f2')
            d.ell(0.5, 0.835, 0.08, 0.04, '#c96a4a')
    if v == 2:
        with near.piece(0.8) as d:
            for x0, fc in ((0.12, 1), (0.88, -1)):  # goals
                d.line([(x0, 0.86), (x0, 0.74), (x0 + fc * 0.06, 0.74), (x0 + fc * 0.06, 0.86)], '#f2f2f2', 0.006)
    else:
        with near.piece(0.8) as d:  # basketball hoop
            d.line([(0.82, 0.88), (0.82, 0.62)], '#4a4a58', 0.008)
            d.rect(0.78, 0.58, 0.86, 0.64, '#f2f2f2')
            d.ell(0.82, 0.645, 0.022, 0.006, '#e05a5a')
        bench(near, 0.3, 0.84, 1.4, col='#3f7fbf')
    fence(near, -0.02, 1.02, 0.7, 1.0, col='#7f9a5a')
    fg = S.L('fg')
    for x in (0.0, 1.0):
        round_tree(fg, x, 1.04, 3.2, rng=rng)
    weather_fx(S, ground=0.7)
    return {0: 'school yard with a hoop and a bench', 1: 'grey school building and yard', 2: 'school sports ground with goals'}[v]


@biome('construction')
def construction(S):
    v = S.variant % 3
    sky(S, horizon=0.55)
    rng = S.rng
    far = S.L('far')
    skyline(far, 0.6, rng, 0.08, 0.3, cols=['#a3aac4', '#b2b8cc'])
    mid = S.L('mid')
    with mid.piece(0.8) as d:  # a building skeleton
        x0, x1, y = 0.35, 0.78, 0.7
        for f in range(8 if v != 1 else 5):
            yy = y - (f + 1) * 0.055
            d.rect(x0, yy, x1, yy + 0.01, '#a9a39a')
        for k in range(7):
            x = x0 + k * (x1 - x0) / 6
            d.rect(x - 0.005, y - (8 if v != 1 else 5) * 0.055, x + 0.005, y, '#a9a39a')
    with mid.piece(0.6) as d:
        d.rect(0.35, 0.56, 0.6, 0.7, '#cfc6b4')
        for k in range(4):
            d.window(0.37 + k * 0.06, 0.6, 0.4 + k * 0.06, 0.64, force=False)
    crane(mid, 0.25, 0.7, 1.15, face=1)
    near = S.L('near')
    with near.piece(0.5) as d:
        d.rect(-0.02, 0.7, 1.02, 1.02, '#c9a87a')
        d.ell(0.2, 0.86, 0.14, 0.06, '#d9b98a')
    with near.piece(0.9) as d:  # sand pile and excavator
        d.pie(0.2, 0.86, 0.12, 180, 360, '#e3c68a')
        if v != 2:
            d.rect(0.55, 0.8, 0.72, 0.88, '#f2b233', r=0.008)
            d.rect(0.62, 0.73, 0.7, 0.81, '#f2b233', r=0.006)
            d.rect(0.63, 0.745, 0.69, 0.78, '#cfe6f2')
            d.rect(0.53, 0.875, 0.74, 0.91, '#3a3a40', r=0.016)
            d.line([(0.58, 0.8), (0.48, 0.7), (0.43, 0.82)], '#e0a22a', 0.012)
            d.poly([(0.41, 0.82), (0.46, 0.82), (0.44, 0.86)], '#6a6a72')
    with near.piece(0.7) as d:  # barrier panels
        for k in range(5):
            x = 0.78 + k * 0.05
            d.rect(x, 0.78, x + 0.045, 0.86, '#e05a5a' if k % 2 else '#f2f2f2')
    fg = S.L('fg')
    with fg.piece() as d:  # cones
        for x in (0.1, 0.4, 0.9):
            d.poly([(x - 0.025, 1.0), (x + 0.025, 1.0), (x + 0.006, 0.92), (x - 0.006, 0.92)], '#f08a2e')
            d.rect(x - 0.018, 0.955, x + 0.018, 0.968, '#f6f3ea')
            d.rect(x - 0.035, 0.995, x + 0.035, 1.02, '#f08a2e')
    weather_fx(S, ground=0.7)
    return {0: 'construction site with a crane and an excavator', 1: 'construction site, low frame and a crane', 2: 'building frame and a sand pile'}[v]


# ---------------------------------------------------------------- space and far places

def space_sky(S, tint=('#0a0a26', '#1c1450', '#2a1f5a'), nebula=True):
    L = sky_gradient(S, cols=[hx(c) for c in tint], horizon=1.0)
    rng = S.rng
    fd = L.flat()
    for _ in range(420):
        fd.circ(rng.random(), rng.random(), 0.001 + rng.random() ** 3 * 0.003, '#fff6dc', lit=True)
    if nebula:  # soft nebula clouds, flat (no felt edge), blurred
        neb = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        nd = ImageDraw.Draw(neb)
        for _ in range(4):
            x, y = rng.random(), rng.random() * 0.8
            c = [(120, 70, 200), (170, 70, 150), (60, 110, 200)][int(rng.integers(3))]
            for k in range(6):
                cx, cy = (x + rng.random() * 0.12) * W, (y + rng.random() * 0.08) * H
                rx, ry = (0.08 + rng.random() * 0.08) * H, (0.04 + rng.random() * 0.05) * H
                nd.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=c + (60,))
        neb = neb.filter(ImageFilter.GaussianBlur(40))
        L.base = Image.alpha_composite(L.base, neb)
    with L.piece(0.4) as d:
        for _ in range(16):
            x, y, r = rng.random(), rng.random(), 0.006 + rng.random() * 0.004
            d.poly([(x + math.cos(a * math.pi / 5 - math.pi / 2) * (r if a % 2 == 0 else r * 0.42) / AR,
                     y + math.sin(a * math.pi / 5 - math.pi / 2) * (r if a % 2 == 0 else r * 0.42)) for a in range(10)], '#fff3c4', lit=True)
    return L


def planet_ball(L, x, y, r, col, ring=None, bands=None, craters=False):
    if ring:
        with L.piece(0.6) as d:
            d.ell(x, y, r * 1.9, r * 0.42, ring, lit=True)
            d.ell(x, y, r * 1.45, r * 0.25, (0, 0, 0, 0))
    with L.piece(1.0) as d:
        d.circ(x, y, r, col, lit=True)
        if bands:
            for k, c in enumerate(bands):
                yy = y - r * 0.6 + k * r * 0.4
                hw = math.sqrt(max(r * r - (yy - y) ** 2, 0))
                d.ell(x, yy, hw * 0.98, r * 0.08, c, lit=True)
        if craters:
            for dx, dy, rr in ((-0.3, -0.2, 0.18), (0.25, 0.3, 0.13), (0.1, -0.4, 0.1)):
                d.circ(x + dx * r / AR, y + dy * r, rr * r, shade(col, 0.85), lit=True)
        pass

    if ring:
        with L.piece(0.5) as d:
            pts = [(x + r * 1.9 * math.cos(a) / AR, y + r * 0.42 * math.sin(a)) for a in np.linspace(0, math.pi, 30)]
            inn = [(x + r * 1.45 * math.cos(a) / AR, y + r * 0.25 * math.sin(a)) for a in np.linspace(math.pi, 0, 30)]
            d.poly(pts + inn, ring, lit=True)


@biome('space')
def space(S):
    v = S.variant % 3
    space_sky(S)
    rng = S.rng
    far = S.L('far')
    for _ in range(3):
        planet_ball(far, S.r(0.05, 0.95), S.r(0.1, 0.5), S.r(0.02, 0.05), S.pick(['#c98a6a', '#8ab0d0', '#d0b0e0', '#e0c080']))
    mid = S.L('mid')
    if v == 0:
        planet_ball(mid, 0.7, 0.42, 0.22, '#e0a86a', ring='#d9c08a', bands=['#d08a5a', '#e9c08a', '#c97a4a'])
    elif v == 1:
        planet_ball(mid, 0.3, 0.5, 0.26, '#4a86c8', bands=None)
        with mid.piece(0.7) as d:
            for dx, dy, rr in ((-0.08, -0.08, 0.08), (0.05, 0.06, 0.09), (-0.02, 0.15, 0.05)):
                d.ell(0.3 + dx, 0.5 + dy, rr, rr * 0.7, '#6fbf6a', lit=True)
        planet_ball(mid, 0.78, 0.2, 0.05, '#d8d8e0', craters=True)
    else:
        planet_ball(mid, 0.5, 1.15, 0.6, '#8a5ac8', bands=['#7a4ab8', '#9a6ad8'])
    near = S.L('near')
    for _ in range(6):  # asteroids
        x, y, r = S.r(0, 1), S.r(0.1, 0.9), S.r(0.015, 0.04)
        with near.piece(0.9) as d:
            d.ell(x, y, r * 1.3, r, '#8a7f78', lit=True)
            d.circ(x + r * 0.3 / AR, y - r * 0.2, r * 0.3, '#6f6660', lit=True)
    fg = S.L('fg')
    with fg.piece() as d:
        d.ell(0.05, 0.95, 0.12, 0.09, '#7a706a', lit=True)
        d.circ(0.07, 0.92, 0.03, '#5f5650', lit=True)
        d.ell(0.97, 0.1, 0.08, 0.06, '#7a706a', lit=True)
    return {0: 'open space with a ringed planet', 1: 'space with a blue-green planet and a moon', 2: 'space above a purple giant planet'}[v]


@biome('moon')
def moon(S):
    v = S.variant % 3
    space_sky(S, tint=('#05050f', '#0c0c22', '#16163a'), nebula=False)
    S.look.T = dict(S.look.T, tint=(0.92, 0.92, 0.96), haze='#20203a')  # sunlit ground under a black sky
    S.look.haze_col = hx('#20203a')
    rng = S.rng
    far = S.L('far')
    planet_ball(far, 0.75, 0.22, 0.09, '#4a86c8')
    with far.piece(0.7) as d:
        d.ell(0.73, 0.2, 0.04, 0.03, '#6fbf6a', lit=True)
        d.ell(0.78, 0.25, 0.03, 0.02, '#f6f6f6', lit=True)
    hills(far, 0.62, 0.08, '#8a8a98', seed=S.seed)
    mid = S.L('mid')
    f = hills(mid, 0.72, 0.05, '#a8a8b6', seed=S.seed + 1)
    with mid.piece(0.5) as d:
        for _ in range(6):
            x = S.r(0, 1)
            d.ell(x, f(x) + 0.05, 0.05, 0.012, '#8f8f9e')
    if v == 0:  # a lander (generic)
        with mid.piece(0.9) as d:
            for a, b in ((0.4, 0.34), (0.52, 0.58)):
                d.line([(a, 0.64), (b, 0.74)], '#9a9aa6', 0.008)
                d.ell(b, 0.745, 0.022, 0.007, '#9a9aa6')
            d.rect(0.38, 0.56, 0.54, 0.66, '#d9b440', r=0.006)
            d.poly([(0.4, 0.56), (0.52, 0.56), (0.5, 0.47), (0.42, 0.47)], '#d0d0d8')
            d.rect(0.445, 0.49, 0.475, 0.52, '#3a4a6a', r=0.004)
            d.line([(0.5, 0.47), (0.53, 0.42)], '#9a9aa6', 0.003)
            d.circ(0.53, 0.42, 0.012, '#e6e6ee')
    elif v == 1:  # a dome base
        with mid.piece(0.9) as d:
            d.pie(0.6, 0.73, 0.08, 180, 360, '#e6e6ee')
            d.pie(0.72, 0.735, 0.05, 180, 360, '#e6e6ee')
            d.rect(0.63, 0.715, 0.7, 0.73, '#c9c9d4')
        with mid.piece(0.5) as d:
            d.window(0.585, 0.69, 0.615, 0.71, force=True)
    near = S.L('near')
    g = hills(near, 0.86, 0.03, '#bdbdca', seed=S.seed + 2)
    with near.piece(0.6) as d:  # craters
        for x, y, r in ((0.2, 0.92, 0.09), (0.65, 0.95, 0.12), (0.88, 0.9, 0.05)):
            d.ell(x, y, r, r * 0.25, '#9a9aaa')
            d.ell(x, y + r * 0.04, r * 0.85, r * 0.18, '#a8a8b8')
    if v == 2:
        with near.piece(0.8) as d:  # a flag pole with a plain flag
            d.line([(0.45, 0.9), (0.45, 0.72)], '#d0d0d8', 0.004)
            d.rect(0.45, 0.72, 0.5, 0.75, '#e05a5a')
            for k in range(8):  # boot prints
                d.ell(0.3 + k * 0.03, 0.95 - 0.004 * (k % 2), 0.006, 0.003, '#9a9aaa')
    fg = S.L('fg')
    rock(fg, 0.06, 1.0, 2.4, col='#9a9aa6')
    rock(fg, 0.94, 1.02, 1.8, col='#8a8a98')
    return {0: 'Moon surface with a lander and Earth in the sky', 1: 'Moon base under domes', 2: 'Moon craters with a plain flag'}[v]


@biome('mars')
def mars(S):
    v = S.variant % 3
    t = S.time
    if t == 'dusk':  # Martian sunset is blue
        cols = ('#3a3050', '#7a6a7a', '#a8b8d0')
    elif t == 'night':
        cols = ('#0e0a1a', '#22142a', '#3a2030')
    else:
        cols = ('#c98a5a', '#e0a878', '#f0c8a0')
    L = sky_gradient(S, cols=[hx(c) for c in cols], horizon=0.6)
    rng = S.rng
    if t == 'night':
        fd = L.flat()
        for _ in range(200):
            fd.circ(rng.random(), rng.random() * 0.6, 0.0012 + rng.random() ** 3 * 0.003, '#fff6dc', lit=True)
    with L.piece(0.6) as d:
        d.circ(0.2, 0.15, 0.025, '#d8d0c0', lit=True)
        d.circ(0.75, 0.3, 0.035 if t != 'night' else 0.02, '#f6efe0' if t in ('dusk', 'night') else '#fff4d8', lit=True)
    far = S.L('far')
    with far.piece(0.8) as d:  # mesas
        for x0, w, h in ((0.05, 0.25, 0.12), (0.45, 0.15, 0.08), (0.7, 0.3, 0.15)):
            d.poly([(x0, 0.62), (x0 + w * 0.15, 0.62 - h), (x0 + w * 0.85, 0.62 - h), (x0 + w, 0.62)], '#b8704a')
            d.rect(x0 + w * 0.15, 0.62 - h, x0 + w * 0.85, 0.62 - h + 0.012, '#c98a5a')
    hills(far, 0.64, 0.02, '#c07a50', seed=S.seed)
    mid = S.L('mid')
    f = dune(mid, 0.74, 0.05, '#c97a4a', S.seed)
    if v == 0:  # a rover
        with mid.piece(0.9) as d:
            d.rect(0.45, 0.66, 0.58, 0.7, '#e6e6ee', r=0.004)
            d.line([(0.55, 0.66), (0.56, 0.6)], '#9a9aa6', 0.004)
            d.rect(0.545, 0.585, 0.58, 0.605, '#d0d0d8')
            d.rect(0.46, 0.65, 0.53, 0.66, '#3a4a7a')
            for x in (0.46, 0.515, 0.57):
                d.circ(x, 0.71, 0.014, '#3a3a40')
    elif v == 1:  # a habitat
        with mid.piece(0.9) as d:
            d.pie(0.62, 0.74, 0.07, 180, 360, '#e6e6ee')
            d.rect(0.42, 0.7, 0.55, 0.74, '#d0d0d8', r=0.02)
            d.rect(0.3, 0.7, 0.4, 0.71, '#3a4a7a')
            d.line([(0.35, 0.71), (0.35, 0.74)], '#9a9aa6', 0.004)
    near = S.L('near')
    g = dune(near, 0.86, 0.04, '#d48a58', S.seed + 1)
    for _ in range(5):
        x = S.r(0, 1)
        rock(near, x, g(x) + 0.05, 1.2, col='#a85a3a')
    fg = S.L('fg')
    rock(fg, 0.08, 1.02, 3.0, col='#9a4f32')
    rock(fg, 0.9, 1.02, 2.2, col='#a85a3a')
    if S.weather == 'fog':  # a dust storm
        weather_fx(S, ground=0.7)
    return {0: 'Mars with mesas and a rover', 1: 'Mars habitat on red dunes', 2: 'red Mars desert with rocks'}[v]


@biome('underwater')
def underwater(S):
    v = S.variant % 3
    deep = S.time in ('night', 'dusk')
    cols = ('#4fb0d0', '#2f7fb0', '#1a4f80') if not deep else ('#1a4a70', '#0f2f50', '#08182e')
    L = sky_gradient(S, cols=[hx(c) for c in cols], horizon=1.0)
    rng = S.rng
    with L.piece(0.2) as d:  # light rays from the surface
        for k in range(6):
            x = S.r(0, 1)
            d.poly([(x, 0), (x + 0.04, 0), (x + 0.12, 0.8), (x + 0.05, 0.8)], (220, 245, 255, 40 if not deep else 18))
    far = S.L('far')
    hills(far, 0.7, 0.12, '#2a6a8a' if not deep else '#163a5a', seed=S.seed)
    mid = S.L('mid')
    f = hills(mid, 0.82, 0.05, '#e6d2a0' if not deep else '#7a7a7a', seed=S.seed + 1)
    for k in range(7):  # seaweed
        x = S.r(0, 1)
        with mid.piece(0.6) as d:
            pts = [(x + 0.012 * math.sin(u * 7 + k), f(x) + 0.03 - u * (0.18 + 0.1 * S.r())) for u in np.linspace(0, 1, 12)]
            d.line(pts, '#3f9a5a', 0.01)
    corals = ['#f28b6b', '#f2a0b8', '#f6c453', '#b99be0', '#e05a5a']
    for k in range(5):
        x = S.r(0, 1)
        with mid.piece(0.9) as d:
            c = S.pick(corals)
            y = f(x) + 0.04
            for a in (-0.6, -0.2, 0.2, 0.6):
                ex, ey = x + a * 0.04, y - 0.07 - 0.03 * abs(a)
                d.line([(x, y), (x + a * 0.02, y - 0.04), (ex, ey)], c, 0.012)
                d.circ(ex, ey, 0.01, c)
    near = S.L('near')
    fish_c = ['#f6c453', '#f28b6b', '#7fd3f0', '#f2a0b8', '#ffffff']
    n = 6 if v != 1 else 14
    for k in range(n):
        x, y, s = S.r(0.05, 0.95), S.r(0.15, 0.7), S.r(0.6, 1.2)
        fc = S.pick([-1, 1])
        with near.piece(0.8) as d:
            c = S.pick(fish_c)
            d.ell(x, y, 0.03 * s, 0.017 * s, c)
            d.poly([(x - fc * 0.025 * s / AR * 1.6, y), (x - fc * 0.045 * s / AR * 1.6, y - 0.015 * s), (x - fc * 0.045 * s / AR * 1.6, y + 0.015 * s)], c)
            d.circ(x + fc * 0.014 * s / AR * 1.6, y - 0.004 * s, 0.004 * s, '#1d1a18')
    if v == 2:  # a sunken chest
        with near.piece(0.9) as d:
            d.rect(0.55, 0.86, 0.68, 0.93, '#8a5a3a', r=0.006)
            d.pie(0.615, 0.865, 0.065, 180, 360, '#a06a40')
            d.rect(0.605, 0.875, 0.625, 0.9, '#f6c453')
    g = hills(near, 0.95, 0.03, '#f1dfae' if not deep else '#8a8a8a', seed=S.seed + 2)
    fg = S.L('fg')
    with fg.piece(0.5) as d:  # bubbles
        for _ in range(26):
            x = S.r(0, 1)
            d.circ(x, S.r(0, 1), S.r(0.003, 0.012), (230, 250, 255, 160))
    for x in (0.02, 0.97):
        with fg.piece() as d:
            pts = [(x + 0.02 * math.sin(u * 6), 1.02 - u * 0.5) for u in np.linspace(0, 1, 14)]
            d.line(pts, '#2f8a4a', 0.018)
    return {0: 'underwater reef with corals, seaweed and fish', 1: 'underwater with a school of fish', 2: 'sea bottom with a sunken chest'}[v]


@biome('cave')
def cave(S):
    v = S.variant % 3
    L = sky_gradient(S, cols=[hx('#2a2420'), hx('#3a302a'), hx('#4a3e34')], horizon=1.0)
    rng = S.rng
    S.look.haze_col = hx('#2a2420')
    for n in ('far', 'mid', 'near'):
        S.L(n).haze *= 0.25
    if v == 0:  # an opening to the outside
        sk = S.look.sky_cols()
        with L.piece(0.6) as d:
            pts = []
            for k in range(40):
                a = 2 * math.pi * k / 40
                rr = 0.24 * (1 + 0.12 * math.sin(a * 3 + 1) + 0.06 * math.sin(a * 7))
                pts.append((0.68 + rr * math.cos(a) / AR, 0.42 + rr * 1.1 * math.sin(a)))
            d.poly(pts, to255(sk[1]), lit=True)
            d.ell(0.68, 0.58, 0.2, 0.08, '#6fa86a', lit=False)
    far = S.L('far')
    with far.piece(0.8) as d:  # stalactites
        x = -0.02
        while x < 1.02:
            w, h = 0.02 + 0.03 * rng.random(), 0.06 + 0.16 * rng.random()
            d.poly([(x, -0.01), (x + w, -0.01), (x + w * 0.5, h)], '#5a4a3e')
            x += w * 0.8
    hills(far, 0.72, 0.06, '#4a3e34', seed=S.seed)
    mid = S.L('mid')
    f = hills(mid, 0.8, 0.04, '#5f5044', seed=S.seed + 1)
    if v == 1:  # glowing crystals
        for k in range(5):
            x = S.r(0.05, 0.95)
            with mid.piece(0.8) as d:
                c = S.pick(['#7fd3f0', '#b99be0', '#8ff0c0'])
                for a in (-0.4, 0, 0.35):
                    d.poly([(x - 0.01 + a * 0.04, f(x) + 0.03), (x + 0.01 + a * 0.04, f(x) + 0.03), (x + a * 0.06, f(x) - 0.08 + abs(a) * 0.08)], c, lit=True)
            mid.glow_circ(x, f(x) - 0.02, 0.05)
    if v == 2:  # an underground lake
        with mid.piece(0.5) as d:
            d.ell(0.5, 0.85, 0.35, 0.05, '#2f5f7a')
    near = S.L('near')
    g = hills(near, 0.9, 0.04, '#6a5a4c', seed=S.seed + 2)
    with near.piece(0.8) as d:  # a lantern
        d.line([(0.25, g(0.25) + 0.02), (0.25, g(0.25) - 0.04)], '#3a3a40', 0.003)
        d.rect(0.24, g(0.25) - 0.04, 0.26, g(0.25), '#3a3a40', r=0.003)
        d.rect(0.244, g(0.25) - 0.034, 0.256, g(0.25) - 0.006, '#ffd36e', lit=True)
    near.glow_circ(0.25, g(0.25) - 0.02, 0.03)
    near.glow_circ(0.25, g(0.25) - 0.02, 0.08)
    for x in (0.1, 0.8):
        rock(near, x, g(x) + 0.05, 2.0, col='#5a4a3e')
    fg = S.L('fg')
    with fg.piece() as d:  # rock frame
        d.poly([(-0.02, -0.02), (0.14, -0.02), (0.1, 0.2), (0.06, 0.55), (0.08, 1.02), (-0.02, 1.02)], '#2e2620')
        d.poly([(1.02, -0.02), (0.84, -0.02), (0.9, 0.3), (0.95, 0.7), (0.9, 1.02), (1.02, 1.02)], '#2e2620')
    return {0: 'cave with an opening to the sky', 1: 'cave with glowing crystals', 2: 'cave with an underground lake'}[v]


@biome('jungle')
def jungle(S):
    v = S.variant % 3
    sky(S, horizon=0.5)
    rng = S.rng
    far = S.L('far')
    f0 = hills(far, 0.55, 0.12, mixc('#3f7a4a', '#a9b4c8', 0.45), seed=S.seed, freqs=(1.6, 3.4, 7.0))
    with far.piece(0.6) as d:
        x = -0.02
        while x < 1.02:
            r = 0.025 + 0.02 * rng.random()
            d.circ(x, f0(x) - r * 0.3, r, mixc('#3a7a4a', '#a9b4c8', 0.4))
            x += 0.025 + 0.02 * rng.random()
    if v == 2:  # a waterfall
        with far.piece(0.5) as d:
            d.rect(0.46, f0(0.5) - 0.02, 0.54, 0.75, '#cfe8f4')
            for k in range(5):
                d.rect(0.47 + k * 0.014, f0(0.5), 0.474 + k * 0.014, 0.74, '#ffffff')
    mid = S.L('mid')
    f = hills(mid, 0.75, 0.03, '#4f8a3a', seed=S.seed + 1)
    for k in range(8):  # big trunks with canopies
        x = k / 7 + S.r(-0.04, 0.04)
        with mid.piece(0.8) as d:
            d.rect(x - 0.01, f(x) - 0.45, x + 0.01, f(x) + 0.02, '#6a4a33')
        with mid.piece(0.9) as d:
            for dx, dy, r in ((-0.04, -0.45, 0.07), (0.03, -0.48, 0.08), (0, -0.53, 0.07)):
                d.circ(x + dx, f(x) + dy, r, S.pick(['#3f8a42', '#4f9e48', '#2f7a3a']))
    for k in range(5):  # vines
        x = S.r(0, 1)
        with mid.piece(0.5) as d:
            pts = [(x + 0.01 * math.sin(u * 9), u * 0.5) for u in np.linspace(0, 1, 12)]
            d.line(pts, '#5a9a3a', 0.004)
    near = S.L('near')
    g = hills(near, 0.88, 0.03, '#3f7a32', seed=S.seed + 2)
    with near.piece(0.9) as d:  # big leaves
        for _ in range(14):
            x = S.r(0, 1)
            y = g(x) + 0.02
            for a in (-60, -30, 0, 30, 60):
                ang = math.radians(-90 + a + S.r(-10, 10))
                ln = S.r(0.08, 0.14)
                ex, ey = x + math.cos(ang) * ln / AR, y + math.sin(ang) * ln
                d.ell((x + ex) / 2, (y + ey) / 2, ln * 0.18, ln * 0.45 if abs(a) < 40 else ln * 0.35, S.pick(['#3f9a4a', '#4fae58', '#2f8a3a']))
    if v == 1:  # bright flowers and a parrot-like bird
        with near.piece(0.7) as d:
            for _ in range(8):
                x = S.r(0, 1)
                d.circ(x, g(x) - S.r(0.04, 0.1), 0.012, S.pick(['#e05a5a', '#f6c453', '#f28bb0']))
            d.ell(0.7, 0.45, 0.02, 0.03, '#e05a5a')
            d.circ(0.705, 0.415, 0.012, '#e05a5a')
            d.poly([(0.7, 0.47), (0.69, 0.53), (0.71, 0.53)], '#3f7fbf')
            d.poly([(0.71, 0.415), (0.72, 0.42), (0.71, 0.425)], '#f6c453')
    fg = S.L('fg')
    with fg.piece() as d:  # framing leaves
        for x, y, ang in ((0.0, 0.2, 20), (0.0, 0.6, -10), (1.0, 0.3, 160), (1.0, 0.75, 190), (0.1, 1.02, -60), (0.9, 1.02, -120)):
            a = math.radians(ang)
            ln = 0.25
            ex, ey = x + math.cos(a) * ln / AR, y + math.sin(a) * ln
            cx, cy = (x + ex) / 2, (y + ey) / 2
            pts = []
            for k in range(21):
                u = k / 20
                wdt = math.sin(math.pi * u) * 0.06
                px = x + (ex - x) * u - math.sin(a) * wdt / AR
                py = y + (ey - y) * u + math.cos(a) * wdt
                pts.append((px, py))
            for k in range(20, -1, -1):
                u = k / 20
                wdt = math.sin(math.pi * u) * 0.06
                pts.append((x + (ex - x) * u + math.sin(a) * wdt / AR, y + (ey - y) * u - math.cos(a) * wdt))
            d.poly(pts, '#2f7a3a')
    weather_fx(S, ground=0.7)
    return {0: 'jungle with giant trees and vines', 1: 'jungle with bright flowers and a parrot', 2: 'jungle with a waterfall'}[v]


@biome('arctic')
def arctic(S):
    v = S.variant % 3
    S.look.season = S.season = 'winter'
    L = sky(S, horizon=0.55)
    rng = S.rng
    if S.time in ('night', 'dusk') and S.weather in ('clear', 'clouds'):  # aurora
        with L.piece(0.2) as d:
            for k in range(3):
                pts = [(x, 0.15 + 0.06 * k + 0.05 * math.sin(x * 7 + k)) for x in np.linspace(-0.05, 1.05, 40)]
                low = [(x, y + 0.12) for x, y in pts[::-1]]
                d.poly(pts + low, (110, 240, 170, 70) if k != 1 else (140, 200, 255, 60))
    far = S.L('far')
    mountains(far, 0.56, 0.3, seed=S.seed, col='#c9d6e6', snow='#f4f8fc', snowline=0.8)
    mid = S.L('mid')
    water(mid, 0.6, col='#3f6f9f', col2='#6a9ac8', seed=S.seed, bottom=0.78)
    for k in range(4):  # ice floes and an iceberg
        x = S.r(0, 1)
        with mid.piece(0.8) as d:
            d.ell(x, S.r(0.64, 0.74), S.r(0.05, 0.1), 0.012, '#f2f6fb')
    with mid.piece(0.9) as d:
        bx = S.r(0.2, 0.8)
        d.poly([(bx - 0.08, 0.66), (bx - 0.05, 0.56), (bx - 0.01, 0.52), (bx + 0.03, 0.58), (bx + 0.07, 0.6), (bx + 0.09, 0.66)], '#e6f0fa')
        d.poly([(bx - 0.01, 0.52), (bx + 0.03, 0.58), (bx + 0.07, 0.6), (bx + 0.09, 0.66), (bx + 0.02, 0.66)], '#c9dcef')
    near = S.L('near')
    g = hills(near, 0.82, 0.04, '#f2f6fb', seed=S.seed + 1)
    if v == 0:  # an igloo
        with near.piece(0.9) as d:
            d.pie(0.65, g(0.65) + 0.06, 0.17, 180, 360, '#f6f9fc')
            d.pie(0.75, g(0.75) + 0.06, 0.065, 180, 360, '#e6eef6')
            d.pie(0.75, g(0.75) + 0.06, 0.04, 180, 360, '#3a4a6a')
        with near.piece(0.3) as d:
            for row in range(4):
                dy = 0.034 * (row + 1)
                hw = math.sqrt(max(0.17 ** 2 - dy ** 2, 0)) / AR * 0.97
                d.line([(0.65 - hw, g(0.65) + 0.06 - dy), (0.65 + hw, g(0.65) + 0.06 - dy)], '#d6e2ee', 0.003)
    elif v == 1:  # a polar bear
        with near.piece(0.9) as d:
            x, y = 0.4, g(0.4) + 0.06
            d.ell(x, y - 0.04, 0.07, 0.04, '#f6f3ea')
            d.ell(x + 0.05, y - 0.055, 0.03, 0.025, '#f6f3ea')
            d.circ(x + 0.04, y - 0.075, 0.009, '#f6f3ea')
            for u in (-0.03, -0.01, 0.02, 0.035):
                d.rect(x + u, y - 0.02, x + u + 0.012, y, '#efe8da', r=0.004)
            d.circ(x + 0.068, y - 0.055, 0.005, '#1d1a18')
    fg = S.L('fg')
    hills(fg, 1.0, 0.05, '#f6f9fc', seed=S.seed + 2)
    weather_fx(S, ground=0.7)
    return {0: 'arctic shore with an igloo and an iceberg', 1: 'arctic ice with a polar bear', 2: 'arctic sea with ice floes'}[v]


import rooms  # noqa: E402,F401  registers the interiors
import studios  # noqa: E402,F401  studio sets (puppet-plates-more)
import rooms2  # noqa: E402,F401  more everyday interiors
import kz  # noqa: E402,F401  Central Asian settings
import outdoors2  # noqa: E402,F401  more outdoor and small-world places
