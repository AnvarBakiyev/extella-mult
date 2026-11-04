"""Studio sets as layered plates (puppet-plates-more): interview, talk show, news, game show, podcast, weather, press
room, cooking show, pitch stage, blogger desk, wedding hall (toi), aquarium studio.

Same layer roles as rooms.py: sky = back wall and floor, far = things on the wall, mid = the set pieces, near = the
furniture in front (the middle is left open for the puppets), fg = framing (light rigs, cameras, the audience).
No text, digits, logos, flags or emblems anywhere: screens show shapes, tickers are dots, scores are lamps."""
import math
from contextlib import contextmanager

import numpy as np
from PIL import Image, ImageFilter

from plates import AR, W, H, shade, mixc, hx, to255, D
from plates import cloud
from scenes import biome
from rooms import shell, lamp_pendant, ceiling_panels, clock, shelf, plant, desk, chair, monitor, sofa, rug, WOOD

# biome -> (variants, looks)
_STUDIO = [('day', 'clear', 'summer', 'felt'), ('night', 'clear', 'summer', 'felt'), ('day', 'clear', 'summer', 'vivid'),
           ('night', 'clear', 'summer', 'cool'), ('golden', 'clear', 'autumn', 'warm'), ('dusk', 'clear', 'winter', 'pastel')]
_EVENING = [('night', 'clear', 'summer', 'felt'), ('dusk', 'clear', 'summer', 'felt'), ('night', 'clear', 'summer', 'vivid'),
            ('day', 'clear', 'summer', 'felt'), ('night', 'clear', 'winter', 'warm'), ('golden', 'clear', 'autumn', 'pastel')]
LOOKS = {b: (3, list(_STUDIO)) for b in ('interview_studio', 'news_desk', 'game_show', 'podcast', 'weather_studio',
                                          'press_room', 'cooking_show', 'pitch_stage', 'unboxing_desk', 'aquarium_studio')}
LOOKS['talkshow'] = (3, list(_EVENING))
LOOKS['wedding_hall'] = (3, list(_EVENING))


# ---------------------------------------------------------------- helpers

@contextmanager
def soft(L, blur=0.0):
    """Draw translucent light (bokeh, beams, gloss) and alpha-blend it onto the layer, optionally blurred; no felt."""
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    yield D(L, img)
    if blur:
        img = img.filter(ImageFilter.GaussianBlur(blur * H))
    L.base = Image.alpha_composite(L.base, img)


def rgba(c, a):
    v = hx(c)
    return (int(v[0] * 255), int(v[1] * 255), int(v[2] * 255), int(a))


def bokeh(L, x0, y0, x1, y1, rng, n=40, cols=('#9fc8ff', '#ffffff', '#ffd9a0'), rmin=0.01, rmax=0.04, blur=0.004):
    with soft(L, blur) as d:
        for _ in range(n):
            r = rmin + (rmax - rmin) * rng.random() ** 2
            c = cols[int(rng.integers(len(cols)))]
            d.circ(x0 + (x1 - x0) * rng.random(), y0 + (y1 - y0) * rng.random(), r, rgba(c, 50 + 90 * rng.random()))


def beams(L, xs, top=0.0, bottom=0.8, spread=0.09, col='#fff2c8', a=46, aim=None):
    """Soft spotlight cones from the rig down to the floor."""
    with soft(L, 0.012) as d:
        for i, x in enumerate(xs):
            tx = aim[i] if aim else x
            d.poly([(x - 0.012, top), (x + 0.012, top), (tx + spread, bottom), (tx - spread, bottom)], rgba(col, a))
            d.ell(tx, bottom, spread * AR * 0.95, 0.03, rgba(col, a + 20))


def gloss(L, y0, y1, xs, col='#ffffff', a=40):
    """Glossy floor: soft streaks under the lights."""
    with soft(L, 0.01) as d:
        for x in xs:
            d.poly([(x - 0.03, y0), (x + 0.03, y0), (x + 0.05, y1), (x - 0.05, y1)], rgba(col, a))


def rig(L, y=0.02, n=7, col='#3a3a40'):
    """A lighting truss across the top with lamps that are always on."""
    with L.piece(0.8) as d:
        d.rect(-0.02, y, 1.02, y + 0.016, col)
        for k in range(40):
            x = k * 0.026
            d.line([(x, y + 0.002), (x + 0.013, y + 0.014)], shade(col, 1.3), 0.002)
        for k in range(n):
            x = (k + 0.5) / n
            d.rect(x - 0.022, y + 0.016, x + 0.022, y + 0.06, '#2a2a30', r=0.006)
            d.ell(x, y + 0.06, 0.018, 0.007, '#fff2c0', lit=True)
            L.glow_circ(x, y + 0.065, 0.025)


def camera(L, x, y=0.98, s=1.0, face=1, body='#4a4a54'):
    """A studio camera on a tripod, lens towards `face`."""
    k = s
    with L.piece(0.8) as d:
        d.line([(x, y), (x, y - 0.2 * k)], '#3a3a40', 0.008 * k)
        d.line([(x, y - 0.18 * k), (x - 0.04 * k, y)], '#3a3a40', 0.006 * k)
        d.line([(x, y - 0.18 * k), (x + 0.04 * k, y)], '#3a3a40', 0.006 * k)
        d.rect(x - 0.045 * k, y - 0.28 * k, x + 0.045 * k, y - 0.2 * k, body, r=0.008 * k)
        lx0, lx1 = (x + 0.04 * k, x + 0.075 * k) if face > 0 else (x - 0.075 * k, x - 0.04 * k)
        d.rect(lx0, y - 0.265 * k, lx1, y - 0.215 * k, '#2e2e36', r=0.006 * k)
        d.rect(x - 0.03 * k, y - 0.305 * k, x + 0.02 * k, y - 0.28 * k, '#2e2e36', r=0.004 * k)
        d.line([(x - face * 0.04 * k, y - 0.21 * k), (x - face * 0.09 * k, y - 0.17 * k)], '#2e2e36', 0.005 * k)
    with L.piece(0.4) as d:
        d.circ(x - face * 0.03 * k, y - 0.265 * k, 0.006 * k, '#e05a5a', lit=True)


def floor_lamp_softbox(L, x, y=0.98, s=1.0, face=1):
    """A softbox light on a stand, glowing."""
    with L.piece(0.8) as d:
        d.line([(x, y), (x, y - 0.32 * s)], '#3a3a40', 0.006 * s)
        d.line([(x, y - 0.06 * s), (x - 0.035 * s, y)], '#3a3a40', 0.005 * s)
        d.line([(x, y - 0.06 * s), (x + 0.035 * s, y)], '#3a3a40', 0.005 * s)
        d.poly([(x - 0.05 * s, y - 0.44 * s), (x + 0.05 * s, y - 0.4 * s), (x + 0.05 * s, y - 0.28 * s), (x - 0.05 * s, y - 0.3 * s)] if face > 0 else
               [(x - 0.05 * s, y - 0.4 * s), (x + 0.05 * s, y - 0.44 * s), (x + 0.05 * s, y - 0.3 * s), (x - 0.05 * s, y - 0.28 * s)], '#2a2a30')
    with L.piece(0.4) as d:
        d.poly([(x - 0.042 * s, y - 0.425 * s), (x + 0.042 * s, y - 0.395 * s), (x + 0.042 * s, y - 0.29 * s), (x - 0.042 * s, y - 0.305 * s)] if face > 0 else
               [(x - 0.042 * s, y - 0.395 * s), (x + 0.042 * s, y - 0.425 * s), (x + 0.042 * s, y - 0.305 * s), (x - 0.042 * s, y - 0.29 * s)], '#fff8e8', lit=True)
    L.glow_rect(x - 0.04 * s, y - 0.42 * s, x + 0.04 * s, y - 0.3 * s)


def armchair(L, x, y, s=1.0, col='#c9a868', face=1, legs='#5a3a2a'):
    """A lounge armchair seen three-quarter, turned towards `face` (the back sits on the far side)."""
    k = s / AR * 1.0
    with L.piece(0.9) as d:  # back
        bx = x - face * 0.018 * s
        d.rect(bx - 0.075 * s, y - 0.3 * s, bx + 0.075 * s, y - 0.1 * s, shade(col, 0.88), r=0.035 * s)
    with L.piece(0.9) as d:  # seat cushion
        d.rect(x - 0.085 * s, y - 0.14 * s, x + 0.085 * s, y - 0.07 * s, col, r=0.025 * s)
        d.rect(x - 0.075 * s, y - 0.15 * s, x + 0.075 * s, y - 0.11 * s, shade(col, 1.12), r=0.02 * s)
    with L.piece(0.9) as d:  # arms: the inner one lower
        for sx in (-1, 1):
            low = 0.0 if sx == face else -0.015 * s
            d.rect(x + sx * 0.085 * s - 0.022 * s, y - 0.2 * s + low, x + sx * 0.085 * s + 0.022 * s, y - 0.06 * s, shade(col, 0.95), r=0.02 * s)
        for sx in (-1, 1):
            d.rect(x + sx * 0.07 * s - 0.005 * s, y - 0.065 * s, x + sx * 0.07 * s + 0.005 * s, y, legs)
    del k


def glass(L, x, y, s=1.0):
    """A glass of water on a table top at y."""
    with L.piece(0.4) as d:
        d.rect(x - 0.008 * s, y - 0.045 * s, x + 0.008 * s, y, (220, 236, 248, 170), r=0.003 * s)
        d.rect(x - 0.007 * s, y - 0.028 * s, x + 0.007 * s, y - 0.002 * s, (150, 196, 232, 200), r=0.002 * s)
        d.rect(x - 0.005 * s, y - 0.042 * s, x - 0.003 * s, y - 0.006 * s, (255, 255, 255, 200))


def side_table(L, x, y, w=0.06, h=0.1, col='#e9e4da', top=None):
    with L.piece(0.9) as d:
        d.ell(x, y - h, w, 0.012, top or shade(col, 1.05))
        d.rect(x - 0.006, y - h, x + 0.006, y, shade(col, 0.7))
        d.ell(x, y, w * 0.6, 0.008, shade(col, 0.7))


def audience(L, y, rng, rows=2, n=16, s=1.0, cols=None, dark=0.55, x0=-0.02, x1=1.02):
    """Rows of puppet spectators seen from behind: heads and shoulders, muted so they read as the house."""
    cols = cols or ['#5a4a6a', '#4a5a6a', '#6a4a4a', '#4a6a5a', '#6a5a4a', '#3a4a6a']
    hair = ['#2a2020', '#4a3020', '#6a4a2a', '#1a1a24', '#8a6a3a', '#3a2a2a']
    for r in range(rows):
        yy = y + r * 0.075 * s
        ss = s * (1 + 0.18 * r)
        with L.piece(1.0) as d:
            m = n - r * 2
            for i in range(m):
                x = x0 + (x1 - x0) * (i + 0.5 + (0.5 if r % 2 else 0) * 0.5) / m + (rng.random() - 0.5) * 0.015
                c = shade(cols[int(rng.integers(len(cols)))], dark + 0.1 * r)
                d.ell(x, yy + 0.05 * ss, 0.055 * ss, 0.045 * ss, c)
                d.circ(x, yy - 0.0 * ss, 0.034 * ss, shade(hair[int(rng.integers(len(hair)))], dark + 0.25 + 0.1 * r))


def screen(L, x0, y0, x1, y1, bezel='#1a1a22', glow=True):
    with L.piece(0.6) as d:
        d.rect(x0 - 0.01, y0 - 0.015, x1 + 0.01, y1 + 0.015, bezel, r=0.008)
    if glow:
        L.glow_rect(x0, y0, x1, y1)


def grad_rect(L, x0, y0, x1, y1, ctop, cbot):
    """A vertical gradient patch pasted straight onto a layer (screen pictures, backdrops)."""
    a, b = hx(ctop), hx(cbot)
    h = max(2, int((y1 - y0) * H))
    w = max(2, int((x1 - x0) * W))
    t = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    arr = np.broadcast_to(a * (1 - t) + b * t, (h, w, 3))
    patch = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), 'RGB').convert('RGBA')
    L.base.alpha_composite(patch, (int(x0 * W), int(y0 * H)))


