"""More outdoor and small-world places for the puppet scripts (writers-room places.md): street, crossroads, river,
new_building, airport (baggage claim), beaver_dam, burrow, anthill, savanna, ice_floe, oil_depot, beach_pier.
Same layer contract as scenes.py: sky, far, mid, near, fg; no readable text, signs, logos or flags anywhere."""
import math

import numpy as np

from plates import AR, shade, mixc, sky, weather_fx, sky_gradient, hx, to255, Look
from scenes import biome, winter, skyline, flat, reeds, water, reflection
from props import (hills, mountains, round_tree, pine, bush, grass_tufts, flowers, rock, block, tower, car, bus,
                   lamp_post, bench, fence, crane, ship, boat, ridge_fn, patches)
from rooms import shell, ceiling_panels, lamp_pendant, rug, plant, clock

# biome -> (number of variants, [(time, weather, season, palette), ...])
CITY = [('day', 'clear', 'summer', 'felt'), ('golden', 'clear', 'autumn', 'warm'), ('night', 'clear', 'summer', 'felt'),
        ('day', 'rain', 'autumn', 'muted'), ('dusk', 'clear', 'summer', 'felt'), ('night', 'rain', 'autumn', 'felt'),
        ('day', 'snow', 'winter', 'cool'), ('dawn', 'fog', 'spring', 'pastel'), ('day', 'clouds', 'spring', 'felt')]
NATURE = [('day', 'clear', 'autumn', 'felt'), ('golden', 'clear', 'autumn', 'warm'), ('night', 'clear', 'summer', 'felt'),
          ('dawn', 'fog', 'autumn', 'felt'), ('day', 'clouds', 'summer', 'felt'), ('dusk', 'clear', 'autumn', 'felt'),
          ('day', 'rain', 'summer', 'muted'), ('day', 'snow', 'winter', 'cool'), ('day', 'clear', 'spring', 'pastel')]
IN6 = [('day', 'clear', 'summer', 'felt'), ('night', 'clear', 'summer', 'felt'), ('golden', 'clear', 'autumn', 'warm'),
       ('day', 'rain', 'autumn', 'felt'), ('dusk', 'clear', 'winter', 'felt'), ('dawn', 'clouds', 'spring', 'pastel')]
LOOKS = {
    'street': (3, CITY),
    'crossroads': (3, CITY),
    'river': (3, NATURE),
    'new_building': (3, CITY[:8]),
    'airport': (3, IN6),
    'beaver_dam': (3, NATURE[:8]),
    'burrow': (3, IN6),
    'anthill': (3, [('day', 'clear', 'summer', 'felt'), ('golden', 'clear', 'summer', 'warm'), ('day', 'clouds', 'autumn', 'felt'),
                    ('day', 'clear', 'spring', 'pastel'), ('dusk', 'clear', 'summer', 'felt'), ('day', 'clear', 'summer', 'vivid')]),
    'savanna': (3, [('day', 'clear', 'summer', 'felt'), ('golden', 'clear', 'summer', 'warm'), ('dusk', 'clear', 'summer', 'felt'),
                    ('night', 'clear', 'summer', 'felt'), ('dawn', 'clouds', 'summer', 'pastel'), ('day', 'rain', 'summer', 'muted'),
                    ('day', 'clouds', 'summer', 'vivid'), ('dawn', 'fog', 'summer', 'felt')]),
    'ice_floe': (3, [('day', 'clear', 'winter', 'felt'), ('golden', 'clear', 'winter', 'warm'), ('night', 'clear', 'winter', 'felt'),
                     ('dusk', 'clear', 'winter', 'felt'), ('day', 'snow', 'winter', 'cool'), ('dawn', 'fog', 'winter', 'pastel'),
                     ('day', 'clouds', 'winter', 'felt'), ('night', 'clouds', 'winter', 'cool')]),
    'oil_depot': (3, [('day', 'clear', 'summer', 'felt'), ('golden', 'clear', 'autumn', 'warm'), ('night', 'clear', 'summer', 'felt'),
                      ('dusk', 'clear', 'summer', 'felt'), ('day', 'rain', 'autumn', 'muted'), ('day', 'snow', 'winter', 'cool'),
                      ('dawn', 'fog', 'spring', 'felt'), ('day', 'clouds', 'summer', 'felt')]),
    'beach_pier': (3, [('day', 'clear', 'summer', 'felt'), ('golden', 'clear', 'summer', 'warm'), ('night', 'clear', 'summer', 'felt'),
                       ('dusk', 'clear', 'summer', 'felt'), ('day', 'clouds', 'summer', 'pastel'), ('day', 'rain', 'autumn', 'muted'),
                       ('dawn', 'fog', 'summer', 'felt'), ('day', 'clear', 'summer', 'vivid')]),
}


# ---------------------------------------------------------------- small props

def walker(L, x, y, s=1.0, col='#5a5a6a', face=1, umbrella=None):
    """A passer-by silhouette: head, coat, legs; an umbrella in the rain."""
    k = s / AR
    with L.piece(0.7) as d:
        d.circ(x, y - 0.115 * s, 0.012 * s, shade(col, 1.15))
        d.rect(x - 0.016 * k, y - 0.1 * s, x + 0.016 * k, y - 0.04 * s, col, r=0.01 * s)
        d.line([(x - 0.007 * k, y - 0.045 * s), (x - 0.007 * k - face * 0.006 * k, y)], shade(col, 0.75), 0.006 * s)
        d.line([(x + 0.007 * k, y - 0.045 * s), (x + 0.007 * k + face * 0.008 * k, y)], shade(col, 0.75), 0.006 * s)
        if umbrella:
            d.line([(x + 0.01 * k, y - 0.08 * s), (x + 0.01 * k, y - 0.15 * s)], '#3a3a40', 0.003 * s)
            d.pie(x + 0.01 * k, y - 0.14 * s, 0.035 * s, 180, 360, umbrella)


def puddle(L, x, y, rx, ry, S):
    """A puddle of shiny cloth: the sky colour with two bright streaks."""
    c = S.look.sky_cols()[1]
    with L.piece(0.3) as d:
        d.ell(x, y, rx, ry, to255(c * 0.85 + 0.1))
        d.ell(x - rx * 0.15 / AR, y - ry * 0.2, rx * 0.55, ry * 0.18, to255(np.clip(c * 0.6 + 0.45, 0, 1)))
        d.ell(x + rx * 0.3 / AR, y + ry * 0.3, rx * 0.25, ry * 0.12, to255(np.clip(c * 0.6 + 0.45, 0, 1)))


def bin_(L, x, y, s=1.0, col='#4f7f5a'):
    k = s / AR
    with L.piece(0.9) as d:
        d.poly([(x - 0.03 * k, y - 0.1 * s), (x + 0.03 * k, y - 0.1 * s), (x + 0.025 * k, y), (x - 0.025 * k, y)], col)
        d.rect(x - 0.034 * k, y - 0.112 * s, x + 0.034 * k, y - 0.098 * s, shade(col, 0.8), r=0.004 * s)
        for u in (-0.012, 0, 0.012):
            d.rect(x + u * k - 0.002 * k, y - 0.088 * s, x + u * k + 0.002 * k, y - 0.012 * s, shade(col, 0.88))


def facade(L, x0, x1, base, h, col, rng, S, shop=True, awning='#c0443a', fh=0.07):
    """A city house front: a window grid, a cornice, and a shop window with an awning on the ground floor (no sign)."""
    with L.piece(0.8) as d:
        d.rect(x0, base - h, x1, base, col)
        d.rect(x0 - 0.006, base - h - 0.014, x1 + 0.006, base - h, shade(col, 0.78))
        d.rect(x0, base - fh * 1.1, x1, base - fh * 1.1 + 0.008, shade(col, 0.85))
    n = max(2, int((x1 - x0) / 0.05))
    ww = (x1 - x0) / n
    floors = int((h - fh * 1.2) / fh)
    with L.piece(0.5) as d:
        for f in range(floors):
            y = base - fh * 1.2 - (f + 1) * fh + fh * 0.22
            for k in range(n):
                wx = x0 + k * ww + ww * 0.25
                d.rect(wx - 0.003, y - 0.004, wx + ww * 0.5 + 0.003, y + fh * 0.58, shade(col, 0.82), r=0.002)
                d.window(wx, y, wx + ww * 0.5, y + fh * 0.55, rng=rng, r=0.002)
                d.rect(wx - 0.004, y + fh * 0.55, wx + ww * 0.5 + 0.004, y + fh * 0.6, shade(col, 1.12))
    if shop:
        on = S.look.lit_share > 0.3
        sx0, sx1 = x0 + (x1 - x0) * 0.08, x0 + (x1 - x0) * 0.7
        with L.piece(0.6) as d:
            d.rect(sx0, base - fh * 0.95, sx1, base - 0.004, '#ffe2a0' if on else mixc('#9fc6dc', col, 0.2), lit=on)
            d.rect(x0 + (x1 - x0) * 0.76, base - fh * 0.9, x0 + (x1 - x0) * 0.92, base, '#6a4a3a', r=0.003)
        if on:
            L.glow_rect(sx0, base - fh * 0.95, sx1, base - 0.004)
        with L.piece(0.6) as d:  # goods in the window, the awning
            for k in range(5):
                gx = sx0 + (sx1 - sx0) * (k + 0.5) / 5
                d.rect(gx - 0.008, base - fh * 0.35, gx + 0.008, base - 0.008, ['#e05a5a', '#3f7fbf', '#6fb850', '#f6c453', '#b99be0'][(k + int(x0 * 50)) % 5], r=0.003)
            d.rect(sx0 + (sx1 - sx0) * 0.5 - 0.002, base - fh * 0.95, sx0 + (sx1 - sx0) * 0.5 + 0.002, base, shade(col, 0.6))
            d.poly([(sx0 - 0.01, base - fh * 1.02), (sx1 + 0.01, base - fh * 1.02), (sx1 + 0.02, base - fh * 0.82), (sx0 - 0.02, base - fh * 0.82)], awning)
            m = max(3, int((sx1 - sx0) / 0.02))
            for k in range(m):
                if k % 2:
                    u0, u1 = k / m, (k + 1) / m
                    d.poly([(sx0 - 0.01 + (sx1 - sx0 + 0.02) * u0, base - fh * 1.02), (sx0 - 0.01 + (sx1 - sx0 + 0.02) * u1, base - fh * 1.02),
                            (sx0 - 0.02 + (sx1 - sx0 + 0.04) * u1, base - fh * 0.82), (sx0 - 0.02 + (sx1 - sx0 + 0.04) * u0, base - fh * 0.82)], '#f3efe6')


def traffic_light(L, x, y, s=1.0, state=0):
    """Pole with a three-lamp head; state 0 red, 1 yellow, 2 green. The lit lamp glows."""
    k = s / AR
    with L.piece(0.8) as d:
        d.line([(x, y), (x, y - 0.32 * s)], '#4a4a58', 0.008 * s)
        d.rect(x - 0.022 * k, y - 0.44 * s, x + 0.022 * k, y - 0.3 * s, '#2e2e36', r=0.008 * s)
        d.rect(x - 0.012 * k, y - 0.006 * s, x + 0.012 * k, y, '#4a4a58')
    cols = ['#ff4a3a', '#ffc23a', '#4ade6a']
    with L.piece(0.4) as d:
        for i in range(3):
            cy = y - (0.415 - i * 0.044) * s
            if i == state:
                d.circ(x, cy, 0.016 * s, cols[i], lit=True)
            else:
                d.circ(x, cy, 0.016 * s, shade(cols[i], 0.35))
    L.glow_circ(x, y - (0.415 - state * 0.044) * s, 0.02 * s)


def scooter(L, x, y, s=1.0, col='#3fb0a8', lean=0.0):
    k = s / AR
    with L.piece(0.7) as d:
        d.circ(x - 0.04 * k, y - 0.012 * s, 0.012 * s, '#2e2e36')
        d.circ(x + 0.04 * k, y - 0.012 * s, 0.012 * s, '#2e2e36')
        d.line([(x - 0.045 * k, y - 0.018 * s), (x + 0.035 * k, y - 0.018 * s)], col, 0.008 * s)
        d.line([(x + 0.038 * k, y - 0.015 * s), (x + 0.03 * k + lean, y - 0.12 * s)], col, 0.006 * s)
        d.line([(x + 0.015 * k + lean, y - 0.12 * s), (x + 0.045 * k + lean, y - 0.12 * s)], '#2e2e36', 0.006 * s)


