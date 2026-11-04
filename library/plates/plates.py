"""Felt background plates made in code: a 16:9 scene built from 3-5 parallax layers (sky, far, mid, near, fg).

Every shape is drawn with Pillow on its own piece and pressed into its layer with felt_composite (felt.py, the same
felt pass as Extella Mult), so it gets a rounded edge, fibre grain and a soft shadow. Each layer is saved as a
transparent 1920x1080 PNG; full.jpg is the layers stacked. No image models, no network.

    python plates.py --one steppe --time golden --weather clear --season summer --seed 3 --out out/
    python plates.py --all --out plates/ --jobs 4          # the whole library from the catalogue (catalog.py)

Parameters: biome (see BIOMES), time (dawn, day, golden, dusk, night), weather (clear, clouds, rain, snow, fog),
season (spring, summer, autumn, winter), palette (felt, pastel, vivid, warm, cool, muted), seed (any int).
"""
import argparse
import colorsys
import json
import math
import os
import sys
from contextlib import contextmanager

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'feltlook'))
import feltlook as FL  # noqa: E402
from feltlook import felt_composite, blur as _blur  # noqa: E402

W, H = 1920, 1080
AR = W / H
LAYERS = ('sky', 'far', 'mid', 'near', 'fg')
# how far each layer moves for a camera move of 1 (sky barely moves, foreground moves most)
PARALLAX = {'sky': 0.04, 'far': 0.18, 'mid': 0.42, 'near': 0.72, 'fg': 1.1}
# how much each layer fades into the air colour (aerial perspective)
HAZE = {'sky': 0.0, 'far': 0.42, 'mid': 0.18, 'near': 0.05, 'fg': 0.0}
FELT = {'sky': 0.6, 'far': 0.7, 'mid': 0.9, 'near': 1.0, 'fg': 1.1}
# felt v2+ (feltlook): extra softening/veil of far layers, shadow strength per layer, felt size unit (1080/804)
DEPTH_HAZE = {'sky': 0.0, 'far': 0.55, 'mid': 0.18, 'near': 0.0, 'fg': 0.0}
SHADOW_K = {'sky': 0.6, 'far': 0.6, 'mid': 0.9, 'near': 1.0, 'fg': 1.0}
S_FELT = H / 804.0
TIMES = ('dawn', 'day', 'golden', 'dusk', 'night')
WEATHERS = ('clear', 'clouds', 'rain', 'snow', 'fog')
SEASONS = ('spring', 'summer', 'autumn', 'winter')
PALETTES = ('felt', 'pastel', 'vivid', 'warm', 'cool', 'muted')