def skyline_patch(L, x0, y0, x1, y1, rng, night=True, top='#141a3e', bot='#4a3a7a', bld='#232848'):
    """A city-at-night picture (for backdrops and the news screen)."""
    grad_rect(L, x0, y0, x1, y1, top, bot)
    with L.piece(0.4) as d:
        x = x0
        while x < x1 - 0.005:
            bw = 0.025 + 0.03 * rng.random()
            bh = (y1 - y0) * (0.25 + 0.5 * rng.random())
            d.rect(x, y1 - bh, min(x + bw, x1), y1, shade(bld, 0.9 + 0.3 * rng.random()))
            x += bw + 0.003
    with L.piece(0.25) as d:
        for _ in range(int((x1 - x0) * 420)):
            xx = x0 + (x1 - x0) * rng.random()
            yy = y0 + (y1 - y0) * (0.5 + 0.48 * rng.random())
            if rng.random() < 0.55:
                d.rect(xx, yy, min(xx + 0.004, x1), yy + 0.006, S_WIN[int(rng.integers(3))], lit=True)
        if night:
            d.circ(x0 + (x1 - x0) * 0.8, y0 + (y1 - y0) * 0.2, (y1 - y0) * 0.07, '#f6efd2', lit=True)


S_WIN = ('#ffd36e', '#ffe7a8', '#9fd0ff')


def mic_stand(L, x, y, s=1.0):
    with L.piece(0.8) as d:
        d.line([(x, y), (x, y - 0.3 * s)], '#3a3a40', 0.005 * s)
        d.line([(x, y - 0.3 * s), (x + 0.03 * s, y - 0.34 * s)], '#3a3a40', 0.004 * s)
        d.ell(x, y, 0.03 * s, 0.006 * s, '#3a3a40')
        d.ell(x + 0.032 * s, y - 0.345 * s, 0.009 * s, 0.012 * s, '#2a2a30')


def drape(L, x0, x1, y0, y1, col, folds=6):
    """A gathered curtain: vertical stripes of light and dark."""
    with L.piece(0.8) as d:
        d.rect(x0, y0, x1, y1, col, r=0.006)
        w = (x1 - x0) / folds
        for k in range(folds):
            d.rect(x0 + k * w + w * 0.55, y0, x0 + k * w + w * 0.75, y1, shade(col, 0.85))
            d.rect(x0 + k * w + w * 0.1, y0, x0 + k * w + w * 0.2, y1, shade(col, 1.12))


# ---------------------------------------------------------------- interview studio

@biome('interview_studio', interior=True)
def interview_studio(S):
    v = S.variant % 3
    rng = S.rng
    wall = ['#1f2a52', '#3a2a24', '#22303a'][v]
    shell(S, wall=wall, floor=['#2a2f48', '#4a3a30', '#2e3a40'][v], fy=0.74, kind='carpet', skirting=False)
    sky_ = S.L('sky')
    if v == 0:  # blue backdrop with soft out-of-focus lights
        grad_rect(sky_, 0.0, 0.0, 1.0, 0.74, '#13204a', '#2f5a9a')
        bokeh(sky_, 0.0, 0.05, 1.0, 0.7, rng, n=70, cols=('#8fc0ff', '#cfe4ff', '#ffd9a0', '#7fd0ff'), rmin=0.012, rmax=0.05)
    elif v == 1:  # warm wooden slats with a lit shelf
        with sky_.piece(0.5) as d:
            for k in range(48):
                x = k * 0.0215
                d.rect(x, 0.0, x + 0.016, 0.74, mixc('#8a5a3a', '#b07a4a', (k * 37 % 11) / 11), r=0.004)
        bokeh(sky_, 0.0, 0.0, 1.0, 0.7, rng, n=24, cols=('#ffd9a0', '#ffe8c0'), rmin=0.01, rmax=0.03)
    else:  # city night panorama behind glass
        skyline_patch(sky_, 0.0, 0.04, 1.0, 0.7, rng, top='#0e1638', bot='#3a4a8a', bld='#1e2848')
        bokeh(sky_, 0.0, 0.3, 1.0, 0.7, rng, n=40, cols=('#ffd36e', '#9fd0ff', '#ff9a8a'), rmin=0.008, rmax=0.03)
    with sky_.piece(0.4) as d:  # floor riser for the set
        d.ell(0.5, 0.8, 0.85, 0.07, shade(['#2a2f48', '#4a3a30', '#2e3a40'][v], 1.25))
    gloss(sky_, 0.74, 0.86, (0.3, 0.7), a=28)
    far = S.L('far')
    if v == 1:
        with far.piece(0.7) as d:
            for y in (0.28, 0.46):
                d.rect(0.62, y, 0.92, y + 0.014, '#5a3a24')
        with far.piece(0.6) as d:
            for x, y, c in ((0.65, 0.28, '#e9a23a'), (0.71, 0.28, '#3d8a5a'), (0.84, 0.28, '#f3ead6'), (0.68, 0.46, '#c0443a'), (0.8, 0.46, '#2f6fb0')):
                d.rect(x, y - 0.06, x + 0.035, y, c, r=0.004)
            d.circ(0.77, 0.25, 0.03, '#f6c453')
        plant(far, 0.14, 0.56, 1.4)
        lamp_pendant(far, 0.3, 0.3, 1.2, col='#2a2a30')
    elif v == 0:
        with far.piece(0.6) as d:  # light columns at the sides
            for x in (0.04, 0.92):
                d.rect(x, 0.08, x + 0.04, 0.72, '#16204a', r=0.01)
        with far.piece(0.3) as d:
            for x in (0.06, 0.94):
                d.rect(x - 0.004, 0.1, x + 0.004, 0.7, '#9fd0ff', lit=True)
        far.glow_rect(0.055, 0.1, 0.065, 0.7)
        far.glow_rect(0.935, 0.1, 0.945, 0.7)
    else:
        with far.piece(0.8) as d:  # window mullions
            for k in range(1, 6):
                d.rect(k / 6 - 0.005, 0.02, k / 6 + 0.005, 0.72, '#1a1e2a')
            d.rect(-0.02, 0.02, 1.02, 0.05, '#1a1e2a')
    mid = S.L('mid')
    cols = [('#e9dcc4', '#e9dcc4'), ('#3f6f6a', '#c9a868'), ('#c0443a', '#c0443a')][v]
    rug(mid, 0.5, 0.79, 0.3, 0.05, col=['#3a4a7a', '#8a5a3a', '#4a5a6a'][v], col2=['#4a5a9a', '#a87a4a', '#5a6a7a'][v])
    armchair(mid, 0.31, 0.82, 1.15, col=cols[0], face=1)
    armchair(mid, 0.69, 0.82, 1.15, col=cols[1], face=-1)
    side_table(mid, 0.5, 0.8, w=0.055, h=0.09, col=['#f3efe6', '#6a4630', '#2e2e36'][v])
    glass(mid, 0.485, 0.71)
    glass(mid, 0.515, 0.71)
    near = S.L('near')
    camera(near, 0.08, 1.0, 1.25, face=1)
    if v != 1:
        floor_lamp_softbox(near, 0.93, 1.0, 1.1, face=-1)
    else:
        plant(near, 0.94, 1.0, 2.2)
    fg = S.L('fg')
    rig(fg, 0.0, n=6)
    return {0: 'TV interview set: two armchairs, a low table, blue backdrop with soft lights',
            1: 'TV interview set with a warm wooden slat wall and shelves', 2: 'TV interview set before a night-city window'}[v]


# ---------------------------------------------------------------- talk show

@biome('talkshow', interior=True)
def talkshow(S):
    v = S.variant % 3
    rng = S.rng
    wall = ['#1a1a34', '#2a1a30', '#1a2a34'][v]
    shell(S, wall=wall, floor='#2a2238', fy=0.72, kind='planks', skirting=False)
    sky_ = S.L('sky')
    if v in (0, 1):  # the city skyline backdrop
        skyline_patch(sky_, 0.04, 0.06, 0.96, 0.66, rng, top=['#0c1236', '#2a1840'][v], bot=['#3a4a8a', '#b0507a'][v],
                      bld=['#1c2446', '#2a1c3a'][v])
    else:  # a velvet curtain
        drape(sky_, 0.0, 1.0, 0.0, 0.72, '#7a1f34', folds=18)
    gloss(sky_, 0.72, 0.9, (0.25, 0.5, 0.75), a=30)
    far = S.L('far')
    with far.piece(0.8) as d:  # frame and side towers
        if v != 2:
            d.rect(0.02, 0.04, 0.98, 0.075, '#3a2a4a')
            for x in (0.0, 0.94):
                d.rect(x, 0.04, x + 0.06, 0.72, '#3a2a4a', r=0.006)
    with far.piece(0.4) as d:  # applause lamp: a glowing pill with a row of bulbs, no words
        d.rect(0.42, 0.09, 0.58, 0.15, '#2a1a1a', r=0.03)
        d.rect(0.43, 0.1, 0.57, 0.14, '#e0402e', r=0.02, lit=True)
        for k in range(7):
            d.circ(0.445 + k * 0.0183, 0.12, 0.007, '#ffe0a0', lit=True)
    far.glow_rect(0.43, 0.1, 0.57, 0.14)
    if v == 2:
        with far.piece(0.6) as d:  # bulb-lit arch
            for k in range(25):
                a = math.pi * k / 24
                d.circ(0.5 - 0.42 * math.cos(a), 0.7 - 0.55 * math.sin(a) * 1.0, 0.011, '#ffe9a8', lit=True)
                far.glow_circ(0.5 - 0.42 * math.cos(a), 0.7 - 0.55 * math.sin(a), 0.02)
    plant(far, 0.08, 0.72, 1.6)
    mid = S.L('mid')
    desk_c = ['#6a3a8a', '#a8473a', '#2f6f8a'][v]
    chair(mid, 0.8, 0.6, 1.5, col='#2e2e36', office=True, face=-1)
    with mid.piece(1.0) as d:  # host desk, right
        d.rect(0.65, 0.56, 0.93, 0.585, '#3a2a24', r=0.006)
        d.rect(0.665, 0.585, 0.915, 0.765, desk_c, r=0.012)
        d.rect(0.68, 0.765, 0.9, 0.78, '#1e1a22')
    with mid.piece(0.6) as d:
        d.rect(0.68, 0.6, 0.9, 0.75, shade(desk_c, 1.12), r=0.01)
        d.circ(0.79, 0.675, 0.035, shade(desk_c, 0.8))
        d.circ(0.79, 0.675, 0.022, shade(desk_c, 1.35))
        d.rect(0.84, 0.52, 0.86, 0.56, '#f3efe6', r=0.004)  # mug
        d.line([(0.72, 0.56), (0.74, 0.51)], '#3a3a40', 0.003)
        d.circ(0.742, 0.505, 0.007, '#2a2a30')
    # guest couch: a gentle curved sofa, left
    cc = ['#c9a868', '#3f8f8a', '#e9dcc4'][v]
    with mid.piece(0.9) as d:
        pts = [(0.1 + 0.42 * u, 0.6 - 0.035 * math.sin(math.pi * u)) for u in np.linspace(0, 1, 30)]
        d.poly(pts + [(0.52, 0.7), (0.1, 0.7)], shade(cc, 0.85))
    with mid.piece(0.9) as d:
        d.rect(0.1, 0.68, 0.52, 0.74, cc, r=0.02)
        d.rect(0.09, 0.64, 0.135, 0.76, shade(cc, 0.95), r=0.02)
        d.rect(0.485, 0.64, 0.53, 0.76, shade(cc, 0.95), r=0.02)
        for x in (0.12, 0.5):
            d.rect(x - 0.005, 0.76, x + 0.005, 0.78, '#3a2a20')
    with mid.piece(0.6) as d:
        d.rect(0.18, 0.63, 0.23, 0.68, shade(desk_c, 1.2), r=0.012)
        d.rect(0.42, 0.63, 0.47, 0.68, shade(desk_c, 1.2), r=0.012)
    side_table(mid, 0.6, 0.78, 0.035, 0.08, col='#2e2e36')
    glass(mid, 0.6, 0.7)
    near = S.L('near')
    plant(near, 0.95, 0.86, 1.8, pot='#2e2e36')
    fg = S.L('fg')
    rig(fg, 0.0, n=8)
    audience(fg, 0.92, rng, rows=2, n=18, s=1.0, dark=0.45)
    return {0: 'late-night talk show: city-night backdrop, guest couch, host desk, the audience in front',
            1: 'talk show with a dusk-city backdrop and a red desk', 2: 'talk show with a velvet curtain and a bulb arch'}[v]


# ---------------------------------------------------------------- news desk

