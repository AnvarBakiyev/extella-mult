"""Interiors as layered plates. sky = back wall and floor (with windows showing the time of day outside),
far = things on the wall, mid = furniture against the wall, near = furniture in front, fg = framing props."""
import math

import numpy as np
from PIL import Image

from plates import AR, W, H, shade, mixc, hx, to255, sky_gradient, Look, FL, S_FELT
from scenes import biome
from props import bush

WOOD = '#b98a5e'


# ---------------------------------------------------------------- room shell

def shell(S, wall='#efe2c8', floor='#c99a6a', fy=0.74, kind='planks', skirting=True, ceiling=None):
    """Back wall (flat colour with a soft vertical light), floor from fy down, in the sky layer (opaque)."""
    L = S.L('sky')
    w = S.look.col(wall)
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    xx = np.linspace(0, 1, W, dtype=np.float32)[None, :, None]
    light = 1.04 - 0.1 * np.abs(xx - 0.5) - 0.06 * yy
    img = np.broadcast_to(w[None, None, :] * light, (H, W, 3)).copy().astype(np.float32)
    # felt v2+: the wall is sheets of felted wool laid side by side (soft seams), heathered, with micro-fibres
    img = FL.felt_panels(img, S_FELT, seed=S.seed * 3 + S.variant, every=0.19 + 0.06 * (S.variant % 3), y1=fy)
    img = FL.wool_field(img, S_FELT, seed=S.seed * 17 + S.variant, strength=1.0, scale=2.0, streaks=0.25)
    L.base = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8), 'RGB').convert('RGBA')
    if ceiling:
        with L.piece(0.5) as d:
            d.rect(-0.02, -0.02, 1.02, ceiling, shade(wall, 0.9))
    with L.piece(0.4, kind={'carpet': 'knit'}.get(kind, 'ground')) as d:
        d.rect(-0.02, fy, 1.02, 1.02, floor)
        if kind == 'planks':
            for k in range(1, 8):
                y = fy + (1 - fy) * (k / 8) ** 1.3
                d.rect(-0.02, y, 1.02, y + 0.003, shade(floor, 0.88))
        elif kind == 'tiles':
            for k in range(1, 6):
                y = fy + (1 - fy) * (k / 6) ** 1.2
                d.rect(-0.02, y, 1.02, y + 0.003, shade(floor, 0.9))
            for k in range(-10, 22):
                x = 0.5 + k * 0.06
                d.line([(0.5 + (x - 0.5) * 0.5, fy), (0.5 + (x - 0.5) * 1.3, 1.02)], shade(floor, 0.9), 0.003)
        elif kind == 'carpet':
            pass
    if skirting:
        with L.piece(0.4) as d:
            d.rect(-0.02, fy - 0.02, 1.02, fy, shade(wall, 0.8))
    return L


def window_view(S, L, x0, y0, x1, y1, view='city', frame='#f6f3ea', bars=2, depth=1.0, moving=False):
    """A window: sky by time of day and a little outside view, with a frame."""
    look = S.look
    cs = look.sky_cols() if look.time != 'night' or True else None
    c0, c1, c2 = cs
    ys = np.linspace(0, 1, max(2, int((y1 - y0) * H)), dtype=np.float32)[:, None]
    col = c0 * (1 - ys[..., None]) + c2 * ys[..., None]
    w = max(2, int((x1 - x0) * W))
    arr = np.broadcast_to(col, (len(ys), w, 3))
    patch = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), 'RGB').convert('RGBA')
    L.base.paste(patch, (int(x0 * W), int(y0 * H)))
    rng = S.rng
    out = Look(look.time, look.weather, look.season, look.palette, interior=False)

    def O(c, hz=0.25):  # outdoor colours graded for the time of day, not for the room light
        return to255(out.col(c, hz))
    with L.piece(0.4 * depth) as d:
        if view == 'city':
            x = x0
            while x < x1:
                bw = 0.02 + 0.03 * rng.random()
                bh = (y1 - y0) * (0.2 + 0.5 * rng.random())
                d.rect(x, y1 - bh, min(x + bw, x1), y1, O('#a3aac4'))
                x += bw + 0.002
        elif view == 'trees':
            for k in range(5):
                cx = x0 + (x1 - x0) * (k + 0.5) / 5
                d.circ(cx, y1 - (y1 - y0) * 0.25, (y1 - y0) * 0.22, O('#6fae5e' if S.season != 'winter' else '#e6ecf2'))
        elif view == 'tunnel':
            d.rect(x0, y0, x1, y1, '#1a1a22')
            for k in range(3):
                yy = y0 + (y1 - y0) * (0.3 + 0.2 * k)
                d.rect(x0, yy, x1, yy + 0.004, '#3a3a44')
        elif view == 'clouds':
            d.rect(x0, y0 + (y1 - y0) * 0.6, x1, y1, O('#f3f6fa', 0.1))
    if view == 'city' and look.lit_share > 0.2:
        with L.piece(0.3) as d:
            for _ in range(int((x1 - x0) * 300)):
                xx, yy = x0 + (x1 - x0) * rng.random(), y0 + (y1 - y0) * (0.55 + 0.42 * rng.random())
                if rng.random() < 0.5:
                    d.rect(xx, yy, xx + 0.003, yy + 0.005, '#ffd36e', lit=True)
    # frame on the far layer, so the view slides behind it
    F = S.L('far')
    with F.piece(0.8 * depth) as d:
        t = 0.012
        d.rect(x0 - t, y0 - t, x1 + t, y0 + 0.004, frame)
        d.rect(x0 - t, y1 - 0.004, x1 + t, y1 + t, frame)
        d.rect(x0 - t, y0 - t, x0 + 0.004, y1 + t, frame)
        d.rect(x1 - 0.004, y0 - t, x1 + t, y1 + t, frame)
        for k in range(1, bars):
            x = x0 + (x1 - x0) * k / bars
            d.rect(x - 0.004, y0, x + 0.004, y1, frame)


def lamp_pendant(L, x, y, s=1.0, col='#f6c453', cord=0.0):
    with L.piece(0.6) as d:
        d.line([(x, cord), (x, y - 0.03 * s)], '#3a3a40', 0.002)
        d.pie(x, y, 0.045 * s, 180, 360, col)
    on = L.look.lit_share > 0.2 or L.look.time in ('night', 'dusk')
    with L.piece(0.4) as d:
        d.ell(x, y, 0.02 * s, 0.008 * s, '#fff2c0' if on else '#e9e2c8', lit=on)
    if on:
        L.glow_circ(x, y + 0.01, 0.06 * s)


def ceiling_panels(L, y, n=4, lit=None):
    on = L.look.lit_share > 0.2 if lit is None else lit
    with L.piece(0.4) as d:
        for k in range(n):
            x = (k + 0.5) / n
            d.rect(x - 0.08, y, x + 0.08, y + 0.012, '#fbf6e6' if on else '#e6e6e6', lit=on or None)
            if on:
                L.glow_rect(x - 0.08, y, x + 0.08, y + 0.012)


def picture(L, x, y, w, h, rng, frame='#8a5a3a'):
    with L.piece(0.7) as d:
        d.rect(x - w / 2, y - h / 2, x + w / 2, y + h / 2, frame, r=0.003)
        d.rect(x - w / 2 + 0.008, y - h / 2 + 0.012, x + w / 2 - 0.008, y + h / 2 - 0.012, '#cfe6f2')
        # a simple landscape: hills and a sun
        d.ell(x - w * 0.1, y + h * 0.35, w * 0.4 * AR, h * 0.3, '#8fcf6a')
        d.ell(x + w * 0.2, y + h * 0.4, w * 0.35 * AR, h * 0.25, '#6fb850')
        d.circ(x + w * 0.25, y - h * 0.18, h * 0.1, '#f6c453')


def clock(L, x, y, r=0.035):
    with L.piece(0.7) as d:
        d.circ(x, y, r, '#3a3a40')
        d.circ(x, y, r * 0.85, '#fbfbf6')
        d.line([(x, y), (x, y - r * 0.6)], '#2a2a30', 0.004)
        d.line([(x, y), (x + r * 0.45 / AR, y + r * 0.1)], '#2a2a30', 0.004)


