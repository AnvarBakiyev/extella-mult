"""Central Asian settings (puppet-plates-more): a steppe aul, a yurt interior, a mountain gorge, a city at dusk under the
range, a business-centre lobby, a home kitchen with a dastarkhan, a public service hall, a university auditorium, a dacha,
a winter bus stop, a railway station, the Caspian shore and a taxi at night.

Drawn with care: real objects of daily life (shanyrak, kerege, uyk poles, tus kiiz, syrmak, sandyk chests, piala bowls,
nan and baursak), ornament only as simple geometric felt shapes (diamonds, ram's-horn curls). No text, digits, logos,
flags or state symbols anywhere; no real landmarks."""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from plates import AR, W, H, shade, mixc, hx, to255, sky, weather_fx, Look, Layer
from scenes import biome, winter, poplar, flat
from props import (hills, mountains, round_tree, pine, birch, bush, grass_tufts, flowers, rock, house, block, tower, yurt,
                   horse, car, bus, lamp_post, bench, fence, train, ridge_fn, patches, boat)
from rooms import shell, ceiling_panels, plant, chair, clock, lamp_pendant, WOOD

IN6 = [('day', 'clear', 'summer', 'felt'), ('night', 'clear', 'summer', 'felt'), ('golden', 'clear', 'autumn', 'warm'),
       ('day', 'rain', 'autumn', 'felt'), ('dusk', 'clear', 'winter', 'felt'), ('dawn', 'clouds', 'spring', 'pastel')]
OUT9 = [('day', 'clear', 'summer', 'felt'), ('golden', 'clear', 'summer', 'felt'), ('night', 'clear', 'summer', 'felt'),
        ('dawn', 'clouds', 'spring', 'pastel'), ('dusk', 'clear', 'autumn', 'warm'), ('day', 'clouds', 'autumn', 'felt'),
        ('day', 'rain', 'summer', 'muted'), ('day', 'snow', 'winter', 'cool'), ('dawn', 'fog', 'summer', 'felt')]

LOOKS = {
    'aul': (3, OUT9),
    'yurt_interior': (3, [('day', 'clear', 'summer', 'felt'), ('night', 'clear', 'summer', 'felt'), ('golden', 'clear', 'autumn', 'warm'),
                          ('dusk', 'clear', 'winter', 'felt'), ('dawn', 'clouds', 'spring', 'pastel'), ('day', 'snow', 'winter', 'felt')]),
    'gorge': (3, [('day', 'clear', 'summer', 'felt'), ('golden', 'clear', 'autumn', 'warm'), ('night', 'clear', 'summer', 'felt'),
                  ('dawn', 'clouds', 'spring', 'pastel'), ('day', 'clouds', 'autumn', 'felt'), ('dusk', 'clear', 'summer', 'felt'),
                  ('day', 'rain', 'summer', 'muted'), ('day', 'snow', 'winter', 'cool'), ('dawn', 'fog', 'summer', 'felt')]),
    'city_dusk': (3, [('dusk', 'clear', 'summer', 'felt'), ('night', 'clear', 'summer', 'felt'), ('golden', 'clear', 'autumn', 'warm'),
                      ('night', 'snow', 'winter', 'cool'), ('dusk', 'clouds', 'autumn', 'felt'), ('night', 'clear', 'spring', 'vivid'),
                      ('dawn', 'clear', 'spring', 'pastel'), ('night', 'rain', 'autumn', 'felt'), ('day', 'clear', 'summer', 'felt')]),
    'business_lobby': (3, IN6),
    'dastarkhan_kitchen': (3, IN6),
    'service_center': (3, IN6),
    'auditorium': (3, IN6),
    'dacha': (3, [('day', 'clear', 'summer', 'felt'), ('golden', 'clear', 'summer', 'felt'), ('night', 'clear', 'summer', 'felt'),
                  ('dawn', 'clouds', 'spring', 'pastel'), ('dusk', 'clear', 'autumn', 'warm'), ('day', 'clouds', 'autumn', 'felt'),
                  ('day', 'rain', 'summer', 'muted'), ('day', 'snow', 'winter', 'cool'), ('day', 'clear', 'spring', 'vivid')]),
    'bus_stop': (3, [('day', 'snow', 'winter', 'cool'), ('night', 'snow', 'winter', 'felt'), ('dusk', 'clear', 'winter', 'felt'),
                     ('day', 'clear', 'winter', 'felt'), ('golden', 'clear', 'winter', 'warm'), ('dawn', 'fog', 'winter', 'felt'),
                     ('day', 'rain', 'autumn', 'muted'), ('night', 'clear', 'autumn', 'felt')]),
    'station': (3, OUT9),
    'caspian': (3, [('day', 'clear', 'summer', 'felt'), ('golden', 'clear', 'summer', 'felt'), ('night', 'clear', 'summer', 'felt'),
                    ('dawn', 'clouds', 'spring', 'pastel'), ('dusk', 'clear', 'autumn', 'warm'), ('day', 'clouds', 'autumn', 'felt'),
                    ('day', 'rain', 'summer', 'muted'), ('day', 'clear', 'winter', 'cool'), ('dawn', 'fog', 'summer', 'felt')]),
    'taxi': (3, [('night', 'clear', 'summer', 'felt'), ('day', 'clear', 'summer', 'felt'), ('dusk', 'clear', 'autumn', 'felt'),
                 ('night', 'rain', 'autumn', 'felt'), ('golden', 'clear', 'summer', 'warm'), ('night', 'snow', 'winter', 'cool')]),
}

GOLD = '#f2c14e'
RED = '#b8332e'


# ---------------------------------------------------------------- shared helpers

def diamonds(d, x0, x1, y, h, col, col2=None, gap=1.15):
    """A row of felt diamonds centred on y, h tall (an ornament band)."""
    hw = h / 2 / AR
    x = x0 + hw
    k = 0
    while x < x1 - hw * 0.5:
        c = col if (col2 is None or k % 2 == 0) else col2
        d.poly([(x - hw, y), (x, y - h / 2), (x + hw, y), (x, y + h / 2)], c)
        x += hw * 2 * gap
        k += 1


def spiral(cx, cy, r, a0, turns, sign=1, n=24):
    pts = []
    for i in range(n + 1):
        t = i / n
        a = a0 + sign * t * turns * 2 * math.pi
        rr = r * (1 - 0.75 * t)
        pts.append((cx + math.cos(a) * rr / AR, cy + math.sin(a) * rr))
    return pts


def horns(d, cx, cy, r, col, w=None):
    """A ram's-horn (koshkar muiz) motif: a short stem and two curls turning outwards."""
    w = w or r * 0.28
    d.line([(cx, cy + r * 0.9), (cx, cy)], col, w)
    for sgn in (-1, 1):
        c2x = cx + sgn * r * 0.55 / AR
        pts = [(cx, cy)] + spiral(c2x, cy - r * 0.05, r * 0.55, math.pi if sgn > 0 else 0, 0.85, sign=sgn)
        d.line(pts, col, w)


def medallion(d, cx, cy, r, bg, fg, fg2=None):
    """A felt medallion: a diamond with four horn curls around it."""
    d.poly([(cx - r / AR, cy), (cx, cy - r), (cx + r / AR, cy), (cx, cy + r)], bg)
    d.poly([(cx - r * 0.45 / AR, cy), (cx, cy - r * 0.45), (cx + r * 0.45 / AR, cy), (cx, cy + r * 0.45)], fg2 or fg)
    for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        d.line(spiral(cx + sx * r * 0.62 / AR, cy + sy * r * 0.62, r * 0.32, 0 if sx > 0 else math.pi, 0.8, sign=sx * sy), fg, r * 0.12)


def outside(S, L, box, draw=None, mask=None, haze=0.2, stars=False):
    """Paint a view of the outdoors (graded for the time of day, not the room light) into box of layer L.
    draw(layer) adds things to the view; mask='ellipse' clips it to the inscribed ellipse."""
    x0, y0, x1, y1 = box
    out = Look(S.look.time, S.look.weather, S.look.season, S.look.palette, interior=False)
    t = Layer(S, 'far')
    t.look, t.haze, t.shadow = out, haze, False
    c0, c1, c2 = out.sky_cols()
    y = np.clip((np.linspace(0, 1, H, dtype=np.float32) - y0) / max(y1 - y0, 1e-3), 0, 1)[:, None]
    t1 = np.clip(y / 0.6, 0, 1)
    t2 = np.clip((y - 0.6) / 0.4, 0, 1)
    col = c0 * (1 - t1[..., None]) + c1 * t1[..., None]
    col = col * (1 - t2[..., None]) + c2 * t2[..., None]
    col = np.broadcast_to(col, (H, W, 3))
    t.base = Image.fromarray((np.clip(col, 0, 1) * 255).astype(np.uint8), 'RGB').convert('RGBA')
    if stars and out.night and out.weather in ('clear', 'clouds'):
        fd = t.flat()
        for _ in range(int(400 * (x1 - x0) * (y1 - y0)) + 6):
            fd.circ(x0 + (x1 - x0) * S.rng.random(), y0 + (y1 - y0) * S.rng.random() * 0.8, 0.0015 + 0.002 * S.rng.random(), '#fff6dc', lit=True)
    if draw:
        draw(t)
    img = t.finish()
    b = (int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H))
    crop = img.crop(b)
    m = Image.new('L', crop.size, 0)
    md = ImageDraw.Draw(m)
    if mask == 'ellipse':
        md.ellipse([0, 0, crop.size[0] - 1, crop.size[1] - 1], fill=255)
    else:
        md.rectangle([0, 0, crop.size[0], crop.size[1]], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(1.2))
    L.base.paste(crop.convert('RGBA'), b[:2], m)


def piala(d, x, y, s, col='#f6f3ea', band='#2f6fb0'):
    """A tea bowl seen from the side: x centre, y bottom."""
    k = s / AR
    d.poly([(x - 0.02 * k, y - 0.024 * s), (x + 0.02 * k, y - 0.024 * s), (x + 0.012 * k, y), (x - 0.012 * k, y)], col)
    d.rect(x - 0.019 * k, y - 0.021 * s, x + 0.019 * k, y - 0.016 * s, band)


def teapot(d, x, y, s, col='#f6f3ea', band='#2f6fb0'):
    k = s / AR
    d.ell(x, y - 0.03 * s, 0.035 * s, 0.03 * s, col)
    d.rect(x - 0.03 * k, y - 0.006 * s, x + 0.03 * k, y, shade(col, 0.9))
    d.line([(x + 0.03 * k, y - 0.03 * s), (x + 0.06 * k, y - 0.055 * s)], col, 0.008 * s)
    d.line([(x - 0.03 * k, y - 0.045 * s), (x - 0.05 * k, y - 0.035 * s), (x - 0.03 * k, y - 0.015 * s)], col, 0.006 * s)
    d.ell(x, y - 0.06 * s, 0.014 * s, 0.006 * s, shade(col, 0.92))
    d.circ(x, y - 0.067 * s, 0.005 * s, band)
    d.rect(x - 0.033 * k, y - 0.035 * s, x + 0.033 * k, y - 0.028 * s, band)


def nan_bread(d, x, y, rx, ry):
    """A round flat nan, seen at a slant: a golden rim, a paler middle with a dotted stamp."""
    d.ell(x, y, rx, ry, '#d9953e')
    d.ell(x, y, rx * 0.68, ry * 0.62, '#efc888')
    for k in range(7):
        a = k * 2 * math.pi / 7
        d.circ(x + math.cos(a) * rx * 0.35 / AR, y + math.sin(a) * ry * 0.32, ry * 0.07, '#c9853a')
    d.circ(x, y, ry * 0.08, '#c9853a')


def baursak_plate(d, x, y, s, plate='#f6f3ea'):
    d.ell(x, y, 0.06 * s, 0.018 * s, plate)
    rng = np.random.default_rng(int(x * 1000 + y * 77))
    for row in range(3):
        for k in range(5 - row * 2 + (1 if row == 0 else 0)):
            bx = x + (k - (4 - row * 2 + (1 if row == 0 else 0)) / 2) * 0.016 * s / AR * 1.7
            by = y - 0.006 * s - row * 0.012 * s + rng.random() * 0.003
            d.rect(bx - 0.009 * s / AR * 1.7, by - 0.011 * s, bx + 0.009 * s / AR * 1.7, by + 0.004 * s, '#d9a04e', r=0.005 * s)


def fruit_bowl(d, x, y, s, rng, bowl='#f6f3ea'):
    cols = ['#e0403a', '#f6d353', '#7cc45e', '#f08a2e', '#8a3a6a', '#e0403a']
    for row in range(2):
        for k in range(4 - row):
            d.circ(x + (k - (3 - row) / 2) * 0.022 * s / AR * 1.6, y - 0.022 * s - row * 0.018 * s, 0.014 * s, cols[int(rng.integers(len(cols)))])
    d.poly([(x - 0.05 * s / AR * 1.6, y - 0.022 * s), (x + 0.05 * s / AR * 1.6, y - 0.022 * s), (x + 0.03 * s / AR * 1.6, y), (x - 0.03 * s / AR * 1.6, y)], bowl)


def sweets(d, x, y, s, rng):
    d.ell(x, y, 0.04 * s, 0.012 * s, '#e9c46a')
    for k in range(6):
        d.ell(x + (rng.random() - 0.5) * 0.05 * s / AR * 1.6, y - 0.006 * s - rng.random() * 0.008 * s, 0.008 * s, 0.005 * s,
              ['#e05a5a', '#3f7fbf', '#f6d353', '#7a4a2a', '#f28bb0'][k % 5])