def suitcase(L, x, y, w, h, col, d=None):
    """A suitcase standing on y: body, a handle, two straps."""
    d.rect(x - w / 2, y - h, x + w / 2, y, col, r=0.008)
    d.rect(x - w * 0.15, y - h - 0.012, x + w * 0.15, y - h + 0.002, shade(col, 0.7), r=0.004)
    for u in (-0.25, 0.25):
        d.rect(x + u * w - 0.002, y - h, x + u * w + 0.002, y, shade(col, 0.82))


def acacia(L, x, y, s=1.0, leaf='#7a9a4a', trunk='#6a4a33'):
    """An umbrella acacia: a split trunk and a flat layered crown."""
    with L.piece(0.8) as d:
        d.poly([(x - 0.006 * s, y), (x + 0.006 * s, y), (x + 0.004 * s, y - 0.12 * s), (x - 0.004 * s, y - 0.12 * s)], trunk)
        d.line([(x, y - 0.11 * s), (x - 0.05 * s, y - 0.22 * s)], trunk, 0.006 * s)
        d.line([(x, y - 0.11 * s), (x + 0.06 * s, y - 0.21 * s)], trunk, 0.006 * s)
        d.line([(x, y - 0.13 * s), (x + 0.005 * s, y - 0.23 * s)], trunk, 0.005 * s)
    with L.piece(1.0) as d:
        d.ell(x, y - 0.235 * s, 0.17 * s, 0.035 * s, shade(leaf, 0.85))
        d.ell(x - 0.04 * s, y - 0.255 * s, 0.12 * s, 0.03 * s, leaf)
        d.ell(x + 0.05 * s, y - 0.25 * s, 0.1 * s, 0.026 * s, shade(leaf, 1.08))


def giraffe(L, x, y, s=1.0, face=1, col='#d9a24a'):
    k = s / AR

    def X(u):
        return x + face * u * k
    with L.piece(0.7) as d:
        for u in (-0.03, -0.018, 0.02, 0.032):  # legs
            d.line([(X(u), y - 0.085 * s), (X(u * 0.9), y)], col, 0.007 * s)
        d.ell(X(0), y - 0.095 * s, 0.05 * s, 0.025 * s, col)
        d.poly([(X(0.02), y - 0.11 * s), (X(0.04), y - 0.1 * s), (X(0.07), y - 0.2 * s), (X(0.055), y - 0.205 * s)], col)
        d.ell(X(0.072), y - 0.205 * s, 0.017 * s, 0.009 * s, col)
        d.line([(X(0.062), y - 0.212 * s), (X(0.06), y - 0.226 * s)], shade(col, 0.6), 0.003 * s)
        d.line([(X(0.068), y - 0.212 * s), (X(0.068), y - 0.226 * s)], shade(col, 0.6), 0.003 * s)
        d.line([(X(-0.045), y - 0.1 * s), (X(-0.058), y - 0.07 * s)], col, 0.003 * s)
    with L.piece(0.3) as d:  # patches
        for (u, v_) in ((-0.025, 0.1), (-0.005, 0.09), (0.015, 0.1), (-0.015, 0.105), (0.005, 0.105), (0.045, 0.135), (0.055, 0.165), (0.03, 0.105)):
            d.circ(X(u), y - v_ * s, 0.005 * s, shade(col, 0.7))


def zebra_animal(L, x, y, s=1.0, face=1, col='#e9e6de'):
    k = s / AR

    def X(u):
        return x + face * u * k
    with L.piece(0.7) as d:
        d.ell(X(0), y - 0.045 * s, 0.03 * s, 0.016 * s, col)
        for u in (-0.022, -0.012, 0.014, 0.024):
            d.line([(X(u), y - 0.04 * s), (X(u), y)], col, 0.004 * s)
        d.line([(X(0.022), y - 0.05 * s), (X(0.035), y - 0.075 * s)], col, 0.007 * s)
        d.ell(X(0.04), y - 0.072 * s, 0.009 * s, 0.006 * s, col)
        for u in (-0.015, -0.005, 0.005, 0.015):
            d.line([(X(u), y - 0.058 * s), (X(u + 0.003), y - 0.035 * s)], '#3a3a40', 0.002 * s)


def elephant(L, x, y, s=1.0, face=1, col='#8a8a96'):
    k = s / AR

    def X(u):
        return x + face * u * k
    with L.piece(0.7) as d:
        d.ell(X(0), y - 0.05 * s, 0.045 * s, 0.03 * s, col)
        for u in (-0.028, -0.012, 0.014, 0.028):
            d.rect(X(u) - 0.004 * k, y - 0.04 * s, X(u) + 0.004 * k, y, col)
        d.ell(X(0.04), y - 0.06 * s, 0.018 * s, 0.018 * s, col)
        d.line([(X(0.05), y - 0.055 * s), (X(0.058), y - 0.02 * s)], col, 0.006 * s)
        d.ell(X(0.03), y - 0.06 * s, 0.01 * s, 0.016 * s, shade(col, 0.88))


def gull(L, x, y, s=1.0):
    k = s / AR
    with L.piece(0.4) as d:
        d.line([(x - 0.02 * k, y - 0.006 * s), (x - 0.008 * k, y - 0.012 * s), (x, y)], '#f6f6f2', 0.004 * s)
        d.line([(x, y), (x + 0.008 * k, y - 0.012 * s), (x + 0.02 * k, y - 0.006 * s)], '#f6f6f2', 0.004 * s)


def barrel(d, x, y, s, col):
    k = s / AR
    d.rect(x - 0.026 * k, y - 0.085 * s, x + 0.026 * k, y, col, r=0.008 * s)
    for v in (0.02, 0.063):
        d.rect(x - 0.026 * k, y - v * s - 0.003 * s, x + 0.026 * k, y - v * s + 0.003 * s, shade(col, 0.75))
    d.ell(x, y - 0.085 * s, 0.021 * s, 0.006 * s, shade(col, 1.12))


def tank(L, x, y, w, h, col='#e6e6e0', stripe='#c0443a'):
    """A round storage tank seen from the side: a cylinder, a domed top, a spiral stair, a coloured band."""
    with L.piece(0.9) as d:
        d.rect(x - w / 2, y - h, x + w / 2, y, col)
        d.ell(x, y - h, w / 2 * AR, 0.02, shade(col, 1.06))
        d.rect(x - w / 2, y - h * 0.62, x + w / 2, y - h * 0.55, stripe)
        d.rect(x + w * 0.2, y - h, x + w / 2, y, shade(col, 0.9))
    with L.piece(0.4) as d:
        n = 5
        for i in range(n):
            y0 = y - h * i / n
            d.line([(x - w / 2, y0), (x + w / 2, y0 - h / n)], '#7a7a86', 0.003)
        d.line([(x - w / 2, y - h - 0.002), (x + w / 2, y - h - 0.002)], '#7a7a86', 0.002)


def stick_pile(d, x0, x1, ytop, ybot, rng, n=60, cols=('#6a4a33', '#7a5a3a', '#8a6a48', '#5a3e2a')):
    """A heap of crossed sticks (a beaver dam or lodge) inside a hump from x0..x1."""
    for _ in range(n):
        u = rng.random()
        x = x0 + (x1 - x0) * u
        top = ybot - (ybot - ytop) * math.sin(math.pi * u) ** 0.6
        y = top + (ybot - top) * rng.random()
        a = (rng.random() - 0.5) * 1.6
        ln = 0.03 + 0.05 * rng.random()
        d.line([(x - math.cos(a) * ln / AR, y - math.sin(a) * ln * 0.5), (x + math.cos(a) * ln / AR, y + math.sin(a) * ln * 0.5)],
               cols[int(rng.integers(len(cols)))], 0.006 + 0.004 * rng.random())


# ---------------------------------------------------------------- city

@biome('street')
def street(S):
    v = S.variant % 3
    rng = S.rng
    sky(S, horizon=0.5, cloud_y=(0.04, 0.16))
    greys = ['#a9a8b0', '#b8b2a8', '#9aa0aa', '#c2bcb2', '#8f949c']
    far = S.L('far')
    skyline(far, 0.55, rng, 0.1, 0.3, cols=['#a3aac4', '#b2b8cc', '#9aa2bc'])
    mid = S.L('mid')
    base = 0.72
    if v == 0:  # a row of grey houses with shop fronts
        x = -0.02
        i = 0
        while x < 1.0:
            w = 0.2 + 0.06 * rng.random()
            facade(mid, x, x + w, base, 0.42 + 0.16 * rng.random(), greys[i % 5], rng, S, awning=['#c0443a', '#3f7fbf', '#3d8a5a', '#e9a23a'][i % 4])
            x += w + 0.004
            i += 1
    elif v == 1:  # two houses with an alley between, trees on the pavement
        facade(mid, -0.02, 0.4, base, 0.58, greys[0], rng, S, awning='#3d8a5a')
        facade(mid, 0.56, 1.02, base, 0.5, greys[3], rng, S, awning='#c0443a')
        with mid.piece(0.5) as d:  # the alley: a far wall and a lamp
            d.rect(0.4, 0.3, 0.56, base, shade(greys[2], 0.8))
            d.rect(0.44, 0.58, 0.52, base, '#5a5a66', r=0.004)
        for x in (0.2, 0.8):
            round_tree(mid, x, base + 0.02, 1.0, rng=rng)
    else:  # an old narrow street: low houses, an arch, cobbles
        facade(mid, -0.02, 0.3, base, 0.46, '#c9b9a0', rng, S, awning='#a34a3a', fh=0.08)
        facade(mid, 0.3, 0.62, base, 0.36, '#b0a898', rng, S, shop=False, fh=0.08)
        facade(mid, 0.62, 1.02, base, 0.5, '#a8b0b4', rng, S, awning='#3f7fbf', fh=0.08)
        with mid.piece(0.6) as d:
            d.pie(0.46, base - 0.06, 0.09, 180, 360, '#4a4652')
            d.rect(0.46 - 0.09 / AR, base - 0.06, 0.46 + 0.09 / AR, base, '#4a4652')
    near = S.L('near')
    with near.piece(0.4) as d:  # pavement, kerb, road
        d.rect(-0.02, base, 1.02, 0.84, '#b3aea4')
        for k in range(14):
            d.rect(k * 0.075, base, k * 0.075 + 0.003, 0.84, shade('#b3aea4', 0.9))
        d.rect(-0.02, 0.84, 1.02, 0.86, '#d4d0c6')
        d.rect(-0.02, 0.86, 1.02, 1.02, '#5a5a66' if v != 2 else '#7a7470')
        if v == 2:
            for j in range(4):
                for k in range(30):
                    d.ell(k * 0.036 + (j % 2) * 0.018, 0.885 + j * 0.035, 0.016, 0.01, shade('#7a7470', 1.1 + 0.05 * ((k + j) % 2)))
    wet = S.weather in ('rain', 'fog') or S.look.time in ('dawn',) or v == 0
    for x, y, rx in ((0.22, 0.93, 0.11), (0.6, 0.965, 0.08), (0.88, 0.9, 0.06)) if wet else ((0.62, 0.94, 0.08),):
        puddle(near, x, y, rx, rx * 0.22, S)
    walkers = 3 + int(rng.integers(3))
    for i in range(walkers):  # passers-by far down the pavement, small
        x = rng.random()
        if 0.35 < x < 0.65:
            x = x + 0.32 if x < 0.5 else x - 0.32
        walker(mid, x, base + 0.005, 0.75, col=S.pick(['#5a5a6a', '#6a4a4a', '#4a5a6a', '#7a6a5a']), face=S.pick([-1, 1]),
               umbrella=S.pick(['#c0443a', '#3f7fbf', '#2e2e36']) if S.weather == 'rain' else None)
    lamp_post(near, 0.08, 0.83, 1.7)
    bin_(near, 0.16, 0.835, 1.2)
    if v != 2:
        car(near, 0.78, 0.96, 2.0, col=S.pick(['#e05a5a', '#3f7fbf', '#f2f2f2', '#2e2e36']), face=-1)
    else:
        bench(near, 0.86, 0.835, 1.5)
    fg = S.L('fg')
    with fg.piece() as d:  # kerb edge and a bollard row in front
        for x in (0.3, 0.7):
            d.rect(x - 0.008, 0.88, x + 0.008, 1.02, '#4a4a58', r=0.006)
            d.circ(x, 0.88, 0.01, '#4a4a58')
    weather_fx(S, ground=0.72)
    return {0: 'city street, grey houses with shop fronts, a lamp and a bin', 1: 'city street with an alley and pavement trees',
            2: 'old narrow street with cobbles and an arch'}[v]