def street_picture(L, x0, y0, x1, y1, rng, look):
    """The 'live link' on the news screen: an abstract street with houses, a lamp and a tree."""
    top, bot = ('#7ab4e6', '#d8ecf6') if not look.night else ('#141c46', '#3a4a86')
    grad_rect(L, x0, y0, x1, y1, top, bot)
    with L.piece(0.4) as d:
        w = x1 - x0
        hh = y1 - y0
        d.rect(x0, y0 + hh * 0.82, x1, y1, '#8a8f99')
        for i, (u, bw, bh, c) in enumerate(((0.0, 0.22, 0.55, '#e9b88a'), (0.24, 0.18, 0.7, '#cfd6e0'), (0.44, 0.2, 0.45, '#e08a6a'),
                                            (0.66, 0.16, 0.62, '#b9c8a8'), (0.84, 0.17, 0.5, '#e6d6b0'))):
            bx0, bx1 = x0 + w * u, x0 + w * (u + bw)
            d.rect(bx0, y0 + hh * (0.82 - bh), bx1, y0 + hh * 0.82, c)
            for r_ in range(int(bh * 7)):
                for cx in range(3):
                    wx = bx0 + (bx1 - bx0) * (0.15 + cx * 0.28)
                    wy = y0 + hh * (0.82 - bh + 0.06 + r_ * 0.12)
                    lit = look.night and rng.random() < 0.6
                    d.rect(wx, wy, wx + (bx1 - bx0) * 0.14, wy + hh * 0.06, '#ffd36e' if lit else '#6f8fb0', lit=lit)
        d.line([(x0 + w * 0.62, y0 + hh * 0.82), (x0 + w * 0.62, y0 + hh * 0.35)], '#3a3a44', 0.004)
        d.circ(x0 + w * 0.625, y0 + hh * 0.35, 0.008, '#ffe6a0', lit=look.night)
        d.circ(x0 + w * 0.15, y0 + hh * 0.6, hh * 0.18, '#5f9e4e')
        d.rect(x0 + w * 0.148, y0 + hh * 0.6, x0 + w * 0.155, y0 + hh * 0.82, '#6a4a2a')


def ticker(L, x0, x1, y, rng, band='#c0302a', dots='#ffffff'):
    """A news ticker made of dots and dashes, no letters."""
    with L.piece(0.6) as d:
        d.rect(x0, y, x1, y + 0.04, '#f3efe6')
        d.rect(x0, y, x0 + (x1 - x0) * 0.16, y + 0.04, band)
    with L.piece(0.3) as d:
        x = x0 + (x1 - x0) * 0.18
        while x < x1 - 0.01:
            n = int(rng.integers(2, 6))
            for k in range(n):
                d.circ(x + k * 0.008, y + 0.02, 0.0045, '#2a2a34')
            x += n * 0.008 + 0.015
        d.circ(x0 + (x1 - x0) * 0.08, y + 0.02, 0.009, dots, lit=True)


def globe(L, x, y, r, accent):
    """An abstract lit globe: a disc with a meridian and parallels, no land, no names."""
    with L.piece(0.5) as d:
        d.circ(x, y, r, shade(accent, 0.6))
        d.circ(x, y, r * 0.88, accent, lit=True)
    with L.piece(0.3) as d:
        lc = shade(accent, 1.45)
        for k in (-2, -1, 1, 2):
            yy = y + k * r * 0.3
            hw = r * 0.88 * math.sqrt(max(0.0, 1 - (k * 0.3 / 0.88) ** 2)) / AR
            d.rect(x - hw, yy - 0.0016, x + hw, yy + 0.0016, lc, lit=True)
        d.rect(x - r * 0.88 / AR, y - 0.0016, x + r * 0.88 / AR, y + 0.0016, lc, lit=True)
        d.rect(x - 0.0016, y - r * 0.88, x + 0.0016, y + r * 0.88, lc, lit=True)
        d.ell(x, y, r * 0.45, r * 0.88, (0, 0, 0, 0))
        d.ell(x, y, r * 0.43, r * 0.86, accent, lit=True)
        d.rect(x - 0.0016, y - r * 0.86, x + 0.0016, y + r * 0.86, lc, lit=True)
        for k in (-2, -1, 1, 2):
            yy = y + k * r * 0.3
            hw = r * 0.43 * math.sqrt(max(0.0, 1 - (k * 0.3 / 0.86) ** 2)) / AR
            d.rect(x - hw, yy - 0.0016, x + hw, yy + 0.0016, lc, lit=True)
    L.glow_circ(x, y, r * 0.8)


@biome('news_desk', interior=True)
def news_desk(S):
    v = S.variant % 3
    rng = S.rng
    wall = ['#1c2c4c', '#3a1e28', '#1e2a2e'][v]
    accent = ['#2f7fd0', '#d04a3a', '#2fb0a0'][v]
    shell(S, wall=wall, floor='#2a2e3a', fy=0.76, kind='carpet', skirting=False)
    sky_ = S.L('sky')
    with sky_.piece(0.5) as d:  # panelled wall with light lines
        for k in range(12):
            x = k / 12
            d.rect(x + 0.004, 0.04, x + 1 / 12 - 0.004, 0.74, shade(wall, 1.12), r=0.006)
    with sky_.piece(0.3) as d:
        d.rect(-0.02, 0.68, 1.02, 0.686, accent, lit=True)
    gloss(sky_, 0.76, 0.95, (0.2, 0.5, 0.8), a=26)
    far = S.L('far')
    look = S.look
    if v == 2:  # split screens: studio graphic + the live link
        for (x0, x1) in ((0.08, 0.46), (0.54, 0.92)):
            screen(far, x0, 0.12, x1, 0.5)
        street_picture(far, 0.54, 0.12, 0.92, 0.5, rng, look)
        grad_rect(far, 0.08, 0.12, 0.46, 0.5, shade(accent, 0.35), shade(accent, 0.6))
        globe(far, 0.27, 0.31, 0.15, accent)
        ticker(far, 0.08, 0.92, 0.52, rng, band=accent)
    else:
        x0, x1 = (0.4, 0.94) if v == 0 else (0.06, 0.6)
        screen(far, x0, 0.11, x1, 0.53)
        street_picture(far, x0, 0.11, x1, 0.53, rng, look)
        with far.piece(0.3) as d:  # 'live' corner: a red dot, no letters
            d.rect(x0 + 0.015, 0.125, x0 + 0.06, 0.15, '#c0302a', r=0.004, lit=True)
            d.circ(x0 + 0.026, 0.1375, 0.006, '#ffffff', lit=True)
        ticker(far, x0, x1, 0.55, rng, band=accent)
        ox = 0.06 if v == 0 else 0.66
        globe(far, ox + 0.14, 0.33, 0.15, accent)
    mid = S.L('mid')
    dx0, dx1 = (0.06, 0.62) if v == 0 else (0.38, 0.94) if v == 1 else (0.2, 0.8)
    chair(mid, dx0 + (dx1 - dx0) * 0.5, 0.66, 1.6, col='#2e2e36', office=True)
    with mid.piece(1.0) as d:  # the anchor desk: a slab top, a dark front with a lit band, a plinth
        d.rect(dx0, 0.59, dx1, 0.615, '#eceef2', r=0.008)
        d.rect(dx0 + 0.015, 0.615, dx1 - 0.015, 0.775, '#2a3040', r=0.01)
        d.rect(dx0 + 0.04, 0.775, dx1 - 0.04, 0.8, '#1a1e28')
    with mid.piece(0.6) as d:
        d.rect(dx0 + 0.03, 0.63, dx1 - 0.03, 0.76, '#343c50', r=0.008)
    with mid.piece(0.5) as d:
        d.rect(dx0 + 0.03, 0.69, dx1 - 0.03, 0.703, accent, lit=True)
        d.rect(dx0 + (dx1 - dx0) * 0.62, 0.575, dx0 + (dx1 - dx0) * 0.75, 0.595, '#f6f3ea', r=0.002)  # papers
        d.rect(dx0 + (dx1 - dx0) * 0.2, 0.555, dx0 + (dx1 - dx0) * 0.3, 0.6, '#2e2e36', r=0.003)  # laptop
    mid.glow_rect(dx0 + 0.03, 0.69, dx1 - 0.03, 0.703)
    near = S.L('near')
    camera(near, 0.92 if v != 1 else 0.08, 1.0, 1.2, face=-1 if v != 1 else 1)
    with near.piece(0.9) as d:  # floor monitor
        mx = 0.07 if v != 1 else 0.9
        d.poly([(mx - 0.05, 0.98), (mx + 0.05, 0.98), (mx + 0.035, 0.9), (mx - 0.035, 0.9)], '#2e2e36')
        d.rect(mx - 0.032, 0.915, mx + 0.032, 0.965, '#3f7fbf', lit=True)
    fg = S.L('fg')
    rig(fg, 0.0, n=7)
    return {0: 'TV news desk with a live-link screen and a ticker of dots', 1: 'TV news set, red, the screen on the left',
            2: 'TV news set with split screens: studio graphic and the live link'}[v]


# ---------------------------------------------------------------- game show

def podium(L, x, y, s, col, btn, lamp_on=True):
    with L.piece(1.0) as d:
        d.poly([(x - 0.06 * s, y - 0.2 * s), (x + 0.06 * s, y - 0.2 * s), (x + 0.045 * s, y), (x - 0.045 * s, y)], col)
        d.rect(x - 0.068 * s, y - 0.225 * s, x + 0.068 * s, y - 0.195 * s, '#f3efe6', r=0.008 * s)
    with L.piece(0.6) as d:
        d.poly([(x - 0.054 * s, y - 0.15 * s), (x + 0.054 * s, y - 0.15 * s), (x + 0.05 * s, y - 0.13 * s), (x - 0.05 * s, y - 0.13 * s)], shade(col, 1.3))
        d.circ(x, y - 0.08 * s, 0.03 * s, '#1e1e26')
        d.circ(x, y - 0.08 * s, 0.024 * s, shade(btn, 1.2), lit=lamp_on)  # round score lamp, no digits
        d.ell(x, y - 0.235 * s, 0.03 * s, 0.012 * s, shade(btn, 0.6))
        d.ell(x, y - 0.243 * s, 0.026 * s, 0.012 * s, btn, lit=True)  # the big button
    if lamp_on:
        L.glow_circ(x, y - 0.08 * s, 0.03 * s)