def dastarkhan_top(L, x0, x1, y0, y1, rng, s=1.0, cloth='#f6f0e0', band=RED):
    """A table top covered with a cloth, seen from slightly above, laid for tea: pialas, a teapot, nan, baursak,
    fruit, sweets and small dishes."""
    with L.piece(0.6) as d:
        d.poly([(x0 + 0.02, y0), (x1 - 0.02, y0), (x1, y1), (x0, y1)], cloth)
        d.rect(x0, y1, x1, y1 + 0.03 * s, shade(cloth, 0.92))
        diamonds(d, x0 + 0.01, x1 - 0.01, y1 + 0.016 * s, 0.018 * s, band)
    cx = (x0 + x1) / 2
    ym = (y0 + y1) / 2
    with L.piece(0.6) as d:
        nan_bread(d, cx - (x1 - x0) * 0.18, ym, 0.05 * s, 0.018 * s)
        nan_bread(d, cx + (x1 - x0) * 0.2, ym + 0.006, 0.045 * s, 0.016 * s)
        for k in range(3):  # small dishes: salad, kurt, raisins
            xx = x0 + (x1 - x0) * (0.12 + 0.37 * k)
            d.ell(xx, y0 + 0.012, 0.03 * s, 0.009 * s, '#f6f3ea')
            d.ell(xx, y0 + 0.009, 0.022 * s, 0.006 * s, ['#e05a5a', '#f3efe0', '#8a3a3a'][k])
    with L.piece(0.8) as d:
        baursak_plate(d, cx, ym + 0.006, s)
        fruit_bowl(d, cx - (x1 - x0) * 0.36, y1 - 0.002, s * 0.9, rng)
        sweets(d, cx + (x1 - x0) * 0.38, y1 - 0.01, s * 0.9, rng)
        teapot(d, cx + (x1 - x0) * 0.08, y0 + 0.02 + 0.01 * s, s * 0.8)
        for k in range(4):
            xx = x0 + (x1 - x0) * (0.08 + 0.28 * k) + 0.01
            piala(d, xx, y1 + 0.004 - (0.01 if k % 2 else 0), s * 0.8)


def smoke(L, x, y, s, rng, n=7):
    with L.piece(0.3) as d:
        for k in range(n):
            t = k / n
            d.circ(x + 0.02 * math.sin(k * 1.3) * s + 0.01 * t * s, y - 0.03 * k * s, (0.01 + 0.012 * t) * s, (235, 235, 240, int(150 * (1 - t))))


def gulls(L, rng, n, y0, y1, s=1.0):
    with L.piece(0.3) as d:
        for _ in range(n):
            x, y = 0.05 + 0.9 * rng.random(), y0 + (y1 - y0) * rng.random()
            w = (0.012 + 0.01 * rng.random()) * s
            d.line([(x - w, y - w * 0.3), (x - w * 0.45, y - w * 0.6), (x, y)], '#f6f6f2', 0.004 * s)
            d.line([(x, y), (x + w * 0.45, y - w * 0.6), (x + w, y - w * 0.3)], '#f6f6f2', 0.004 * s)


# ---------------------------------------------------------------- aul

def white_house(L, x, y, s, rng, col='#f4f0e6', roof='#7f8f9a', door='#3f7fbf'):
    """A small whitewashed village house with a low pitched tin roof and blue window frames."""
    w, h = 0.075 * s, 0.085 * s
    with L.piece(0.9) as d:
        d.rect(x - w, y - h, x + w, y, col)
        d.rect(x - w - 0.004, y - 0.012 * s, x + w + 0.004, y, shade(col, 0.85))
        d.rect(x + w * 0.5, y - h - 0.06 * s, x + w * 0.7, y - h - 0.01, '#a89a88')
    with L.piece(0.9) as d:
        d.poly([(x - w - 0.01 * s, y - h), (x + w + 0.01 * s, y - h), (x + w * 0.6, y - h - 0.045 * s), (x - w * 0.6, y - h - 0.045 * s)], roof)
        if L.look.season == 'winter':
            d.poly([(x - w - 0.008 * s, y - h - 0.004), (x + w + 0.008 * s, y - h - 0.004), (x + w * 0.6, y - h - 0.045 * s), (x - w * 0.6, y - h - 0.045 * s)], '#f8fafc')
    with L.piece(0.6) as d:
        for dx in (-0.045, 0.02):
            d.rect(x + dx * s - 0.004 * s, y - h * 0.78 - 0.004 * s, x + dx * s + 0.03 * s / AR * 1.7 + 0.004 * s, y - h * 0.35 + 0.004 * s, door)
            d.window(x + dx * s, y - h * 0.78, x + dx * s + 0.03 * s / AR * 1.7, y - h * 0.35, rng=rng)
        d.rect(x + w * 0.55, y - 0.065 * s, x + w * 0.9, y, door, r=0.003)
    return x + w * 0.6, y - h - 0.06 * s


def corral(L, x0, x1, y, s, col='#9a7a52'):
    """A wooden pen: posts and three rails, seen from the front."""
    with L.piece(0.7) as d:
        x = x0
        while x <= x1 + 1e-6:
            d.rect(x - 0.004 * s, y - 0.075 * s, x + 0.004 * s, y + 0.004, shade(col, 0.85), r=0.002)
            x += 0.05 * s
        for k in range(3):
            yy = y - (0.02 + 0.024 * k) * s
            d.line([(x0 - 0.008, yy), (x1 + 0.008, yy + 0.003 * math.sin(k))], col, 0.006 * s)


def tether(L, x, y, s):
    with L.piece(0.7) as d:
        d.rect(x - 0.005 * s, y - 0.12 * s, x + 0.005 * s, y, '#7a5a3a', r=0.002)
        d.line([(x - 0.012 * s, y - 0.11 * s), (x + 0.012 * s, y - 0.11 * s)], '#7a5a3a', 0.006 * s)


def samovar(L, x, y, s):
    k = s / AR
    with L.piece(0.9) as d:
        d.rect(x - 0.06 * k, y - 0.05 * s, x + 0.06 * k, y - 0.04 * s, '#8a5a3a', r=0.003)  # a low table
        for u in (-0.05, 0.05):
            d.rect(x + u * k - 0.005 * k, y - 0.04 * s, x + u * k + 0.005 * k, y, '#6a4a2a')
        d.rect(x - 0.022 * k, y - 0.11 * s, x + 0.022 * k, y - 0.05 * s, '#d9a441', r=0.012 * s)
        d.rect(x - 0.014 * k, y - 0.125 * s, x + 0.014 * k, y - 0.105 * s, '#c08a2e', r=0.004)
        d.rect(x - 0.004 * k, y - 0.15 * s, x + 0.004 * k, y - 0.12 * s, '#8a8f99')
        d.line([(x + 0.022 * k, y - 0.07 * s), (x + 0.04 * k, y - 0.07 * s)], '#c08a2e', 0.005 * s)
        teapot(d, x, y - 0.153 * s, s * 0.45, col='#2f6fb0', band='#f6f3ea')
        piala(d, x - 0.045 * k, y - 0.05 * s, s * 0.7)
        piala(d, x + 0.045 * k, y - 0.05 * s, s * 0.7)


@biome('aul')
def aul(S):
    """A steppe aul: yurts with ornament bands, small whitewashed houses, a pen, a tethered horse, a samovar."""
    v = S.variant % 3
    rng = S.rng
    hz = 0.58
    sky(S, horizon=hz)
    far = S.L('far')
    if v == 1:
        mountains(far, hz + 0.02, hz - 0.22, seed=S.seed, col='#9aa3cf', snowline=0.5)
    else:
        hills(far, hz + 0.01, 0.07, '#b4b6cc' if not winter(S) else '#dfe5ec', seed=S.seed, freqs=(0.8, 2.2, 5.0))
    mid = S.L('mid')
    hills(mid, hz + 0.04, 0.03, 'steppe2', seed=S.seed + 5, freqs=(0.9, 2.4, 5.0))
    f = hills(mid, hz + 0.1, 0.04, 'steppe', seed=S.seed + 1, freqs=(0.7, 1.9, 4.0))
    patches(mid, f, 0.85, 8, rng, ['steppe2'])
    bands = [RED, '#2f6fb0', RED, '#3d8a5a']
    if v == 0:
        houses = [0.12, 0.84]
        yurts = [(0.33, 1.05), (0.52, 0.9), (0.66, 1.1)]
    elif v == 1:
        houses = [0.9]
        yurts = [(0.1, 0.95), (0.28, 1.15), (0.47, 0.85), (0.63, 1.0)]
    else:
        houses = [0.18, 0.4, 0.78]
        yurts = [(0.6, 1.05), (0.95, 0.9)]
    for x in houses:
        cx, cy = white_house(mid, x, f(x) + 0.06, 1.0 + 0.15 * S.r(), rng, col=S.pick(['#f4f0e6', '#efe6d4', '#e9eef2']),
                             roof=S.pick(['#7f8f9a', '#4f7fa8', '#8a5a4a']), door=S.pick(['#3f7fbf', '#2f8f8a', '#3f7fbf']))
        if winter(S) or S.time in ('dawn', 'dusk', 'night') or v == 2:
            smoke(mid, cx, cy, 1.2, rng)
    for i, (x, s) in enumerate(yurts):
        yurt(mid, x, f(x) + 0.06, s, band=bands[i % 4], door=S.pick(['#d9822b', '#c0443a', '#2f6fb0']))
    near = S.L('near')
    g = hills(near, 0.82, 0.035, 'steppe', seed=S.seed + 2, freqs=(0.6, 1.4, 3.3))
    patches(near, g, 1.0, 6, rng, ['steppe2'])
    with near.piece(0.4) as d:  # a trodden path
        pts = [(0.42 + 0.12 * u + 0.03 * math.sin(u * 4), g(0.45) + 0.01 + (1.02 - g(0.45)) * u) for u in np.linspace(0, 1, 16)]
        d.line(pts, '#c8a77a' if not winter(S) else '#d8dde6', 0.035)
    if v in (0, 2):
        corral(near, 0.03, 0.27, g(0.15) + 0.07, 1.2)
        horse(near, 0.1, g(0.1) + 0.06, 1.6, col='#8a5a3a', graze=True)
        horse(near, 0.2, g(0.2) + 0.065, 1.5, col='#f0ece4', face=-1)
        tether(near, 0.82, g(0.82) + 0.09, 1.3)
        horse(near, 0.75, g(0.75) + 0.1, 1.9, col=S.pick(['#5a3a2a', '#c9955c']), face=1)
    else:
        samovar(near, 0.8, g(0.8) + 0.1, 1.5)
        tether(near, 0.16, g(0.16) + 0.09, 1.3)
        horse(near, 0.1, g(0.1) + 0.1, 1.9, col='#3a2a24', face=1)
    if v == 0:
        samovar(near, 0.62, g(0.62) + 0.06, 1.1)
    fg = S.L('fg')
    grass_tufts(fg, 0.93, 1.0, 26, rng, col='steppe2', col2='steppe', s=2.2)
    if S.season == 'spring':
        flowers(fg, 0.9, 0.99, 18, rng, s=1.8)
    weather_fx(S, ground=hz + 0.08)
    return {0: 'steppe aul: yurts, whitewashed houses, a pen with horses, a samovar', 1: 'aul of yurts under far mountains, a horse at the post',
            2: 'aul with whitewashed houses and smoking chimneys, yurts and a pen'}[v]


# ---------------------------------------------------------------- yurt interior

