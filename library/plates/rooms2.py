"""More everyday interiors (puppet-plates-more): dining room, meeting room, interview room, office kitchen, therapist,
doctor, vet, empty flat, call centre, gym, supermarket, stairwell, bathroom, bank, museum.

Same layer roles as rooms.py: sky = back wall and floor (windows show the time of day outside), far = things on the
wall, mid = furniture against the wall, near = furniture in front (the middle of the floor stays open for puppets),
fg = framing props. No readable text, digits, logos or emblems anywhere."""
import math

import numpy as np

from plates import AR, shade, mixc
from scenes import biome
from rooms import (shell, window_view, lamp_pendant, ceiling_panels, picture, clock, shelf, plant, desk, chair, monitor,
                   sofa, rug, WOOD)

IN6 = [('day', 'clear', 'summer', 'felt'), ('night', 'clear', 'summer', 'felt'), ('golden', 'clear', 'autumn', 'warm'),
       ('day', 'rain', 'autumn', 'felt'), ('dusk', 'clear', 'winter', 'felt'), ('dawn', 'clouds', 'spring', 'pastel')]
IN6B = [('day', 'clear', 'summer', 'felt'), ('night', 'clear', 'summer', 'felt'), ('day', 'clouds', 'spring', 'pastel'),
        ('golden', 'clear', 'autumn', 'warm'), ('dusk', 'clear', 'winter', 'cool'), ('day', 'clear', 'summer', 'vivid')]
IN6C = [('day', 'clear', 'summer', 'felt'), ('night', 'clear', 'summer', 'felt'), ('day', 'clear', 'winter', 'cool'),
        ('dawn', 'clouds', 'spring', 'pastel'), ('dusk', 'clear', 'autumn', 'warm'), ('day', 'rain', 'autumn', 'muted')]

LOOKS = {
    'dining': (3, IN6), 'meeting_room': (3, IN6B), 'hr_room': (3, IN6), 'office_kitchen': (3, IN6B),
    'therapy': (3, IN6), 'clinic': (3, IN6C), 'vet': (3, IN6B), 'apartment_empty': (3, IN6C),
    'call_center': (3, IN6C), 'gym': (3, IN6B), 'supermarket': (3, IN6B), 'stairwell': (3, IN6C),
    'bathroom': (3, IN6), 'bank': (3, IN6C), 'museum': (3, IN6),
}


def lit(S):
    return S.look.lit_share > 0.2


# ---------------------------------------------------------------- small props

def blinds(L, x0, y0, x1, y1, col='#eceae2', open_=0.45):
    """Venetian blinds over a window (on the far layer, in front of the frame)."""
    with L.piece(0.6) as d:
        d.rect(x0 - 0.012, y0 - 0.025, x1 + 0.012, y0 - 0.005, shade(col, 0.9), r=0.004)
        n = int((y1 - y0) / 0.022)
        for k in range(n):
            y = y0 + k * (y1 - y0) / n
            if k / n > 1 - open_:
                break
            d.rect(x0 - 0.006, y, x1 + 0.006, y + (y1 - y0) / n * 0.72, col, r=0.002)
        d.line([(x1 - 0.02, y0), (x1 - 0.02, y0 + (y1 - y0) * 0.8)], shade(col, 0.7), 0.002)


def curtains(L, x0, x1, y0, y1, col, rod='#6a4a2a'):
    with L.piece(0.6) as d:
        d.rect(x0 - 0.03, y0 - 0.01, x1 + 0.03, y0 + 0.005, rod, r=0.003)
        for x, sgn in ((x0 - 0.025, 1), (x1 + 0.025, -1)):
            pts = [(x, y0), (x + sgn * 0.055, y0)]
            for k in range(9):
                u = k / 8
                pts.append((x + sgn * (0.055 - 0.02 * math.sin(u * math.pi)), y0 + (y1 - y0) * u))
            pts.append((x, y1))
            d.poly(pts, col)
    with L.piece(0.4) as d:
        for x, sgn in ((x0 - 0.025, 1), (x1 + 0.025, -1)):
            for k in (1, 2):
                xx = x + sgn * 0.017 * k
                d.line([(xx, y0 + 0.02), (xx, y1 - 0.01)], shade(col, 0.85), 0.003)


def door(L, x, yb, w=0.11, h=0.42, col='#8a5a3a', frame='#f2ede2', padded=False, glass=False):
    with L.piece(0.9) as d:
        d.rect(x - w / 2 - 0.012, yb - h - 0.014, x + w / 2 + 0.012, yb, frame, r=0.003)
        d.rect(x - w / 2, yb - h, x + w / 2, yb, col, r=0.003)
    with L.piece(0.6) as d:
        if padded:  # Soviet leatherette door with button studs
            for i in range(4):
                for j in range(7):
                    d.circ(x - w / 2 + w * (i + 0.5) / 4, yb - h + h * (j + 0.5) / 7, 0.004, shade(col, 1.25))
            for i in range(1, 4):
                d.line([(x - w / 2 + w * i / 4, yb - h + 0.02), (x - w / 2 + w * i / 4, yb - 0.02)], shade(col, 0.85), 0.002)
        elif glass:
            d.rect(x - w / 2 + 0.015, yb - h + 0.02, x + w / 2 - 0.015, yb - h * 0.45, '#cfe6f2')
        else:
            d.rect(x - w / 2 + 0.012, yb - h + 0.02, x + w / 2 - 0.012, yb - h * 0.55, shade(col, 1.08), r=0.003)
            d.rect(x - w / 2 + 0.012, yb - h * 0.5, x + w / 2 - 0.012, yb - 0.02, shade(col, 1.08), r=0.003)
        d.circ(x + w / 2 - 0.016, yb - h * 0.48, 0.007, '#d9b65a')


def radiator(L, x0, x1, y, h=0.09, col='#f2f0ea'):
    with L.piece(0.8) as d:
        n = int((x1 - x0) / 0.012)
        for k in range(n):
            x = x0 + k * (x1 - x0) / n
            d.rect(x, y - h, x + (x1 - x0) / n * 0.8, y, col, r=0.003)
        d.rect(x0 - 0.004, y - h * 0.8, x1, y - h * 0.72, shade(col, 0.92))
        d.line([(x1, y - h * 0.3), (x1 + 0.02, y - h * 0.3), (x1 + 0.02, y + 0.03)], '#c9c4b8', 0.006)


def bulb(L, x, y, cord=0.0, s=1.0, on=None, shade_col=None):
    """A bare bulb (or a simple shade) on a cord, glowing at night."""
    on = lit(L.scene) if on is None else on
    with L.piece(0.5) as d:
        d.line([(x, cord), (x, y - 0.02 * s)], '#3a3a40', 0.002)
        d.rect(x - 0.006 * s, y - 0.025 * s, x + 0.006 * s, y - 0.01 * s, '#6a6a72')
        if shade_col:
            d.pie(x, y - 0.005 * s, 0.035 * s, 180, 360, shade_col)
    with L.piece(0.4) as d:
        d.ell(x, y, 0.012 * s, 0.015 * s, '#fff2c0' if on else '#ecebe2', lit=on)
    if on:
        L.glow_circ(x, y, 0.07 * s)


def chandelier(L, x, y, s=1.0, col='#d9b65a'):
    on = lit(L.scene) or L.look.time in ('night', 'dusk')
    with L.piece(0.6) as d:
        d.line([(x, -0.01), (x, y - 0.03 * s)], '#6a5a3a', 0.003)
        d.ell(x, y - 0.03 * s, 0.012 * s, 0.01 * s, col)
        d.line([(x - 0.07 * s, y), (x - 0.04 * s, y + 0.012 * s), (x, y + 0.015 * s), (x + 0.04 * s, y + 0.012 * s), (x + 0.07 * s, y)], col, 0.004 * s)
        for k in range(5):
            xx = x + (k - 2) * 0.035 * s
            d.line([(x, y - 0.03 * s), (xx, y + 0.01 * s)], col, 0.002)
    with L.piece(0.4) as d:
        for k in range(5):
            xx = x + (k - 2) * 0.035 * s
            yy = y - 0.002 * s + (0.008 if k in (1, 3) else 0.0) * s
            d.rect(xx - 0.003 * s, yy - 0.015 * s, xx + 0.003 * s, yy, '#fbf6e6')
            d.ell(xx, yy - 0.024 * s, 0.006 * s, 0.009 * s, '#ffe08f' if on else '#f4f1e4', lit=on)
            if on:
                L.glow_circ(xx, yy - 0.024 * s, 0.03 * s)
        for k in range(7):
            d.circ(x + (k - 3) * 0.02 * s, y + 0.03 * s + 0.01 * (3 - abs(k - 3)) * s / 3, 0.004 * s, '#e6f2fa')


def wall_tiles(L, x0, y0, x1, y1, col, size=0.04, grout=None, depth=0.4):
    grout = grout or shade(col, 0.85)
    with L.piece(depth) as d:
        d.rect(x0, y0, x1, y1, grout)
        sx = size / AR
        y = y0
        while y < y1 - 0.002:
            x = x0
            while x < x1 - 0.002:
                d.rect(x + 0.0015, y + 0.002, min(x + sx, x1) - 0.0015, min(y + size, y1) - 0.002, col, r=0.002)
                x += sx
            y += size


def frame_art(L, x, y, w, h, rng, frame='#2e2e36', bg='#f6f3ea', kind=None):
    """An abstract framed picture: circles, stripes or blocks, never text."""
    kind = kind if kind is not None else int(rng.integers(3))
    cols = ['#e05a5a', '#f6c453', '#3f7fbf', '#3d8a5a', '#e9a23a', '#8a5a9a', '#f28b6b']
    with L.piece(0.7) as d:
        d.rect(x - w / 2, y - h / 2, x + w / 2, y + h / 2, frame, r=0.002)
        d.rect(x - w / 2 + 0.008, y - h / 2 + 0.014, x + w / 2 - 0.008, y + h / 2 - 0.014, bg)
    with L.piece(0.5) as d:
        if kind == 0:
            for k in range(3):
                d.circ(x - w * 0.2 + k * w * 0.2, y - h * 0.1 + (k % 2) * h * 0.15, h * (0.18 - k * 0.03), cols[int(rng.integers(len(cols)))])
        elif kind == 1:
            for k in range(4):
                xx = x - w / 2 + 0.012 + k * (w - 0.024) / 4
                d.rect(xx, y - h / 2 + 0.02, xx + (w - 0.024) / 4 - 0.004, y + h / 2 - 0.02, cols[(k * 2 + int(rng.integers(3))) % len(cols)])
        else:
            d.rect(x - w * 0.35, y - h * 0.3, x + w * 0.05, y + h * 0.1, cols[int(rng.integers(len(cols)))])
            d.rect(x - w * 0.05, y - h * 0.05, x + w * 0.35, y + h * 0.32, cols[int(rng.integers(len(cols)))])
            d.circ(x + w * 0.2, y - h * 0.2, h * 0.12, cols[int(rng.integers(len(cols)))])


def mug(d, x, y, s, col):
    d.rect(x - 0.008 * s, y - 0.022 * s, x + 0.008 * s, y, col, r=0.003 * s)
    d.ell(x + 0.011 * s, y - 0.012 * s, 0.006 * s, 0.007 * s, col)


def sticky_board(L, x, y, w, h, rng, col='#c9a06a'):
    with L.piece(0.7) as d:
        d.rect(x - w / 2, y - h / 2, x + w / 2, y + h / 2, '#8a6a4a', r=0.004)
        d.rect(x - w / 2 + 0.006, y - h / 2 + 0.01, x + w / 2 - 0.006, y + h / 2 - 0.01, col)
    with L.piece(0.5) as d:
        for _ in range(9):
            xx, yy = x + (rng.random() - 0.5) * (w - 0.04), y + (rng.random() - 0.5) * (h - 0.06)
            d.rect(xx - 0.012, yy - 0.02, xx + 0.012, yy + 0.02, ['#f6e86a', '#f2a6c0', '#9fd8f0', '#b6e07e', '#ffffff'][int(rng.integers(5))])
            d.circ(xx, yy - 0.015, 0.004, '#e05a5a')


def plinth(L, x, yb, w=0.1, h=0.2, col='#f2efe8'):
    with L.piece(1.0) as d:
        d.rect(x - w / 2, yb - h, x + w / 2, yb, col, r=0.002)
        d.rect(x - w / 2 - 0.006, yb - h - 0.012, x + w / 2 + 0.006, yb - h, shade(col, 0.95), r=0.002)
        d.rect(x - w / 2 - 0.004, yb - 0.012, x + w / 2 + 0.004, yb, shade(col, 0.9))


def rope_barrier(L, x0, x1, yb, h=0.12, rope='#c0443a', post='#d9b65a'):
    with L.piece(0.9) as d:
        n = max(1, int((x1 - x0) / 0.18))
        xs = [x0 + (x1 - x0) * k / n for k in range(n + 1)]
        for a, b in zip(xs, xs[1:]):
            pts = [(a + (b - a) * u, yb - h + 0.01 + 0.035 * math.sin(u * math.pi)) for u in np.linspace(0, 1, 14)]
            d.line(pts, rope, 0.007)
        for x in xs:
            d.rect(x - 0.004, yb - h, x + 0.004, yb, post)
            d.circ(x, yb - h, 0.009, post)
            d.ell(x, yb, 0.02, 0.006, post)


def armchair(L, x, y, s=1.0, col='#c9a868', face=1):
    """A soft armchair, three-quarter, facing face (+1 right, -1 left)."""
    k = 1 / AR
    with L.piece(0.9) as d:
        bx = x - face * 0.05 * s * k * AR / AR
        d.rect(x - 0.085 * s * k * AR / 1.6, y - 0.24 * s, x + 0.085 * s * k * AR / 1.6, y - 0.08 * s, col, r=0.035 * s)
    with L.piece(0.9) as d:
        w = 0.085 * s * k * AR / 1.6
        d.rect(x - w + 0.008, y - 0.12 * s, x + w - 0.008, y - 0.04 * s, shade(col, 1.1), r=0.02 * s)
        for sx in (-1, 1):
            d.rect(x + sx * w - 0.022 * s, y - 0.15 * s, x + sx * w + 0.012 * s * (1 if sx > 0 else -1) + (0 if sx > 0 else 0.022 * s), y - 0.03 * s,
                   shade(col, 0.92), r=0.02 * s)
        for sx in (-1, 1):
            d.rect(x + sx * (w - 0.015) - 0.005, y - 0.035 * s, x + sx * (w - 0.015) + 0.005, y, '#5a3a2a')


def ficus(L, x, y, s=1.0, pot='#e6e0d4'):
    with L.piece(0.8) as d:
        d.line([(x, y - 0.06 * s), (x - 0.005 * s, y - 0.3 * s)], '#7a5a3a', 0.007 * s)
        d.line([(x, y - 0.18 * s), (x + 0.03 * s, y - 0.28 * s)], '#7a5a3a', 0.005 * s)
    with L.piece(0.9) as d:
        for cx, cy, r in ((-0.03, -0.32, 0.07), (0.035, -0.33, 0.065), (0.0, -0.4, 0.07), (-0.02, -0.25, 0.05), (0.03, -0.24, 0.05)):
            d.circ(x + cx * s, y + cy * s, r * s, '#4f9e48')
        for cx, cy, r in ((-0.015, -0.36, 0.035), (0.03, -0.29, 0.03), (0.01, -0.42, 0.03)):
            d.circ(x + cx * s, y + cy * s, r * s, '#68b456')
    with L.piece(0.9) as d:
        d.poly([(x - 0.032 * s, y - 0.08 * s), (x + 0.032 * s, y - 0.08 * s), (x + 0.025 * s, y), (x - 0.025 * s, y)], pot)


def water_cooler(L, x, y, s=1.0):
    with L.piece(0.9) as d:
        d.rect(x - 0.025 * s, y - 0.18 * s, x + 0.025 * s, y, '#e6eaee', r=0.006)
        d.rect(x - 0.01 * s, y - 0.13 * s, x + 0.01 * s, y - 0.11 * s, '#5a6a7a')
    with L.piece(0.8) as d:
        d.rect(x - 0.022 * s, y - 0.28 * s, x + 0.022 * s, y - 0.18 * s, (150, 200, 235, 200), r=0.012 * s)
        d.rect(x - 0.008 * s, y - 0.19 * s, x - 0.003 * s, y - 0.17 * s, '#3f7fbf')
        d.rect(x + 0.003 * s, y - 0.19 * s, x + 0.008 * s, y - 0.17 * s, '#e05a5a')


def tv(L, x, y, w=0.16, h=0.1, on=True, stand=True, col='#4a8fc9'):
    with L.piece(0.9) as d:
        d.rect(x - w / 2, y - h, x + w / 2, y, '#1e1e26', r=0.005)
        if stand:
            d.rect(x - 0.006, y, x + 0.006, y + 0.02, '#2e2e36')
            d.rect(x - 0.03, y + 0.018, x + 0.03, y + 0.024, '#2e2e36', r=0.002)
    with L.piece(0.4) as d:
        if on:
            d.rect(x - w / 2 + 0.006, y - h + 0.01, x + w / 2 - 0.006, y - 0.01, col, lit=True)
            d.circ(x - w * 0.15, y - h * 0.45, h * 0.18, shade(col, 1.35), lit=True)
            d.rect(x, y - h * 0.62, x + w * 0.3, y - h * 0.3, shade(col, 0.7), lit=True)
        else:
            d.rect(x - w / 2 + 0.006, y - h + 0.01, x + w / 2 - 0.006, y - 0.01, '#2e3440')
    if on:
        L.glow_rect(x - w / 2, y - h, x + w / 2, y)