@biome('game_show', interior=True)
def game_show(S):
    v = S.variant % 3
    rng = S.rng
    wall = ['#24163e', '#0e2238', '#3a1414'][v]
    gold = ['#f6c453', '#5fd0f0', '#ffa04a'][v]
    shell(S, wall=wall, floor=['#2a1a44', '#122a40', '#401a1a'][v], fy=0.7, kind='carpet', skirting=False)
    sky_ = S.L('sky')
    with sky_.piece(0.4) as d:  # stage floor ring
        d.ell(0.5, 0.8, 0.95, 0.12, shade(wall, 1.6))
        d.ell(0.5, 0.8, 0.8, 0.09, shade(wall, 1.3))
    beams(sky_, (0.15, 0.38, 0.62, 0.85), top=0.0, bottom=0.78, spread=0.07, col=gold, a=40,
          aim=(0.25, 0.5, 0.75, 0.62) if v != 1 else (0.28, 0.42, 0.58, 0.72))
    gloss(sky_, 0.7, 0.95, (0.25, 0.5, 0.75), a=35)
    far = S.L('far')
    if v == 0:  # bulb arch and a ring of lamps
        with far.piece(0.7) as d:
            for k in range(31):
                a = math.pi * k / 30
                x, y = 0.5 - 0.44 * math.cos(a), 0.68 - 0.58 * math.sin(a)
                d.circ(x, y, 0.013, gold, lit=True)
                far.glow_circ(x, y, 0.02)
        with far.piece(0.6) as d:
            d.circ(0.5, 0.36, 0.16, '#3a2460')
            for k in range(12):
                a = 2 * math.pi * k / 12
                d.circ(0.5 + 0.13 * math.cos(a) / AR, 0.36 + 0.13 * math.sin(a), 0.016, ['#e05a5a', '#f6c453', '#5fd0f0'][k % 3], lit=True)
            d.circ(0.5, 0.36, 0.07, '#f6c453', lit=True)
        far.glow_circ(0.5, 0.36, 0.08)
    elif v == 1:  # an LED wall of round cells
        with far.piece(0.5) as d:
            d.rect(0.06, 0.06, 0.94, 0.6, '#0a1420', r=0.01)
            for i in range(30):
                for j in range(10):
                    x, y = 0.08 + i * 0.0293, 0.09 + j * 0.052
                    on = (math.sin(i * 0.5 + j * 0.9) + math.sin(i * 0.21 - j * 0.3)) > 0.4
                    d.circ(x, y, 0.012, '#5fd0f0' if on else '#163448', lit=on)
    else:  # a big wheel of coloured segments, no numbers
        with far.piece(0.8) as d:
            d.circ(0.5, 0.33, 0.27, '#f3efe6')
            cs = ['#e05a5a', '#f6c453', '#3f7fbf', '#6fb850', '#b99be0', '#f28b6b']
            for k in range(12):
                d.pie(0.5, 0.33, 0.25, k * 30, k * 30 + 30, cs[k % 6])
            d.circ(0.5, 0.33, 0.05, '#f6c453')
            d.poly([(0.49, 0.03), (0.51, 0.03), (0.5, 0.09)], '#f3efe6')
        with far.piece(0.4) as d:
            for k in range(24):
                a = 2 * math.pi * k / 24
                d.circ(0.5 + 0.262 * math.cos(a) / AR, 0.33 + 0.262 * math.sin(a), 0.006, '#fff2c0', lit=True)
        with far.piece(0.6) as d:
            for x in (0.1, 0.9):
                for j in range(6):
                    d.circ(x, 0.12 + j * 0.09, 0.022, gold if j % 2 == 0 else '#e05a5a', lit=True)
                    far.glow_circ(x, 0.12 + j * 0.09, 0.03)
    with far.piece(0.6) as d:  # score lamps above each podium
        for x in (0.25, 0.5, 0.75):
            d.rect(x - 0.06, 0.62 if v != 2 else 0.63, x + 0.06, 0.67 if v != 2 else 0.68, '#1e1e26', r=0.02)
            for k in range(4):
                d.circ(x - 0.04 + k * 0.027, 0.645 if v != 2 else 0.655, 0.008, gold if k < 1 + int(rng.integers(4)) else '#3a3a44', lit=True)
    mid = S.L('mid')
    pcol = [('#e05a5a', '#e05a5a'), ('#3f7fbf', '#f6c453'), ('#6fb850', '#5fd0f0')]
    for i, x in enumerate((0.25, 0.5, 0.75)):
        yy = 0.86 if v != 1 else (0.86 if i != 1 else 0.82)
        podium(mid, x, yy, 1.25, [['#c0443a', '#2f6fb0', '#3d8a5a'], ['#2f6fb0', '#2f6fb0', '#2f6fb0'], ['#8a3a6a', '#c07a2a', '#3a6a8a']][v][i],
               ['#ff5a4a', '#ffd34a', '#5ad06a'][i])
    del pcol
    near = S.L('near')
    camera(near, 0.04, 1.0, 1.1, face=1)
    with near.piece(0.9) as d:  # host lectern at the right
        d.poly([(0.88, 0.62), (1.0, 0.62), (0.99, 0.98), (0.89, 0.98)], shade(wall, 1.5))
        d.rect(0.895, 0.66, 0.985, 0.94, shade(wall, 1.9), r=0.006)
        d.rect(0.875, 0.6, 1.01, 0.625, gold, lit=True)
    fg = S.L('fg')
    rig(fg, 0.0, n=8)
    with fg.piece(0.6) as d:  # stage-edge lights
        d.rect(-0.02, 0.975, 1.02, 1.02, '#1a1a22')
        for k in range(26):
            x = k * 0.04 + 0.01
            d.circ(x, 0.99, 0.008, gold, lit=True)
            fg.glow_circ(x, 0.99, 0.012)
    return {0: 'game show: three podiums, a bulb arch and a ring of lamps, spotlights',
            1: 'game show with an LED wall of round cells, blue light', 2: 'game show with a big wheel of colours, warm light'}[v]


# ---------------------------------------------------------------- podcast

def foam_wall(L, x0, y0, x1, y1, col, n=6):
    """Acoustic foam: squares of wedges, alternately turned."""
    cw = (x1 - x0) / n
    rows = max(1, int(round((y1 - y0) / (cw * AR))))
    ch = (y1 - y0) / rows
    with L.piece(0.6) as d:
        for i in range(n):
            for j in range(rows):
                cx0, cy0 = x0 + i * cw, y0 + j * ch
                d.rect(cx0 + 0.002, cy0 + 0.004, cx0 + cw - 0.002, cy0 + ch - 0.004, col, r=0.004)
                for k in range(4):
                    if (i + j) % 2:
                        d.rect(cx0 + cw * (0.1 + k * 0.22), cy0 + 0.01, cx0 + cw * (0.2 + k * 0.22), cy0 + ch - 0.01, shade(col, 0.75))
                    else:
                        d.rect(cx0 + 0.006, cy0 + ch * (0.1 + k * 0.22), cx0 + cw - 0.006, cy0 + ch * (0.2 + k * 0.22), shade(col, 0.75))


def ball_mic(L, x, y, s=1.0, face=1, col='#2a2a30'):
    """A podcast mic on a boom arm rising from the table edge at (x, y)."""
    with L.piece(0.8) as d:
        d.line([(x, y), (x + face * 0.03 * s, y - 0.12 * s), (x + face * 0.08 * s, y - 0.16 * s)], '#4a4a54', 0.005 * s)
        d.line([(x + face * 0.08 * s, y - 0.16 * s), (x + face * 0.1 * s, y - 0.12 * s)], '#4a4a54', 0.004 * s)
        d.circ(x + face * 0.1 * s, y - 0.1 * s, 0.032 * s, col)
        d.circ(x + face * 0.1 * s, y - 0.1 * s, 0.024 * s, shade(col, 1.35))
        for k in range(3):
            d.rect(x + face * 0.1 * s - 0.016 * s, y - 0.11 * s + k * 0.009 * s, x + face * 0.1 * s + 0.016 * s, y - 0.107 * s + k * 0.009 * s, shade(col, 0.8))


def headphones(L, x, y, s=1.0, col='#3a3a44'):
    with L.piece(0.7) as d:
        d.ell(x, y - 0.012 * s, 0.03 * s, 0.022 * s, col)
        d.ell(x, y - 0.012 * s, 0.022 * s, 0.014 * s, (0, 0, 0, 0))
        d.ell(x - 0.022 * s, y - 0.004 * s, 0.012 * s, 0.008 * s, shade(col, 0.8))
        d.ell(x + 0.022 * s, y - 0.004 * s, 0.012 * s, 0.008 * s, shade(col, 0.8))


@biome('podcast', interior=True)
def podcast(S):
    v = S.variant % 3
    rng = S.rng
    wall = ['#5a5f6a', '#8a4a3a', '#3a4a44'][v]
    shell(S, wall=wall, floor='#6a4a34', fy=0.76, kind='planks')
    sky_ = S.L('sky')
    if v == 1:  # brick wall
        with sky_.piece(0.4) as d:
            for j in range(26):
                for i in range(30):
                    x = i * 0.036 + (j % 2) * 0.018 - 0.02
                    d.rect(x, j * 0.029, x + 0.033, j * 0.029 + 0.025, mixc('#a8543e', '#8a4030', ((i * 7 + j * 13) % 9) / 9), r=0.002)
    far = S.L('far')
    if v == 0:
        foam_wall(far, 0.04, 0.1, 0.4, 0.62, '#3a3a44', n=5)
        foam_wall(far, 0.6, 0.1, 0.96, 0.62, '#3a3a44', n=5)
    elif v == 1:
        foam_wall(far, 0.3, 0.12, 0.7, 0.5, '#2e2e36', n=6)
        shelf(far, 0.04, 0.24, 0.3, rng)
        shelf(far, 0.04, 0.24, 0.5, rng)
        plant(far, 0.86, 0.6, 1.4)
        with far.piece(0.7) as d:  # framed records
            for x in (0.78, 0.9):
                d.rect(x - 0.045, 0.16, x + 0.045, 0.32, '#1e1e26', r=0.003)
                d.circ(x, 0.24, 0.06, '#121218')
                d.circ(x, 0.24, 0.018, ['#e05a5a', '#f6c453'][x > 0.8])
    else:  # cosy: bookcase wall with a warm lamp
        with far.piece(0.8) as d:
            d.rect(0.02, 0.06, 0.3, 0.74, '#5a3a24', r=0.006)
            d.rect(0.7, 0.06, 0.98, 0.74, '#5a3a24', r=0.006)
        for y in (0.2, 0.34, 0.48, 0.62):
            shelf(far, 0.03, 0.29, y, rng)
            shelf(far, 0.71, 0.97, y, rng)
        foam_wall(far, 0.34, 0.14, 0.66, 0.46, '#4a5a54', n=5)
    with far.piece(0.6) as d:  # the 'on air' lamp: a red circle, no text
        lx = 0.5
        ly = 0.08 if v != 1 else 0.07
        d.circ(lx, ly, 0.032, '#2a2a30')
        d.circ(lx, ly, 0.024, '#ff3a2e', lit=True)
    far.glow_circ(lx, ly, 0.04)
    mid = S.L('mid')
    tcol = ['#b07a4a', '#3a3a44', '#8a5a3a'][v]
    chair(mid, 0.31, 0.78, 1.7, col=['#3a3a44', '#e9a23a', '#3f6f6a'][v], office=True, face=-1)
    chair(mid, 0.69, 0.78, 1.7, col=['#3a3a44', '#e9a23a', '#3f6f6a'][v], office=True, face=1)
    with mid.piece(1.0) as d:  # round table
        d.ell(0.5, 0.64, 0.24, 0.035, tcol)
        d.rect(0.488, 0.64, 0.512, 0.76, shade(tcol, 0.7))
        d.ell(0.5, 0.76, 0.08, 0.01, shade(tcol, 0.7))
    with mid.piece(0.7) as d:
        d.rect(0.46, 0.6, 0.54, 0.63, '#2a2a30', r=0.004)  # mixer
        for k in range(5):
            d.rect(0.467 + k * 0.014, 0.606, 0.472 + k * 0.014, 0.62, '#9a9aa8')
        d.rect(0.6, 0.6, 0.625, 0.635, '#f3efe6', r=0.004)  # mugs
        d.rect(0.38, 0.6, 0.402, 0.632, '#e05a5a', r=0.004)
    headphones(mid, 0.43, 0.632)
    headphones(mid, 0.57, 0.632, col='#2f6fb0')
    ball_mic(mid, 0.4, 0.63, 1.45, face=-1)
    ball_mic(mid, 0.6, 0.63, 1.45, face=1)
    near = S.L('near')
    if v == 2:
        with near.piece(0.8) as d:  # floor lamp, warm
            d.line([(0.07, 0.98), (0.07, 0.56)], '#3a3a40', 0.006)
            d.ell(0.07, 0.98, 0.03, 0.007, '#3a3a40')
            d.poly([(0.04, 0.56), (0.1, 0.56), (0.088, 0.49), (0.052, 0.49)], '#f6e0a0', lit=True)
        near.glow_circ(0.07, 0.53, 0.06)
        plant(near, 0.95, 1.0, 2.2)
    else:
        floor_lamp_softbox(near, 0.06, 1.0, 1.05, face=1)
        plant(near, 0.95, 1.0, 2.0, pot='#3a3a44')
    fg = S.L('fg')
    with fg.piece(0.8) as d:  # a cable snaking on the floor and a boom arm in the corner
        pts = [(0.15 + 0.7 * u, 0.985 + 0.01 * math.sin(u * 12)) for u in np.linspace(0, 1, 40)]
        d.line(pts, '#1e1e26', 0.006)
    return {0: 'podcast studio: grey foam wedges, two ball microphones, a red on-air lamp',
            1: 'podcast studio with a brick wall, records and a foam panel', 2: 'cosy podcast studio between bookcases'}[v]


# ---------------------------------------------------------------- weather studio

def map_land(L, x0, y0, x1, y1, rng, sea='#3f8fcf', land=('#7fbf55', '#a7cf6a', '#d6c27a', '#6aa848')):
    """A felt weather map: sea and soft land blobs, no borders, no names."""
    with L.piece(0.6) as d:
        d.rect(x0, y0, x1, y1, sea, r=0.01)
    w, h = x1 - x0, y1 - y0
    with L.piece(0.7) as d:
        for cx, cy, sx, sy in ((0.3, 0.42, 0.22, 0.3), (0.42, 0.3, 0.18, 0.22), (0.68, 0.55, 0.22, 0.28), (0.78, 0.35, 0.14, 0.16), (0.22, 0.75, 0.1, 0.1)):
            for k in range(7):
                ox, oy = (rng.random() - 0.5) * sx * 0.9, (rng.random() - 0.5) * sy * 0.9
                d.ell(x0 + w * (cx + ox), y0 + h * (cy + oy), h * sx * 0.6 * (0.6 + 0.5 * rng.random()), h * sy * 0.45 * (0.6 + 0.5 * rng.random()), land[k % 2])
    with L.piece(0.5) as d:
        for _ in range(9):  # inner shading: hills and sand
            d.ell(x0 + w * (0.2 + 0.6 * rng.random()), y0 + h * (0.25 + 0.5 * rng.random()), h * 0.06, h * 0.04, land[2 + int(rng.integers(2))])