@biome('crossroads')
def crossroads(S):
    v = S.variant % 3
    rng = S.rng
    if v == 2:
        return _crossroads_top(S)
    sky(S, horizon=0.5, cloud_y=(0.04, 0.18))
    far = S.L('far')
    skyline(far, 0.6, rng, 0.12, 0.34, cols=['#a3aac4', '#b2b8cc', '#9aa2bc'])
    mid = S.L('mid')
    base = 0.66
    for i, x in enumerate((-0.02, 0.24, 0.56, 0.78)):
        block(mid, x, x + 0.2, base, 6 + (i % 2) * 2, ['#d8cfc2', '#c9d2d8', '#e2d4c0', '#cfcac2'][i], rng, fh=0.045)
    if v == 1:
        for x in (0.22, 0.54, 0.76):
            round_tree(mid, x, base + 0.01, 0.9, rng=rng)
    near = S.L('near')
    with near.piece(0.4) as d:
        d.rect(-0.02, base, 1.02, 0.7, '#b3aea4')
        d.rect(-0.02, 0.7, 1.02, 0.72, '#d4d0c6')
        d.rect(-0.02, 0.72, 1.02, 0.92, '#5a5a66')
        for k in range(12):  # lane marks
            d.rect(k * 0.09, 0.815, k * 0.09 + 0.045, 0.822, '#e8e4d0')
        d.rect(-0.02, 0.92, 1.02, 0.94, '#d4d0c6')
        d.rect(-0.02, 0.94, 1.02, 1.02, '#b3aea4')
    with near.piece(0.3) as d:  # the zebra crossing, receding stripes
        cx = 0.5 if v == 0 else 0.42
        for j in range(7):
            y0 = 0.725 + j * 0.028
            w0, w1 = 0.11 + j * 0.006, 0.11 + (j + 1) * 0.006
            d.poly([(cx - w0, y0), (cx + w0, y0), (cx + w1, y0 + 0.016), (cx - w1, y0 + 0.016)], '#f4f2ea')
    cs = ['#e05a5a', '#f2f2f2', '#3f7fbf', '#2e2e36', '#f6c453', '#7f8a96']
    car(near, 0.2 if v == 0 else 0.15, 0.8, 1.6, col=S.pick(cs), face=1)
    car(near, 0.82, 0.9, 1.9, col=S.pick(cs), face=-1)
    if v == 1:
        bus(near, 0.75, 0.8, 1.5, col='#3f8f5a', rng=rng)
    traffic_light(near, 0.68 if v == 0 else 0.62, 0.72, 1.0, state=int(rng.integers(3)))
    traffic_light(near, 0.3 if v == 0 else 0.24, 0.72, 0.85, state=int(rng.integers(3)))
    fg = S.L('fg')
    traffic_light(fg, 0.93, 1.0, 1.5, state=0 if v == 0 else 2)
    with fg.piece() as d:  # a pole with scooters leaning on it
        d.line([(0.07, 1.02), (0.07, 0.55)], '#5a5a66', 0.012)
        d.circ(0.07, 0.55, 0.012, '#5a5a66')
    scooter(fg, 0.04, 1.0, 1.6, col='#3fb0a8', lean=0.01)
    scooter(fg, 0.12, 1.01, 1.6, col='#f08a2e', lean=-0.01)
    if v == 1:
        lamp_post(near, 0.04, 0.7, 1.4)
    weather_fx(S, ground=0.7)
    return {0: 'crossroads with a zebra crossing, traffic lights and scooters', 1: 'crossroads with a bus, trees and scooters'}[v]


def _crossroads_top(S):
    """The crossroads seen from above: two roads, four zebras, car roofs, tree crowns, a pavement corner each side."""
    rng = S.rng
    L = sky_gradient(S, cols=[hx('#8a8a96')] * 3, horizon=1.0)
    with L.piece(0.4) as d:
        d.rect(-0.02, -0.02, 1.02, 1.02, '#5a5a66')
    rw, rh = 0.16, 0.2  # half width of the vertical road (x units) and half height of the horizontal road
    cx, cy = 0.5, 0.5
    far = S.L('far')
    with far.piece(0.5) as d:  # pavement corners
        for (x0, x1, y0, y1) in ((-0.02, cx - rw, -0.02, cy - rh), (cx + rw, 1.02, -0.02, cy - rh),
                                 (-0.02, cx - rw, cy + rh, 1.02), (cx + rw, 1.02, cy + rh, 1.02)):
            d.rect(x0, y0, x1, y1, '#d4d0c6')
            d.rect(x0 + 0.015, y0 + 0.025, x1 - 0.015, y1 - 0.025, '#b3aea4', r=0.01)
    with far.piece(0.35) as d:
        for (x0, x1, y0, y1) in ((-0.02, cx - rw - 0.04, -0.02, cy - rh - 0.06), (cx + rw + 0.04, 1.02, -0.02, cy - rh - 0.06),
                                 (-0.02, cx - rw - 0.04, cy + rh + 0.06, 1.02), (cx + rw + 0.04, 1.02, cy + rh + 0.06, 1.02)):
            d.rect(x0, y0, x1, y1, 'grass', r=0.02)
    mid = S.L('mid')
    with mid.piece(0.3) as d:  # zebras and lane lines
        for k in range(7):
            x = cx - rw + 0.02 + k * (2 * rw - 0.04) / 6
            d.rect(x - 0.01, cy - rh - 0.07, x + 0.01, cy - rh - 0.01, '#f4f2ea')
            d.rect(x - 0.01, cy + rh + 0.01, x + 0.01, cy + rh + 0.07, '#f4f2ea')
        for k in range(6):
            y = cy - rh + 0.02 + k * (2 * rh - 0.04) / 5
            d.rect(cx - rw - 0.05, y - 0.01, cx - rw - 0.01, y + 0.01, '#f4f2ea')
            d.rect(cx + rw + 0.01, y - 0.01, cx + rw + 0.05, y + 0.01, '#f4f2ea')
        for k in range(4):
            d.rect(0.02 + k * 0.07, cy - 0.004, 0.06 + k * 0.07, cy + 0.004, '#e8e4d0')
            d.rect(1 - 0.06 - k * 0.07, cy - 0.004, 1 - 0.02 - k * 0.07, cy + 0.004, '#e8e4d0')
            d.rect(cx - 0.0025, 0.02 + k * 0.06, cx + 0.0025, 0.05 + k * 0.06, '#e8e4d0')
            d.rect(cx - 0.0025, 0.95 - k * 0.06, cx + 0.0025, 0.98 - k * 0.06, '#e8e4d0')
    cs = ['#e05a5a', '#f2f2f2', '#3f7fbf', '#2e2e36', '#f6c453', '#7f8a96', '#3d8a5a']
    near = S.L('near')
    for (x, y, horiz) in ((0.12, cy - 0.1, True), (0.27, cy + 0.1, True), (0.84, cy + 0.1, True), (cx - 0.07, 0.12, False), (cx + 0.07, 0.86, False)):
        c = S.pick(cs)
        with near.piece(0.9) as d:  # a car roof seen from above
            if horiz:
                d.rect(x - 0.05, y - 0.045, x + 0.05, y + 0.045, c, r=0.02)
                d.rect(x - 0.022, y - 0.035, x + 0.025, y + 0.035, shade(c, 0.85), r=0.012)
                d.rect(x + 0.025, y - 0.035, x + 0.035, y + 0.035, '#9fc6dc' if not S.look.night else '#3a4870', r=0.006)
            else:
                d.rect(x - 0.028, y - 0.08, x + 0.028, y + 0.08, c, r=0.02)
                d.rect(x - 0.02, y - 0.035, x + 0.02, y + 0.04, shade(c, 0.85), r=0.012)
                d.rect(x - 0.02, y - 0.055, x + 0.02, y - 0.035, '#9fc6dc' if not S.look.night else '#3a4870', r=0.006)
    fg = S.L('fg')
    for (x, y) in ((0.12, 0.14), (0.88, 0.12), (0.1, 0.88), (0.9, 0.86), (0.24, 0.06), (0.76, 0.95)):
        with fg.piece() as d:  # tree crowns from above
            if winter(S):
                for a in range(7):
                    ang = a * 0.9
                    d.line([(x, y), (x + math.cos(ang) * 0.05 / AR, y + math.sin(ang) * 0.05)], '#6a5546', 0.005)
            else:
                d.circ(x, y, 0.085, 'leaf')
                d.circ(x - 0.015, y - 0.02, 0.055, 'leaf2')
    for (x, y) in ((cx - rw - 0.01, cy - rh - 0.02), (cx + rw + 0.01, cy + rh + 0.02)):
        with fg.piece() as d:
            d.circ(x, y, 0.016, '#2e2e36')
        fg.flat().circ(x, y, 0.008, '#4ade6a', lit=True)
        fg.glow_circ(x, y, 0.012)
    if S.look.lit_share > 0.2:
        for (x, y) in ((cx - rw - 0.03, 0.25), (cx + rw + 0.03, 0.75), (0.25, cy + rh + 0.03), (0.75, cy - rh - 0.03)):
            mid.glow_circ(x, y, 0.05)
    weather_fx(S, ground=0.7)
    return 'crossroads seen from above: zebras, car roofs, tree crowns'


# ---------------------------------------------------------------- water and forest

def foam(d, x0, x1, y0, y1, rng, n=30):
    for _ in range(n):
        x, y = x0 + (x1 - x0) * rng.random(), y0 + (y1 - y0) * rng.random()
        d.ell(x, y, 0.01 + 0.03 * rng.random(), 0.004 + 0.004 * rng.random(), '#f4f8fa')