def sunbeam(S, L, x0, x1, y0, y1, fy):
    """A soft patch of sunlight on the floor below a window (day and golden hour only)."""
    if S.look.time not in ('day', 'golden') or S.look.weather in ('rain', 'fog'):
        return
    a = 60 if S.look.weather == 'clear' else 30
    c = (255, 240, 200, a) if S.look.time == 'day' else (255, 210, 140, a + 10)
    with L.piece(0.2) as d:
        d.poly([(x0, fy + 0.01), (x1, fy + 0.01), (x1 + 0.16, 1.02), (x0 + 0.06, 1.02)], c)


# ---------------------------------------------------------------- dining room

@biome('dining', interior=True)
def dining(S):
    v = S.variant % 3
    rng = S.rng
    wall = ['#efdcbc', '#d6e2d2', '#3f5a4f'][v]
    shell(S, wall=wall, floor=['#b98a5e', '#a9784e', '#8a5a3a'][v], fy=0.72)
    sky_ = S.L('sky')
    far = S.L('far')
    if v != 2:  # wallpaper stripes
        with sky_.piece(0.2) as d:
            for k in range(40):
                x = k * 0.026
                d.rect(x, 0.0, x + 0.009, 0.7, shade(wall, 0.95))
    wx = 0.66 if v == 0 else 0.08
    window_view(S, sky_, wx, 0.14, wx + 0.24, 0.5, view='trees' if v != 1 else 'city', bars=2)
    curtains(far, wx, wx + 0.24, 0.1, 0.62, ['#c0443a', '#3f6fa8', '#d9b65a'][v])
    if v == 0:
        picture(far, 0.2, 0.3, 0.16, 0.13, rng)
    elif v == 1:  # geometric carpet on the wall
        with far.piece(0.6) as d:
            d.rect(0.5, 0.12, 0.86, 0.48, '#a8323a', r=0.004)
            d.rect(0.515, 0.14, 0.845, 0.46, '#d9a23a')
            d.rect(0.53, 0.165, 0.83, 0.435, '#a8323a')
        with far.piece(0.4) as d:
            for i in range(5):
                for j in range(3):
                    cx, cy = 0.56 + i * 0.06, 0.21 + j * 0.08
                    d.poly([(cx, cy - 0.03), (cx + 0.018, cy), (cx, cy + 0.03), (cx - 0.018, cy)], '#f3ead6' if (i + j) % 2 else '#2f4f7a')
    else:
        frame_art(far, 0.45, 0.28, 0.14, 0.18, rng, frame='#d9b65a')
        frame_art(far, 0.62, 0.3, 0.1, 0.13, rng, frame='#d9b65a')
    mid = S.L('mid')
    if v == 0:  # TV on a low stand behind, left
        with mid.piece(0.9) as d:
            d.rect(0.02, 0.62, 0.22, 0.73, '#6a4630', r=0.004)
            d.rect(0.03, 0.635, 0.12, 0.72, shade('#6a4630', 1.15), r=0.003)
            d.rect(0.125, 0.635, 0.21, 0.72, shade('#6a4630', 1.15), r=0.003)
        tv(mid, 0.12, 0.58, 0.17, 0.11, on=True)
    elif v == 1:  # sideboard with dishes, TV on top
        with mid.piece(0.9) as d:
            d.rect(0.88, 0.4, 1.02, 0.73, '#8a5a3a', r=0.004)
            d.rect(0.89, 0.42, 1.01, 0.56, '#cfe6f2')
            for k in range(3):
                d.circ(0.91 + k * 0.035, 0.49, 0.018, '#f6f3ea')
        tv(mid, 0.2, 0.6, 0.17, 0.11, on=True, stand=True)
        with mid.piece(0.9) as d:
            d.rect(0.1, 0.62, 0.3, 0.73, '#8a5a3a', r=0.004)
    else:  # TV on the wall, sideboard under it
        tv(mid, 0.82, 0.46, 0.2, 0.12, on=True, stand=False, col='#c9734a')
        with mid.piece(0.9) as d:
            d.rect(0.7, 0.58, 0.95, 0.73, '#2e2420', r=0.004)
            for k in range(3):
                d.rect(0.71 + k * 0.08, 0.6, 0.77 + k * 0.08, 0.71, '#4a3a30', r=0.003)
        with mid.piece(0.6) as d:
            d.rect(0.74, 0.53, 0.76, 0.58, '#f6f3ea', r=0.004)
            d.ell(0.75, 0.53, 0.01, 0.016, '#f6c453', lit=True)
    # table: chairs behind it first (their backs show above the top), then the table
    tx0, tx1, ty = 0.27, 0.73, 0.66
    cloth = ['#f6f3ea', '#e05a5a', '#f2ead6'][v]
    for x in (0.37, 0.63):
        with mid.piece(1.0) as d:
            d.rect(x - 0.035, ty - 0.17, x + 0.035, ty - 0.02, ['#8a5a3a', '#b98a5e', '#6a3a2a'][v], r=0.01)
            d.rect(x - 0.026, ty - 0.16, x + 0.026, ty - 0.1, shade(['#8a5a3a', '#b98a5e', '#6a3a2a'][v], 1.15), r=0.008)
    near = S.L('near')
    with near.piece(1.0) as d:
        d.rect(tx0 - 0.02, ty, tx1 + 0.02, ty + 0.025, WOOD, r=0.004)
        d.poly([(tx0 - 0.02, ty), (tx1 + 0.02, ty), (tx1 + 0.03, ty + 0.1), (tx0 - 0.03, ty + 0.1)], cloth)
        for x in (tx0 + 0.01, tx1 - 0.01):
            d.rect(x - 0.007, ty + 0.1, x + 0.007, ty + 0.24, shade(WOOD, 0.8))
    if v == 1:  # checks on the cloth
        with near.piece(0.3) as d:
            for k in range(12):
                x = tx0 - 0.02 + k * 0.036
                d.rect(x, ty, x + 0.018, ty + 0.1, '#f6f3ea')
    with near.piece(0.8) as d:  # food
        for x in (0.36, 0.46, 0.54, 0.64):
            d.ell(x, ty - 0.004, 0.032, 0.009, '#ffffff')
            d.ell(x, ty - 0.006, 0.02, 0.005, S.pick(['#e9a23a', '#7cc45e', '#c0443a']))
        d.ell(0.5, ty - 0.02, 0.05, 0.022, '#c9734a')  # a big dish
        d.ell(0.5, ty - 0.03, 0.035, 0.018, '#e9a23a')
        d.ell(0.41, ty - 0.02, 0.025, 0.014, '#7cc45e')  # salad bowl
        d.rect(0.385, ty - 0.02, 0.435, ty - 0.004, '#f6f3ea', r=0.006)
        d.ell(0.59, ty - 0.015, 0.03, 0.01, '#d9a05a')  # bread
        d.rect(0.665, ty - 0.05, 0.68, ty - 0.004, '#c0443a', r=0.004)  # a bottle of juice
        d.rect(0.315, ty - 0.035, 0.335, ty - 0.004, '#cfe6f2', r=0.003)
    chair(near, 0.22, 0.92, 1.9, col=['#8a5a3a', '#b98a5e', '#6a3a2a'][v], face=-1)
    chair(near, 0.78, 0.92, 1.9, col=['#8a5a3a', '#b98a5e', '#6a3a2a'][v], face=1)
    rug(S.L('mid'), 0.5, 0.86, 0.36, 0.05, col=['#a8323a', '#3f6fa8', '#d9a23a'][v], col2=['#e9a23a', '#cfe6f2', '#8a3a2a'][v])
    fg = S.L('fg')
    chandelier(fg, 0.5, 0.2, 2.2)
    if v == 2:
        ficus(fg, 0.95, 1.02, 1.5)
    else:
        plant(fg, 0.04 if v == 0 else 0.96, 1.0, 2.2)
    return {0: 'family dining room: a laid table, a chandelier, a TV in the corner',
            1: 'dining room with a carpet on the wall and a checked tablecloth',
            2: 'dark green evening dining room with a wall TV'}[v]


# ---------------------------------------------------------------- meeting room

def whiteboard(L, x, y, w, h, rng):
    with L.piece(0.7) as d:
        d.rect(x - w / 2, y - h / 2, x + w / 2, y + h / 2, '#b9c0c8', r=0.004)
        d.rect(x - w / 2 + 0.006, y - h / 2 + 0.01, x + w / 2 - 0.006, y + h / 2 - 0.01, '#fbfbf8')
        d.rect(x - w / 2 + 0.02, y + h / 2, x + w / 2 - 0.02, y + h / 2 + 0.012, '#b9c0c8')
        for k, c in enumerate(('#e05a5a', '#3f7fbf', '#3d8a5a')):
            d.rect(x - w / 2 + 0.04 + k * 0.03, y + h / 2 - 0.004, x - w / 2 + 0.062 + k * 0.03, y + h / 2 + 0.004, c, r=0.002)
    with L.piece(0.3) as d:  # doodles: boxes, arrows, a circle, a squiggle (no words)
        bx = x - w / 2 + 0.03
        d.line([(bx, y - h * 0.25), (bx + 0.05, y - h * 0.25), (bx + 0.05, y - h * 0.05), (bx, y - h * 0.05), (bx, y - h * 0.25)], '#3f7fbf', 0.003)
        d.line([(bx + 0.06, y - h * 0.15), (bx + 0.1, y - h * 0.15)], '#3f7fbf', 0.003)
        d.line([(bx + 0.09, y - h * 0.19), (bx + 0.1, y - h * 0.15), (bx + 0.09, y - h * 0.11)], '#3f7fbf', 0.003)
        cx = bx + 0.14
        pts = [(cx + 0.025 * math.cos(a), y - h * 0.15 + 0.04 * math.sin(a)) for a in np.linspace(0, 6.3, 30)]
        d.line(pts, '#e05a5a', 0.003)
        pts = [(bx + u * (w - 0.08), y + h * 0.22 - 0.03 * math.sin(u * 12) * (1 - u) - u * h * 0.2) for u in np.linspace(0, 1, 40)]
        d.line(pts, '#3d8a5a', 0.003)


def screen_chart(L, x, y, w, h, col='#2f6fb0', on=True):
    """A wall screen with an abstract bar chart (no numbers)."""
    with L.piece(0.7) as d:
        d.rect(x - w / 2, y - h / 2, x + w / 2, y + h / 2, '#1e1e26', r=0.006)
    with L.piece(0.4) as d:
        if not on:
            d.rect(x - w / 2 + 0.008, y - h / 2 + 0.012, x + w / 2 - 0.008, y + h / 2 - 0.012, '#2e3440')
            return
        d.rect(x - w / 2 + 0.008, y - h / 2 + 0.012, x + w / 2 - 0.008, y + h / 2 - 0.012, '#f3f6fa', lit=True)
        n = 6
        for k in range(n):
            bh = h * (0.15 + 0.1 * k + 0.06 * ((k * 7) % 3))
            xx = x - w / 2 + 0.03 + k * (w - 0.06) / n
            d.rect(xx, y + h / 2 - 0.03 - bh * 0.8, xx + (w - 0.06) / n * 0.6, y + h / 2 - 0.03, col if k < n - 1 else '#e9a23a', lit=True)
        d.rect(x - w / 2 + 0.025, y + h / 2 - 0.03, x + w / 2 - 0.025, y + h / 2 - 0.027, '#8a8f99', lit=True)
    L.glow_rect(x - w / 2, y - h / 2, x + w / 2, y + h / 2)


@biome('meeting_room', interior=True)
def meeting_room(S):
    v = S.variant % 3
    rng = S.rng
    wall = ['#e8ecef', '#efe9df', '#5a4436'][v]
    shell(S, wall=wall, floor=['#7d8590', '#9a8f84', '#3e3530'][v], fy=0.7, kind='carpet', ceiling=0.05)
    sky_ = S.L('sky')
    far = S.L('far')
    mid = S.L('mid')
    if v == 0:  # glass wall to the open office behind
        with sky_.piece(0.4) as d:
            d.rect(-0.02, 0.05, 1.02, 0.7, '#dde3e8')
            for k in range(6):  # desks and monitors out there
                x = 0.02 + k * 0.17
                d.rect(x, 0.5, x + 0.13, 0.52, '#c9ced4')
                d.rect(x + 0.03, 0.44, x + 0.08, 0.49, '#4a5058', r=0.003)
                d.rect(x + 0.01, 0.52, x + 0.015, 0.6, '#b0b6be')
                d.rect(x + 0.115, 0.52, x + 0.12, 0.6, '#b0b6be')
        window_view(S, sky_, 0.7, 0.1, 0.98, 0.35, view='city', frame='#c9ced4', bars=3, depth=0.6)
        with far.piece(0.3) as d:  # glass, mullions, frosted band
            d.rect(-0.02, 0.05, 1.02, 0.7, (220, 235, 245, 70))
            d.rect(-0.02, 0.36, 1.02, 0.42, (245, 248, 250, 170))
        with far.piece(0.7) as d:
            for k in range(5):
                x = k * 0.25
                d.rect(x - 0.004, 0.05, x + 0.004, 0.7, '#9aa4ae')
        screen_chart(mid, 0.5, 0.36, 0.3, 0.2, on=True)
    elif v == 1:  # window wall, whiteboard
        for k in range(2):
            x = 0.56 + k * 0.21
            window_view(S, sky_, x, 0.12, x + 0.18, 0.52, view='city', frame='#e6e2da', bars=2)
            blinds(far, x, 0.12, x + 0.18, 0.52, open_=0.3 + 0.2 * k)
        whiteboard(far, 0.25, 0.32, 0.32, 0.26, rng)
        ceiling_panels(far, 0.05, 3)
    else:  # dark wood boardroom
        with sky_.piece(0.3) as d:
            for k in range(12):
                x = k * 0.09
                d.rect(x, 0.05, x + 0.088, 0.68, shade(wall, 1.06 if k % 2 else 0.97))
        screen_chart(mid, 0.5, 0.34, 0.36, 0.24, col='#3d8a5a', on=True)
        frame_art(far, 0.15, 0.3, 0.13, 0.17, rng, frame='#d9b65a')
        frame_art(far, 0.85, 0.3, 0.13, 0.17, rng, frame='#d9b65a')
        for x in (0.12, 0.88):
            with far.piece(0.5) as d:
                d.pie(x, 0.06, 0.04, 0, 180, '#d9b65a')
            if lit(S) or True:
                far.glow_circ(x, 0.1, 0.06)
    # the long table seen at an angle, with office chairs along it
    tcol = ['#f2f0ea', '#b98a5e', '#2e2420'][v]
    ccol = ['#2e2e36', '#3f6fa8', '#6a3a2a'][v]
    for k in range(4):  # far side chairs: backs above the table
        x = 0.32 + k * 0.12
        with mid.piece(1.0) as d:
            d.rect(x - 0.03, 0.5, x + 0.03, 0.63, ccol, r=0.015)
    with mid.piece(1.0) as d:
        d.poly([(0.24, 0.6), (0.76, 0.6), (0.84, 0.68), (0.16, 0.68)], tcol)
        d.rect(0.16, 0.68, 0.84, 0.695, shade(tcol, 0.8))
        d.rect(0.3, 0.695, 0.32, 0.8, shade(tcol, 0.7))
        d.rect(0.68, 0.695, 0.7, 0.8, shade(tcol, 0.7))
    with mid.piece(0.6) as d:  # laptops, papers, water
        for k, x in enumerate((0.3, 0.42, 0.56, 0.68)):
            if k % 2 == 0:
                d.poly([(x - 0.03, 0.635), (x + 0.03, 0.635), (x + 0.036, 0.645), (x - 0.036, 0.645)], '#9aa4ae')
                d.rect(x - 0.028, 0.595, x + 0.028, 0.635, '#4a5058', r=0.003)
            else:
                d.rect(x - 0.02, 0.63, x + 0.02, 0.645, '#fbfbf8')
                d.rect(x + 0.025, 0.61, x + 0.035, 0.64, (180, 215, 240, 210), r=0.002)
        d.rect(0.495, 0.6, 0.51, 0.64, (170, 205, 235, 220), r=0.004)
    near = S.L('near')
    chair(near, 0.12, 0.95, 1.8, col=ccol, face=1, office=True)
    chair(near, 0.88, 0.95, 1.8, col=ccol, face=-1, office=True)
    fg = S.L('fg')
    if v == 0:
        ficus(fg, 0.04, 1.02, 1.7)
        with fg.piece(0.3) as d:  # glass edge of the door with a frosted stripe
            d.rect(0.9, -0.02, 1.02, 1.02, (215, 230, 240, 60))
            d.rect(0.9, 0.45, 1.02, 0.5, (245, 248, 250, 150))
            d.rect(0.9, -0.02, 0.906, 1.02, '#9aa4ae')
    elif v == 1:
        water_cooler(fg, 0.95, 1.0, 2.0)
    else:
        plant(fg, 0.96, 1.0, 2.4, pot='#2e2e36')
    return {0: 'meeting room with glass walls, a long table and a wall screen',
            1: 'bright meeting room with a whiteboard of doodles and blinds',
            2: 'dark wood boardroom with a big screen'}[v]