def sun_icon(d, x, y, r):
    for k in range(8):
        a = k * math.pi / 4
        d.line([(x + math.cos(a) * r * 1.2 / AR, y + math.sin(a) * r * 1.2), (x + math.cos(a) * r * 1.6 / AR, y + math.sin(a) * r * 1.6)], '#f6b23a', r * 0.25)
    d.circ(x, y, r, '#f6c453')


def rain_icon(d, x, y, r):
    cloud(d, x, y, r * 4.0, '#e6ecf2')
    for k in range(3):
        xx, yy = x - r * 0.8 / AR + k * r * 0.8 / AR, y + r * 1.4
        d.circ(xx, yy, r * 0.22, '#5aa0e0')
        d.poly([(xx - r * 0.2 / AR, yy - r * 0.05), (xx + r * 0.2 / AR, yy - r * 0.05), (xx, yy - r * 0.5)], '#5aa0e0')


def snow_icon(d, x, y, r):
    for a in (0, 60, 120):
        t = math.radians(a)
        d.line([(x - math.cos(t) * r / AR, y - math.sin(t) * r), (x + math.cos(t) * r / AR, y + math.sin(t) * r)], '#ffffff', r * 0.22)
    d.circ(x, y, r * 0.25, '#ffffff')


@biome('weather_studio', interior=True)
def weather_studio(S):
    v = S.variant % 3
    rng = S.rng
    wall = ['#2f6fa8', '#3a8a5a', '#2a3a5a'][v]
    shell(S, wall=wall, floor='#3a4050', fy=0.78, kind='carpet', skirting=False)
    sky_ = S.L('sky')
    with sky_.piece(0.4) as d:
        d.ell(0.5, 0.9, 0.5, 0.06, shade(wall, 1.15))  # presenter's spot
        d.ell(0.5, 0.9, 0.12, 0.022, '#f6c453')
        d.ell(0.5, 0.9, 0.09, 0.015, shade(wall, 1.15))
    far = S.L('far')
    if v == 0:  # one big map across the wall
        mx0, my0, mx1, my1 = 0.08, 0.08, 0.92, 0.7
        with far.piece(0.6) as d:
            d.rect(mx0 - 0.012, my0 - 0.02, mx1 + 0.012, my1 + 0.02, '#e9edf0', r=0.012)
        map_land(far, mx0, my0, mx1, my1, rng)
    elif v == 1:  # chroma-green wall with a framed map and a row of forecast cards
        mx0, my0, mx1, my1 = 0.06, 0.1, 0.62, 0.66
        screen(far, mx0, my0, mx1, my1, bezel='#2a2a30', glow=False)
        map_land(far, mx0, my0, mx1, my1, rng, sea='#4a9ad8')
        with far.piece(0.6) as d:  # forecast cards: icon + coloured bar (no digits)
            for k in range(4):
                y = 0.1 + k * 0.145
                d.rect(0.68, y, 0.95, y + 0.125, '#f3efe6', r=0.01)
                d.rect(0.8, y + 0.045, 0.8 + 0.03 + 0.03 * ((k * 3) % 4), y + 0.08, ['#f08a3a', '#f6c453', '#5aa0e0', '#7fb6e8'][k], r=0.006)
        with far.piece(0.5) as d:
            for k, fn in enumerate((sun_icon, rain_icon, snow_icon, sun_icon)):
                y = 0.1 + k * 0.145 + 0.062
                if fn is snow_icon:
                    d.circ(0.73, y, 0.04, '#7fb6e8')
                fn(d, 0.73, y, 0.025 if fn is not rain_icon else 0.012)
    else:  # dark studio with a round globe screen and a wide map
        mx0, my0, mx1, my1 = 0.3, 0.1, 0.95, 0.66
        screen(far, mx0, my0, mx1, my1)
        map_land(far, mx0, my0, mx1, my1, rng, sea='#2f7fc0', land=('#6fb850', '#8fcf6a', '#c9b06a', '#5a9a48'))
        with far.piece(0.7) as d:
            d.circ(0.14, 0.34, 0.17, '#1e2a40')
            d.circ(0.14, 0.34, 0.15, '#3f8fcf', lit=True)
            d.ell(0.12, 0.3, 0.07, 0.06, '#7fbf55', lit=True)
            d.ell(0.18, 0.4, 0.05, 0.05, '#7fbf55', lit=True)
        far.glow_circ(0.14, 0.34, 0.15)
    mid = S.L('mid')
    with mid.piece(0.8) as d:  # weather magnets on the map: clouds, suns, drops, flakes
        if v == 0:
            pts = [(0.25, 0.25, 'sun'), (0.45, 0.2, 'cloud'), (0.62, 0.42, 'rain'), (0.8, 0.28, 'snow'), (0.35, 0.52, 'cloud'), (0.72, 0.6, 'sun')]
        elif v == 1:
            pts = [(0.18, 0.25, 'sun'), (0.38, 0.4, 'rain'), (0.5, 0.2, 'cloud'), (0.25, 0.55, 'cloud')]
        else:
            pts = [(0.42, 0.25, 'cloud'), (0.6, 0.45, 'rain'), (0.78, 0.25, 'sun'), (0.86, 0.5, 'snow'), (0.5, 0.56, 'sun')]
        for x, y, k in pts:
            if k == 'sun':
                sun_icon(d, x, y, 0.035)
            elif k == 'cloud':
                cloud(d, x, y, 0.5, '#f3f6fa')
            elif k == 'rain':
                rain_icon(d, x, y, 0.025)
            else:
                d.circ(x, y, 0.04, '#7fb6e8')
                snow_icon(d, x, y, 0.03)
    with mid.piece(0.9) as d:  # arrows of wind as felt strips
        for x, y in ((0.55, 0.3), (0.3, 0.38)) if v == 0 else ((0.45, 0.5),) if v == 2 else ():
            d.line([(x, y), (x + 0.06, y - 0.02)], '#f3efe6', 0.008)
            d.poly([(x + 0.06, y - 0.035), (x + 0.075, y - 0.025), (x + 0.058, y - 0.005)], '#f3efe6')
    near = S.L('near')
    camera(near, 0.92, 1.0, 1.15, face=-1)
    with near.piece(0.9) as d:  # a monitor on a stand for the presenter
        d.line([(0.08, 0.98), (0.08, 0.74)], '#3a3a40', 0.006)
        d.ell(0.08, 0.98, 0.03, 0.007, '#3a3a40')
        d.rect(0.03, 0.62, 0.13, 0.74, '#2a2a30', r=0.006)
    map_land(near, 0.038, 0.63, 0.122, 0.73, S.rng)
    fg = S.L('fg')
    rig(fg, 0.0, n=6)
    return {0: 'weather studio: a big felt map with no borders, magnet clouds, suns, rain and snow',
            1: 'weather studio with a green wall, a framed map and forecast cards', 2: 'dark weather studio with a globe and a wide map screen'}[v]


# ---------------------------------------------------------------- press room

def mic_cluster(L, x, y, s=1.0, rng=None):
    cols = ['#e05a5a', '#3f7fbf', '#f6c453', '#3d8a5a', '#f3efe6', '#2a2a30', '#b99be0']
    with L.piece(0.8) as d:
        for k in range(7):
            a = -0.9 + k * 0.3
            ex, ey = x + math.sin(a) * 0.06 * s, y - 0.07 * s - abs(math.cos(a)) * 0.03 * s
            d.line([(x, y), (ex, ey)], '#3a3a40', 0.003 * s)
            d.ell(ex, ey, 0.011 * s, 0.016 * s, cols[(k * 3 + int(x * 10)) % len(cols)])


@biome('press_room', interior=True)
def press_room(S):
    v = S.variant % 3
    rng = S.rng
    wall = ['#d9dde4', '#e6e0d4', '#8a6a4a'][v]
    shell(S, wall=wall, floor='#5a5f6a' if v != 2 else '#6a4a34', fy=0.74, kind='carpet' if v != 2 else 'planks', ceiling=0.05)
    far = S.L('far')
    ceiling_panels(far, 0.05, 4, lit=True)
    look = S.look
    if v in (0, 1):  # backdrop panel: plain colour with soft abstract stripes, no emblem
        bc = ['#2a4a7a', '#3a6a5a'][v]
        with far.piece(0.6) as d:
            d.rect(0.18, 0.1, 0.82, 0.66, bc, r=0.008)
        with far.piece(0.4) as d:
            for k in range(5):
                pts = [(0.18 + 0.64 * u, 0.5 + k * 0.03 + 0.05 * math.sin(u * 4 + k * 0.4)) for u in np.linspace(0, 1, 30)]
                d.line(pts, shade(bc, 1.25 + 0.05 * k), 0.008)
    else:  # wood panelling and two tall plain banners
        with far.piece(0.5) as d:
            for k in range(10):
                d.rect(k * 0.1 + 0.005, 0.08, k * 0.1 + 0.095, 0.72, shade(wall, 1.1), r=0.004)
        with far.piece(0.7) as d:
            for x in (0.22, 0.78):
                d.rect(x - 0.06, 0.1, x + 0.06, 0.66, '#3a5a7a', r=0.006)
                d.rect(x - 0.06, 0.6, x + 0.06, 0.66, '#2a4a6a')
    plant(far, 0.1, 0.74, 1.8)
    plant(far, 0.9, 0.74, 1.8)
    mid = S.L('mid')
    if v == 1:  # press conference table with three chairs
        for x in (0.32, 0.5, 0.68):
            chair(mid, x, 0.62, 1.1, col='#2e2e36', office=True)
        with mid.piece(1.0) as d:
            d.rect(0.2, 0.6, 0.8, 0.625, '#f3efe6', r=0.004)
            d.rect(0.21, 0.625, 0.79, 0.78, '#3a5a7a', r=0.004)
        for x in (0.32, 0.5, 0.68):
            mic_cluster(mid, x, 0.6, 0.6, rng)
            glass(mid, x + 0.05, 0.6)
    else:
        for x in ((0.5,) if v == 0 else (0.38, 0.62)):
            with mid.piece(1.0) as d:  # lectern
                d.poly([(x - 0.07, 0.56), (x + 0.07, 0.56), (x + 0.055, 0.8), (x - 0.055, 0.8)], ['#5a3a24', '#5a3a24', '#3a2a1e'][v])
                d.poly([(x - 0.08, 0.545), (x + 0.08, 0.545), (x + 0.07, 0.57), (x - 0.07, 0.57)], shade('#5a3a24', 1.2))
                d.rect(x - 0.04, 0.62, x + 0.04, 0.7, shade('#5a3a24', 1.25), r=0.004)
            mic_cluster(mid, x, 0.55, 1.0, rng)
        side_table(mid, 0.78, 0.78, 0.04, 0.12, col='#e9e4da')
        with mid.piece(0.5) as d:
            d.rect(0.765, 0.6, 0.795, 0.66, (200, 226, 244, 190), r=0.008)
        glass(mid, 0.81, 0.66)
    near = S.L('near')
    camera(near, 0.07, 1.0, 1.0, face=1)
    camera(near, 0.93, 1.0, 1.0, face=-1)
    fg = S.L('fg')
    audience(fg, 0.9, rng, rows=2, n=14, s=1.15, dark=0.5)
    with fg.piece(0.9) as d:  # raised hands with phones and handheld cameras
        for x, y in ((0.2, 0.78), (0.64, 0.8), (0.82, 0.76)):
            d.line([(x, y + 0.14), (x + 0.01, y + 0.03)], '#4a4a5a', 0.014)
            d.rect(x - 0.02, y - 0.03, x + 0.035, y + 0.03, '#2a2a30', r=0.006)
            d.circ(x + 0.008, y, 0.012, '#4a4a54')
    flashes = look.time in ('night', 'dusk') or v == 1
    if flashes:
        with soft(fg, 0.01) as d:
            for x, y in ((0.22, 0.75), (0.83, 0.73)):
                for k in range(8):
                    a = k * math.pi / 4
                    d.line([(x, y), (x + math.cos(a) * 0.05 / AR, y + math.sin(a) * 0.05)], (255, 252, 235, 200), 0.006)
                d.circ(x, y, 0.025, (255, 255, 245, 230))
        for x, y in ((0.22, 0.75), (0.83, 0.73)):
            fg.glow_circ(x, y, 0.05)
    return {0: 'press room: a lectern with a cluster of microphones, a plain blue backdrop, journalists in front',
            1: 'press conference: a long table with three chairs and microphones, camera flashes',
            2: 'wood-panelled press room with two lecterns'}[v]