def shelf(L, x0, x1, y, rng, books=True):
    with L.piece(0.7) as d:
        d.rect(x0, y, x1, y + 0.012, '#8a5a3a')
    if books:
        with L.piece(0.6) as d:
            x = x0 + 0.005
            while x < x1 - 0.02:
                w, h = 0.008 + 0.008 * rng.random(), 0.05 + 0.03 * rng.random()
                d.rect(x, y - h, x + w, y, ['#c0443a', '#2f6fb0', '#3d8a5a', '#e9a23a', '#8a3a6a', '#f3ead6'][int(rng.integers(6))], r=0.002)
                x += w + 0.002
                if rng.random() < 0.1:
                    x += 0.02


def plant(L, x, y, s=1.0, pot='#c5583e'):
    with L.piece(0.9) as d:
        for a in (-70, -40, -15, 10, 35, 65):
            ang = math.radians(-90 + a)
            ln = 0.1 * s
            ex, ey = x + math.cos(ang) * ln / AR, y - 0.06 * s + math.sin(ang) * ln
            d.ell((x + ex) / 2, (y - 0.06 * s + ey) / 2, 0.012 * s, 0.05 * s, '#4f9e48' if a % 20 else '#68b456')
    with L.piece(0.9) as d:
        d.poly([(x - 0.03 * s, y - 0.07 * s), (x + 0.03 * s, y - 0.07 * s), (x + 0.022 * s, y), (x - 0.022 * s, y)], pot)
        d.rect(x - 0.034 * s, y - 0.075 * s, x + 0.034 * s, y - 0.062 * s, shade(pot, 0.85))


def desk(L, x0, x1, y, h=0.12, col=WOOD, legs=True, front=False):
    with L.piece(0.9) as d:
        d.rect(x0, y - h, x1, y - h + 0.018, col, r=0.004)
        if front:
            d.rect(x0 + 0.005, y - h + 0.018, x1 - 0.005, y, shade(col, 0.9), r=0.004)
        elif legs:
            for x in (x0 + 0.01, x1 - 0.01):
                d.rect(x - 0.005, y - h + 0.015, x + 0.005, y, shade(col, 0.8))


def chair(L, x, y, s=1.0, col='#3f6fa8', face=1, office=False):
    k = s / AR
    with L.piece(0.9) as d:
        d.rect(x - 0.03 * k, y - 0.07 * s, x + 0.03 * k, y - 0.055 * s, col, r=0.005 * s)
        bx = x - face * 0.028 * k
        d.rect(bx - 0.006 * k, y - 0.15 * s, bx + 0.006 * k, y - 0.06 * s, col, r=0.005 * s)
        if office:
            d.rect(bx - 0.014 * k, y - 0.16 * s, bx + 0.014 * k, y - 0.09 * s, col, r=0.01 * s)
            d.rect(x - 0.003 * k, y - 0.06 * s, x + 0.003 * k, y - 0.012 * s, '#3a3a40')
            d.line([(x - 0.03 * k, y - 0.006 * s), (x + 0.03 * k, y - 0.006 * s)], '#3a3a40', 0.006 * s)
        else:
            for u in (-0.025, 0.025):
                d.rect(x + u * k - 0.003 * k, y - 0.06 * s, x + u * k + 0.003 * k, y, shade(col, 0.75))


def monitor(L, x, y, s=1.0, on=True, rng=None):
    k = s / AR
    with L.piece(0.8) as d:
        d.rect(x - 0.045 * k, y - 0.08 * s, x + 0.045 * k, y - 0.025 * s, '#2e2e36', r=0.004)
        d.rect(x - 0.005 * k, y - 0.027 * s, x + 0.005 * k, y - 0.006 * s, '#4a4a54')
        d.rect(x - 0.02 * k, y - 0.008 * s, x + 0.02 * k, y, '#4a4a54', r=0.002)
    with L.piece(0.4) as d:
        scr = '#7fb6e8' if on else '#3a4048'
        d.rect(x - 0.04 * k, y - 0.075 * s, x + 0.04 * k, y - 0.03 * s, scr, lit=on)
        if on:
            for j in range(3):
                d.rect(x - 0.034 * k, y - 0.068 * s + j * 0.012 * s, x + (0.0 + 0.02 * j) * k, y - 0.063 * s + j * 0.012 * s, '#e9f2fa', lit=True)


def sofa(L, x, y, w, col='#3f8f8a', s=1.0):
    with L.piece(0.9) as d:
        d.rect(x - w / 2, y - 0.2 * s, x + w / 2, y - 0.07 * s, col, r=0.03 * s)
    with L.piece(0.9) as d:
        d.rect(x - w / 2 + 0.01, y - 0.11 * s, x + w / 2 - 0.01, y - 0.03 * s, shade(col, 1.1), r=0.02 * s)
        n = max(2, int(w / 0.13))
        for k in range(1, n):
            xx = x - w / 2 + 0.01 + (w - 0.02) * k / n
            d.rect(xx - 0.002, y - 0.11 * s, xx + 0.002, y - 0.05 * s, shade(col, 0.95))
    with L.piece(0.9) as d:
        for sx in (-1, 1):
            d.rect(x + sx * w / 2 - 0.025, y - 0.14 * s, x + sx * w / 2 + 0.025, y - 0.02 * s, shade(col, 0.92), r=0.02 * s)
        for sx in (-1, 1):
            d.rect(x + sx * (w / 2 - 0.02) - 0.006, y - 0.025 * s, x + sx * (w / 2 - 0.02) + 0.006, y, '#5a3a2a')


def rug(L, x, y, rx, ry, col='#c0443a', col2='#e9a23a'):
    with L.piece(0.3, kind='knit') as d:
        d.ell(x, y, rx, ry, col)
        d.ell(x, y, rx * 0.78, ry * 0.7, col2)
        d.ell(x, y, rx * 0.5, ry * 0.42, col)


def seat_profile(L, x, y, s, col, cover='#e6e2d6'):
    """A passenger seat seen from the side, facing right: a tilted back with a headrest, a cushion, a leg."""
    k = s / AR
    with L.piece(0.7) as d:
        d.rect(x + 0.06 * k, y - 0.1 * s, x + 0.075 * k, y, '#7a7a86')
        d.rect(x + 0.02 * k, y - 0.012 * s, x + 0.12 * k, y, '#7a7a86', r=0.004)
    with L.piece(1.0) as d:
        d.poly([(x, y - 0.13 * s), (x + 0.03 * k, y - 0.4 * s), (x + 0.075 * k, y - 0.4 * s), (x + 0.07 * k, y - 0.13 * s)], col)
        d.ell(x + 0.052 * k, y - 0.4 * s, 0.032 * s, 0.03 * s, col)
    with L.piece(1.0) as d:
        d.rect(x - 0.005 * k, y - 0.15 * s, x + 0.16 * k, y - 0.095 * s, shade(col, 1.12), r=0.022 * s)
        d.rect(x + 0.06 * k, y - 0.2 * s, x + 0.15 * k, y - 0.185 * s, shade(col, 0.8), r=0.006 * s)
    with L.piece(0.5) as d:
        d.ell(x + 0.052 * k, y - 0.405 * s, 0.026 * s, 0.022 * s, cover)


def people_free(L):
    """Plates leave room for characters: nothing is put in the central floor area of the near layer by default."""
    return L


# ---------------------------------------------------------------- interiors