# ---------------------------------------------------------------- interview room

@biome('hr_room', interior=True)
def hr_room(S):
    v = S.variant % 3
    rng = S.rng
    wall = ['#eef0ec', '#e9e4f0', '#f0e6d6'][v]
    shell(S, wall=wall, floor=['#a8a39a', '#8f949c', '#b98a5e'][v], fy=0.72, kind='tiles' if v < 2 else 'planks', ceiling=0.05)
    sky_ = S.L('sky')
    far = S.L('far')
    wx = [0.6, 0.12, 0.62][v]
    window_view(S, sky_, wx, 0.12, wx + 0.28, 0.52, view='city' if v != 2 else 'trees', frame='#e6e6e2', bars=2)
    blinds(far, wx, 0.12, wx + 0.28, 0.52, open_=[0.45, 0.6, 0.25][v])
    ceiling_panels(far, 0.05, 2)
    ox = 0.25 if v != 1 else 0.68
    if v == 0:
        frame_art(far, 0.3, 0.27, 0.15, 0.12, rng, kind=1)
        clock(far, 0.47, 0.2)
        with far.piece(0.9) as d:  # coat stand with a coat and an umbrella
            d.line([(0.08, 0.73), (0.08, 0.3)], '#6a4a2a', 0.006)
            d.line([(0.05, 0.73), (0.08, 0.68), (0.11, 0.73)], '#6a4a2a', 0.005)
            d.line([(0.06, 0.32), (0.1, 0.34)], '#6a4a2a', 0.004)
            d.poly([(0.07, 0.32), (0.095, 0.33), (0.105, 0.55), (0.06, 0.55)], '#8a5a3a')
            d.line([(0.115, 0.36), (0.12, 0.6)], '#2e2e36', 0.004)
            d.poly([(0.11, 0.42), (0.13, 0.42), (0.125, 0.6), (0.115, 0.6)], '#3f6fa8')
    elif v == 1:
        sticky_board(far, 0.6, 0.3, 0.2, 0.2, rng)
        clock(far, 0.85, 0.2)
    else:
        shelf(far, 0.1, 0.35, 0.28, rng)
        shelf(far, 0.1, 0.35, 0.42, rng)
    mid = S.L('mid')
    # a filing cabinet and a plant against the wall
    with mid.piece(0.9) as d:
        cx = 0.92 if v != 1 else 0.06
        d.rect(cx - 0.05, 0.48, cx + 0.05, 0.73, '#c9ced4', r=0.004)
        for k in range(3):
            d.rect(cx - 0.044, 0.49 + k * 0.08, cx + 0.044, 0.56 + k * 0.08, '#dde2e6', r=0.003)
            d.rect(cx - 0.012, 0.515 + k * 0.08, cx + 0.012, 0.522 + k * 0.08, '#7a7a86')
    with mid.piece(0.6) as d:  # binders on the cabinet
        cx = 0.92 if v != 1 else 0.06
        for k, c in enumerate(('#3f7fbf', '#e05a5a', '#3d8a5a', '#e9a23a')):
            d.rect(cx - 0.04 + k * 0.02, 0.4, cx - 0.024 + k * 0.02, 0.48, c, r=0.002)
    # the desk: interviewer behind it, candidate's chair in front
    dx0, dx1 = (0.3, 0.62) if v != 1 else (0.38, 0.7)
    chair(mid, (dx0 + dx1) / 2 + 0.06, 0.74, 1.6, col='#2e2e36', face=-1, office=True)
    near = S.L('near')
    with near.piece(1.0) as d:
        d.rect(dx0, 0.62, dx1, 0.645, ['#f2f0ea', '#b98a5e', '#8a5a3a'][v], r=0.004)
        d.rect(dx0 + 0.01, 0.645, dx1 - 0.01, 0.8, shade(['#e0ddd4', '#a9784e', '#7a4a2a'][v], 1.0), r=0.004)
    monitor(near, dx1 - 0.06, 0.62, 1.4, on=True)
    with near.piece(0.6) as d:
        d.rect(dx0 + 0.03, 0.608, dx0 + 0.09, 0.62, '#fbfbf8')
        d.rect(dx0 + 0.035, 0.598, dx0 + 0.085, 0.608, '#f3efe4')
        mug(d, dx0 + 0.12, 0.62, 1.3, '#e05a5a')
        d.line([(dx0 + 0.1, 0.612), (dx0 + 0.16, 0.6)], '#2f6fb0', 0.003)
    chair(near, dx0 - 0.08 if v != 1 else dx1 + 0.1, 0.95, 1.9, col=['#3f8f8a', '#c0443a', '#3f6fa8'][v], face=1 if v != 1 else -1)
    fg = S.L('fg')
    if v == 1:
        ficus(fg, 0.05, 1.02, 1.6)
    else:
        plant(fg, 0.95, 1.0, 2.4, pot=['#e6e0d4', '#c5583e', '#3f6fa8'][v])
    return {0: 'interview room: a desk with a monitor, two chairs, blinds', 1: 'HR office with a sticky-note board',
            2: 'warm interview room with bookshelves'}[v]


# ---------------------------------------------------------------- office kitchen

def coffee_machine(d, x, y, s=1.0, col='#2e2e36'):
    k = s
    d.rect(x - 0.035 * k, y - 0.12 * k, x + 0.035 * k, y, col, r=0.006)
    d.rect(x - 0.025 * k, y - 0.06 * k, x + 0.025 * k, y - 0.005 * k, shade(col, 0.6), r=0.004)
    d.rect(x - 0.008 * k, y - 0.065 * k, x + 0.008 * k, y - 0.05 * k, '#9aa4ae')
    d.rect(x - 0.022 * k, y - 0.105 * k, x + 0.022 * k, y - 0.08 * k, '#7fb6e8', lit=True)
    mug(d, x - 0.002 * k, y - 0.006 * k, 0.8 * k, '#f6f3ea')


@biome('office_kitchen', interior=True)
def office_kitchen(S):
    v = S.variant % 3
    rng = S.rng
    wall = ['#e8ece6', '#f2e8d8', '#dfe6ee'][v]
    accent = ['#3d8a5a', '#e9a23a', '#3f6fa8'][v]
    shell(S, wall=wall, floor='#b0aaa0', fy=0.74, kind='tiles', ceiling=0.05)
    sky_ = S.L('sky')
    far = S.L('far')
    wx, ww = [(0.03, 0.14), (0.68, 0.13), (0.4, 0.22)][v]
    window_view(S, sky_, wx, 0.12, wx + ww, 0.44, view='city', frame='#e6e6e2', bars=2)
    ceiling_panels(far, 0.05, 3)
    # splashback tiles and wall cabinets around the window
    cx0, cx1 = [(0.32, 0.98), (0.02, 0.66), (0.02, 0.36)][v]
    wall_tiles(far, cx0, 0.42, cx1, 0.58, '#f6f6f2', 0.04)
    with far.piece(0.8) as d:
        x = cx0
        while x < cx1 - 0.05:
            d.rect(x + 0.004, 0.12, x + 0.104, 0.34, accent, r=0.006)
            d.rect(x + 0.088, 0.3, x + 0.094, 0.32, '#f6f3ea')
            x += 0.108
    if v == 2:
        sticky_board(far, 0.75, 0.26, 0.14, 0.16, rng, col='#c9a06a')
    mid = S.L('mid')
    # counter
    with mid.piece(1.0) as d:
        d.rect(cx0 - 0.01, 0.58, cx1 + 0.01, 0.605, '#d0ccc2', r=0.004)
        x = cx0
        while x < cx1 - 0.05:
            d.rect(x + 0.004, 0.605, x + 0.104, 0.75, shade(accent, 1.25), r=0.006)
            d.rect(x + 0.04, 0.62, x + 0.068, 0.628, '#8a8f99')
            x += 0.108
    sx = cx0 + (cx1 - cx0) * 0.55
    with mid.piece(0.7) as d:  # sink with a pile of mugs, tap
        d.rect(sx - 0.06, 0.578, sx + 0.06, 0.59, '#9aa4ae', r=0.003)
        d.line([(sx + 0.03, 0.58), (sx + 0.03, 0.53), (sx, 0.53), (sx, 0.545)], '#b9c0c8', 0.006)
    with mid.piece(0.8) as d:
        cols = ['#e05a5a', '#f6f3ea', '#3f7fbf', '#f6c453', '#3d8a5a', '#8a5a9a', '#f28b6b']
        for row, n in ((0, 5), (1, 4), (2, 3), (3, 1)):
            for k in range(n):
                mug(d, sx - 0.045 + 0.022 * row / 2 + k * 0.022, 0.58 - row * 0.02, 0.95, cols[(row * 3 + k) % len(cols)])
    with mid.piece(0.9) as d:  # coffee machine, kettle, microwave
        coffee_machine(d, cx0 + 0.07, 0.58, 1.0)
        mx = cx1 - 0.1
        d.rect(mx - 0.07, 0.49, mx + 0.07, 0.58, '#e6eaee', r=0.006)
        d.rect(mx - 0.062, 0.5, mx + 0.03, 0.57, '#2e3440', r=0.004)
        d.rect(mx + 0.038, 0.505, mx + 0.062, 0.52, '#3a3a40')
        for k in range(3):
            d.circ(mx + 0.05, 0.535 + k * 0.012, 0.004, '#9aa4ae')
    with mid.piece(0.9) as d:  # fridge
        fx = [0.25, 0.9, 0.9][v]
        d.rect(fx - 0.06, 0.22, fx + 0.06, 0.75, '#f2f4f6', r=0.01)
        d.rect(fx - 0.06, 0.4, fx + 0.06, 0.405, '#c9cfd6')
        d.rect(fx + 0.04, 0.26, fx + 0.046, 0.36, '#9aa4ae')
        d.rect(fx + 0.04, 0.43, fx + 0.046, 0.55, '#9aa4ae')
    with mid.piece(0.5) as d:  # magnets and a child's drawing on the fridge
        fx = [0.25, 0.9, 0.9][v]
        d.rect(fx - 0.04, 0.44, fx + 0.01, 0.52, '#fbfbf8')
        d.circ(fx - 0.015, 0.47, 0.012, '#f6c453')
        d.rect(fx - 0.035, 0.49, fx + 0.005, 0.505, '#7cc45e')
        for k, c in enumerate(('#e05a5a', '#3f7fbf', '#f6c453')):
            d.circ(fx - 0.03 + k * 0.025, 0.3 + (k % 2) * 0.03, 0.007, c)
    near = S.L('near')
    # a small round high table with two stools, at the side
    tx = 0.82 if v == 0 else 0.16 if v == 1 else 0.5
    if v == 2:
        tx = 0.62
    with near.piece(1.0) as d:
        d.ell(tx, 0.7, 0.08, 0.018, '#f2f0ea')
        d.rect(tx - 0.006, 0.7, tx + 0.006, 0.93, '#7a7a86')
        d.ell(tx, 0.935, 0.04, 0.01, '#7a7a86')
    with near.piece(0.7) as d:
        mug(d, tx - 0.02, 0.695, 1.2, '#3f7fbf')
        d.ell(tx + 0.03, 0.69, 0.025, 0.008, '#fbfbf8')
        d.circ(tx + 0.025, 0.682, 0.008, '#d9a05a')
    for sx_ in (tx - 0.11, tx + 0.11):
        with near.piece(1.0) as d:
            d.ell(sx_, 0.79, 0.035, 0.01, accent)
            d.line([(sx_ - 0.02, 0.97), (sx_, 0.79), (sx_ + 0.02, 0.97)], '#7a7a86', 0.004)
            d.line([(sx_ - 0.014, 0.9), (sx_ + 0.014, 0.9)], '#7a7a86', 0.003)
    fg = S.L('fg')
    water_cooler(fg, 0.05, 1.0, 2.2)
    return {0: 'office kitchen with a coffee machine, a sink full of mugs and a fridge',
            1: 'warm office kitchen with a high table and stools', 2: 'blue office kitchenette with a fridge'}[v]


# ---------------------------------------------------------------- therapist

def couch_chaise(L, x, y, w, col, s=1.0, head=-1):
    """A therapy couch (chaise longue) with a raised head end."""
    with L.piece(0.9) as d:
        hx_ = x + head * w / 2
        d.rect(x - w / 2, y - 0.1 * s, x + w / 2, y - 0.04 * s, col, r=0.02 * s)
        d.poly([(hx_, y - 0.06 * s), (hx_ - head * 0.015, y - 0.22 * s), (hx_ - head * 0.06, y - 0.2 * s), (hx_ - head * 0.1, y - 0.08 * s)], shade(col, 0.92))
    with L.piece(0.9) as d:
        d.ell(hx_ - head * 0.06, y - 0.12 * s, 0.035 * s, 0.022 * s, shade(col, 1.2))
        for xx in (x - w / 2 + 0.02, x + w / 2 - 0.02):
            d.rect(xx - 0.005, y - 0.045 * s, xx + 0.005, y, '#5a3a2a')


def tissue_box(d, x, y, s=1.0):
    d.rect(x - 0.022 * s, y - 0.025 * s, x + 0.022 * s, y, '#9fc8e8', r=0.004)
    d.poly([(x - 0.008 * s, y - 0.025 * s), (x + 0.004 * s, y - 0.05 * s), (x + 0.01 * s, y - 0.03 * s), (x + 0.008 * s, y - 0.025 * s)], '#ffffff')


def floor_lamp(L, x, y, s=1.0, col='#f6e0a0'):
    on = lit(L.scene)
    with L.piece(0.8) as d:
        d.line([(x, y), (x, y - 0.32 * s)], '#4a4a54', 0.006)
        d.ell(x, y, 0.025 * s, 0.006, '#4a4a54')
        d.poly([(x - 0.03 * s, y - 0.31 * s), (x + 0.03 * s, y - 0.31 * s), (x + 0.02 * s, y - 0.37 * s), (x - 0.02 * s, y - 0.37 * s)], col, lit=on)
    if on:
        L.glow_circ(x, y - 0.33 * s, 0.06 * s)


@biome('therapy', interior=True)
def therapy(S):
    v = S.variant % 3
    rng = S.rng
    wall = ['#e6dcc8', '#d8e2dc', '#e8d6cc'][v]
    shell(S, wall=wall, floor=['#a9784e', '#8a6a4e', '#b98a5e'][v], fy=0.72)
    sky_ = S.L('sky')
    far = S.L('far')
    wx = [0.64, 0.08, 0.4][v]
    window_view(S, sky_, wx, 0.14, wx + 0.22, 0.5, view='trees', bars=2)
    curtains(far, wx, wx + 0.22, 0.1, 0.62, ['#8a9a6a', '#c9a868', '#6f8fa8'][v])
    # bookshelf
    bx = [0.06, 0.78, 0.06][v]
    with far.piece(0.9) as d:
        d.rect(bx, 0.16, bx + 0.16, 0.72, '#7a4a2a', r=0.004)
        d.rect(bx + 0.01, 0.18, bx + 0.15, 0.7, '#5a3420')
    for k in range(4):
        shelf(far, bx + 0.01, bx + 0.15, 0.3 + k * 0.13, rng)
    with far.piece(0.6) as d:  # diplomas: blank framed sheets
        for k in range(2):
            x = [0.36, 0.38, 0.72][v] + k * 0.08
            d.rect(x - 0.03, 0.22, x + 0.03, 0.3, '#3a2a20', r=0.002)
            d.rect(x - 0.024, 0.228, x + 0.024, 0.292, '#f6f0e0')
            d.circ(x + 0.012, 0.28, 0.006, '#c0443a')
    clock(far, [0.5, 0.56, 0.86][v], 0.18 if v != 2 else 0.4, 0.032)
    mid = S.L('mid')
    ficus(mid, [0.29, 0.7, 0.29][v], 0.74, 1.4)
    floor_lamp(mid, [0.58, 0.26, 0.92][v], 0.74, 1.2)
    near = S.L('near')
    cc = ['#3f6f8a', '#8a3a3a', '#5a7a4a'][v]
    ac = ['#c9a868', '#3f6f8a', '#d9a05a'][v]
    rug(near, 0.5, 0.86, 0.4, 0.06, col=['#8a3a3a', '#3f6f8a', '#c9734a'][v], col2=['#d9a05a', '#cfe0e6', '#f2ead6'][v])
    if v == 1:
        couch_chaise(near, 0.78, 0.86, 0.3, cc, 1.5, head=1)
        armchair(near, 0.2, 0.9, 1.4, ac, face=1)
        tx = 0.38
    else:
        couch_chaise(near, 0.22, 0.86, 0.3, cc, 1.5, head=-1)
        armchair(near, 0.8, 0.9, 1.4, ac, face=-1)
        tx = 0.62
    with near.piece(1.0) as d:  # side table with a tissue box and a glass of water
        d.ell(tx, 0.76, 0.045, 0.01, '#8a5a3a')
        d.rect(tx - 0.004, 0.76, tx + 0.004, 0.86, '#6a4a2a')
        d.ell(tx, 0.86, 0.025, 0.006, '#6a4a2a')
    with near.piece(0.6) as d:
        tissue_box(d, tx - 0.01, 0.758, 1.0)
        d.rect(tx + 0.02, 0.73, tx + 0.032, 0.758, (190, 220, 240, 210), r=0.002)
    fg = S.L('fg')
    if v == 2:
        plant(fg, 0.95, 1.0, 2.3, pot='#e6e0d4')
    with fg.piece(0.6) as d:  # notebook and pen on the armrest side table
        pass
    return {0: "therapist's office: a couch, an armchair, a ficus, tissues and a clock",
            1: 'green therapy room, couch by the window', 2: 'warm therapy room with bookshelves'}[v]