# ---------------------------------------------------------------- cooking show

def pan(d, x, y, r, col='#c87a4a'):
    d.line([(x, y - r - 0.02), (x, y - r * 0.9)], '#5a3a24', 0.004)
    d.circ(x, y, r, col)
    d.circ(x, y, r * 0.75, shade(col, 0.82))
    d.line([(x, y + r * 0.9), (x, y + r * 2.6)], shade(col, 0.7), r * 0.28)


def jar_row(L, x0, x1, y, rng):
    with L.piece(0.6) as d:
        x = x0
        while x < x1 - 0.02:
            w, h = 0.018 + 0.01 * rng.random(), 0.04 + 0.03 * rng.random()
            c = ['#e9a23a', '#c0443a', '#7cc45e', '#f3ead6', '#8a5a3a', '#f6d353'][int(rng.integers(6))]
            d.rect(x, y - h, x + w, y, (225, 236, 240, 200), r=0.004)
            d.rect(x + 0.002, y - h * 0.7, x + w - 0.002, y - 0.002, c, r=0.003)
            d.rect(x + 0.002, y - h - 0.008, x + w - 0.002, y - h + 0.002, '#8a8f99', r=0.002)
            x += w + 0.006


@biome('cooking_show', interior=True)
def cooking_show(S):
    v = S.variant % 3
    rng = S.rng
    wall = ['#f3efe6', '#e6efe6', '#e9dcc8'][v]
    shell(S, wall=wall, floor='#6a5f58', fy=0.76, kind='tiles', skirting=False)
    sky_ = S.L('sky')
    if v == 2:  # brick back wall
        with sky_.piece(0.4) as d:
            for j in range(16):
                for i in range(30):
                    x = i * 0.036 + (j % 2) * 0.018 - 0.02
                    d.rect(x, 0.08 + j * 0.029, x + 0.033, 0.08 + j * 0.029 + 0.025, mixc('#c9785a', '#b0644a', ((i * 7 + j * 5) % 7) / 7), r=0.002)
    else:
        with sky_.piece(0.4) as d:  # metro tiles
            for j in range(14):
                for i in range(30):
                    x = i * 0.036 + (j % 2) * 0.018 - 0.02
                    d.rect(x, 0.2 + j * 0.026, x + 0.033, 0.2 + j * 0.026 + 0.022, shade(wall, 0.95 if v == 0 else 0.9), r=0.004)
    far = S.L('far')
    cab = ['#3f6f8a', '#3d7a5a', '#8a5a3a'][v]
    with far.piece(0.8) as d:  # upper cabinets at the sides, a rail of pans in the middle
        for x in (0.02, 0.13, 0.78, 0.89):
            d.rect(x, 0.06, x + 0.1, 0.32, cab, r=0.006)
            d.rect(x + 0.01, 0.08, x + 0.09, 0.3, shade(cab, 1.1), r=0.004)
        d.rect(0.3, 0.12, 0.7, 0.13, '#8a8f99')
    with far.piece(0.8) as d:
        for k, x in enumerate((0.34, 0.41, 0.48, 0.55, 0.62, 0.67)):
            pan(d, x, 0.2 + (k % 2) * 0.03, 0.026 + 0.008 * (k % 3), ['#c87a4a', '#d08850', '#b86a3a'][k % 3])
    for y in (0.42, 0.56):
        with far.piece(0.8) as d:
            for x0 in (0.04, 0.78):
                d.rect(x0, y, x0 + 0.18, y + 0.012, '#8a5a3a' if v != 1 else '#f3efe6')
        jar_row(far, 0.05, 0.21, y, rng)
        jar_row(far, 0.79, 0.95, y, rng)
    if v == 2:
        with far.piece(0.7) as d:  # hanging herbs
            for x in (0.32, 0.4, 0.6, 0.68):
                d.line([(x, 0.3), (x, 0.36)], '#5a3a24', 0.002)
                d.ell(x, 0.4, 0.015, 0.04, '#5f9e4e')
    mid = S.L('mid')
    icol = ['#2f4f6a', '#2f5a44', '#6a4630'][v]
    with mid.piece(1.0) as d:  # the island
        d.rect(0.18, 0.6, 0.82, 0.63, '#e9e6e0' if v != 2 else '#c9b8a0', r=0.004)
        d.rect(0.19, 0.63, 0.81, 0.82, icol, r=0.006)
        for k in range(4):
            x = 0.21 + k * 0.15
            d.rect(x, 0.65, x + 0.13, 0.8, shade(icol, 1.12), r=0.004)
            d.rect(x + 0.04, 0.665, x + 0.09, 0.672, '#c9cfd6')
    with mid.piece(0.6) as d:  # hob, board with vegetables, pot, bowls
        d.rect(0.25, 0.598, 0.4, 0.612, '#1e1e26', r=0.003)
        for x in (0.285, 0.365):
            d.ell(x, 0.603, 0.025, 0.005, '#3a3a44')
        d.rect(0.27, 0.55, 0.33, 0.6, '#9aa6b0', r=0.006)  # pot
        d.rect(0.26, 0.55, 0.34, 0.558, '#7a8690', r=0.003)
        d.rect(0.48, 0.595, 0.62, 0.605, '#d9b48a', r=0.003)  # board
        for k, c in enumerate(('#e0403a', '#f08a2e', '#7cc45e', '#f6d353')):
            d.circ(0.5 + k * 0.03, 0.585, 0.011, c)
        d.ell(0.7, 0.592, 0.035, 0.012, '#f3efe6')
        d.ell(0.7, 0.586, 0.028, 0.007, '#e9a23a')
    if S.look.lit_share > 0.2 or True:
        with soft(mid, 0.01) as d:  # steam
            for k in range(3):
                d.ell(0.3 + k * 0.012, 0.51 - k * 0.04, 0.02, 0.025, (255, 255, 255, 60))
    near = S.L('near')
    camera(near, 0.06, 1.0, 1.15, face=1)
    plant(near, 0.95, 1.0, 1.8, pot='#e9e6e0')
    fg = S.L('fg')
    rig(fg, 0.0, n=6)
    with fg.piece(0.8) as d:  # overhead camera boom
        d.line([(1.02, 0.3), (0.86, 0.36), (0.8, 0.4)], '#3a3a40', 0.012)
        d.rect(0.76, 0.4, 0.84, 0.46, '#4a4a54', r=0.008)
        d.rect(0.775, 0.46, 0.805, 0.49, '#2e2e36', r=0.004)
        d.circ(0.79, 0.49, 0.012, '#1e1e26')
    return {0: 'cooking show kitchen: an island with a hob, copper pans on a rail, jars, an overhead camera',
            1: 'cooking show kitchen with green cabinets', 2: 'rustic cooking show set: brick wall, wood island, hanging herbs'}[v]


# ---------------------------------------------------------------- pitch stage

@biome('pitch_stage', interior=True)
def pitch_stage(S):
    v = S.variant % 3
    rng = S.rng
    wall = ['#1a1e2e', '#20182e', '#121a24'][v]
    acc = ['#4ad0a0', '#f08a4a', '#5aa0f0'][v]
    shell(S, wall=wall, floor='#24242e', fy=0.72, kind='carpet', skirting=False)
    sky_ = S.L('sky')
    beams(sky_, (0.3, 0.5), top=0.0, bottom=0.82, spread=0.12, col='#fff2c8', a=34, aim=(0.42, 0.5))
    far = S.L('far')
    sx0, sx1 = (0.2, 0.8) if v == 0 else (0.06, 0.62) if v == 1 else (0.34, 0.94)
    screen(far, sx0, 0.08, sx1, 0.52)
    grad_rect(far, sx0, 0.08, sx1, 0.52, '#f6f8fa', '#e0e8f0')
    w = sx1 - sx0
    with far.piece(0.4) as d:  # an upward chart, no text
        d.line([(sx0 + w * 0.08, 0.46), (sx1 - w * 0.05, 0.46)], '#8a8f99', 0.003)
        d.line([(sx0 + w * 0.08, 0.46), (sx0 + w * 0.08, 0.12)], '#8a8f99', 0.003)
        if v == 0:
            for k in range(6):
                bx = sx0 + w * (0.14 + k * 0.13)
                d.rect(bx, 0.46 - (0.05 + 0.05 * k), bx + w * 0.08, 0.46, acc if k == 5 else shade(acc, 1.35), r=0.003)
        else:
            pts = [(sx0 + w * (0.1 + 0.8 * u), 0.43 - 0.27 * u ** 1.8 - 0.02 * math.sin(u * 9)) for u in np.linspace(0, 1, 24)]
            d.line(pts, acc, 0.008)
            ex, ey = pts[-1]
            d.poly([(ex + 0.012, ey - 0.02), (ex - 0.012, ey - 0.005), (ex + 0.008, ey + 0.012)], acc)
            for k in range(5):
                bx = sx0 + w * (0.15 + k * 0.15)
                d.rect(bx, 0.46 - (0.03 + 0.02 * k), bx + w * 0.06, 0.46, shade(acc, 1.5), r=0.002)
    if v == 1:  # a second screen: a pie
        screen(far, 0.7, 0.14, 0.94, 0.46)
        grad_rect(far, 0.7, 0.14, 0.94, 0.46, '#f6f8fa', '#e0e8f0')
        with far.piece(0.4) as d:
            d.pie(0.82, 0.3, 0.12, 0, 230, acc)
            d.pie(0.82, 0.3, 0.12, 230, 300, '#f6c453')
            d.pie(0.82, 0.3, 0.12, 300, 360, '#8a8f99')
    elif v == 2:  # LED dots on the side
        with far.piece(0.4) as d:
            for i in range(8):
                for j in range(12):
                    d.circ(0.04 + i * 0.03, 0.1 + j * 0.035, 0.007, acc if (i + j * 3) % 5 == 0 else '#2a3444', lit=(i + j * 3) % 5 == 0)
    mid = S.L('mid')
    with mid.piece(1.0) as d:  # the stage platform
        d.rect(-0.02, 0.66, 1.02, 0.7, '#3a3a48')
        d.rect(-0.02, 0.7, 1.02, 0.78, '#2a2a34')
    with mid.piece(0.4) as d:
        d.rect(-0.02, 0.695, 1.02, 0.702, acc, lit=True)
    mid.glow_rect(0.0, 0.695, 1.0, 0.702)
    mic_stand(mid, 0.5 if v != 2 else 0.22, 0.68, 1.0)
    with far.piece(0.7) as d:  # tall light pillars at the sides of the stage
        for x in ((0.04, 0.96) if v == 0 else (0.97,) if v == 1 else (0.03, 0.3)):
            d.rect(x - 0.018, 0.06, x + 0.018, 0.68, '#2a2e3a', r=0.006)
    with far.piece(0.3) as d:
        for x in ((0.04, 0.96) if v == 0 else (0.97,) if v == 1 else (0.03, 0.3)):
            d.rect(x - 0.005, 0.08, x + 0.005, 0.66, acc, lit=True)
            far.glow_rect(x - 0.005, 0.08, x + 0.005, 0.66)
    for x in ((0.12, 0.88) if v == 0 else (0.03, 0.62) if v == 1 else (0.4, 0.97)):
        plant(mid, x, 0.67, 1.3, pot='#2e2e36')
    with mid.piece(0.8) as d:  # a small table with a laptop for the slides
        tx = 0.78 if v != 1 else 0.7
        d.rect(tx - 0.05, 0.56, tx + 0.05, 0.575, '#e9e6e0', r=0.003)
        d.rect(tx - 0.004, 0.575, tx + 0.004, 0.68, '#8a8f99')
        d.poly([(tx - 0.03, 0.56), (tx + 0.03, 0.56), (tx + 0.035, 0.52), (tx - 0.025, 0.52)], '#3a3a44')
    near = S.L('near')
    jx = 0.82 if v != 2 else 0.18
    with near.piece(1.0) as d:  # jury table, seen from behind the chairs
        d.rect(jx - 0.18, 0.78, jx + 0.18, 0.8, '#f3efe6', r=0.004)
        d.rect(jx - 0.17, 0.8, jx + 0.17, 0.92, '#3a3a48', r=0.004)
    for k in (-1, 0, 1):
        glass(near, jx + k * 0.11 + 0.03, 0.78)
    with near.piece(1.0) as d:
        for k in (-1, 0, 1):
            x = jx + k * 0.11
            d.rect(x - 0.045, 0.82, x + 0.045, 1.02, '#1e1e26', r=0.02)
            d.rect(x - 0.035, 0.84, x + 0.035, 1.02, '#2e2e36', r=0.015)
    fg = S.L('fg')
    rig(fg, 0.0, n=6)
    return {0: 'pitch-day stage: a screen with rising bars, a mic stand, the jury table in front',
            1: 'pitch stage with a growth line and a pie on two screens', 2: 'pitch stage with an LED wall, the jury on the left'}[v]