@biome('river')
def river(S):
    v = S.variant % 3
    rng = S.rng
    hz = 0.5
    sky(S, horizon=hz)
    far = S.L('far')
    if v != 2:
        mountains(far, hz + 0.05, hz - 0.18, seed=S.seed, col='#9aa3cf', snowline=0.6)
    hills(far, hz + 0.08, 0.07, mixc('#7f9a6a', '#a9b4c8', 0.4) if not winter(S) else '#e0e6ee', seed=S.seed + 1)
    mid = S.L('mid')
    bank_l = hills(mid, 0.62, 0.05, 'grass2', seed=S.seed + 3)
    for k in range(9):  # autumn trees on both banks
        x = (k + 0.5) / 9 + S.r(-0.03, 0.03)
        if v == 1 and 0.35 < x < 0.65:
            continue
        if S.r() < 0.35:
            pine(mid, x, bank_l(x) + 0.03, 0.75)
        else:
            round_tree(mid, x, bank_l(x) + 0.03, 0.8, rng=rng)
    wc, wc2 = '#4f8fca', '#7ab4e0'
    if winter(S):
        wc, wc2 = '#5a86b0', '#8ab0d0'
    near = S.L('near')
    if v == 0:  # a wide rapid with boulders and foam
        with mid.piece(0.6) as d:
            d.poly([(-0.02, 0.64), (1.02, 0.6), (1.02, 1.02), (-0.02, 1.02)], wc)
        with mid.piece(0.35) as d:
            foam(d, 0.0, 1.0, 0.64, 0.8, rng, 40)
            for k in range(16):
                y = 0.66 + k * 0.012
                x = S.r(0, 1)
                d.rect(x, y, x + S.r(0.04, 0.12), y + 0.004, wc2, r=0.002)
        for x, y, s in ((0.15, 0.72, 1.4), (0.42, 0.7, 1.0), (0.7, 0.73, 1.6), (0.88, 0.69, 0.9)):
            rock(mid, x, y, s, col='#8f8a84')
            with mid.piece(0.3) as d:
                d.ell(x - 0.015, y + 0.002, 0.06 * s, 0.008 * s, '#f4f8fa')
        with near.piece(0.6) as d:
            d.poly([(-0.02, 0.8), (1.02, 0.78), (1.02, 1.02), (-0.02, 1.02)], wc)
        with near.piece(0.35) as d:
            foam(d, 0.0, 1.0, 0.8, 0.92, rng, 30)
        g = ridge_fn(S.seed + 4, 0.93, 0.03)
        with near.piece(0.8) as d:  # the near bank: pebbles
            d.ridge(g, '#b9a88e')
            for k in range(30):
                x = S.r(0, 1)
                d.ell(x, g(x) + S.r(0.01, 0.08), 0.012, 0.007, S.pick(['#9a958f', '#c9c1b0', '#8a7a6a']))
    elif v == 1:  # a small waterfall over a rock ledge
        with mid.piece(0.6) as d:
            d.rect(-0.02, 0.6, 1.02, 0.66, wc)
        with mid.piece(0.9) as d:  # ledge
            d.poly([(-0.02, 0.64), (0.3, 0.62), (0.36, 0.66), (0.64, 0.66), (0.7, 0.62), (1.02, 0.63), (1.02, 0.8), (-0.02, 0.8)], '#8a857e')
            d.poly([(0.0, 0.7), (0.3, 0.68), (0.33, 0.8), (0.0, 0.8)], shade('#8a857e', 0.88))
            d.poly([(0.7, 0.68), (1.02, 0.7), (1.02, 0.8), (0.67, 0.8)], shade('#8a857e', 0.9))
        with mid.piece(0.5) as d:  # falling water
            d.rect(0.36, 0.655, 0.64, 0.8, wc2)
            for k in range(14):
                x = 0.37 + k * 0.019
                d.rect(x, 0.66, x + 0.006, 0.8, '#d6eaf6', r=0.003)
        with near.piece(0.6) as d:
            d.rect(-0.02, 0.79, 1.02, 1.02, wc)
        with near.piece(0.35) as d:
            for k in range(22):
                d.ell(0.32 + 0.36 * rng.random(), 0.8 + 0.03 * rng.random(), 0.03 + 0.02 * rng.random(), 0.012, '#f4f8fa')
            foam(d, 0.1, 0.9, 0.84, 0.98, rng, 18)
        for x in (0.12, 0.86):
            rock(near, x, 0.9, 2.2, col='#8f8a84')
    else:  # a calm bend with a fallen log and big boulders in front
        with mid.piece(0.6) as d:
            pts = [(u, 0.63 + 0.03 * math.sin(u * 4)) for u in np.linspace(-0.02, 1.02, 30)]
            d.poly(pts + [(1.02, 1.02), (-0.02, 1.02)], wc)
        with mid.piece(0.35) as d:
            for k in range(20):
                x = S.r(0, 1)
                y = S.r(0.67, 0.84)
                d.rect(x, y, x + S.r(0.03, 0.1), y + 0.004, wc2, r=0.002)
            foam(d, 0.55, 0.95, 0.7, 0.76, rng, 14)
        with mid.piece(0.9) as d:  # fallen log across the stream
            d.line([(0.5, 0.7), (1.03, 0.64)], '#7a5a3a', 0.03)
            d.circ(0.5, 0.7, 0.016, '#c9a87a')
        with near.piece(0.8) as d:
            d.ridge(ridge_fn(S.seed + 9, 0.95, 0.03), 'grass2')
        for x, s in ((0.06, 2.8), (0.24, 1.8), (0.8, 2.4)):
            rock(near, x, 0.98, s, col='#8f8a84')
    fg = S.L('fg')
    if v != 1 or winter(S):
        reeds(fg, -0.02, 0.12, 1.02, 2.0, rng)
        reeds(fg, 0.9, 1.02, 1.02, 2.0, rng)
    else:
        with fg.piece() as d:  # a leafy branch framing the top left
            d.line([(-0.03, 0.02), (0.12, 0.08), (0.24, 0.07)], '#6a4a33', 0.014)
            d.line([(0.12, 0.08), (0.18, 0.15)], '#6a4a33', 0.008)
            for k in range(16):
                x = -0.02 + 0.27 * k / 15
                d.ell(x, 0.06 + 0.05 * math.sin(k * 1.7) ** 2 + 0.02, 0.045, 0.024, S.pick(['leaf', 'leaf2', 'leaf3']))
    with fg.piece(0.5) as d:  # falling leaves
        if S.season == 'autumn':
            for k in range(12):
                d.ell(S.r(0, 1), S.r(0.1, 0.9), 0.008, 0.004, S.pick(['#e08a3a', '#e9b443', '#c9532e']))
    weather_fx(S, ground=0.62)
    return {0: 'mountain river on a rapid with boulders and foam', 1: 'small waterfall over a rock ledge, autumn trees',
            2: 'river bend with a fallen log and big boulders'}[v]


@biome('beaver_dam')
def beaver_dam(S):
    v = S.variant % 3
    rng = S.rng
    hz = 0.52
    sky(S, horizon=hz)
    far = S.L('far')
    for k in range(18):  # a dark forest edge
        x = k / 17 + S.r(-0.02, 0.02)
        pine(far, x, hz + 0.08 + S.r(0, 0.02), 0.7 + S.r(0, 0.4), depth=0.7)
    mid = S.L('mid')
    wc = '#4f86b8' if not winter(S) else '#9ab8d0'
    with mid.piece(0.6) as d:  # the pond behind the dam
        d.rect(-0.02, hz + 0.08, 1.02, 0.86, wc)
    with mid.piece(0.35) as d:
        for k in range(18):
            x, y = S.r(0, 1), S.r(hz + 0.1, 0.7)
            d.rect(x, y, x + S.r(0.03, 0.09), y + 0.004, shade(wc, 1.2), r=0.002)
    if S.look.time in ('golden', 'dusk', 'night') and S.weather == 'clear':
        reflection(mid, S.look.T['sun'][0], hz + 0.085, 0.04, S.look.T['sun'][2] if S.time != 'night' else '#f6efd2', n=8)
    lx = 0.72 if v != 1 else 0.25
    ls = 1.0 if v != 2 else 1.5
    with mid.piece(0.9) as d:  # the lodge: a dome of sticks in the pond
        d.pie(lx, 0.66, 0.11 * ls, 180, 360, '#6a4a33')
        stick_pile(d, lx - 0.11 * ls / AR, lx + 0.11 * ls / AR, 0.66 - 0.11 * ls, 0.66, rng, n=45)
    with mid.piece(0.5) as d:
        d.ell(lx, 0.665, 0.13 * ls, 0.012, shade(wc, 1.15))
    near = S.L('near')
    dy = 0.86 if v != 2 else 0.9  # foot of the dam
    th = 0.13 if v != 2 else 0.09  # its height
    crest = lambda u: dy - th - 0.012 * math.sin(u * 9) - 0.01 * math.sin(u * 23)
    with near.piece(0.9) as d:  # the dam: a long hump of mud and sticks across the stream
        d.poly([(-0.03, dy + 0.02)] + [(u, crest(u)) for u in np.linspace(-0.03, 1.03, 40)] + [(1.03, dy + 0.02)], '#5a3e2a')
    with near.piece(0.6) as d:
        stick_pile(d, -0.06, 1.06, dy - th - 0.01, dy + 0.01, rng, n=200)
    with near.piece(0.5) as d:  # water spilling over in three places, the stream below
        d.rect(-0.02, dy, 1.02, 1.02, shade(wc, 0.92))
        for x in (0.42, 0.62, 0.86) if v != 1 else (0.36, 0.55, 0.2):
            d.poly([(x - 0.02, crest(x) + 0.004), (x + 0.02, crest(x) + 0.004), (x + 0.03, dy + 0.01), (x - 0.03, dy + 0.01)], shade(wc, 1.25))
            for k in range(4):
                d.rect(x - 0.016 + k * 0.01, crest(x) + 0.01, x - 0.012 + k * 0.01, dy, '#e6f2fa', r=0.002)
            d.ell(x, dy + 0.012, 0.05, 0.01, '#f4f8fa')
        for k in range(12):
            x, y = S.r(0, 1), S.r(dy + 0.03, 1.0)
            d.rect(x, y, x + S.r(0.03, 0.08), y + 0.004, shade(wc, 1.15), r=0.002)
    sx = 0.15 if v != 1 else 0.84
    side = -1 if v != 1 else 1
    fg = S.L('fg')
    bank = lambda x: 0.84 + 0.25 * max(0.0, (abs(x - (0.0 if side < 0 else 1.0)) - 0.12)) ** 1.2 * 4
    with fg.piece() as d:  # the near bank in a bottom corner with the stump on it
        xs = np.linspace(0.0, 0.42, 30) if side < 0 else np.linspace(1.0, 0.58, 30)
        pts = [(x, min(1.04, bank(x))) for x in xs]
        d.poly([(xs[0] + side * 0.03, 1.04), (xs[0] + side * 0.03, 0.84)] + pts + [(pts[-1][0], 1.04)], 'grass2' if not winter(S) else '#eef3f8')
    with fg.piece() as d:  # the stump with a plan of the dam drawn in lines
        d.rect(sx - 0.05, 0.8, sx + 0.05, 0.93, '#7a5a3a', r=0.01)
        for u in (-0.03, 0.0, 0.03):
            d.rect(sx + u - 0.002, 0.81, sx + u + 0.002, 0.92, shade('#7a5a3a', 0.85))
        d.ell(sx, 0.8, 0.095, 0.028, '#d9b98a')
        d.ell(sx, 0.8, 0.065, 0.019, '#cfae7e')
    with fg.piece(0.3) as d:
        k = 0.06 / AR * 1.5
        d.line([(sx - k, 0.808), (sx + k, 0.808)], '#4a3a2a', 0.003)
        d.line([(sx - k * 0.8, 0.808), (sx - k * 0.3, 0.792), (sx + k * 0.3, 0.792), (sx + k * 0.8, 0.808)], '#4a3a2a', 0.003)
        for u in (-0.3, 0.0, 0.3):
            d.line([(sx + u * k, 0.792), (sx + u * k, 0.808)], '#4a3a2a', 0.002)
        d.line([(sx + k * 0.5, 0.788), (sx + k * 0.9, 0.786)], '#c0443a', 0.003)
    with fg.piece(0.7) as d:
        for k in range(10):
            x = S.r(0.0, 0.3) if side < 0 else S.r(0.7, 1.0)
            y = max(bank(x), 0.86) + 0.03
            d.line([(x, y), (x + S.r(-0.01, 0.01), y - S.r(0.03, 0.06))], 'tuft', 0.004)
    reeds(fg, 0.86 if side < 0 else -0.02, 1.02 if side < 0 else 0.14, 1.02, 2.2, rng)
    weather_fx(S, ground=0.62)
    return {0: 'beaver dam of sticks across a stream, a lodge in the pond', 1: 'beaver dam with the stump-plan on the right',
            2: 'big beaver lodge in a forest pond, low dam in front'}[v]


@biome('savanna')
def savanna(S):
    v = S.variant % 3
    rng = S.rng
    hz = 0.6
    sky(S, horizon=hz)
    far = S.L('far')
    hills(far, hz + 0.01, 0.04, '#b9a6b0', seed=S.seed, freqs=(0.6, 1.5, 3.0))
    if S.look.time in ('day', 'golden') and S.weather == 'clear':
        with far.piece(0.2) as d:  # heat haze: pale wavering bands over the horizon
            for k in range(4):
                y = hz + 0.005 + k * 0.012
                d.poly([(u, y + 0.004 * math.sin(u * 40 + k)) for u in np.linspace(-0.02, 1.02, 60)] +
                       [(u, y + 0.007 + 0.004 * math.sin(u * 40 + k + 1)) for u in np.linspace(1.02, -0.02, 60)], (255, 246, 220, 70))
    mid = S.L('mid')
    f = hills(mid, hz + 0.05, 0.025, '#d9b75a', seed=S.seed + 1, freqs=(0.7, 1.9, 4.0))
    patches(mid, f, 0.82, 10, rng, ['#c9a54a', '#e2c46a'])
    for k in range(5):  # distant acacias
        x = S.r(0.02, 0.98)
        acacia(mid, x, f(x) + 0.01, 0.35 + S.r(0, 0.15), leaf='#8a9a5a')
    cx = S.r(0.2, 0.5) if v != 1 else 0.7
    herd = {0: 'giraffe', 1: 'zebra', 2: 'elephant'}[v]
    for i in range(4 + v):
        x = cx + S.r(-0.14, 0.14)
        y = f(x) + 0.02 + S.r(0, 0.03)
        if herd == 'giraffe':
            giraffe(mid, x, y, 1.5 + S.r(0, 0.4), face=S.pick([-1, 1]))
        elif herd == 'zebra':
            zebra_animal(mid, x, y, 1.7, face=S.pick([-1, 1]))
        else:
            elephant(mid, x, y, 1.5 + S.r(0, 0.4), face=S.pick([-1, 1]), col='#8a8296')
    near = S.L('near')
    g = hills(near, 0.82, 0.03, '#e2c46a', seed=S.seed + 2, freqs=(0.6, 1.4, 3.3))
    patches(near, g, 1.0, 8, rng, ['#d4b250', '#c9a54a'])
    if v == 0:
        acacia(near, 0.74, g(0.74) + 0.02, 2.4, leaf='#6f8f45')
    elif v == 1:
        acacia(near, 0.18, g(0.18) + 0.02, 2.2, leaf='#6f8f45')
        acacia(near, 0.88, g(0.88) + 0.02, 1.4, leaf='#7a9a4a')
    else:
        with near.piece(0.9) as d:  # a termite mound and a waterhole
            d.poly([(0.74, g(0.74) + 0.03), (0.77, 0.52), (0.79, 0.5), (0.82, 0.56), (0.84, 0.58), (0.87, g(0.87) + 0.03)], '#b0703f')
            d.poly([(0.79, 0.5), (0.8, 0.52), (0.8, 0.7), (0.78, 0.7)], shade('#b0703f', 0.85))
        with near.piece(0.4) as d:
            d.ell(0.32, 0.9, 0.16, 0.03, mixc('#7aa6c0', to255(S.look.sky_cols()[1]), 0.4))
        acacia(near, 0.1, g(0.1) + 0.03, 1.6, leaf='#6f8f45')
    fg = S.L('fg')
    with fg.piece(0.8) as d:  # tall dry grass on the edges
        for k in range(70):
            x = S.r(-0.02, 0.3) if k % 2 else S.r(0.72, 1.02)
            h = S.r(0.08, 0.2)
            d.line([(x, 1.02), (x + S.r(-0.03, 0.03), 1.02 - h)], S.pick(['#d9b75a', '#c9a54a', '#e6cc7a', '#b8954a']), 0.004)
    weather_fx(S, ground=hz + 0.05)
    return {0: 'savanna with a lone umbrella acacia and giraffes far away', 1: 'savanna with zebras and acacias framing',
            2: 'savanna with a termite mound, a waterhole and elephants'}[v]