# ---------------------------------------------------------------- doctor

def skeleton_poster(L, x, y, h, rng, bg='#f6f3ea'):
    w = h * 0.55 / AR * 1.0
    with L.piece(0.7) as d:
        d.rect(x - w / 2, y - h / 2, x + w / 2, y + h / 2, bg, r=0.002)
        d.circ(x - w / 2 + 0.004, y - h / 2 + 0.004, 0.004, '#9aa4ae')
        d.circ(x + w / 2 - 0.004, y - h / 2 + 0.004, 0.004, '#9aa4ae')
    b = '#5a6a7a'
    s = h / 0.3
    with L.piece(0.35) as d:
        top = y - h / 2 + 0.03 * s
        d.ell(x, top + 0.02 * s, 0.017 * s, 0.02 * s, b)
        d.line([(x, top + 0.04 * s), (x, top + 0.17 * s)], b, 0.004 * s)
        for k in range(4):
            yy = top + 0.06 * s + k * 0.017 * s
            d.line([(x - 0.022 * s / AR * 1.5, yy + 0.006 * s), (x, yy), (x + 0.022 * s / AR * 1.5, yy + 0.006 * s)], b, 0.003 * s)
        d.line([(x - 0.03 * s / AR * 1.5, top + 0.055 * s), (x + 0.03 * s / AR * 1.5, top + 0.055 * s)], b, 0.003 * s)
        for sg in (-1, 1):
            d.line([(x + sg * 0.03 * s / AR * 1.5, top + 0.055 * s), (x + sg * 0.04 * s / AR * 1.5, top + 0.14 * s), (x + sg * 0.045 * s / AR * 1.5, top + 0.2 * s)], b, 0.003 * s)
            d.line([(x + sg * 0.01 * s, top + 0.18 * s), (x + sg * 0.015 * s, top + 0.25 * s)], b, 0.004 * s)
        d.ell(x, top + 0.18 * s, 0.02 * s, 0.012 * s, b)
    with L.piece(0.3) as d:  # a red heart and blue lungs on the side
        d.ell(x - 0.008 * s, top + 0.085 * s, 0.006 * s, 0.006 * s, '#e05a5a')


def bp_cuff(L, x, y, s=1.0):
    """A wall blood-pressure gauge: a round dial, a tube and a cuff hanging below."""
    with L.piece(0.8) as d:
        d.circ(x, y, 0.035 * s, '#3a3a40')
        d.circ(x, y, 0.029 * s, '#fbfbf6')
        for k in range(12):
            a = math.radians(-220 + k * 22)
            d.line([(x + math.cos(a) * 0.022 * s / AR * 1.0, y + math.sin(a) * 0.022 * s), (x + math.cos(a) * 0.026 * s / AR * 1.0, y + math.sin(a) * 0.026 * s)], '#5a5a66', 0.0015)
        d.line([(x, y), (x + 0.012 * s, y - 0.012 * s)], '#e05a5a', 0.003)
        d.line([(x, y + 0.035 * s), (x - 0.01, y + 0.1 * s), (x + 0.005, y + 0.14 * s)], '#3a3a40', 0.003)
        d.rect(x - 0.015, y + 0.12 * s, x + 0.025, y + 0.19 * s, '#2f4f7a', r=0.006)
        d.ell(x + 0.03, y + 0.17 * s, 0.01 * s, 0.014 * s, '#2e2e36')


def exam_couch(L, x, y, w, col='#5aa8a0', s=1.0, paper=True):
    with L.piece(1.0) as d:
        d.rect(x - w / 2, y - 0.13 * s, x + w / 2, y - 0.1 * s, '#c9cfd6', r=0.004)
        d.rect(x - w / 2, y - 0.16 * s, x + w / 2, y - 0.125 * s, col, r=0.012)
        d.poly([(x - w / 2, y - 0.15 * s), (x - w / 2 + 0.01, y - 0.22 * s), (x - w / 2 + 0.08, y - 0.18 * s), (x - w / 2 + 0.08, y - 0.15 * s)], col)
        for xx in (x - w / 2 + 0.02, x + w / 2 - 0.02):
            d.rect(xx - 0.005, y - 0.1 * s, xx + 0.005, y, '#9aa4ae')
        d.rect(x - w / 2 + 0.02, y - 0.03 * s, x + w / 2 - 0.02, y - 0.02 * s, '#9aa4ae')
    if paper:
        with L.piece(0.4) as d:
            d.rect(x - w / 2 + 0.05, y - 0.165 * s, x + w / 2 - 0.02, y - 0.152 * s, '#fbfbf8')
    with L.piece(0.7) as d:  # a step stool
        d.rect(x + 0.02, y - 0.05 * s, x + 0.09, y - 0.04 * s, '#9aa4ae')
        d.rect(x + 0.025, y - 0.04 * s, x + 0.03, y, '#9aa4ae')
        d.rect(x + 0.08, y - 0.04 * s, x + 0.085, y, '#9aa4ae')


def folding_screen(L, x, y, w, h, col='#cfe6e2', frame='#9aa4ae'):
    with L.piece(0.9) as d:
        for k in range(3):
            x0 = x - w / 2 + k * w / 3
            d.rect(x0 + 0.003, y - h, x0 + w / 3 - 0.003, y - 0.02, frame, r=0.003)
            d.rect(x0 + 0.008, y - h + 0.01, x0 + w / 3 - 0.008, y - 0.03, col)
            d.rect(x0 + 0.01, y - 0.02, x0 + 0.014, y, frame)
            d.rect(x0 + w / 3 - 0.014, y - 0.02, x0 + w / 3 - 0.01, y, frame)


def shape_chart(L, x, y, w, h):
    """An eye chart made of rings with gaps (no letters), getting smaller row by row."""
    with L.piece(0.7) as d:
        d.rect(x - w / 2, y - h / 2, x + w / 2, y + h / 2, '#fbfbf8', r=0.002)
    with L.piece(0.35) as d:
        for row, n in enumerate((1, 2, 3, 4, 5)):
            r = 0.018 * (1 - row * 0.17)
            yy = y - h / 2 + 0.03 + row * (h - 0.05) / 5
            for k in range(n):
                xx = x + (k - (n - 1) / 2) * (w - 0.02) / 5.5
                d.circ(xx, yy, r, '#2e2e36')
                d.circ(xx, yy, r * 0.6, '#fbfbf8')
                gap = (row + k) % 4
                dx, dy = [(1, 0), (0, 1), (-1, 0), (0, -1)][gap]
                d.rect(xx + dx * r * 0.5 / AR - r * 0.25 / AR, yy + dy * r * 0.5 - r * 0.25, xx + dx * r * 0.5 / AR + r * 0.25 / AR + dx * r * 0.6 / AR,
                       yy + dy * r * 0.5 + r * 0.25 + dy * r * 0.6, '#fbfbf8')


@biome('clinic', interior=True)
def clinic(S):
    v = S.variant % 3
    rng = S.rng
    wall = ['#e4eef0', '#eef0e6', '#e8eaf2'][v]
    shell(S, wall=wall, floor=['#c9d6d6', '#d6d2c6', '#c6cdd8'][v], fy=0.74, kind='tiles', ceiling=0.05)
    sky_ = S.L('sky')
    far = S.L('far')
    with sky_.piece(0.3) as d:  # painted lower wall band
        d.rect(-0.02, 0.5, 1.02, 0.72, shade(wall, 0.92))
        d.rect(-0.02, 0.495, 1.02, 0.502, shade(wall, 0.8))
    wx = [0.66, 0.66, 0.4][v]
    window_view(S, sky_, wx, 0.13, wx + 0.22, 0.45, view='trees' if v != 2 else 'city', frame='#f6f6f6', bars=2)
    blinds(far, wx, 0.13, wx + 0.22, 0.45, col='#f2f2ee', open_=0.35)
    ceiling_panels(far, 0.05, 2, lit=True)
    sx = [0.1, 0.42, 0.16][v]
    skeleton_poster(far, sx, 0.3, 0.3, rng)
    bp_cuff(far, [0.27, 0.6, 0.8][v], 0.27, 1.1)
    if v == 1:
        clock(far, 0.3, 0.2)
    if v != 1:
        shape_chart(far, [0.52, 0.0, 0.92][v], 0.3, 0.09, 0.22)
    mid = S.L('mid')
    with mid.piece(0.9) as d:  # sink with a mirror and a dispenser, glass cabinet
        kx = [0.4, 0.5, 0.62][v]
        d.rect(kx - 0.05, 0.56, kx + 0.05, 0.585, '#f2f4f6', r=0.006)
        d.rect(kx - 0.03, 0.585, kx + 0.03, 0.66, '#dde2e6', r=0.004)
        d.line([(kx + 0.02, 0.56), (kx + 0.02, 0.52), (kx, 0.52)], '#b9c0c8', 0.005)
        d.rect(kx + 0.06, 0.46, kx + 0.08, 0.52, '#f2f4f6', r=0.004)
    with mid.piece(0.9) as d:
        gx = [0.92, 0.16, 0.08][v]
        if v != 2:
            d.rect(gx - 0.06, 0.3, gx + 0.06, 0.74, '#f2f4f6', r=0.006)
            d.rect(gx - 0.052, 0.31, gx + 0.052, 0.52, '#cfe6f2')
            for k in range(3):
                d.rect(gx - 0.05, 0.37 + k * 0.06, gx + 0.05, 0.375 + k * 0.06, '#b9c0c8')
            d.rect(gx - 0.052, 0.54, gx + 0.052, 0.72, '#e6eaee', r=0.004)
    with mid.piece(0.6) as d:
        gx = [0.92, 0.16, 0.08][v]
        if v != 2:
            for k in range(3):
                for j in range(4):
                    d.rect(gx - 0.045 + j * 0.024, 0.34 + k * 0.06, gx - 0.032 + j * 0.024, 0.37 + k * 0.06,
                           ['#f6f3ea', '#e9a23a', '#3f7fbf', '#e05a5a'][(k + j) % 4], r=0.003)
    near = S.L('near')
    # doctor's desk with a monitor; a patient chair
    dx0, dx1 = [(0.6, 0.86), (0.12, 0.38), (0.64, 0.9)][v]
    chair(near, (dx0 + dx1) / 2 + (0.05 if v != 1 else -0.05), 0.8, 1.5, col='#3f6fa8', face=-1 if v != 1 else 1, office=True)
    with near.piece(1.0) as d:
        d.rect(dx0, 0.66, dx1, 0.68, '#f2f0ea', r=0.004)
        d.rect(dx1 - 0.08, 0.68, dx1 - 0.005, 0.86, '#dde0e2', r=0.004)
        d.rect(dx0 + 0.005, 0.68, dx0 + 0.015, 0.86, '#c9cfd6')
    monitor(near, dx0 + 0.07, 0.66, 1.3, on=True)
    with near.piece(0.6) as d:
        d.rect(dx0 + 0.13, 0.65, dx0 + 0.19, 0.66, '#fbfbf8')
        d.line([(dx0 + 0.2, 0.655), (dx0 + 0.22, 0.64), (dx0 + 0.235, 0.655)], '#2e2e36', 0.003)  # stethoscope
        d.circ(dx0 + 0.24, 0.656, 0.006, '#9aa4ae')
    if v == 2:
        folding_screen(near, 0.14, 0.9, 0.2, 0.36)
        exam_couch(S.L('mid'), 0.33, 0.78, 0.24, s=1.2)
    else:
        exam_couch(S.L('mid'), [0.2, 0.7][v], 0.78, 0.26, col=['#5aa8a0', '#c96a6a'][v], s=1.2)
    chair(near, dx0 - 0.06 if v != 1 else dx1 + 0.06, 0.95, 1.7, col='#c9cfd6', face=1 if v != 1 else -1)
    fg = S.L('fg')
    with fg.piece(0.9) as d:  # scales with a height rod
        x = 0.05 if v != 1 else 0.95
        d.rect(x - 0.04, 0.97, x + 0.04, 1.0, '#e6eaee', r=0.006)
        d.rect(x - 0.005, 0.45, x + 0.005, 0.97, '#c9cfd6')
        d.rect(x - 0.005, 0.55, x + 0.04, 0.56, '#9aa4ae')
        d.rect(x - 0.02, 0.62, x + 0.02, 0.67, '#f2f4f6', r=0.004)
    return {0: "doctor's office with an exam couch, a skeleton poster and a blood-pressure gauge",
            1: "clinic room, couch on the right, glass cabinet", 2: "doctor's room with a folding screen"}[v]


# ---------------------------------------------------------------- vet

def paw(d, x, y, r, col):
    d.ell(x, y + r * 0.35, r * 0.75, r * 0.6, col)
    for k, (dx, dy) in enumerate(((-0.75, -0.35), (-0.28, -0.8), (0.28, -0.8), (0.75, -0.35))):
        d.ell(x + dx * r / AR * 1.0, y + dy * r, r * 0.27, r * 0.33, col)


def carrier(L, x, y, s=1.0, col='#e9a23a'):
    with L.piece(0.9) as d:
        d.rect(x - 0.06 * s, y - 0.09 * s, x + 0.06 * s, y, col, r=0.02 * s)
        d.rect(x - 0.06 * s, y - 0.05 * s, x + 0.06 * s, y - 0.045 * s, shade(col, 0.8))
        d.rect(x - 0.015 * s, y - 0.11 * s, x + 0.015 * s, y - 0.09 * s, shade(col, 0.7), r=0.005)
    with L.piece(0.5) as d:
        d.rect(x + 0.03 * s, y - 0.075 * s, x + 0.058 * s, y - 0.015 * s, '#3a3a40', r=0.004)
        for k in range(4):
            d.rect(x + 0.033 * s + k * 0.006 * s, y - 0.072 * s, x + 0.035 * s + k * 0.006 * s, y - 0.018 * s, '#c9cfd6')