# ---------------------------------------------------------------- blogger's desk

def figurine(d, x, y, s, col, head):
    d.rect(x - 0.012 * s, y - 0.035 * s, x + 0.012 * s, y, col, r=0.01 * s)
    d.circ(x, y - 0.045 * s, 0.014 * s, head)
    d.circ(x - 0.005 * s, y - 0.047 * s, 0.002 * s, '#1e1e26')
    d.circ(x + 0.005 * s, y - 0.047 * s, 0.002 * s, '#1e1e26')


@biome('unboxing_desk', interior=True)
def unboxing_desk(S):
    v = S.variant % 3
    rng = S.rng
    wall = ['#f2c4d0', '#d4c4ec', '#bfe4d4'][v]
    shell(S, wall=wall, floor='#e6dcd0', fy=0.8, kind='planks')
    sky_ = S.L('sky')
    with sky_.piece(0.4) as d:  # a soft pattern on the wall
        for i in range(22):
            for j in range(12):
                if (i + j) % 2 == 0:
                    d.circ(i * 0.047 + 0.02, j * 0.065 + 0.03, 0.006, shade(wall, 1.12))
    far = S.L('far')
    if v == 2:  # a pegboard
        with far.piece(0.6) as d:
            d.rect(0.3, 0.08, 0.7, 0.42, '#e9e2d4', r=0.006)
            for i in range(16):
                for j in range(13):
                    d.circ(0.315 + i * 0.024, 0.095 + j * 0.025, 0.003, '#b9b0a0')
        with far.piece(0.8) as d:
            d.circ(0.4, 0.2, 0.04, '#f6c453')
            d.rect(0.5, 0.14, 0.6, 0.26, '#e05a5a', r=0.01)
            d.line([(0.64, 0.12), (0.66, 0.34)], '#3f7fbf', 0.008)
    else:
        with far.piece(0.7) as d:  # a lit strip, a round mirror or an arch
            if v == 0:
                d.circ(0.5, 0.27, 0.17, '#f9dde4')
                d.circ(0.5, 0.27, 0.15, '#fdeef2')
            else:
                d.rect(0.38, 0.1, 0.62, 0.48, '#e9e0f6', r=0.12)
        with far.piece(0.4) as d:
            d.rect(-0.02, 0.04, 1.02, 0.05, '#ffd9f0' if v == 0 else '#c0b0ff', lit=True)
        far.glow_rect(0.0, 0.04, 1.0, 0.05)
    for x0 in (0.04, 0.76):  # shelves with figurines and plants
        for k, y in enumerate((0.22, 0.4, 0.58)):
            with far.piece(0.8) as d:
                d.rect(x0, y, x0 + 0.2, y + 0.012, '#f3efe6')
            with far.piece(0.7) as d:
                for i in range(4):
                    x = x0 + 0.025 + i * 0.05
                    if (i + k) % 3 == 0:
                        d.rect(x - 0.012, y - 0.03, x + 0.012, y, '#c5583e', r=0.004)
                        d.ell(x, y - 0.045, 0.02, 0.022, '#68b456')
                    elif (i + k) % 3 == 1:
                        figurine(d, x, y, 1.0, ['#3f7fbf', '#f6c453', '#e05a5a', '#6fb850'][(i + k) % 4], ['#f6dcc4', '#c99a6a', '#8a5a3a'][(i * 2 + k) % 3])
                    else:
                        d.rect(x - 0.018, y - 0.05, x + 0.018, y, ['#b99be0', '#7fd0c0', '#f28b6b'][(i + k) % 3], r=0.004)
                        d.rect(x - 0.012, y - 0.04, x + 0.012, y - 0.015, (255, 255, 255, 140), r=0.003)
    mid = S.L('mid')
    chair(mid, 0.5, 0.9, 2.1, col=['#f3efe6', '#3a3a44', '#f6c453'][v], office=True)
    # ring lamp on a stand
    rx = 0.27 if v != 1 else 0.73
    with mid.piece(0.8) as d:
        d.line([(rx, 0.8), (rx, 0.42)], '#3a3a40', 0.005)
        d.line([(rx, 0.75), (rx - 0.03, 0.8)], '#3a3a40', 0.004)
        d.line([(rx, 0.75), (rx + 0.03, 0.8)], '#3a3a40', 0.004)
        d.circ(rx, 0.33, 0.1, '#2a2a30')
        d.circ(rx, 0.33, 0.085, (0, 0, 0, 0))
        d.rect(rx - 0.012, 0.31, rx + 0.012, 0.36, '#2a2a30', r=0.003)  # phone holder
    with mid.piece(0.3) as d:
        d.circ(rx, 0.33, 0.094, '#fffaf0', lit=True)
        d.circ(rx, 0.33, 0.086, (0, 0, 0, 0))
        d.rect(rx - 0.012, 0.31, rx + 0.012, 0.36, '#2a2a30', r=0.003)
    with soft(mid, 0.012) as d:  # the ring's glow
        d.circ(rx, 0.33, 0.115, (255, 244, 220, 90))
        d.circ(rx, 0.33, 0.07, (0, 0, 0, 0))
    near = S.L('near')
    dcol = ['#f3efe6', '#e9e0d0', '#d9b48a'][v]
    with near.piece(1.0) as d:  # the desk, low in frame
        d.rect(0.08, 0.8, 0.92, 0.83, dcol, r=0.006)
        d.rect(0.1, 0.83, 0.9, 1.02, shade(dcol, 0.9), r=0.004)
        for x in (0.12, 0.52):
            d.rect(x, 0.85, x + 0.36, 0.92, shade(dcol, 0.96), r=0.006)
            d.rect(x + 0.15, 0.88, x + 0.21, 0.89, '#8a8f99', r=0.002)
    with near.piece(0.8) as d:  # the box, a cutter, tape, packing chips
        bx = 0.62 if v != 1 else 0.3
        d.poly([(bx - 0.08, 0.72), (bx + 0.08, 0.72), (bx + 0.08, 0.8), (bx - 0.08, 0.8)], '#c9965c')
        d.poly([(bx - 0.08, 0.72), (bx - 0.02, 0.67), (bx - 0.01, 0.72)], '#b8854c')
        d.poly([(bx + 0.08, 0.72), (bx + 0.03, 0.665), (bx + 0.015, 0.72)], '#b8854c')
        d.rect(bx - 0.02, 0.72, bx + 0.02, 0.8, '#d9ae78')
        for k in range(6):
            d.ell(bx - 0.05 + k * 0.02, 0.715 - (k % 2) * 0.006, 0.008, 0.005, '#f6f3ea')
        cx = 0.38 if v != 1 else 0.6
        d.rect(cx, 0.79, cx + 0.06, 0.8, '#f6c453', r=0.003)
        d.rect(cx + 0.04, 0.789, cx + 0.07, 0.797, '#c9cfd6', r=0.002)
        d.circ(cx + 0.12, 0.787, 0.016, '#9aa6b0')
        d.circ(cx + 0.12, 0.787, 0.008, dcol)
    fg = S.L('fg')
    with fg.piece(0.9) as d:  # a stack of parcels waiting in the corner
        for (x0, y0, x1, y1, c) in ((0.86, 0.86, 1.03, 1.03, '#c9965c'), (0.88, 0.74, 1.01, 0.86, '#b8854c'), (0.9, 0.66, 0.99, 0.74, '#d9ae78')):
            d.rect(x0, y0, x1, y1, c, r=0.004)
            d.rect((x0 + x1) / 2 - 0.008, y0, (x0 + x1) / 2 + 0.008, y1, '#e9cfa0')
    plant(fg, 0.04, 1.02, 2.4)
    return {0: 'blogger desk: pink wall, ring lamp, a cardboard box being opened, shelves of figurines',
            1: 'blogger desk with a lilac wall and an arch', 2: 'blogger desk with a mint wall and a pegboard'}[v]


# ---------------------------------------------------------------- wedding hall (toi)

def chandelier(L, x, y, s=1.0, metal='#d9b45a'):
    on = True
    with L.piece(0.7) as d:
        d.line([(x, 0.0), (x, y - 0.05 * s)], metal, 0.003)
        d.ell(x, y, 0.07 * s, 0.018 * s, metal)
        for k in range(7):
            u = (k - 3) / 3
            d.line([(x + u * 0.06 * s, y), (x + u * 0.07 * s, y + 0.05 * s)], metal, 0.002)
            d.ell(x + u * 0.07 * s, y + 0.055 * s, 0.006 * s, 0.01 * s, '#fff6dc', lit=on)
        d.ell(x, y - 0.035 * s, 0.035 * s, 0.012 * s, metal)
        for k in range(5):
            u = (k - 2) / 2
            d.circ(x + u * 0.035 * s, y - 0.045 * s, 0.006 * s, '#fff6dc', lit=on)
    L.glow_circ(x, y + 0.02, 0.06 * s)


def balloons(L, x, y, s, cols, rng):
    with L.piece(0.9) as d:
        for k in range(5):
            bx, by = x + (rng.random() - 0.5) * 0.04 * s, y - 0.06 * s - rng.random() * 0.06 * s
            d.line([(x, y + 0.08 * s), (bx, by)], '#c9c4b8', 0.0015)
            d.ell(bx, by, 0.022 * s, 0.027 * s, cols[k % len(cols)])
            d.ell(bx - 0.007 * s, by - 0.01 * s, 0.005 * s, 0.007 * s, (255, 255, 255, 120))


def ornament_band(L, x0, x1, y, h, col, bg):
    """A geometric band of rhombi and hooks (felt appliqué), no symbols."""
    with L.piece(0.6) as d:
        d.rect(x0, y, x1, y + h, bg)
        n = max(2, int((x1 - x0) / (h * 1.2 / AR)))
        w = (x1 - x0) / n
        for k in range(n):
            cx = x0 + (k + 0.5) * w
            d.poly([(cx, y + h * 0.15), (cx + w * 0.32, y + h * 0.5), (cx, y + h * 0.85), (cx - w * 0.32, y + h * 0.5)], col)
            d.circ(cx, y + h * 0.5, h * 0.12, bg)


def banquet_table(L, x0, x1, y, rng, cloth='#f8f5ee', skirt=None):
    """A long table in front view: cloth, plates, dishes of fruit and bread, tea bowls, bottles of juice."""
    with L.piece(1.0) as d:
        d.rect(x0, y - 0.01, x1, y + 0.012, cloth, r=0.004)
        d.rect(x0 + 0.005, y + 0.012, x1 - 0.005, y + 0.11, skirt or shade(cloth, 0.94), r=0.004)
        for k in range(int((x1 - x0) / 0.03)):
            xx = x0 + 0.01 + k * 0.03
            d.rect(xx, y + 0.015, xx + 0.004, y + 0.11, shade(skirt or cloth, 0.88))
    with L.piece(0.6) as d:
        x = x0 + 0.03
        while x < x1 - 0.03:
            kind = rng.random()
            if kind < 0.3:  # fruit platter
                d.ell(x, y - 0.006, 0.03, 0.007, '#f3efe6')
                for i in range(4):
                    d.circ(x - 0.012 + i * 0.008, y - 0.016 - (i % 2) * 0.006, 0.009, ['#e0403a', '#f6d353', '#7cc45e', '#a04a8a'][i])
            elif kind < 0.5:  # round bread
                d.ell(x, y - 0.012, 0.024, 0.012, '#d9a05a')
                d.ell(x, y - 0.014, 0.012, 0.006, '#e9b878')
            elif kind < 0.7:  # tea bowls
                for i in range(2):
                    d.pie(x - 0.012 + i * 0.024, y - 0.008, 0.012, 0, 180, '#f3efe6')
                    d.rect(x - 0.02 + i * 0.024, y - 0.01, x - 0.004 + i * 0.024, y - 0.006, '#3f6fb0')
            elif kind < 0.85:  # a juice jug
                d.rect(x - 0.008, y - 0.05, x + 0.008, y - 0.002, (240, 200, 120, 220), r=0.006)
            else:  # a pyramid of small fried dough pieces
                for i, (dx, dy) in enumerate(((-0.012, 0), (0, 0), (0.012, 0), (-0.006, -0.012), (0.006, -0.012), (0, -0.024))):
                    d.circ(x + dx, y - 0.01 + dy, 0.007, '#d99a4a')
            x += 0.04 + 0.025 * rng.random()