@biome('tv_studio', interior=True)
def tv_studio(S):
    v = S.variant % 3
    rng = S.rng
    wallc = ['#2a2f4a', '#3a2a4a', '#1f3a4a'][v]
    shell(S, wall=wallc, floor='#3a3a48', fy=0.76, kind='carpet', skirting=False)
    far = S.L('far')
    with far.piece(0.6) as d:  # big screen with abstract shapes, panels around
        d.rect(0.28, 0.12, 0.72, 0.52, '#1a1a24', r=0.01)
        d.rect(0.295, 0.135, 0.705, 0.505, ['#3f7fbf', '#c0443a', '#3d8a8a'][v], lit=True)
    with far.piece(0.4) as d:
        d.circ(0.42, 0.32, 0.1, shade(['#3f7fbf', '#c0443a', '#3d8a8a'][v], 1.3), lit=True)
        d.rect(0.5, 0.25, 0.68, 0.28, '#f3f6fa', lit=True)
        d.rect(0.5, 0.31, 0.64, 0.33, '#f3f6fa', lit=True)
        d.rect(0.5, 0.36, 0.66, 0.38, '#f3f6fa', lit=True)
    far.glow_rect(0.3, 0.14, 0.7, 0.5)
    with far.piece(0.6) as d:
        for k in range(6):
            x = 0.02 + k * 0.04
            d.rect(x, 0.1, x + 0.03, 0.7, shade(wallc, 1.15), r=0.006)
            d.rect(1 - x - 0.03, 0.1, 1 - x, 0.7, shade(wallc, 1.15), r=0.006)
    with far.piece(0.4) as d:
        for k in range(6):
            x = 0.035 + k * 0.04
            for xx in (x, 1 - x - 0.03 + 0.015):
                d.rect(xx - 0.002, 0.12, xx + 0.002, 0.68, '#7fb6e8', lit=True)
    mid = S.L('mid')
    with mid.piece(1.0) as d:  # the anchor desk
        pts = [(0.2 + 0.6 * u, 0.62 + 0.04 * math.sin(math.pi * u)) for u in np.linspace(0, 1, 30)]
        d.poly(pts + [(0.78, 0.8), (0.22, 0.8)], '#e6e6ee')
        d.poly([(x, y + 0.04) for x, y in pts] + [(0.78, 0.7), (0.22, 0.7)], ['#3f7fbf', '#c0443a', '#3d8a8a'][v])
    for x in (0.38, 0.62):
        chair(mid, x, 0.66, 1.0, col='#2e2e36', office=True)
    near = S.L('near')
    with near.piece(0.8) as d:  # studio cameras on tripods
        for x, fc in ((0.1, 1), (0.9, -1)):
            d.line([(x, 0.98), (x, 0.78)], '#3a3a40', 0.008)
            d.line([(x, 0.8), (x - 0.04, 0.98)], '#3a3a40', 0.006)
            d.line([(x, 0.8), (x + 0.04, 0.98)], '#3a3a40', 0.006)
            d.rect(x - 0.045, 0.7, x + 0.045, 0.78, '#4a4a54', r=0.008)
            d.rect(x + fc * 0.045 - (0.015 if fc > 0 else -0.015), 0.715, x + fc * 0.07, 0.765, '#2e2e36', r=0.006)
            d.circ(x - 0.03, 0.73, 0.006, '#e05a5a', lit=True)
    fg = S.L('fg')
    with fg.piece(0.8) as d:  # light rig
        d.rect(-0.02, 0.02, 1.02, 0.035, '#3a3a40')
        for k in range(7):
            x = 0.07 + k * 0.143
            d.rect(x - 0.025, 0.035, x + 0.025, 0.08, '#2e2e36', r=0.006)
            d.ell(x, 0.08, 0.02, 0.008, '#fff2c0', lit=True)
            fg.glow_circ(x, 0.085, 0.03)
    return {0: 'TV news studio with a blue screen', 1: 'TV studio, red set', 2: 'TV studio, teal set'}[v]


@biome('office', interior=True)
def office(S):
    v = S.variant % 3
    rng = S.rng
    shell(S, wall=['#e6e2da', '#dfe6ea', '#ece0d0'][v], floor='#8f949c', fy=0.7, kind='tiles', ceiling=0.06)
    sky_ = S.L('sky')
    for k in range(3):
        x = 0.06 + k * 0.32
        window_view(S, sky_, x, 0.14, x + 0.26, 0.56, view='city', frame='#d0d4da', bars=3)
    far = S.L('far')
    ceiling_panels(far, 0.06, 4)
    mid = S.L('mid')
    for k in range(4):  # a row of desks with monitors
        x = 0.05 + k * 0.24
        desk(mid, x, x + 0.2, 0.76, h=0.12, col='#e6e2da', front=True)
        monitor(mid, x + 0.06, 0.64, 0.9, on=rng.random() < 0.7, rng=rng)
        monitor(mid, x + 0.14, 0.64, 0.9, on=rng.random() < 0.7, rng=rng)
        with mid.piece(0.5) as d:
            d.rect(x, 0.58, x + 0.2, 0.6, '#9aa6b0')
    near = S.L('near')
    for x in (0.18, 0.66):
        chair(near, x, 0.9, 1.4, col=S.pick(['#3f6fa8', '#2e2e36', '#c0443a']), office=True, face=-1)
    plant(near, 0.95, 0.95, 1.8)
    fg = S.L('fg')
    if v != 1:
        desk(fg, -0.02, 0.28, 1.06, h=0.12, col='#e6e2da', front=True)
        with fg.piece(0.8) as d:  # a mug and papers
            d.rect(0.18, 0.89, 0.21, 0.94, '#f6f3ea', r=0.004)
            d.rect(0.04, 0.93, 0.14, 0.94, '#ffffff')
    return {0: 'open-space office with city windows', 1: 'open-space office, desks and monitors', 2: 'open-space office, warm walls'}[v]


@biome('boss_office', interior=True)
def boss_office(S):
    v = S.variant % 3
    rng = S.rng
    shell(S, wall=['#5a4636', '#3a4656', '#e6dccb'][v], floor='#7a5236', fy=0.74, kind='planks')
    sky_ = S.L('sky')
    window_view(S, sky_, 0.3, 0.1, 0.7, 0.58, view='city', frame='#3a3a40', bars=3)
    far = S.L('far')
    shelf(far, 0.04, 0.24, 0.32, rng)
    shelf(far, 0.04, 0.24, 0.48, rng)
    picture(far, 0.86, 0.32, 0.12, 0.16, rng, frame='#d9b440')
    with far.piece(0.6) as d:  # wood panelling
        for k in range(12):
            x = k * 0.09
            if 0.28 < x < 0.7:
                continue
            d.rect(x, 0.6, x + 0.085, 0.72, shade(['#5a4636', '#3a4656', '#e6dccb'][v], 0.9), r=0.004)
    mid = S.L('mid')
    chair(mid, 0.5, 0.74, 1.6, col='#2e2622', office=True)
    near = S.L('near')
    with near.piece(1.0) as d:  # big desk
        d.rect(0.26, 0.68, 0.74, 0.71, '#5a3a24', r=0.006)
        d.rect(0.28, 0.71, 0.72, 0.92, '#6a4630', r=0.006)
        d.rect(0.3, 0.73, 0.7, 0.9, '#7a5236', r=0.006)
    with near.piece(0.7) as d:
        d.rect(0.32, 0.655, 0.4, 0.68, '#2e2e36', r=0.003)  # closed laptop
        d.rect(0.6, 0.66, 0.66, 0.68, '#f3ead6')
        d.ell(0.45, 0.675, 0.02, 0.006, '#d9b440')
        d.rect(0.535, 0.62, 0.545, 0.68, '#3a3a40')
        d.pie(0.54, 0.62, 0.03, 180, 360, '#3f8f5a')  # desk lamp
    plant(near, 0.9, 0.95, 2.4)
    fg = S.L('fg')
    with fg.piece() as d:  # armchair back for a visitor
        d.rect(0.0, 0.8, 0.18, 1.04, '#8a3a3a', r=0.04)
    return {0: 'boss office with a big desk and a city window', 1: 'boss office, blue walls', 2: 'boss office, light walls'}[v]