@biome('vet', interior=True)
def vet(S):
    v = S.variant % 3
    rng = S.rng
    wall = ['#dff0e8', '#f2ead8', '#e0e8f4'][v]
    shell(S, wall=wall, floor=['#bcc8c0', '#c9b8a0', '#b8c0cc'][v], fy=0.74, kind='tiles', ceiling=0.05)
    sky_ = S.L('sky')
    far = S.L('far')
    wall_tiles(sky_, -0.02, 0.5, 1.02, 0.74, shade(wall, 0.96), 0.045, depth=0.25)
    wx = [0.4, 0.68, 0.06][v]
    window_view(S, sky_, wx, 0.13, wx + 0.2, 0.43, view='trees', frame='#f6f6f6', bars=2)
    ceiling_panels(far, 0.05, 3, lit=True)
    px = [0.18, 0.47, 0.52][v]
    with far.piece(0.7) as d:  # paw poster
        d.rect(px - 0.06, 0.16, px + 0.06, 0.4, ['#f6c453', '#7fc6c0', '#f28b6b'][v], r=0.004)
    with far.piece(0.4) as d:
        paw(d, px, 0.29, 0.05, '#ffffff')
    with far.piece(0.7) as d:  # a small dog/cat silhouette poster
        qx = px + 0.15
        if qx + 0.05 < wx or qx - 0.05 > wx + 0.2:
            d.rect(qx - 0.045, 0.2, qx + 0.045, 0.36, '#fbfbf8', r=0.004)
            d.ell(qx, 0.31, 0.03, 0.025, '#c99a5e')
            d.circ(qx + 0.02, 0.27, 0.02, '#c99a5e')
            d.ell(qx + 0.032, 0.25, 0.008, 0.014, '#8a5a3a')
            d.circ(qx - 0.02, 0.27, 0.017, '#3a3a40')
            d.poly([(qx - 0.033, 0.27), (qx - 0.03, 0.245), (qx - 0.022, 0.26)], '#3a3a40')
            d.poly([(qx - 0.012, 0.26), (qx - 0.008, 0.245), (qx - 0.002, 0.265)], '#3a3a40')
    mid = S.L('mid')
    # cages stacked on one side
    cx0 = [0.66, 0.04, 0.66][v]
    with mid.piece(0.9) as d:
        d.rect(cx0, 0.3, cx0 + 0.3, 0.74, '#c9cfd6', r=0.004)
        for i in range(3):
            for j in range(2):
                x0, y0 = cx0 + 0.01 + i * 0.097, 0.31 + j * 0.21
                d.rect(x0, y0, x0 + 0.09, y0 + 0.2, '#5a6470', r=0.003)
    with mid.piece(0.6) as d:  # some pets inside (simple shapes), bars over them
        animals = [(0, 1, 'cat', '#e9a23a'), (1, 1, 'dog', '#f2ead6'), (2, 0, 'cat', '#3a3a40'), (0, 0, 'rabbit', '#ffffff')]
        for i, j, kind, col in animals[: 2 + v]:
            x0, y0 = cx0 + 0.01 + i * 0.097, 0.31 + j * 0.21
            cx, cy = x0 + 0.045, y0 + 0.17
            d.ell(cx, cy, 0.03, 0.022, col)
            d.circ(cx + 0.02, cy - 0.025, 0.02, col)
            if kind == 'cat':
                d.poly([(cx + 0.008, cy - 0.04), (cx + 0.012, cy - 0.06), (cx + 0.02, cy - 0.043)], col)
                d.poly([(cx + 0.022, cy - 0.043), (cx + 0.03, cy - 0.06), (cx + 0.034, cy - 0.038)], col)
            elif kind == 'dog':
                d.ell(cx + 0.01, cy - 0.02, 0.008, 0.016, '#c99a5e')
            else:
                d.ell(cx + 0.014, cy - 0.06, 0.006, 0.02, col)
                d.ell(cx + 0.026, cy - 0.06, 0.006, 0.02, col)
            d.circ(cx + 0.026, cy - 0.028, 0.003, '#1e1e26')
        for i in range(3):
            for j in range(2):
                x0, y0 = cx0 + 0.01 + i * 0.097, 0.31 + j * 0.21
                for k in range(1, 7):
                    d.rect(x0 + k * 0.0128, y0 + 0.005, x0 + k * 0.0128 + 0.002, y0 + 0.195, '#d0d6dc')
                d.rect(x0 + 0.003, y0 + 0.004, x0 + 0.087, y0 + 0.012, '#d0d6dc')
    with mid.piece(0.9) as d:  # shelf of food bags and jars
        sx = [0.06, 0.42, 0.3][v]
        d.rect(sx, 0.52, sx + 0.2, 0.535, '#9aa4ae')
        d.rect(sx, 0.42, sx + 0.2, 0.435, '#9aa4ae')
        for k in range(5):
            d.rect(sx + 0.01 + k * 0.038, 0.45 + (k % 2) * 0.01, sx + 0.04 + k * 0.038, 0.52, ['#3f7fbf', '#e05a5a', '#3d8a5a', '#f6c453', '#8a5a9a'][k], r=0.006)
            d.rect(sx + 0.01 + k * 0.038, 0.38, sx + 0.035 + k * 0.038, 0.42, (200, 225, 240, 230), r=0.004)
    near = S.L('near')
    # steel exam table on a pedestal
    ex = [0.36, 0.6, 0.38][v]
    with near.piece(1.0) as d:
        d.rect(ex - 0.12, 0.66, ex + 0.12, 0.685, '#c9cfd6', r=0.006)
        d.rect(ex - 0.115, 0.685, ex + 0.115, 0.695, '#9aa4ae')
        d.rect(ex - 0.02, 0.695, ex + 0.02, 0.88, '#9aa4ae')
        d.ell(ex, 0.885, 0.07, 0.014, '#7a8490')
    with near.piece(0.7) as d:
        d.rect(ex - 0.1, 0.655, ex - 0.05, 0.665, '#7fc6c0', r=0.003)
        d.rect(ex + 0.05, 0.645, ex + 0.09, 0.665, '#fbfbf8', r=0.004)
    # floor scales with a dial
    sx = [0.12, 0.86, 0.86][v]
    with near.piece(1.0) as d:
        d.rect(sx - 0.07, 0.9, sx + 0.07, 0.93, '#9aa4ae', r=0.006)
        d.rect(sx - 0.065, 0.885, sx + 0.065, 0.9, '#3a3a40', r=0.004)
        d.rect(sx + 0.05, 0.7, sx + 0.06, 0.9, '#9aa4ae')
        d.circ(sx + 0.055, 0.69, 0.028, '#fbfbf6')
        d.line([(sx + 0.055, 0.69), (sx + 0.065, 0.676)], '#e05a5a', 0.003)
    fg = S.L('fg')
    carrier(fg, 0.92 if v != 1 else 0.08, 1.0, 2.0, col=['#e9a23a', '#3f7fbf', '#e05a5a'][v])
    with fg.piece(0.8) as d:  # a ball and a bone toy
        bx = 0.78 if v != 1 else 0.22
        d.circ(bx, 0.975, 0.025, '#e05a5a')
        d.line([(bx + 0.04, 0.99), (bx + 0.08, 0.98)], '#f6f3ea', 0.012)
        for x, y in ((bx + 0.04, 0.99), (bx + 0.08, 0.98)):
            d.circ(x - 0.004, y - 0.008, 0.009, '#f6f3ea')
            d.circ(x + 0.004, y + 0.008, 0.009, '#f6f3ea')
    return {0: 'vet clinic: steel exam table, scales, cages with pets, a paw poster',
            1: 'warm vet room with the cages on the left', 2: 'blue vet room with a carrier and toys'}[v]


# ---------------------------------------------------------------- empty flat

@biome('apartment_empty', interior=True)
def apartment_empty(S):
    v = S.variant % 3
    rng = S.rng
    wall = ['#f4f2ec', '#f0efea', '#eef0ee'][v]
    fy = 0.73
    shell(S, wall=wall, floor=['#c9a06a', '#b98a5e', '#c8bfb0'][v], fy=fy, kind='planks')
    sky_ = S.L('sky')
    far = S.L('far')
    with sky_.piece(0.25) as d:  # marks where furniture once stood, a socket, a switch
        d.rect(0.08, 0.36, 0.22, 0.6, shade(wall, 0.96), r=0.004)
        d.rect(0.77, 0.25, 0.86, 0.33, shade(wall, 0.95), r=0.003)
        d.rect(0.27, 0.62, 0.29, 0.645, '#e6e2d8', r=0.003)
        d.rect(0.07, 0.4, 0.085, 0.43, '#e6e2d8', r=0.002) if v == 1 else None
        d.rect(0.94, 0.4, 0.955, 0.425, '#e6e2d8', r=0.002)
    wx0, wx1 = [(0.36, 0.64), (0.55, 0.85), (0.3, 0.55)][v]
    window_view(S, sky_, wx0, 0.14, wx1, 0.52, view='city' if v != 2 else 'trees', frame='#fbfbf8', bars=2)
    if v == 1:  # the 'view' is the wall of the neighbouring block
        with sky_.piece(0.4) as d:
            d.rect(wx0, 0.2, wx1, 0.52, '#c9c2b4')
            for i in range(4):
                for j in range(3):
                    d.window(wx0 + 0.02 + i * 0.07, 0.24 + j * 0.09, wx0 + 0.05 + i * 0.07, 0.29 + j * 0.09, rng=rng)
    with far.piece(0.7) as d:  # window sill
        d.rect(wx0 - 0.03, 0.52, wx1 + 0.03, 0.535, '#fbfbf8', r=0.003)
    radiator(far, wx0 + 0.04, wx1 - 0.04, 0.68, 0.1)
    sunbeam(S, S.L('mid'), wx0, wx1, 0.14, 0.52, fy)
    bulb(far, 0.5 if v != 1 else 0.3, 0.2, s=1.6)
    mid = S.L('mid')
    # a door frame to the next room
    dxo = [0.14, 0.18, 0.78][v]
    with mid.piece(0.9) as d:
        d.rect(dxo - 0.07, 0.3, dxo + 0.07, fy, '#fbfbf8')
        d.rect(dxo - 0.058, 0.315, dxo + 0.058, fy, shade(wall, 0.82))
        d.rect(dxo - 0.058, 0.6, dxo + 0.058, fy, shade(['#c9a06a', '#b98a5e', '#c8bfb0'][v], 0.8))
    near = S.L('near')
    if v == 0:  # a few moving boxes
        for x, y, w, h in ((0.8, 0.9, 0.12, 0.12), (0.88, 0.92, 0.1, 0.1), (0.83, 0.78, 0.09, 0.08)):
            with near.piece(1.0) as d:
                d.rect(x - w / 2, y - h, x + w / 2, y, '#c99a5e', r=0.003)
                d.rect(x - w / 2, y - h, x + w / 2, y - h + 0.012, shade('#c99a5e', 0.85))
                d.rect(x - 0.008, y - h, x + 0.008, y - h * 0.4, '#d9c08a')
    elif v == 1:  # a stepladder, a paint tin and a rolled rug
        with near.piece(1.0) as d:
            d.line([(0.78, 0.97), (0.82, 0.6)], '#9aa4ae', 0.008)
            d.line([(0.88, 0.97), (0.84, 0.6)], '#9aa4ae', 0.008)
            for k in range(4):
                y = 0.68 + k * 0.075
                d.line([(0.82 - (y - 0.6) * 0.1, y), (0.84 + (y - 0.6) * 0.11, y)], '#9aa4ae', 0.006)
            d.rect(0.8, 0.58, 0.86, 0.6, '#b9c0c8', r=0.004)
            d.rect(0.62, 0.9, 0.68, 0.97, '#e6eaee', r=0.004)
            d.ell(0.65, 0.9, 0.03, 0.008, '#3f7fbf')
        with near.piece(1.0) as d:
            d.rect(0.04, 0.88, 0.36, 0.95, '#a8323a', r=0.035)
            d.ell(0.36, 0.915, 0.02, 0.035, '#d9a23a')
    else:  # one chair left behind, a stack of newspapers (blank)
        chair(near, 0.62, 0.95, 1.8, col='#b98a5e', face=-1)
        with near.piece(1.0) as d:
            for k in range(4):
                d.rect(0.12 + 0.004 * (k % 2), 0.95 - 0.02 * (k + 1), 0.24 + 0.004 * (k % 2), 0.95 - 0.02 * k, '#ecebe2', r=0.002)
    fg = S.L('fg')
    with fg.piece(0.4) as d:  # dust motes in the light
        if S.look.time in ('day', 'golden') and S.look.weather == 'clear':
            for _ in range(18):
                d.circ(wx0 + (wx1 - wx0) * rng.random() + 0.05, 0.3 + 0.5 * rng.random(), 0.002, '#fff6dc', lit=True)
    return {0: 'empty flat for viewing: white walls, a window, a radiator, a bare bulb, moving boxes',
            1: 'empty flat under repair, the window looks at the next block', 2: 'empty room with one chair left'}[v]


# ---------------------------------------------------------------- call centre

def headset(d, x, y, s=1.0, col='#2e2e36'):
    pts = [(x + 0.016 * s * math.cos(a) / AR * 1.8, y - 0.02 * s * math.sin(a)) for a in np.linspace(0, math.pi, 14)]
    d.line(pts, col, 0.003 * s)
    d.ell(x - 0.016 * s / AR * 1.8, y, 0.007 * s, 0.009 * s, col)
    d.ell(x + 0.016 * s / AR * 1.8, y, 0.007 * s, 0.009 * s, col)
    d.line([(x - 0.016 * s / AR * 1.8, y + 0.004), (x - 0.006, y + 0.018 * s)], col, 0.002 * s)


@biome('call_center', interior=True)
def call_center(S):
    v = S.variant % 3
    rng = S.rng
    wall = ['#e6eaee', '#efe8de', '#2f3a4a'][v]
    shell(S, wall=wall, floor=['#6f7884', '#7d7468', '#3e4450'][v], fy=0.66, kind='carpet', ceiling=0.05)
    sky_ = S.L('sky')
    far = S.L('far')
    if v != 2:
        for k in range(3):
            x = 0.04 + k * 0.33 if v == 0 else 0.36 + k * 0.22
            if v == 1 and k == 2:
                break
            window_view(S, sky_, x, 0.1, x + (0.24 if v == 0 else 0.18), 0.42, view='city', frame='#d0d4da', bars=2)
            blinds(far, x, 0.1, x + (0.24 if v == 0 else 0.18), 0.42, open_=0.4)
    ceiling_panels(far, 0.05, 4, lit=True)
    # the queue board: rows of dots (green waiting, amber, red)
    bx = [0.5, 0.18, 0.5][v]
    bw = 0.26 if v != 2 else 0.4
    with far.piece(0.7) as d:
        d.rect(bx - bw / 2, 0.12 if v != 0 else 0.44, bx + bw / 2, (0.12 if v != 0 else 0.44) + (0.1 if v != 2 else 0.16), '#1e1e26', r=0.006)
    with far.piece(0.3) as d:
        y0 = 0.12 if v != 0 else 0.44
        rows = 3 if v != 2 else 5
        n = int(bw / 0.018)
        for j in range(rows):
            m = int(n * (0.3 + 0.7 * rng.random()))
            for i in range(n):
                on = i < m
                c = ['#6af0a0', '#f6c453', '#f05a4a', '#6af0a0', '#7fb6e8'][j % 5] if on else '#3a3a44'
                d.circ(bx - bw / 2 + 0.012 + i * 0.018, y0 + 0.022 + j * 0.028, 0.006, c, lit=on)
    far.glow_rect(bx - bw / 2, 0.12 if v != 0 else 0.44, bx + bw / 2, (0.12 if v != 0 else 0.44) + 0.1)
    mid = S.L('mid')
    # rows of desks behind low partitions, with monitors and headsets
    pc = ['#7f9fbf', '#c9a868', '#4a6a8a'][v]
    for row, (y, sc, n) in enumerate(((0.62, 0.8, 7), (0.7, 1.0, 5))):
        L = far if row == 0 else mid
        for k in range(n):
            x = (k + 0.5) / n
            if row == 1 and 0.36 < x < 0.64:
                continue
            monitor(L, x - 0.02 * sc, y - 0.07 * sc, 1.1 * sc, on=True)
        with L.piece(0.9) as d:
            for k in range(n):
                x = (k + 0.5) / n
                if row == 1 and 0.36 < x < 0.64:
                    continue
                d.rect(x - 0.5 / n + 0.004, y - 0.08 * sc, x + 0.5 / n - 0.004, y, pc, r=0.006)
                d.rect(x - 0.5 / n + 0.004, y - 0.085 * sc, x + 0.5 / n - 0.004, y - 0.075 * sc, shade(pc, 0.75), r=0.003)
        with L.piece(0.5) as d:
            for k in range(n):
                x = (k + 0.5) / n
                if row == 1 and 0.36 < x < 0.64:
                    continue
                headset(d, x + 0.04 * sc, y - 0.04 * sc, 1.2 * sc, '#2e2e36')
                d.circ(x - 0.05 * sc, y - 0.05 * sc, 0.006, '#f6c453')
    near = S.L('near')
    # one desk close up on each side with a headset and a cup
    for x0, x1, face in ((-0.02, 0.24, 1), (0.76, 1.02, -1)):
        with near.piece(1.0) as d:
            d.rect(x0, 0.78, x1, 0.8, '#e6e2da', r=0.004)
            d.rect(x0, 0.55 if face > 0 else 0.55, x0 + 0.012 if face < 0 else x0 + 0.012, 0.8, pc) if False else None
            d.rect(x0 if face > 0 else x1 - 0.015, 0.56, x0 + 0.015 if face > 0 else x1, 1.02, pc, r=0.006)
        monitor(near, (x0 + x1) / 2, 0.78, 1.7, on=True)
        with near.piece(0.6) as d:
            headset(d, (x0 + x1) / 2 + face * 0.08, 0.77, 2.2)
            mug(d, (x0 + x1) / 2 - face * 0.08, 0.78, 1.5, ['#e05a5a', '#3f7fbf', '#f6c453'][v])
    chair(near, 0.27, 0.99, 1.8, col='#2e2e36', face=-1, office=True)
    chair(near, 0.73, 0.99, 1.8, col='#2e2e36', face=1, office=True)
    fg = S.L('fg')
    if v == 1:
        ficus(fg, 0.5, 1.15, 1.2) if False else plant(fg, 0.5, 1.04, 1.4)
    return {0: 'call centre: rows of desks with headsets, a queue board of dots',
            1: 'warm call centre by the windows', 2: 'night shift call centre, a big dot board'}[v]


# ---------------------------------------------------------------- gym

def mirror(L, x0, y0, x1, y1, frame='#c9cfd6'):
    with L.piece(0.6) as d:
        d.rect(x0 - 0.006, y0 - 0.01, x1 + 0.006, y1 + 0.01, frame, r=0.003)
        d.rect(x0, y0, x1, y1, '#d8e6ee')
    with L.piece(0.25) as d:  # streaks of reflection
        for k in range(int((x1 - x0) / 0.12) + 1):
            x = x0 + 0.03 + k * 0.12
            d.poly([(x, y1), (x + 0.03, y1), (min(x + 0.09, x1), y0), (min(x + 0.06, x1), y0)], (255, 255, 255, 70))