@biome('yurt_interior', interior=True)
def yurt_interior(S):
    """Inside a yurt: kerege lattice wall, red uyk poles converging on the shanyrak (sky through it), tus kiiz hangings,
    syrmak rugs, a stack of chests and folded blankets, a low round table laid for tea."""
    v = S.variant % 3
    rng = S.rng
    pole = ['#c0583a', '#b8452e', '#c9773a'][v]
    felt_in = ['#efe2c4', '#eadcc0', '#f2e6cc'][v]
    hang = [('#7a1f2a', GOLD, '#2f6fb0'), ('#1f3a6a', GOLD, '#c0443a'), ('#2f5a3a', '#f6d353', '#c0443a')][v]

    def top(x):  # the top of the lattice wall: farther (centre) appears lower
        return 0.37 - 0.13 * ((x - 0.5) / 0.6) ** 2

    def bot(x):  # the foot of the wall: farther appears higher
        return 0.74 + 0.11 * ((x - 0.5) / 0.6) ** 2

    xs = np.linspace(-0.03, 1.03, 80)
    shell(S, wall=felt_in, floor='#8a5a3a', fy=0.9, kind='carpet', skirting=False)
    L = S.L('sky')
    with L.piece(0.3) as d:  # roof felt above the wall
        d.poly([(x, top(x)) for x in xs] + [(1.03, -0.02), (-0.03, -0.02)], shade(felt_in, 0.93))
    with L.piece(0.3) as d:  # floor of felt and rugs
        d.poly([(x, bot(x)) for x in xs] + [(1.03, 1.03), (-0.03, 1.03)], '#a8794a')
    with L.piece(0.4) as d:  # a big syrmak rug
        rx0, rx1 = 0.12, 0.88
        d.poly([(rx0 + 0.05, 0.79), (rx1 - 0.05, 0.79), (rx1 + 0.06, 1.03), (rx0 - 0.06, 1.03)], hang[0])
        d.poly([(rx0 + 0.07, 0.805), (rx1 - 0.07, 0.805), (rx1 + 0.03, 1.03), (rx0 - 0.03, 1.03)], shade(hang[0], 1.25))
        diamonds(d, rx0 + 0.06, rx1 - 0.06, 0.797, 0.012, hang[1])
        for k in range(5):
            medallion(d, 0.22 + k * 0.14, 0.9, 0.04, hang[0], hang[1], hang[2])
    # shanyrak opening shows the sky
    scx, scy, srx, sry = 0.5, 0.03, 0.17, 0.075
    outside(S, L, (scx - srx / AR, scy - sry, scx + srx / AR, scy + sry), mask='ellipse', stars=True,
            draw=(lambda t: _clouds_in(t, scx, scy, rng)) if S.weather in ('clouds', 'snow') else None)
    far = S.L('far')
    with far.piece(0.6) as d:  # kerege lattice: diagonal crisscross between the top and the foot
        n = 46
        for k in range(-6, n + 6):
            x = k / n
            for sgn in (-1, 1):
                pts = []
                for u in np.linspace(0, 1, 10):
                    xx = x + sgn * u * 0.09
                    pts.append((xx, top(xx) + (bot(xx) - top(xx)) * u))
                d.line(pts, '#b07a46', 0.0035)
        d.line([(x, top(x)) for x in xs], shade(pole, 0.85), 0.012)
    with far.piece(0.8) as d:  # uyk poles from the wall top to the shanyrak ring
        for k in range(28):
            th = -math.pi / 2 + math.pi * (k + 0.5) / 28
            xb = 0.5 + 0.62 * math.sin(th)
            a = math.pi + math.pi * (k + 0.5) / 28
            xr, yr = scx + math.cos(a) * srx * 1.12 / AR, scy - math.sin(a) * sry * 1.12
            d.line([(xr, yr), (xb, top(xb) + 0.004)], pole, 0.007)
    with far.piece(0.8) as d:  # the shanyrak ring and its crossed arches
        d.ell(scx, scy, srx * 1.18, sry * 1.25, '#9a6a3a')
        d.ell(scx, scy, srx, sry, (0, 0, 0, 0))
    _shanyrak_hole(far, scx, scy, srx, sry)
    with far.piece(0.6) as d:
        for sgn in (-1, 1):
            for k in (-1, 0, 1):
                pts = []
                for u in np.linspace(-1, 1, 14):
                    xx = scx + u * srx / AR * 0.98
                    pts.append((xx + sgn * 0, scy + k * sry * 0.45 - (1 - u * u) * 0.02))
                d.line(pts, '#b07a46', 0.006)
            for k in (-1, 0, 1):
                pts = [(scx + k * srx * 0.42 / AR, scy - sry), (scx + k * srx * 0.42 / AR + 0.002, scy + sry * 0.95)]
                d.line(pts, '#b07a46', 0.006)
    # tus kiiz hangings on the wall
    for x0, x1 in ((0.04, 0.27), (0.73, 0.96)):
        y0 = top((x0 + x1) / 2) + 0.03
        y1 = bot((x0 + x1) / 2) - 0.04
        with far.piece(0.8) as d:
            d.rect(x0, y0, x1, y1, hang[0], r=0.004)
            d.rect(x0 + 0.012, y0 + 0.02, x1 - 0.012, y1 - 0.02, shade(hang[0], 1.18), r=0.004)
        with far.piece(0.5) as d:
            diamonds(d, x0 + 0.005, x1 - 0.005, y0 + 0.01, 0.014, hang[1])
            diamonds(d, x0 + 0.005, x1 - 0.005, y1 - 0.01, 0.014, hang[1])
            cx = (x0 + x1) / 2
            medallion(d, cx, (y0 + y1) / 2, 0.075, hang[2], hang[1], hang[0])
            for yy in (y0 + 0.07, y1 - 0.07):
                horns(d, cx, yy, 0.025, hang[1])
            for k in range(9):  # tassels
                tx = x0 + (x1 - x0) * (k + 0.5) / 9
                d.line([(tx, y1), (tx, y1 + 0.025)], [hang[1], '#c0443a', '#2f6fb0'][k % 3], 0.004)
    with far.piece(0.8) as d:  # a dombra hanging on the wall
        dx, dy = 0.32, 0.47
        d.line([(dx, dy), (dx + 0.06, dy - 0.15)], '#8a5a2a', 0.008)
        d.ell(dx - 0.008, dy + 0.035, 0.03, 0.045, '#b07a46')
        d.ell(dx - 0.008, dy + 0.035, 0.008, 0.008, '#5a3a20')
        d.rect(dx + 0.055, dy - 0.165, dx + 0.07, dy - 0.14, '#6a4a2a', r=0.003)
    mid = S.L('mid')
    # the tor: chests with folded blankets (zhuk) at the back, opposite the door
    cx0, cx1 = 0.4, 0.6
    base = bot(0.5) + 0.005
    with mid.piece(0.9) as d:
        for i, (a, b) in enumerate(((cx0 - 0.04, cx0 + 0.07), (cx1 - 0.07, cx1 + 0.04))):
            d.rect(a, base - 0.1, b, base, '#8a4a2a', r=0.004)
            d.rect(a, base - 0.1, b, base - 0.092, '#d9b46a')
            d.rect(a, base - 0.008, b, base, '#d9b46a')
            for xx in np.linspace(a + 0.015, b - 0.015, 3):
                d.poly([(xx - 0.01, base - 0.05), (xx, base - 0.075), (xx + 0.01, base - 0.05), (xx, base - 0.025)], '#e6e2d6')
        d.rect(cx0 + 0.07, base - 0.08, cx1 - 0.07, base, '#6a3a2a', r=0.003)
    with mid.piece(0.9) as d:  # folded blankets
        y = base - 0.1
        cols = ['#c0443a', '#2f6fb0', '#e9b443', '#3d8a5a', '#8a3a6a', '#f2e6cc', '#c0443a', '#2f6fb0']
        for k in range(7):
            w = 0.11 - 0.004 * k
            hh = 0.024
            d.rect(0.5 - w, y - hh, 0.5 + w, y, cols[(k + v) % len(cols)], r=0.01)
            y -= hh - 0.002
        d.rect(0.5 - 0.07, y - 0.03, 0.5 + 0.07, y + 0.002, '#f6f3ea', r=0.012)
    with mid.piece(0.5) as d:
        y = base - 0.1
        for k in range(7):
            w = 0.11 - 0.004 * k
            diamonds(d, 0.5 - w + 0.01, 0.5 + w - 0.01, y - 0.012, 0.008, '#f6f3ea' if k % 2 else GOLD, gap=2.0)
            y -= 0.022
    near = S.L('near')
    # the low round table laid for tea
    tx, ty = 0.5, 0.86
    with near.piece(0.9) as d:
        for u in (-0.12, 0.12):
            d.rect(tx + u - 0.008, ty, tx + u + 0.008, ty + 0.05, '#6a3a2a')
        d.ell(tx, ty + 0.012, 0.42, 0.03, '#7a4a2a')
    with near.piece(0.7) as d:
        d.ell(tx, ty, 0.42, 0.055, '#f6f0e0')
        d.ell(tx, ty, 0.4, 0.05, shade('#f6f0e0', 0.96))
    with near.piece(0.6) as d:
        nan_bread(d, tx - 0.09, ty - 0.004, 0.06, 0.018)
        nan_bread(d, tx + 0.11, ty + 0.012, 0.05, 0.015)
        d.ell(tx + 0.18, ty - 0.02, 0.03, 0.008, '#f6f3ea')
        d.ell(tx + 0.18, ty - 0.022, 0.022, 0.005, '#f3efe0')
    with near.piece(0.8) as d:
        baursak_plate(d, tx + 0.01, ty - 0.012, 1.2)
        fruit_bowl(d, tx - 0.2, ty + 0.01, 1.1, rng)
        teapot(d, tx + 0.21, ty + 0.002, 0.9)
        sweets(d, tx - 0.03, ty + 0.03, 0.9, rng)
        for xx in (-0.3, -0.12, 0.08, 0.3):
            piala(d, tx + xx * 0.9, ty + 0.035 + (0.006 if xx > 0 else 0), 0.95)
    for sx in (-1, 1):  # floor cushions (korpe) left and right
        with near.piece(0.9) as d:
            x = 0.5 + sx * 0.4
            for k in range(2):
                d.rect(x - 0.11, 0.93 - k * 0.03, x + 0.11, 0.97 - k * 0.03, [hang[2], hang[0]][k], r=0.014)
        with near.piece(0.5) as d:
            diamonds(d, x - 0.1, x + 0.1, 0.92, 0.012, hang[1])
    fg = S.L('fg')
    with fg.piece(0.8) as d:  # a woven band (baskur) with tassels across the top
        d.rect(-0.02, -0.02, 1.02, 0.035, hang[0])
        diamonds(d, -0.01, 1.01, 0.012, 0.026, hang[1], '#f6f3ea')
        for k in range(0, 40, 3):
            x = 0.012 + k * 0.025
            d.line([(x, 0.035), (x, 0.08 + 0.02 * (k % 2))], [hang[1], '#c0443a', '#2f6fb0'][k % 3], 0.005)
            d.circ(x, 0.085 + 0.02 * (k % 2), 0.008, [hang[1], '#c0443a', '#2f6fb0'][k % 3])
    if S.look.lit_share > 0.2 or S.time in ('night', 'dusk'):
        lamp_pendant(fg, 0.5, 0.2, 1.2, col='#c08a2e', cord=0.1)
    return {0: 'inside a yurt: shanyrak, kerege lattice, wine-red tus kiiz, a low table laid for tea',
            1: 'yurt interior in blue and gold, chests and folded blankets, tea table',
            2: 'yurt interior in green and gold, rugs, a dombra on the wall, tea table'}[v]


def _clouds_in(t, cx, cy, rng):
    from plates import cloud
    with t.piece(0.6) as d:
        cloud(d, cx - 0.03, cy + 0.01, 0.5, '#f4f4f0' if t.look.time != 'night' else '#5a6890')


def _shanyrak_hole(L, cx, cy, rx, ry):
    """Cut the inside of the shanyrak ring back out of the far layer, so the sky shows through."""
    m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).ellipse([cx * W - rx * H, cy * H - ry * H, cx * W + rx * H, cy * H + ry * H], fill=255)
    m = np.asarray(m.filter(ImageFilter.GaussianBlur(1.5)), np.float32) / 255
    a = np.asarray(L.base, np.float32)
    a = a * (1 - m[..., None])
    L.base = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')


# ---------------------------------------------------------------- gorge

def _wall(d, edge, side, col, strata, y0, y1, rng):
    """A canyon wall from the frame edge to edge(y): side -1 for the left wall, +1 for the right."""
    ys = np.linspace(y0, y1, 60)
    outer = -0.03 if side < 0 else 1.03
    pts = [(edge(y), y) for y in ys]
    d.poly(pts + [(outer, y1), (outer, y0)], col)


@biome('gorge')
def gorge(S):
    """A mountain gorge: ochre and red rock walls, a river at the bottom, spruces on the ledges, a footbridge."""
    v = S.variant % 3
    rng = S.rng
    sky(S, horizon=0.42, cloud_y=(0.04, 0.2))
    far = S.L('far')
    mountains(far, 0.5, 0.12, seed=S.seed, col='#8f9ccc', snowline=0.6)
    rockc = [('#c96a4a', '#d98a5a', '#b8573e'), ('#c9955a', '#ddb070', '#b07a46'), ('#b85a4a', '#cf7b5a', '#9a4a3e')][v]
    f1 = ridge_fn(S.seed + 3, 0, 1, freqs=(2.1, 5.3, 13.0))
    f2 = ridge_fn(S.seed + 4, 0, 1, freqs=(1.7, 4.9, 12.0))
    with far.piece(0.8) as d:  # far canyon walls, hazy
        d.poly([(0.3 + 0.05 * f1(y * 3), y) for y in np.linspace(0.3, 0.7, 30)] + [(-0.03, 0.7), (-0.03, 0.34)], mixc(rockc[1], '#b4b8d0', 0.2))
        d.poly([(0.7 - 0.05 * f2(y * 3), y) for y in np.linspace(0.32, 0.7, 30)] + [(1.03, 0.7), (1.03, 0.36)], mixc(rockc[1], '#b4b8d0', 0.2))
    mid = S.L('mid')

    def le(y):  # left mid wall edge: ledges and bulges
        return 0.22 + 0.1 * (y - 0.18) + 0.05 * f1(y * 4) + 0.025 * math.floor(y * 9 % 2) + (0.05 if y > 0.6 else 0) * (y - 0.6) * 4

    def re(y):
        return 0.78 - 0.08 * (y - 0.2) - 0.05 * f2(y * 4) - 0.025 * math.floor((y * 9 + 0.5) % 2) - (0.05 if y > 0.6 else 0) * (y - 0.6) * 4
    with mid.piece(1.0) as d:
        _wall(d, le, -1, rockc[0], None, 0.18, 0.78, rng)
        _wall(d, re, 1, rockc[2], None, 0.22, 0.78, rng)
    with mid.piece(0.5) as d:  # the lit and the shaded faces near the edges
        ys = np.linspace(0.18, 0.78, 60)
        d.poly([(le(y), y) for y in ys] + [(le(y) - 0.05, y) for y in ys[::-1]], shade(rockc[0], 0.82))
        ys = np.linspace(0.22, 0.78, 60)
        d.poly([(re(y), y) for y in ys] + [(re(y) + 0.06, y) for y in ys[::-1]], shade(rockc[2], 1.15))
    with mid.piece(0.6) as d:  # strata bands
        for k in range(10):
            y = 0.24 + k * 0.055
            d.line([(-0.03, y + 0.01 * math.sin(k)), (le(y) - 0.012, y)], shade(rockc[0], 0.86 if k % 2 else 1.1), 0.008 + 0.004 * (k % 3))
            d.line([(re(y + 0.02) + 0.012, y + 0.02), (1.03, y + 0.02 + 0.01 * math.cos(k))], shade(rockc[2], 0.86 if k % 2 else 1.1), 0.008 + 0.004 * (k % 3))
    for y in (0.2, 0.33, 0.47):  # spruces on the ledges
        for k in range(2):
            pine(mid, le(y) - 0.04 - 0.05 * k, y + 0.01, 0.5 + 0.15 * S.r(), depth=0.8)
            pine(mid, re(y + 0.03) + 0.04 + 0.05 * k, y + 0.04, 0.5 + 0.15 * S.r(), depth=0.8)
    if v == 1:  # a hanging footbridge across the gorge
        yb = 0.5
        with mid.piece(0.7) as d:
            xa, xb = le(yb) - 0.01, re(yb) + 0.01
            deck = [(xa + (xb - xa) * u, yb + 0.05 * math.sin(math.pi * u)) for u in np.linspace(0, 1, 30)]
            d.line(deck, '#8a5a3a', 0.012)
            d.line([(x, y - 0.045) for x, y in deck], '#5a4a3a', 0.003)
            for k, (x, y) in enumerate(deck[::2]):
                d.line([(x, y), (x, y - 0.045)], '#5a4a3a', 0.002)
    near = S.L('near')
    water_c = '#4f8fca' if not winter(S) else '#9ab8d0'
    with near.piece(0.5) as d:  # the river winding out of the gorge
        pts_l = [(0.42 + 0.06 * math.sin(u * 3) - 0.3 * u ** 2, 0.7 + 0.32 * u) for u in np.linspace(0, 1, 30)]
        pts_r = [(0.58 + 0.06 * math.sin(u * 3) + 0.02 + 0.08 * u, 0.7 + 0.32 * u) for u in np.linspace(0, 1, 30)]
        d.poly(pts_l + pts_r[::-1], water_c)
    with near.piece(0.3) as d:
        for k in range(14):
            u = rng.random()
            xc = 0.5 + 0.06 * math.sin(u * 3) - 0.1 * u ** 2
            d.ell(xc + (rng.random() - 0.5) * 0.12 * (1 + u), 0.72 + 0.28 * u, 0.02 + 0.03 * u, 0.003 + 0.002 * u, '#d6ecf8')
    with near.piece(0.9) as d:  # banks: left a flat pebbly beach (room for characters), right boulders
        d.poly([(-0.03, 0.7)] + [(0.42 + 0.06 * math.sin(u * 3) - 0.3 * u ** 2 - 0.01, 0.7 + 0.32 * u) for u in np.linspace(0, 1, 30)] + [(-0.03, 1.03)],
               '#b8a890' if not winter(S) else '#eef3f8')
        d.poly([(1.03, 0.7)] + [(0.6 + 0.06 * math.sin(u * 3) + 0.08 * u + 0.01, 0.7 + 0.32 * u) for u in np.linspace(0, 1, 30)] + [(1.03, 1.03)],
               '#a8987e' if not winter(S) else '#e6ecf2')
    patches(near, lambda x: 0.72, 1.0, 14, rng, ['#9a8a74', '#c8b89e', '#8a8070'], rx=(0.01, 0.03), ry=(0.004, 0.008), depth=0.5)
    for k in range(4):
        rock(near, 0.66 + 0.09 * k + S.r(-0.02, 0.02), 0.82 + 0.04 * (k % 2), 1.4 + 0.5 * S.r(), col=S.pick(['#9a958f', '#a88a7a', '#8a8580']))
    rock(near, 0.52, 0.8, 0.9, col='#8a8580')
    fg = S.L('fg')
    pine(fg, 0.04, 1.05, 2.4, depth=1.0)
    if v == 2:
        pine(fg, 0.97, 1.05, 2.0, depth=1.0)
    rock(fg, 0.9, 1.02, 3.0, col='#8f8a84')
    grass_tufts(fg, 0.95, 1.0, 12, rng, s=2.0)
    weather_fx(S, ground=0.72)
    return {0: 'red-rock mountain gorge with a river and spruces', 1: 'ochre gorge with a hanging footbridge over the river',
            2: 'deep red gorge, snowy peak in the gap, a pebbly bank'}[v]