@biome('kitchen', interior=True)
def kitchen(S):
    v = S.variant % 3
    rng = S.rng
    wall = ['#f2e6c8', '#d8ecdf', '#f4dccc'][v]
    shell(S, wall=wall, floor='#c9b8a0', fy=0.74, kind='tiles')
    sky_ = S.L('sky')
    window_view(S, sky_, 0.4, 0.14, 0.62, 0.42, view='trees' if v != 1 else 'city')
    far = S.L('far')
    with far.piece(0.5) as d:  # tiles band
        for row in range(4):
            for k in range(30):
                x = k * 0.036 + (row % 2) * 0.018
                if 0.38 < x < 0.64:
                    continue
                d.rect(x, 0.46 + row * 0.04, x + 0.033, 0.497 + row * 0.04, shade(wall, 0.93), r=0.002)
    with far.piece(0.8) as d:  # wall cabinets
        for x in (0.04, 0.16, 0.66, 0.78):
            d.rect(x, 0.12, x + 0.11, 0.36, ['#f6f3ea', '#7fb6a8', '#e9b88a'][v], r=0.006)
            d.circ(x + 0.09, 0.32, 0.005, '#8a8f99')
    clock(far, 0.89, 0.2)
    mid = S.L('mid')
    with mid.piece(1.0) as d:  # counter with base cabinets, stove, fridge
        d.rect(-0.02, 0.6, 0.88, 0.625, '#d0c8bc', r=0.004)
        for x in np.arange(-0.02, 0.86, 0.12):
            d.rect(x + 0.005, 0.625, x + 0.115, 0.76, ['#f6f3ea', '#7fb6a8', '#e9b88a'][v], r=0.006)
        d.rect(0.89, 0.2, 1.02, 0.76, '#e9edf0', r=0.01)
        d.rect(0.89, 0.42, 1.02, 0.425, '#c9cfd6')
    with mid.piece(0.6) as d:
        d.rect(0.5, 0.63, 0.62, 0.75, '#3a3a40', r=0.004)
        d.rect(0.51, 0.64, 0.61, 0.7, '#5a5a66')
        for x in (0.52, 0.6):
            d.ell(x, 0.6, 0.02, 0.004, '#2e2e36')
        d.rect(0.2, 0.555, 0.25, 0.6, '#e05a5a', r=0.01)  # kettle
        d.rect(0.245, 0.565, 0.26, 0.575, '#e05a5a')
        d.ell(0.75, 0.59, 0.04, 0.012, '#f3f6fa')  # bowl of fruit
        for k in range(4):
            d.circ(0.73 + k * 0.012, 0.58, 0.011, S.pick(['#e0403a', '#f6d353', '#7cc45e', '#f08a2e']))
    near = S.L('near')
    with near.piece(1.0) as d:  # table and chairs
        d.rect(0.3, 0.78, 0.72, 0.8, WOOD, r=0.004)
        for x in (0.33, 0.69):
            d.rect(x - 0.006, 0.8, x + 0.006, 0.95, shade(WOOD, 0.8))
    with near.piece(0.7) as d:
        d.ell(0.4, 0.775, 0.03, 0.007, '#f6f3ea')
        d.ell(0.6, 0.775, 0.03, 0.007, '#f6f3ea')
        d.rect(0.48, 0.74, 0.52, 0.78, '#f3f6fa', r=0.004)
    chair(near, 0.22, 0.97, 1.4, col=WOOD, face=-1)
    chair(near, 0.8, 0.97, 1.4, col=WOOD, face=1)
    fg = S.L('fg')
    lamp_pendant(fg, 0.5, 0.18, 1.6)
    return {0: 'home kitchen with a window and a table', 1: 'mint kitchen with a city window', 2: 'warm kitchen with a table'}[v]


@biome('living_room', interior=True)
def living_room(S):
    v = S.variant % 3
    rng = S.rng
    wall = ['#e9dcc0', '#cfdde6', '#e6d0d8'][v]
    shell(S, wall=wall, floor='#b98a5e', fy=0.72)
    sky_ = S.L('sky')
    window_view(S, sky_, 0.62, 0.12, 0.88, 0.5, view='trees')
    far = S.L('far')
    with far.piece(0.6) as d:  # curtains
        d.rect(0.58, 0.08, 0.64, 0.6, '#c0443a' if v != 1 else '#3f6fa8', r=0.01)
        d.rect(0.86, 0.08, 0.92, 0.6, '#c0443a' if v != 1 else '#3f6fa8', r=0.01)
        d.rect(0.56, 0.07, 0.94, 0.085, '#6a4a2a')
    picture(far, 0.3, 0.3, 0.18, 0.14, rng)
    shelf(far, 0.06, 0.2, 0.2, rng)
    mid = S.L('mid')
    sofa(mid, 0.3, 0.74, 0.42, col=['#3f8f8a', '#c9a868', '#8a5a9a'][v])
    with mid.piece(0.8) as d:  # floor lamp
        d.line([(0.06, 0.74), (0.06, 0.42)], '#4a4a54', 0.006)
        d.ell(0.06, 0.74, 0.025, 0.006, '#4a4a54')
        d.poly([(0.035, 0.42), (0.085, 0.42), (0.075, 0.36), (0.045, 0.36)], '#f6e0a0', lit=S.look.lit_share > 0.2)
    if S.look.lit_share > 0.2:
        mid.glow_circ(0.06, 0.4, 0.05)
    with mid.piece(0.9) as d:  # TV stand
        d.rect(0.7, 0.62, 0.95, 0.73, '#6a4630', r=0.004)
        d.rect(0.73, 0.46, 0.92, 0.6, '#1e1e26', r=0.006)
        d.rect(0.81, 0.6, 0.84, 0.62, '#2e2e36')
    near = S.L('near')
    rug(near, 0.45, 0.88, 0.32, 0.06)
    with near.piece(0.9) as d:  # coffee table
        d.rect(0.3, 0.82, 0.58, 0.84, WOOD, r=0.006)
        for x in (0.32, 0.56):
            d.rect(x - 0.006, 0.84, x + 0.006, 0.9, shade(WOOD, 0.8))
        d.rect(0.4, 0.8, 0.43, 0.82, '#f6f3ea')
    plant(near, 0.96, 0.94, 2.0)
    fg = S.L('fg')
    with fg.piece() as d:  # armchair edge
        d.rect(-0.04, 0.78, 0.12, 1.04, ['#c9a868', '#3f8f8a', '#c9a868'][v], r=0.04)
    return {0: 'living room with a sofa and a TV', 1: 'blue living room', 2: 'pink living room'}[v]


@biome('bedroom', interior=True)
def bedroom(S):
    v = S.variant % 3
    rng = S.rng
    wall = ['#d9e4f0', '#f2e0e6', '#e6eedc'][v]
    shell(S, wall=wall, floor='#c99a6a', fy=0.74)
    sky_ = S.L('sky')
    window_view(S, sky_, 0.66, 0.14, 0.88, 0.46, view='trees' if v else 'city')
    far = S.L('far')
    with far.piece(0.4) as d:  # wallpaper dots
        for k in range(60):
            x, y = S.r(0, 1), S.r(0.05, 0.7)
            if 0.62 < x < 0.92 and y < 0.5:
                continue
            d.circ(x, y, 0.005, shade(wall, 0.9))
    picture(far, 0.35, 0.28, 0.14, 0.11, rng)
    mid = S.L('mid')
    with mid.piece(1.0) as d:  # bed
        d.rect(0.12, 0.44, 0.16, 0.8, WOOD, r=0.01)
        d.rect(0.14, 0.62, 0.62, 0.72, shade(WOOD, 0.9), r=0.01)
        d.rect(0.6, 0.56, 0.63, 0.8, WOOD, r=0.008)
    with mid.piece(1.0) as d:
        d.rect(0.16, 0.6, 0.6, 0.64, '#ffffff', r=0.01)
        d.rect(0.24, 0.58, 0.6, 0.67, ['#7fb6e8', '#f2a0b8', '#9ccf7a'][v], r=0.02)
        d.ell(0.2, 0.585, 0.045, 0.025, '#ffffff')
    with mid.piece(0.9) as d:  # nightstand and lamp
        d.rect(0.66, 0.62, 0.76, 0.76, WOOD, r=0.005)
        d.circ(0.73, 0.69, 0.005, '#6a4a2a')
        d.rect(0.705, 0.57, 0.715, 0.62, '#4a4a54')
        d.poly([(0.69, 0.57), (0.73, 0.57), (0.72, 0.535), (0.7, 0.535)], '#f6e0a0', lit=S.look.lit_share > 0.2)
    if S.look.lit_share > 0.2:
        mid.glow_circ(0.71, 0.55, 0.05)
    with mid.piece(0.9) as d:  # wardrobe
        d.rect(0.86, 0.3, 1.02, 0.76, '#e9e2d6' if v != 2 else WOOD, r=0.006)
        d.rect(0.94, 0.3, 0.945, 0.76, '#b9b2a4')
    near = S.L('near')
    rug(near, 0.45, 0.88, 0.25, 0.05, col='#8a6ac8', col2='#c9b8f0')
    fg = S.L('fg')
    with fg.piece(0.8) as d:  # toys
        d.circ(0.9, 0.95, 0.04, '#e05a5a')
        d.rect(0.88, 0.94, 0.92, 0.945, '#f6f3ea')
        d.rect(0.05, 0.92, 0.12, 0.98, '#f6c453', r=0.004)
        d.rect(0.07, 0.88, 0.11, 0.92, '#3f7fbf', r=0.004)
    return {0: 'bedroom with a bed and a night lamp', 1: 'pink bedroom', 2: 'green bedroom'}[v]