def dumbbell(d, x, y, s, col):
    d.rect(x - 0.022 * s, y - 0.003 * s, x + 0.022 * s, y + 0.003 * s, '#9aa4ae')
    for sx in (-1, 1):
        d.rect(x + sx * 0.022 * s - 0.006 * s, y - 0.012 * s, x + sx * 0.022 * s + 0.006 * s, y + 0.012 * s, col, r=0.003)


def treadmill(L, x, y, s=1.0, col='#2e2e36', face=1):
    k = 0.5 * s  # x offsets in width units
    with L.piece(1.0) as d:
        d.poly([(x - 0.11 * k, y - 0.03 * s), (x + 0.11 * k, y - 0.05 * s), (x + 0.11 * k, y), (x - 0.11 * k, y)], col)
        d.rect(x - 0.105 * k, y - 0.045 * s, x + 0.1 * k, y - 0.035 * s, '#2e2e36')
        hx_ = x + face * 0.09 * k
        d.line([(hx_, y - 0.04 * s), (hx_ + face * 0.012 * k, y - 0.24 * s)], '#8a8f99', 0.008 * s)
        d.rect(hx_ + face * 0.012 * k - 0.03 * k, y - 0.27 * s, hx_ + face * 0.012 * k + 0.03 * k, y - 0.225 * s, '#3a3a44', r=0.006)
        d.line([(hx_, y - 0.19 * s), (hx_ - face * 0.07 * k, y - 0.185 * s)], '#8a8f99', 0.005 * s)
    with L.piece(0.4) as d:
        cx = hx_ + face * 0.012 * k
        d.rect(cx - 0.02 * k, y - 0.262 * s, cx + 0.02 * k, y - 0.235 * s, '#6af0a0', lit=True)


def gym_machine(L, x, y, s=1.0, col='#c0443a'):
    """A cable station: a frame, a weight stack, a seat and a bar."""
    fcol = shade(col, 0.8)
    with L.piece(1.0) as d:
        d.rect(x - 0.08 * s, y - 0.4 * s, x - 0.07 * s, y, fcol)
        d.rect(x + 0.07 * s, y - 0.4 * s, x + 0.08 * s, y, fcol)
        d.rect(x - 0.08 * s, y - 0.41 * s, x + 0.08 * s, y - 0.39 * s, fcol)
        d.rect(x - 0.1 * s, y - 0.01 * s, x + 0.1 * s, y, '#3a3a40')
        for k in range(10):
            d.rect(x - 0.035 * s, y - 0.32 * s + k * 0.022 * s, x + 0.035 * s, y - 0.302 * s + k * 0.022 * s, '#3a3a44', r=0.002)
        d.line([(x, y - 0.39 * s), (x, y - 0.33 * s)], '#9aa4ae', 0.003)
        d.line([(x - 0.06 * s, y - 0.36 * s), (x + 0.06 * s, y - 0.36 * s)], '#9aa4ae', 0.006 * s)
        d.rect(x + 0.1 * s, y - 0.12 * s, x + 0.2 * s, y - 0.1 * s, col, r=0.008)
        d.rect(x + 0.145 * s, y - 0.1 * s, x + 0.155 * s, y, '#5a5a66')


@biome('gym', interior=True)
def gym(S):
    v = S.variant % 3
    rng = S.rng
    wall = ['#e8e6e2', '#2e3440', '#efe6d8'][v]
    accent = ['#e05a5a', '#f6c453', '#3d8a8a'][v]
    shell(S, wall=wall, floor=['#3a3a44', '#2a2a30', '#b98a5e'][v], fy=0.72, kind='tiles' if v < 2 else 'planks', ceiling=0.05)
    sky_ = S.L('sky')
    far = S.L('far')
    with sky_.piece(0.3) as d:  # an accent stripe along the wall
        d.rect(-0.02, 0.16, 1.02, 0.2, accent)
    if v != 1:  # high windows
        for k in range(4):
            x = 0.06 + k * 0.24
            window_view(S, sky_, x, 0.06, x + 0.16, 0.14, view='city', frame='#d0d4da', bars=2, depth=0.6)
    ceiling_panels(far, 0.04, 4, lit=True)
    # the mirror wall
    mx0, mx1 = [(0.3, 0.98), (0.02, 0.7), (0.22, 0.78)][v]
    mirror(far, mx0, 0.25, mx1, 0.7)
    mid = S.L('mid')
    # dumbbell rack along the mirror
    rx0, rx1 = [(0.36, 0.7), (0.06, 0.4), (0.3, 0.56)][v]
    with mid.piece(1.0) as d:
        d.rect(rx0, 0.6, rx1, 0.615, '#3a3a40')
        d.rect(rx0, 0.66, rx1, 0.675, '#3a3a40')
        for x in (rx0 + 0.01, rx1 - 0.01):
            d.rect(x - 0.005, 0.6, x + 0.005, 0.73, '#3a3a40')
    with mid.piece(0.8) as d:
        n = int((rx1 - rx0) / 0.05)
        for k in range(n):
            x = rx0 + 0.03 + k * (rx1 - rx0 - 0.04) / n
            dumbbell(d, x, 0.592, 1.0 + 0.05 * k, ['#2e2e36', accent][k % 2])
            dumbbell(d, x, 0.652, 1.1 + 0.05 * k, ['#2e2e36', '#5a5a66'][k % 2])
    gym_machine(mid, [0.84, 0.82, 0.12][v], 0.74, 1.0, col=accent)
    with mid.piece(0.9) as d:  # rolled mats and a swiss ball against the wall
        mx = [0.1, 0.5, 0.66][v]
        for k in range(3):
            d.ell(mx + k * 0.04, 0.7, 0.02, 0.03, ['#3f7fbf', '#8a5a9a', '#3d8a5a'][k])
            d.ell(mx + k * 0.04, 0.7, 0.008, 0.012, shade(['#3f7fbf', '#8a5a9a', '#3d8a5a'][k], 0.7))
        d.circ(mx + 0.17 if v != 2 else 0.88, 0.69, 0.045, accent)
    near = S.L('near')
    tx = [0.16, 0.84, 0.84][v]
    treadmill(near, tx, 0.95, 1.9, col='#5a5a66', face=1 if v != 0 else -1)
    wx = [0.82, 0.18, 0.2][v]  # a flat weight bench with a barbell on a rack, on the other side
    with near.piece(1.0) as d:
        d.rect(wx - 0.11, 0.84, wx + 0.11, 0.87, accent, r=0.012)
        for x in (wx - 0.08, wx + 0.08):
            d.rect(x - 0.006, 0.87, x + 0.006, 0.95, '#3a3a40')
            d.rect(x - 0.025, 0.945, x + 0.025, 0.955, '#3a3a40')
        for x in (wx - 0.13, wx + 0.13):
            d.rect(x - 0.005, 0.66, x + 0.005, 0.95, '#5a5a66')
        d.line([(wx - 0.2, 0.68), (wx + 0.2, 0.68)], '#b9c0c8', 0.007)
        for x in (wx - 0.17, wx + 0.17):
            d.ell(x, 0.68, 0.012, 0.05, '#2e2e36')
            d.ell(x + (0.012 if x > wx else -0.012), 0.68, 0.009, 0.04, '#3a3a44')
    with near.piece(1.0) as d:  # kettlebells
        kx = [0.34, 0.6, 0.6][v]
        for k, sz in enumerate((1.0, 1.25, 1.5)):
            x = kx + k * 0.04
            d.circ(x, 0.96 - 0.02 * sz, 0.02 * sz, '#3a3a44')
            d.line([(x - 0.012 * sz, 0.96 - 0.035 * sz), (x - 0.01 * sz, 0.96 - 0.055 * sz), (x + 0.01 * sz, 0.96 - 0.055 * sz), (x + 0.012 * sz, 0.96 - 0.035 * sz)], '#3a3a44', 0.005)
    fg = S.L('fg')
    px = 0.03 if v != 0 else 0.97  # a punching bag on a chain in the corner
    with fg.piece(0.9) as d:
        d.line([(px, -0.02), (px, 0.36)], '#7a7a86', 0.004)
        d.rect(px - 0.04, 0.36, px + 0.04, 0.78, ['#c0443a', '#2e2e36', '#8a5a3a'][v], r=0.035)
        d.rect(px - 0.04, 0.44, px + 0.04, 0.455, '#2e2e36')
        d.rect(px - 0.04, 0.68, px + 0.04, 0.695, '#2e2e36')
    with fg.piece(0.7) as d:  # a water bottle and a towel on the floor edge
        bx = 0.44
        d.rect(bx, 0.95, bx + 0.018, 1.0, '#7fb6e8', r=0.004)
        d.rect(bx + 0.004, 0.94, bx + 0.014, 0.952, '#3f6fa8')
    return {0: 'gym: mirror wall, dumbbell rack, a cable machine, a treadmill, mats',
            1: 'dark gym with a yellow stripe', 2: 'studio gym with a wooden floor'}[v]


# ---------------------------------------------------------------- supermarket

GOODS = ['#e05a5a', '#f6c453', '#3f7fbf', '#6fb850', '#f28b6b', '#b99be0', '#f6f3ea', '#e9a23a', '#3d8a8a']


def goods_row(d, x0, x1, y, h, rng, s=1.0):
    x = x0
    while x < x1 - 0.012 * s:
        c = GOODS[int(rng.integers(len(GOODS)))]
        kind = rng.random()
        if kind < 0.3:  # bottle
            w = 0.012 * s
            hh = h * (0.7 + 0.3 * rng.random())
            d.rect(x, y - hh, x + w, y, c, r=0.004 * s)
            d.rect(x + w * 0.3, y - hh - 0.012 * s, x + w * 0.7, y - hh + 0.002, c)
            x += w + 0.003
        elif kind < 0.5:  # jars
            w = 0.016 * s
            d.rect(x, y - h * 0.55, x + w, y, (200, 225, 240, 230), r=0.004 * s)
            d.rect(x, y - h * 0.55, x + w, y - h * 0.45, c)
            x += w + 0.003
        else:  # boxes, a pale band instead of a label
            w = (0.014 + 0.016 * rng.random()) * s
            hh = h * (0.6 + 0.4 * rng.random())
            d.rect(x, y - hh, x + w, y, c, r=0.002)
            d.rect(x + w * 0.2, y - hh * 0.7, x + w * 0.8, y - hh * 0.45, '#ffffff')
            x += w + 0.002


def cart(L, x, y, s=1.0, face=1):
    with L.piece(1.0) as d:
        X = lambda u: x + face * u * s  # noqa: E731
        d.line([(X(-0.1), y - 0.18 * s), (X(-0.08), y - 0.07 * s), (X(0.08), y - 0.07 * s), (X(0.1), y - 0.18 * s), (X(-0.1), y - 0.18 * s)], '#9aa6b0', 0.005)
        for k in range(1, 7):
            u = -0.1 + k * 0.2 / 7
            d.line([(X(u), y - 0.18 * s), (X(u * 0.85), y - 0.07 * s)], '#9aa6b0', 0.0025)
        d.line([(X(-0.1), y - 0.15 * s), (X(0.1), y - 0.15 * s)], '#9aa6b0', 0.0025)
        d.line([(X(-0.1), y - 0.18 * s), (X(-0.13), y - 0.21 * s)], '#9aa6b0', 0.005)
        d.line([(X(-0.13), y - 0.21 * s), (X(-0.15), y - 0.21 * s)], '#e05a5a', 0.008)
        d.line([(X(-0.08), y - 0.07 * s), (X(-0.07), y - 0.02 * s), (X(0.08), y - 0.02 * s)], '#9aa6b0', 0.004)
        for u in (-0.06, 0.07):
            d.circ(X(u), y - 0.012 * s, 0.012 * s, '#3a3a40')
    with L.piece(0.7) as d:  # some shopping in it
        d.rect(X(-0.05) - 0.02, y - 0.22 * s, X(-0.05) + 0.02, y - 0.17 * s, '#f6c453', r=0.003)
        d.circ(X(0.02), y - 0.19 * s, 0.022 * s, '#7cc45e')
        d.rect(X(0.05), y - 0.24 * s, X(0.05) + 0.012, y - 0.17 * s, '#3f7fbf', r=0.004)