# ---------------------------------------------------------------- city at dusk

@biome('city_dusk')
def city_dusk(S):
    """A big city under a snowy range, seen from a hillside or a rooftop: lit windows, poplar avenues, chains of
    street lights. Abstract buildings only, no landmarks."""
    v = S.variant % 3
    rng = S.rng
    sky(S, horizon=0.48, cloud_y=(0.03, 0.16))
    far = S.L('far')
    mountains(far, 0.5, 0.06, seed=S.seed + 11, col='#8d9bd0', snowline=0.55)
    hills(far, 0.53, 0.05, mixc('#7f8fb8', '#6f7f6a', 0.3), seed=S.seed + 2)
    x = -0.02
    while x < 1.02:  # far rows of the city
        w = 0.02 + 0.03 * rng.random()
        h = 0.02 + 0.05 * rng.random() + (0.06 if rng.random() < 0.12 else 0)
        tower(far, x, x + w, 0.6, h, S.pick(['#b9c3d6', '#c9cfd9', '#aab6c9']), rng, fh=0.012)
        x += w + 0.001
    mid = S.L('mid')
    base = 0.72
    items = []
    x = -0.02
    while x < 1.02:
        w = 0.035 + 0.045 * rng.random()
        tall = rng.random() < 0.2
        h = 0.18 + 0.12 * rng.random() if tall else 0.06 + 0.08 * rng.random()
        items.append((x, w, h, tall))
        x += w + 0.002
    for x, w, h, tall in sorted(items, key=lambda t: -t[2]):
        if tall:
            tower(mid, x, x + w, base, h, S.pick(['#c9d6e2', '#d8dee6', '#b9cbd9', '#e0d6c8']), rng, top=S.pick(['flat', 'step', 'slant', 'round']), fh=0.022)
        else:
            block(mid, x, x + w, base, max(2, int(h / 0.026)), S.pick(['#e9dcc6', '#d8c9b4', '#f0e2c8', '#c9d3dc']), rng, fh=0.026, balcony=False)
    for k in range(18):  # poplars between the blocks
        poplar(mid, rng.random(), base + 0.005, 0.55 + 0.2 * rng.random())
    lit = S.look.lit_share > 0.2
    with mid.piece(0.3) as d:  # avenues: chains of lights running towards the mountains
        for a in range(3):
            x0 = 0.15 + a * 0.33 + S.r(-0.05, 0.05)
            for k in range(16):
                u = k / 15
                xx = x0 + (u - 0.5) * 0.5
                yy = base - 0.005 - 0.002 * k
                if lit:
                    d.circ(xx, yy, 0.0035, '#ffe08f', lit=True)
                    mid.glow_circ(xx, yy, 0.008)
                else:
                    d.circ(xx, yy, 0.002, '#6a6a72')
    near = S.L('near')
    if v == 1:  # a rooftop with a parapet, a water tank, vents
        with near.piece(0.8) as d:
            d.rect(-0.03, 0.8, 1.03, 1.03, '#8a8a92')
            d.rect(-0.03, 0.78, 1.03, 0.81, '#a8a8b0')
            d.rect(0.04, 0.6, 0.2, 0.8, '#9a8a7a', r=0.004)
            d.ell(0.12, 0.6, 0.1, 0.02, '#8a7a6a')
            for x in (0.02, 0.22):
                d.line([(x + 0.02, 0.8), (x, 0.86)], '#5a5a62', 0.006)
            d.rect(0.78, 0.7, 0.9, 0.8, '#b0b4ba', r=0.006)
            d.rect(0.8, 0.72, 0.88, 0.78, '#8a8f99')
            for k in range(5):
                d.rect(0.81, 0.725 + k * 0.011, 0.87, 0.73 + k * 0.011, '#6a6f79')
        with near.piece(0.6) as d:
            for k in range(40):
                d.rect(k * 0.026, 0.76, k * 0.026 + 0.005, 0.8, '#5a5a62')
            d.rect(-0.03, 0.755, 1.03, 0.765, '#5a5a62')
        lamp_post(near, 0.94, 0.95, 1.4)
    else:  # a hillside park with apple trees or poplars, a bench and a lamp
        g = hills(near, 0.82, 0.06, 'grass', seed=S.seed)
        if v == 2:
            for x in (0.06, 0.2, 0.84, 0.96):
                round_tree(near, x, g(x) + 0.05, 1.1 + 0.3 * S.r(), rng=rng)
            with near.piece(0.5) as d:  # apples
                if S.season in ('summer', 'autumn'):
                    for x in (0.06, 0.2, 0.84, 0.96):
                        for k in range(6):
                            d.circ(x + S.r(-0.04, 0.04), g(x) + 0.05 - (0.25 + 0.08 * S.r()) * 1.2, 0.007, '#d8342c')
        else:
            for x in (0.04, 0.12, 0.88, 0.97):
                poplar(near, x, g(x) + 0.05, 1.5 + 0.3 * S.r())
        with near.piece(0.6) as d:
            d.line([(0.25, 1.02), (0.4, g(0.4) + 0.05), (0.7, g(0.7) + 0.06), (1.03, g(0.95) + 0.1)], '#c9b89a' if not winter(S) else '#d8dde6', 0.03)
        bench(near, 0.72, g(0.72) + 0.1, 1.4)
        lamp_post(near, 0.83, g(0.83) + 0.11, 1.4)
    fg = S.L('fg')
    if v == 1:
        with fg.piece(0.9) as d:  # railing in front
            d.rect(-0.03, 0.9, 1.03, 0.915, '#4a4a58')
            for k in range(0, 41, 4):
                d.rect(k * 0.025, 0.9, k * 0.025 + 0.006, 1.03, '#4a4a58')
        plant(fg, 0.06, 1.0, 2.0)
    else:
        bush(fg, 0.04, 1.03, 2.3)
        bush(fg, 0.95, 1.04, 2.0)
        grass_tufts(fg, 0.95, 1.0, 14, rng, s=2.0)
    weather_fx(S, ground=0.75)
    return {0: 'city under a snowy range at dusk, seen from a hillside with poplars', 1: 'city lights and mountains from a rooftop',
            2: 'city panorama from an apple-tree hillside'}[v]


# ---------------------------------------------------------------- business lobby

def _range_view(t, y, col='#9aa6d0'):
    mountains(t, y, y - 0.3, seed=7, col=col, snowline=0.5)


@biome('business_lobby', interior=True)
def business_lobby(S):
    """A business-centre lobby: a glass wall onto the mountains, a curved reception desk, turnstiles, lifts, tall
    plants, a big abstract artwork."""
    v = S.variant % 3
    rng = S.rng
    wall = ['#e9e4dc', '#dfe3e6', '#ece2d2'][v]
    shell(S, wall=wall, floor='#d6d2cc', fy=0.74, kind='tiles', ceiling=0.05)
    sky_ = S.L('sky')
    gx0, gx1, gy0, gy1 = 0.25, 0.75, 0.08, 0.66

    def view(t):
        _range_view(t, 0.52)
        x = gx0
        while x < gx1:
            w = 0.02 + 0.03 * rng.random()
            tower(t, x, x + w, gy1, 0.06 + 0.12 * rng.random(), S.pick(['#c9d6e2', '#d8dee6', '#e0d6c8']), rng, fh=0.018)
            x += w + 0.002
        for k in range(10):
            poplar(t, gx0 + (gx1 - gx0) * rng.random(), gy1, 0.5)
    outside(S, sky_, (gx0, gy0, gx1, gy1), draw=view, stars=True)
    with sky_.piece(0.2) as d:  # the floor reflects the glass wall
        d.rect(gx0, 0.75, gx1, 0.9, (255, 255, 255, 40))
    far = S.L('far')
    with far.piece(0.6) as d:  # mullions
        for k in range(6):
            x = gx0 + (gx1 - gx0) * k / 5
            d.rect(x - 0.004, gy0, x + 0.004, gy1, '#5a5f68')
        d.rect(gx0 - 0.004, gy0 - 0.006, gx1 + 0.004, gy0 + 0.004, '#5a5f68')
        d.rect(gx0 - 0.004, 0.36, gx1 + 0.004, 0.367, '#5a5f68')
        d.rect(gx0 - 0.004, gy1 - 0.004, gx1 + 0.004, gy1 + 0.006, '#5a5f68')
    with far.piece(0.5) as d:  # downlights
        for k in range(9):
            x = 0.06 + k * 0.11
            d.ell(x, 0.05, 0.012, 0.005, '#fff6dc', lit=True)
            far.glow_circ(x, 0.06, 0.02)
    # an abstract artwork on the left wall, lifts on the right
    art = [('#e9a23a', '#2f6fb0', '#c0443a'), ('#3d8a8a', '#f6c453', '#e05a5a'), ('#8a3a6a', '#f2c14e', '#3f7fbf')][v]
    with far.piece(0.8) as d:
        d.rect(0.03, 0.14, 0.21, 0.5, '#f8f6f0', r=0.004)
    with far.piece(0.6) as d:
        d.circ(0.1, 0.27, 0.08, art[0])
        d.rect(0.12, 0.3, 0.2, 0.48, art[1])
        d.pie(0.14, 0.24, 0.07, 180, 360, art[2])
        d.line([(0.05, 0.46), (0.19, 0.18)], '#2e2e36', 0.004)
    with far.piece(0.8) as d:
        for k in range(2):
            x = 0.8 + k * 0.095
            d.rect(x, 0.22, x + 0.08, 0.74, '#9aa0a8', r=0.003)
            d.rect(x + 0.006, 0.24, x + 0.074, 0.74, '#c9ced4')
            d.rect(x + 0.039, 0.24, x + 0.041, 0.74, '#9aa0a8')
    with far.piece(0.4) as d:
        for k in range(2):
            x = 0.84 + k * 0.095
            d.poly([(x - 0.008, 0.2), (x, 0.19), (x + 0.008, 0.2)], '#7fd0ff', lit=True)
            d.poly([(x - 0.008, 0.205), (x, 0.215), (x + 0.008, 0.205)], '#7fd0ff', lit=True)
    mid = S.L('mid')
    desk = ['#f4f1ea', '#2e3440', '#b98a5e'][v]
    with mid.piece(1.0) as d:  # curved reception desk
        pts = [(0.27 + 0.4 * u, 0.6 + 0.025 * math.sin(math.pi * u)) for u in np.linspace(0, 1, 30)]
        d.poly(pts + [(0.67, 0.76), (0.27, 0.76)], desk)
        d.poly([(x, y + 0.03) for x, y in pts] + [(0.67, 0.665), (0.27, 0.665)], shade(desk, 0.85) if v != 1 else '#c9a46a')
    with mid.piece(0.6) as d:
        for x in (0.36, 0.56):
            d.rect(x - 0.022, 0.55, x + 0.022, 0.595, '#2e2e36', r=0.003)
            d.rect(x - 0.018, 0.555, x + 0.018, 0.588, '#7fb6e8', lit=True)
        d.ell(0.47, 0.6, 0.02, 0.005, '#f6f3ea')
        for k in range(5):
            d.circ(0.465 + k * 0.004, 0.585 - (k % 2) * 0.006, 0.008, '#e05a5a' if k % 2 else '#f6d353')
    near = S.L('near')
    with near.piece(1.0) as d:  # turnstiles with glass gates, on the right
        for k in range(3):
            x = 0.7 + k * 0.08
            d.rect(x, 0.72, x + 0.022, 0.88, '#b9bec6', r=0.006)
            d.rect(x + 0.004, 0.735, x + 0.018, 0.75, '#6fd08a', lit=True)
    with near.piece(0.3) as d:
        for k in range(3):
            x = 0.722 + k * 0.08
            d.rect(x, 0.76, x + 0.055, 0.84, (210, 235, 250, 110), r=0.006)
    fg = S.L('fg')
    for x, s in ((0.06, 2.6), (0.95, 2.4)):  # tall plants in planters
        with fg.piece(0.9) as d:
            for k in range(9):
                a = -math.pi / 2 + (k - 4) * 0.28
                ln = 0.28 * s / 2.5
                ex, ey = x + math.cos(a) * ln / AR, 0.8 + math.sin(a) * ln
                d.ell((x + ex) / 2, (0.8 + ey) / 2, 0.016 * s / 2.5 * 1.5, ln / 2, '#4f9e48' if k % 2 else '#68b456')
        with fg.piece(0.9) as d:
            d.rect(x - 0.04, 0.82, x + 0.04, 1.03, '#3a3a44' if v != 2 else '#c9b8a0', r=0.01)
    return {0: 'business-centre lobby with a glass wall onto the mountains', 1: 'dark-desk lobby, lifts and turnstiles',
            2: 'warm wood lobby with an abstract artwork and tall plants'}[v]


# ---------------------------------------------------------------- dastarkhan kitchen

def _yard_view(t, rng):
    block(t, 0.3, 0.62, 0.42, 9, '#d6d2c8', rng, fh=0.03, balcony=True)
    block(t, 0.63, 0.75, 0.42, 7, '#cfd6dc', rng, fh=0.03, balcony=False)
    with t.piece(0.6) as d:
        d.rect(0.2, 0.41, 0.8, 0.5, 'grass2')
    for k in range(4):
        poplar(t, 0.33 + k * 0.09, 0.44, 0.5)