def hx(c):
    if isinstance(c, str):
        c = c.lstrip('#')
        return np.array([int(c[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255
    return np.array(c[:3], np.float32) / (255 if max(c[:3]) > 1 else 1)


def to255(rgb, a=255):
    r = np.clip(rgb, 0, 1)
    return (int(r[0] * 255 + .5), int(r[1] * 255 + .5), int(r[2] * 255 + .5), a)


def shade(c, k):
    """k<1 darker, k>1 lighter (towards white)."""
    v = hx(c)
    v = v * k if k <= 1 else v + (1 - v) * (k - 1)
    return '#%02x%02x%02x' % tuple(int(np.clip(x, 0, 1) * 255) for x in v)


def mixc(a, b, t):
    v = hx(a) * (1 - t) + hx(b) * t
    return '#%02x%02x%02x' % tuple(int(np.clip(x, 0, 1) * 255) for x in v)


# ---------------------------------------------------------------- light and air

TIME = {
    'dawn':   dict(top='#6f7fc0', mid='#d9a7c0', bot='#ffd6a8', tint=(0.96, 0.86, 0.9), haze='#e7bfc4', sun=(0.24, 0.6, '#ffe2b0', 0.07)),
    'day':    dict(top='#6fb2e6', mid='#a8d4f0', bot='#e0f1f8', tint=(1.0, 1.0, 1.0), haze='#cfe3ef', sun=(0.82, 0.16, '#fff0a0', 0.075)),
    'golden': dict(top='#7aa0d6', mid='#f2c49a', bot='#ffd78a', tint=(1.05, 0.9, 0.72), haze='#f2cf9e', sun=(0.74, 0.47, '#ffd06a', 0.085)),
    'dusk':   dict(top='#2c3270', mid='#a3628c', bot='#f2906e', tint=(0.66, 0.58, 0.76), haze='#a07b9a', sun=(0.3, 0.64, '#ffae7a', 0.09)),
    'night':  dict(top='#0b1236', mid='#1c2a5e', bot='#34477f', tint=(0.36, 0.43, 0.7), haze='#2c3a6a', sun=(0.78, 0.17, '#f6efd2', 0.06)),
}
WEATHER = {  # desaturate, darken, extra haze, sky colours pulled towards
    'clear':  dict(desat=0.0, dark=1.0, haze=0.0, sky=None),
    'clouds': dict(desat=0.18, dark=0.94, haze=0.06, sky='#b7c3cf'),
    'rain':   dict(desat=0.38, dark=0.8, haze=0.14, sky='#8592a0'),
    'snow':   dict(desat=0.22, dark=1.0, haze=0.16, sky='#d4dbe4'),
    'fog':    dict(desat=0.3, dark=0.98, haze=0.42, sky='#d9dde0'),
}
SEASON = {  # colour roles that change with the season
    'grass':  dict(spring='#9ed36a', summer='#7fbf55', autumn='#c4ad55', winter='#eef3f8'),
    'grass2': dict(spring='#86c45a', summer='#68a948', autumn='#ad9443', winter='#dfe7f0'),
    'grass3': dict(spring='#b6e07e', summer='#97cf68', autumn='#d6bf6a', winter='#f6f9fc'),
    'leaf':   dict(spring='#7cc45e', summer='#4f9e48', autumn='#e08a3a', winter='#7d6a5c'),
    'leaf2':  dict(spring='#9fd877', summer='#68b456', autumn='#e9b443', winter='#8c7868'),
    'leaf3':  dict(spring='#f2b6c9', summer='#3f8a42', autumn='#c9532e', winter='#6f5e52'),
    'pine':   dict(spring='#3f8f5a', summer='#357f4e', autumn='#3d7f55', winter='#3a6f55'),
    'pine2':  dict(spring='#52a56a', summer='#47975f', autumn='#4c9163', winter='#4a7f63'),
    'steppe': dict(spring='#a9d46e', summer='#cdbf6a', autumn='#c9a35a', winter='#eef2f6'),
    'steppe2': dict(spring='#93c25c', summer='#bba95a', autumn='#b48c4c', winter='#dfe6ee'),
    'field':  dict(spring='#a7d36a', summer='#e6c45a', autumn='#c98a4a', winter='#f1f5f9'),
    'tuft':   dict(spring='#86c45a', summer='#68a948', autumn='#ad9443', winter='#a8987a'),
    'tuft2':  dict(spring='#9ed36a', summer='#7fbf55', autumn='#c4ad55', winter='#bcae90'),
}
PALETTE = {  # saturation, value lift, warm shift (+ = warmer)
    'felt': (1.0, 0.0, 0.0), 'pastel': (0.72, 0.12, 0.0), 'vivid': (1.25, 0.0, 0.0), 'warm': (1.02, 0.02, 0.06),
    'cool': (0.95, 0.0, -0.06), 'muted': (0.6, -0.02, 0.0)}


class Look:
    """Turns a drawn colour into the colour seen at a given time, weather, season, palette and distance."""

    def __init__(self, time='day', weather='clear', season='summer', palette='felt', interior=False):
        self.time, self.weather, self.season, self.palette, self.interior = time, weather, season, palette, interior
        self.T, self.Wt = TIME[time], WEATHER[weather]
        self.night = time == 'night'
        self.lit_share = {'night': 0.8, 'dusk': 0.55, 'dawn': 0.25}.get(time, 0.0)
        if weather in ('rain', 'clouds') and time in ('day', 'golden'):
            self.lit_share = 0.15
        self.haze_col = self._air(hx(self.T['haze']))

    def role(self, c):
        if isinstance(c, str) and not c.startswith('#'):
            if c in SEASON:
                return SEASON[c][self.season] or '#ffffff'
            raise KeyError(c)
        return c

    def _air(self, v):
        if self.Wt['sky'] and not self.interior:
            lum = {'night': 0.25, 'dusk': 0.55, 'dawn': 0.8, 'golden': 0.85}.get(self.time, 1.0)
            v = v * 0.6 + hx(self.Wt['sky']) * lum * 0.4
        return np.clip(v, 0, 1)

    def _pal(self, v):
        sat, lift, warm = PALETTE[self.palette]
        h, l, s = colorsys.rgb_to_hls(*np.clip(v, 0, 1))
        s = min(1, s * sat)
        v = np.array(colorsys.hls_to_rgb(h, l, s), np.float32)
        v = v + (1 - v) * lift if lift > 0 else v * (1 + lift)
        v = v + np.array([warm, warm * 0.3, -warm], np.float32)
        return np.clip(v, 0, 1)

    def col(self, c, haze=0.0, lit=False):
        v = self._pal(hx(self.role(c)))
        if lit:  # a lamp or a lit window: not darkened by the night
            return v
        g = v.mean()
        k = self.Wt['desat'] * (0.5 if self.interior else 1)
        v = v * (1 - k) + g * k
        if self.interior:
            tint = {'night': (0.92, 0.84, 0.74), 'dusk': (0.97, 0.9, 0.84), 'golden': (1.03, 0.96, 0.86), 'dawn': (0.98, 0.94, 0.95)}.get(self.time, (1, 1, 1))
            return np.clip(v * np.array(tint), 0, 1)
        v = v * np.array(self.T['tint']) * self.Wt['dark']
        hz = min(0.92, haze + (self.Wt['haze'] * (haze / 0.42) if haze else 0))
        return np.clip(v * (1 - hz) + self.haze_col * hz, 0, 1)

    def sky_cols(self):
        t = self.T
        cs = [hx(t['top']), hx(t['mid']), hx(t['bot'])]
        if self.Wt['sky']:
            w = hx(self.Wt['sky'])
            lum = {'night': 0.25, 'dusk': 0.55, 'dawn': 0.8, 'golden': 0.85}.get(self.time, 1.0)
            k = {'clouds': 0.45, 'rain': 0.7, 'snow': 0.6, 'fog': 0.75}[self.weather]
            cs = [c * (1 - k) + w * lum * k for c in cs]
        return [self._pal(c) for c in cs]


# ---------------------------------------------------------------- drawing

class D:
    """Draws one felt piece. Coordinates: x in 0..1 of the width, y in 0..1 of the height; radii and widths in
    units of the height (so circles stay round)."""

    def __init__(self, layer, img):
        self.L, self.img = layer, img
        self.d = ImageDraw.Draw(img)

    def C(self, c, lit=False):
        if isinstance(c, tuple) and len(c) == 4:
            return c
        return to255(self.L.look.col(c, self.L.haze, lit))

    def poly(self, pts, c, lit=False):
        if len(pts) > 2:
            self.d.polygon([(x * W, y * H) for x, y in pts], fill=self.C(c, lit))

    def rect(self, x0, y0, x1, y1, c, r=0, lit=False):
        b = [min(x0, x1) * W, min(y0, y1) * H, max(x0, x1) * W, max(y0, y1) * H]
        if b[2] - b[0] < 1 or b[3] - b[1] < 1:
            return
        if r:
            rr = min(r * H, (b[2] - b[0]) / 2 - 0.5, (b[3] - b[1]) / 2 - 0.5)
            self.d.rounded_rectangle(b, max(rr, 0), fill=self.C(c, lit))
        else:
            self.d.rectangle(b, fill=self.C(c, lit))

    def ell(self, cx, cy, rx, ry, c, lit=False):
        self.d.ellipse([cx * W - rx * H, cy * H - ry * H, cx * W + rx * H, cy * H + ry * H], fill=self.C(c, lit))

    def circ(self, cx, cy, r, c, lit=False):
        self.ell(cx, cy, r, r, c, lit)

    def line(self, pts, c, w, lit=False):
        self.d.line([(x * W, y * H) for x, y in pts], fill=self.C(c, lit), width=max(1, int(w * H)), joint='curve')
        r = w * H / 2
        if r > 1.5:
            for x, y in (pts[0], pts[-1]):
                self.d.ellipse([x * W - r, y * H - r, x * W + r, y * H + r], fill=self.C(c, lit))

    def ridge(self, f, c, bottom=1.02, n=160, x0=-0.03, x1=1.03):
        pts = [(x0 + (x1 - x0) * i / n, f(x0 + (x1 - x0) * i / n)) for i in range(n + 1)]
        self.poly(pts + [(x1, bottom), (x0, bottom)], c)

    def pie(self, cx, cy, r, a0, a1, c, lit=False):
        self.d.pieslice([cx * W - r * H, cy * H - r * H, cx * W + r * H, cy * H + r * H], a0, a1, fill=self.C(c, lit))

    def window(self, x0, y0, x1, y1, day='#cfe6f2', r=0.003, rng=None, force=None):
        """A window: lit warm at night (and glowing), sky-blue by day."""
        on = force if force is not None else (rng.random() < self.L.look.lit_share if rng is not None else self.L.look.lit_share > 0.5)
        if on:
            warm = ('#ffd36e', '#ffe08f', '#ffc45a', '#fff0b8')[int((x0 * 97 + y0 * 31) * 10) % 4]
            self.rect(x0, y0, x1, y1, warm, r, lit=True)
            self.L.glow_rect(x0, y0, x1, y1)
        else:
            self.rect(x0, y0, x1, y1, day if not self.L.look.night else '#3a4870', r)
        return on

    def lamp(self, x, y, r, col='#ffe6a0'):
        """A light source: drawn unshaded at night, with a glow."""
        on = self.L.look.lit_share > 0.2
        self.circ(x, y, r, col if on else '#f4f1e4', lit=on)
        if on:
            self.L.glow_circ(x, y, r * 4)


class Layer:
    def __init__(self, scene, name):
        self.scene, self.look, self.name = scene, scene.look, name
        self.haze = HAZE[name] if not scene.interior else HAZE[name] * 0.15
        self.depth = FELT[name]
        self.base = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        self.glow = None
        self.fog = None  # y of a fog bank drawn over this layer's foot
        self.post = []  # callables run on the final premultiplied arrays
        self.shadow = name != 'sky'
        self.kind = 'felt'

    @contextmanager
    def piece(self, depth=None, kind=None):
        """One felt piece. kind: feltlook kind ('felt', 'cloud', 'foliage', 'ground', 'knit', 'snow', 'fine', 'hard')."""
        img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        yield D(self, img)
        k = kind or self.kind
        # far layers: finer fibres (they are far away), weaker shadows
        felt_composite(self.base, img, self.depth * (depth if depth is not None else 1.0), kind=k, s=S_FELT,
                       shadow_k=SHADOW_K[self.name], fibres=self.name != 'far' or k in ('cloud', 'foliage'))

    def flat(self):
        """Draw straight onto the layer, no felt pass (for rain, stars, fine lines)."""
        return D(self, self.base)

    def _gmask(self):
        if self.glow is None:
            self.glow = Image.new('L', (W, H), 0)
        return ImageDraw.Draw(self.glow)

    def glow_rect(self, x0, y0, x1, y1):
        self._gmask().rectangle([x0 * W, y0 * H, x1 * W, y1 * H], fill=255)

    def glow_circ(self, x, y, r):
        self._gmask().ellipse([x * W - r * H, y * H - r * H, x * W + r * H, y * H + r * H], fill=150)

    def finish(self):
        a = np.asarray(self.base, np.float32) / 255
        al = a[..., 3].copy()
        rgb = a[..., :3] * al[..., None]  # premultiplied from here on
        if self.glow is not None:
            g = np.asarray(self.glow, np.float32) / 255
            g = _blur(g, 22) * 0.55 + _blur(g, 6) * 0.25
            col = np.array([1.0, 0.82, 0.5], np.float32)
            rgb = rgb + g[..., None] * col * (1 - al[..., None] * 0.6)
            al = np.maximum(al, np.clip(g * 1.2, 0, 1))
        hz = DEPTH_HAZE[self.name] * (0.35 if self.scene.interior else 1.0)
        if hz > 0:  # aerial perspective: far felt melts softly into the air, so the parallax reads
            rgb, al = FL.depth_haze(rgb, al, hz, self.look.haze_col)
        for f in self.post:
            rgb, al = f(rgb, al)
        if self.shadow and self.name != 'sky':  # ambient occlusion / soft shadow cast onto the layers behind
            k = 0.32 if not self.scene.interior else 0.38
            sh = FL.layer_ao(al, S_FELT * 0.8, k)
            al = al + sh * (1 - al)
        out = np.zeros((H, W, 4), np.float32)
        nz = al > 1e-4
        out[..., :3][nz] = np.clip(rgb[nz] / al[nz][:, None], 0, 1)
        out[..., 3] = np.clip(al, 0, 1)
        return Image.fromarray((out * 255 + 0.5).astype(np.uint8), 'RGBA')


class Scene:
    def __init__(self, biome, time='day', weather='clear', season='summer', palette='felt', seed=1, variant=0, interior=False):
        self.biome, self.time, self.weather, self.season, self.palette = biome, time, weather, season, palette
        self.seed, self.variant, self.interior = seed, variant, interior
        self.look = Look(time, weather, season, palette, interior)
        self.rng = np.random.default_rng(seed * 1000 + variant)
        self.layers = {}
        self.about = ''
        FL.begin(seed * 7 + variant * 1009 + sum(map(ord, biome)) * 31 + TIMES.index(time) * 3)

    def L(self, name):
        if name not in self.layers:
            self.layers[name] = Layer(self, name)
        return self.layers[name]

    def r(self, a=0.0, b=1.0):
        return a + (b - a) * self.rng.random()

    def pick(self, seq):
        return seq[int(self.rng.integers(len(seq)))]


# ---------------------------------------------------------------- sky, weather

def sky_gradient(S, cols=None, horizon=0.62):
    look = S.look
    c0, c1, c2 = cols or look.sky_cols()
    y = np.linspace(0, 1, H, dtype=np.float32)[:, None] / max(horizon, 0.3)
    y = np.clip(y, 0, 1.4)
    t1 = np.clip(y / 0.6, 0, 1)
    t2 = np.clip((y - 0.6) / 0.4, 0, 1)
    col = c0 * (1 - t1[..., None]) + c1 * t1[..., None]
    col = col * (1 - t2[..., None]) + c2 * t2[..., None]
    col = np.broadcast_to(col, (H, W, 3)).copy()
    sx, sy, scol, sr = look.T['sun']
    if look.time in ('dawn', 'golden', 'dusk') and look.weather in ('clear', 'clouds'):
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.sqrt(((xx / H - sx * AR)) ** 2 + (yy / H - sy) ** 2)
        g = np.exp(-d / 0.35)[..., None] * 0.45
        col = col * (1 - g) + hx(scol) * g
    # a soft wool gradient: broad heathered batts, faint micro-fibres, needle dimples, long carded streaks
    night = look.time == 'night'
    col = FL.wool_field(np.clip(col, 0, 1).astype(np.float32), S_FELT, seed=S.seed * 13 + S.variant,
                        strength=0.75 if night else 1.0, scale=2.6, streaks=0.0 if night else 0.9)
    L = S.L('sky')
    L.base = Image.fromarray((np.clip(col, 0, 1) * 255).astype(np.uint8), 'RGB').convert('RGBA')
    return L


def cloud(d, x, y, s, c='#fbfbf6', flat=False):
    blobs = ((-0.1, 0.03, 0.06), (-0.045, -0.012, 0.08), (0.035, -0.03, 0.095), (0.105, 0.015, 0.068), (0.0, 0.035, 0.065), (0.06, 0.04, 0.05))
    for dx, dy, r in blobs:
        d.ell(x + dx * s * 0.62, y + dy * s * (0.6 if flat else 1), r * s * (1.25 if flat else 1), r * s * (0.55 if flat else 0.88), c)
    if flat:
        d.rect(x - 0.08 * s, y, x + 0.08 * s, y + 0.045 * s, c, r=0.02 * s)


def sky(S, horizon=0.62, sun=True, clouds=None, stars=True, moon_phase='full', cloud_y=(0.06, 0.4)):
    """The sky layer: gradient, sun or moon, stars, clouds, by time and weather."""
    look = S.look
    L = sky_gradient(S, horizon=horizon)
    sx, sy, scol, sr = look.T['sun']
    rng = S.rng
    wx = look.weather
    if look.night and stars and wx in ('clear', 'clouds'):
        fd = L.flat()
        for _ in range(260):
            x, y = rng.random(), rng.random() ** 1.6 * horizon * 0.95
            r = 0.0012 + rng.random() ** 3 * 0.0035
            fd.circ(x, y, r, '#fff6dc', lit=True)
        with L.piece(0.4, kind='fine') as d:
            for _ in range(14):
                x, y = rng.random(), rng.random() * horizon * 0.7
                r = 0.006 + rng.random() * 0.004
                d.poly([(x + math.cos(a * math.pi / 5 - math.pi / 2) * (r if a % 2 == 0 else r * 0.45) / AR,
                         y + math.sin(a * math.pi / 5 - math.pi / 2) * (r if a % 2 == 0 else r * 0.45)) for a in range(10)], '#fff3c4', lit=True)
    if sun and wx in ('clear', 'clouds') and not (look.time == 'dusk' and horizon < sy):
        with L.piece(0.8) as d:
            if look.night:
                d.circ(sx, sy, sr, '#f6efd2', lit=True)
                if moon_phase == 'crescent':
                    c0 = look.sky_cols()[0]
                    d.circ(sx + 0.022, sy - 0.018, sr * 0.92, to255(c0))
                else:
                    for dx, dy, rr in ((-0.012, -0.01, 0.016), (0.014, 0.014, 0.011), (0.0, 0.025, 0.008)):
                        d.circ(sx + dx, sy + dy, rr, '#e6dcb8', lit=True)
                L.glow_circ(sx, sy, sr * 0.7)
            else:
                d.circ(sx, sy, sr, scol, lit=True)
                if look.time == 'day':
                    d.circ(sx, sy, sr * 0.7, '#fff7c6', lit=True)
    n = clouds if clouds is not None else {'clear': 3, 'clouds': 7, 'rain': 0, 'snow': 0, 'fog': 1}[wx]
    ccol = {'night': '#5a6890', 'dusk': '#f0b7b0', 'golden': '#fff0d8', 'dawn': '#fde4e4'}.get(look.time, '#fbfbf6')
    for i in range(n):
        x = (i + 0.2 + 0.6 * rng.random()) / max(n, 1)
        y = cloud_y[0] + (cloud_y[1] - cloud_y[0]) * rng.random()
        s = 0.6 + 0.6 * rng.random()
        if sun and abs(x - sx) < 0.16 and abs(y - sy) < 0.14:  # keep the sun or moon clear
            x = (x + 0.33) % 1.0
        with L.piece(0.8, kind='cloud') as d:
            cloud(d, x, y, s, ccol, flat=rng.random() < 0.4)
    if wx in ('rain', 'snow'):  # a heavy cloud deck
        deck = {'rain': '#7d8896', 'snow': '#cdd4de'}[wx]
        deck = mixc(deck, '#1a2040', 0.6) if look.night else (mixc(deck, '#6a5070', 0.35) if look.time == 'dusk' else deck)
        for row, (yy, k) in enumerate(((0.02, 1.0), (0.1, 0.9))):
            with L.piece(0.7, kind='cloud') as d:
                x = -0.05
                while x < 1.1:
                    s = 0.9 + 0.5 * rng.random()
                    cloud(d, x, yy + 0.06 * rng.random(), s, to255(hx(deck) * (k + 0.06 * row)), flat=True)
                    x += 0.13 + 0.06 * rng.random()
    return L


def weather_fx(S, ground=0.75):
    """Rain streaks and snowflakes in the near and fg layers; fog banks between layers."""
    look, rng = S.look, S.rng
    if look.weather == 'rain':
        for name, n, ln, al in (('near', 380, 0.03, 0.4), ('fg', 160, 0.06, 0.55)):
            L = S.L(name)
            img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            dd = ImageDraw.Draw(img)
            c = (205, 215, 235, int(255 * al)) if not look.night else (150, 165, 210, int(255 * al))
            for _ in range(n):
                x, y = rng.random() * W, rng.random() * H
                dd.line([(x, y), (x - ln * H * 0.18, y + ln * H)], fill=c, width=2 if name == 'near' else 3)
            L.post.append(_over(img))
    if look.weather == 'snow':
        for name, n, rmin, rmax in (('mid', 140, 0.002, 0.004), ('near', 140, 0.004, 0.007), ('fg', 50, 0.007, 0.012)):
            L = S.L(name)
            with L.piece(0.35, kind='snow') as d:
                for _ in range(n):
                    d.circ(rng.random(), rng.random(), rmin + (rmax - rmin) * rng.random(), '#ffffff', lit=look.night)
    if look.weather == 'fog':
        for name, k in (('far', 0.45), ('mid', 0.36), ('near', 0.18)):
            if name in S.layers:
                S.L(name).post.append(_fogbank(ground - {'far': 0.12, 'mid': 0.04, 'near': -0.06}[name], k, look.haze_col))


def _over(img):
    a = np.asarray(img, np.float32) / 255

    def f(rgb, al):
        o = a[..., 3]
        return rgb * (1 - o[..., None]) + a[..., :3] * o[..., None], al + o * (1 - al)
    return f


def _fogbank(y, k, col):
    yy = np.linspace(0, 1, H, dtype=np.float32)
    band = np.exp(-((yy - y) / 0.16) ** 2) * k + np.clip((yy - y) / 0.5, 0, 1) * k * 0.4
    xs = np.linspace(0, 6.28 * 2, W, dtype=np.float32)
    wav = (0.85 + 0.15 * np.sin(xs[None, :] + y * 9) * np.cos(xs[None, :] * 0.37))
    f_ = np.clip(band[:, None] * wav, 0, 0.85)

    def f(rgb, al):
        return rgb * (1 - f_[..., None]) + col * f_[..., None], al + f_ * (1 - al)
    return f


# ---------------------------------------------------------------- output

SMALL = os.environ.get('PLATES_PNG', 'small') == 'small'  # 256-colour PNGs (8x smaller); PLATES_PNG=full for RGBA


def save_png(img, path):
    if SMALL:
        img = img.quantize(256, method=Image.Quantize.FASTOCTREE)
    img.save(path, optimize=SMALL, compress_level=9 if SMALL else 7)


def save_plate(S, outdir, name, about):
    os.makedirs(outdir, exist_ok=True)
    order = [n for n in LAYERS if n in S.layers]
    full = None
    layers = []
    for n in order:
        img = S.layers[n].finish()
        save_png(img, os.path.join(outdir, f'{n}.png'))
        full = img.copy() if full is None else Image.alpha_composite(full, img)
        layers.append({'file': f'{n}.png', 'layer': n, 'z': len(layers), 'parallax': PARALLAX[n]})
    full.convert('RGB').save(os.path.join(outdir, 'full.jpg'), quality=88)
    meta = {'name': name, 'about': about, 'biome': S.biome, 'variant': S.variant, 'time': S.time, 'weather': S.weather,
            'season': S.season, 'palette': S.palette, 'seed': S.seed, 'interior': S.interior, 'size': [W, H],
            'layers': layers}
    with open(os.path.join(outdir, 'plate.json'), 'w') as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    return meta


def build(biome, time='day', weather='clear', season='summer', palette='felt', seed=1, variant=0):
    from scenes import BIOMES
    fn, interior = BIOMES[biome]
    if weather == 'snow':
        season = 'winter'
    S = Scene(biome, time, weather, season, palette, seed, variant, interior)
    about = fn(S)
    S.about = about
    return S


def render(spec, outroot):
    name = spec['name']
    S = build(spec['biome'], spec['time'], spec['weather'], spec['season'], spec.get('palette', 'felt'), spec['seed'], spec.get('variant', 0))
    return save_plate(S, os.path.join(outroot, name), name, S.about)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--one')
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--only', default='', help='comma list of biomes for --all')
    ap.add_argument('--time', default='day')
    ap.add_argument('--weather', default='clear')
    ap.add_argument('--season', default='summer')
    ap.add_argument('--palette', default='felt')
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--variant', type=int, default=0)
    ap.add_argument('--out', default='out')
    ap.add_argument('--jobs', type=int, default=os.cpu_count())
    a = ap.parse_args()
    if a.one:
        name = f'{a.one}-v{a.variant}-{a.time}-{a.weather}-{a.season}'
        spec = dict(name=name, biome=a.one, time=a.time, weather=a.weather, season=a.season, palette=a.palette, seed=a.seed, variant=a.variant)
        print(render(spec, a.out)['name'])
    elif a.all:
        from catalog import catalog
        specs = catalog()
        if a.only:
            keep = set(a.only.split(','))
            specs = [s for s in specs if s['biome'] in keep]
        specs = [s for s in specs if not os.path.exists(os.path.join(a.out, s['name'], 'plate.json'))]
        print(len(specs), 'plates to render', flush=True)
        from multiprocessing import Pool
        with Pool(a.jobs) as p:
            for i, m in enumerate(p.imap_unordered(_job, [(s, a.out) for s in specs])):
                print(i + 1, m, flush=True)


def _job(arg):
    s, out = arg
    try:
        return render(s, out)['name']
    except Exception as e:  # keep going; report
        import traceback
        traceback.print_exc()
        return f'FAILED {s["name"]}: {e}'


if __name__ == '__main__':
    main()