@biome('classroom', interior=True)
def classroom(S):
    v = S.variant % 3
    rng = S.rng
    shell(S, wall=['#e6efe0', '#f2ead6', '#dfe8f0'][v], floor='#b98a5e', fy=0.7, ceiling=0.05)
    sky_ = S.L('sky')
    window_view(S, sky_, 0.04, 0.14, 0.2, 0.52, view='trees')
    far = S.L('far')
    with far.piece(0.8) as d:  # board
        d.rect(0.3, 0.16, 0.78, 0.48, '#7a5a3a', r=0.006)
        d.rect(0.31, 0.175, 0.77, 0.465, '#2f5a46' if v != 2 else '#f6f6f2')
        d.rect(0.3, 0.48, 0.78, 0.495, '#8a6a4a')
    with far.piece(0.3) as d:  # chalk scribbles: lines and a triangle, no words
        c = '#e6efe8' if v != 2 else '#3f6fa8'
        d.line([(0.35, 0.24), (0.47, 0.24)], c, 0.003)
        d.line([(0.35, 0.28), (0.5, 0.28)], c, 0.003)
        d.line([(0.6, 0.4), (0.7, 0.4), (0.65, 0.25), (0.6, 0.4)], c, 0.003)
        d.line([(0.35, 0.36), (0.44, 0.36)], c, 0.003)
    clock(far, 0.88, 0.2)
    ceiling_panels(far, 0.05, 3)
    with far.piece(0.6) as d:  # posters
        for x, c in ((0.83, '#f6c453'), (0.92, '#7fb6e8')):
            d.rect(x, 0.3, x + 0.07, 0.42, c, r=0.004)
            d.circ(x + 0.035, 0.35, 0.025, shade(c, 0.8))
    mid = S.L('mid')
    desk(mid, 0.42, 0.66, 0.72, h=0.11, col=WOOD, front=True)
    near = S.L('near')
    for row, (y, s) in enumerate(((0.84, 1.2), (0.98, 1.5))):
        for k in range(3):
            x = 0.12 + k * 0.33 + row * 0.04
            desk(near, x, x + 0.18 * s / 1.2, y, h=0.1 * s, col='#d9b98a', front=True)
            chair(near, x + 0.12 * s / 1.2, y + 0.02, s, col=['#3f6fa8', '#3d8a5a', '#c0443a'][k], face=-1)
    fg = S.L('fg')
    with fg.piece(0.8) as d:  # a backpack
        d.rect(0.9, 0.86, 0.98, 0.98, '#e05a5a', r=0.02)
        d.rect(0.91, 0.9, 0.97, 0.94, shade('#e05a5a', 0.85), r=0.01)
    return {0: 'classroom with a chalkboard and desks', 1: 'warm classroom', 2: 'classroom with a whiteboard'}[v]


@biome('hospital', interior=True)
def hospital(S):
    v = S.variant % 3
    rng = S.rng
    shell(S, wall=['#e2eef0', '#e6f0e6', '#eef0f4'][v], floor='#c9d6d6', fy=0.74, kind='tiles', ceiling=0.05)
    sky_ = S.L('sky')
    window_view(S, sky_, 0.68, 0.14, 0.92, 0.48, view='city', frame='#f6f6f6')
    far = S.L('far')
    ceiling_panels(far, 0.05, 2)
    with far.piece(0.6) as d:  # curtain rail and curtain
        d.rect(0.02, 0.1, 0.6, 0.11, '#b9c4c9')
        for k in range(5):
            d.rect(0.02 + k * 0.025, 0.11, 0.045 + k * 0.025, 0.66, '#8fc6c0' if k % 2 else '#7fb8b2', r=0.006)
    with far.piece(0.7) as d:  # monitor on an arm
        d.rect(0.52, 0.22, 0.64, 0.32, '#2e2e36', r=0.006)
        d.rect(0.53, 0.23, 0.63, 0.31, '#13202a')
        d.line([(0.58, 0.32), (0.58, 0.36), (0.6, 0.36)], '#9aa6b0', 0.004)
    with far.piece(0.3) as d:
        d.line([(0.535, 0.27), (0.56, 0.27), (0.567, 0.245), (0.575, 0.295), (0.583, 0.27), (0.625, 0.27)], '#6af0a0', 0.003, lit=True)
    mid = S.L('mid')
    with mid.piece(1.0) as d:  # bed
        d.rect(0.2, 0.56, 0.24, 0.8, '#d0d6dc', r=0.01)
        d.rect(0.22, 0.64, 0.7, 0.7, '#e6eaee', r=0.01)
        d.rect(0.68, 0.6, 0.71, 0.8, '#d0d6dc', r=0.01)
        for x in (0.26, 0.66):
            d.circ(x, 0.79, 0.012, '#5a5a66')
    with mid.piece(1.0) as d:
        d.rect(0.3, 0.6, 0.7, 0.66, '#9fc8e8', r=0.015)
        d.ell(0.27, 0.615, 0.04, 0.022, '#ffffff')
    with mid.piece(0.8) as d:  # IV stand
        d.line([(0.78, 0.78), (0.78, 0.3)], '#9aa6b0', 0.004)
        d.line([(0.75, 0.3), (0.81, 0.3)], '#9aa6b0', 0.004)
        d.rect(0.765, 0.31, 0.795, 0.38, '#e6f2fa', r=0.006)
        d.line([(0.78, 0.38), (0.75, 0.5), (0.6, 0.62)], '#cfe6f2', 0.002)
        d.line([(0.75, 0.78), (0.81, 0.78)], '#9aa6b0', 0.004)
    near = S.L('near')
    chair(near, 0.86, 0.94, 1.5, col='#7fb6a8', face=1)
    fg = S.L('fg')
    with fg.piece(0.9) as d:  # bedside trolley
        d.rect(0.0, 0.8, 0.14, 0.83, '#d0d6dc', r=0.004)
        d.rect(0.005, 0.83, 0.015, 1.02, '#9aa6b0')
        d.rect(0.125, 0.83, 0.135, 1.02, '#9aa6b0')
        d.rect(0.04, 0.76, 0.06, 0.8, '#f6f3ea', r=0.004)
        d.rect(0.08, 0.775, 0.11, 0.8, '#e0403a', r=0.004)
    return {0: 'hospital ward bed with a monitor', 1: 'hospital room, green walls', 2: 'hospital room, light walls'}[v]