@biome('dastarkhan_kitchen', interior=True)
def dastarkhan_kitchen(S):
    """An ordinary apartment kitchen with the table laid as a dastarkhan: nan, baursak, tea, fruit, sweets."""
    v = S.variant % 3
    rng = S.rng
    wall = ['#f2e6c8', '#dfeae6', '#f1dccd'][v]
    cab = ['#f6f3ea', '#8fb8b0', '#d9a878'][v]
    shell(S, wall=wall, floor='#b9a48a', fy=0.72, kind='tiles')
    sky_ = S.L('sky')
    wx0, wy0, wx1, wy1 = 0.36, 0.12, 0.62, 0.44
    outside(S, sky_, (wx0, wy0, wx1, wy1), draw=lambda t: _yard_view(t, rng), stars=True)
    far = S.L('far')
    with far.piece(0.8) as d:  # window frame and a light curtain
        t = 0.012
        d.rect(wx0 - t, wy0 - t, wx1 + t, wy0 + 0.004, '#f6f3ea')
        d.rect(wx0 - t, wy1 - 0.004, wx1 + t, wy1 + 0.016, '#f6f3ea')
        d.rect(wx0 - t, wy0 - t, wx0 + 0.004, wy1 + t, '#f6f3ea')
        d.rect(wx1 - 0.004, wy0 - t, wx1 + t, wy1 + t, '#f6f3ea')
        d.rect((wx0 + wx1) / 2 - 0.004, wy0, (wx0 + wx1) / 2 + 0.004, wy1, '#f6f3ea')
    with far.piece(0.5) as d:
        cur = ['#f6e7c8', '#f2f2ea', '#f4d6c8'][v]
        d.poly([(wx0 - 0.03, wy0 - 0.03), (wx0 + 0.05, wy0 - 0.03), (wx0 + 0.01, wy1 + 0.03), (wx0 - 0.03, wy1 + 0.03)], cur)
        d.poly([(wx1 + 0.03, wy0 - 0.03), (wx1 - 0.05, wy0 - 0.03), (wx1 - 0.01, wy1 + 0.03), (wx1 + 0.03, wy1 + 0.03)], cur)
        d.rect(wx0 - 0.04, wy0 - 0.04, wx1 + 0.04, wy0 - 0.03, '#a89a88')
        for k in range(8):
            d.line([(wx0 - 0.02 + k * 0.004, wy0 - 0.02), (wx0 + 0.005 + k * 0.001, wy1 + 0.02)], shade(cur, 0.92), 0.002)
    with far.piece(0.5) as d:  # a plant and a jar on the sill
        d.rect(wx0 + 0.02, wy1 - 0.03, wx0 + 0.04, wy1, '#c5583e')
        d.circ(wx0 + 0.03, wy1 - 0.04, 0.02, 'leaf')
        d.rect(wx1 - 0.05, wy1 - 0.04, wx1 - 0.03, wy1, (230, 240, 250, 180), r=0.004)
    with far.piece(0.8) as d:  # wall cabinets, tiled splashback
        for x in (0.02, 0.13, 0.7, 0.81):
            d.rect(x, 0.1, x + 0.1, 0.34, cab, r=0.006)
            d.rect(x + 0.045, 0.3, x + 0.055, 0.31, '#8a8f99')
    with far.piece(0.4) as d:
        for row in range(4):
            for k in range(30):
                x = k * 0.036 + (row % 2) * 0.018
                if 0.33 < x < 0.64:
                    continue
                d.rect(x, 0.42 + row * 0.035, x + 0.033, 0.452 + row * 0.035, shade(wall, 0.93), r=0.002)
    clock(far, 0.91, 0.42, 0.03)
    mid = S.L('mid')
    with mid.piece(1.0) as d:  # counter, stove, fridge
        d.rect(-0.02, 0.555, 0.3, 0.575, '#d0c8bc', r=0.004)
        for x in np.arange(-0.02, 0.28, 0.1):
            d.rect(x + 0.005, 0.575, x + 0.095, 0.72, cab, r=0.006)
        d.rect(0.66, 0.555, 0.88, 0.575, '#d0c8bc', r=0.004)
        d.rect(0.665, 0.575, 0.78, 0.72, '#e6e6ea', r=0.004)
        d.rect(0.785, 0.575, 0.875, 0.72, cab, r=0.006)
        d.rect(0.89, 0.15, 1.02, 0.72, '#eef0f2', r=0.012)
        d.rect(0.89, 0.37, 1.02, 0.375, '#c9cfd6')
    with mid.piece(0.6) as d:
        d.rect(0.675, 0.59, 0.77, 0.66, '#3a3a40', r=0.004)
        for x in (0.69, 0.75):
            d.ell(x, 0.554, 0.018, 0.004, '#2e2e36')
        d.rect(0.7, 0.505, 0.745, 0.55, '#c0443a', r=0.01)  # kettle on the stove
        d.rect(0.74, 0.515, 0.76, 0.524, '#c0443a')
        d.rect(0.06, 0.51, 0.11, 0.555, '#e9e2d0', r=0.004)  # a bread bin
        d.rect(0.15, 0.53, 0.2, 0.555, '#f6f3ea', r=0.006)
        d.ell(0.175, 0.53, 0.03, 0.006, '#f6f3ea')
    with mid.piece(0.6) as d:  # fridge magnets: plain shapes
        for k in range(4):
            d.circ(0.92 + 0.02 * k, 0.23 + 0.03 * (k % 2), 0.008, ['#e05a5a', '#f6d353', '#3f7fbf', '#7cc45e'][k])
    near = S.L('near')
    cloth = ['#f6f0e0', '#f2f6f2', '#f8eadc'][v]
    band = [RED, '#2f6fb0', '#3d8a5a'][v]
    with near.piece(0.9) as d:  # the table
        for x in (0.23, 0.77):
            d.rect(x - 0.008, 0.84, x + 0.008, 0.99, shade(WOOD, 0.75))
    dastarkhan_top(near, 0.2, 0.8, 0.7, 0.8, rng, s=1.6, cloth=cloth, band=band)
    for x, f in ((0.12, 1), (0.88, -1)):
        chair(near, x, 0.99, 1.5, col=WOOD, face=f)
    fg = S.L('fg')
    lamp_pendant(fg, 0.5, 0.2, 1.6, col=['#f6c453', '#7fb6a8', '#e9a23a'][v])
    return {0: 'apartment kitchen, the table laid as a dastarkhan with nan, baursak and tea',
            1: 'mint kitchen with a courtyard window and a laid dastarkhan',
            2: 'warm kitchen, dastarkhan with fruit, sweets and tea'}[v]


# ---------------------------------------------------------------- service hall

def dot_screen(L, x0, y0, x1, y1, rows, rng, col='#f6a63a', col2='#6fd08a'):
    """A queue screen: rows of glowing pills and dots of different lengths. Nothing on it can be read."""
    with L.piece(0.8) as d:
        d.rect(x0, y0, x1, y1, '#1e2028', r=0.006)
    with L.piece(0.3) as d:
        rh = (y1 - y0 - 0.02) / rows
        for r_ in range(rows):
            y = y0 + 0.01 + r_ * rh + rh * 0.5
            c = col2 if r_ == 0 else col
            x = x0 + 0.012
            # left: a pill (the ticket), right: a short run of dots (the window), never letter shapes
            w = (x1 - x0) * (0.25 + 0.15 * rng.random())
            d.rect(x, y - rh * 0.2, x + w, y + rh * 0.2, c, r=rh * 0.2, lit=True)
            xr = x1 - 0.012 - (x1 - x0) * 0.25
            for k in range(3):
                d.circ(xr + k * 0.012, y, rh * 0.17, c, lit=True)
            d.rect(x1 - 0.06, y - rh * 0.05, x1 - 0.015, y + rh * 0.05, shade(c, 0.8), lit=True)
    L.glow_rect(x0 + 0.01, y0 + 0.01, x1 - 0.01, y1 - 0.01)


@biome('service_center', interior=True)
def service_center(S):
    """A big public service hall: a long row of service windows with operators' desks, queue screens of glowing dots,
    rows of waiting seats, ticket kiosks, plants. No symbols, no readable text."""
    v = S.variant % 3
    rng = S.rng
    wall = ['#eef0f2', '#efe8dc', '#e2ecea'][v]
    accent = ['#2f8fb0', '#c98a3a', '#3d8a6a'][v]
    shell(S, wall=wall, floor='#c9c6c0', fy=0.72, kind='tiles', ceiling=0.04)
    sky_ = S.L('sky')
    if v == 2:  # a skylight strip
        outside(S, sky_, (0.05, 0.0, 0.95, 0.04))
    far = S.L('far')
    ceiling_panels(far, 0.04, 5, lit=True)
    with far.piece(0.5) as d:  # an accent band with a quiet geometric ornament
        d.rect(-0.02, 0.27, 1.02, 0.3, accent)
        diamonds(d, 0.0, 1.0, 0.285, 0.02, shade(accent, 1.4), gap=1.6)
    dot_screen(far, 0.08, 0.09, 0.3, 0.24, 4, rng)
    dot_screen(far, 0.7, 0.09, 0.92, 0.24, 4, rng)
    clock(far, 0.5, 0.17, 0.04)
    mid = S.L('mid')
    n = 7
    with mid.piece(1.0) as d:  # counter
        d.rect(-0.02, 0.5, 1.02, 0.52, '#d8d4cc', r=0.004)
        d.rect(-0.02, 0.52, 1.02, 0.72, shade(accent, 1.25))
        for k in range(n):
            x = 0.01 + k * (1.0 / n)
            d.rect(x + 0.01, 0.54, x + 1.0 / n - 0.02, 0.7, shade(accent, 1.4), r=0.006)
    with mid.piece(0.3) as d:  # glass partitions
        for k in range(n):
            x = k * (1.0 / n)
            d.rect(x + 0.006, 0.31, x + 1.0 / n - 0.006, 0.5, (225, 240, 250, 80))
            d.rect(x, 0.31, x + 0.006, 0.5, '#b9c0c8')
    with mid.piece(0.7) as d:  # operators' monitors and window lamps
        for k in range(n):
            x = k * (1.0 / n) + 0.5 / n
            d.rect(x - 0.025, 0.42, x + 0.025, 0.47, '#2e2e36', r=0.003)
            d.rect(x - 0.004, 0.47, x + 0.004, 0.5, '#4a4a54')
            d.rect(x + 0.03, 0.485, x + 0.06, 0.5, '#f6f3ea')
            d.rect(x - 0.02, 0.325, x + 0.02, 0.345, '#2e2e36', r=0.004)
    with mid.piece(0.3) as d:
        for k in range(n):
            x = k * (1.0 / n) + 0.5 / n
            on = (k * 3 + v) % 4 != 0
            d.rect(x - 0.012, 0.33, x + 0.012, 0.34, '#6fd08a' if on else '#5a5a62', r=0.004, lit=on)
            d.rect(x - 0.021, 0.425, x + 0.021, 0.465, '#7fb6e8', lit=True)
    near = S.L('near')
    seat = ['#3f6fa8', '#c0603a', '#3d8a8a'][v]
    for x0 in (0.04, 0.6):  # two blocks of waiting seats, an aisle in the middle
        with near.piece(1.0) as d:
            for k in range(4):
                x = x0 + k * 0.09
                d.rect(x, 0.83, x + 0.08, 0.85, seat, r=0.006)
                d.rect(x + 0.005, 0.75, x + 0.075, 0.82, seat, r=0.012)
            d.rect(x0, 0.85, x0 + 0.35, 0.86, '#7a7a86')
            for x in (x0 + 0.02, x0 + 0.33):
                d.rect(x, 0.86, x + 0.008, 0.93, '#7a7a86')
    fg = S.L('fg')
    for x in (0.0, 0.92):  # ticket kiosks
        with fg.piece(0.9) as d:
            d.rect(x + 0.01, 0.56, x + 0.09, 1.03, '#d6dce2', r=0.012)
            d.rect(x + 0.02, 0.6, x + 0.08, 0.7, '#2e2e36', r=0.004)
            d.rect(x + 0.04, 0.76, x + 0.06, 0.77, '#3a3a40')
        with fg.piece(0.3) as d:
            d.rect(x + 0.025, 0.605, x + 0.075, 0.695, shade(accent, 1.3), lit=True)
            for k in range(3):
                d.rect(x + 0.033, 0.62 + k * 0.022, x + 0.067, 0.633 + k * 0.022, '#f6f3ea', r=0.005, lit=True)
    plant(fg, 0.13, 1.0, 2.0)
    plant(fg, 0.86, 1.0, 1.8, pot='#3a3a44')
    return {0: 'public service hall: a row of windows, queue screens of dots, waiting seats', 1: 'service hall in warm tones with kiosks',
            2: 'service hall with a skylight and green seats'}[v]


# ---------------------------------------------------------------- auditorium