@biome('wedding_hall', interior=True)
def wedding_hall(S):
    v = S.variant % 3
    rng = S.rng
    wall = ['#f2e6cc', '#e6eef4', '#f0dcd4'][v]
    gold = '#d9b45a'
    drape_c = ['#e9d6a8', '#9cc0e0', '#8a2a3a'][v]
    shell(S, wall=wall, floor='#c9a878' if v != 2 else '#9a7a5a', fy=0.72, kind='planks', ceiling=0.04)
    sky_ = S.L('sky')
    with sky_.piece(0.4) as d:  # columns of light panels and the aisle runner to the stage
        for x in (0.06, 0.94):
            d.rect(x - 0.03, 0.04, x + 0.03, 0.7, shade(wall, 0.94), r=0.006)
        d.poly([(0.4, 0.72), (0.6, 0.72), (0.74, 1.02), (0.26, 1.02)], shade(drape_c, 0.85))
        d.poly([(0.415, 0.72), (0.585, 0.72), (0.71, 1.02), (0.29, 1.02)], shade(drape_c, 1.05))
    far = S.L('far')
    # the stage at the back with a drape arch
    with far.piece(0.6) as d:
        d.rect(0.3, 0.06, 0.7, 0.62, shade(drape_c, 1.25), r=0.01)
    drape(far, 0.3, 0.4, 0.06, 0.62, drape_c, folds=4)
    drape(far, 0.6, 0.7, 0.06, 0.62, drape_c, folds=4)
    with far.piece(0.7) as d:  # swag across the top
        for k in range(4):
            d.pie(0.35 + k * 0.1, 0.06, 0.06, 0, 180, shade(drape_c, 0.92))
    ornament_band(far, 0.3, 0.7, 0.05, 0.035, gold, shade(drape_c, 0.7))
    with far.piece(0.6) as d:  # backdrop: a soft round with a flower ring and an inner felt pattern
        d.circ(0.5, 0.33, 0.17, shade(drape_c, 1.4))
        d.circ(0.5, 0.33, 0.13, shade(drape_c, 1.25))
        for k in range(8):
            a = 2 * math.pi * k / 8
            d.ell(0.5 + 0.075 * math.cos(a) / AR, 0.33 + 0.075 * math.sin(a), 0.022, 0.022, gold)
        d.circ(0.5, 0.33, 0.035, shade(drape_c, 1.4))
        d.circ(0.5, 0.33, 0.018, gold)
        for k in range(28):
            a = 2 * math.pi * k / 28
            d.circ(0.5 + 0.17 * math.cos(a) / AR, 0.33 + 0.17 * math.sin(a), 0.016, ['#f6f3ea', '#f2b6c9', '#e9d6a8'][k % 3])
    with far.piece(0.9) as d:  # the stage platform
        d.rect(0.26, 0.62, 0.74, 0.67, shade(drape_c, 0.7), r=0.004)
        d.rect(0.25, 0.61, 0.75, 0.625, gold)
    mic_stand(far, 0.56, 0.62, 0.8)
    with far.piece(0.8) as d:  # flower urns at the stage corners
        for x in (0.28, 0.72):
            d.poly([(x - 0.02, 0.61), (x + 0.02, 0.61), (x + 0.012, 0.56), (x - 0.012, 0.56)], gold)
            for k in range(6):
                d.circ(x + (k - 2.5) * 0.008, 0.545 - (k % 2) * 0.012, 0.014, ['#f6f3ea', '#f2b6c9', '#e05a7a'][k % 3])
    for x in (0.12, 0.3, 0.7, 0.88):
        chandelier(far, x, 0.13 if x in (0.12, 0.88) else 0.12, 1.0)
    mid = S.L('mid')
    cloth = ['#fbf8f0', '#fbfbfb', '#fbf4f0'][v]
    skirt = ['#efe2c0', '#d8e6f2', '#e8c8c8'][v]
    banquet_table(mid, -0.02, 0.36, 0.7, rng, cloth, skirt)
    banquet_table(mid, 0.64, 1.02, 0.7, rng, cloth, skirt)
    with mid.piece(0.9) as d:  # chair backs with bows along the tables
        for x in list(np.arange(0.02, 0.34, 0.07)) + list(np.arange(0.68, 1.0, 0.07)):
            d.rect(x - 0.016, 0.62, x + 0.016, 0.69, '#f8f5ee', r=0.01)
            d.ell(x, 0.655, 0.012, 0.008, ['#e9c46a', '#7fb6e8', '#c0445a'][v])
    bc = [['#f6f3ea', '#e9c46a', '#f2b6c9'], ['#ffffff', '#9cc0e0', '#d9b45a'], ['#c0445a', '#f6f3ea', '#d9b45a']][v]
    balloons(mid, 0.2, 0.6, 1.2, bc, rng)
    balloons(mid, 0.8, 0.6, 1.2, bc, rng)
    near = S.L('near')
    with near.piece(1.0) as d:  # the cake on a little round table at the left
        d.ell(0.12, 0.84, 0.07, 0.012, cloth)
        d.rect(0.06, 0.84, 0.18, 0.98, skirt, r=0.006)
        d.rect(0.075, 0.76, 0.165, 0.835, '#fbf8f0', r=0.008)
        d.rect(0.088, 0.7, 0.152, 0.765, '#fbf8f0', r=0.008)
        d.rect(0.1, 0.65, 0.14, 0.705, '#fbf8f0', r=0.008)
    with near.piece(0.6) as d:
        for y in (0.79, 0.73, 0.675):
            d.rect(0.075 + (0.79 - y) * 0.2, y, 0.165 - (0.79 - y) * 0.2, y + 0.008, gold)
        for k in range(3):
            d.circ(0.11 + k * 0.01, 0.645, 0.008, ['#f2b6c9', '#e05a7a', '#f2b6c9'][k])
    with near.piece(1.0) as d:  # a corner of a guest table at the right
        d.rect(0.84, 0.86, 1.04, 0.88, cloth, r=0.004)
        d.rect(0.845, 0.88, 1.04, 1.02, skirt)
    with near.piece(0.6) as d:
        d.ell(0.9, 0.855, 0.03, 0.008, '#f3efe6')
        d.ell(0.97, 0.85, 0.025, 0.012, '#d9a05a')
    fg = S.L('fg')
    with fg.piece(0.8) as d:  # a draped garland across the top
        pts = [(u, 0.02 + 0.05 * math.sin(math.pi * ((u * 3) % 1))) for u in np.linspace(0, 1, 60)]
        d.line(pts, shade(drape_c, 0.9), 0.022)
        for k in range(4):
            d.circ(k / 3, 0.02, 0.022, gold)
    return {0: 'toi banquet hall in cream and gold: a stage with drapes and a mic, long tables, chandeliers, a cake',
            1: 'wedding hall in white and sky blue', 2: 'wedding hall in burgundy and gold'}[v]


# ---------------------------------------------------------------- aquarium studio

@biome('aquarium_studio', interior=True)
def aquarium_studio(S):
    v = S.variant % 3
    rng = S.rng
    wall = ['#121a2e', '#0e2428', '#1e1430'][v]
    shell(S, wall=wall, floor='#1a1e2a', fy=0.76, kind='carpet', skirting=False)
    sky_ = S.L('sky')
    bokeh(sky_, 0.0, 0.05, 1.0, 0.7, rng, n=40, cols=(['#5aa0f0', '#9fd0ff'], ['#4ad0c0', '#a0f0e0'], ['#b080f0', '#f0a0d0'])[v], rmin=0.01, rmax=0.04)
    beams(sky_, (0.5,), top=0.0, bottom=0.82, spread=0.2, col='#bfe4ff', a=30)
    far = S.L('far')
    with far.piece(0.6) as d:  # side light towers
        for x in (0.06, 0.94):
            d.rect(x - 0.025, 0.1, x + 0.025, 0.74, '#1a2236', r=0.006)
    with far.piece(0.3) as d:
        for x in (0.06, 0.94):
            for j in range(9):
                d.circ(x, 0.14 + j * 0.07, 0.01, ['#5aa0f0', '#4ad0c0', '#b080f0'][v], lit=True)
                far.glow_circ(x, 0.14 + j * 0.07, 0.015)
    mid = S.L('mid')
    cx = [0.5, 0.42, 0.58][v]
    hw, top, bot = 0.17, 0.26, 0.82
    with mid.piece(0.9) as d:  # plinth
        d.rect(cx - hw - 0.015, bot, cx + hw + 0.015, bot + 0.03, '#2a2e3a', r=0.004)
    with mid.piece(0.6) as d:  # the water
        d.rect(cx - hw, top + 0.05, cx + hw, bot, (70, 150, 210, 150))
        d.rect(cx - hw, top + 0.05, cx + hw, top + 0.065, (170, 220, 250, 190))
    with mid.piece(0.5) as d:  # sand on the bottom and a strand of weed
        d.ell(cx, bot - 0.005, hw * AR * 0.98, 0.025, (220, 196, 140, 230))
        wx = cx + hw * 0.6
        pts = [(wx + 0.012 * math.sin(u * 9), bot - 0.01 - 0.4 * u) for u in np.linspace(0, 1, 30)]
        d.line(pts, (80, 160, 90, 240), 0.007)
        for k in range(5):
            x, y = pts[6 + k * 5]
            d.ell(x + 0.012 * (1 if k % 2 else -1), y, 0.012, 0.007, (90, 175, 100, 240))
    armchair(mid, cx - 0.03, bot - 0.02, 1.0, col=['#e05a5a', '#f6c453', '#f3efe6'][v], face=1)
    with mid.piece(0.4) as d:  # bubbles
        for _ in range(26):
            x = cx - hw + 0.02 + (2 * hw - 0.04) * rng.random()
            y = top + 0.08 + (bot - top - 0.12) * rng.random()
            r = 0.004 + 0.008 * rng.random() ** 2
            d.circ(x, y, r, (220, 240, 255, 200))
            d.circ(x - r * 0.3 / AR, y - r * 0.3, r * 0.35, (255, 255, 255, 230))
    with mid.piece(0.5) as d:  # the glass: edges and highlights
        d.rect(cx - hw, top, cx + hw, bot, (200, 230, 250, 26))
        for x0, x1 in ((cx - hw, cx - hw + 0.004), (cx + hw - 0.004, cx + hw)):
            d.rect(x0, top, x1, bot, (220, 240, 255, 200))
        d.rect(cx - hw, top, cx + hw, top + 0.004, (220, 240, 255, 200))
        d.poly([(cx - hw + 0.02, top + 0.02), (cx - hw + 0.04, top + 0.02), (cx - hw + 0.02, top + 0.26)], (255, 255, 255, 90))
        d.poly([(cx + hw - 0.05, bot - 0.02), (cx + hw - 0.03, bot - 0.02), (cx + hw - 0.03, bot - 0.2)], (255, 255, 255, 70))
    mid.glow_rect(cx - hw, top + 0.05, cx + hw, top + 0.07)
    near = S.L('near')
    camera(near, 0.08 if v != 1 else 0.92, 1.0, 1.2, face=1 if v != 1 else -1)
    with near.piece(0.8) as d:  # a hose and a pump box beside the tank
        px = cx + hw + 0.06 if v != 2 else cx - hw - 0.06
        d.rect(px - 0.03, 0.8, px + 0.03, 0.86, '#3a3a48', r=0.006)
        d.circ(px, 0.83, 0.008, '#4ad0a0', lit=True)
        d.line([(px, 0.8), (px, 0.7), (cx + (hw if px > cx else -hw), top + 0.06)], '#5a6a7a', 0.006)
    fg = S.L('fg')
    rig(fg, 0.0, n=5)
    with soft(fg, 0.02) as d:  # wavy light from the water on the floor
        for k in range(6):
            d.ell(cx + (k - 2.5) * 0.06, 0.92 + 0.02 * (k % 2), 0.05, 0.008, (150, 210, 250, 50))
    return {0: 'guest in an aquarium: a glass cube of water with an armchair, bubbles and a strand of weed, dark blue studio',
            1: 'aquarium-cube studio, teal light', 2: 'aquarium-cube studio, violet light'}[v]