@biome('courtroom', interior=True)
def courtroom(S):
    """A courtroom without state symbols: wood panels, the judge's bench, the stand, benches."""
    v = S.variant % 3
    rng = S.rng
    wallc = ['#8a6a4a', '#e6dccb', '#6a5a4a'][v]
    shell(S, wall=wallc, floor='#7a5236', fy=0.74)
    far = S.L('far')
    with far.piece(0.7) as d:  # tall panels
        for k in range(11):
            x = 0.01 + k * 0.09
            d.rect(x, 0.08, x + 0.08, 0.7, shade(wallc, 0.92), r=0.006)
            d.rect(x + 0.01, 0.1, x + 0.07, 0.38, shade(wallc, 0.86), r=0.006)
    with far.piece(0.6) as d:  # plain round emblem space left empty: a clock instead
        pass
    clock(far, 0.5, 0.18, 0.04)
    mid = S.L('mid')
    with mid.piece(1.0) as d:  # judge's bench
        d.rect(0.3, 0.42, 0.7, 0.46, '#5a3a24', r=0.006)
        d.rect(0.31, 0.46, 0.69, 0.76, '#6a4630', r=0.004)
        for k in range(4):
            d.rect(0.33 + k * 0.09, 0.5, 0.4 + k * 0.09, 0.72, '#7a5236', r=0.004)
    with mid.piece(0.9) as d:
        d.rect(0.46, 0.27, 0.54, 0.42, '#3a2a22', r=0.02)  # high chair back
    with mid.piece(0.7) as d:
        d.ell(0.6, 0.415, 0.025, 0.006, '#6a4630')  # gavel block
        d.rect(0.585, 0.395, 0.62, 0.405, '#5a3a24', r=0.003)
    near = S.L('near')
    with near.piece(1.0) as d:  # witness stand and a desk
        d.rect(0.75, 0.6, 0.92, 0.84, '#6a4630', r=0.006)
        d.rect(0.74, 0.58, 0.93, 0.61, '#5a3a24', r=0.004)
        d.rect(0.06, 0.66, 0.3, 0.68, '#5a3a24', r=0.004)
        d.rect(0.07, 0.68, 0.29, 0.86, '#6a4630', r=0.004)
    with near.piece(0.6) as d:
        d.rect(0.12, 0.64, 0.2, 0.66, '#f6f3ea')
        d.line([(0.8, 0.58), (0.81, 0.53)], '#3a3a40', 0.003)
        d.circ(0.81, 0.53, 0.006, '#3a3a40')
    fg = S.L('fg')
    with fg.piece(1.0) as d:  # gallery bench backs
        d.rect(-0.02, 0.9, 0.45, 0.95, '#5a3a24', r=0.006)
        d.rect(0.55, 0.9, 1.02, 0.95, '#5a3a24', r=0.006)
        d.rect(-0.02, 0.95, 0.45, 1.02, '#6a4630')
        d.rect(0.55, 0.95, 1.02, 1.02, '#6a4630')
    return {0: 'courtroom with wood panels and the bench', 1: 'light courtroom', 2: 'dark courtroom'}[v]


@biome('cafe', interior=True)
def cafe(S):
    v = S.variant % 3
    rng = S.rng
    wall = ['#e9d2b4', '#d6e2d6', '#3a3a44'][v]
    shell(S, wall=wall, floor='#8a6a4a', fy=0.72)
    sky_ = S.L('sky')
    window_view(S, sky_, 0.06, 0.12, 0.3, 0.5, view='city', frame='#3a3a40')
    far = S.L('far')
    with far.piece(0.8) as d:  # blank menu boards
        for k in range(3):
            x = 0.42 + k * 0.17
            d.rect(x, 0.12, x + 0.15, 0.34, '#2e2e36', r=0.006)
            for j in range(4):
                d.rect(x + 0.015, 0.16 + j * 0.04, x + 0.1 - 0.01 * j, 0.168 + j * 0.04, '#e6e6e0')
    for x in (0.5, 0.67, 0.84):
        lamp_pendant(far, x, 0.42, 1.0, col='#2e2e36')
    mid = S.L('mid')
    with mid.piece(1.0) as d:  # counter
        d.rect(0.38, 0.52, 0.98, 0.545, '#5a3a24', r=0.004)
        d.rect(0.39, 0.545, 0.97, 0.74, '#7a5236' if v != 2 else '#c0443a', r=0.004)
        for k in range(6):
            d.rect(0.4 + k * 0.095, 0.56, 0.48 + k * 0.095, 0.72, shade('#7a5236' if v != 2 else '#c0443a', 0.9), r=0.006)
    with mid.piece(0.8) as d:  # coffee machine, cups, cake stand
        d.rect(0.6, 0.42, 0.72, 0.52, '#c9cfd6', r=0.008)
        d.rect(0.62, 0.47, 0.7, 0.5, '#3a3a40')
        for k in range(4):
            d.rect(0.42 + k * 0.03, 0.495, 0.442 + k * 0.03, 0.52, '#f6f3ea', r=0.003)
        d.ell(0.86, 0.515, 0.05, 0.008, '#e6e6ee')
        d.pie(0.86, 0.512, 0.04, 180, 360, '#f2a0b8')
    near = S.L('near')
    for x in (0.18, 0.5):
        with near.piece(1.0) as d:  # round tables
            d.ell(x, 0.8, 0.09, 0.015, '#f6f3ea' if v != 2 else '#2e2e36')
            d.rect(x - 0.005, 0.8, x + 0.005, 0.94, '#3a3a40')
            d.ell(x, 0.94, 0.04, 0.008, '#3a3a40')
        with near.piece(0.6) as d:
            d.rect(x - 0.02, 0.765, x + 0.0, 0.79, '#ffffff', r=0.003)
            d.ell(x + 0.04, 0.785, 0.02, 0.005, '#e6e6ee')
        chair(near, x + 0.1, 0.96, 1.3, col='#3a3a40', face=1)
    fg = S.L('fg')
    plant(fg, 0.94, 1.0, 2.6)
    return {0: 'cafe with a counter and round tables', 1: 'green cafe', 2: 'dark cafe with a red counter'}[v]


@biome('metro', interior=True)
def metro(S):
    v = S.variant % 3
    rng = S.rng
    wall = ['#d9dfe4', '#e6e2d6', '#cfd8e0'][v]
    shell(S, wall=wall, floor='#6a6a74', fy=0.8, kind='carpet', skirting=False, ceiling=0.08)
    sky_ = S.L('sky')
    for k in range(3):
        x = 0.08 + k * 0.32
        window_view(S, sky_, x, 0.18, x + 0.22, 0.44, view='tunnel', frame='#b9c0c8', bars=1)
    far = S.L('far')
    ceiling_panels(far, 0.08, 3, lit=True)
    with far.piece(0.6) as d:  # blank ad panels between windows
        for k in range(2):
            x = 0.32 + k * 0.32
            d.rect(x + 0.0, 0.18, x + 0.08, 0.44, ['#f6c453', '#7fb6e8', '#f2a0b8'][(k + v) % 3], r=0.006)
    with far.piece(0.5) as d:  # a line map stripe without names
        d.rect(0.1, 0.11, 0.9, 0.125, '#f6f6f2')
        d.line([(0.12, 0.118), (0.88, 0.118)], ['#e05a5a', '#3f7fbf', '#3d8a5a'][v], 0.005)
        for k in range(10):
            d.circ(0.12 + k * 0.084, 0.118, 0.005, '#ffffff')
    mid = S.L('mid')
    with mid.piece(1.0) as d:  # bench seats along the wall
        d.rect(0.02, 0.52, 0.98, 0.64, ['#3f6fa8', '#c0443a', '#3d8a5a'][v], r=0.02)
        d.rect(0.02, 0.62, 0.98, 0.68, shade(['#3f6fa8', '#c0443a', '#3d8a5a'][v], 1.1), r=0.015)
        d.rect(0.02, 0.68, 0.98, 0.8, '#9aa2ab')
    near = S.L('near')
    with near.piece(0.9) as d:  # poles and handles
        for x in (0.18, 0.5, 0.82):
            d.rect(x - 0.006, 0.08, x + 0.006, 0.82, '#c9cfd6')
        d.rect(-0.02, 0.15, 1.02, 0.16, '#c9cfd6')
        for k in range(14):
            x = 0.04 + k * 0.07
            d.line([(x, 0.16), (x, 0.21)], '#9aa2ab', 0.002)
            d.ell(x, 0.225, 0.012, 0.015, '#e6e6ee')
    fg = S.L('fg')
    with fg.piece() as d:  # door edge
        d.rect(-0.02, 0.0, 0.05, 1.02, '#b9c0c8')
        d.rect(0.05, 0.0, 0.06, 1.02, '#3a3a40')
    return {0: 'metro car interior with blue seats', 1: 'metro car with red seats', 2: 'metro car with green seats'}[v]