@biome('auditorium', interior=True)
def auditorium(S):
    """A university lecture hall. v0/v2: the tiered rows rising to tall windows (the lecturer's view); v1: the front,
    a long chalkboard with diagrams, a projection screen with a chart, a lectern."""
    v = S.variant % 3
    rng = S.rng
    wood = ['#b98a5e', '#c9a072', '#9a6a46'][v]
    wall = ['#ece4d6', '#e6e8e2', '#efe2cf'][v]
    if v != 1:
        shell(S, wall=wall, floor='#9a8a7a', fy=0.9, kind='planks', ceiling=0.03, skirting=False)
        sky_ = S.L('sky')
        for k in range(5):  # tall windows high up on the back wall
            x = 0.06 + k * 0.2
            outside(S, sky_, (x, 0.05, x + 0.1, 0.3), draw=lambda t: _trees_band(t, 0.3), stars=True)
        far = S.L('far')
        with far.piece(0.7) as d:
            for k in range(5):
                x = 0.06 + k * 0.2
                d.rect(x - 0.008, 0.04, x + 0.108, 0.055, '#f6f3ea')
                d.rect(x - 0.008, 0.295, x + 0.108, 0.31, '#f6f3ea')
                d.rect(x - 0.008, 0.04, x, 0.31, '#f6f3ea')
                d.rect(x + 0.1, 0.04, x + 0.108, 0.31, '#f6f3ea')
                d.rect(x + 0.046, 0.05, x + 0.054, 0.3, '#f6f3ea')
                d.rect(x - 0.008, 0.17, x + 0.108, 0.177, '#f6f3ea')
        mid = S.L('mid')
        near = S.L('near')
        rows = 6
        for r_ in range(rows - 1, -1, -1):  # back rows first
            L = mid if r_ >= 2 else near
            y = 0.86 - r_ * 0.085
            sc = 1 - r_ * 0.07
            hw = 0.48 * sc
            with L.piece(0.9) as d:
                d.rect(0.5 - hw - 0.03, y, 0.5 + hw + 0.03, y + 0.09, shade(wall, 0.88 - 0.02 * r_))  # the riser step
                for sgn in (-1, 1):
                    a, b = (0.5 - hw, 0.5 - 0.05 * sc) if sgn < 0 else (0.5 + 0.05 * sc, 0.5 + hw)
                    d.rect(a, y - 0.06 * sc, b, y - 0.048 * sc, shade(wood, 1.05), r=0.003)  # desk top
                    d.rect(a + 0.004, y - 0.048 * sc, b - 0.004, y + 0.01, wood, r=0.004)  # desk front
            with L.piece(0.5) as d:
                for sgn in (-1, 1):
                    a, b = (0.5 - hw, 0.5 - 0.05 * sc) if sgn < 0 else (0.5 + 0.05 * sc, 0.5 + hw)
                    n = int((b - a) / 0.07)
                    for k in range(n):
                        xx = a + (k + 0.5) * (b - a) / n
                        d.rect(xx - 0.025 * sc, y - 0.035 * sc, xx + 0.025 * sc, y - 0.005, shade(wood, 0.88), r=0.004)
                        if rng.random() < 0.35:  # a notebook or a laptop left on the desk
                            d.rect(xx - 0.012 * sc, y - 0.066 * sc, xx + 0.012 * sc, y - 0.058 * sc, S.pick(['#f6f3ea', '#3f7fbf', '#2e2e36', '#e05a5a']))
            with L.piece(0.5) as d:  # the stairs in the aisle
                d.rect(0.5 - 0.045 * sc, y + 0.04, 0.5 + 0.045 * sc, y + 0.05, shade(wall, 0.75))
        fg = S.L('fg')
        with fg.piece(0.9) as d:  # the lectern's corner and a projector beam
            d.poly([(0.84, 0.82), (1.03, 0.8), (1.03, 1.03), (0.86, 1.03)], shade(wood, 0.9))
            d.rect(0.83, 0.8, 1.03, 0.83, shade(wood, 1.1), r=0.004)
        with fg.piece(0.4) as d:
            d.rect(0.88, 0.77, 0.94, 0.8, '#2e2e36', r=0.004)
            d.ell(0.95, 0.79, 0.012, 0.004, '#d0d6dc')
        return {0: 'tiered university lecture hall, the lecturer\'s view up to tall windows', 2: 'lecture hall in dark wood, tiered rows'}[v]
    # v1: the front of the hall
    shell(S, wall=wall, floor='#a8957e', fy=0.76, kind='planks', ceiling=0.04)
    sky_ = S.L('sky')
    for x in (0.02, 0.89):
        outside(S, sky_, (x, 0.08, x + 0.09, 0.6), draw=lambda t: _trees_band(t, 0.6), stars=True)
    far = S.L('far')
    with far.piece(0.7) as d:
        for x in (0.02, 0.89):
            for (a, b, c, e) in ((x - 0.008, 0.07, x + 0.098, 0.085), (x - 0.008, 0.59, x + 0.098, 0.61), (x - 0.008, 0.07, x, 0.61),
                                 (x + 0.09, 0.07, x + 0.098, 0.61), (x + 0.041, 0.08, x + 0.049, 0.6), (x - 0.008, 0.33, x + 0.098, 0.338)):
                d.rect(a, b, c, e, '#f6f3ea')
    with far.piece(0.9) as d:  # the long chalkboard and a pull-down screen
        d.rect(0.13, 0.2, 0.55, 0.56, '#8a6a46', r=0.004)
        d.rect(0.14, 0.21, 0.54, 0.55, '#2f4a3e')
        d.rect(0.13, 0.555, 0.55, 0.57, '#8a6a46')
        d.rect(0.58, 0.1, 0.86, 0.12, '#5a5a62', r=0.006)
        d.rect(0.59, 0.12, 0.85, 0.5, '#f8f8f4')
    with far.piece(0.3) as d:  # chalk diagrams: a circle, a triangle, a curve, arrows; a bar chart on the screen
        ch = '#e8eee6'
        d.line([(0.2 + 0.05 * math.cos(a) / AR * 1.7, 0.32 + 0.05 * math.sin(a)) for a in np.linspace(0, 6.3, 30)], ch, 0.003)
        d.line([(0.18, 0.32), (0.22, 0.32)], ch, 0.003)
        d.line([(0.29, 0.46), (0.36, 0.28), (0.42, 0.46), (0.29, 0.46)], ch, 0.003)
        d.line([(0.44 + 0.08 * u, 0.48 - 0.18 * u * u) for u in np.linspace(0, 1, 16)], ch, 0.003)
        d.line([(0.44, 0.27), (0.44, 0.49), (0.53, 0.49)], ch, 0.003)
        d.line([(0.17, 0.46), (0.25, 0.46), (0.23, 0.445)], ch, 0.003)
        d.rect(0.5, 0.548, 0.52, 0.556, '#f6f3ea')
        for k in range(5):
            h = 0.06 + 0.045 * k + 0.03 * rng.random()
            d.rect(0.62 + k * 0.042, 0.46 - h, 0.65 + k * 0.042, 0.46, ['#3f7fbf', '#e9a23a', '#6fb850', '#e05a5a', '#9a7ac8'][k])
        d.line([(0.61, 0.465), (0.84, 0.465)], '#5a5a62', 0.002)
    mid = S.L('mid')
    with mid.piece(1.0) as d:  # lecturer's table and the lectern
        d.rect(0.25, 0.6, 0.6, 0.625, shade(wood, 1.05), r=0.004)
        d.rect(0.26, 0.625, 0.59, 0.76, wood, r=0.004)
        d.poly([(0.67, 0.55), (0.79, 0.55), (0.77, 0.77), (0.69, 0.77)], shade(wood, 0.92))
        d.rect(0.66, 0.535, 0.8, 0.56, shade(wood, 1.1), r=0.004)
    with mid.piece(0.6) as d:
        d.rect(0.3, 0.57, 0.37, 0.6, '#2e2e36', r=0.003)
        d.rect(0.42, 0.585, 0.48, 0.6, '#f6f3ea')
        d.rect(0.52, 0.56, 0.535, 0.6, (225, 240, 250, 180), r=0.004)
        d.line([(0.73, 0.535), (0.75, 0.49)], '#3a3a40', 0.003)
        d.circ(0.752, 0.485, 0.008, '#3a3a40')
    near = S.L('near')
    with near.piece(1.0) as d:  # the first row of desks at the edges of the frame
        for a, b in ((-0.03, 0.22), (0.78, 1.03)):
            d.rect(a, 0.86, b, 0.885, shade(wood, 1.05), r=0.004)
            d.rect(a + 0.005, 0.885, b - 0.005, 1.03, wood, r=0.004)
    fg = S.L('fg')
    ceiling_panels(fg, 0.0, 4, lit=True)
    return {1: 'front of a lecture hall: chalkboard with diagrams, a chart on the screen, a lectern'}[v]


def _trees_band(t, y1):
    rng = np.random.default_rng(3)
    for k in range(30):
        x = rng.random()
        with t.piece(0.5) as d:
            d.circ(x, y1 - 0.02, 0.04 + 0.03 * rng.random(), 'leaf' if t.look.season != 'winter' else '#e6ecf2')


# ---------------------------------------------------------------- dacha

def greenhouse(L, x, y, s):
    k = s / AR
    with L.piece(0.5) as d:
        d.rect(x - 0.12 * k, y - 0.1 * s, x + 0.12 * k, y, (220, 240, 245, 150))
        d.ell(x, y - 0.1 * s, 0.12 * s, 0.06 * s, (220, 240, 245, 150))
    with L.piece(0.6) as d:
        for u in np.linspace(-0.12, 0.12, 6):
            d.line([(x + u * k, y), (x + u * k, y - 0.1 * s - 0.06 * s * math.sqrt(max(0, 1 - (u / 0.12) ** 2)))], '#f6f3ea', 0.003 * s)
        d.line([(x - 0.12 * k, y - 0.1 * s), (x + 0.12 * k, y - 0.1 * s)], '#f6f3ea', 0.003 * s)
        if L.look.season != 'winter':
            for u in np.linspace(-0.09, 0.09, 6):
                d.circ(x + u * k, y - 0.04 * s, 0.02 * s, 'leaf')
                d.circ(x + u * k + 0.005, y - 0.05 * s, 0.006 * s, '#e0403a')


def dacha_house(L, x, y, s, rng, col='#c9a06a'):
    k = s / AR
    with L.piece(0.9) as d:
        d.rect(x - 0.09 * k * 1.7, y - 0.13 * s, x + 0.09 * k * 1.7, y, col)
        for j in range(8):  # log or board lines
            d.rect(x - 0.09 * k * 1.7, y - 0.13 * s + j * 0.016 * s, x + 0.09 * k * 1.7, y - 0.13 * s + j * 0.016 * s + 0.002, shade(col, 0.88))
    with L.piece(0.9) as d:
        d.poly([(x - 0.1 * k * 1.7, y - 0.13 * s), (x + 0.1 * k * 1.7, y - 0.13 * s), (x, y - 0.22 * s)], '#4f7fa8' if col != '#c9a06a' else '#8a4a3a')
        d.poly([(x - 0.03 * k * 1.7, y - 0.15 * s), (x + 0.03 * k * 1.7, y - 0.15 * s), (x, y - 0.19 * s)], shade(col, 1.1))
        if L.look.season == 'winter':
            d.poly([(x - 0.1 * k * 1.7, y - 0.135 * s), (x + 0.1 * k * 1.7, y - 0.135 * s), (x, y - 0.22 * s)], '#f8fafc')
    with L.piece(0.6) as d:
        for dx in (-0.05, 0.05):
            d.rect(x + dx * k * 1.7 - 0.022 * k * 1.7, y - 0.1 * s, x + dx * k * 1.7 + 0.022 * k * 1.7, y - 0.05 * s, '#f6f3ea')
            d.window(x + dx * k * 1.7 - 0.017 * k * 1.7, y - 0.095 * s, x + dx * k * 1.7 + 0.017 * k * 1.7, y - 0.055 * s, rng=rng)
        d.rect(x - 0.12 * k * 1.7, y - 0.03 * s, x + 0.12 * k * 1.7, y - 0.022 * s, shade(col, 0.7))  # porch rail


@biome('dacha')
def dacha(S):
    """A dacha garden: a small wooden house, a greenhouse, vegetable beds, a water barrel, a picket fence, apple trees."""
    v = S.variant % 3
    rng = S.rng
    sky(S, horizon=0.55)
    far = S.L('far')
    if v != 1:
        mountains(far, 0.56, 0.24, seed=S.seed, col='#9aa3cf', snowline=0.55)
    hills(far, 0.58, 0.04, mixc('#8fb07a', '#a9b4c8', 0.4) if not winter(S) else '#dfe5ec', seed=S.seed + 1)
    mid = S.L('mid')
    with mid.piece(0.4) as d:
        d.rect(-0.03, 0.62, 1.03, 1.03, 'grass')
    for x in (0.03, 0.97):  # neighbours' roofs over the fence
        house(mid, x, 0.62, 0.8, col=S.pick(['#e9dcc0', '#c9d6e2']), roof=S.pick(['#4f7fa8', '#a34a3a', '#3d8a5a']), rng=rng)
    hx_ = [0.25, 0.72, 0.5][v]
    dacha_house(mid, hx_, 0.66, 1.2, rng, col=S.pick(['#c9a06a', '#9ac0d0', '#d9b46a']))
    ghx = [0.62, 0.3, 0.2][v]
    greenhouse(mid, ghx, 0.67, 1.1)
    for x in ([0.1, 0.85], [0.08, 0.52, 0.92], [0.78, 0.92])[v]:
        round_tree(mid, x, 0.67, 1.2 + 0.2 * S.r(), rng=rng)
        if S.season in ('summer', 'autumn'):
            with mid.piece(0.5) as d:
                for k in range(7):
                    d.circ(x + S.r(-0.05, 0.05), 0.67 - (0.24 + 0.1 * S.r()) * 1.2, 0.008, S.pick(['#d8342c', '#e9b443', '#d8342c']))
    fence(mid, -0.03, 1.03, 0.69, 1.0, col='#e6d2a8' if v != 2 else '#a8c8a0')
    near = S.L('near')
    with near.piece(0.5) as d:  # the path
        d.poly([(0.44, 0.7), (0.56, 0.7), (0.66, 1.03), (0.34, 1.03)], '#c9b89a' if not winter(S) else '#e6ecf2')
    for side in (-1, 1):  # raised vegetable beds either side of the path
        for r_ in range(2):
            y = 0.76 + r_ * 0.1
            a, b = (0.02, 0.36 - r_ * 0.03) if side < 0 else (0.64 + r_ * 0.03, 0.98)
            with near.piece(0.9) as d:
                d.rect(a, y, b, y + 0.04, '#8a6a46', r=0.004)
                d.rect(a + 0.005, y - 0.008, b - 0.005, y + 0.008, '#6a4a32' if not winter(S) else '#f2f6fa', r=0.006)
            if winter(S):
                continue
            with near.piece(0.7) as d:
                kind = (r_ + (side > 0)) % 3
                xx = a + 0.02
                while xx < b - 0.015:
                    if kind == 0:  # cabbages
                        d.circ(xx, y - 0.012, 0.018, '#9ad070')
                        d.circ(xx, y - 0.014, 0.01, '#c8ec9a')
                        xx += 0.035
                    elif kind == 1:  # tomatoes on stakes
                        d.line([(xx, y), (xx, y - 0.07)], '#8a6a46', 0.003)
                        d.circ(xx, y - 0.04, 0.016, 'leaf')
                        d.circ(xx + 0.006, y - 0.03, 0.006, '#e0403a')
                        d.circ(xx - 0.005, y - 0.05, 0.006, '#e0403a' if S.season != 'spring' else '#7cc45e')
                        xx += 0.03
                    else:  # greens and carrot tops
                        for j in range(3):
                            d.poly([(xx - 0.003, y), (xx + 0.003, y), (xx + (j - 1) * 0.006, y - 0.03)], 'leaf2')
                        xx += 0.016
    with near.piece(0.9) as d:  # a water barrel and a watering can
        d.rect(0.86, 0.62, 0.94, 0.75, '#3f6fa8', r=0.012)
        d.rect(0.86, 0.65, 0.94, 0.66, shade('#3f6fa8', 0.7))
        d.rect(0.86, 0.71, 0.94, 0.72, shade('#3f6fa8', 0.7))
        d.ell(0.9, 0.62, 0.04, 0.008, '#2f4f78')
        d.rect(0.38, 0.88, 0.42, 0.93, '#6fb850', r=0.008)
        d.line([(0.42, 0.9), (0.45, 0.875)], '#6fb850', 0.005)
    fg = S.L('fg')
    if S.season in ('summer', 'autumn') and not winter(S):  # sunflowers
        for x in (0.04, 0.1, 0.95):
            with fg.piece(0.9) as d:
                d.line([(x, 1.03), (x + 0.01, 0.62)], '#5a8a3a', 0.008)
                d.ell(x - 0.01, 0.8, 0.025, 0.01, 'leaf')
                d.circ(x + 0.01, 0.6, 0.04, '#f6c453')
                d.circ(x + 0.01, 0.6, 0.022, '#6a4a2a')
    else:
        bush(fg, 0.05, 1.03, 2.0)
        bush(fg, 0.96, 1.03, 1.8)
    grass_tufts(fg, 0.95, 1.0, 14, rng, s=2.0)
    weather_fx(S, ground=0.68)
    return {0: 'dacha garden: a wooden house, a greenhouse, vegetable beds, mountains far away',
            1: 'dacha plot with apple trees, a greenhouse and a water barrel', 2: 'dacha with a blue house, beds and sunflowers under the mountains'}[v]