@biome('ice_floe')
def ice_floe(S):
    v = S.variant % 3
    rng = S.rng
    hz = 0.48
    sky(S, horizon=hz)
    far = S.L('far')
    sea = mixc('#2f6fa8', S.look.T['bot'], 0.2)
    water(far, hz, col=sea, col2='#5a92c8', seed=S.seed, bottom=1.02)
    with far.piece(0.9) as d:  # a far iceberg
        x = 0.25 if v != 2 else 0.7
        s = 1.0 if v != 2 else 2.0
        pts = [(x - 0.1 * s, hz + 0.005), (x - 0.06 * s, hz - 0.06 * s), (x - 0.02 * s, hz - 0.075 * s), (x + 0.01 * s, hz - 0.12 * s),
               (x + 0.05 * s, hz - 0.08 * s), (x + 0.09 * s, hz - 0.05 * s), (x + 0.12 * s, hz + 0.005)]
        d.poly(pts, '#eef4fa')
        d.poly([(x + 0.01 * s, hz - 0.12 * s), (x + 0.05 * s, hz - 0.08 * s), (x + 0.09 * s, hz - 0.05 * s), (x + 0.12 * s, hz + 0.005), (x + 0.02 * s, hz + 0.005)], '#c9dcee')
    if S.look.time in ('golden', 'dusk', 'night') and S.weather == 'clear':
        reflection(far, S.look.T['sun'][0], hz + 0.005, 0.05, S.look.T['sun'][2] if S.time != 'night' else '#f6efd2', n=12)
    mid = S.L('mid')
    for k in range(6):  # small floes on the open water
        x, y = S.r(0, 1), S.r(hz + 0.04, 0.66)
        w = 0.02 + 0.05 * (y - hz) / 0.2
        with mid.piece(0.6) as d:
            d.ell(x, y, w, w * 0.18, '#c9dcee')
            d.ell(x, y - w * 0.04, w * 0.95, w * 0.15, '#f4f8fc')
    near = S.L('near')
    top = 0.74 if v != 1 else 0.7
    with near.piece(1.0) as d:  # the big floe in front: a white top and a blue edge
        pts = [(-0.03, top + 0.02), (0.1, top - 0.005), (0.3, top + 0.01), (0.55, top - 0.01), (0.75, top + 0.008), (0.92, top - 0.004), (1.03, top + 0.015)]
        d.poly(pts + [(1.03, top + 0.06), (-0.03, top + 0.07)], '#8fb8dc')
        d.poly(pts + [(1.03, 1.03), (-0.03, 1.03)], '#f4f8fc')
        d.poly([(x, y + 0.035) for x, y in pts] + [(1.03, top + 0.07), (-0.03, top + 0.08)], '#a9cbe8')
    with near.piece(0.35) as d:  # cracks and soft blue shadows on the floe
        for k in range(5):
            x = S.r(0.05, 0.95)
            y = S.r(top + 0.1, 0.95)
            d.line([(x, y), (x + S.r(-0.05, 0.05), y + 0.02), (x + S.r(-0.08, 0.08), y + 0.04)], '#b9d2ea', 0.003)
        for k in range(4):
            d.ell(S.r(0, 1), S.r(top + 0.12, 0.98), S.r(0.06, 0.14), 0.012, '#dfeaf6')
    if v == 1:  # a pressure ridge of tilted ice slabs and a seal hole
        with near.piece(0.9) as d:
            for k in range(8):
                x = 0.62 + k * 0.045
                d.poly([(x, top + 0.12), (x + 0.03, top + 0.02 - 0.03 * (k % 3)), (x + 0.055, top + 0.12)], S.pick(['#eaf2fa', '#d4e4f2', '#f6fafd']))
        with near.piece(0.4) as d:
            d.ell(0.25, 0.9, 0.06, 0.015, sea)
    elif v == 2:
        with near.piece(0.9) as d:  # snow drifts
            for x in (0.15, 0.85):
                d.ell(x, top + 0.07, 0.14, 0.035, '#fbfdff')
                d.ell(x + 0.02, top + 0.085, 0.12, 0.012, '#d4e4f2')
    else:
        with near.piece(0.9) as d:  # ice hummocks on the left and a block on the right
            for x, w, h in ((0.06, 0.07, 0.07), (0.13, 0.05, 0.045), (0.86, 0.06, 0.05)):
                d.poly([(x - w, top + 0.1), (x - w * 0.4, top + 0.1 - h), (x + w * 0.2, top + 0.1 - h * 1.2), (x + w, top + 0.1)], '#eef4fa')
                d.poly([(x + w * 0.2, top + 0.1 - h * 1.2), (x + w, top + 0.1), (x + w * 0.1, top + 0.1)], '#cfe0f0')
    fg = S.L('fg')
    with fg.piece() as d:  # ice chunks in the water at the bottom corners
        for x, y, w in ((0.04, 0.99, 0.08), (0.95, 1.0, 0.1), (0.85, 0.97, 0.04)):
            d.ell(x, y, w, w * 0.4, '#e6f0fa')
    weather_fx(S, ground=hz + 0.05)
    return {0: 'white ice floe on the open sea, an iceberg far away', 1: 'ice floe with a pressure ridge and a seal hole',
            2: 'ice floe with snow drifts and a big iceberg'}[v]


# ---------------------------------------------------------------- industry and the shore

@biome('new_building')
def new_building(S):
    v = S.variant % 3
    rng = S.rng
    sky(S, horizon=0.55)
    far = S.L('far')
    skyline(far, 0.62, rng, 0.06, 0.2, cols=['#a3aac4', '#b2b8cc'])
    concrete = '#b4b0a8'
    mid = S.L('mid')
    if v == 1:  # the view from an empty window: the wall of the next block fills it
        block(mid, 0.12, 0.7, 0.98, 12, '#d8cfc2', rng, fh=0.06)
        block(mid, 0.74, 1.0, 0.98, 9, '#c9d2d8', rng, fh=0.06)
        crane(mid, 0.78, 0.6, 1.0, face=-1)
        fg = S.L('fg')
        with fg.piece(1.0) as d:  # bare concrete around a window hole
            d.rect(-0.02, -0.02, 1.02, 0.14, concrete)
            d.rect(-0.02, 0.82, 1.02, 1.02, concrete)
            d.rect(-0.02, -0.02, 0.14, 1.02, concrete)
            d.rect(0.86, -0.02, 1.02, 1.02, concrete)
        with fg.piece(0.4) as d:  # formwork marks, a radiator, a cable
            for y in (0.04, 0.09):
                d.rect(-0.02, y, 1.02, y + 0.003, shade(concrete, 0.9))
            d.rect(0.3, 0.88, 0.7, 0.97, '#e6e6e0', r=0.006)
            for k in range(12):
                d.rect(0.31 + k * 0.032, 0.89, 0.325 + k * 0.032, 0.96, '#d4d4ce', r=0.003)
            d.line([(0.07, -0.02), (0.07, 0.3), (0.1, 0.34)], '#2e2e36', 0.004)
            d.rect(0.135, 0.8, 0.865, 0.83, shade(concrete, 0.85))
        near = S.L('near')
        with near.piece(0.5) as d:  # puddle on the yard far below between the blocks
            d.rect(0.14, 0.78, 0.86, 0.82, '#8a8478')
        weather_fx(S, ground=0.8)
        return 'view from an unfinished flat: the wall of the next new block'
    # the concrete shell: floors, columns, empty window holes, rebar on the top
    x0, x1, base = (0.38, 0.86, 0.72) if v == 0 else (0.5, 0.82, 0.7)
    floors = 9 if v == 0 else 7
    fh = 0.052
    with mid.piece(0.9) as d:
        d.rect(x0, base - floors * fh, x1, base, concrete)
        for f in range(floors):
            y = base - (f + 1) * fh
            d.rect(x0 - 0.004, y, x1 + 0.004, y + 0.008, shade(concrete, 0.88))
    n = int((x1 - x0) / 0.04)
    with mid.piece(0.4) as d:
        for f in range(floors - 1):
            y = base - (f + 1) * fh + 0.016
            for k in range(n):
                wx = x0 + (k + 0.25) * (x1 - x0) / n
                d.rect(wx, y, wx + (x1 - x0) / n * 0.5, y + fh * 0.55, '#3a3a44')
        for k in range(14):
            x = x0 + 0.01 + k * (x1 - x0 - 0.02) / 13
            d.line([(x, base - (floors - 1) * fh + 0.004), (x + 0.003, base - floors * fh - 0.03)], '#7a5a4a', 0.003)
    if v == 2:
        block(mid, 0.1, 0.42, 0.7, 12, '#e6d8c4', rng, fh=0.045)
    crane(mid, x0 - 0.06 if v == 0 else 0.46, base, 1.25 if v == 0 else 1.1, face=1)
    near = S.L('near')
    g = ridge_fn(S.seed, 0.74, 0.015)
    with near.piece(0.6) as d:  # wasteland
        d.ridge(g, '#a89070')
    patches(near, g, 1.0, 8, rng, ['#9a8262', 'grass2', '#b9a07a'])
    puddle(near, 0.5, 0.9, 0.12, 0.025, S)
    with near.piece(0.9) as d:  # dirt pile and a stack of slabs
        d.pie(0.16, 0.86, 0.1, 180, 360, '#8f7a5a')
        for k in range(4):
            d.rect(0.72, 0.86 - k * 0.018, 0.88, 0.876 - k * 0.018, shade(concrete, 0.95 + 0.03 * k), r=0.003)
    with near.piece(0.9) as d:  # a construction fence of blue panels
        for k in range(9):
            x = -0.02 + k * 0.045
            if x > 0.36:
                break
            d.rect(x, 0.72, x + 0.043, 0.8, '#3f6fa8' if k % 2 else '#4a7fb8')
    fg = S.L('fg')
    with fg.piece() as d:  # weeds and a rebar bundle in front
        for k in range(5):
            d.line([(0.78 + k * 0.01, 1.0), (0.98, 0.93 + k * 0.004)], '#7a5a4a', 0.004)
    grass_tufts(fg, 0.95, 1.0, 12, rng, s=2.0)
    weather_fx(S, ground=0.72)
    return {0: 'new apartment block shell with a tower crane on a wasteland', 2: 'new blocks on the city edge, one finished, one a shell'}[v]