@biome('bus_interior', interior=True)
def bus_interior(S):
    v = S.variant % 3
    rng = S.rng
    shell(S, wall='#e6e2d6', floor='#5a5a64', fy=0.8, kind='carpet', skirting=False, ceiling=0.08)
    sky_ = S.L('sky')
    for k in range(3):
        x = 0.04 + k * 0.33
        window_view(S, sky_, x, 0.16, x + 0.28, 0.5, view='city' if v != 2 else 'trees', frame='#3a3a40', bars=1)
    far = S.L('far')
    ceiling_panels(far, 0.08, 3)
    with far.piece(0.6) as d:
        d.rect(-0.02, 0.5, 1.02, 0.53, '#c9c4b8')
    mid = S.L('mid')
    seat = ['#3f6fa8', '#c0443a', '#e9a23a'][v]
    for k in range(4):
        seat_profile(mid, 0.05 + k * 0.25, 0.8, 0.9, seat, cover='#e6e2d6')
    near = S.L('near')
    with near.piece(0.9) as d:  # rail and stop button poles
        d.rect(-0.02, 0.11, 1.02, 0.12, '#f2b233')
        for x in (0.28, 0.78):
            d.rect(x - 0.006, 0.12, x + 0.006, 0.82, '#f2b233')
            d.rect(x - 0.01, 0.4, x + 0.01, 0.43, '#e05a5a', r=0.004)
    fg = S.L('fg')
    seat_profile(fg, 0.86, 1.1, 1.9, seat)
    return {0: 'city bus interior with blue seats', 1: 'bus interior with red seats', 2: 'country bus with orange seats'}[v]


@biome('airplane', interior=True)
def airplane(S):
    v = S.variant % 3
    rng = S.rng
    shell(S, wall='#eceae4', floor='#4a5068', fy=0.82, kind='carpet', skirting=False)
    sky_ = S.L('sky')
    with sky_.piece(0.5) as d:  # curved ceiling and overhead bins
        d.rect(-0.02, -0.02, 1.02, 0.2, '#e2e0da')
    for k in range(5):
        x = 0.06 + k * 0.2
        window_view(S, sky_, x, 0.32, x + 0.07, 0.46, view='clouds', frame='#d6d4ce', bars=1)
    far = S.L('far')
    with far.piece(0.8) as d:
        d.rect(-0.02, 0.06, 1.02, 0.2, '#f2f0ea', r=0.03)
        for k in range(6):
            d.rect(k * 0.18, 0.18, k * 0.18 + 0.004, 0.2, '#c9c6c0')
        d.rect(-0.02, 0.2, 1.02, 0.215, '#c9c6c0')
    mid = S.L('mid')
    seat = ['#3a4a7a', '#7a3a4a', '#3a6a6a'][v]
    for k in range(5):
        seat_profile(mid, 0.03 + k * 0.2, 0.8, 1.0, seat)
    near = S.L('near')
    with near.piece(0.6) as d:  # aisle lights
        for k in range(12):
            d.rect(k * 0.09, 0.95, k * 0.09 + 0.03, 0.955, '#fff2c0', lit=True)
    fg = S.L('fg')
    seat_profile(fg, 0.86, 1.08, 2.0, seat)
    return {0: 'airplane cabin with window seats', 1: 'airplane cabin, red seats', 2: 'airplane cabin, teal seats'}[v]


@biome('lab', interior=True)
def lab(S):
    v = S.variant % 3
    rng = S.rng
    shell(S, wall=['#e6eef2', '#eef2e6', '#2a3440'][v], floor='#b9c4c9', fy=0.74, kind='tiles', ceiling=0.05)
    far = S.L('far')
    ceiling_panels(far, 0.05, 3)
    shelf(far, 0.05, 0.35, 0.3, rng, books=False)
    shelf(far, 0.65, 0.95, 0.3, rng, books=False)
    with far.piece(0.6) as d:  # jars on shelves
        for x0 in (0.06, 0.66):
            for k in range(6):
                x = x0 + k * 0.048
                c = S.pick(['#7fd3f0', '#8ff0c0', '#f6c453', '#f2a0b8'])
                d.rect(x, 0.24, x + 0.03, 0.3, '#e6f2fa', r=0.006)
                d.rect(x + 0.003, 0.265, x + 0.027, 0.297, c, r=0.004)
    with far.piece(0.7) as d:  # a whiteboard with a molecule
        d.rect(0.4, 0.14, 0.6, 0.4, '#f6f6f2', r=0.006)
    with far.piece(0.4) as d:
        pts = [(0.45, 0.22), (0.5, 0.19), (0.55, 0.22), (0.55, 0.3), (0.5, 0.33), (0.45, 0.3), (0.45, 0.22)]
        d.line(pts, '#3f6fa8', 0.003)
        for p in pts[:-1]:
            d.circ(p[0], p[1], 0.008, '#e05a5a')
    mid = S.L('mid')
    with mid.piece(1.0) as d:  # bench
        d.rect(0.0, 0.56, 1.0, 0.59, '#2e2e36', r=0.004)
        for k in range(5):
            d.rect(0.01 + k * 0.2, 0.59, 0.19 + k * 0.2, 0.76, '#d0d6dc', r=0.004)
    with mid.piece(0.8) as d:  # flasks, a microscope
        for x, c in ((0.15, '#8ff0c0'), (0.22, '#f2a0b8'), (0.8, '#7fd3f0')):
            d.poly([(x - 0.008, 0.48), (x + 0.008, 0.48), (x + 0.03, 0.56), (x - 0.03, 0.56)], '#e6f2fa')
            d.poly([(x - 0.02, 0.53), (x + 0.02, 0.53), (x + 0.03, 0.56), (x - 0.03, 0.56)], c, lit=True)
        d.rect(0.5, 0.54, 0.58, 0.56, '#3a3a40')
        d.rect(0.535, 0.46, 0.55, 0.54, '#3a3a40')
        d.line([(0.54, 0.47), (0.52, 0.42)], '#3a3a40', 0.01)
        d.rect(0.62, 0.5, 0.72, 0.56, '#c9cfd6', r=0.006)
    near = S.L('near')
    chair(near, 0.35, 0.92, 1.4, col='#3a3a40', office=True)
    fg = S.L('fg')
    with fg.piece(0.9) as d:  # test-tube rack
        d.rect(0.82, 0.92, 0.98, 0.94, '#c9cfd6')
        for k in range(5):
            d.rect(0.835 + k * 0.03, 0.85, 0.85 + k * 0.03, 0.94, '#e6f2fa', r=0.006)
            d.rect(0.837 + k * 0.03, 0.89, 0.848 + k * 0.03, 0.935, S.pick(['#8ff0c0', '#f2a0b8', '#7fd3f0', '#f6c453']), r=0.005)
    return {0: 'science lab with a bench and flasks', 1: 'green-walled lab', 2: 'dark lab'}[v]


@biome('server_room', interior=True)
def server_room(S):
    v = S.variant % 3
    rng = S.rng
    shell(S, wall=['#2a3038', '#20283a', '#303034'][v], floor='#4a525e', fy=0.8, kind='tiles', skirting=False)
    led = ['#6af0a0', '#7fb6ff', '#f6c453'][v]
    for name, x0s, y1, h, s in (('far', [0.0, 0.17, 0.34, 0.51, 0.68, 0.85], 0.72, 0.5, 0.8), ('near', [-0.05, 0.75], 0.97, 0.9, 1.0)):
        L = S.L(name)
        for x0 in x0s:
            w = 0.15 * s
            with L.piece(0.9) as d:
                d.rect(x0, y1 - h, x0 + w, y1, '#1a1e24', r=0.004)
                for k in range(int(h / 0.035)):
                    yy = y1 - h + 0.012 + k * 0.035
                    d.rect(x0 + 0.008, yy, x0 + w - 0.008, yy + 0.026, '#2e343e', r=0.002)
            with L.piece(0.3) as d:
                for k in range(int(h / 0.035)):
                    yy = y1 - h + 0.022 + k * 0.035
                    for j in range(4):
                        if rng.random() < 0.6:
                            c = led if rng.random() < 0.8 else '#f05a4a'
                            d.circ(x0 + 0.015 + j * 0.012, yy, 0.0035, c, lit=True)
                            L.glow_circ(x0 + 0.015 + j * 0.012, yy, 0.005)
    mid = S.L('mid')
    with mid.piece(0.8) as d:  # cable trays
        d.rect(-0.02, 0.1, 1.02, 0.13, '#5a626e')
        for k in range(8):
            d.line([(0.05 + k * 0.12, 0.13), (0.06 + k * 0.12, 0.22)], S.pick(['#3f7fbf', '#f6c453', '#e05a5a']), 0.004)
    with mid.piece(0.6) as d:  # a console desk in the aisle
        d.rect(0.4, 0.7, 0.6, 0.72, '#5a626e')
        d.rect(0.42, 0.72, 0.58, 0.82, '#3a404a')
    monitor(mid, 0.5, 0.7, 1.0, on=True)
    fg = S.L('fg')
    with fg.piece(0.7) as d:  # floor vent tiles
        for k in range(6):
            d.rect(0.3 + k * 0.07, 0.95, 0.36 + k * 0.07, 0.99, '#5a626e', r=0.004)
    return {0: 'server room with green LEDs', 1: 'server room in blue light', 2: 'server room with amber LEDs'}[v]