@biome('supermarket', interior=True)
def supermarket(S):
    v = S.variant % 3
    rng = S.rng
    wall = ['#f2ede0', '#e6eef2', '#f4e6dc'][v]
    fy = 0.74 if v != 0 else 0.52
    shell(S, wall=wall, floor='#d6d2c8', fy=fy, kind='tiles', ceiling=0.05)
    sky_ = S.L('sky')
    far = S.L('far')
    mid = S.L('mid')
    near = S.L('near')
    if v == 0:  # an aisle in perspective: two shelf runs converging to the back wall
        vx, vy = 0.5, 0.36
        with sky_.piece(0.3) as d:
            d.rect(0.38, 0.14, 0.62, 0.52, shade(wall, 0.94))
            for k in range(3):  # far end: fridges with a cool glow
                d.rect(0.39 + k * 0.077, 0.24, 0.46 + k * 0.077, 0.52, '#cfe6f2', lit=True)
        sky_.glow_rect(0.39, 0.24, 0.61, 0.52)
        ceiling_panels(far, 0.05, 3, lit=True)
        for side in (-1, 1):
            xo, xi = (0.0, 0.38) if side < 0 else (1.0, 0.62)
            with mid.piece(1.0) as d:  # the shelf body: a trapezoid
                d.poly([(xo - side * 0.0, 0.08), (xi, 0.2), (xi, 0.52), (xo, 0.96)], '#b9b2a4')
            with mid.piece(0.8) as d:  # shelves lines with goods
                for k in range(6):
                    t = (k + 1) / 7
                    yo, yi = 0.08 + 0.88 * t, 0.2 + 0.32 * t
                    d.line([(xo, yo), (xi, yi)], '#8a8f99', 0.006)
                    # goods: small blocks sitting on the shelf, shrinking with distance
                    n = 14
                    for j in range(n):
                        u = (j + 0.2) / n
                        x = xo + (xi - xo) * u
                        y = yo + (yi - yo) * u
                        sc = 1 - 0.7 * u
                        h = 0.1 * sc
                        w = 0.022 * sc
                        c = GOODS[int(rng.integers(len(GOODS)))]
                        d.rect(min(x, x - side * w), y - h, max(x, x - side * w), y - 0.003, c, r=0.002)
        cart(near, 0.5, 0.97, 1.7, face=1)
        with near.piece(0.6) as d:  # price-less shelf tags: little coloured strips
            pass
    else:
        ceiling_panels(far, 0.05, 4, lit=True)
        if v == 1:  # a wall of shelves and the checkout
            for x0 in (0.02, 0.33):
                with far.piece(0.9) as d:
                    d.rect(x0, 0.14, x0 + 0.29, 0.74, '#b9b2a4', r=0.004)
                    d.rect(x0 + 0.01, 0.15, x0 + 0.28, 0.74, '#e6e0d4')
                    for k in range(5):
                        d.rect(x0 + 0.005, 0.25 + k * 0.11, x0 + 0.285, 0.262 + k * 0.11, '#8a8f99')
                with far.piece(0.6) as d:
                    for k in range(5):
                        goods_row(d, x0 + 0.015, x0 + 0.275, 0.25 + k * 0.11, 0.08, rng)
            window_view(S, sky_, 0.68, 0.12, 0.98, 0.5, view='city', frame='#c9ced4', bars=3)
            with mid.piece(1.0) as d:  # checkout belt
                d.rect(0.62, 0.6, 0.98, 0.625, '#3a3a40', r=0.004)
                d.rect(0.63, 0.625, 0.97, 0.8, '#3f7fbf', r=0.006)
                d.rect(0.88, 0.5, 0.95, 0.6, '#2e2e36', r=0.004)
            with mid.piece(0.5) as d:
                d.rect(0.885, 0.51, 0.945, 0.56, '#7fb6e8', lit=True)
                for k in range(4):
                    d.rect(0.66 + k * 0.04, 0.585, 0.69 + k * 0.04, 0.6, GOODS[k * 2], r=0.003)
            cart(near, 0.2, 0.96, 1.6, face=-1)
        else:  # produce section and glass-door fridges
            for k in range(4):
                x = 0.04 + k * 0.12
                with far.piece(0.9) as d:
                    d.rect(x, 0.12, x + 0.11, 0.72, '#dfe4ea', r=0.006)
                    d.rect(x + 0.008, 0.14, x + 0.102, 0.66, '#d6e8f0')
                    d.rect(x + 0.09, 0.3, x + 0.096, 0.45, '#9aa4ae')
                with far.piece(0.5) as d:
                    for j in range(4):
                        goods_row(d, x + 0.012, x + 0.088, 0.25 + j * 0.12, 0.07, rng, 0.8)
                        d.rect(x + 0.008, 0.25 + j * 0.12, x + 0.102, 0.255 + j * 0.12, '#b9c0c8')
            with far.piece(0.9) as d:  # a striped canopy over the produce, with hanging lamps and bread baskets
                d.rect(0.55, 0.3, 1.0, 0.33, '#3d8a5a')
                for k in range(9):
                    x = 0.55 + k * 0.05
                    d.poly([(x, 0.33), (x + 0.05, 0.33), (x + 0.05, 0.4), (x + 0.025, 0.42), (x, 0.4)], '#3d8a5a' if k % 2 else '#f6f3ea')
                d.rect(0.6, 0.5, 0.96, 0.512, '#8a5a3a')
            with far.piece(0.7) as d:
                for k in range(4):
                    x = 0.63 + k * 0.09
                    d.ell(x, 0.49, 0.035, 0.016, '#b07a4a')
                    for j in range(3):
                        d.ell(x - 0.02 + j * 0.02, 0.475, 0.014, 0.01, '#d9a05a')
            for x in (0.66, 0.78, 0.9):
                lamp_pendant(far, x, 0.22, 0.8, col='#3d8a5a', cord=0.05)
            fruit = [('#e0403a', '#c0302a'), ('#f6d353', '#e0b030'), ('#7cc45e', '#5aa040'), ('#f08a2e', '#d06a1e'), ('#8a3a6a', '#6a2a50')]
            for k in range(3):  # produce crates on stands
                x = 0.58 + k * 0.14
                with mid.piece(1.0) as d:
                    d.poly([(x, 0.6), (x + 0.13, 0.6), (x + 0.12, 0.74), (x + 0.01, 0.74)], '#b07a4a')
                    d.rect(x + 0.02, 0.74, x + 0.03, 0.76, '#7a5030')
                    d.rect(x + 0.1, 0.74, x + 0.11, 0.76, '#7a5030')
                with mid.piece(0.8) as d:
                    for half in range(2):
                        c1, c2 = fruit[(k * 2 + half) % len(fruit)]
                        for j in range(4):
                            for i in range(3 - j // 2):
                                d.circ(x + 0.02 + half * 0.06 + i * 0.016 + (j % 2) * 0.008, 0.6 - j * 0.012, 0.012, c1 if (i + j) % 3 else c2)
            cart(near, 0.88, 0.97, 1.6, face=-1)
            with near.piece(1.0) as d:  # a basket stack
                for k in range(3):
                    d.rect(0.06, 0.88 - k * 0.025, 0.2, 0.9 - k * 0.025, '#e05a5a', r=0.006)
                d.rect(0.07, 0.9, 0.19, 0.97, '#e05a5a', r=0.006)
    fg = S.L('fg')
    if v != 0:
        with fg.piece(0.9) as d:  # end of a shelf in the foreground
            x = 0.97 if v == 2 else -0.01
            if v == 1:
                d.rect(-0.04, 0.5, 0.05, 1.04, '#b9b2a4', r=0.006)
                for k in range(4):
                    d.rect(-0.04, 0.6 + k * 0.12, 0.05, 0.61 + k * 0.12, '#8a8f99')
        if v == 1:
            with fg.piece(0.6) as d:
                for k in range(4):
                    goods_row(d, -0.03, 0.045, 0.6 + k * 0.12, 0.09, rng, 1.4)
    return {0: 'supermarket aisle in perspective with a trolley', 1: 'supermarket shelves and a checkout',
            2: 'supermarket produce section and glass-door fridges'}[v]


# ---------------------------------------------------------------- stairwell

def mailboxes(L, x, y, cols=4, rows=3, col='#6a8a6a', s=1.0):
    w, h = 0.035 * s, 0.045 * s
    with L.piece(0.8) as d:
        d.rect(x - 0.006, y - 0.006, x + cols * w + 0.006, y + rows * h + 0.006, shade(col, 0.75), r=0.003)
        for i in range(cols):
            for j in range(rows):
                d.rect(x + i * w + 0.002, y + j * h + 0.003, x + (i + 1) * w - 0.002, y + (j + 1) * h - 0.003, col, r=0.002)
    with L.piece(0.4) as d:
        for i in range(cols):
            for j in range(rows):
                d.rect(x + i * w + 0.008, y + j * h + 0.01, x + (i + 1) * w - 0.008, y + j * h + 0.014, shade(col, 0.55))
                d.circ(x + (i + 1) * w - 0.008, y + (j + 0.6) * h, 0.003, '#d9b65a')


@biome('stairwell', interior=True)
def stairwell(S):
    v = S.variant % 3
    rng = S.rng
    top = ['#ecebe2', '#efe9da', '#e8ece8'][v]
    low = ['#4f7f6f', '#4a6a9a', '#8a6a4a'][v]
    fy = 0.76
    shell(S, wall=top, floor='#b0a294', fy=fy, kind='tiles', skirting=False)
    sky_ = S.L('sky')
    far = S.L('far')
    mid = S.L('mid')
    near = S.L('near')
    with sky_.piece(0.3) as d:  # two-tone painted wall
        d.rect(-0.02, 0.44, 1.02, fy, low)
        d.rect(-0.02, 0.435, 1.02, 0.445, shade(low, 0.7))
    with sky_.piece(0.3) as d:  # small floor tiles pattern
        for k in range(30):
            x = k * 0.036
            d.rect(x, fy + 0.04, x + 0.018, fy + 0.06, shade('#b0a294', 0.85))
            d.rect(x + 0.018, fy + 0.1, x + 0.036, fy + 0.12, '#c9734a')
    if v == 2:  # a landing window with plants on the sill
        window_view(S, sky_, 0.42, 0.12, 0.6, 0.4, view='trees', frame='#f2f0ea', bars=2)
        with far.piece(0.8) as d:
            d.rect(0.4, 0.4, 0.62, 0.415, '#f2f0ea')
        for x in (0.45, 0.51, 0.57):
            plant(far, x, 0.4, 0.55, pot=S.pick(['#c5583e', '#e9a23a', '#f2f0ea']))
    # apartment doors
    dcols = ['#6a3a2a', '#8a2a2a', '#3a2a24', '#7a5030']
    if v == 0:
        doors = [(0.2, True), (0.5, False), (0.8, True)]
    elif v == 1:
        doors = [(0.14, True), (0.42, True)]
    else:
        doors = [(0.12, True), (0.86, False)]
    for k, (x, padded) in enumerate(doors):
        door(far, x, fy, 0.12, 0.46, dcols[k % len(dcols)], frame=shade(top, 0.9), padded=padded)
        with far.piece(0.6) as d:  # door bell and a mat
            d.rect(x + 0.08, fy - 0.27, x + 0.09, fy - 0.255, '#f2f0ea', r=0.002)
            d.circ(x + 0.085, fy - 0.262, 0.003, '#c0443a')
    with mid.piece(0.4) as d:
        for k, (x, _) in enumerate(doors):
            d.rect(x - 0.05, fy + 0.005, x + 0.05, fy + 0.025, ['#8a3a2a', '#3f6f5a', '#5a4a8a'][k % 3], r=0.004)
    if v == 1:  # stairs going up on the right, with a railing
        with mid.piece(1.0) as d:
            x0, y0 = 0.58, fy
            pts = [(x0, y0)]
            for k in range(9):
                x = x0 + k * 0.045
                y = y0 - k * 0.055
                pts += [(x, y - 0.055), (x + 0.045, y - 0.055)]
            pts += [(1.02, y0 - 9 * 0.055), (1.02, y0)]
            d.poly(pts, '#b0a294')
        with mid.piece(1.0) as d:
            d.poly([(0.58, fy), (1.02, fy - 0.6), (1.02, fy - 0.5), (0.62, fy + 0.02)], shade(low, 0.85))
        with mid.piece(0.8) as d:  # railing
            d.line([(0.58, fy - 0.22), (1.02, fy - 0.8)], '#8a4a2a', 0.012)
            for k in range(10):
                x = 0.6 + k * 0.045
                yb = fy - k * 0.055 - 0.05
                d.line([(x, yb), (x, yb - 0.17)], '#3a3a40', 0.004)
        mailboxes(far, 0.27, 0.4, 4, 3, col=['#6a8a6a', '#5a7aa0', '#a07a5a'][v])
    else:
        mailboxes(far, 0.66 if v == 0 else 0.27, 0.32, 4 if v == 0 else 5, 3, col=['#6a8a6a', '#5a7aa0', '#a07a5a'][v])
        with near.piece(1.0) as d:  # the first steps going down / up at the side
            side = 1 if v == 0 else -1
            for k in range(4):
                x = (1.0 if side > 0 else 0.0) - side * (0.06 + k * 0.05)
                d.rect(min(x, x + side * 0.4), 0.84 + k * 0.045, max(x, x + side * 0.4), 0.885 + k * 0.045, shade('#b0a294', 1.0 - 0.04 * k))
        with near.piece(0.9) as d:
            side = 1 if v == 0 else -1
            xr = 1.0 - 0.06 if side > 0 else 0.06
            d.line([(xr, 0.62), (xr - side * 0.2, 0.86)], '#8a4a2a', 0.012)
            for k in range(5):
                xx = xr - side * k * 0.045
                d.line([(xx, 0.62 + k * 0.054), (xx, 0.84 + k * 0.045)], '#3a3a40', 0.004)
    radiator(far, 0.33 if v == 0 else 0.62, 0.43 if v == 0 else 0.74, fy - 0.03, 0.1, col=shade(low, 1.3))
    bulb(S.L('fg'), [0.5, 0.3, 0.5][v] if v != 2 else 0.3, 0.12, s=1.5, on=S.look.time in ('night', 'dusk', 'dawn') or S.look.weather in ('rain', 'clouds'))
    fg = S.L('fg')
    with fg.piece(0.8) as d:  # cables and a junction box on the ceiling line
        d.line([(-0.02, 0.03), (1.02, 0.035)], '#5a5a66', 0.004)
        d.rect(0.88, 0.02, 0.94, 0.06, '#c9c4b8', r=0.003)
    return {0: 'stairwell landing: padded doors, mailboxes, a bare bulb, two-tone paint',
            1: 'stairwell with steps going up and a railing', 2: 'stairwell landing with plants on the window sill'}[v]


# ---------------------------------------------------------------- bathroom

@biome('bathroom', interior=True)
def bathroom(S):
    v = S.variant % 3
    rng = S.rng
    tile = ['#cfe6ee', '#f2efe6', '#d8ecd8'][v]
    shell(S, wall=shade(tile, 1.05), floor=['#8a9aa8', '#b0a294', '#7a9a8a'][v], fy=0.76, kind='tiles', skirting=False)
    sky_ = S.L('sky')
    far = S.L('far')
    mid = S.L('mid')
    near = S.L('near')
    wall_tiles(sky_, -0.02, 0.0 if v != 1 else 0.3, 1.02, 0.76, tile, 0.06, depth=0.3)
    if v == 1:
        with sky_.piece(0.3) as d:
            d.rect(-0.02, 0.29, 1.02, 0.305, '#3f6fa8')
    if v == 2:  # a small high window
        window_view(S, sky_, 0.44, 0.1, 0.56, 0.22, view='clouds', frame='#f6f6f2', bars=1)
    # exposed pipes
    with far.piece(0.8) as d:
        px = [0.32, 0.86, 0.06][v]
        d.line([(px, -0.02), (px, 0.76)], '#b9c0c8', 0.01)
        d.line([(px + 0.025, -0.02), (px + 0.025, 0.6), (px + 0.06, 0.6)], '#c9734a', 0.008)
        for y in (0.2, 0.45):
            d.rect(px - 0.012, y, px + 0.037, y + 0.012, '#9aa4ae', r=0.003)
        d.circ(px + 0.0125, 0.5, 0.012, '#c0443a')
    # bathtub
    bx0, bx1 = [(0.02, 0.3), (0.55, 0.98), (0.6, 0.98)][v]
    with mid.piece(0.6) as d:  # shower curtain rail and curtain
        d.line([(bx0, 0.16), (bx1, 0.16)], '#9aa4ae', 0.006)
        cc = ['#f6c453', '#3f7fbf', '#f28b6b'][v]
        cx1 = bx0 + (bx1 - bx0) * 0.35
        pts = [(bx0, 0.16)] + [(bx0 + (cx1 - bx0) * u, 0.17 + 0.005 * math.sin(u * 30)) for u in np.linspace(0, 1, 12)] + [(cx1 - 0.01, 0.58), (bx0, 0.58)]
        d.poly(pts, cc)
    with mid.piece(0.3) as d:
        for k in range(5):
            xx = bx0 + 0.01 + k * (cx1 - bx0 - 0.02) / 5
            d.line([(xx, 0.18), (xx, 0.57)], shade(cc, 0.85), 0.003)
        d.rect(bx1 - 0.08, 0.3, bx1 - 0.02, 0.33, '#9aa4ae')
        d.ell(bx1 - 0.05, 0.34, 0.025, 0.008, '#b9c0c8')
    with mid.piece(1.0) as d:
        d.rect(bx0, 0.56, bx1, 0.76, '#fbfbf8', r=0.03)
        d.rect(bx0 - 0.005, 0.555, bx1 + 0.005, 0.58, '#f2f2ee', r=0.01)
        if v == 0:
            for x in (bx0 + 0.03, bx1 - 0.03):
                d.ell(x, 0.77, 0.012, 0.01, '#d9b65a')
    with mid.piece(0.7) as d:  # bath foam and a duck
        if v != 1:
            for k in range(6):
                d.circ(bx0 + 0.05 + k * (bx1 - bx0 - 0.1) / 6, 0.555, 0.022, '#ffffff')
        dx = (bx0 + bx1) / 2 + 0.04
        d.ell(dx, 0.54, 0.02, 0.014, '#f6d353')
        d.circ(dx + 0.012, 0.52, 0.01, '#f6d353')
        d.poly([(dx + 0.02, 0.518), (dx + 0.032, 0.522), (dx + 0.02, 0.526)], '#e9822b')
    # sink with a mirror and a shelf
    sx = [0.52, 0.28, 0.32][v]
    with far.piece(0.7) as d:
        d.rect(sx - 0.07, 0.18, sx + 0.07, 0.4, '#c9cfd6', r=0.01)
        d.rect(sx - 0.062, 0.19, sx + 0.062, 0.39, '#d8e6ee', r=0.008)
        d.rect(sx - 0.08, 0.42, sx + 0.08, 0.432, '#f6f6f2', r=0.003)
    with far.piece(0.3) as d:
        d.poly([(sx - 0.04, 0.39), (sx - 0.01, 0.39), (sx + 0.03, 0.19), (sx, 0.19)], (255, 255, 255, 80))
    with far.piece(0.6) as d:
        for k, c in enumerate(('#7fb6e8', '#f28b6b', '#f6f3ea', '#b99be0')):
            d.rect(sx - 0.07 + k * 0.035, 0.38 + 0.04 - (0.03 + 0.008 * (k % 2)), sx - 0.05 + k * 0.035, 0.42, c, r=0.004)
        d.rect(sx + 0.045, 0.39, sx + 0.06, 0.42, '#e05a5a', r=0.003)  # toothbrush cup
        d.line([(sx + 0.05, 0.39), (sx + 0.048, 0.37)], '#3f7fbf', 0.003)
    with mid.piece(1.0) as d:
        d.rect(sx - 0.07, 0.5, sx + 0.07, 0.53, '#fbfbf8', r=0.012)
        d.poly([(sx - 0.03, 0.53), (sx + 0.03, 0.53), (sx + 0.02, 0.76), (sx - 0.02, 0.76)], '#f2f2ee')
        d.line([(sx, 0.5), (sx, 0.46), (sx + 0.025, 0.46)], '#b9c0c8', 0.006)
        d.line([(sx - 0.02, 0.47), (sx + 0.0, 0.47)], '#b9c0c8', 0.004)
        d.line([(sx + 0.02, 0.53), (sx + 0.02, 0.6), (sx + 0.07, 0.6), (sx + 0.07, 0.76)], '#b9c0c8', 0.006)
    # towel rail with towels
    tx = [0.72, 0.1, 0.12][v] if v != 2 else 0.14
    with far.piece(0.8) as d:
        d.line([(tx - 0.05, 0.3), (tx + 0.05, 0.3)], '#9aa4ae', 0.006)
        d.rect(tx - 0.045, 0.3, tx - 0.005, 0.46, ['#e05a5a', '#3f7fbf', '#f6c453'][v], r=0.006)
        d.rect(tx + 0.002, 0.3, tx + 0.04, 0.42, ['#f6f3ea', '#f6f3ea', '#7fc6c0'][v], r=0.006)
    near_ = near
    # washing machine
    wx = [0.86, 0.06, 0.2][v] if v != 2 else 0.16
    if v == 2:
        wx = 0.12
    with near_.piece(1.0) as d:
        d.rect(wx - 0.07, 0.62, wx + 0.07, 0.88, '#f2f4f6', r=0.01)
        d.rect(wx - 0.07, 0.62, wx + 0.07, 0.66, '#dde2e6', r=0.006)
        d.circ(wx, 0.77, 0.075, '#c9cfd6')
        d.circ(wx, 0.77, 0.058, '#7fa8c8')
    with near_.piece(0.5) as d:
        d.circ(wx - 0.015, 0.785, 0.03, '#e05a5a')
        d.circ(wx + 0.02, 0.765, 0.025, '#f6f3ea')
        d.circ(wx + 0.05, 0.64, 0.008, '#3a3a40')
        d.rect(wx - 0.06, 0.632, wx - 0.02, 0.645, '#3a3a40', r=0.002)
    with near_.piece(0.8) as d:  # laundry basket
        lx = wx + (0.15 if v != 0 else -0.15)
        d.poly([(lx - 0.05, 0.8), (lx + 0.05, 0.8), (lx + 0.04, 0.9), (lx - 0.04, 0.9)], '#c9a06a')
        d.ell(lx, 0.79, 0.04, 0.015, '#9fc8e8')
    fg = S.L('fg')
    with fg.piece(0.4) as d:  # a bath mat
        d.rect(0.35, 0.94, 0.62, 1.0, ['#7fc6c0', '#f28b6b', '#b99be0'][v], r=0.015)
    with fg.piece(0.9) as d:
        if v == 1:
            plant(fg, 0.94, 1.0, 1.8)
    return {0: 'bathroom: a tub with a curtain, a sink, a mirror, pipes, a washing machine',
            1: 'white tiled bathroom with a blue band', 2: 'green bathroom with a small high window'}[v]


# ---------------------------------------------------------------- bank

def atm(L, x, y, s=1.0, col='#3f6fa8'):
    with L.piece(1.0) as d:
        d.rect(x - 0.06 * s, y - 0.36 * s, x + 0.06 * s, y, '#c9cfd6', r=0.006)
        d.rect(x - 0.055 * s, y - 0.35 * s, x + 0.055 * s, y - 0.3 * s, col, r=0.004)
        d.rect(x - 0.045 * s, y - 0.28 * s, x + 0.045 * s, y - 0.2 * s, '#2e2e36', r=0.004)
        d.rect(x - 0.05 * s, y - 0.18 * s, x + 0.05 * s, y - 0.12 * s, '#9aa4ae', r=0.004)
    with L.piece(0.4) as d:
        d.rect(x - 0.04 * s, y - 0.27 * s, x + 0.04 * s, y - 0.21 * s, '#7fb6e8', lit=True)
        for i in range(3):
            for j in range(3):
                d.rect(x - 0.03 * s + i * 0.02 * s, y - 0.175 * s + j * 0.017 * s, x - 0.018 * s + i * 0.02 * s, y - 0.163 * s + j * 0.017 * s, '#e6eaee')
        d.rect(x + 0.01 * s, y - 0.11 * s, x + 0.045 * s, y - 0.1 * s, '#1e1e26')
    L.glow_rect(x - 0.04 * s, y - 0.27 * s, x + 0.04 * s, y - 0.21 * s)


def queue_posts(L, x0, x1, y, col='#2f4f7a'):
    with L.piece(0.9) as d:
        n = max(1, int((x1 - x0) / 0.12))
        xs = [x0 + (x1 - x0) * k / n for k in range(n + 1)]
        d.line([(xs[0], y - 0.1), (xs[-1], y - 0.1)], col, 0.008)
        for x in xs:
            d.rect(x - 0.004, y - 0.12, x + 0.004, y, '#b9c0c8')
            d.ell(x, y, 0.018, 0.005, '#9aa4ae')


@biome('bank', interior=True)
def bank(S):
    v = S.variant % 3
    rng = S.rng
    wall = ['#efe9dc', '#e2e8ee', '#e9e2d6'][v]
    accent = ['#2f6f5a', '#2f4f7a', '#8a3a3a'][v]
    shell(S, wall=wall, floor=['#d6cfc2', '#c6ccd4', '#cfc6b8'][v], fy=0.74, kind='tiles', ceiling=0.05)
    sky_ = S.L('sky')
    far = S.L('far')
    mid = S.L('mid')
    near = S.L('near')
    with sky_.piece(0.3) as d:  # marble-like panels
        for k in range(10):
            x = k * 0.1
            d.rect(x + 0.002, 0.08, x + 0.098, 0.74, shade(wall, 1.03 if k % 2 else 0.98))
            d.line([(x + 0.02, 0.2), (x + 0.05, 0.35), (x + 0.04, 0.5)], shade(wall, 0.92), 0.002)
    with sky_.piece(0.3) as d:
        d.rect(-0.02, 0.08, 1.02, 0.11, accent)
    ceiling_panels(far, 0.05, 4, lit=True)
    if v == 1:
        window_view(S, sky_, 0.04, 0.16, 0.26, 0.5, view='city', frame='#c9ced4', bars=2)
    # a screen with an abstract graph, and the queue display (coloured lamps)
    gx = [0.2, 0.42, 0.78][v]
    screen_chart(far, gx, 0.28, 0.18, 0.13, col=accent)
    with far.piece(0.7) as d:  # an abstract emblem-free wall art: three circles
        ax = [0.78, 0.82, 0.2][v]
        for k in range(3):
            d.circ(ax - 0.04 + k * 0.04, 0.27, 0.035, [accent, shade(accent, 1.5), '#d9b65a'][k])
    # the counter with glass and teller windows
    cx0, cx1 = [(0.36, 0.98), (0.3, 0.98), (0.02, 0.62)][v]
    with mid.piece(1.0) as d:
        d.rect(cx0, 0.5, cx1, 0.525, '#f2f0ea', r=0.004)
        d.rect(cx0 + 0.005, 0.525, cx1 - 0.005, 0.74, accent, r=0.004)
        n = int((cx1 - cx0) / 0.2)
        for k in range(n):
            x = cx0 + 0.02 + k * (cx1 - cx0) / n
            d.rect(x, 0.55, x + (cx1 - cx0) / n - 0.04, 0.72, shade(accent, 1.15), r=0.006)
    with mid.piece(0.3) as d:
        d.rect(cx0, 0.3, cx1, 0.5, (225, 240, 250, 80))
        n = int((cx1 - cx0) / 0.2)
        for k in range(n + 1):
            x = cx0 + k * (cx1 - cx0) / n
            d.rect(x - 0.003, 0.3, x + 0.003, 0.5, '#b9c0c8')
    with mid.piece(0.7) as d:  # tellers' monitors and number lamps above each window
        n = int((cx1 - cx0) / 0.2)
        for k in range(n):
            x = cx0 + (k + 0.5) * (cx1 - cx0) / n
            d.rect(x - 0.035, 0.42, x + 0.01, 0.5, '#2e2e36', r=0.004)
            d.rect(x + 0.03, 0.49, x + 0.07, 0.5, '#f6f3ea')
            d.circ(x, 0.24, 0.014, ['#6af0a0', '#f6c453', '#6af0a0', '#f05a4a'][k % 4], lit=True)
    # waiting sofa, ticket machine, ATM
    sx = [0.17, 0.16, 0.8][v]
    ax_ = [0.1, 0.9, 0.95][v]
    if v == 0:
        atm(S.L('far'), 0.06, 0.74, 1.0, accent)
    near_ = near
    sofa(near_, sx if v != 0 else 0.2, 0.96, 0.3, col=['#c9a868', '#8a5a5a', '#3f6f8a'][v], s=1.2)
    if v != 0:
        atm(near_, ax_, 0.96, 1.6, accent)
    with near_.piece(1.0) as d:  # ticket machine
        tx = [0.86, 0.32, 0.66][v]
        d.rect(tx - 0.035, 0.66, tx + 0.035, 0.96, '#e6eaee', r=0.008)
        d.rect(tx - 0.028, 0.68, tx + 0.028, 0.74, accent, lit=True)
        d.rect(tx - 0.015, 0.77, tx + 0.015, 0.775, '#3a3a40')
        d.rect(tx - 0.006, 0.775, tx + 0.006, 0.79, '#fbfbf8')
    queue_posts(S.L('mid'), [0.42, 0.4, 0.14][v], [0.7, 0.66, 0.42][v], 0.86, accent)
    fg = S.L('fg')
    plant(fg, 0.5 if False else (0.04 if v == 2 else 0.97), 1.0, 2.4, pot='#2e2e36')
    return {0: 'bank branch: teller windows behind glass, an ATM, a ticket machine, a waiting sofa',
            1: 'blue bank hall with a window and queue posts', 2: 'bank branch with a red counter on the left'}[v]


# ---------------------------------------------------------------- museum

def vase(d, x, y, s, col, pat):
    d.ell(x, y - 0.06 * s, 0.035 * s, 0.05 * s, col)
    d.rect(x - 0.015 * s, y - 0.13 * s, x + 0.015 * s, y - 0.09 * s, col)
    d.ell(x, y - 0.13 * s, 0.022 * s, 0.008 * s, shade(col, 0.8))
    d.rect(x - 0.02 * s, y - 0.015 * s, x + 0.02 * s, y, shade(col, 0.85))
    d.rect(x - 0.03 * s, y - 0.07 * s, x + 0.03 * s, y - 0.06 * s, pat)
    for k in range(4):
        d.circ(x - 0.018 * s + k * 0.012 * s, y - 0.045 * s, 0.004 * s, pat)


def statue(d, x, y, s, col):
    """An abstract figure: a smooth standing form, a round head."""
    d.poly([(x - 0.02 * s, y), (x + 0.022 * s, y), (x + 0.03 * s, y - 0.1 * s), (x + 0.018 * s, y - 0.2 * s), (x - 0.018 * s, y - 0.2 * s), (x - 0.03 * s, y - 0.1 * s)], col)
    d.circ(x, y - 0.225 * s, 0.026 * s, col)
    d.ell(x + 0.035 * s, y - 0.15 * s, 0.01 * s, 0.045 * s, shade(col, 0.95))


def dino(L, x, y, s=1.0, col='#ece4d0'):
    """A dinosaur skeleton on a stand: a spine arc, ribs, a long tail, a skull."""
    kx = 0.55  # x offsets are in width units: squeeze them so the beast keeps its proportions
    with L.piece(0.8) as d:
        d.rect(x - 0.005, y - 0.16 * s, x + 0.005, y, '#5a5a66')
        d.rect(x + 0.15 * s * kx, y - 0.12 * s, x + 0.16 * s, y, '#5a5a66')
        d.rect(x - 0.14 * s * kx, y - 0.01, x + 0.25 * s, y, '#5a5a66')
    with L.piece(0.6) as d:
        spine = [(x - 0.25 * s * kx + 0.5 * s * kx * u, y - 0.18 * s - 0.1 * s * math.sin(u * math.pi) + 0.04 * s * u) for u in np.linspace(0, 1, 30)]
        d.line(spine, col, 0.007 * s)
        tail = [(x + 0.25 * s * kx + 0.2 * s * kx * u, y - 0.12 * s + 0.08 * s * u) for u in np.linspace(0, 1, 10)]
        d.line([spine[-1]] + tail, col, 0.005 * s)
        for k in range(8):
            u = 0.25 + k * 0.06
            sx, sy = spine[int(u * 29)]
            d.line([(sx, sy), (sx - 0.005, sy + 0.07 * s * math.sin(u * math.pi))], col, 0.004 * s)
        hx_, hy = spine[0]
        d.line([(hx_, hy), (hx_ - 0.04 * s * kx, hy - 0.06 * s)], col, 0.006 * s)
        d.ell(hx_ - 0.07 * s * kx, hy - 0.07 * s, 0.045 * s, 0.025 * s, col)
        d.circ(hx_ - 0.07 * s * kx, hy - 0.075 * s, 0.006 * s, '#5a5a66')
        for lx in (0.05, 0.2):
            px, py = spine[int(lx / 0.5 * 29)]
            d.line([(px, py), (px - 0.01 * s, y - 0.08 * s), (px + 0.01 * s, y - 0.01)], col, 0.006 * s)


@biome('museum', interior=True)
def museum(S):
    v = S.variant % 3
    rng = S.rng
    wall = ['#e9e2d4', '#3f4a5a', '#dfe6e0'][v]
    fy = 0.74
    shell(S, wall=wall, floor=['#b98a5e', '#8a7a6a', '#c9c2b4'][v], fy=fy, kind='planks' if v != 2 else 'tiles', ceiling=0.05)
    sky_ = S.L('sky')
    far = S.L('far')
    mid = S.L('mid')
    near = S.L('near')
    # an arch to the next hall
    ax_ = [0.5, 0.86, 0.14][v]
    with sky_.piece(0.4) as d:
        d.rect(ax_ - 0.08, 0.3, ax_ + 0.08, fy, shade(wall, 0.85))
        d.pie(ax_, 0.3, 0.145, 180, 360, shade(wall, 0.85))
        d.rect(ax_ - 0.06, 0.32, ax_ + 0.06, fy, shade(wall, 0.92))
        d.pie(ax_, 0.32, 0.11, 180, 360, shade(wall, 0.92))
    with sky_.piece(0.3) as d:  # a far painting and a far plinth through the arch
        d.rect(ax_ - 0.03, 0.4, ax_ + 0.03, 0.48, '#c9734a')
        d.rect(ax_ - 0.012, 0.62, ax_ + 0.012, fy, '#f2efe8')
    # spotlights on a track
    with far.piece(0.6) as d:
        d.rect(-0.02, 0.07, 1.02, 0.08, '#2e2e36')
        for k in range(6):
            x = 0.08 + k * 0.17
            d.poly([(x - 0.012, 0.08), (x + 0.012, 0.08), (x + 0.02, 0.11), (x - 0.004, 0.115)], '#2e2e36')
    for k in range(6):
        far.glow_circ(0.08 + k * 0.17 + 0.01, 0.12, 0.03)
    # framed paintings on the wall, skipping the arch
    spots = [x for x in (0.1, 0.27, 0.73, 0.9, 0.5) if abs(x - ax_) > 0.16]
    for k, x in enumerate(spots[:4]):
        w, h = (0.13, 0.18) if k % 2 == 0 else (0.15, 0.12)
        frame_art(far, x, 0.32, w, h, rng, frame='#c9a24a' if v != 1 else '#d9b65a', bg='#f6f0e0' if v != 1 else '#2e2e36')
        with far.piece(0.4) as d:  # a blank caption plate
            d.rect(x + w / 2 - 0.03, 0.43, x + w / 2 - 0.005, 0.445, '#f6f3ea')
    # exhibits on plinths in the mid layer
    if v == 0:
        plinth(mid, 0.18, fy + 0.01, 0.09, 0.2)
        with mid.piece(0.9) as d:
            vase(d, 0.18, fy - 0.2 + 0.01, 1.4, '#c9734a', '#2e2e36')
        plinth(mid, 0.82, fy + 0.01, 0.1, 0.16)
        with mid.piece(0.9) as d:
            statue(d, 0.82, fy - 0.15, 1.3, '#f2efe8')
        with mid.piece(0.6) as d:  # a glass case with small objects
            d.rect(0.62, 0.52, 0.72, 0.74, '#8a5a3a', r=0.003)
        with mid.piece(0.3) as d:
            d.rect(0.62, 0.4, 0.72, 0.52, (220, 238, 248, 110))
            d.circ(0.65, 0.5, 0.015, '#d9b65a')
            d.ell(0.69, 0.505, 0.018, 0.01, '#3f7f8a')
    elif v == 1:
        dino(mid, 0.45, fy + 0.0, 1.5)
        plinth(mid, 0.1, fy + 0.01, 0.09, 0.22, col='#d0ccc4')
        with mid.piece(0.9) as d:
            statue(d, 0.1, fy - 0.21, 1.2, '#c9a24a')
    else:
        for x, kind in ((0.4, 'vase'), (0.6, 'statue'), (0.8, 'vase')):
            plinth(mid, x, fy + 0.01, 0.08, 0.18)
            with mid.piece(0.9) as d:
                if kind == 'vase':
                    vase(d, x, fy - 0.17, 1.2, S.pick(['#3f6f8a', '#c9734a', '#d9b65a']), '#f6f3ea')
                else:
                    statue(d, x, fy - 0.17, 1.1, '#9aa4ae')
    rope_barrier(near, [0.05, 0.22, 0.3][v], [0.4, 0.7, 0.95][v], 0.84 if v != 1 else 0.82)
    with near.piece(1.0) as d:  # a bench for visitors
        bx = [0.75, 0.16, 0.12][v]
        if v == 1:
            bx = 0.86
        d.rect(bx - 0.1, 0.88, bx + 0.1, 0.905, '#2e2e36', r=0.006)
        for x in (bx - 0.08, bx + 0.08):
            d.rect(x - 0.006, 0.905, x + 0.006, 0.97, '#2e2e36')
    fg = S.L('fg')
    with fg.piece(0.9) as d:  # the attendant's chair in the corner
        x = 0.96 if v != 2 else 0.04
        d.rect(x - 0.04, 0.82, x + 0.04, 0.85, '#8a3a3a', r=0.006)
        d.rect(x - 0.04, 0.68, x - 0.025, 0.85, '#8a3a3a', r=0.006)
        d.rect(x - 0.035, 0.85, x - 0.028, 1.02, '#5a3a2a')
        d.rect(x + 0.028, 0.85, x + 0.035, 1.02, '#5a3a2a')
    return {0: 'museum hall: paintings, a vase and a statue on plinths, a rope barrier',
            1: 'dark museum hall with a dinosaur skeleton', 2: 'museum gallery with a row of plinths'}[v]