@biome('oil_depot')
def oil_depot(S):
    v = S.variant % 3
    rng = S.rng
    hz = 0.58
    sky(S, horizon=hz)
    far = S.L('far')
    hills(far, hz + 0.01, 0.04, '#b2b6cc' if not winter(S) else '#e0e6ee', seed=S.seed, freqs=(0.8, 2.0, 4.0))
    mid = S.L('mid')
    with mid.piece(0.4) as d:
        d.rect(-0.02, hz + 0.02, 1.02, 1.02, 'steppe2' if not winter(S) else '#e6ecf2')
    stripes = ['#c0443a', '#3f7fbf', '#3d8a5a']
    xs = [0.12, 0.34, 0.6, 0.84] if v != 1 else [0.08, 0.92]
    for i, x in enumerate(xs):
        tank(mid, x, 0.72, 0.21 if v != 1 else 0.16, 0.26 if i % 2 else 0.32, stripe=stripes[i % 3])
    with mid.piece(0.6) as d:  # a pipe rack between the tanks
        d.rect(-0.02, 0.62, 1.02, 0.63, '#8a8f99')
        d.rect(-0.02, 0.64, 1.02, 0.65, '#a8acb4')
        for k in range(12):
            d.rect(k * 0.09, 0.6, k * 0.09 + 0.005, 0.72, '#7a7a86')
    if S.look.lit_share > 0.2:  # red lamps on the tank tops
        for i, x in enumerate(xs):
            mid.flat().circ(x, 0.72 - (0.26 if i % 2 else 0.32) - 0.025, 0.005, '#ff5040', lit=True)
            mid.glow_circ(x, 0.72 - (0.26 if i % 2 else 0.32) - 0.025, 0.02)
    near = S.L('near')
    with near.piece(0.4) as d:  # concrete yard with slab joints and oil stains
        d.rect(-0.02, 0.74, 1.02, 1.02, '#a8a39a')
        for k in range(8):
            d.rect(-0.02, 0.74 + k * 0.04, 1.02, 0.742 + k * 0.04, '#9a958c')
        for k in range(12):
            d.rect(k * 0.09, 0.74, k * 0.09 + 0.002, 1.02, '#9a958c')
        for k in range(4):
            d.ell(S.r(0.35, 0.65), S.r(0.88, 0.98), S.r(0.03, 0.06), 0.01, '#8a857c')
    with near.piece(0.8) as d:  # a ground pipe with a valve wheel
        d.rect(-0.02, 0.765, 1.02, 0.782, '#7a8a96', r=0.006)
        d.circ(0.5, 0.758, 0.022, '#c0443a')
        d.circ(0.5, 0.758, 0.012, '#a8a39a')
        d.rect(0.497, 0.76, 0.503, 0.775, '#c0443a')
    bc = ['#3f7fbf', '#c0443a', '#3d8a5a', '#e9b443', '#4a4a58']
    rows = [(0.02, 0.3), (0.7, 0.98)] if v != 1 else [(0.02, 0.36), (0.64, 0.98)]
    for (a, b) in rows:  # barrels on pallets, two tiers
        with near.piece(0.9) as d:
            n = int((b - a) / 0.07)
            for j in range(2 if v != 2 else 1):
                y = 0.86 - j * 0.11
                d.rect(a - 0.005, y, b + 0.005, y + 0.015, '#b98a5e')
                for k in range(n):
                    barrel(d, a + 0.035 + k * (b - a - 0.04) / max(n - 1, 1), y, 1.2, bc[(k + j + int(a * 10)) % 5] if v != 2 else bc[(k // 3) % 5])
    if v == 1:  # a gantry crane over the barrel yard
        with mid.piece(0.8) as d:
            for x in (0.2, 0.8):
                d.rect(x - 0.012, 0.32, x + 0.012, 0.76, '#e9b443')
                d.line([(x - 0.04, 0.76), (x + 0.04, 0.76)], '#3a3a40', 0.012)
            d.rect(0.15, 0.3, 0.85, 0.34, '#e9b443')
            for k in range(14):
                x = 0.16 + k * 0.05
                d.line([(x, 0.3), (x + 0.025, 0.34)], shade('#e9b443', 0.8), 0.003)
            d.rect(0.46, 0.34, 0.54, 0.38, '#3a3a40', r=0.004)
            d.line([(0.5, 0.38), (0.5, 0.55)], '#2e2e36', 0.003)
            barrel(d, 0.5, 0.63, 1.0, '#c0443a')
    if v == 2:  # rail tank wagons
        with near.piece(0.9) as d:
            d.rect(-0.02, 0.8, 1.02, 0.808, '#6a5a4a')
            for k in range(3):
                x = 0.36 + k * 0.14
                d.rect(x - 0.065, 0.69, x + 0.065, 0.775, ['#3a3a40', '#4a4a58', '#3a3a40'][k], r=0.04)
                d.rect(x - 0.012, 0.67, x + 0.012, 0.69, '#3a3a40')
                d.rect(x - 0.07, 0.775, x + 0.07, 0.785, '#2e2e36')
                for u in (-0.045, -0.025, 0.025, 0.045):
                    d.circ(x + u, 0.792, 0.011, '#2e2e36')
    fg = S.L('fg')
    with fg.piece() as d:  # chain-link fence posts and a top wire
        for x in (0.03, 0.97):
            d.rect(x - 0.006, 0.55, x + 0.006, 1.02, '#7a7a86')
        d.line([(-0.02, 0.58), (0.03, 0.58)], '#7a7a86', 0.004)
        d.line([(0.97, 0.58), (1.02, 0.58)], '#7a7a86', 0.004)
    with fg.piece(0.3) as d:
        for k in range(10):
            d.line([(-0.02, 0.6 + k * 0.04), (0.03, 0.64 + k * 0.04)], (150, 150, 160, 160), 0.002)
            d.line([(0.97, 0.6 + k * 0.04), (1.02, 0.64 + k * 0.04)], (150, 150, 160, 160), 0.002)
    weather_fx(S, ground=0.7)
    return {0: 'oil depot: round tanks, a pipe rack and barrels on pallets', 1: 'barrel yard under a gantry crane',
            2: 'oil depot with rail tank wagons and barrels'}[v]


@biome('beach_pier')
def beach_pier(S):
    v = S.variant % 3
    rng = S.rng
    hz = 0.52
    sky(S, horizon=hz)
    far = S.L('far')
    sea = mixc('#3f8fc0', S.look.T['bot'], 0.25)
    water(far, hz, col=sea, col2='#6ab0dc', seed=S.seed, bottom=0.8)
    boat(far, S.r(0.55, 0.85), hz + 0.02, 0.6)
    if S.look.time in ('golden', 'dusk', 'night') and S.weather == 'clear':
        reflection(far, S.look.T['sun'][0], hz + 0.005, 0.05, S.look.T['sun'][2] if S.time != 'night' else '#f6efd2', n=10)
    sk = S.L('sky')
    if not S.look.night:
        for k in range(5):
            gull(sk, S.r(0.1, 0.9), S.r(0.15, 0.35), 1.2 + S.r(0, 0.8))
    mid = S.L('mid')
    with mid.piece(0.5) as d:  # surf line
        d.rect(-0.02, 0.69, 1.02, 0.74, shade(sea, 1.15))
        for k in range(14):
            d.ell(k / 13, 0.735, 0.06, 0.01, '#f3f7fa')
    with mid.piece(0.9) as d:  # the buoy
        bx = 0.3 if v != 1 else 0.62
        d.circ(bx, 0.6, 0.02, '#e05a3a')
        d.rect(bx - 0.012, 0.596, bx + 0.012, 0.604, '#f6f3ea')
        d.rect(bx - 0.002, 0.555, bx + 0.002, 0.585, '#3a3a40')
        d.ell(bx, 0.618, 0.03, 0.005, shade(sea, 1.2))
    if S.look.lit_share > 0.2:
        mid.flat().circ(bx, 0.552, 0.005, '#ffd36e', lit=True)
        mid.glow_circ(bx, 0.552, 0.02)
    # the wooden pier
    if v == 0:
        px0, px1, py = 0.52, 1.03, 0.62
    elif v == 1:
        px0, px1, py = -0.03, 0.42, 0.64
    else:
        px0, px1, py = 0.6, 1.03, 0.6
    with mid.piece(0.9) as d:
        for k in range(int((px1 - px0) / 0.04) + 1):
            x = px0 + 0.01 + k * 0.04
            d.rect(x - 0.005, py, x + 0.005, 0.76, '#6a4a33')
        d.rect(px0, py - 0.022, px1, py, '#b98a5e', r=0.003)
        for k in range(int((px1 - px0) / 0.016)):
            x = px0 + k * 0.016
            d.rect(x, py - 0.022, x + 0.002, py, shade('#b98a5e', 0.85))
        d.rect(px0, py - 0.06, px1, py - 0.054, '#8a5a3a')
        for k in range(int((px1 - px0) / 0.08) + 1):
            x = px0 + 0.005 + k * 0.08
            d.rect(x - 0.003, py - 0.06, x + 0.003, py - 0.02, '#8a5a3a')
    if v == 2:  # a lamp at the pier head
        lamp_post(mid, 0.64, py - 0.02, 0.9)
    near = S.L('near')
    g = ridge_fn(S.seed, 0.76, 0.015)
    with near.piece(0.6) as d:
        d.ridge(g, '#f1dfae')
    with near.piece(0.4) as d:  # wet sand band and shells
        d.poly([(x, g(x)) for x in np.linspace(-0.02, 1.02, 30)] + [(1.02, 0.79), (-0.02, 0.79)], '#d9c08a')
        for k in range(16):
            d.ell(S.r(0, 1), S.r(0.84, 0.98), 0.006, 0.004, S.pick(['#f6e7d8', '#e9c8b0', '#c9c1b0']))
    cols = [('#e05a5a', '#f6f3ea'), ('#3f7fbf', '#f6d353'), ('#3d8a5a', '#f6f3ea')]
    spots = (0.12, 0.84) if v != 2 else (0.15,)
    for i, x in enumerate(spots):
        a, b = cols[i % 3]
        with near.piece(0.8) as d:  # beach umbrellas (closed in the evening variant)
            if v == 2 or S.look.time in ('night',):
                d.line([(x, 0.94), (x, 0.74)], '#8a5a3a', 0.006)
                d.poly([(x - 0.012, 0.86), (x + 0.012, 0.86), (x + 0.004, 0.72), (x - 0.004, 0.72)], a)
            else:
                d.line([(x, 0.94), (x + 0.02, 0.73)], '#8a5a3a', 0.006)
                d.pie(x + 0.02, 0.75, 0.1, 180, 360, a)
                for a0 in (195, 235, 275, 315):
                    d.pie(x + 0.02, 0.75, 0.1, a0, a0 + 20, b)
                d.rect(x + 0.04, 0.9, x + 0.15, 0.925, b if b != '#f6f3ea' else '#f6c453', r=0.006)
    if v == 2:  # a lifeguard tower
        with near.piece(0.9) as d:
            for u in (0.78, 0.9):
                d.line([(u, 0.92), (u + (0.84 - u) * 0.3, 0.68)], '#f3efe6', 0.008)
            d.rect(0.76, 0.6, 0.92, 0.68, '#e05a5a', r=0.004)
            d.poly([(0.75, 0.6), (0.93, 0.6), (0.84, 0.55)], '#f3efe6')
            d.rect(0.79, 0.62, 0.89, 0.66, '#cfe6f2' if not S.look.night else '#3a4870')
    fg = S.L('fg')
    with fg.piece() as d:  # a sandcastle or a bucket, dune grass
        if v == 1:
            d.rect(0.8, 0.94, 0.9, 1.0, '#e6cf96')
            for x in (0.8, 0.85, 0.9):
                d.rect(x - 0.012, 0.9, x + 0.012, 0.95, '#e6cf96')
        else:
            d.poly([(0.88, 1.0), (0.93, 1.0), (0.94, 0.93), (0.87, 0.93)], '#3f9fd0')
            d.line([(0.87, 0.93), (0.905, 0.9), (0.94, 0.93)], '#3a3a40', 0.003)
    with fg.piece(0.7) as d:
        for k in range(18):
            x = S.r(-0.02, 0.12)
            d.line([(x, 1.02), (x + S.r(-0.02, 0.02), 0.9 + S.r(0, 0.05))], '#9aa85a', 0.004)
    weather_fx(S, ground=0.72)
    return {0: 'sandy beach with a long wooden pier, a buoy and umbrellas', 1: 'beach with a pier from the left, a sandcastle',
            2: 'evening beach: closed umbrellas, a lifeguard tower, a pier lamp'}[v]


# ---------------------------------------------------------------- airport, burrow, anthill

def plane(d, x, y, s, tail='#3f7fbf', night=False):
    """An airliner seen from the side, facing left: fuselage, tail, wing, a window row (no markings)."""
    k = s / AR
    d.rect(x - 0.28 * k, y - 0.05 * s, x + 0.26 * k, y + 0.02 * s, '#f3f3f0', r=0.035 * s)
    d.poly([(x + 0.16 * k, y - 0.04 * s), (x + 0.26 * k, y - 0.05 * s), (x + 0.3 * k, y - 0.17 * s), (x + 0.25 * k, y - 0.17 * s)], tail)
    d.poly([(x - 0.06 * k, y), (x + 0.08 * k, y), (x + 0.16 * k, y + 0.06 * s), (x + 0.1 * k, y + 0.06 * s)], '#d8d8d4')
    d.rect(x - 0.02 * k, y + 0.03 * s, x + 0.06 * k, y + 0.055 * s, '#b8b8c0', r=0.012 * s)
    for i in range(16):
        d.circ(x - 0.2 * k + i * 0.025 * k, y - 0.025 * s, 0.005 * s, '#3a4870' if not night else '#ffd36e', lit=night)
    d.rect(x - 0.27 * k, y - 0.036 * s, x - 0.245 * k, y - 0.022 * s, '#3a4870', r=0.004)
    d.rect(x - 0.28 * k, y - 0.002 * s, x + 0.26 * k, y + 0.006 * s, tail)


@biome('airport', interior=True)
def airport(S):
    v = S.variant % 3
    rng = S.rng
    wall = ['#e6e8ea', '#e8e2d8', '#dfe6ea'][v]
    shell(S, wall=wall, floor='#b9b8b2', fy=0.72, kind='tiles', ceiling=0.07)
    sk = S.L('sky')
    # the big window wall: sky, tarmac and a plane outside
    wx0, wx1, wy0, wy1 = (0.04, 0.96, 0.14, 0.5) if v != 2 else (0.36, 0.96, 0.14, 0.5)
    out = Look(S.look.time, S.look.weather, S.look.season, S.look.palette, interior=False)
    c0, c1, c2 = S.look.sky_cols()
    ys = np.linspace(0, 1, int((wy1 - wy0) * 1080), dtype=np.float32)[:, None]
    col = c0 * (1 - ys[..., None]) + c2 * ys[..., None]
    from PIL import Image
    arr = np.broadcast_to(col, (len(ys), int((wx1 - wx0) * 1920), 3))
    sk.base.paste(Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), 'RGB').convert('RGBA'), (int(wx0 * 1920), int(wy0 * 1080)))
    night = S.look.night or S.look.time == 'dusk'
    with sk.piece(0.5) as d:
        d.rect(wx0, wy1 - 0.08, wx1, wy1, to255(out.col('#7a7a80', 0.2)))
        for k in range(8):
            d.rect(wx0 + k * 0.12, wy1 - 0.045, wx0 + k * 0.12 + 0.05, wy1 - 0.04, to255(out.col('#e8e4c0', 0.2)))
    with sk.piece(0.6) as d:
        plane(d, (wx0 + wx1) / 2 + 0.05, wy1 - 0.1, 1.15, tail=['#3f7fbf', '#c0443a', '#3d8a8a'][v], night=night)
    if night:
        for k in range(6):
            x = wx0 + 0.04 + k * (wx1 - wx0 - 0.08) / 5
            sk.flat().circ(x, wy1 - 0.065, 0.004, '#7fb6e8', lit=True)
            sk.glow_circ(x, wy1 - 0.065, 0.012)
    far = S.L('far')
    with far.piece(0.8) as d:  # mullions of the window wall
        t = 0.008
        d.rect(wx0 - t, wy0 - t, wx1 + t, wy0 + 0.004, '#9aa0a8')
        d.rect(wx0 - t, wy1 - 0.004, wx1 + t, wy1 + t, '#9aa0a8')
        n = int((wx1 - wx0) / 0.115)
        for k in range(n + 1):
            x = wx0 + (wx1 - wx0) * k / n
            d.rect(x - 0.004, wy0, x + 0.004, wy1, '#9aa0a8')
        d.rect(wx0, (wy0 + wy1) / 2 - 0.003, wx1, (wy0 + wy1) / 2 + 0.003, '#9aa0a8')
    ceiling_panels(far, 0.07, 5, lit=True)
    if v == 2:  # a big wall-hung dot board on the left
        bx0, bx1, by0, by1 = 0.04, 0.32, 0.16, 0.48
    else:  # a hanging dot board over the belt
        bx0, bx1, by0, by1 = 0.38, 0.62, 0.51, 0.585
    with far.piece(0.8) as d:
        if v != 2:
            d.line([(0.41, 0.07), (0.41, by0)], '#5a5a66', 0.003)
            d.line([(0.59, 0.07), (0.59, by0)], '#5a5a66', 0.003)
        d.rect(bx0, by0, bx1, by1, '#1e2230', r=0.006)
    rows = 6 if v == 2 else 3
    fd = far.flat()
    for r_ in range(rows):  # rows of amber dots: blocks of dots, never letters
        y = by0 + 0.02 + r_ * (by1 - by0 - 0.03) / rows
        x = bx0 + 0.015
        while x < bx1 - 0.02:
            w = int(rng.integers(3, 9))
            for i in range(w):
                for j in range(3):
                    if rng.random() < 0.75:
                        fd.circ(x + i * 0.0045, y + j * 0.008, 0.0022, '#ffc24a' if r_ % 3 else '#7fe07a', lit=True)
            x += w * 0.0045 + 0.015
    far.glow_rect(bx0, by0, bx1, by1)
    mid = S.L('mid')
    # the baggage belt
    with mid.piece(1.0) as d:
        if v == 1:  # an oval carousel seen from the front: two runs and round ends
            d.rect(0.12, 0.66, 0.88, 0.7, '#4a4a54', r=0.02)
            d.rect(0.08, 0.7, 0.92, 0.8, '#9aa0a8', r=0.02)
            d.rect(0.1, 0.71, 0.9, 0.735, '#3a3a44', r=0.01)
        else:
            d.rect(-0.02, 0.68, 1.02, 0.79, '#9aa0a8')
            d.rect(-0.02, 0.685, 1.02, 0.715, '#3a3a44')
    with mid.piece(0.4) as d:
        for k in range(46):
            x = -0.02 + k * 0.023
            if v == 1 and not (0.1 < x < 0.9):
                continue
            d.rect(x, 0.688 if v != 1 else 0.713, x + 0.002, 0.712 if v != 1 else 0.733, '#5a5a66')
    if v != 1:  # the curtain where bags come out
        with mid.piece(0.8) as d:
            cx = 0.12 if v == 0 else 0.22
            d.rect(cx - 0.08, 0.48, cx + 0.08, 0.715, '#8a8f99', r=0.01)
            d.rect(cx - 0.065, 0.51, cx + 0.065, 0.712, '#1e1e26', r=0.006)
            for k in range(9):
                x = cx - 0.062 + k * 0.0138
                d.rect(x, 0.515, x + 0.012, 0.71, '#3a3a46', r=0.004)
    bags = ['#c0443a', '#3f7fbf', '#2e2e36', '#e9b443', '#3d8a5a', '#8a5a7a', '#f28b6b', '#7a7a86']
    ys_ = 0.7 if v != 1 else 0.72
    with mid.piece(0.9) as d:
        x = 0.24 if v != 1 else 0.14
        while x < 0.95:
            w, h = S.r(0.05, 0.08), S.r(0.07, 0.11)
            if rng.random() < 0.8:
                suitcase(mid, x + w / 2, ys_, w, h, S.pick(bags), d=d)
            x += w + S.r(0.02, 0.07)
    near = S.L('near')
    with near.piece(1.0) as d:  # luggage trolleys
        for x in (0.06, 0.82):
            d.line([(x, 0.82), (x, 0.95)], '#8a8f99', 0.006)
            d.line([(x, 0.95), (x + 0.1, 0.95)], '#8a8f99', 0.006)
            d.line([(x - 0.01, 0.82), (x + 0.01, 0.82)], '#2e2e36', 0.008)
            d.circ(x + 0.01, 0.97, 0.012, '#2e2e36')
            d.circ(x + 0.09, 0.97, 0.012, '#2e2e36')
        suitcase(near, 0.1, 0.945, 0.06, 0.08, bags[1], d=d)
    fg = S.L('fg')
    with fg.piece() as d:  # a column on the right edge and a row of seats on the left
        d.rect(0.95, -0.02, 1.02, 1.02, shade(wall, 0.85))
        d.rect(0.945, 0.86, 1.02, 1.02, shade(wall, 0.7))
    plant(fg, 0.92, 1.0, 2.0)
    clock(far, 0.92 if v != 2 else 0.18, 0.1 if v != 2 else 0.11, 0.03)
    return {0: 'airport baggage claim: a belt with suitcases, a dot board, a plane outside',
            1: 'airport baggage carousel with suitcases and a big window', 2: 'baggage claim with a big dot board on the wall'}[v]


@biome('burrow', interior=True)
def burrow(S):
    v = S.variant % 3
    rng = S.rng
    shell(S, wall='#a7805a', floor='#8a6646', fy=0.76, kind='carpet', skirting=False)
    sk = S.L('sky')
    with sk.piece(0.4) as d:  # pebbles and soil streaks in the back wall
        for k in range(60):
            d.ell(S.r(0, 1), S.r(0.05, 0.72), S.r(0.004, 0.012), S.r(0.003, 0.008), S.pick(['#8f6a48', '#b99470', '#97734e', '#c2a07a']))
        for k in range(6):
            y = S.r(0.15, 0.65)
            d.poly([(u, y + 0.01 * math.sin(u * 7 + k)) for u in np.linspace(-0.02, 1.02, 30)] +
                   [(u, y + 0.006 + 0.01 * math.sin(u * 7 + k)) for u in np.linspace(1.02, -0.02, 30)], '#9a7552')
    for x, r in (((0.14, 0.12), (0.87, 0.1)) if v != 2 else ((0.12, 0.1),)):  # tunnel openings
        with sk.piece(0.9) as d:
            d.ell(x, 0.62, r, r * 1.1, '#6a4c34')
            d.ell(x, 0.64, r * 0.82, r * 0.95, '#2e2018')
    if v == 2:  # a round window up to the outside: grass and sky
        c0, c1, c2 = S.look.sky_cols()
        with sk.piece(0.8) as d:
            d.circ(0.8, 0.3, 0.13, '#6a4c34')
            d.circ(0.8, 0.3, 0.11, to255(c1))
            d.ell(0.8, 0.38, 0.11, 0.04, '#6fae5e' if S.season != 'winter' else '#e6ecf2')
            for k in range(6):
                a = math.pi * k / 3
                d.line([(0.8, 0.3), (0.8 + math.cos(a) * 0.11 / AR, 0.3 + math.sin(a) * 0.11)], '#8a5a3a', 0.006)
    far = S.L('far')
    with far.piece(0.7) as d:  # roots hanging from the ceiling
        for k in range(16):
            x = S.r(0.0, 1.0)
            ln = S.r(0.06, 0.2)
            pts = [(x + 0.01 * math.sin(t * 6 + k), -0.02 + ln * t) for t in np.linspace(0, 1, 10)]
            d.line(pts, '#6a4a33', 0.005)
            d.line([pts[4], (pts[4][0] + 0.02, pts[4][1] + 0.04)], '#6a4a33', 0.003)
    if v == 1:  # pantry shelves cut into the wall with jars and acorns
        with far.piece(0.8) as d:
            for y in (0.3, 0.46):
                d.rect(0.3, y, 0.7, y + 0.014, '#7a5a3a', r=0.003)
        with far.piece(0.7) as d:
            for j, y in enumerate((0.3, 0.46)):
                x = 0.32
                while x < 0.68:
                    if rng.random() < 0.5:
                        d.rect(x, y - 0.07, x + 0.035, y, (220, 236, 240, 200), r=0.008)
                        d.rect(x + 0.004, y - 0.045, x + 0.031, y - 0.004, S.pick(['#e05a5a', '#e9b443', '#8a3a6a', '#f28b6b']), r=0.006)
                        d.rect(x - 0.002, y - 0.08, x + 0.037, y - 0.068, '#c0443a', r=0.003)
                        x += 0.045
                    else:
                        d.ell(x + 0.012, y - 0.016, 0.014, 0.016, '#a8743e')
                        d.ell(x + 0.012, y - 0.03, 0.016, 0.008, '#6a4a2a')
                        x += 0.03
    else:  # a little framed picture of a leaf and a clock
        with far.piece(0.7) as d:
            d.rect(0.44, 0.22, 0.56, 0.36, '#7a5a3a', r=0.004)
            d.rect(0.45, 0.235, 0.55, 0.345, '#f3ead6')
            d.ell(0.5, 0.29, 0.03, 0.04, '#6fae5e')
            d.line([(0.5, 0.25), (0.5, 0.33)], '#3d7a3a', 0.003)
        clock(far, 0.32, 0.3, 0.03)
    lamp_pendant(far, 0.5 if v != 1 else 0.5, 0.15, 1.0, col='#c9a24a')
    far.glow_circ(0.5, 0.18, 0.2)
    mid = S.L('mid')
    if v == 0:  # a moss armchair and a stump table with a mug
        with mid.piece(0.9) as d:
            d.rect(0.2, 0.56, 0.34, 0.76, '#5a8a48', r=0.04)
            d.rect(0.22, 0.66, 0.32, 0.72, '#6f9e58', r=0.02)
            d.rect(0.62, 0.66, 0.72, 0.76, '#8a6a48', r=0.006)
            d.ell(0.67, 0.66, 0.06, 0.016, '#c9a87a')
        with mid.piece(0.7) as d:
            d.rect(0.655, 0.62, 0.685, 0.655, '#e6e0d4', r=0.005)
            d.line([(0.685, 0.63), (0.692, 0.64), (0.685, 0.648)], '#e6e0d4', 0.004)
    elif v == 1:  # sacks of seeds
        with mid.piece(0.9) as d:
            for x, c in ((0.22, '#c9b08a'), (0.3, '#b99a6a'), (0.74, '#d4bc94')):
                d.rect(x - 0.04, 0.62, x + 0.04, 0.76, c, r=0.03)
                d.ell(x, 0.62, 0.025, 0.012, shade(c, 0.85))
    else:  # a bed of leaves under a patched blanket
        with mid.piece(0.9) as d:
            d.rect(0.42, 0.64, 0.7, 0.76, '#8a6a48', r=0.02)
            for k in range(10):
                d.ell(0.43 + k * 0.03, 0.645, 0.03, 0.014, S.pick(['#e08a3a', '#e9b443', '#c9532e']))
            d.rect(0.5, 0.635, 0.7, 0.68, '#3f7fbf', r=0.01)
            d.rect(0.56, 0.635, 0.62, 0.68, '#e9a23a')
            d.ell(0.465, 0.632, 0.035, 0.018, '#f3ead6')
    near = S.L('near')
    rug(near, 0.5, 0.87, 0.3, 0.06, col='#c0443a', col2='#e9b443')
    fg = S.L('fg')
    with fg.piece() as d:  # the earthen arch framing the hall
        pts = [(-0.03, -0.03), (1.03, -0.03), (1.03, 1.03), (0.96, 1.03)]
        for t in np.linspace(0, 1, 40):
            a = math.pi * t
            pts.append((0.5 + 0.47 * math.cos(a), 1.03 - 0.98 * math.sin(a) ** 0.6))
        pts += [(0.04, 1.03), (-0.03, 1.03)]
        d.poly(pts, '#5a3e2a')
    with fg.piece(0.6) as d:  # roots poking through the arch
        for k in range(6):
            x = S.r(0.15, 0.85)
            d.line([(x, 0.0), (x + S.r(-0.02, 0.02), S.r(0.07, 0.12))], '#3e2a1c', 0.006)
    return {0: 'underground burrow hall with a moss armchair, a hanging bulb and a rug',
            1: 'burrow pantry with jars and acorns on earthen shelves', 2: 'burrow bedroom with a leaf bed and a round window'}[v]


@biome('anthill')
def anthill(S):
    v = S.variant % 3
    rng = S.rng
    soil, soil2, tun = '#8a6646', '#7a583c', '#c9a77a'
    if v == 2:  # deep inside: a storage chamber, all earth
        sky_gradient(S, cols=[hx('#5a3e2a'), hx('#6a4a33'), hx('#7a583c')], horizon=1.0)
        S.look.haze_col = hx('#4a3424')
        sk = S.L('sky')
        with sk.piece(0.5) as d:
            for k in range(80):
                d.ell(S.r(0, 1), S.r(0, 1), S.r(0.004, 0.014), S.r(0.003, 0.01), S.pick(['#6a4a33', '#8f6a48', '#5a3e2a']))
        far = S.L('far')
        with far.piece(0.8) as d:  # the chamber: a big lighter hollow, tunnels leading off
            d.ell(0.5, 0.56, 0.62, 0.36, '#a8845c')
            for (x0, y0, x1, y1) in ((0.0, 0.3, 0.18, 0.45), (1.0, 0.25, 0.82, 0.45), (0.4, -0.02, 0.48, 0.24)):
                d.line([(x0, y0), (x1, y1)], '#a8845c', 0.09)
        with far.piece(0.4) as d:
            for (x0, y0, x1, y1) in ((0.0, 0.3, 0.18, 0.45), (1.0, 0.25, 0.82, 0.45), (0.4, -0.02, 0.48, 0.24)):
                d.line([(x0, y0), ((x0 + x1) / 2, (y0 + y1) / 2)], '#5a3e2a', 0.05)
        mid = S.L('mid')
        with mid.piece(0.9) as d:  # piles of crumbs and seeds
            for cx, n in ((0.24, 22), (0.78, 18)):
                for k in range(n):
                    a = rng.random() * math.pi
                    rr = rng.random() ** 0.5 * 0.1
                    d.ell(cx + math.cos(a) * rr / AR * 1.6, 0.78 - math.sin(a) * rr * 0.9, 0.018, 0.014,
                          S.pick(['#e6cf96', '#d4b070', '#f3ead6', '#c9a05a', '#e9b443']))
        lit = '#ffe6a0'
        with mid.piece(0.7) as d:  # glowing mushrooms as lamps
            for x in (0.1, 0.92):
                d.rect(x - 0.006, 0.66, x + 0.006, 0.78, '#e6e0d4')
                d.pie(x, 0.67, 0.035, 180, 360, lit, lit=True)
        for x in (0.1, 0.92):
            mid.glow_circ(x, 0.65, 0.08)
        near = S.L('near')
        with near.piece(0.6) as d:
            d.ridge(ridge_fn(S.seed, 0.86, 0.02), '#9a7652')
        fg = S.L('fg')
        with fg.piece() as d:  # root ends framing
            d.line([(-0.02, 0.1), (0.08, 0.2), (0.1, 0.35)], '#4a3424', 0.02)
            d.line([(1.02, 0.7), (0.94, 0.8), (0.9, 1.02)], '#4a3424', 0.025)
        return 'inside an anthill: a storage chamber with crumb piles and mushroom lamps'
    hz = 0.34 if v == 0 else 0.5
    sky(S, horizon=hz + 0.2 if v == 0 else hz, clouds=2)
    far = S.L('far')
    with far.piece(0.8) as d:  # giant grass blades against the sky
        for k in range(26):
            x = S.r(-0.02, 1.02)
            h = S.r(0.2, 0.45)
            d.poly([(x - 0.012, hz + 0.05), (x + 0.012, hz + 0.05), (x + S.r(-0.04, 0.04), hz + 0.05 - h)], S.pick(['grass', 'grass2', 'grass3']))
    if v == 0:  # cutaway: surface strip, then soil with tunnels and chambers
        mid = S.L('mid')
        with mid.piece(0.8) as d:
            d.ridge(ridge_fn(S.seed, hz + 0.06, 0.02), soil)
            d.ridge(ridge_fn(S.seed + 1, hz + 0.05, 0.01), 'grass2', bottom=hz + 0.08)
        with mid.piece(0.5) as d:  # pine needle mound on top, cut in half
            d.pie(0.5, hz + 0.08, 0.22, 180, 360, '#a0703f')
            for k in range(60):
                a = rng.random() * math.pi
                rr = rng.random() ** 0.5 * 0.2
                x, y = 0.5 + math.cos(a) * rr / AR, hz + 0.08 - math.sin(a) * rr
                ang = rng.random() * math.pi
                d.line([(x, y), (x + math.cos(ang) * 0.03 / AR, y + math.sin(ang) * 0.03)], S.pick(['#8a5a2a', '#b07a3a', '#6a4a2a']), 0.004)
        with mid.piece(0.6) as d:  # tunnels and chambers
            path = [(0.5, hz + 0.08), (0.45, 0.5), (0.3, 0.56), (0.2, 0.68), (0.32, 0.8), (0.55, 0.78), (0.7, 0.66), (0.82, 0.55), (0.7, 0.48), (0.5, 0.5)]
            d.line(path, tun, 0.035)
            d.line([(0.55, 0.78), (0.6, 0.92)], tun, 0.03)
            d.line([(0.82, 0.55), (0.98, 0.62)], tun, 0.03)
            for x, y, r in ((0.2, 0.68, 0.06), (0.7, 0.66, 0.055), (0.6, 0.92, 0.05), (0.3, 0.56, 0.04)):
                d.ell(x, y, r * 1.5, r, tun)
        with mid.piece(0.6) as d:  # crumbs moving along a tunnel like a conveyor
            for t in np.linspace(0.05, 0.95, 16):
                i = int(t * (len(path) - 1))
                u = t * (len(path) - 1) - i
                (x0, y0), (x1, y1) = path[i], path[i + 1]
                d.ell(x0 + (x1 - x0) * u, y0 + (y1 - y0) * u, 0.008, 0.006, S.pick(['#f3ead6', '#e6cf96', '#e9b443']))
            for x, y in ((0.2, 0.7), (0.7, 0.68)):
                for k in range(6):
                    d.ell(x + S.r(-0.04, 0.04), y + 0.02 + S.r(-0.01, 0.01), 0.01, 0.007, S.pick(['#f3ead6', '#e6cf96']))
        near = S.L('near')
        with near.piece(0.5) as d:  # pebbles and roots in the soil
            for k in range(20):
                d.ell(S.r(0, 1), S.r(hz + 0.12, 1.0), S.r(0.01, 0.025), S.r(0.008, 0.015), S.pick(['#9a958f', '#6a4a33', '#a89a88']))
            for x in (0.05, 0.95):
                d.line([(x, hz + 0.06), (x + 0.02, 0.5), (x - 0.01, 0.75)], '#5a3e2a', 0.008)
        with S.L('sky').piece(0.3) as d:  # soil behind the cutaway
            d.rect(-0.02, hz + 0.06, 1.02, 1.02, soil2)
        return 'anthill cutaway: a needle mound, tunnels, chambers and a crumb line'
    # v1: surface macro — a ramp of needles, moss, mushrooms, a leaf conveyor of crumbs
    mid = S.L('mid')
    with mid.piece(0.8) as d:
        d.ridge(ridge_fn(S.seed, hz + 0.08, 0.03), '#6f8f45')
    with mid.piece(0.9) as d:  # the needle mound on the right
        d.pie(0.78, hz + 0.12, 0.32, 180, 360, '#a0703f')
    with mid.piece(0.5) as d:
        for k in range(120):
            a = rng.random() * math.pi
            rr = rng.random() ** 0.6 * 0.31
            x, y = 0.78 + math.cos(a) * rr / AR, hz + 0.12 - math.sin(a) * rr
            ang = rng.random() * math.pi
            d.line([(x, y), (x + math.cos(ang) * 0.04 / AR, y + math.sin(ang) * 0.04)], S.pick(['#8a5a2a', '#b07a3a', '#6a4a2a', '#c48a4a']), 0.005)
        for x in (0.7, 0.86):
            d.ell(x, hz + 0.1, 0.02, 0.025, '#3a2418')
    near = S.L('near')
    with near.piece(0.6) as d:  # mossy ground
        d.ridge(ridge_fn(S.seed + 2, 0.78, 0.02), '#5f8a3f')
    with near.piece(0.5) as d:
        for k in range(40):
            d.circ(S.r(0, 1), S.r(0.78, 1.0), S.r(0.01, 0.025), S.pick(['#6f9e48', '#7aa852', '#56803a']))
    with near.piece(0.9) as d:  # a leaf laid as a conveyor ramp up to the mound, crumbs on it
        d.poly([(0.08, 0.84), (0.2, 0.76), (0.42, 0.68), (0.6, 0.6), (0.66, 0.63), (0.56, 0.74), (0.36, 0.82), (0.16, 0.88)], '#7cbf4e')
        d.line([(0.1, 0.85), (0.63, 0.62)], '#5a9a3a', 0.005)
        for t in np.linspace(0.15, 0.85, 6):
            bx, by = 0.1 + 0.53 * t, 0.85 - 0.23 * t
            d.line([(bx, by), (bx + 0.03, by - 0.035)], '#5a9a3a', 0.003)
            d.line([(bx, by), (bx + 0.02, by + 0.03)], '#5a9a3a', 0.003)
        for t in np.linspace(0.1, 0.9, 9):
            d.ell(0.12 + 0.5 * t, 0.84 - 0.22 * t - 0.012, 0.014, 0.011, S.pick(['#f3ead6', '#e6cf96', '#e9b443']))
    fg = S.L('fg')
    with fg.piece() as d:  # mushrooms and giant fallen needles in front
        for x, s in ((0.06, 1.0), (0.93, 1.3)):
            d.rect(x - 0.01 * s, 0.88, x + 0.01 * s, 1.02, '#f3ead6')
            d.pie(x, 0.9, 0.07 * s, 180, 360, '#c0443a')
            for u in (-0.02, 0.0, 0.02):
                d.circ(x + u * s, 0.86, 0.006 * s, '#f6f3ea')
        d.line([(0.25, 1.02), (0.45, 0.94)], '#8a5a2a', 0.012)
        d.line([(0.7, 1.02), (0.6, 0.93)], '#b07a3a', 0.012)
    weather_fx(S, ground=0.8)
    return 'anthill from an ant\'s height: a needle mound, moss, mushrooms and a leaf ramp with crumbs'