@biome('gov_counter', interior=True)
def gov_counter(S):
    """A public service counter: windows behind glass, a ticket display, queue chairs. No symbols."""
    v = S.variant % 3
    rng = S.rng
    wall = ['#e6e2d6', '#dfe8ec', '#ece4d4'][v]
    shell(S, wall=wall, floor='#a8a39a', fy=0.76, kind='tiles', ceiling=0.05)
    far = S.L('far')
    ceiling_panels(far, 0.05, 4, lit=True)
    with far.piece(0.7) as d:  # number display
        d.rect(0.38, 0.1, 0.62, 0.2, '#2e2e36', r=0.006)
        for k in range(3):
            d.rect(0.4 + k * 0.075, 0.12, 0.46 + k * 0.075, 0.18, '#3a3a44', r=0.004)
    with far.piece(0.4) as d:
        for k in range(3):
            x = 0.43 + k * 0.075
            d.rect(x - 0.015, 0.13, x + 0.015, 0.17, '#f05a4a', lit=True)
    clock(far, 0.88, 0.16)
    mid = S.L('mid')
    with mid.piece(1.0) as d:  # counter and glass partitions
        d.rect(-0.02, 0.5, 1.02, 0.53, '#c9c4b8', r=0.004)
        d.rect(-0.02, 0.53, 1.02, 0.76, ['#8a9aa8', '#9aa88a', '#a89a8a'][v])
        for k in range(4):
            x = 0.04 + k * 0.25
            d.rect(x, 0.55, x + 0.2, 0.74, shade(['#8a9aa8', '#9aa88a', '#a89a8a'][v], 1.08), r=0.006)
    with mid.piece(0.3) as d:
        for k in range(4):
            x = 0.03 + k * 0.25
            d.rect(x, 0.22, x + 0.22, 0.5, (225, 240, 250, 90))
            d.rect(x + 0.07, 0.46, x + 0.15, 0.5, (0, 0, 0, 0))
            d.rect(x + 0.22, 0.22, x + 0.23, 0.5, '#b9c0c8')
    with mid.piece(0.7) as d:
        for k in range(4):
            x = 0.05 + k * 0.25
            d.rect(x + 0.1, 0.45, x + 0.17, 0.5, '#f6f3ea')
            d.rect(x + 0.02, 0.39, x + 0.08, 0.5, '#2e2e36', r=0.004)
            d.rect(x, 0.13, x + 0.04, 0.2, '#3f7fbf', r=0.004)
    with mid.piece(0.4) as d:
        for k in range(4):
            x = 0.05 + k * 0.25
            d.rect(x + 0.01, 0.15, x + 0.03, 0.18, '#ffffff', lit=True)
    near = S.L('near')
    with near.piece(1.0) as d:  # queue chairs row
        for k in range(5):
            x = 0.18 + k * 0.13
            d.rect(x, 0.82, x + 0.11, 0.84, '#3f6fa8', r=0.006)
            d.rect(x, 0.74, x + 0.11, 0.8, '#3f6fa8', r=0.01)
        d.rect(0.17, 0.84, 0.83, 0.85, '#7a7a86')
        for x in (0.2, 0.8):
            d.rect(x, 0.85, x + 0.008, 0.92, '#7a7a86')
    fg = S.L('fg')
    with fg.piece(0.9) as d:  # ticket machine
        d.rect(0.02, 0.6, 0.12, 1.02, '#d0d6dc', r=0.01)
        d.rect(0.035, 0.64, 0.105, 0.72, '#3f7fbf', lit=True)
        d.rect(0.05, 0.78, 0.09, 0.79, '#3a3a40')
    plant(fg, 0.94, 1.0, 2.2)
    return {0: 'public service counter with a queue display', 1: 'service hall, cool colours', 2: 'service hall, warm colours'}[v]


@biome('shop', interior=True)
def shop(S):
    v = S.variant % 3
    rng = S.rng
    shell(S, wall=['#f2ede0', '#e6eef2', '#f4e6dc'][v], floor='#c9c4b8', fy=0.76, kind='tiles', ceiling=0.05)
    far = S.L('far')
    ceiling_panels(far, 0.05, 4)
    goods = ['#e05a5a', '#f6c453', '#3f7fbf', '#6fb850', '#f28b6b', '#b99be0', '#f6f3ea', '#e9a23a']
    for x0 in (0.02, 0.36, 0.7):  # shelving units with goods
        with far.piece(0.9) as d:
            d.rect(x0, 0.16, x0 + 0.28, 0.74, '#b9b2a4', r=0.004)
            d.rect(x0 + 0.01, 0.17, x0 + 0.27, 0.74, '#e6e0d4')
            for k in range(5):
                d.rect(x0 + 0.005, 0.27 + k * 0.11, x0 + 0.275, 0.282 + k * 0.11, '#8a8f99')
        with far.piece(0.6) as d:
            for k in range(5):
                y = 0.27 + k * 0.11
                x = x0 + 0.015
                while x < x0 + 0.26:
                    w, h = 0.015 + 0.02 * rng.random(), 0.04 + 0.05 * rng.random()
                    kind = rng.random()
                    c = goods[int(rng.integers(len(goods)))]
                    if kind < 0.3:  # bottles
                        d.rect(x, y - h, x + 0.014, y, c, r=0.006)
                        d.rect(x + 0.004, y - h - 0.015, x + 0.01, y - h + 0.002, c)
                        x += 0.018
                    else:  # boxes
                        d.rect(x, y - h, x + w, y, c, r=0.003)
                        d.rect(x + w * 0.2, y - h * 0.7, x + w * 0.8, y - h * 0.4, '#ffffff')
                        x += w + 0.003
    mid = S.L('mid')
    with mid.piece(1.0) as d:  # checkout
        d.rect(0.55, 0.62, 0.95, 0.65, '#3a3a40', r=0.004)
        d.rect(0.56, 0.65, 0.94, 0.84, ['#3f7fbf', '#c0443a', '#3d8a5a'][v], r=0.006)
    with mid.piece(0.7) as d:
        d.rect(0.8, 0.55, 0.88, 0.62, '#2e2e36', r=0.004)
        d.rect(0.81, 0.56, 0.87, 0.6, '#7fb6e8', lit=True)
        d.rect(0.6, 0.6, 0.72, 0.62, '#1e1e26')
    near = S.L('near')
    with near.piece(1.0) as d:  # shopping basket stack and a cart
        d.line([(0.1, 0.8), (0.14, 0.92), (0.3, 0.92), (0.33, 0.8), (0.1, 0.8)], '#9aa6b0', 0.006)
        for k in range(4):
            d.line([(0.12 + k * 0.05, 0.8), (0.15 + k * 0.045, 0.92)], '#9aa6b0', 0.003)
        d.line([(0.33, 0.8), (0.37, 0.76)], '#9aa6b0', 0.006)
        d.circ(0.16, 0.95, 0.014, '#3a3a40')
        d.circ(0.29, 0.95, 0.014, '#3a3a40')
    fg = S.L('fg')
    with fg.piece(0.9) as d:  # a fruit crate
        d.rect(-0.02, 0.88, 0.2, 1.04, '#b07a4a', r=0.006)
        for k in range(8):
            d.circ(0.0 + k * 0.026, 0.875, 0.022, S.pick(['#e0403a', '#f6d353', '#7cc45e']))
    return {0: 'grocery shop with shelves and a checkout', 1: 'cool-coloured shop', 2: 'warm shop'}[v]