# ---------------------------------------------------------------- bus stop

def shelter(L, x0, x1, y, s, rng, col='#5a7a9a'):
    with L.piece(0.9) as d:
        d.rect(x0, y - 0.32 * s, x1, y - 0.3 * s, col, r=0.004)  # roof
        d.rect(x0 - 0.01, y - 0.335 * s, x1 + 0.01, y - 0.315 * s, shade(col, 0.8), r=0.006)
        for x in (x0 + 0.005, x1 - 0.005):
            d.rect(x - 0.004, y - 0.3 * s, x + 0.004, y, shade(col, 0.7))
    with L.piece(0.3) as d:  # glass back panel
        d.rect(x0 + 0.01, y - 0.29 * s, x1 - 0.01, y - 0.04 * s, (220, 236, 245, 90))
    with L.piece(0.8) as d:  # schedule panel of dots (no text) and a bench
        px = x1 - 0.07
        d.rect(px, y - 0.26 * s, px + 0.05, y - 0.12 * s, '#f6f3ea', r=0.003)
        for r_ in range(6):
            for k in range(5):
                if rng.random() < 0.8:
                    d.circ(px + 0.008 + k * 0.009, y - 0.24 * s + r_ * 0.02 * s, 0.003, '#5a6a7a')
        d.rect(x0 + 0.03, y - 0.09 * s, x1 - 0.1, y - 0.075 * s, '#b07a4a', r=0.003)
        for x in (x0 + 0.04, x1 - 0.11):
            d.rect(x - 0.003, y - 0.075 * s, x + 0.003, y, '#3a3a44')
        if L.look.season == 'winter':
            d.rect(x0 - 0.01, y - 0.345 * s, x1 + 0.01, y - 0.33 * s, '#f8fafc', r=0.008)


@biome('bus_stop')
def bus_stop(S):
    """A bus stop on a city street: a shelter with a bench and a schedule panel of dots, a lamp, a bin, snowdrifts,
    panel blocks and poplars across the road."""
    v = S.variant % 3
    rng = S.rng
    sky(S, horizon=0.5, cloud_y=(0.04, 0.2))
    far = S.L('far')
    if v == 2:
        mountains(far, 0.5, 0.2, seed=S.seed, col='#9aa3cf', snowline=0.5)
    for k in range(4):
        x = -0.05 + k * 0.27 + S.r(0, 0.04)
        block(far, x, x + 0.22, 0.56, 9 if v != 1 else 12, S.pick(['#d6d2c8', '#c9cdd2', '#e0d8c4']), rng, fh=0.034, balcony=False)
    mid = S.L('mid')
    for k in range(9):
        poplar(mid, 0.02 + k * 0.12 + S.r(-0.02, 0.02), 0.6, 1.0 + 0.2 * S.r())
    snow = winter(S)
    with mid.piece(0.5) as d:  # road
        d.rect(-0.03, 0.6, 1.03, 0.62, '#c9c1b0' if not snow else '#eef3f8')
        d.rect(-0.03, 0.62, 1.03, 0.76, '#7a7a86' if not snow else '#a8acb6')
        for k in range(10):
            d.rect(k * 0.11, 0.69, k * 0.11 + 0.05, 0.696, '#f2f2f2')
    if v == 1:
        bus(mid, 0.3, 0.72, 1.7, col=S.pick(['#e9b443', '#3f8f5a', '#c0443a']), rng=rng)
        car(mid, 0.78, 0.68, 1.4, col='#f2f2f2', face=-1)
    else:
        car(mid, 0.2, 0.74, 1.5, col=S.pick(['#e05a5a', '#3f7fbf', '#2e2e36']), face=1)
        car(mid, 0.68, 0.68, 1.3, col=S.pick(['#f6c453', '#f2f2f2']), face=-1)
    near = S.L('near')
    with near.piece(0.5) as d:  # the pavement and a curb with snowbanks
        d.rect(-0.03, 0.76, 1.03, 1.03, '#b9b4aa' if not snow else '#eef3f8')
        d.rect(-0.03, 0.76, 1.03, 0.775, '#8f8a82')
    if snow:
        with near.piece(0.6) as d:
            for k in range(12):
                d.ell(k * 0.09 + S.r(-0.02, 0.02), 0.77, 0.07 + 0.03 * S.r(), 0.022, '#ffffff')
    sx0 = [0.58, 0.6, 0.06][v]
    shelter(near, sx0, sx0 + 0.34, 0.92, 1.25, rng, col=S.pick(['#5a7a9a', '#3d8a6a', '#8a5a4a']))
    lx = 0.3 if v != 2 else 0.6
    lamp_post(near, lx, 0.9, 2.2)
    with near.piece(0.9) as d:  # a bin
        bx = sx0 - 0.04 if v != 2 else sx0 + 0.38
        d.rect(bx - 0.018, 0.84, bx + 0.018, 0.91, '#4a6a5a', r=0.006)
        d.rect(bx - 0.022, 0.835, bx + 0.022, 0.845, '#3a4a40', r=0.004)
    fg = S.L('fg')
    if snow:
        with fg.piece(0.8) as d:
            d.ell(0.08 if v != 2 else 0.92, 1.03, 0.2, 0.07, '#ffffff')
            d.ell(0.9 if v != 2 else 0.1, 1.04, 0.15, 0.05, '#f6f8fc')
    else:
        with fg.piece(0.4) as d:  # puddles
            d.ell(0.15, 0.97, 0.12, 0.015, '#8a9ab0')
            d.ell(0.8, 0.99, 0.09, 0.012, '#8a9ab0')
        grass_tufts(fg, 0.97, 1.0, 6, rng, s=1.6)
    weather_fx(S, ground=0.7)
    return {0: 'city bus stop in winter: shelter, bench, lamp, snowbanks, panel blocks', 1: 'bus stop with a bus pulling in, poplars and tall blocks',
            2: 'bus stop on a snowy street under the mountains'}[v]


# ---------------------------------------------------------------- station

def station_building(L, x0, x1, y, s, rng, col='#e9d8b4', trim='#f6f3ea', roof='#5a7a8a'):
    """A station building in a plain classical style: arched windows, a central block with a clock face."""
    h = 0.22 * s
    cx = (x0 + x1) / 2
    with L.piece(0.9) as d:
        d.rect(x0, y - h, x1, y, col)
        d.rect(x0 - 0.005, y - h - 0.015, x1 + 0.005, y - h, trim)
        d.rect(cx - 0.08, y - h - 0.1 * s, cx + 0.08, y, col)
        d.poly([(cx - 0.09, y - h - 0.1 * s), (cx + 0.09, y - h - 0.1 * s), (cx, y - h - 0.17 * s)], roof)
        d.rect(cx - 0.09, y - h - 0.105 * s, cx + 0.09, y - h - 0.095 * s, trim)
        for x in (x0 + 0.01, cx - 0.08, cx + 0.07, x1 - 0.02):
            d.rect(x, y - h, x + 0.01, y, trim)
    with L.piece(0.6) as d:
        n = int((x1 - x0) / 0.05)
        for k in range(n):
            wx = x0 + (k + 0.5) * (x1 - x0) / n
            if abs(wx - cx) < 0.09:
                continue
            d.rect(wx - 0.013, y - h * 0.7, wx + 0.013, y - h * 0.2, trim)
            d.window(wx - 0.01, y - h * 0.68, wx + 0.01, y - h * 0.22, rng=rng)
            d.ell(wx, y - h * 0.68, 0.016 / AR * 1.6 * 0.8, 0.012, trim)
        d.circ(cx, y - h - 0.03 * s, 0.035 * s, '#3a3a40')
        d.circ(cx, y - h - 0.03 * s, 0.03 * s, '#fbfbf6', lit=L.look.lit_share > 0.3)
        d.line([(cx, y - h - 0.03 * s), (cx, y - h - 0.05 * s)], '#2a2a30', 0.003)
        d.line([(cx, y - h - 0.03 * s), (cx + 0.01, y - h - 0.026 * s)], '#2a2a30', 0.003)
        d.rect(cx - 0.035, y - h * 0.75, cx + 0.035, y, '#7a4a2a', r=0.01)
        d.window(cx - 0.03, y - h * 0.72, cx + 0.03, y - h * 0.4, rng=rng)


@biome('station')
def station(S):
    """A railway station: the station building with a clock face, a train at the platform, a canopy on columns,
    benches and lamps on the platform."""
    v = S.variant % 3
    rng = S.rng
    sky(S, horizon=0.5, cloud_y=(0.04, 0.2))
    far = S.L('far')
    if v == 1:
        mountains(far, 0.5, 0.2, seed=S.seed, col='#9aa3cf', snowline=0.5)
    else:
        for k in range(3):
            x = 0.05 + k * 0.33
            block(far, x, x + 0.2, 0.5, 7, S.pick(['#d6d2c8', '#c9cdd2']), rng, fh=0.03, balcony=False)
    station_building(far, 0.08, 0.92, 0.6, 1.0, rng, col=['#e9d8b4', '#e6e0d4', '#d9c8a8'][v], roof=['#5a7a8a', '#3d8a6a', '#8a5a4a'][v])
    for x in (0.02, 0.97):
        poplar(far, x, 0.6, 1.0)
    mid = S.L('mid')
    with mid.piece(0.6) as d:  # track bed
        d.rect(-0.03, 0.58, 1.03, 0.68, '#a89a88')
        d.rect(-0.03, 0.665, 1.03, 0.672, '#6a6a72')
    if v != 2:
        train(mid, [-0.1, 0.15][v], 0.665, 1.5, 6, rng, col=S.pick(['#3f8f5a', '#3f6fa8', '#8a5a9a']))
    else:
        train(mid, 0.55, 0.665, 1.5, 3, rng, col='#3f6fa8', face=-1)
    near = S.L('near')
    with near.piece(0.8) as d:  # platform with a safety line
        d.rect(-0.03, 0.68, 1.03, 1.03, '#b9b4aa' if not winter(S) else '#eef3f8')
        d.rect(-0.03, 0.68, 1.03, 0.695, '#d8d2c6')
        d.rect(-0.03, 0.705, 1.03, 0.712, '#f2c14e')
    with near.piece(0.3) as d:
        for k in range(14):
            d.rect(k * 0.08, 0.75 + 0.002 * (k % 2), k * 0.08 + 0.078, 1.03, shade('#b9b4aa', 0.97 + 0.03 * (k % 2)) if not winter(S) else '#f2f6fa')
    for x in (0.2, 0.8):
        bench(near, x, 0.86, 1.6, col='#8a5a3a')
    for x in (0.08, 0.5, 0.92):
        lamp_post(near, x, 0.92, 1.6)
    fg = S.L('fg')
    with fg.piece(0.9) as d:  # the canopy over the platform on cast columns
        col = ['#4f6a7a', '#3d6a5a', '#6a4a4a'][v]
        d.poly([(-0.03, -0.02), (1.03, -0.02), (1.03, 0.1), (-0.03, 0.14)], col)
        d.rect(-0.03, 0.1, 1.03, 0.115, shade(col, 0.8))
        for k in range(30):
            d.poly([(k * 0.036, 0.115), (k * 0.036 + 0.018, 0.115), (k * 0.036 + 0.009, 0.135)], shade(col, 0.8))
        for x in (0.02, 0.36, 0.64, 0.98):
            d.rect(x - 0.01, 0.11, x + 0.01, 1.03, '#3a4048', r=0.004)
            d.rect(x - 0.016, 0.96, x + 0.016, 1.03, '#2e3238', r=0.004)
            d.line([(x, 0.2), (x + 0.06, 0.13)], '#3a4048', 0.005)
            d.line([(x, 0.2), (x - 0.06, 0.13)], '#3a4048', 0.005)
    if winter(S):
        with fg.piece(0.5) as d:
            d.rect(-0.03, 0.135, 1.03, 0.15, '#ffffff', r=0.006)
    weather_fx(S, ground=0.65)
    return {0: 'railway station: a building with a clock face, a train at the platform, a canopy', 1: 'mountain station with a long train',
            2: 'station platform, a short train arriving'}[v]


# ---------------------------------------------------------------- Caspian shore

def chink(L, x0, x1, top, base, col, rng, depth=0.9):
    """A pale flat-topped cliff (chink) with layered bands and gullies."""
    f = ridge_fn(abs(int(x0 * 1000)) + 3, top, 0.015, freqs=(3.0, 9.0, 21.0))
    with L.piece(depth) as d:
        pts = [(x0 + (x1 - x0) * u, f(x0 + (x1 - x0) * u)) for u in np.linspace(0, 1, 40)]
        d.poly([(x0 - 0.04, base)] + pts + [(x1 + 0.04, base)], col)
    with L.piece(0.6 * depth) as d:  # scree at the foot
        d.poly([(x0 - 0.06, base), (x0 + 0.02, base - (base - top) * 0.25), (x1 - 0.02, base - (base - top) * 0.22), (x1 + 0.06, base)], shade(col, 0.92))
    with L.piece(0.5 * depth) as d:
        for k in range(3):  # soft wavy strata
            y = top + 0.03 + k * (base - top) * 0.2
            d.line([(x0 + 0.01 + (x1 - x0) * u, y + 0.006 * math.sin(u * 9 + k)) for u in np.linspace(0, 1, 30)],
                   shade(col, 0.9 if k % 2 else 1.06), 0.007)
        x = x0 + 0.03 * rng.random()
        while x < x1 - 0.02:
            w = 0.004 + 0.012 * rng.random()
            t0 = top + 0.02 + 0.08 * rng.random()
            d.poly([(x, t0), (x + w * 1.8, base - (base - top) * 0.25), (x - w * 1.2, base - (base - top) * 0.25)], shade(col, 0.86))
            x += 0.07 + 0.1 * rng.random()


@biome('caspian')
def caspian(S):
    """The Caspian shore: steppe meeting the sea, pale chink cliffs, a sandy beach, a fishing boat, gulls."""
    v = S.variant % 3
    rng = S.rng
    hz = 0.5
    sky(S, horizon=hz, cloud_y=(0.04, 0.24))
    gulls(S.L('sky'), rng, 6, 0.12, 0.35, 1.4)
    far = S.L('far')
    from scenes import water
    water(far, hz, col='#4f9fc0' if S.time == 'day' else '#5a8fb0', col2='#7ab8d0', seed=S.seed)
    sand = '#e6d2a4' if not winter(S) else '#e9ece8'
    cliff = ['#eadcc0', '#efd6c0', '#e6dcc6'][v]
    mid = S.L('mid')
    if v == 0:
        chink(mid, 0.62, 1.04, 0.36, 0.7, cliff, rng)
        chink(far, 0.85, 1.05, 0.44, hz + 0.02, mixc(cliff, '#b4b8d0', 0.3), rng, depth=0.6)
        boat(mid, 0.3, 0.6, 1.2, col='#2f6fb0', sail='#f6f3ea')
    elif v == 1:
        chink(far, -0.05, 0.3, 0.42, hz + 0.02, mixc(cliff, '#b4b8d0', 0.3), rng, depth=0.6)
        chink(mid, -0.05, 0.22, 0.4, 0.68, cliff, rng)
    else:
        chink(far, 0.1, 0.45, 0.45, hz + 0.02, mixc(cliff, '#b4b8d0', 0.3), rng, depth=0.6)
        boat(far, 0.7, hz + 0.04, 0.7, col='#c0443a')
    with mid.piece(0.5) as d:  # surf and the wet sand line
        f = ridge_fn(S.seed, 0.66, 0.012, freqs=(1.3, 3.1, 7.0))
        d.ridge(f, sand)
        d.line([(x, f(x) + 0.002) for x in np.linspace(-0.03, 1.03, 60)], '#f6faf8', 0.006)
    near = S.L('near')
    if v == 2:  # the steppe plateau edge, looking down
        g = hills(near, 0.8, 0.04, 'steppe', seed=S.seed + 2)
        with near.piece(0.6) as d:
            d.poly([(0.0, g(0.0)), (0.12, g(0.12) + 0.04), (0.2, 1.03), (-0.03, 1.03)], cliff)
        horse(near, 0.8, g(0.8) + 0.1, 2.0, col='#8a5a3a', face=-1)
    else:
        with near.piece(0.5) as d:
            d.rect(-0.03, 0.74, 1.03, 1.03, sand)
            d.ell(0.4, 0.76, 0.5, 0.02, shade(sand, 0.95))
        patches(near, lambda x: 0.76, 1.0, 10, rng, [shade(sand, 0.93), shade(sand, 1.05)], depth=0.3)
        with near.piece(0.6) as d:  # shells and pebbles
            for _ in range(18):
                x, y = rng.random(), 0.8 + 0.18 * rng.random()
                d.ell(x, y, 0.006, 0.004, S.pick(['#f6f3ea', '#d9c8b0', '#bfb4a4', '#f2d6c8']))
        if v == 1:
            boat(near, 0.72, 0.84, 2.0, col='#c0443a', sail=None or '#f6f3ea')
            with near.piece(0.6) as d:  # nets drying on poles
                for x in (0.12, 0.3):
                    d.line([(x, 0.88), (x, 0.7)], '#7a5a3a', 0.006)
                d.line([(0.12, 0.71), (0.3, 0.72)], '#5a5a62', 0.002)
                for k in range(12):
                    x = 0.125 + k * 0.015
                    d.line([(x, 0.71), (x + 0.004, 0.8)], (90, 90, 110, 140), 0.0015)
                for k in range(5):
                    d.line([(0.12, 0.73 + k * 0.016), (0.3, 0.735 + k * 0.016)], (90, 90, 110, 140), 0.0015)
                for k in range(5):
                    d.circ(0.13 + k * 0.04, 0.8, 0.006, '#f2a03a')
    fg = S.L('fg')
    grass_tufts(fg, 0.94, 1.0, 16, rng, col='steppe2', col2='steppe', s=2.2)
    if v != 2:
        rock(fg, 0.05, 1.03, 2.4, col='#d6cbb6')
    gulls(fg, rng, 2, 0.15, 0.3, 3.0)
    weather_fx(S, ground=0.7)
    return {0: 'Caspian shore: pale chink cliffs, a sandy beach, a fishing boat, gulls', 1: 'Caspian beach with a boat pulled up and nets drying',
            2: 'steppe plateau edge above the Caspian sea, a horse grazing'}[v]


# ---------------------------------------------------------------- taxi

def _street_view(S, kind):
    def draw(t):
        rng = np.random.default_rng(S.seed)
        night = t.look.lit_share > 0.3
        x = 0.0
        while x < 1.0:
            w = 0.05 + 0.06 * rng.random()
            h = 0.12 + 0.2 * rng.random()
            if rng.random() < 0.5:
                block(t, x, x + w, 0.52, max(3, int(h / 0.03)), S.pick(['#e9dcc6', '#d8c9b4', '#c9d3dc']), rng, fh=0.03, balcony=False)
            else:
                tower(t, x, x + w, 0.52, h + 0.06, S.pick(['#c9d6e2', '#d8dee6']), rng, fh=0.02)
            x += w + 0.004
        for k in range(10):
            poplar(t, 0.05 + k * 0.1, 0.53, 0.9)
        with t.piece(0.4) as d:
            d.rect(0.0, 0.52, 1.0, 0.7, '#6a6a76' if not winter(S) else '#c9cfd8')
            d.poly([(0.47, 0.52), (0.53, 0.52), (0.6, 0.7), (0.4, 0.7)], shade('#6a6a76', 1.1) if not winter(S) else '#dfe4ea')
            for k in range(4):
                y = 0.55 + k * 0.04
                d.rect(0.497 - k * 0.002, y, 0.503 + k * 0.002, y + 0.015 + k * 0.004, '#f2f2f2')
        car(t, 0.42, 0.6, 1.1, col='#e05a5a', face=-1)
        car(t, 0.7, 0.58, 0.9, col='#f2f2f2', face=1)
        if night:  # bokeh: soft discs of street and car lights
            img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            dd = ImageDraw.Draw(img)
            for _ in range(70):
                x, y = rng.random() * W, (0.3 + 0.3 * rng.random()) * H
                r = (0.008 + 0.025 * rng.random()) * H
                c = [(255, 214, 120), (255, 160, 90), (255, 90, 70), (140, 190, 255), (255, 240, 200)][int(rng.integers(5))]
                dd.ellipse([x - r, y - r, x + r, y + r], fill=c + (int(110 + 80 * rng.random()),))
            img = img.filter(ImageFilter.GaussianBlur(5))
            t.base.alpha_composite(img)
    return draw


@biome('taxi', interior=True)
def taxi(S):
    """A taxi at night, from the back seat: the dashboard and wheel, the backs of the front seats, a rear-view mirror
    with a little felt tree hanging from it, and the city lights through the windscreen."""
    v = S.variant % 3
    rng = S.rng
    trim = ['#2e2e36', '#3a3430', '#2a3038'][v]
    seatc = ['#3a3a44', '#6a4a3a', '#4a4a5a'][v]
    shell(S, wall=trim, floor=trim, fy=1.0, kind='carpet', skirting=False)
    sky_ = S.L('sky')
    outside(S, sky_, (0.0, 0.1, 1.0, 0.62), draw=_street_view(S, v), stars=True, haze=0.25)
    far = S.L('far')
    with far.piece(0.9) as d:  # roof lining, A-pillars, the dashboard
        d.poly([(-0.03, -0.02), (1.03, -0.02), (1.03, 0.14), (0.85, 0.12), (0.15, 0.12), (-0.03, 0.14)], shade(trim, 1.3))
        d.poly([(-0.03, 0.1), (0.08, 0.12), (0.0, 0.62), (-0.03, 0.62)], shade(trim, 1.1))
        d.poly([(1.03, 0.1), (0.92, 0.12), (1.0, 0.62), (1.03, 0.62)], shade(trim, 1.1))
        pts = [(u, 0.58 - 0.025 * math.sin(math.pi * u)) for u in np.linspace(-0.03, 1.03, 30)]
        d.poly(pts + [(1.03, 1.03), (-0.03, 1.03)], trim)
    with far.piece(0.6) as d:  # instruments (plain dials), vents, a phone on a holder
        for x in (0.2, 0.28):
            d.circ(x, 0.62, 0.035, '#1a1a20')
            d.circ(x, 0.62, 0.029, '#24242c')
        for k in range(4):
            d.rect(0.44 + k * 0.035, 0.6, 0.47 + k * 0.035, 0.62, '#1a1a20', r=0.004)
        d.rect(0.62, 0.52, 0.67, 0.6, '#1a1a20', r=0.006)
    with far.piece(0.3) as d:
        for x in (0.2, 0.28):
            d.line([(x, 0.62), (x + 0.012, 0.6)], '#ff8a5a', 0.003, lit=True)
            for k in range(7):
                a = math.pi * (0.8 + 0.2 * k)
                d.circ(x + math.cos(a) * 0.025 / AR, 0.62 + math.sin(a) * 0.025, 0.002, '#9fd0ff', lit=True)
        d.rect(0.625, 0.527, 0.665, 0.593, '#5a9ad0', lit=True)
        d.circ(0.645, 0.56, 0.01, '#f6f3ea', lit=True)
        far.glow_rect(0.63, 0.53, 0.66, 0.59)
    mid = S.L('mid')
    with mid.piece(1.0) as d:  # the steering wheel (left-hand drive)
        cx, cy, r = 0.2, 0.585, 0.14
        d.line([(cx + math.cos(a) * r / AR * 1.3, cy + math.sin(a) * r * 0.7) for a in np.linspace(0, 6.3, 40)], '#4a4a58', 0.02)
        d.ell(cx, cy, 0.03, 0.022, '#3a3a46')
        d.line([(cx - r / AR * 1.3, cy), (cx + r / AR * 1.3, cy)], '#4a4a58', 0.016)
    with mid.piece(0.9) as d:  # the rear-view mirror and a felt tree hanging from it
        d.line([(0.5, 0.12), (0.5, 0.16)], '#1a1a20', 0.008)
        d.rect(0.43, 0.15, 0.57, 0.2, '#1a1a20', r=0.012)
        d.rect(0.435, 0.155, 0.565, 0.195, '#4a5068', r=0.01)
        d.line([(0.53, 0.2), (0.535, 0.27)], '#d0d0d0', 0.002)
        tree = ['#3d9a5a', '#e9b443', '#c0443a'][v]
        d.poly([(0.535, 0.265), (0.565, 0.32), (0.55, 0.318), (0.57, 0.355), (0.5, 0.355), (0.52, 0.318), (0.505, 0.32)], tree)
        d.rect(0.532, 0.355, 0.538, 0.365, '#8a5a3a')
    near = S.L('near')
    for x0, x1 in ((0.04, 0.36), (0.64, 0.96)):  # the front seats from behind, with headrests
        with near.piece(1.0) as d:
            d.rect(x0 + 0.08, 0.5, x1 - 0.08, 0.6, seatc, r=0.03)
            d.rect((x0 + x1) / 2 - 0.014, 0.59, (x0 + x1) / 2 - 0.008, 0.66, '#8a8f99')
            d.rect((x0 + x1) / 2 + 0.008, 0.59, (x0 + x1) / 2 + 0.014, 0.66, '#8a8f99')
            d.rect(x0 + 0.02, 0.65, x1 - 0.02, 1.05, seatc, r=0.05)
        with near.piece(0.5) as d:
            d.rect(x0 + 0.05, 0.71, x1 - 0.05, 0.98, shade(seatc, 1.15), r=0.04)
            d.rect(x0 + 0.08, 0.86, x1 - 0.08, 0.94, shade(seatc, 0.85), r=0.02)  # seat-back pocket
    with near.piece(0.9) as d:  # the console between the seats
        d.rect(0.43, 0.84, 0.57, 1.05, shade(trim, 1.2), r=0.02)
        d.rect(0.46, 0.86, 0.54, 0.89, '#1a1a20', r=0.008)
    fg = S.L('fg')
    if S.weather in ('rain', 'snow'):  # drops on the windscreen
        with fg.piece(0.3) as d:
            for _ in range(70):
                x, y = rng.random(), 0.14 + 0.42 * rng.random()
                if 0.42 < x < 0.58 and y > 0.14:
                    pass
                r = 0.003 + 0.006 * rng.random()
                d.ell(x, y, r, r * (1.2 if S.weather == 'rain' else 1), (230, 240, 255, 120) if S.weather == 'rain' else (255, 255, 255, 200))
    with fg.piece(0.9) as d:  # the door edges and the back-seat headliner framing the shot
        d.poly([(-0.03, 0.2), (0.03, 0.25), (0.03, 1.03), (-0.03, 1.03)], shade(trim, 0.8))
        d.poly([(1.03, 0.2), (0.97, 0.25), (0.97, 1.03), (1.03, 1.03)], shade(trim, 0.8))
        d.rect(-0.03, -0.02, 1.03, 0.04, shade(trim, 0.9))
        d.circ(0.5, 0.025, 0.012, '#fff2c0' if S.look.lit_share > 0.5 else '#c9c9c9', lit=S.look.lit_share > 0.5)
    return {0: 'taxi at night from the back seat: wheel, dashboard, a felt tree on the mirror, city lights',
            1: 'taxi interior in warm brown, the street through the windscreen', 2: 'taxi interior, blue-grey, a red felt tree on the mirror'}[v]
