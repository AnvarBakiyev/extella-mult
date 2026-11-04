"""Code-built talking felt puppets (busts), no image generation.

A character is a spec (dict) of interchangeable parts. Every part is drawn with Pillow primitives on its own piece at
2x resolution, reduced to 1024 px and laid on the picture with felt_composite (bevel, wool grain, soft shadow), so each
piece reads as a cut-out of felt glued over the ones beneath.

The picture is built in three passes:
  bare     every piece except the talking face (head, hair, ears, body, clothes, hats ...)      -> drawn once
  face     eyes (sclera, iris, lids), brows, mouth                                                -> redrawn per state
  front    things that sit over the face: nose, moustache, glasses, helmet glass, hand with mic -> redrawn per state
Every state (viseme, blink, expression) is bare + face(state) + front, pixel-aligned with base.png. The saved frames
are full-size 1024x1024 overlays holding only the region of the face that changes (eyes region and/or mouth region),
so `base + overlay` gives the full frame and overlays of different regions stack (talk + blink + expression).

Units: x, y in [0, 1] of the 1024 canvas; y grows downwards.
"""
import math
import random
from contextlib import contextmanager

import numpy as np
from PIL import Image, ImageChops, ImageDraw
from scipy.ndimage import binary_dilation, gaussian_filter

from felt import felt_composite

SS, OUT = 2048, 1024  # drawing resolution, output resolution
_ORG = [0.0, 0.0]  # unit point drawn at the canvas's top-left corner (body parts shift it so a pivot sits mid-canvas)
_STRAIGHT = [False]  # body parts: lay() composites with straight alpha (felt_rgba) instead of felt_composite

# ---------------------------------------------------------------- palette (muted felt)
PAL = {
    'cream': '#ebe2cd', 'oat': '#d6c7a8', 'sand': '#c9ae84', 'mustard': '#c49638', 'ochre': '#b07c30', 'rust': '#a9553a',
    'terracotta': '#bd6b4e', 'brick': '#8c3f33', 'burgundy': '#713039', 'rose': '#c47a7c', 'blush': '#dca196',
    'plum': '#6b4a64', 'lilac': '#9a8bb0', 'navy': '#343f5a', 'denim': '#506889', 'sky': '#8cabc1', 'teal': '#3c7775',
    'mint': '#a4c1a2', 'sage': '#8a986c', 'olive': '#6a6e40', 'forest': '#3c5946', 'moss': '#5e7845', 'coffee': '#684936',
    'chestnut': '#7b4e35', 'charcoal': '#38363a', 'slate': '#5b6270', 'gray': '#8b8987', 'silver': '#b8b6b1',
    'white': '#ece6d9', 'black': '#2b282b', 'butter': '#e2cd88', 'coral': '#d47a62', 'salmon': '#d7896f', 'pine': '#2e4842',
    'wine': '#58293a', 'peach': '#e5b691', 'ink': '#262a36', 'red': '#a5433a', 'gold': '#c9a245', 'steel': '#8e9aa1',
    'tomato': '#c4523f', 'lavender': '#b3a7c6', 'khaki': '#a99a6c', 'orange': '#cf7a3a', 'pink': '#d99aa6',
}
SKIN = {'porcelain': '#efd3bf', 'light': '#e4bd9c', 'olive': '#d0a079', 'tan': '#b88257', 'brown': '#8b5b3d',
        'deep': '#5e3c2a'}
HAIRC = {'black': '#2a2422', 'espresso': '#43302a', 'brown': '#694731', 'auburn': '#86442c', 'ginger': '#b2602f',
         'blonde': '#c7a262', 'ash': '#a39985', 'gray': '#999692', 'white': '#dcd7ce', 'teal': '#3c7775',
         'rose': '#b66f79', 'plumhair': '#6b4a64'}
IRIS = {'brown': '#5a3a26', 'dark': '#2e241f', 'hazel': '#7a6136', 'green': '#55704a', 'blue': '#4e6b89',
        'grayeye': '#6b737a', 'amber': '#c1892e', 'yellow': '#d2a43a', 'cyan': '#4e999f', 'redeye': '#a5433a'}
INK = '#2a2325'      # lash lines, pupils
CAVITY = '#4a2330'   # inside of the mouth
TONGUE = '#b4596a'
TEETH = '#f1ece0'
SCLERA = '#f2eee5'


def col(c, first=None):
    if c is None:
        return None
    if first and c in first:
        return first[c]
    for d in (PAL, SKIN, HAIRC, IRIS):
        if c in d:
            return d[c]
    return c


def rgb(c):
    c = col(c).lstrip('#')
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def hexc(t):
    return '#%02x%02x%02x' % tuple(max(0, min(255, int(round(v)))) for v in t)


def shade(c, k):
    return hexc(v * k for v in rgb(c))


def mix(a, b, t):
    a, b = rgb(a), rgb(b)
    return hexc(a[i] + (b[i] - a[i]) * t for i in range(3))


def lum(c):
    r, g, b = rgb(c)
    return 0.3 * r + 0.59 * g + 0.11 * b


# ---------------------------------------------------------------- geometry helpers
def spline(pts, n=10, closed=False):
    """Catmull-Rom through the points."""
    P = list(pts)
    if len(P) < 3:
        return P
    P = [P[-1]] + P + [P[0], P[1]] if closed else [P[0]] + P + [P[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    if not closed:
        out.append(P[-2])
    return out


def ell_pts(cx, cy, rx, ry, angle=0.0, n=64, a0=0.0, a1=2 * math.pi):
    ca, sa = math.cos(angle), math.sin(angle)
    out = []
    for i in range(n + 1 if a1 - a0 < 2 * math.pi - 1e-6 else n):
        t = a0 + (a1 - a0) * i / n
        x, y = rx * math.cos(t), ry * math.sin(t)
        out.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
    return out


def mirror(pts, cx=0.5):
    return [(2 * cx - x, y) for x, y in pts]


def path_len(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


# ---------------------------------------------------------------- pieces
class Piece:
    """One felt cut-out, drawn at SS resolution."""

    def __init__(self):
        self.im = Image.new('RGBA', (SS, SS), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im, 'RGBA')

    @staticmethod
    def _p(pts):
        ox, oy = _ORG
        return [((x - ox) * SS, (y - oy) * SS) for x, y in pts]

    @staticmethod
    def _c(c, a=255):
        return rgb(c) + (int(a),)

    def poly(self, pts, c, a=255):
        if len(pts) >= 3:
            self.d.polygon(self._p(pts), fill=self._c(c, a))

    def blob(self, pts, c, a=255, n=10):
        self.poly(spline(pts, n, closed=True), c, a)

    def ellipse(self, cx, cy, rx, ry, c, angle=0.0, a=255):
        if angle:
            self.poly(ell_pts(cx, cy, rx, ry, angle), c, a)
        else:
            cx, cy = cx - _ORG[0], cy - _ORG[1]
            self.d.ellipse([(cx - rx) * SS, (cy - ry) * SS, (cx + rx) * SS, (cy + ry) * SS], fill=self._c(c, a))

    def circle(self, cx, cy, r, c, a=255):
        self.ellipse(cx, cy, r, r, c, a=a)

    def line(self, pts, c, w, a=255, caps=True):
        px = self._p(pts)
        wpx = max(1, int(w * SS))
        self.d.line(px, fill=self._c(c, a), width=wpx, joint='curve')
        if caps:
            for x, y in (px[0], px[-1]):
                r = wpx / 2
                self.d.ellipse([x - r, y - r, x + r, y + r], fill=self._c(c, a))

    def curve(self, pts, c, w, a=255):
        self.line(spline(pts, 12), c, w, a)

    def taper(self, pts, c, w0, w1, w2=None, a=255):
        """A stroke whose width goes w0 -> w1 (-> w2) along a smooth path: brows, strands, whiskers."""
        P = spline(pts, 12)
        n = len(P)
        left, right = [], []
        for i, (x, y) in enumerate(P):
            j0, j1 = max(0, i - 1), min(n - 1, i + 1)
            dx, dy = P[j1][0] - P[j0][0], P[j1][1] - P[j0][1]
            L = math.hypot(dx, dy) or 1
            t = i / (n - 1)
            if w2 is None:
                w = w0 + (w1 - w0) * t
            else:
                w = w0 + (w1 - w0) * (t * 2) if t < 0.5 else w1 + (w2 - w1) * (t * 2 - 1)
            nx, ny = -dy / L * w / 2, dx / L * w / 2
            left.append((x + nx, y + ny))
            right.append((x - nx, y - ny))
        self.poly(left + right[::-1], c, a)

    def stitches(self, pts, c, w=0.0032, dash=0.011, gap=0.008, a=200, smooth=True):
        """Running stitch along a path."""
        P = spline(pts, 12) if smooth and len(pts) > 2 else list(pts)
        total, acc, on, seg = path_len(P), 0.0, True, [P[0]]
        if total <= 0:
            return
        for i in range(1, len(P)):
            a0, b0 = P[i - 1], P[i]
            d = math.dist(a0, b0)
            pos = 0.0
            while pos < d:
                need = (dash if on else gap) - acc
                if pos + need <= d:
                    t = (pos + need) / d
                    q = (a0[0] + (b0[0] - a0[0]) * t, a0[1] + (b0[1] - a0[1]) * t)
                    if on:
                        seg.append(q)
                        self.line(seg, c, w, a)
                    seg = [q]
                    on, acc, pos = not on, 0.0, pos + need
                else:
                    if on:
                        seg.append(b0)
                    acc += d - pos
                    pos = d

    def mask(self):
        return self.im.getchannel('A')

    @contextmanager
    def clip(self, mask=None):
        """Draw into a temporary layer, kept only where `mask` (default: what this piece already holds) is set."""
        if mask is None:
            mask = self.mask()
        saved = self.im, self.d
        tmp = Image.new('RGBA', (SS, SS), (0, 0, 0, 0))
        self.im, self.d = tmp, ImageDraw.Draw(tmp, 'RGBA')
        try:
            yield self
        finally:
            tmp.putalpha(ImageChops.multiply(tmp.getchannel('A'), mask))
            self.im, self.d = saved
            self.im.alpha_composite(tmp)

    def fill_mask(self, mask, c, a=255):
        self.im.paste(Image.new('RGBA', (SS, SS), self._c(c, a)), (0, 0), mask)


def shape_mask(fn):
    p = Piece()
    fn(p)
    return p.mask()


def to_layer(piece):
    box = piece.im.getbbox()
    if not box:
        return None
    x0, y0 = max(0, box[0] // 2 * 2 - 4), max(0, box[1] // 2 * 2 - 4)
    x1, y1 = min(SS, (box[2] + 1) // 2 * 2 + 4), min(SS, (box[3] + 1) // 2 * 2 + 4)
    crop = piece.im.crop((x0, y0, x1, y1)).convert('RGBa').reduce(2).convert('RGBA')
    L = Image.new('RGBA', (OUT, OUT), (0, 0, 0, 0))
    L.paste(crop, (x0 // 2, y0 // 2))
    return L


_SKIN = ['felt']  # felt v3 wool kind for skin pieces of the character being drawn ('skin' for people, 'fur' for animals)
_SKIN_PARTS = ('head', 'neck', 'ears_back', 'ears_front', 'muzzle', 'nose')


def lay(img, fn, depth=1.0, flat=False):
    kind = _SKIN[0] if getattr(fn, '__name__', '') in _SKIN_PARTS else 'felt'
    p = Piece()
    fn(p)
    L = to_layer(p)
    if L is None:
        return img
    if flat:
        img.alpha_composite(L)
        return img
    return felt_composite(img, L, depth, kind)  # felt v3 composites premultiplied: fine on transparent parts too


# ---------------------------------------------------------------- heads
# asp: height/width, n: superellipse exponent, wt/wb: width at the top/bottom, chin: narrowing of the jaw,
# bump: lumpiness, jag: fur tufts on the cheeks (amplitude, count)
HEADS = {
    'round': dict(asp=1.02, n=2.0, wt=1.0, wb=1.0),
    'oval': dict(asp=1.22, n=2.2, wt=1.0, wb=0.94),
    'egg': dict(asp=1.12, n=2.2, wt=0.86, wb=1.08),
    'pear': dict(asp=1.1, n=2.5, wt=0.76, wb=1.14),
    'square': dict(asp=1.04, n=3.6, wt=1.0, wb=1.0),
    'long': dict(asp=1.4, n=2.6, wt=1.0, wb=0.95),
    'wide': dict(asp=0.84, n=2.5, wt=1.0, wb=1.02),
    'heart': dict(asp=1.1, n=2.2, wt=1.1, wb=0.78, chin=0.35),
    'diamond': dict(asp=1.12, n=1.75, wt=0.92, wb=0.9),
    'jaw': dict(asp=1.06, n=3.0, wt=0.78, wb=1.16),
    'potato': dict(asp=1.06, n=2.3, wt=0.97, wb=1.04, bump=0.035),
    'moon': dict(asp=0.95, n=2.2, wt=1.0, wb=1.0, flat=0.5),
}


class Head:
    def __init__(self, shape, R=0.2, cx=0.5, cy=0.42, jag=None, wscale=1.0):
        self.p = dict(HEADS[shape])
        self.shape = shape
        asp = self.p['asp']
        self.rx = R / math.sqrt(asp) * wscale
        self.ry = R * math.sqrt(asp)
        self.cx, self.cy = cx, cy
        self.jag = jag

    def pt(self, phi, k=1.0):
        """phi = 0 at the top of the head, growing clockwise (pi/2 = right side, pi = chin)."""
        p = self.p
        s, c = math.sin(phi), math.cos(phi)
        n = p['n']
        if p.get('flat') and c < 0:  # flatter jaw for the moon head
            n = n + p['flat'] * 3 * (-c)
        X = math.copysign(abs(s) ** (2 / n), s)
        Y = math.copysign(abs(c) ** (2 / n), c)
        v = (1 - Y) / 2
        wf = p['wt'] + (p['wb'] - p['wt']) * v
        if p.get('chin') and v > 0.55:
            wf *= 1 - p['chin'] * ((v - 0.55) / 0.45) ** 1.5
        r = 1.0
        if p.get('bump'):
            r += p['bump'] * math.sin(5 * phi + 0.7) + p['bump'] * 0.6 * math.sin(3 * phi)
        if self.jag:
            amp, cnt, a0, a1 = self.jag
            ph = abs(phi)
            if a0 < ph < a1:
                u = (ph - a0) / (a1 - a0)
                saw = abs(((u * cnt) % 1.0) - 0.5) * 2  # 1 at the tips
                r += amp * saw * math.sin(math.pi * u)
        return (self.cx + k * r * self.rx * X * wf, self.cy - k * r * self.ry * Y)

    def outline(self, k=1.0, n=180):
        return [self.pt(-math.pi + 2 * math.pi * i / n, k) for i in range(n)]

    def arc(self, a0, a1, k=1.0, n=60):
        return [self.pt(a0 + (a1 - a0) * i / n, k) for i in range(n + 1)]

    def phi_at_y(self, y, side=1):
        lo, hi = 0.0, math.pi
        for _ in range(40):
            mid = (lo + hi) / 2
            if self.pt(mid)[1] < y:
                lo = mid
            else:
                hi = mid
        return side * (lo + hi) / 2

    def half_w(self, y):
        return self.pt(self.phi_at_y(y))[0] - self.cx

    @property
    def top(self):
        return self.cy - self.ry

    @property
    def chin(self):
        return self.pt(math.pi)[1]


# ---------------------------------------------------------------- kits (animals and specials)
# Each kit sets defaults; the spec can override them. 'ears' names the ear drawer.
KITS = {
    'fox': dict(head='heart', fur='orange', fur2='cream', ears='fox', nose='snout', nose_col='black', eyes='narrow',
                iris='amber', jag=(0.09, 3, 1.35, 2.35), muzzle='fox', lid_fur=True),
    'bear': dict(head='round', fur='chestnut', fur2='sand', ears='bear', nose='snout', nose_col='black', eyes='bead',
                 muzzle='bear', R=0.21),
    'cat': dict(head='wide', fur='gray', fur2='cream', ears='cat', nose='cat', eyes='round', iris='green',
                jag=(0.05, 3, 1.45, 2.2), muzzle='cat', whiskers=True),
    'dog': dict(head='egg', fur='sand', fur2='cream', ears='dog', nose='snout', nose_col='black', eyes='round',
                iris='brown', muzzle='dog'),
    'owl': dict(head='wide', fur='coffee', fur2='oat', ears='owl', nose='none', eyes='wide', iris='amber',
                muzzle='owl', beak=True, R=0.215),
    'salmon': dict(head='egg', fur='salmon', fur2='peach', ears='fins', nose='none', eyes='round', iris='hazel',
                   muzzle='fish', lip_col='#b65a5a', mouth_w=1.15),
    'frog': dict(head='wide', fur='moss', fur2='#c3c98c', ears='none', nose='dots', eyes='round', iris='amber',
                 muzzle='frog', frog_eyes=True, mouth_w=1.3),
    'mouse': dict(head='heart', fur='gray', fur2='#ddd2c8', ears='mouse', nose='mouse', eyes='bead', muzzle='mouse',
                  whiskers=True, R=0.19),
    'hare': dict(head='oval', fur='oat', fur2='white', ears='hare', nose='hare', eyes='round', iris='brown',
                 muzzle='hare', whiskers=True, R=0.185, cy=0.45),
    'pig': dict(head='round', fur='pink', fur2='#e9b9b4', ears='pig', nose='pig', eyes='bead', muzzle=None),
    # specials
    'robot': dict(head='square', fur='steel', fur2='silver', ears='bolts', nose='none', eyes='round', iris='cyan',
                  muzzle='robot', lip_col='#5b6870', robot=True),
    'imp': dict(head='heart', fur='#a8483f', fur2=None, ears='pointy', nose='button', eyes='narrow', iris='yellow',
                horns=True, brow='angry'),
    'monster': dict(head='potato', fur='lilac', fur2='lavender', ears='none', nose='ball', eyes='wide', iris='green',
                    jag=(0.07, 7, 0.0, 3.14), mouth_w=1.25),
    'sheep': dict(head='egg', fur='#d9c7ad', fur2='#4a3d3a', wool_col='#f1ebdf', ears='sheep', nose='sheep', eyes='bead', muzzle='sheep',
                  wool=True),
}
ANIMAL_KITS = ['fox', 'bear', 'cat', 'dog', 'owl', 'salmon', 'frog', 'mouse', 'hare', 'pig']

EYE_TYPES = {  # base lid positions (0 open .. 1 closed), size factor, iris factor
    'round': dict(top=0.14, bot=0.0, size=1.0, iris=0.62, asp=1.12),
    'sleepy': dict(top=0.46, bot=0.06, size=0.96, iris=0.64, asp=1.05),
    'wide': dict(top=0.0, bot=0.0, size=1.12, iris=0.46, asp=1.12),
    'narrow': dict(top=0.22, bot=0.12, size=0.98, iris=0.68, asp=0.72),
    'bead': dict(top=0.0, bot=0.0, size=0.62, iris=0.0, asp=1.15),
}
BROWS = ['neutral', 'angry', 'worried', 'raised']
NOSES = ['ball', 'button', 'long', 'hooked', 'wide', 'snout', 'pig', 'beak']  # + kit variants (cat, mouse, hare, dots ...)
HAIR = ['bald', 'horseshoe', 'buzz', 'short', 'sidepart', 'quiff', 'spiky', 'curly', 'bob', 'long', 'ponytail',
        'bun', 'braids', 'wavy', 'mohawk', 'kerchief', 'topknot']
OUTFITS = ['sweater', 'suit', 'labcoat', 'hoodie', 'overalls', 'dress', 'uniform', 'chef', 'robe', 'vest', 'tshirt',
           'shirt', 'spacesuit']
HATS = ['cap', 'beanie', 'tubeteika', 'kalpak', 'toque', 'fedora', 'beret', 'straw', 'hardhat', 'bowler']
ACCESSORIES = ['glasses', 'hat', 'headphones', 'scarf', 'earrings', 'mic', 'stethoscope', 'bowtie', 'necklace',
               'pencil', 'lanyard', 'helmet', 'headset', 'flower']
VISEMES = ['closed', 'A', 'E', 'O', 'U', 'MBP']
EXPRESSIONS = ['neutral', 'happy', 'angry', 'shocked']
VOICES = ['journalist', 'salmon', 'lady', 'deep', 'ad', 'narrator', 'odessa', 'gogi', 'fairy', 'calm']


# ---------------------------------------------------------------- mouth shapes (unit = half the mouth width)
def _mouth_open(v):
    if v == 'A':
        return spline([(-0.84, -0.06), (-0.4, -0.13), (0, -0.14), (0.4, -0.13), (0.84, -0.06), (0.7, 0.2), (0.4, 0.5),
                       (0, 0.62), (-0.4, 0.5), (-0.7, 0.2)], closed=True)
    if v == 'E':
        return spline([(-1.0, -0.01), (-0.55, -0.13), (0, -0.16), (0.55, -0.13), (1.0, -0.01), (0.6, 0.18),
                       (0, 0.25), (-0.6, 0.18)], closed=True)
    if v == 'O':
        return ell_pts(0, 0.12, 0.4, 0.48)
    if v == 'U':
        return ell_pts(0, 0.06, 0.2, 0.22)
    if v == 'smile':
        return spline([(-0.95, -0.14), (-0.5, -0.06), (0, -0.04), (0.5, -0.06), (0.95, -0.14), (0.7, 0.22), (0.35, 0.46),
                       (0, 0.52), (-0.35, 0.46), (-0.7, 0.22)], closed=True)
    if v == 'shock':
        return ell_pts(0, 0.24, 0.42, 0.62)
    if v == 'grit':
        return spline([(-0.82, 0.12), (-0.45, -0.02), (0, -0.06), (0.45, -0.02), (0.82, 0.12), (0.62, 0.26), (0, 0.24),
                       (-0.62, 0.26)], closed=True)
    return None


TEETH_TOP = {'A': 0.13, 'E': 0.11, 'smile': 0.14, 'grit': 0.12, 'O': 0.07}
TEETH_BOT = {'E': 0.08, 'grit': 0.11}
TONGUE_Y = {'A': (0.4, 0.42, 0.22), 'O': (0.38, 0.26, 0.18), 'smile': (0.36, 0.42, 0.16), 'shock': (0.6, 0.28, 0.2)}


class Character:
    def __init__(self, spec):
        _SKIN[0] = 'skin' if spec.get('kind') == 'person' else 'fur'
        s = dict(spec)
        self.kit = s.get('kit')
        if self.kit:
            for k, v in KITS[self.kit].items():
                s.setdefault(k, v)
        s.setdefault('kind', 'animal' if self.kit in ANIMAL_KITS else (self.kit or 'person'))
        s.setdefault('head', 'round')
        s.setdefault('age', 'adult')
        s.setdefault('eyes', 'round')
        s.setdefault('brow', 'neutral')
        s.setdefault('nose', 'ball')
        s.setdefault('outfit', 'sweater')
        s.setdefault('hair', 'short' if not self.kit else 'none')
        s.setdefault('acc', [])
        s.setdefault('build', 'normal')
        self.s = s
        self.rnd = random.Random(s['name'])
        age = s['age']
        # colours
        skin = col(s.get('fur') or s.get('skin') or 'light', SKIN)
        self.skin = skin
        self.skin2 = col(s.get('fur2')) if s.get('fur2') else None
        self.hair_col = col(s.get('hair_col', 'espresso'), HAIRC)
        self.brow_col = col(s.get('brow_col')) if s.get('brow_col') else (
            shade(self.hair_col, 0.85) if s['hair'] not in ('bald', 'none') or s.get('hair_col') else shade(skin, 0.55))
        if self.kit and not s.get('brow_col'):
            self.brow_col = shade(skin, 0.55)
        self.iris = col(s.get('iris', 'brown'), IRIS)
        self.lid = shade(skin, 0.94)
        self.lip = col(s.get('lip_col')) if s.get('lip_col') else mix(shade(skin, 0.68), '#7a3040', 0.25)
        self.o1 = col(s.get('o1', 'teal'))
        self.o2 = col(s.get('o2', 'cream'))
        self.o3 = col(s.get('o3', 'mustard'))
        # geometry
        R = s.get('R', {'kid': 0.19, 'young': 0.198, 'adult': 0.2, 'old': 0.2}[age])
        cy = s.get('cy', 0.45 if age != 'kid' else 0.47)
        self.sh_y = 0.765 if age != 'kid' else 0.785
        G = Head(s['head'], R, 0.5, cy, jag=s.get('jag'), wscale=s.get('wscale', 1.0))
        if 'cy' not in spec:  # sit the chin a short neck above the shoulders
            gap = 0.105 if s['kind'] == 'person' else 0.08
            dy = (self.sh_y - gap) - G.chin
            dy = max(dy, 0.215 - G.top)
            G = Head(s['head'], R, 0.5, cy + dy, jag=s.get('jag'), wscale=s.get('wscale', 1.0))
        self.G = G
        et = EYE_TYPES[s['eyes']]
        self.et = et
        base = 0.205 * G.rx * et['size'] * {'kid': 1.12, 'young': 1.03, 'adult': 1.0, 'old': 0.94}[age]
        base *= s.get('eye_scale', 1.0)
        self.erx, self.ery = base, base * et['asp']
        self.eye_dx = G.rx * s.get('eye_sep', 0.37)
        self.eye_y = G.cy - G.ry * s.get('eye_up', 0.16)
        if s.get('frog_eyes'):
            self.eye_y = G.top + G.ry * 0.02
            self.eye_dx = G.rx * 0.5
        self.mouth_y = G.cy + G.ry * s.get('mouth_down', 0.5)
        self.mouth_w = G.rx * 0.47 * s.get('mouth_w', 1.0)
        if s.get('beak'):
            self.mouth_y = G.cy + G.ry * 0.26
        if s.get('frog_eyes'):
            self.mouth_y = G.cy + G.ry * 0.35
        self.nose_y = G.cy + G.ry * s.get('nose_down', 0.16)
        self.W = {'slim': 0.27, 'normal': 0.31, 'broad': 0.355}[s['build']] * (0.9 if age == 'kid' else 1.0)
        if self.kit in ('bear', 'monster'):
            self.W *= 1.07
        self.neck_w = 0.06 if s['kind'] == 'person' else 0.085
        if s['kind'] in ('robot', 'imp'):
            self.neck_w = 0.05
        self.split_y = (self.eye_y + self.ery + self.mouth_y - 0.25 * self.mouth_w) / 2
        if s.get('beak'):
            self.split_y = self.eye_y + self.ery * 1.15

    # ------------------------------------------------------------ public
    def bare(self):
        img = Image.new('RGBA', (OUT, OUT), (0, 0, 0, 0))
        for fn, depth, flat in self.base_parts():
            lay(img, fn, depth, flat)
        return img

    def state(self, expr='neutral', mouth=None, blink=False):
        et = self.et
        top0 = self.s.get('lid_top', et['top'])
        st = dict(top=top0, bot=et['bot'], tilt=0.0, iris=1.0, brow=self.s['brow'], lift=0.0, mouth='closed', look=0.0)
        if expr == 'happy':
            st.update(top=top0 * 0.7, bot=0.42, brow='raised', lift=-0.15, mouth='smile')
        elif expr == 'angry':
            st.update(top=max(top0, 0.3), bot=max(et['bot'], 0.12), tilt=0.42, brow='angry', mouth='grit')
        elif expr == 'shocked':
            st.update(top=0.0, bot=0.0, iris=0.72, brow='raised', lift=0.35, mouth='shock')
        if mouth:
            st['mouth'] = mouth
        if blink:
            st.update(top=1.0, bot=0.0)
        return st

    def frame(self, bare, st):
        img = bare.copy()
        for fn, depth, flat in self.face_parts(st) + self.front_parts():
            lay(img, fn, depth, flat)
        return img

    # ------------------------------------------------------------ assembly lists
    def base_parts(self):
        s, out = self.s, []
        add = lambda fn, d=1.0, flat=False: out.append((fn, d, flat))
        hair = HAIR_DRAW.get(s['hair'])
        hat = self.hat()
        head_only = getattr(self, 'head_only', False)  # full-body rig: body pieces and the hair behind them are own parts
        if hair and hair.get('back') and not head_only:
            add(lambda P: hair['back'](self, P), 0.9)
        if not head_only:
            if s['outfit'] == 'hoodie':
                add(lambda P: self.hood(P), 0.9)
            add(self.neck, 0.7)
            for fn, d in OUTFIT_DRAW[s['outfit']](self):
                add(fn, d)
        if hair and hair.get('over'):
            add(lambda P: hair['over'](self, P), 0.9)
        if not head_only:
            if 'scarf' in self.acc_names():
                add(self.scarf, 1.0)
            for name in ('necklace', 'stethoscope', 'lanyard', 'bowtie', 'flower'):
                if name in self.acc_names():
                    add(getattr(self, 'acc_' + name), 0.6)
        add(self.ears_back, 0.8)
        if s.get('wool'):
            add(self.wool_back, 1.0)
        add(self.head, 1.0)
        if s.get('frog_eyes'):
            add(self.frog_bumps, 0.9)
        add(self.face_paint, 0.35)
        if s.get('muzzle'):
            add(self.muzzle, 0.55)
        add(self.ears_front, 0.8)
        if s.get('facial') in ('beard', 'goatee', 'stubble', 'chinstrap'):
            add(self.beard, 0.8 if s['facial'] != 'stubble' else 0.2)
        if hair and hair.get('front'):
            add(lambda P: hair['front'](self, P), 0.9)
        if s.get('wool'):
            add(self.wool_top, 1.0)
        if s.get('horns'):
            add(self.horns, 0.9)
        if s.get('robot'):
            add(self.antenna, 0.8)
        if 'earrings' in self.acc_names():
            add(self.acc_earrings, 0.5)
        if 'headphones' in self.acc_names() or 'headset' in self.acc_names():
            add(self.headphones, 0.9)
        if hat:
            for fn, d in HAT_DRAW[hat[1] if len(hat) > 1 else 'cap'](self, hat):
                add(fn, d)
        if hat and s.get('ears') == 'hare':
            add(self.ears_back, 0.8)
        if 'pencil' in self.acc_names():
            add(self.acc_pencil, 0.6)
        return out

    def face_parts(self, st):
        out = []
        add = lambda fn, d=1.0, flat=False: out.append((fn, d, flat))
        add(lambda P: self.sclera(P), 0.55)
        if self.et['iris'] > 0 or True:
            add(lambda P: self.iris_piece(P, st), 0.22)
        add(lambda P: self.lids(P, st), 0.45)
        if not self.s.get('no_brows'):
            add(lambda P: self.brows(P, st), 0.6)
        if self.s.get('beak'):
            add(lambda P: self.beak(P, st['mouth']), 0.8)
        else:
            add(lambda P: self.mouth_cavity(P, st['mouth']), 0.18)
            add(lambda P: self.mouth_lips(P, st['mouth']), 0.5)
        return out

    def front_parts(self):
        s, out = self.s, []
        add = lambda fn, d=1.0, flat=False: out.append((fn, d, flat))
        if s['nose'] not in ('none',) and not s.get('beak'):
            add(self.nose, 0.85)
        if s.get('facial') in ('mustache', 'walrus', 'beard'):
            add(self.mustache, 0.8)
        if s.get('whiskers'):
            add(self.whiskers, 0.25)
        if 'glasses' in self.acc_names():
            add(self.glasses, 0.45)
        if 'headset' in self.acc_names():
            add(self.headset_mic, 0.5)
        if (s.get('hands') or 'mic' in self.acc_names()) and not getattr(self, 'head_only', False):
            for fn, d in self.hands():
                add(fn, d)
        if 'helmet' in self.acc_names():
            add(self.helmet_glass, 0.35, False)
        return out

    def acc_names(self):
        return [a[0] if isinstance(a, (tuple, list)) else a for a in self.s['acc']]

    def acc(self, name):
        for a in self.s['acc']:
            a = a if isinstance(a, (tuple, list)) else (a,)
            if a[0] == name:
                return a
        return None

    def hat(self):
        return self.acc('hat')

    # ------------------------------------------------------------ body
    def neck(self, P):
        G, nw = self.G, self.neck_w
        y0 = G.chin - 0.06
        c = shade(self.skin, 0.86)
        if self.s.get('robot'):
            for i in range(5):
                y = y0 + 0.03 + i * 0.04
                P.blob([(0.5 - nw, y - 0.015), (0.5 + nw, y - 0.015), (0.5 + nw * 1.05, y + 0.016), (0.5 - nw * 1.05, y + 0.016)],
                       shade(self.skin, 0.8 + 0.06 * (i % 2)))
            return
        P.poly([(0.5 - nw, y0), (0.5 + nw, y0), (0.5 + nw * 1.12, 0.84), (0.5 - nw * 1.12, 0.84)], c)

    def torso_pts(self, neck='crew', W=None, top=None, vdepth=0.1, notch_w=None):
        W = W or self.W
        sy = self.sh_y
        nw = notch_w or self.neck_w * 1.55
        ny = sy - 0.045 if top is None else top
        body = getattr(self, 'body_ref', None)
        if body is not None:  # full-body puppet: shoulders down to the waist, rounded under the waist pivot
            wy = body.waist
            left = spline([(0.5 - W * 0.8, wy + 0.055), (0.5 - W * 0.86, wy - 0.02), (0.5 - W * 0.93, sy + 0.12),
                           (0.5 - W * 0.97, sy + 0.05), (0.5 - W * 0.8, sy + 0.002), (0.5 - W * 0.5, sy - 0.022),
                           (0.5 - nw * 1.1, ny + 0.004)], 8)
        else:
            left = spline([(0.5 - W * 1.08, 1.06), (0.5 - W * 1.03, 0.92), (0.5 - W * 0.93, sy + 0.035),
                           (0.5 - W * 0.7, sy - 0.012), (0.5 - nw * 1.1, ny + 0.004)], 8)
        if neck == 'crew':
            mid = spline([(0.5 - nw, ny), (0.5, ny + 0.03), (0.5 + nw, ny)], 8)
        elif neck == 'v':
            mid = [(0.5 - nw, ny), (0.5, ny + vdepth), (0.5 + nw, ny)]
        elif neck == 'high':
            mid = spline([(0.5 - nw * 0.95, ny - 0.045), (0.5, ny - 0.035), (0.5 + nw * 0.95, ny - 0.045)], 8)
        elif neck == 'wrap':
            mid = [(0.5 - nw, ny), (0.5 + nw * 0.35, ny + vdepth), (0.5 + nw, ny)]
        elif neck == 'scoop':
            mid = spline([(0.5 - nw * 1.2, ny), (0.5, ny + 0.065), (0.5 + nw * 1.2, ny)], 8)
        else:
            mid = []
        right = [(1 - x, y) for x, y in left[::-1]]
        if body is not None:
            wy = body.waist
            return left + mid + right + spline([(0.5 + W * 0.8, wy + 0.055), (0.5, wy + 0.072), (0.5 - W * 0.8, wy + 0.055)], 8)[1:-1]
        return left + mid + right

    def body(self, P, c, neck='crew', **kw):
        P.poly(self.torso_pts(neck, **kw), c)

    def hood(self, P):
        c = shade(self.o1, 0.82)
        P.blob([(0.5 - self.W * 0.82, self.sh_y + 0.02), (0.5 - self.W * 0.6, self.sh_y - 0.075), (0.5, self.sh_y - 0.1),
                (0.5 + self.W * 0.6, self.sh_y - 0.075), (0.5 + self.W * 0.82, self.sh_y + 0.02), (0.5, self.sh_y + 0.03)], c)

    # ------------------------------------------------------------ head
    def head(self, P):
        G = self.G
        P.poly(G.outline(), self.skin)
        s = self.s
        with P.clip():
            if s.get('robot'):
                P.poly([(0, G.cy + G.ry * 0.35), (1, G.cy + G.ry * 0.35), (1, 1), (0, 1)], shade(self.skin, 0.9))
                for sx in (-1, 1):
                    for yy in (-0.7, 0.75):
                        P.circle(0.5 + sx * G.rx * 0.82, G.cy + yy * G.ry, 0.008, shade(self.skin, 0.7))
                        P.circle(0.5 + sx * G.rx * 0.82 - 0.002, G.cy + yy * G.ry - 0.002, 0.004, mix(self.skin, '#ffffff', 0.4))
                P.stitches([(G.cx - G.rx, G.cy + G.ry * 0.35), (G.cx + G.rx, G.cy + G.ry * 0.35)], shade(self.skin, 0.6),
                           smooth=False)
            if self.kit == 'salmon':
                for i in range(4):
                    for j in range(7):
                        x = G.cx - G.rx + (j + 0.5 * (i % 2)) * G.rx / 3
                        y = G.top + 0.025 + i * 0.032
                        P.line(ell_pts(x, y, 0.028, 0.02, 0, 16, 0.2, math.pi - 0.2), shade(self.skin, 0.84), 0.004)
                for sx in (-1, 1):
                    P.curve([(0.5 + sx * G.rx * 0.6, G.cy - G.ry * 0.05), (0.5 + sx * G.rx * 0.72, G.cy + G.ry * 0.25),
                             (0.5 + sx * G.rx * 0.6, G.cy + G.ry * 0.55)], shade(self.skin, 0.78), 0.006)
                for k in range(9):
                    r = self.rnd
                    P.circle(G.cx + (r.random() - 0.5) * G.rx * 1.6, G.top + 0.03 + r.random() * 0.08, 0.006, shade(self.skin, 0.62))
            if self.kit == 'cat' and s.get('tabby', True):
                for dx in (-0.03, 0, 0.03):
                    P.taper([(0.5 + dx, G.top + 0.005), (0.5 + dx * 1.1, G.top + 0.05)], shade(self.skin, 0.7), 0.012, 0.002)
            if s.get('panda'):
                for sx in (-1, 1):
                    P.ellipse(0.5 + sx * self.eye_dx * 1.05, self.eye_y + 0.008, self.erx * 2.3, self.ery * 1.9, '#2f2b2e',
                              angle=-sx * 0.5)
            if self.kit == 'dog' and s.get('patch'):
                P.ellipse(0.5 + self.eye_dx * 1.05, self.eye_y - 0.01, self.erx * 2.2, self.ery * 2.0, shade(self.skin, 0.62), 0.4)
            if self.kit == 'owl':
                for i in range(3):
                    for j in range(5):
                        x = G.cx + (j - 2) * 0.045 + (0.022 if i % 2 else 0)
                        y = G.top + 0.035 + i * 0.03
                        P.line([(x - 0.012, y - 0.008), (x, y + 0.004), (x + 0.012, y - 0.008)], shade(self.skin, 0.75), 0.005)

    def face_paint(self, P):
        """Flat markings on the face: blush, freckles, wrinkles, dimples."""
        G, s = self.G, self.s
        if s['kind'] == 'person' or s.get('blush') or self.kit in ('pig', 'mouse', 'hare', 'bear', 'imp'):
            if s.get('blush', True):
                bc = mix(self.skin, '#c85a5a', 0.38)
                for sx in (-1, 1):
                    P.ellipse(0.5 + sx * G.rx * 0.6, self.nose_y + 0.03, G.rx * 0.17, G.rx * 0.11, bc, a=105)
        if s.get('freckles'):
            r = random.Random(s['name'] + 'f')
            for sx in (-1, 1):
                for k in range(7):
                    P.circle(0.5 + sx * G.rx * (0.35 + 0.35 * r.random()), self.nose_y - 0.01 + 0.04 * r.random(), 0.0035,
                             shade(self.skin, 0.72))
        if s['age'] == 'old' or s.get('wrinkles'):
            wc = shade(self.skin, 0.78)
            fy = G.top + G.ry * 0.38
            for i in range(2):
                y = fy + i * 0.014
                P.curve([(0.5 - G.rx * 0.32, y + 0.004), (0.5, y - 0.004), (0.5 + G.rx * 0.32, y + 0.004)], wc, 0.004)
            for sx in (-1, 1):
                P.curve([(0.5 + sx * G.rx * 0.36, self.nose_y + 0.025), (0.5 + sx * G.rx * 0.5, self.mouth_y - 0.01),
                         (0.5 + sx * G.rx * 0.5, self.mouth_y + 0.025)], wc, 0.0045)
        if s.get('scar'):
            P.line([(0.5 + G.rx * 0.45, G.cy - 0.03), (0.5 + G.rx * 0.6, G.cy + 0.03)], shade(self.skin, 0.7), 0.005)
        if s.get('kind') == 'robot':
            pass

    def muzzle(self, P):
        G, m, c2 = self.G, self.s['muzzle'], self.skin2 or mix(self.skin, '#ffffff', 0.5)
        my, ny = self.mouth_y, self.nose_y
        if m == 'fox':
            P.blob([(0.5 - G.rx * 0.95, G.cy + 0.0), (0.5 - G.rx * 0.45, ny - 0.01), (0.5, ny - 0.03),
                    (0.5 + G.rx * 0.45, ny - 0.01), (0.5 + G.rx * 0.95, G.cy + 0.0), (0.5 + G.rx * 0.5, my + 0.05),
                    (0.5, G.chin - 0.005), (0.5 - G.rx * 0.5, my + 0.05)], c2)
        elif m in ('bear', 'dog', 'cat', 'mouse', 'hare', 'sheep'):
            k = {'bear': (0.55, 0.62), 'dog': (0.6, 0.6), 'cat': (0.42, 0.42), 'mouse': (0.38, 0.4), 'hare': (0.36, 0.38),
                 'sheep': (0.0, 0.0)}[m]
            if k[0]:
                for sx in (-1, 1):
                    P.ellipse(0.5 + sx * G.rx * k[0] * 0.48, ny + 0.035, G.rx * k[0] * 0.62, G.ry * k[1] * 0.42, c2)
                if m in ('bear', 'dog'):
                    P.ellipse(0.5, my + 0.02, G.rx * k[0] * 0.95, G.ry * 0.28, c2)
        elif m == 'owl':
            for sx in (-1, 1):
                P.circle(0.5 + sx * self.eye_dx, self.eye_y + 0.004, self.erx * 1.85, c2)
            P.stitches(spline([(0.5 - self.eye_dx * 2.05, self.eye_y), (0.5 - self.eye_dx, self.eye_y - self.erx * 1.95),
                               (0.5, self.eye_y - self.erx * 0.6)], 6), shade(c2, 0.7))
            P.stitches(spline([(0.5 + self.eye_dx * 2.05, self.eye_y), (0.5 + self.eye_dx, self.eye_y - self.erx * 1.95),
                               (0.5, self.eye_y - self.erx * 0.6)], 6), shade(c2, 0.7))
        elif m == 'fish':
            P.ellipse(0.5, my + 0.01, G.rx * 0.8, G.ry * 0.36, c2)
        elif m == 'frog':
            P.ellipse(0.5, G.chin - G.ry * 0.12, G.rx * 0.78, G.ry * 0.3, c2)
        elif m == 'robot':
            P.blob([(0.5 - self.mouth_w * 1.35, my - 0.035), (0.5 + self.mouth_w * 1.35, my - 0.035),
                    (0.5 + self.mouth_w * 1.4, my + 0.065), (0.5 - self.mouth_w * 1.4, my + 0.065)], shade(self.skin, 0.82), n=4)

    # ------------------------------------------------------------ ears
    def ears_back(self, P):
        G, e, c = self.G, self.s.get('ears', 'human'), self.skin
        inner = mix(self.skin, '#d98a96', 0.55)
        if self.s['kind'] == 'person' and e == 'human' or e == 'human':
            for sx in (-1, 1):
                x = 0.5 + sx * (G.half_w(G.cy + 0.01) - 0.004)
                P.ellipse(x + sx * 0.012, G.cy + 0.02, 0.032, 0.05, c)
                P.ellipse(x + sx * 0.014, G.cy + 0.022, 0.016, 0.03, shade(c, 0.86))
        elif e == 'fox' or e == 'cat':
            big = 1.25 if e == 'fox' else 1.0
            for sx in (-1, 1):
                bx = 0.5 + sx * G.rx * 0.55
                by = G.top + G.ry * 0.25
                tip = (0.5 + sx * G.rx * 0.85, G.top - 0.105 * big)
                base = [(bx - sx * 0.065 * big, by), (tip[0], tip[1]), (bx + sx * 0.075 * big, by + 0.06)]
                P.blob([base[0], ((base[0][0] + tip[0]) / 2 - sx * 0.006, (base[0][1] + tip[1]) / 2), tip,
                        ((base[2][0] + tip[0]) / 2 + sx * 0.012, (base[2][1] + tip[1]) / 2), base[2]], c, n=6)
                with P.clip():
                    if e == 'fox':
                        P.circle(tip[0], tip[1], 0.05, self.s.get('ear_tip', '#3a2c28'))
                ix = [(bx - sx * 0.035 * big, by + 0.01), (tip[0] - sx * 0.006, tip[1] + 0.035), (bx + sx * 0.04 * big, by + 0.04)]
                P.blob(ix, self.skin2 if e == 'fox' and self.skin2 else inner, n=6)
        elif e == 'bear':
            for sx in (-1, 1):
                x, y = 0.5 + sx * G.rx * 0.75, G.top + G.ry * 0.2
                ec = '#2f2b2e' if self.s.get('panda') else c
                P.circle(x, y, G.rx * 0.36, ec)
                P.circle(x, y + 0.006, G.rx * 0.2, shade(ec, 1.4) if self.s.get('panda') else (self.skin2 or shade(c, 0.8)))
        elif e == 'mouse':
            for sx in (-1, 1):
                x, y = 0.5 + sx * G.rx * 0.95, G.top + G.ry * 0.12
                P.circle(x, y, G.rx * 0.6, c)
                P.circle(x, y + 0.008, G.rx * 0.4, inner)
        elif e == 'hare':
            for sx in (-1, 1):
                x = 0.5 + sx * G.rx * 0.42
                ang = sx * 0.16
                P.ellipse(x + sx * 0.02, G.top - 0.105, 0.052, 0.155, c, angle=ang)
                P.ellipse(x + sx * 0.02, G.top - 0.095, 0.026, 0.12, inner, angle=ang)
        elif e == 'pig':
            for sx in (-1, 1):
                x, y = 0.5 + sx * G.rx * 0.62, G.top + G.ry * 0.1
                P.blob([(x - sx * 0.06, y + 0.04), (x + sx * 0.02, y - 0.09), (x + sx * 0.085, y + 0.025)], c, n=6)
        elif e == 'owl':
            for sx in (-1, 1):
                x, y = 0.5 + sx * G.rx * 0.7, G.top + G.ry * 0.16
                pts = [(x - sx * 0.06, y + 0.03), (x + sx * 0.02, y - 0.06), (x + sx * 0.07, y - 0.13),
                       (x + sx * 0.075, y - 0.05), (x + sx * 0.09, y + 0.03)]
                P.poly(pts, shade(c, 0.82))
                with P.clip():
                    for k in range(3):
                        P.line([(x + sx * (0.0 + 0.02 * k), y + 0.03), (x + sx * (0.05 + 0.008 * k), y - 0.1 + 0.03 * k)],
                               shade(c, 0.6), 0.004)
        elif e == 'fins':
            for sx in (-1, 1):
                x, y = 0.5 + sx * G.rx * 0.92, G.cy + G.ry * 0.25
                pts = [(x, y - 0.05), (x + sx * 0.1, y - 0.07), (x + sx * 0.12, y + 0.0), (x + sx * 0.09, y + 0.07), (x, y + 0.05)]
                P.blob(pts, shade(c, 0.9), n=6)
                with P.clip():
                    for k in range(4):
                        P.line([(x, y), (x + sx * 0.13, y - 0.065 + k * 0.043)], shade(c, 0.72), 0.004)
            # dorsal fin on the crown
            pts = [(0.5 - 0.06, G.top + 0.03), (0.5 - 0.035, G.top - 0.06), (0.5 + 0.02, G.top - 0.085),
                   (0.5 + 0.07, G.top - 0.04), (0.5 + 0.07, G.top + 0.04)]
            P.blob(pts, shade(c, 0.85), n=6)
            with P.clip():
                for k in range(5):
                    P.line([(0.5, G.top + 0.03), (0.5 - 0.06 + k * 0.035, G.top - 0.1)], shade(c, 0.68), 0.004)
        elif e == 'bolts':
            for sx in (-1, 1):
                x = 0.5 + sx * (G.rx + 0.01)
                P.blob([(x - 0.025, G.cy - 0.04), (x + sx * 0.03, G.cy - 0.035), (x + sx * 0.03, G.cy + 0.035),
                        (x - 0.025, G.cy + 0.04)], shade(c, 0.78), n=4)
        elif e == 'pointy':
            for sx in (-1, 1):
                x = 0.5 + sx * (G.half_w(G.cy) - 0.01)
                P.blob([(x, G.cy - 0.04), (x + sx * 0.1, G.cy - 0.085), (x + sx * 0.04, G.cy + 0.01), (x, G.cy + 0.05)], c, n=5)
                P.blob([(x + sx * 0.008, G.cy - 0.03), (x + sx * 0.07, G.cy - 0.065), (x + sx * 0.03, G.cy + 0.0)],
                       shade(c, 0.8), n=5)
        elif e == 'sheep':
            for sx in (-1, 1):
                x = 0.5 + sx * (G.rx * 0.9)
                P.ellipse(x + sx * 0.045, G.top + G.ry * 0.42, 0.065, 0.026, self.skin, angle=sx * 0.35)
                P.ellipse(x + sx * 0.05, G.top + G.ry * 0.42, 0.04, 0.012, mix(self.skin, '#d98a96', 0.4), angle=sx * 0.35)

    def ears_front(self, P):
        G, e = self.G, self.s.get('ears')
        if e == 'dog':
            c = shade(self.skin, self.s.get('ear_shade', 0.72))
            for sx in (-1, 1):
                x = 0.5 + sx * G.rx * 0.88
                P.blob([(x - sx * 0.05, G.top + 0.03), (x + sx * 0.04, G.top + 0.02), (x + sx * 0.075, G.cy + 0.03),
                        (x + sx * 0.03, G.cy + 0.11), (x - sx * 0.025, G.cy + 0.06)], c, n=8)
        if e == 'pig':
            for sx in (-1, 1):
                x, y = 0.5 + sx * G.rx * 0.62, G.top + G.ry * 0.12
                P.blob([(x - sx * 0.035, y + 0.0), (x + sx * 0.06, y - 0.02), (x + sx * 0.08, y + 0.07)], shade(self.skin, 0.93), n=6)

    def frog_bumps(self, P):
        for sx in (-1, 1):
            P.circle(0.5 + sx * self.eye_dx, self.eye_y, self.erx * 1.45, self.skin)

    def wool_back(self, P):
        G = self.G
        r = random.Random(self.s['name'] + 'w')
        for k in range(26):
            a = -2.0 + 4.0 * k / 25
            x, y = G.pt(a, 1.05)
            P.circle(x, y, 0.05 + 0.012 * r.random(), col(self.s.get('wool_col', self.skin)))

    def wool_top(self, P):
        G = self.G
        c = col(self.s.get('wool_col', self.skin))
        for i, (dx, dy) in enumerate([(-0.11, 0.03), (-0.055, -0.01), (0, -0.02), (0.055, -0.01), (0.11, 0.03),
                                      (-0.08, 0.06), (-0.02, 0.05), (0.04, 0.05), (0.09, 0.07)]):
            P.circle(0.5 + dx, G.top + dy, 0.042, c if i % 2 else shade(c, 0.96))

    def horns(self, P):
        G = self.G
        hc = col(self.s.get('horn_col', '#e6d9bc'))
        for sx in (-1, 1):
            x = 0.5 + sx * G.rx * 0.5
            y = G.top + G.ry * 0.14
            P.blob([(x - sx * 0.03, y + 0.02), (x - sx * 0.01, y - 0.04), (x + sx * 0.035, y - 0.095),
                    (x + sx * 0.03, y - 0.03), (x + sx * 0.035, y + 0.02)], hc, n=6)

    def antenna(self, P):
        G = self.G
        P.line([(0.5, G.top + 0.01), (0.5, G.top - 0.07)], shade(self.skin, 0.7), 0.009)
        P.circle(0.5, G.top - 0.075, 0.02, col(self.s.get('o3', 'tomato')))

    # ------------------------------------------------------------ eyes
    def eye_centers(self):
        return [(0.5 - self.eye_dx, self.eye_y, -1), (0.5 + self.eye_dx, self.eye_y, 1)]

    def _eye_shape(self, P, ex, ey, k=1.0, c=SCLERA):
        rx, ry = self.erx * k, self.ery * k
        if self.s['eyes'] == 'narrow':
            pts = spline([(ex - rx, ey + ry * 0.12), (ex - rx * 0.4, ey - ry * 0.95), (ex + rx * 0.5, ey - ry),
                          (ex + rx, ey - ry * 0.1), (ex + rx * 0.4, ey + ry * 0.9), (ex - rx * 0.4, ey + ry * 0.85)],
                         closed=True)
            P.poly(pts, c)
        else:
            P.ellipse(ex, ey, rx, ry, c)

    def sclera(self, P):
        bead = self.s['eyes'] == 'bead'
        for ex, ey, sx in self.eye_centers():
            if bead:
                P.ellipse(ex, ey, self.erx, self.ery, INK)
            else:
                self._eye_shape(P, ex, ey, 1.0, col(self.s.get('sclera', SCLERA)))

    def iris_piece(self, P, st):
        if self.s['eyes'] == 'bead':
            for ex, ey, sx in self.eye_centers():
                P.circle(ex - self.erx * 0.3, ey - self.ery * 0.35, self.erx * 0.28, '#ffffff', a=235)
            return
        m = shape_mask(self.sclera)
        with P.clip(m):
            for ex, ey, sx in self.eye_centers():
                r = min(self.erx, self.ery) * self.et['iris'] * st['iris'] * (1.15 if self.s['eyes'] == 'narrow' else 1)
                ix = ex - sx * self.erx * 0.12
                iy = ey + self.ery * 0.06
                P.circle(ix, iy, r, self.iris)
                P.circle(ix, iy, r * 0.55, INK)
                P.circle(ix - r * 0.38, iy - r * 0.4, r * 0.24, '#ffffff', a=240)

    def lids(self, P, st):
        lidc = shade(self.skin, 0.93) if not self.s.get('robot') else shade(self.skin, 0.75)
        lash = shade(self.skin, 0.45) if self.s['kind'] != 'person' else INK
        m_big = shape_mask(lambda Q: [self._eye_shape(Q, ex, ey, 1.07) for ex, ey, sx in self.eye_centers()])
        top, bot, tilt = st['top'], st['bot'], st['tilt']
        with P.clip(m_big):
            for ex, ey, sx in self.eye_centers():
                rx, ry = self.erx * 1.1, self.ery * 1.1
                xs = [ex - rx * 1.2 + 2.4 * rx * i / 20 for i in range(21)]

                def ytop(x):
                    u = (x - ex) / rx
                    base = ey - ry + top * 2 * ry
                    arc = -0.28 * ry * (1 - u * u) * (1 - top) + (0.3 * ry * (1 - u * u) if top >= 0.99 else 0)
                    return base + arc + tilt * ry * (-u * sx)
                if top > 0.01 or tilt:
                    pts = [(x, ytop(x)) for x in xs]
                    P.poly(pts + [(xs[-1], ey - ry * 2), (xs[0], ey - ry * 2)], lidc)
                    P.line(pts, lash, max(0.0045, self.ery * 0.12))
                if bot > 0.01:
                    def ybot(x):
                        u = (x - ex) / rx
                        return ey + ry - bot * 2 * ry - 0.35 * bot * ry * (1 - u * u)
                    pts = [(x, ybot(x)) for x in xs]
                    P.poly(pts + [(xs[-1], ey + ry * 2), (xs[0], ey + ry * 2)], lidc)
                    P.line(pts, shade(lidc, 0.75), max(0.003, self.ery * 0.07))
        if st['top'] >= 0.99 and self.s['kind'] == 'person' and self.s.get('lashes'):
            for ex, ey, sx in self.eye_centers():
                for k in (-0.5, 0, 0.5):
                    P.line([(ex + k * self.erx, ey + self.ery * 0.95), (ex + k * self.erx * 1.3, ey + self.ery * 1.3)], INK, 0.004)
        elif self.s.get('lashes') and st['top'] < 0.99:
            for ex, ey, sx in self.eye_centers():
                ytop = ey - self.ery * 1.1 + st['top'] * 2.2 * self.ery
                P.taper([(ex + sx * self.erx * 0.75, ytop + self.ery * 0.25), (ex + sx * self.erx * 1.2, ytop - self.ery * 0.15)],
                        INK, 0.008, 0.002)

    def brows(self, P, st):
        kind = st['brow']
        thick = self.s.get('brow_w', 1.0) * self.ery * 0.42 * (1.25 if self.s['age'] == 'old' else 1.0)
        for ex, ey, sx in self.eye_centers():
            by = ey - self.ery * 1.55 - st['lift'] * self.ery
            if self.s['eyes'] == 'narrow':
                by += self.ery * 0.45
            if self.s.get('frog_eyes'):
                by = ey - self.ery * 1.9 - st['lift'] * self.ery
            rx = self.erx
            prof = {'neutral': (0.0, -0.3, 0.05), 'angry': (0.62, 0.05, -0.35), 'worried': (-0.5, -0.32, 0.28),
                    'raised': (-0.3, -0.62, -0.15)}[kind]
            inner = (ex - sx * rx * 0.95, by + prof[0] * self.ery)
            mid = (ex + sx * rx * 0.05, by + prof[1] * self.ery)
            outer = (ex + sx * rx * 1.15, by + prof[2] * self.ery)
            P.taper([inner, mid, outer], self.brow_col, thick * 1.05, thick, thick * 0.45)
            if self.s.get('bushy'):
                P.taper([inner, mid, outer], self.brow_col, thick * 1.5, thick * 1.4, thick * 0.9)

    # ------------------------------------------------------------ mouth
    def _mpts(self, v, k=1.0, dy=0.0):
        w = self.mouth_w
        sh = _mouth_open(v)
        return [(0.5 + x * w * k, self.mouth_y + (y + dy) * w * k) for x, y in sh]

    def _mmask(self, v, dy=0.0):
        return shape_mask(lambda Q: Q.poly(self._mpts(v, dy=dy), '#000000'))

    def mouth_cavity(self, P, v):
        if _mouth_open(v) is None:
            return
        w = self.mouth_w
        M = self._mmask(v)
        cav = col(self.s.get('cavity', CAVITY))
        P.fill_mask(M, cav)
        with P.clip(M):
            # inner shadow under the upper lip
            P.poly(self._mpts(v, dy=-0.06), shade(cav, 0.7)) if False else None
            if v in TONGUE_Y:
                ty, rx, ry = TONGUE_Y[v]
                P.ellipse(0.5, self.mouth_y + ty * w + ry * w * 0.5, rx * w, ry * w * 1.3, col(self.s.get('tongue', TONGUE)))
                P.line([(0.5, self.mouth_y + (ty - 0.02) * w + ry * w * 0.1), (0.5, self.mouth_y + ty * w + ry * w * 0.9)],
                       shade(TONGUE, 0.82), 0.004)
        teeth = col(self.s.get('teeth_col', TEETH))
        if self.s.get('robot'):
            teeth = '#a8d8cc'
        t = TEETH_TOP.get(v)
        if t and not self.s.get('no_teeth'):
            Mt = ImageChops.subtract(M, self._mmask(v, dy=t))
            P.fill_mask(Mt, teeth)
            if self.s.get('buck'):
                with P.clip(M):
                    P.poly([(0.5 - 0.11 * w, self.mouth_y - 0.2 * w), (0.5 + 0.11 * w, self.mouth_y - 0.2 * w),
                            (0.5 + 0.1 * w, self.mouth_y + (t + 0.15) * w), (0.5 - 0.1 * w, self.mouth_y + (t + 0.15) * w)], teeth)
                    P.line([(0.5, self.mouth_y - 0.1 * w), (0.5, self.mouth_y + (t + 0.15) * w)], shade(teeth, 0.75), 0.003)
            if v == 'grit' or self.s.get('robot'):
                with P.clip(Mt):
                    for i in range(-3, 4):
                        P.line([(0.5 + i * 0.22 * w, self.mouth_y - 0.3 * w), (0.5 + i * 0.22 * w, self.mouth_y + 0.4 * w)],
                               shade(teeth, 0.72), 0.003)
        b = TEETH_BOT.get(v)
        if b and not self.s.get('no_teeth'):
            Mb = ImageChops.subtract(M, self._mmask(v, dy=-b))
            P.fill_mask(Mb, teeth)
            if v == 'grit':
                with P.clip(Mb):
                    for i in range(-3, 4):
                        P.line([(0.5 + (i + 0.5) * 0.22 * w, self.mouth_y), (0.5 + (i + 0.5) * 0.22 * w, self.mouth_y + 0.5 * w)],
                               shade(teeth, 0.72), 0.003)
        if self.s.get('fangs') and v in ('A', 'E', 'smile', 'grit', 'shock', 'O'):
            with P.clip(M):
                for sx in (-1, 1):
                    x = 0.5 + sx * 0.35 * w
                    ytop = min(y for xx, y in self._mpts(v) if abs(xx - x) < 0.05 * w) if v != 'U' else self.mouth_y
                    P.poly([(x - 0.06 * w, ytop - 0.02), (x + 0.06 * w, ytop - 0.02), (x, ytop + 0.2 * w)], teeth)

    def mouth_lips(self, P, v):
        w = self.mouth_w
        lip = self.lip
        th = w * 0.085 * self.s.get('lip_w', 1.0)
        if v == 'closed':
            curve = self.s.get('smile', 0.08)
            pts = [(0.5 - 0.78 * w, self.mouth_y - curve * w * 0.6), (0.5 - 0.35 * w, self.mouth_y + curve * 0.6 * w),
                   (0.5, self.mouth_y + curve * w), (0.5 + 0.35 * w, self.mouth_y + curve * 0.6 * w),
                   (0.5 + 0.78 * w, self.mouth_y - curve * w * 0.6)]
            P.taper(pts, lip, th * 0.6, th * 1.1, th * 0.6)
            for sx in (-1, 1):
                x, y = 0.5 + sx * 0.78 * w, self.mouth_y - curve * w * 0.6
                P.curve([(x - sx * 0.03 * w, y - 0.1 * w), (x + sx * 0.05 * w, y), (x - sx * 0.02 * w, y + 0.1 * w)], lip, th * 0.45)
            return
        if v == 'MBP':
            pts = spline([(-0.62, 0.02), (-0.3, -0.1), (0, -0.07), (0.3, -0.1), (0.62, 0.02), (0.3, 0.13), (0, 0.15),
                          (-0.3, 0.13)], closed=True)
            P.poly([(0.5 + x * w, self.mouth_y + y * w) for x, y in pts], mix(lip, '#ffffff', 0.12))
            P.taper([(0.5 - 0.6 * w, self.mouth_y + 0.02 * w), (0.5, self.mouth_y + 0.03 * w), (0.5 + 0.6 * w, self.mouth_y + 0.02 * w)],
                    shade(lip, 0.6), th * 0.4, th * 0.8, th * 0.4)
            return
        pts = self._mpts(v)
        k = 1.6 if v in ('U', 'O') else 1.0
        P.line(pts + pts[:2], lip, th * k, caps=False)

    def beak(self, P, v):
        """Owl beak: the upper half is fixed, the lower half drops with the viseme."""
        w = self.mouth_w * 0.75
        x0, y0 = 0.5, self.mouth_y - 0.055
        drop = {'closed': 0.0, 'A': 0.62, 'E': 0.3, 'O': 0.5, 'U': 0.18, 'MBP': -0.03, 'smile': 0.45, 'shock': 0.85,
                'grit': 0.08}[v]
        bc = col(self.s.get('beak_col', '#d0a24a'))
        if drop > 0.01:
            P.blob([(x0 - w * 0.55, y0 + 0.02), (x0 + w * 0.55, y0 + 0.02), (x0 + w * 0.25, y0 + 0.05 + drop * w),
                    (x0 - w * 0.25, y0 + 0.05 + drop * w)], CAVITY, n=6)
        lower_y = y0 + 0.045 + drop * w
        P.blob([(x0 - w * 0.42, lower_y - 0.025), (x0 + w * 0.42, lower_y - 0.025), (x0, lower_y + 0.055)], shade(bc, 0.85), n=6)
        P.blob([(x0 - w * 0.6, y0 - 0.03), (x0, y0 - 0.06), (x0 + w * 0.6, y0 - 0.03), (x0 + w * 0.12, y0 + 0.045),
                (x0, y0 + 0.08 + (0.0 if drop > 0.01 else -0.01)), (x0 - w * 0.12, y0 + 0.045)], bc, n=6)

    # ------------------------------------------------------------ nose, facial hair, whiskers
    def nose(self, P):
        G, n = self.G, self.s['nose']
        x, y = 0.5, self.nose_y
        c = col(self.s.get('nose_col')) or shade(self.skin, 0.93)
        if self.s['kind'] == 'person' and not self.s.get('nose_col'):
            c = mix(self.skin, '#d77a6e', 0.18)
        r = G.rx * {'kid': 0.85, 'young': 0.95, 'adult': 1.0, 'old': 1.08}[self.s['age']]
        if n == 'ball':
            P.circle(x, y + 0.005, r * 0.2, c)
        elif n == 'button':
            P.ellipse(x, y + 0.012, r * 0.12, r * 0.09, c)
        elif n == 'long':
            P.blob([(x - r * 0.07, y - r * 0.3), (x + r * 0.07, y - r * 0.3), (x + r * 0.15, y + r * 0.08),
                    (x, y + r * 0.16), (x - r * 0.15, y + r * 0.08)], c, n=8)
        elif n == 'hooked':
            P.blob([(x - r * 0.06, y - r * 0.28), (x + r * 0.08, y - r * 0.2), (x + r * 0.1, y + r * 0.12),
                    (x - r * 0.02, y + r * 0.2), (x - r * 0.16, y + r * 0.1), (x - r * 0.06, y + r * 0.04)], c, n=8)
        elif n == 'wide':
            P.ellipse(x, y + 0.012, r * 0.26, r * 0.14, c)
            for sx in (-1, 1):
                P.ellipse(x + sx * r * 0.1, y + 0.022, r * 0.04, r * 0.025, shade(c, 0.7))
        elif n == 'snout':
            nc = col(self.s.get('nose_col', 'black'))
            P.blob([(x - r * 0.2, y - r * 0.02), (x, y - r * 0.07), (x + r * 0.2, y - r * 0.02), (x + r * 0.08, y + r * 0.12),
                    (x, y + r * 0.15), (x - r * 0.08, y + r * 0.12)], nc, n=8)
            P.ellipse(x - r * 0.07, y - r * 0.01, r * 0.05, r * 0.025, mix(nc, '#ffffff', 0.45))
            P.line([(x, y + r * 0.14), (x, self.mouth_y - 0.005)], shade(self.skin2 or self.skin, 0.6), 0.004)
        elif n == 'pig':
            pc = mix(self.skin, '#c86a72', 0.25)
            P.ellipse(x, y + 0.012, r * 0.3, r * 0.21, pc)
            for sx in (-1, 1):
                P.ellipse(x + sx * r * 0.1, y + 0.014, r * 0.045, r * 0.08, shade(pc, 0.55))
        elif n == 'cat':
            P.blob([(x - r * 0.11, y - r * 0.02), (x + r * 0.11, y - r * 0.02), (x, y + r * 0.1)], '#c7787f', n=6)
            P.line([(x, y + r * 0.08), (x, self.mouth_y - 0.006)], shade(self.skin2 or self.skin, 0.55), 0.004)
        elif n == 'mouse':
            P.circle(x, y + 0.01, r * 0.1, '#c7787f')
        elif n == 'hare':
            P.blob([(x - r * 0.1, y), (x + r * 0.1, y), (x, y + r * 0.1)], '#c7787f', n=6)
            P.line([(x, y + r * 0.08), (x, self.mouth_y - 0.006)], shade(self.skin2 or self.skin, 0.55), 0.004)
        elif n == 'sheep':
            P.blob([(x - r * 0.12, y), (x + r * 0.12, y), (x, y + r * 0.1)], '#5a4545', n=6)
        elif n == 'dots':
            for sx in (-1, 1):
                P.ellipse(x + sx * r * 0.09, y + 0.01, r * 0.035, r * 0.025, shade(self.skin, 0.55))
        elif n == 'beak':
            P.blob([(x - r * 0.16, y - r * 0.05), (x + r * 0.16, y - r * 0.05), (x, y + r * 0.25)], '#d0a24a', n=6)

    def mustache(self, P):
        w = self.mouth_w
        c = self.hair_col if self.s['kind'] == 'person' else shade(self.skin, 0.6)
        y = self.mouth_y - 0.022
        big = 1.35 if self.s['facial'] == 'walrus' else 1.0
        for sx in (-1, 1):
            P.blob([(0.5, y - 0.018 * big), (0.5 + sx * w * 0.55 * big, y - 0.022 * big),
                    (0.5 + sx * w * 0.95 * big, y + 0.012 * big), (0.5 + sx * w * 0.5 * big, y + 0.016 * big),
                    (0.5, y + 0.01 * big)], c, n=8)

    def beard(self, P):
        G, f = self.G, self.s['facial']
        c = self.hair_col
        if f == 'stubble':
            r = random.Random(self.s['name'] + 's')
            for k in range(220):
                a = math.pi * (0.62 + 0.76 * r.random())
                x, y = G.pt(a, 0.55 + 0.42 * r.random())
                if y > self.nose_y + 0.04:
                    P.circle(x, y, 0.0025, shade(self.skin, 0.62), a=200)
            return
        if f == 'goatee':
            P.blob([(0.5 - self.mouth_w * 0.45, self.mouth_y + 0.03), (0.5 + self.mouth_w * 0.45, self.mouth_y + 0.03),
                    (0.5 + self.mouth_w * 0.3, G.chin + 0.03), (0.5, G.chin + 0.06), (0.5 - self.mouth_w * 0.3, G.chin + 0.03)], c, n=8)
            return
        # full beard / chinstrap: follows the jaw
        pts = G.arc(math.pi * 0.55, math.pi * 1.45, 1.06)
        inner = [(0.5 + self.mouth_w * 1.15, self.nose_y + 0.03), (0.5 + self.mouth_w * 0.8, self.mouth_y + 0.06),
                 (0.5, self.mouth_y + (0.11 if f == 'beard' else 0.12)), (0.5 - self.mouth_w * 0.8, self.mouth_y + 0.06),
                 (0.5 - self.mouth_w * 1.15, self.nose_y + 0.03)]
        if f == 'beard':
            low = [(x, y + 0.035 * max(0, math.sin((x - 0.5) / G.rx * math.pi / 2 + math.pi / 2))) for x, y in pts]
            P.poly(low + spline(inner, 6), c)
            with P.clip():
                for k in range(9):
                    x = 0.5 + (k - 4) * G.rx * 0.2
                    P.curve([(x, self.mouth_y + 0.08), (x + 0.004, G.chin), (x - 0.002, G.chin + 0.03)], shade(c, 0.82), 0.004)
        else:
            P.poly(pts + spline(inner, 6), c)

    def whiskers(self, P):
        c = shade(self.skin2 or self.skin, 0.5)
        y = self.nose_y + 0.03
        for sx in (-1, 1):
            for k, dy in enumerate((-0.012, 0.004, 0.02)):
                P.taper([(0.5 + sx * self.G.rx * 0.32, y + dy * 0.6), (0.5 + sx * self.G.rx * 0.8, y + dy * 1.3 - 0.004),
                         (0.5 + sx * self.G.rx * 1.12, y + dy * 2.2)], c, 0.004, 0.003, 0.0015)

    # ------------------------------------------------------------ accessories
    def glasses(self, P):
        a = self.acc('glasses')
        kind = a[1] if len(a) > 1 else 'round'
        c = col(a[2] if len(a) > 2 else 'charcoal')
        th = 0.0085
        for ex, ey, sx in self.eye_centers():
            rx, ry = self.erx * 1.55, self.ery * 1.35
            if kind == 'round':
                pts = ell_pts(ex, ey, rx, rx)
            elif kind == 'square':
                pts = spline([(ex - rx, ey - ry * 0.8), (ex + rx, ey - ry * 0.8), (ex + rx * 0.95, ey + ry * 0.75),
                              (ex - rx * 0.95, ey + ry * 0.75)], 8, closed=True)
            else:  # cat-eye
                pts = spline([(ex - sx * rx * 0.9, ey - ry * 0.6), (ex + sx * rx * 0.2, ey - ry * 0.85),
                              (ex + sx * rx * 1.25, ey - ry * 1.15), (ex + sx * rx * 0.9, ey + ry * 0.55),
                              (ex - sx * rx * 0.6, ey + ry * 0.8)], 8, closed=True)
            P.poly(pts, '#dfe8ea', a=46)
            P.line(pts + pts[:2], c, th * (1.4 if kind == 'cateye' else 1.0), caps=False)
            P.line([(ex + sx * rx * 0.95, ey - ry * 0.3), (ex + sx * (self.G.half_w(ey) - self.eye_dx + 0.004), ey - ry * 0.35)],
                   c, th * 0.8)
            P.line([(ex - sx * rx * 0.55, ey - ry * 0.3), (ex - sx * rx * 0.35, ey - ry * 0.55)], '#ffffff', 0.004, a=150)
        P.curve([(0.5 - self.eye_dx + self.erx * 1.5, self.eye_y - 0.004), (0.5, self.eye_y - 0.014),
                 (0.5 + self.eye_dx - self.erx * 1.5, self.eye_y - 0.004)], c, th)

    def headphones(self, P):
        G = self.G
        a = self.acc('headphones') or self.acc('headset')
        c = col(a[1] if len(a) > 1 else 'charcoal')
        band = G.arc(-1.55, 1.55, 1.16)
        P.line(band, c, 0.02)
        for sx in (-1, 1):
            x = 0.5 + sx * (G.half_w(G.cy) + 0.012)
            P.blob([(x - 0.03, G.cy - 0.06), (x + 0.03, G.cy - 0.06), (x + 0.032, G.cy + 0.06), (x - 0.032, G.cy + 0.06)],
                   c, n=4)
            P.blob([(x - 0.018, G.cy - 0.045), (x + sx * 0.012, G.cy - 0.045), (x + sx * 0.014, G.cy + 0.045),
                    (x - 0.018, G.cy + 0.045)], col(a[2]) if len(a) > 2 else shade(c, 1.5), n=4)

    def headset_mic(self, P):
        G = self.G
        x = 0.5 - (G.half_w(G.cy) + 0.012)
        P.curve([(x, G.cy + 0.04), (x + 0.03, self.mouth_y + 0.03), (0.5 - self.mouth_w * 1.3, self.mouth_y + 0.02)],
                'charcoal', 0.008)
        P.ellipse(0.5 - self.mouth_w * 1.3, self.mouth_y + 0.02, 0.016, 0.013, 'black')

    def scarf(self, P):
        a = self.acc('scarf')
        c1 = col(a[1] if len(a) > 1 else 'rust')
        c2 = col(a[2] if len(a) > 2 else 'cream')
        y = self.sh_y - 0.035
        w = self.neck_w * 2.0
        P.blob([(0.5 - w, y - 0.04), (0.5, y - 0.025), (0.5 + w, y - 0.04), (0.5 + w * 1.15, y + 0.02), (0.5, y + 0.05),
                (0.5 - w * 1.15, y + 0.02)], c1, n=8)
        P.blob([(0.5 + w * 0.25, y + 0.02), (0.5 + w * 0.85, y + 0.02), (0.5 + w * 0.9, 1.02), (0.5 + w * 0.2, 1.02)], c1, n=4)
        with P.clip():
            for i in range(7):
                yy = y + 0.07 + i * 0.045
                P.line([(0.5, yy), (0.5 + w * 1.2, yy)], c2, 0.012)
            P.stitches([(0.5 - w * 1.05, y), (0.5, y + 0.03), (0.5 + w * 1.05, y)], shade(c1, 0.6))

    def acc_earrings(self, P):
        G = self.G
        a = self.acc('earrings')
        c = col(a[1] if len(a) > 1 else 'gold')
        for sx in (-1, 1):
            x = 0.5 + sx * (G.half_w(G.cy + 0.06) + 0.008)
            P.line(ell_pts(x, G.cy + 0.09, 0.013, 0.017), c, 0.005, caps=False)

    def acc_necklace(self, P):
        a = self.acc('necklace')
        c = col(a[1] if len(a) > 1 else 'coral')
        for i in range(13):
            t = i / 12
            ang = math.pi * (0.1 + 0.8 * t)
            x = 0.5 - math.cos(ang) * self.neck_w * 1.9
            y = self.sh_y - 0.04 + math.sin(ang) * 0.06
            P.circle(x, y, 0.0105, c if i % 3 else mix(c, '#ffffff', 0.4))

    def acc_stethoscope(self, P):
        c = '#3a3c42'
        y0 = self.sh_y - 0.04
        P.curve([(0.5 - self.neck_w * 1.4, y0 - 0.01), (0.5 - self.neck_w * 1.8, y0 + 0.06), (0.5 - self.neck_w * 1.2, y0 + 0.14)],
                c, 0.008)
        P.curve([(0.5 + self.neck_w * 1.4, y0 - 0.01), (0.5 + self.neck_w * 1.9, y0 + 0.08), (0.5 + self.neck_w * 1.5, y0 + 0.18)],
                c, 0.008)
        P.circle(0.5 + self.neck_w * 1.5, y0 + 0.195, 0.022, '#b8b6b1')
        P.circle(0.5 + self.neck_w * 1.5, y0 + 0.195, 0.012, '#8e9aa1')

    def acc_lanyard(self, P):
        a = self.acc('lanyard')
        c = col(a[1] if len(a) > 1 else 'teal')
        y0 = self.sh_y - 0.045
        P.line([(0.5 - self.neck_w * 1.3, y0), (0.5 - 0.012, y0 + 0.14)], c, 0.009)
        P.line([(0.5 + self.neck_w * 1.3, y0), (0.5 + 0.012, y0 + 0.14)], c, 0.009)
        P.blob([(0.5 - 0.045, y0 + 0.14), (0.5 + 0.045, y0 + 0.14), (0.5 + 0.045, y0 + 0.21), (0.5 - 0.045, y0 + 0.21)],
               'white', n=3)
        P.line([(0.5 - 0.03, y0 + 0.17), (0.5 + 0.03, y0 + 0.17)], 'slate', 0.005)
        P.line([(0.5 - 0.03, y0 + 0.188), (0.5 + 0.015, y0 + 0.188)], 'silver', 0.004)

    def acc_bowtie(self, P):
        a = self.acc('bowtie')
        c = col(a[1] if len(a) > 1 else 'burgundy')
        y = self.sh_y - 0.03
        P.blob([(0.5, y), (0.5 - 0.05, y - 0.028), (0.5 - 0.055, y + 0.028)], c, n=4)
        P.blob([(0.5, y), (0.5 + 0.05, y - 0.028), (0.5 + 0.055, y + 0.028)], c, n=4)
        P.circle(0.5, y, 0.012, shade(c, 0.85))

    def acc_flower(self, P):
        a = self.acc('flower')
        c = col(a[1] if len(a) > 1 else 'rose')
        x, y = 0.5 - self.W * 0.55, self.sh_y + 0.04
        for k in range(5):
            ang = k * 1.2566
            P.circle(x + 0.017 * math.cos(ang), y + 0.017 * math.sin(ang), 0.014, c)
        P.circle(x, y, 0.009, 'butter')

    def acc_pencil(self, P):
        G = self.G
        x = 0.5 + G.half_w(G.cy - 0.03) + 0.005
        P.line([(x - 0.03, G.cy - 0.06), (x + 0.04, G.cy + 0.01)], 'mustard', 0.012)
        P.line([(x + 0.04, G.cy + 0.01), (x + 0.052, G.cy + 0.022)], 'sand', 0.01)

    def helmet_glass(self, P):
        G = self.G
        r = max(G.rx, G.ry) * 1.32
        P.circle(0.5, G.cy - 0.005, r, '#cfe0e6', a=38)
        P.line(ell_pts(0.5, G.cy - 0.005, r, r, 0, 90), '#e8ecef', 0.022, caps=False)
        P.line(ell_pts(0.5, G.cy - 0.005, r * 0.86, r * 0.86, 0, 30, math.pi * 1.1, math.pi * 1.4), '#ffffff', 0.008, a=170)

    def hands(self):
        out = []
        kind = self.s.get('hands') or ('mic' if 'mic' in self.acc_names() else None)
        animal = self.s['kind'] != 'person'
        hc = self.skin
        sleeve = col(self.s.get('sleeve')) or self.o1
        if kind == 'mic':
            a = self.acc('mic') or ('mic',)
            flag = col(a[1] if len(a) > 1 else 'tomato')
            hx, hy = 0.5 + self.W * 0.62, 0.93

            def mic(P):
                P.line([(hx - 0.01, hy - 0.06), (hx - 0.035, self.sh_y + 0.03)], '#2f2d31', 0.022)
                P.blob([(hx - 0.06, self.sh_y - 0.0), (hx - 0.01, self.sh_y - 0.005), (hx - 0.008, self.sh_y + 0.045),
                        (hx - 0.062, self.sh_y + 0.05)], flag, n=4)
                P.circle(hx - 0.04, self.sh_y - 0.035, 0.034, '#4a484c')
                with P.clip():
                    for k in range(-3, 4):
                        P.line([(hx - 0.075, self.sh_y - 0.035 + k * 0.01), (hx - 0.005, self.sh_y - 0.035 + k * 0.01)],
                               '#2a282c', 0.003)
                P.circle(hx - 0.05, self.sh_y - 0.05, 0.008, '#8a888c')

            def hand(P):
                P.poly([(hx - 0.03, 1.02), (hx + 0.07, 1.02), (hx + 0.06, hy + 0.04), (hx - 0.04, hy + 0.04)], sleeve)
                P.blob([(hx - 0.045, hy - 0.06), (hx + 0.035, hy - 0.07), (hx + 0.055, hy + 0.0), (hx + 0.04, hy + 0.05),
                        (hx - 0.04, hy + 0.05), (hx - 0.055, hy - 0.01)], hc, n=6)
                for k in range(3):
                    P.line([(hx - 0.03, hy - 0.04 + k * 0.025), (hx + 0.03, hy - 0.045 + k * 0.025)], shade(hc, 0.82), 0.0035)
                if animal:
                    P.circle(hx + 0.01, hy + 0.02, 0.012, self.skin2 or shade(hc, 0.8))
            out += [(mic, 0.7), (hand, 0.8)]
        elif kind == 'wave':
            hx, hy = 0.5 + self.W * 1.02, 0.66

            def arm(P):
                P.poly([(hx - 0.04, 1.03), (hx + 0.06, 1.03), (hx + 0.045, hy + 0.08), (hx - 0.03, hy + 0.08)], sleeve)
            def hand(P):
                P.blob([(hx - 0.04, hy + 0.09), (hx - 0.05, hy + 0.0), (hx - 0.04, hy - 0.06), (hx, hy - 0.075),
                        (hx + 0.04, hy - 0.06), (hx + 0.05, hy + 0.0), (hx + 0.045, hy + 0.09)], hc, n=6)
                if animal:
                    for k in (-1, 0, 1):
                        P.circle(hx + k * 0.022, hy - 0.04, 0.009, self.skin2 or shade(hc, 0.8))
                    P.circle(hx, hy + 0.0, 0.02, self.skin2 or shade(hc, 0.8))
                else:
                    for k in (-1, 0, 1):
                        P.line([(hx + k * 0.02, hy - 0.06), (hx + k * 0.02, hy - 0.02)], shade(hc, 0.8), 0.0035)
                    P.blob([(hx - 0.04, hy + 0.0), (hx - 0.07, hy - 0.03), (hx - 0.075, hy - 0.005), (hx - 0.045, hy + 0.04)], hc, n=5)
            out += [(arm, 0.8), (hand, 0.8)]
        elif kind == 'clasp':
            def hands(P):
                for sx in (-1, 1):
                    P.poly([(0.5 + sx * 0.12, 1.03), (0.5 + sx * 0.2, 1.03), (0.5 + sx * 0.12, 0.93), (0.5 + sx * 0.04, 0.93)], sleeve)
                P.blob([(0.5 - 0.075, 0.9), (0.5, 0.88), (0.5 + 0.075, 0.9), (0.5 + 0.08, 0.95), (0.5, 0.97), (0.5 - 0.08, 0.95)],
                       hc, n=6)
                for k in (-1, 0, 1):
                    P.line([(0.5 + k * 0.022, 0.89), (0.5 + k * 0.022, 0.93)], shade(hc, 0.8), 0.0035)
            out += [(hands, 0.8)]
        return out


# ---------------------------------------------------------------- hair
def _cap(c, P, colr, s=1.95, puff=0.06, hairline=0.42, fringe=None, k_top=1.0):
    """A cap of hair over the top of the head down to the sideburns; `fringe` is the inner edge (forehead line)."""
    G = c.G
    outer = [G.pt(a, 1 + puff * (0.4 + 0.6 * math.cos(a / 2) ** 2) * k_top) for a in
             [-s + 2 * s * i / 60 for i in range(61)]]
    if fringe is None:
        yh = G.top + G.ry * hairline
        fringe = [G.pt(s, 1.0), (0.5 + G.rx * 0.85, G.cy - G.ry * 0.1), (0.5 + G.rx * 0.55, yh + 0.012), (0.5, yh),
                  (0.5 - G.rx * 0.55, yh + 0.012), (0.5 - G.rx * 0.85, G.cy - G.ry * 0.1), G.pt(-s, 1.0)]
        fringe = spline(fringe, 8)
    P.poly(outer + fringe, colr)


def _strands(c, P, colr, n=7, y0=None, y1=None):
    G = c.G
    with P.clip():
        for i in range(n):
            x = 0.5 + (i - (n - 1) / 2) * G.rx * 0.28
            P.curve([(x, (y0 or G.top) - 0.01), (x + 0.01, ((y0 or G.top) + (y1 or G.cy)) / 2), (x - 0.004, (y1 or G.cy))],
                    shade(colr, 0.82), 0.004)


def h_short_front(c, P):
    G, hc = c.G, c.hair_col
    yh = G.top + G.ry * 0.36
    fr = spline([G.pt(1.9), (0.5 + G.rx * 0.8, G.cy - G.ry * 0.25), (0.5 + G.rx * 0.45, yh + 0.025),
                 (0.5 + G.rx * 0.2, yh + 0.005), (0.5 - G.rx * 0.05, yh + 0.03), (0.5 - G.rx * 0.35, yh + 0.008),
                 (0.5 - G.rx * 0.7, yh + 0.03), (0.5 - G.rx * 0.88, G.cy - G.ry * 0.25), G.pt(-1.9)], 8)
    _cap(c, P, hc, 1.9, 0.07, fringe=fr)
    _strands(c, P, hc, 6, G.top, yh)


def h_buzz_front(c, P):
    G = c.G
    _cap(c, P, mix(c.hair_col, c.skin, 0.25), 1.75, 0.02, hairline=0.3)


def h_sidepart_front(c, P):
    G, hc = c.G, c.hair_col
    yh = G.top + G.ry * 0.38
    fr = spline([G.pt(1.95), (0.5 + G.rx * 0.88, G.cy - G.ry * 0.2), (0.5 + G.rx * 0.6, yh + 0.035),
                 (0.5 + G.rx * 0.1, yh + 0.015), (0.5 - G.rx * 0.35, yh - 0.03), (0.5 - G.rx * 0.6, yh - 0.05),
                 (0.5 - G.rx * 0.85, G.cy - G.ry * 0.3), G.pt(-1.95)], 8)
    _cap(c, P, hc, 1.95, 0.08, fringe=fr)
    with P.clip():
        P.curve([(0.5 - G.rx * 0.45, G.top - 0.02), (0.5 - G.rx * 0.5, G.top + 0.04), (0.5 - G.rx * 0.6, yh - 0.04)],
                shade(hc, 0.7), 0.006)
        for i in range(5):
            x = 0.5 - G.rx * 0.3 + i * G.rx * 0.25
            P.curve([(x - 0.02, G.top + 0.005), (x + 0.03, G.top + 0.05), (x + 0.04, yh)], shade(hc, 0.82), 0.004)


def h_quiff_front(c, P):
    G, hc = c.G, c.hair_col
    h_short_front(c, P)
    P.blob([(0.5 - G.rx * 0.7, G.top + 0.06), (0.5 - G.rx * 0.6, G.top - 0.03), (0.5 - G.rx * 0.1, G.top - 0.075),
            (0.5 + G.rx * 0.5, G.top - 0.06), (0.5 + G.rx * 0.85, G.top + 0.0), (0.5 + G.rx * 0.6, G.top + 0.07),
            (0.5, G.top + 0.04)], shade(hc, 1.05), n=8)
    with P.clip():
        for i in range(4):
            P.curve([(0.5 - G.rx * 0.6 + i * 0.03, G.top + 0.05), (0.5 - G.rx * 0.2 + i * 0.03, G.top - 0.05),
                     (0.5 + G.rx * 0.5, G.top - 0.03 + i * 0.02)], shade(hc, 0.8), 0.004)


def h_spiky_front(c, P):
    G, hc = c.G, c.hair_col
    _cap(c, P, hc, 1.8, 0.04, hairline=0.33)
    for i in range(9):
        a = -1.6 + 3.2 * i / 8
        bx, by = G.pt(a, 1.0)
        tx, ty = G.pt(a * 1.05, 1.32 + 0.06 * (i % 2))
        nx, ny = G.pt(a - 0.22, 1.02), G.pt(a + 0.22, 1.02)
        P.poly([nx, (tx, ty), ny, (bx, by + 0.02)], hc)


def h_mohawk_front(c, P):
    G, hc = c.G, c.hair_col
    _cap(c, P, mix(hc, c.skin, 0.55), 1.7, 0.01, hairline=0.3)
    for i in range(6):
        a = -0.55 + 1.1 * i / 5
        bx, by = G.pt(a, 0.95)
        tx, ty = G.pt(a * 1.2, 1.45 - 0.08 * abs(i - 2.5) / 2.5)
        P.poly([(bx - 0.03, by + 0.02), (tx, ty), (bx + 0.03, by + 0.02)], col(c.s.get('hair_col2', hc)))


def h_curly_back(c, P):
    G, hc = c.G, c.hair_col
    r = random.Random(c.s['name'] + 'c')
    for i in range(22):
        a = -2.3 + 4.6 * i / 21
        x, y = G.pt(a, 1.12 + 0.05 * r.random())
        P.circle(x, y, 0.05 + 0.015 * r.random(), shade(hc, 0.9))


def h_curly_front(c, P):
    G, hc = c.G, c.hair_col
    r = random.Random(c.s['name'] + 'C')
    _cap(c, P, hc, 1.9, 0.12, hairline=0.33)
    for i in range(13):
        a = -1.85 + 3.7 * i / 12
        x, y = G.pt(a, 1.0 + 0.1 * r.random())
        if y < G.top + G.ry * 0.45:
            y += 0.02
        P.circle(x, y, 0.035 + 0.01 * r.random(), hc)
    with P.clip():
        for i in range(30):
            x = 0.5 + (r.random() - 0.5) * G.rx * 2.4
            y = G.top - 0.05 + r.random() * G.ry * 0.7
            P.line(ell_pts(x, y, 0.012, 0.01, 0, 10, 0.3, 3.0), shade(hc, 0.72), 0.004)


def h_bob_back(c, P):
    G, hc = c.G, c.hair_col
    top = G.arc(-1.7, 1.7, 1.12)
    bottom_y = G.chin - 0.01
    P.poly(top + [(0.5 + G.rx * 1.15, bottom_y - 0.02), (0.5 + G.rx * 0.9, bottom_y + 0.02),
                  (0.5 - G.rx * 0.9, bottom_y + 0.02), (0.5 - G.rx * 1.15, bottom_y - 0.02)], shade(hc, 0.86))


def h_bob_front(c, P):
    G, hc = c.G, c.hair_col
    yh = G.top + G.ry * 0.42
    fr = spline([G.pt(2.0, 1.0), (0.5 + G.rx * 0.82, G.cy - G.ry * 0.05), (0.5 + G.rx * 0.75, yh + 0.01),
                 (0.5, yh + 0.012), (0.5 - G.rx * 0.75, yh + 0.01), (0.5 - G.rx * 0.82, G.cy - G.ry * 0.05),
                 G.pt(-2.0, 1.0)], 8)
    outer = [G.pt(a, 1.12) for a in [-2.05 + 4.1 * i / 60 for i in range(61)]]
    P.poly(outer + [(0.5 + G.rx * 0.8, G.cy + G.ry * 0.55)] + fr + [(0.5 - G.rx * 0.8, G.cy + G.ry * 0.55)], hc)
    with P.clip():
        for i in range(9):
            x = 0.5 + (i - 4) * G.rx * 0.22
            P.line([(x, yh - 0.06), (x * 1.0, yh + 0.01)], shade(hc, 0.8), 0.004)


def h_long_back(c, P):
    G, hc = c.G, c.hair_col
    top = G.arc(-1.75, 1.75, 1.1)
    wave = c.s['hair'] == 'wavy'
    side = []
    yb = 0.98 if c.s['hair'] in ('long', 'wavy') else G.chin + 0.03
    if getattr(c, 'body_ref', None) is not None:  # full body: hair ends a little below the shoulders
        yb = min(yb, c.sh_y + 0.11)
    for sx in (1,):
        pass
    right = [(0.5 + G.rx * 1.18, G.cy + 0.05), (0.5 + G.rx * 1.3, 0.8), (0.5 + G.rx * 1.25, yb)]
    left = [(0.5 - G.rx * 1.25, yb), (0.5 - G.rx * 1.3, 0.8), (0.5 - G.rx * 1.18, G.cy + 0.05)]
    bottom = []
    n = 6
    for i in range(n + 1):
        x = 0.5 + G.rx * 1.25 - 2.5 * G.rx * i / n
        bottom.append((x, yb + (0.02 if (i % 2 and wave) else 0)))
    P.poly(top + spline(right, 8) + bottom + spline(left, 8), shade(hc, 0.86))


def h_long_over(c, P):
    """Locks falling in front of the shoulders."""
    G, hc = c.G, c.hair_col
    wave = c.s['hair'] == 'wavy'
    for sx in (-1, 1):
        x0 = 0.5 + sx * G.rx * 0.95
        pts = [(x0, G.cy), (x0 + sx * 0.04, 0.72), (x0 + sx * 0.025, 0.84), (x0 + sx * 0.06, 0.9)]
        inner = [(x0 + sx * 0.1, 0.92), (x0 + sx * 0.085, 0.8), (x0 + sx * 0.1, 0.7), (x0 + sx * 0.06, G.cy)]
        if wave:
            pts = [(x0, G.cy), (x0 + sx * 0.06, 0.66), (x0 + sx * 0.01, 0.78), (x0 + sx * 0.05, 0.9)]
        P.poly(spline(pts, 8) + spline(inner, 8), hc)
        with P.clip():
            for k in range(3):
                P.curve([(x0 + sx * (0.02 + k * 0.025), G.cy + 0.05), (x0 + sx * (0.05 + k * 0.02), 0.75),
                         (x0 + sx * (0.04 + k * 0.025), 0.92)], shade(hc, 0.8), 0.004)


def h_long_front(c, P):
    G, hc = c.G, c.hair_col
    yh = G.top + G.ry * 0.3
    fr = spline([G.pt(2.05), (0.5 + G.rx * 0.8, G.cy - G.ry * 0.1), (0.5 + G.rx * 0.35, yh + 0.02), (0.5 + 0.004, yh - 0.03),
                 (0.5 - G.rx * 0.35, yh + 0.02), (0.5 - G.rx * 0.8, G.cy - G.ry * 0.1), G.pt(-2.05)], 8)
    _cap(c, P, hc, 2.05, 0.1, fringe=fr)
    with P.clip():
        P.line([(0.5, G.top - 0.03), (0.5, yh - 0.02)], shade(hc, 0.7), 0.005)
        for sx in (-1, 1):
            for k in range(3):
                P.curve([(0.5 + sx * 0.01, G.top + 0.0 + k * 0.012), (0.5 + sx * G.rx * (0.5 + 0.15 * k), yh - 0.02),
                         (0.5 + sx * G.rx * (0.95 + 0.05 * k), G.cy)], shade(hc, 0.82), 0.004)


def h_ponytail_back(c, P):
    G, hc = c.G, c.hair_col
    x = 0.5 + G.rx * 0.95
    P.blob([(x - 0.04, G.top + 0.03), (x + 0.07, G.top + 0.06), (x + 0.1, G.cy + 0.1), (x + 0.075, G.cy + 0.2),
            (x + 0.03, G.cy + 0.12), (x - 0.02, G.top + 0.12)], shade(hc, 0.9), n=8)


def h_bun_back(c, P):
    G = c.G
    P.circle(0.5, G.top - 0.03, G.rx * 0.42, shade(c.hair_col, 0.92))


def h_bun_front(c, P):
    G, hc = c.G, c.hair_col
    yh = G.top + G.ry * 0.3
    fr = spline([G.pt(1.95), (0.5 + G.rx * 0.85, G.cy - G.ry * 0.2), (0.5 + G.rx * 0.4, yh + 0.02), (0.5, yh - 0.005),
                 (0.5 - G.rx * 0.4, yh + 0.02), (0.5 - G.rx * 0.85, G.cy - G.ry * 0.2), G.pt(-1.95)], 8)
    _cap(c, P, hc, 1.95, 0.04, fringe=fr)
    with P.clip():
        for sx in (-1, 1):
            for k in range(3):
                P.curve([(0.5, G.top + 0.005), (0.5 + sx * G.rx * (0.45 + 0.2 * k), yh - 0.01 + k * 0.005),
                         (0.5 + sx * G.rx * (0.9 + 0.03 * k), G.cy - 0.01)], shade(hc, 0.8), 0.004)


def h_braids_over(c, P):
    G, hc = c.G, c.hair_col
    for sx in (-1, 1):
        x0 = 0.5 + sx * G.rx * 0.95
        for k in range(7):
            y = G.cy + 0.03 + k * 0.052
            P.ellipse(x0 + sx * (0.02 + 0.006 * k), y, 0.03 - 0.0015 * k, 0.034, hc if k % 2 else shade(hc, 0.9))
        P.circle(x0 + sx * 0.065, G.cy + 0.03 + 7 * 0.052 - 0.01, 0.014, col(c.s.get('o3', 'rose')))


def h_horseshoe_front(c, P):
    G, hc = c.G, c.hair_col
    for sx in (-1, 1):
        pts = [G.pt(sx * 1.25, 1.08), G.pt(sx * 1.55, 1.1), G.pt(sx * 1.95, 1.04), G.pt(sx * 1.95, 0.94),
               G.pt(sx * 1.55, 0.95), G.pt(sx * 1.3, 0.97)]
        P.blob(pts, hc, n=6)


def h_kerchief_back(c, P):
    G = c.G
    kc = col(c.s.get('kerchief', 'rose'))
    P.poly(G.arc(-1.9, 1.9, 1.14) + [(0.5 + G.rx * 0.95, 0.8), (0.5 - G.rx * 0.95, 0.8)], shade(kc, 0.85))


def h_kerchief_front(c, P):
    G = c.G
    kc = col(c.s.get('kerchief', 'rose'))
    hc = c.hair_col
    yh = G.top + G.ry * 0.4
    P.poly(spline([(0.5 - G.rx * 0.75, yh + 0.015), (0.5, yh - 0.012), (0.5 + G.rx * 0.75, yh + 0.015)], 8)
           + [(0.5 + G.rx * 0.75, yh - 0.04), (0.5 - G.rx * 0.75, yh - 0.04)], hc)
    fr = spline([G.pt(2.05, 1.0), (0.5 + G.rx * 0.9, G.cy - 0.02), (0.5 + G.rx * 0.6, yh - 0.005), (0.5, yh - 0.025),
                 (0.5 - G.rx * 0.6, yh - 0.005), (0.5 - G.rx * 0.9, G.cy - 0.02), G.pt(-2.05, 1.0)], 8)
    _cap(c, P, kc, 2.05, 0.12, fringe=fr)
    with P.clip():
        r = random.Random(c.s['name'] + 'k')
        for i in range(40):
            x = 0.5 + (r.random() - 0.5) * G.rx * 2.6
            y = G.top - 0.04 + r.random() * G.ry * 1.4
            dot = col(c.s.get('kerchief2', 'cream'))
            for k in range(5):
                a = k * 1.2566
                P.circle(x + 0.007 * math.cos(a), y + 0.007 * math.sin(a), 0.004, dot)
        P.stitches(spline([G.pt(1.9, 0.97), (0.5 + G.rx * 0.55, yh + 0.0), (0.5, yh - 0.02), (0.5 - G.rx * 0.55, yh + 0.0),
                           G.pt(-1.9, 0.97)], 6), shade(kc, 0.6))


def h_topknot_front(c, P):
    G, hc = c.G, c.hair_col
    h_bun_front(c, P)
    P.circle(0.5, G.top - 0.035, G.rx * 0.3, hc)
    P.ellipse(0.5, G.top - 0.0, G.rx * 0.18, 0.012, col(c.s.get('o3', 'tomato')))


def h_tuft_front(c, P):
    G = c.G
    hc = c.s.get('hair_col') and c.hair_col or shade(c.skin, 0.88)
    for k, dx in enumerate((-0.03, 0.0, 0.028)):
        P.blob([(0.5 + dx - 0.025, G.top + 0.03), (0.5 + dx + 0.01 * (k - 1), G.top - 0.06 + 0.012 * abs(k - 1)),
                (0.5 + dx + 0.025, G.top + 0.03)], hc, n=6)


HAIR_DRAW = {
    'bald': {}, 'none': {},
    'horseshoe': dict(front=h_horseshoe_front),
    'buzz': dict(front=h_buzz_front),
    'short': dict(front=h_short_front),
    'sidepart': dict(front=h_sidepart_front),
    'quiff': dict(front=h_quiff_front),
    'spiky': dict(front=h_spiky_front),
    'mohawk': dict(front=h_mohawk_front),
    'curly': dict(back=h_curly_back, front=h_curly_front),
    'bob': dict(back=h_bob_back, front=h_bob_front),
    'long': dict(back=h_long_back, over=h_long_over, front=h_long_front),
    'wavy': dict(back=h_long_back, over=h_long_over, front=h_long_front),
    'ponytail': dict(back=h_ponytail_back, front=h_bun_front),
    'bun': dict(back=h_bun_back, front=h_bun_front),
    'braids': dict(over=h_braids_over, front=h_long_front),
    'kerchief': dict(back=h_kerchief_back, front=h_kerchief_front),
    'topknot': dict(front=h_topknot_front),
    'tuft': dict(front=h_tuft_front),
}


# ---------------------------------------------------------------- hats
def _hat_base_y(c):
    return c.G.top + c.G.ry * 0.36


def hat_cap(c, a):
    G = c.G
    hc = col(a[2] if len(a) > 2 else 'tomato')
    yb = _hat_base_y(c)

    def crown(P):
        pts = [p for p in G.outline(1.07) if p[1] < yb]
        pts.sort(key=lambda p: math.atan2(p[0] - 0.5, -(p[1] - G.cy)))
        P.poly(pts, hc)
        with P.clip():
            for sx in (-0.33, 0.33):
                P.curve([(0.5, G.top - 0.02), (0.5 + sx * G.rx, G.top + 0.03), (0.5 + sx * G.rx * 1.4, yb)], shade(hc, 0.75), 0.004)
            P.circle(0.5, G.top - 0.012, 0.012, shade(hc, 0.8))

    def brim(P):
        P.blob([(0.5 - G.rx * 0.95, yb - 0.005), (0.5, yb - 0.02), (0.5 + G.rx * 0.95, yb - 0.005),
                (0.5 + G.rx * 0.75, yb + 0.03), (0.5, yb + 0.045), (0.5 - G.rx * 0.75, yb + 0.03)], shade(hc, 0.85), n=8)
        P.stitches([(0.5 - G.rx * 0.75, yb + 0.012), (0.5, yb + 0.026), (0.5 + G.rx * 0.75, yb + 0.012)], shade(hc, 0.55))
    return [(crown, 0.9), (brim, 0.9)]


def hat_beanie(c, a):
    G = c.G
    hc = col(a[2] if len(a) > 2 else 'mustard')
    yb = _hat_base_y(c) + 0.01

    def body(P):
        pts = [p for p in G.outline(1.1) if p[1] < yb]
        pts.sort(key=lambda p: math.atan2(p[0] - 0.5, -(p[1] - G.cy)))
        P.poly(pts, hc)
        P.circle(0.5, G.top - 0.05, 0.04, mix(hc, '#ffffff', 0.35))
        with P.clip():
            for i in range(-6, 7):
                P.line([(0.5 + i * 0.022, G.top - 0.04), (0.5 + i * 0.03, yb)], shade(hc, 0.85), 0.004)

    def band(P):
        w = G.half_w(yb) + 0.02
        P.blob([(0.5 - w, yb - 0.045), (0.5 + w, yb - 0.045), (0.5 + w, yb + 0.012), (0.5 - w, yb + 0.012)], shade(hc, 0.9), n=4)
        with P.clip():
            for i in range(-12, 13):
                P.line([(0.5 + i * 0.016, yb - 0.05), (0.5 + i * 0.016, yb + 0.02)], shade(hc, 0.75), 0.003)
    return [(body, 0.9), (band, 0.9)]


def hat_tubeteika(c, a):
    G = c.G
    hc = col(a[2] if len(a) > 2 else 'black')
    yb = G.top + G.ry * 0.28
    w = G.half_w(yb) * 0.92

    def hat(P):
        P.poly(spline([(0.5 - w, yb + 0.012), (0.5, yb + 0.022), (0.5 + w, yb + 0.012)], 8)
               + [(0.5 + w * 0.88, G.top - 0.03), (0.5 + w * 0.3, G.top - 0.045), (0.5 - w * 0.3, G.top - 0.045),
                  (0.5 - w * 0.88, G.top - 0.03)], hc)
        with P.clip():
            for i in range(-2, 3):
                x = 0.5 + i * w * 0.42
                y = (yb + G.top) / 2 - 0.01
                P.blob([(x, y - 0.025), (x + 0.018, y), (x + 0.004, y + 0.026), (x - 0.016, y + 0.006)], '#ece6d9', n=6)
                P.circle(x + 0.0, y + 0.0, 0.004, hc)
            P.stitches([(0.5 - w, yb + 0.002), (0.5, yb + 0.012), (0.5 + w, yb + 0.002)], '#ece6d9', w=0.004)
    return [(hat, 0.8)]


def hat_kalpak(c, a):
    G = c.G
    hc = col(a[2] if len(a) > 2 else 'white')
    yb = G.top + G.ry * 0.36
    w = G.half_w(yb) * 1.02

    def crown(P):
        P.blob([(0.5 - w, yb + 0.01), (0.5 - w * 0.75, G.top - 0.06), (0.5 - w * 0.2, G.top - 0.15), (0.5, G.top - 0.17),
                (0.5 + w * 0.2, G.top - 0.15), (0.5 + w * 0.75, G.top - 0.06), (0.5 + w, yb + 0.01)], hc, n=8)
        with P.clip():
            for sx in (-1, 0, 1):
                P.stitches([(0.5 + sx * w * 0.7, yb), (0.5 + sx * w * 0.35, G.top - 0.06), (0.5, G.top - 0.16)], '#3a383c', w=0.004)
        P.circle(0.5, G.top - 0.175, 0.012, '#3a383c')

    def brim(P):
        bc = '#2b282b'
        for sx in (-1, 1):
            P.blob([(0.5 + sx * 0.015, yb - 0.05), (0.5 + sx * w * 1.08, yb - 0.035), (0.5 + sx * w * 1.05, yb + 0.02),
                    (0.5 + sx * 0.01, yb + 0.015)], bc, n=4)
        with P.clip():
            P.stitches([(0.5 - w, yb - 0.01), (0.5 + w, yb - 0.01)], '#ece6d9', smooth=False, w=0.004)
    return [(crown, 1.0), (brim, 0.9)]


def hat_toque(c, a):
    G = c.G
    yb = G.top + G.ry * 0.3
    w = G.half_w(yb) * 0.95

    def hat(P):
        for dx, dy, r in ((-0.09, -0.13, 0.08), (0.0, -0.17, 0.09), (0.09, -0.13, 0.08), (-0.04, -0.2, 0.06), (0.05, -0.2, 0.06)):
            P.circle(0.5 + dx, G.top + dy, r, '#efeae0')
        P.poly([(0.5 - w, yb + 0.012), (0.5 + w, yb + 0.012), (0.5 + w * 0.98, G.top - 0.08), (0.5 - w * 0.98, G.top - 0.08)], '#efeae0')
        with P.clip():
            for i in range(-3, 4):
                P.line([(0.5 + i * w * 0.28, yb), (0.5 + i * w * 0.32, G.top - 0.2)], '#cfc8bb', 0.004)
            P.line([(0.5 - w, yb - 0.025), (0.5 + w, yb - 0.025)], '#cfc8bb', 0.006)
    return [(hat, 1.0)]


def hat_fedora(c, a, bowler=False):
    G = c.G
    hc = col(a[2] if len(a) > 2 else 'charcoal')
    yb = G.top + G.ry * 0.34
    w = G.half_w(yb) * 0.95

    def crown(P):
        if bowler:
            P.poly([(0.5 - w, yb)] + ell_pts(0.5, yb, w, 0.17, 0, 40, math.pi, 2 * math.pi) + [(0.5 + w, yb)], hc)
        else:
            P.blob([(0.5 - w, yb), (0.5 - w * 0.92, G.top - 0.11), (0.5 - w * 0.2, G.top - 0.13), (0.5, G.top - 0.105),
                    (0.5 + w * 0.2, G.top - 0.13), (0.5 + w * 0.92, G.top - 0.11), (0.5 + w, yb)], hc, n=8)
        with P.clip():
            P.poly([(0, yb - 0.04), (1, yb - 0.04), (1, yb), (0, yb)], col(a[3] if len(a) > 3 else 'burgundy'))

    def brim(P):
        P.ellipse(0.5, yb + 0.004, w * 1.55, 0.03, shade(hc, 0.92))
    return [(crown, 0.9), (brim, 0.9)]


def hat_beret(c, a):
    G = c.G
    hc = col(a[2] if len(a) > 2 else 'wine')

    def hat(P):
        P.ellipse(0.5 + G.rx * 0.2, G.top + 0.02, G.rx * 1.15, 0.07, hc, angle=-0.12)
        P.circle(0.5 + G.rx * 0.2, G.top - 0.05, 0.012, shade(hc, 0.8))
    return [(hat, 0.9)]


def hat_straw(c, a):
    G = c.G
    hc = col(a[2] if len(a) > 2 else '#d6b56a')
    yb = G.top + G.ry * 0.32
    w = G.half_w(yb) * 0.95

    def crown(P):
        P.blob([(0.5 - w, yb), (0.5 - w * 0.9, G.top - 0.09), (0.5, G.top - 0.11), (0.5 + w * 0.9, G.top - 0.09), (0.5 + w, yb)],
               hc, n=8)
        with P.clip():
            P.poly([(0, yb - 0.035), (1, yb - 0.035), (1, yb), (0, yb)], col(a[3] if len(a) > 3 else 'rust'))
            for i in range(8):
                P.line([(0, G.top - 0.1 + i * 0.016), (1, G.top - 0.1 + i * 0.016)], shade(hc, 0.85), 0.003)

    def brim(P):
        P.ellipse(0.5, yb + 0.006, w * 2.1, 0.042, shade(hc, 0.95))
        with P.clip():
            for k in range(4):
                P.line(ell_pts(0.5, yb + 0.006, w * (1.3 + 0.2 * k), 0.02 + 0.006 * k, 0, 60), shade(hc, 0.8), 0.003)
    return [(crown, 0.9), (brim, 0.9)]


def hat_hardhat(c, a):
    G = c.G
    hc = col(a[2] if len(a) > 2 else 'mustard')
    yb = G.top + G.ry * 0.36
    w = G.half_w(yb) * 1.05

    def hat(P):
        P.poly([(0.5 - w, yb)] + ell_pts(0.5, yb, w, 0.16, 0, 40, math.pi, 2 * math.pi) + [(0.5 + w, yb)], hc)
        P.blob([(0.5 - w * 1.18, yb - 0.01), (0.5 + w * 1.18, yb - 0.01), (0.5 + w * 1.15, yb + 0.02), (0.5 - w * 1.15, yb + 0.02)],
               shade(hc, 0.9), n=4)
        with P.clip():
            P.poly([(0.5 - 0.02, G.top - 0.1), (0.5 + 0.02, G.top - 0.1), (0.5 + 0.025, yb), (0.5 - 0.025, yb)], shade(hc, 0.88))
    return [(hat, 0.9)]


HAT_DRAW = {'cap': hat_cap, 'beanie': hat_beanie, 'tubeteika': hat_tubeteika, 'kalpak': hat_kalpak, 'toque': hat_toque,
            'fedora': hat_fedora, 'bowler': lambda c, a: hat_fedora(c, a, True), 'beret': hat_beret, 'straw': hat_straw,
            'hardhat': hat_hardhat}


# ---------------------------------------------------------------- outfits
def _collar_points(c, P, colr, spread=1.0):
    y = c.sh_y - 0.05
    nw = c.neck_w
    for sx in (-1, 1):
        P.blob([(0.5 + sx * nw * 0.2, y + 0.04), (0.5 + sx * nw * 1.3, y - 0.015), (0.5 + sx * nw * 1.55, y + 0.01),
                (0.5 + sx * nw * 0.9 * spread, y + 0.075)], colr, n=4)


def o_sweater(c):
    o1, o2 = c.o1, c.o2

    def body(P):
        c.body(P, o1, 'crew')
        with P.clip():
            pat = c.s.get('pattern', 'stripes')
            if pat == 'stripes':
                for i in range(4):
                    y = c.sh_y + 0.07 + i * 0.065
                    P.poly([(0, y), (1, y), (1, y + 0.025), (0, y + 0.025)], o2)
            elif pat == 'zigzag':
                y = c.sh_y + 0.1
                pts = [(i * 0.03, y + (0.02 if i % 2 else -0.02)) for i in range(35)]
                P.line(pts, o2, 0.016)
                P.line([(x, yy + 0.05) for x, yy in pts], c.o3, 0.012)
            elif pat == 'diamonds':
                for i in range(-6, 7):
                    x, y = 0.5 + i * 0.07, c.sh_y + 0.13
                    P.poly([(x, y - 0.03), (x + 0.03, y), (x, y + 0.03), (x - 0.03, y)], o2 if i % 2 else c.o3)
            for i in range(-15, 16):
                x = 0.5 + i * 0.024
                P.line([(x, c.sh_y - 0.02), (x, 1.02)], shade(o1, 0.93), 0.003)

    def collar(P):
        ny = c.sh_y - 0.045
        nw = c.neck_w * 1.55
        pts = spline([(0.5 - nw * 1.1, ny - 0.006), (0.5, ny + 0.026), (0.5 + nw * 1.1, ny - 0.006)], 8)
        P.line(pts, shade(o1, 0.85), 0.03)
        with P.clip():
            for i in range(-12, 13):
                P.line([(0.5 + i * 0.012, ny - 0.03), (0.5 + i * 0.012, ny + 0.05)], shade(o1, 0.7), 0.003)
    return [(body, 1.0), (collar, 0.6)]


def o_tshirt(c):
    o1 = c.o1

    def body(P):
        c.body(P, o1, 'crew')
        with P.clip():
            for sx in (-1, 1):
                P.stitches([(0.5 + sx * c.W * 0.75, c.sh_y - 0.01), (0.5 + sx * c.W * 0.85, c.sh_y + 0.12),
                            (0.5 + sx * c.W * 0.9, 1.0)], shade(o1, 0.65))
            pr = c.s.get('print')
            if pr == 'circle':
                P.circle(0.5, c.sh_y + 0.14, 0.06, c.o2)
                P.circle(0.5, c.sh_y + 0.14, 0.03, c.o3)
            elif pr == 'star':
                pts = [(0.5 + (0.07 if i % 2 == 0 else 0.03) * math.sin(i * math.pi / 5),
                        c.sh_y + 0.14 - (0.07 if i % 2 == 0 else 0.03) * math.cos(i * math.pi / 5)) for i in range(10)]
                P.poly(pts, c.o2)
            elif pr == 'stripe':
                P.poly([(0, c.sh_y + 0.11), (1, c.sh_y + 0.11), (1, c.sh_y + 0.16), (0, c.sh_y + 0.16)], c.o2)
            elif pr == 'bolt':
                x, y = 0.5, c.sh_y + 0.14
                P.poly([(x + 0.01, y - 0.07), (x - 0.04, y + 0.01), (x - 0.0, y + 0.01), (x - 0.015, y + 0.07),
                        (x + 0.04, y - 0.015), (x + 0.0, y - 0.015)], c.o2)

    def collar(P):
        ny = c.sh_y - 0.045
        nw = c.neck_w * 1.55
        P.line(spline([(0.5 - nw * 1.05, ny - 0.004), (0.5, ny + 0.027), (0.5 + nw * 1.05, ny - 0.004)], 8), shade(o1, 0.85), 0.016)
    return [(body, 1.0), (collar, 0.5)]


def o_shirt(c):
    o1 = c.o1

    def body(P):
        c.body(P, o1, 'v', vdepth=0.05)
        with P.clip():
            P.line([(0.5, c.sh_y + 0.0), (0.5, 1.02)], shade(o1, 0.85), 0.006)
            for i in range(4):
                P.circle(0.507, c.sh_y + 0.04 + i * 0.065, 0.0075, mix(o1, '#ffffff', 0.5))
            P.blob([(0.5 - c.W * 0.62, c.sh_y + 0.08), (0.5 - c.W * 0.25, c.sh_y + 0.08), (0.5 - c.W * 0.27, c.sh_y + 0.17),
                    (0.5 - c.W * 0.6, c.sh_y + 0.17)], shade(o1, 0.94), n=3)
            P.stitches([(0.5 - c.W * 0.62, c.sh_y + 0.095), (0.5 - c.W * 0.25, c.sh_y + 0.095)], shade(o1, 0.6), smooth=False)
            if c.s.get('pattern') == 'check':
                for i in range(-12, 13):
                    P.line([(0.5 + i * 0.04, 0.6), (0.5 + i * 0.04, 1.05)], c.o2, 0.008, a=110)
                for i in range(12):
                    P.line([(0, 0.66 + i * 0.04), (1, 0.66 + i * 0.04)], c.o2, 0.008, a=110)

    def collar(P):
        _collar_points(c, P, mix(o1, '#ffffff', 0.1))
    return [(body, 1.0), (collar, 0.6)]


def _shirt_under(c, colr='white', tie=None):
    def shirt(P):
        c.body(P, col(colr), 'crew', top=c.sh_y - 0.065)

    def collar(P):
        _collar_points(c, P, col(colr))
    out = [(shirt, 0.7), (collar, 0.6)]
    if tie:
        def tiep(P):
            y = c.sh_y - 0.035
            P.blob([(0.5 - 0.018, y - 0.008), (0.5 + 0.018, y - 0.008), (0.5 + 0.014, y + 0.022), (0.5 - 0.014, y + 0.022)], tie, n=3)
            P.poly([(0.5 - 0.014, y + 0.02), (0.5 + 0.014, y + 0.02), (0.5 + 0.03, y + 0.2), (0.5, y + 0.23), (0.5 - 0.03, y + 0.2)], tie)
            with P.clip():
                if c.s.get('tie_stripes', True):
                    for i in range(8):
                        P.line([(0.46, y + 0.03 + i * 0.03), (0.54, y + i * 0.03)], shade(tie, 0.75), 0.005)
        out.append((tiep, 0.6))
    return out


def o_suit(c):
    o1 = c.o1
    out = _shirt_under(c, c.s.get('shirt', 'white'), tie=c.o3 if c.s.get('tie', True) else None)

    def jacket(P):
        c.body(P, o1, 'v', vdepth=0.2, notch_w=c.neck_w * 1.45)
        with P.clip():
            P.line([(0.5, c.sh_y + 0.15), (0.5, 1.02)], shade(o1, 0.8), 0.004)
            P.circle(0.51, c.sh_y + 0.2, 0.008, shade(o1, 0.7))
            P.line([(0.5 + c.W * 0.4, c.sh_y + 0.07), (0.5 + c.W * 0.68, c.sh_y + 0.07)], shade(o1, 0.75), 0.006)
            P.poly([(0.5 + c.W * 0.42, c.sh_y + 0.07), (0.5 + c.W * 0.62, c.sh_y + 0.07), (0.5 + c.W * 0.6, c.sh_y + 0.045),
                    (0.5 + c.W * 0.45, c.sh_y + 0.045)], col(c.s.get('pocket_sq', 'white')))

    def lapels(P):
        y = c.sh_y - 0.045
        nw = c.neck_w * 1.45
        for sx in (-1, 1):
            P.poly([(0.5 + sx * nw, y), (0.5 + sx * nw * 1.9, y + 0.03), (0.5 + sx * nw * 1.5, y + 0.07),
                    (0.5 + sx * nw * 1.75, y + 0.09), (0.5 + sx * 0.008, y + 0.2), (0.5 + sx * nw * 0.65, y + 0.04)], shade(o1, 0.9))
    return out + [(jacket, 1.0), (lapels, 0.6)]


def o_labcoat(c):
    out = _shirt_under(c, c.s.get('shirt', 'sky'), tie=c.o3 if c.s.get('tie') else None)
    wc = '#ebe7df'

    def coat(P):
        c.body(P, wc, 'v', vdepth=0.24, notch_w=c.neck_w * 1.5)
        with P.clip():
            x0 = 0.5 + c.W * 0.35
            P.blob([(x0, c.sh_y + 0.1), (x0 + 0.12, c.sh_y + 0.1), (x0 + 0.115, c.sh_y + 0.2), (x0 + 0.005, c.sh_y + 0.2)],
                   '#dcd6cb', n=3)
            for i, pc in enumerate(('#38363a', '#a5433a', '#506889')):
                x = x0 + 0.025 + i * 0.03
                P.line([(x, c.sh_y + 0.06), (x, c.sh_y + 0.11)], pc, 0.009)
            P.stitches([(0.5 + 0.03, c.sh_y + 0.2), (0.5 + 0.03, 1.02)], '#bdb6a8', smooth=False)

    def lapels(P):
        y = c.sh_y - 0.045
        nw = c.neck_w * 1.5
        for sx in (-1, 1):
            P.poly([(0.5 + sx * nw, y), (0.5 + sx * nw * 1.95, y + 0.03), (0.5 + sx * nw * 1.55, y + 0.075),
                    (0.5 + sx * nw * 1.85, y + 0.095), (0.5 + sx * 0.008, y + 0.24), (0.5 + sx * nw * 0.65, y + 0.04)], '#dedad1')
    return out + [(coat, 1.0), (lapels, 0.6)]


def o_vest(c):
    out = _shirt_under(c, c.s.get('shirt', 'white'), tie=c.o3 if c.s.get('tie') else None)
    if not c.s.get('tie') and not any(a == 'bowtie' or (isinstance(a, (tuple, list)) and a[0] == 'bowtie') for a in c.s['acc']):
        pass
    o1 = c.o1

    def vest(P):
        W = c.W * 0.86
        P.poly(c.torso_pts('v', W=W, vdepth=0.17), o1)
        with P.clip():
            for i in range(4):
                P.circle(0.505, c.sh_y + 0.155 + i * 0.05, 0.007, shade(o1, 0.6))
            P.line([(0.5 - 0.004, c.sh_y + 0.12), (0.5 - 0.004, 1.02)], shade(o1, 0.75), 0.004)
            for sx in (-1, 1):
                P.line([(0.5 + sx * W * 0.35, c.sh_y + 0.17), (0.5 + sx * W * 0.65, c.sh_y + 0.17)], shade(o1, 0.75), 0.006)

    def sleeves(P):
        for sx in (-1, 1):
            P.poly([(0.5 + sx * c.W * 0.86, c.sh_y + 0.0), (0.5 + sx * c.W * 1.03, c.sh_y + 0.05), (0.5 + sx * c.W * 1.09, 1.03),
                    (0.5 + sx * c.W * 0.86, 1.03)], col(c.s.get('shirt', 'white')))
    return out + [(vest, 1.0)]


def o_hoodie(c):
    o1 = c.o1

    def body(P):
        c.body(P, o1, 'crew', notch_w=c.neck_w * 1.4)
        with P.clip():
            P.blob([(0.5 - c.W * 0.55, 0.95), (0.5 + c.W * 0.55, 0.95), (0.5 + c.W * 0.62, 1.05), (0.5 - c.W * 0.62, 1.05)],
                   shade(o1, 0.92), n=3)
            P.stitches([(0.5 - c.W * 0.53, 0.965), (0.5 + c.W * 0.53, 0.965)], shade(o1, 0.6), smooth=False)

    def strings(P):
        for sx in (-1, 1):
            x = 0.5 + sx * 0.035
            P.curve([(x, c.sh_y - 0.02), (x + sx * 0.004, c.sh_y + 0.06), (x - sx * 0.003, c.sh_y + 0.13)], c.o2, 0.008)
            P.line([(x - sx * 0.003, c.sh_y + 0.13), (x - sx * 0.003, c.sh_y + 0.15)], shade(c.o2, 0.7), 0.011)
    return [(body, 1.0), (strings, 0.4)]


def o_overalls(c):
    o1 = c.o1  # denim

    def shirt(P):
        c.body(P, c.o2, 'crew')
        if c.s.get('pattern') == 'check':
            with P.clip():
                for i in range(-12, 13):
                    P.line([(0.5 + i * 0.04, 0.6), (0.5 + i * 0.04, 1.05)], c.o3, 0.01, a=120)
                for i in range(12):
                    P.line([(0, 0.7 + i * 0.04), (1, 0.7 + i * 0.04)], c.o3, 0.01, a=120)

    def bib(P):
        bw = c.W * 0.5
        y0 = c.sh_y + 0.08
        P.blob([(0.5 - bw, y0), (0.5 + bw, y0), (0.5 + bw * 1.05, 1.04), (0.5 - bw * 1.05, 1.04)], o1, n=3)
        for sx in (-1, 1):
            P.poly([(0.5 + sx * bw * 0.7, y0 + 0.02), (0.5 + sx * bw * 1.0, y0 + 0.02), (0.5 + sx * c.W * 0.8, c.sh_y - 0.01),
                    (0.5 + sx * c.W * 0.55, c.sh_y - 0.03)], o1)
        with P.clip():
            P.blob([(0.5 - bw * 0.5, y0 + 0.05), (0.5 + bw * 0.5, y0 + 0.05), (0.5 + bw * 0.45, y0 + 0.14),
                    (0.5 - bw * 0.45, y0 + 0.14)], shade(o1, 0.9), n=3)
            P.stitches([(0.5 - bw * 0.9, y0 + 0.015), (0.5 + bw * 0.9, y0 + 0.015)], c.o3 if c.s.get('stitch3') else '#d9b46a',
                       smooth=False)
        for sx in (-1, 1):
            P.circle(0.5 + sx * bw * 0.85, y0 + 0.035, 0.012, '#c9a245')
    return [(shirt, 1.0), (bib, 0.9)]


def o_dress(c):
    o1 = c.o1

    def body(P):
        c.body(P, o1, 'scoop')
        with P.clip():
            pat = c.s.get('pattern', 'dots')
            if pat == 'dots':
                for i in range(-8, 9):
                    for j in range(7):
                        P.circle(0.5 + i * 0.05 + (0.025 if j % 2 else 0), c.sh_y + j * 0.045, 0.008, c.o2)
            elif pat == 'flowers':
                r = random.Random(c.s['name'] + 'd')
                for k in range(22):
                    x, y = 0.5 + (r.random() - 0.5) * 0.7, c.sh_y + r.random() * 0.26
                    for q in range(5):
                        a = q * 1.2566
                        P.circle(x + 0.012 * math.cos(a), y + 0.012 * math.sin(a), 0.009, c.o2)
                    P.circle(x, y, 0.006, c.o3)
            elif pat == 'ikat':
                for i in range(-8, 9):
                    x = 0.5 + i * 0.05
                    for j in range(5):
                        y = c.sh_y + 0.02 + j * 0.06
                        P.poly([(x, y - 0.025), (x + 0.018, y), (x, y + 0.025), (x - 0.018, y)], c.o2 if (i + j) % 2 else c.o3)

    def collar(P):
        if c.s.get('collar', True):
            ny = c.sh_y - 0.045
            nw = c.neck_w * 1.55
            for sx in (-1, 1):
                P.blob([(0.5 + sx * 0.005, ny + 0.065), (0.5 + sx * nw * 1.25, ny - 0.0), (0.5 + sx * nw * 1.6, ny + 0.03),
                        (0.5 + sx * nw * 1.1, ny + 0.085)], c.o2 if c.s.get('pattern') == 'plain' else '#ece6d9', n=6)
    return [(body, 1.0), (collar, 0.6)]


def o_uniform(c):
    o1 = c.o1

    def body(P):
        c.body(P, o1, 'high')
        with P.clip():
            for i in range(4):
                P.circle(0.5, c.sh_y + 0.035 + i * 0.065, 0.009, c.o3)
            for sx in (-1, 1):
                x = 0.5 + sx * c.W * 0.5
                P.blob([(x - 0.06, c.sh_y + 0.07), (x + 0.06, c.sh_y + 0.07), (x + 0.058, c.sh_y + 0.16), (x - 0.058, c.sh_y + 0.16)],
                       shade(o1, 0.92), n=3)
                P.blob([(x - 0.065, c.sh_y + 0.06), (x + 0.065, c.sh_y + 0.06), (x + 0.06, c.sh_y + 0.095), (x - 0.06, c.sh_y + 0.095)],
                       shade(o1, 0.85), n=3)
                P.circle(x, c.sh_y + 0.083, 0.006, c.o3)
            P.line([(0.5, c.sh_y), (0.5, 1.02)], shade(o1, 0.82), 0.004)

    def epaulettes(P):
        for sx in (-1, 1):
            P.blob([(0.5 + sx * c.W * 0.42, c.sh_y - 0.03), (0.5 + sx * c.W * 0.9, c.sh_y + 0.0),
                    (0.5 + sx * c.W * 0.88, c.sh_y + 0.035), (0.5 + sx * c.W * 0.42, c.sh_y + 0.0)], shade(o1, 0.85), n=3)
            P.circle(0.5 + sx * c.W * 0.48, c.sh_y - 0.014, 0.007, c.o3)

    def collar(P):
        ny = c.sh_y - 0.095
        nw = c.neck_w * 1.45
        P.line(spline([(0.5 - nw * 0.95, ny + 0.005), (0.5, ny + 0.015), (0.5 + nw * 0.95, ny + 0.005)], 8), shade(o1, 0.8), 0.012)
    return [(body, 1.0), (epaulettes, 0.6), (collar, 0.4)]


def o_spacesuit(c):
    o1 = col(c.s.get('o1', 'white'))

    def body(P):
        c.body(P, o1, 'crew')
        with P.clip():
            for sx in (-1, 1):
                P.poly([(0.5 + sx * c.W * 0.45, c.sh_y + 0.08), (0.5 + sx * c.W * 0.7, c.sh_y + 0.08),
                        (0.5 + sx * c.W * 0.7, c.sh_y + 0.11), (0.5 + sx * c.W * 0.45, c.sh_y + 0.11)], c.o3)
            P.blob([(0.5 - 0.07, c.sh_y + 0.1), (0.5 + 0.07, c.sh_y + 0.1), (0.5 + 0.07, c.sh_y + 0.2), (0.5 - 0.07, c.sh_y + 0.2)],
                   '#cfc9bd', n=3)
            for i, cc in enumerate(('#a5433a', '#c49638', '#3c7775')):
                P.circle(0.5 - 0.035 + i * 0.035, c.sh_y + 0.15, 0.011, cc)

    def ring(P):
        y = c.sh_y - 0.05
        P.ellipse(0.5, y + 0.005, c.neck_w * 2.4, 0.04, '#a9adb0')
        P.ellipse(0.5, y - 0.004, c.neck_w * 1.9, 0.026, '#7e8387')
    return [(body, 1.0), (ring, 0.8)]


def o_chef(c):
    wc = '#ece8df'

    def body(P):
        c.body(P, wc, 'high')
        with P.clip():
            P.poly([(0.5 - c.W * 0.1, c.sh_y - 0.06), (0.5 + c.W * 0.65, c.sh_y + 0.04), (0.5 + c.W * 0.6, 1.05),
                    (0.5 - c.W * 0.1, 1.05)], '#e3ded4')
            P.line([(0.5 - c.W * 0.1, c.sh_y - 0.06), (0.5 + c.W * 0.65, c.sh_y + 0.04)], '#cbc4b7', 0.004)
            for i in range(3):
                for sx in (-1, 1):
                    P.circle(0.5 + sx * c.W * 0.28, c.sh_y + 0.07 + i * 0.07, 0.01, '#8b8987')

    def kerchief(P):
        y = c.sh_y - 0.06
        P.blob([(0.5 - c.neck_w * 1.3, y - 0.02), (0.5 + c.neck_w * 1.3, y - 0.02), (0.5 + 0.02, y + 0.06), (0.5 - 0.02, y + 0.06)],
               c.o1, n=4)
    return [(body, 1.0), (kerchief, 0.6)]


def o_robe(c):
    """A long padded robe (chapan) with vertical stripes and a trimmed wrap collar."""
    o1, o2, o3 = c.o1, c.o2, c.o3

    def under(P):
        c.body(P, col(c.s.get('shirt', 'white')), 'crew', top=c.sh_y - 0.06)

    def robe(P):
        c.body(P, o1, 'v', vdepth=0.25, notch_w=c.neck_w * 1.3)
        with P.clip():
            for i in range(-14, 15):
                x = 0.5 + i * 0.03
                P.line([(x, 0.6), (x, 1.05)], o2 if i % 3 == 0 else (o3 if i % 3 == 1 else o1), 0.012)

    def trim(P):
        y = c.sh_y - 0.045
        nw = c.neck_w * 1.3
        for sx in (-1, 1):
            P.line([(0.5 + sx * nw * 1.05, y - 0.005), (0.5 + sx * 0.004, y + 0.25), (0.5 + sx * 0.004, 1.03)],
                   col(c.s.get('trim', 'black')), 0.024)
        with P.clip():
            for sx in (-1, 1):
                P.stitches([(0.5 + sx * nw * 1.05, y - 0.005), (0.5 + sx * 0.004, y + 0.25), (0.5 + sx * 0.004, 1.03)],
                           'gold', smooth=False, w=0.004)
    return [(under, 0.7), (robe, 1.0), (trim, 0.5)]


OUTFIT_DRAW = {'sweater': o_sweater, 'suit': o_suit, 'labcoat': o_labcoat, 'hoodie': o_hoodie, 'overalls': o_overalls,
               'dress': o_dress, 'uniform': o_uniform, 'chef': o_chef, 'robe': o_robe, 'vest': o_vest, 'tshirt': o_tshirt,
               'shirt': o_shirt, 'spacesuit': o_spacesuit}


# ---------------------------------------------------------------- rendering a full set of frames
def region_masks(base, frames_eye, frames_mouth, split_y):
    """Masks (0..1 float, OUT x OUT) of where the eye and mouth states differ from base, dilated and feathered."""
    b = np.asarray(base, np.int16)
    yy = np.arange(OUT)[:, None] / OUT

    def diff(frames):
        d = np.zeros((OUT, OUT), bool)
        for f in frames:
            d |= np.abs(np.asarray(f, np.int16) - b).max(axis=2) > 2
        return d
    de, dm = diff(frames_eye), diff(frames_mouth)
    eye = (de | dm) & (yy < split_y)
    mouth = (de | dm) & (yy >= split_y)
    out = []
    for m in (eye, mouth):
        m = binary_dilation(m, iterations=7)
        f = np.clip(gaussian_filter(m.astype(np.float32), 2.2) * 2.0, 0, 1)
        f[m & ~binary_dilation(~m, iterations=3)] = 1.0
        out.append(f)
    solid = np.asarray(base)[..., 3] == 255  # overlays only touch fully opaque pixels, so stacking stays exact
    out = [o * solid for o in out]
    # keep the two regions disjoint at the split line
    sp = int(split_y * OUT)
    out[0][sp:] = 0
    out[1][:sp] = 0
    return out


def overlay(frame, mask):
    a = np.asarray(frame, np.float32).copy()
    a[..., 3] *= mask
    a[a[..., 3] < 0.5] = 0  # clean transparent pixels so the overlay png stays small
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')


def render_all(spec, head_only=False):
    """Returns dict name -> image: base, mouth_<v>, blink, expr_<e>, plus 'full' frames for previews.
    head_only: only the head (no neck, clothes, hair behind the body, hand with mic) for the full-body rig."""
    c = Character(spec)
    c.head_only = head_only
    bare = c.bare()
    base = c.frame(bare, c.state())
    full = {'base': base}
    for v in VISEMES:
        full['mouth_' + v] = base if v == 'closed' else c.frame(bare, c.state(mouth=v))
    full['blink'] = c.frame(bare, c.state(blink=True))
    for e in EXPRESSIONS:
        full['expr_' + e] = base if e == 'neutral' else c.frame(bare, c.state(e))
    eyes = [full['blink']] + [full['expr_' + e] for e in EXPRESSIONS]
    mouths = [full['mouth_' + v] for v in VISEMES] + [full['expr_' + e] for e in EXPRESSIONS]
    me, mm = region_masks(base, eyes, mouths, c.split_y)
    out = {'base': base}
    for v in VISEMES:
        out['mouth_' + v] = overlay(full['mouth_' + v], mm)
    out['blink'] = overlay(full['blink'], me)
    both = np.maximum(me, mm)
    for e in EXPRESSIONS:
        out['expr_' + e] = overlay(full['expr_' + e], both)
    return c, out, full


def compose(base, *overlays):
    """base + overlays (in order) -> full frame; what a renderer does per frame."""
    img = base.copy()
    for o in overlays:
        img.alpha_composite(o)
    return img


# ================================================================ full-body puppets: parts on a 2D rig
# A body is built from the same spec, palette and drawers as the bust. Every part (torso, pelvis, neck, head, hair
# behind the body, upper/lower arms, hands, thighs, shins, feet, tail, wings) is its own felt cut-out with a pivot and a
# parent; a renderer (anim.py) rotates parts per frame. Rest pose: arms and legs hang straight down.
# Units are the bust's (1 unit = OUT px); the body continues below the bust's canvas.
# Naming: _L is the near side, _R the far side; the puppet faces screen-right in both views
# ('q34' = front three-quarter, 'side' = walking profile; the face is turned with a cylinder warp).

def felt_rgba(base, layer, depth=1.0):
    """felt_composite with straight-alpha 'over' compositing, so a part drawn on a transparent canvas keeps clean edges
    (felt_composite assumes the base is opaque wherever the layer's soft edge falls)."""
    return felt_composite(base, layer, depth)  # felt v3 composites premultiplied, so transparent canvases keep clean edges
    from felt import _blur, _grain_for
    W, H = layer.size
    box = layer.getbbox()
    if box is None:
        return base
    s = H / 804.0
    m = int(40 * s * max(depth, 0.3))
    x0, y0, x1, y1 = max(0, box[0] - m), max(0, box[1] - m), min(W, box[2] + m), min(H, box[3] + m)
    arr = np.asarray(layer.crop((x0, y0, x1, y1)), np.float32) / 255.0
    a = arr[..., 3]
    hgt = _blur(a, 9 * s)
    gy, gx = np.gradient(hgt)
    light = -(gx * 0.7 + gy * 0.7) * 22 * s * depth
    rim = np.clip(1 - hgt * 1.8, 0, 1) * a
    sh_ = 1 + np.clip(light, -0.35, 0.35) - 0.18 * rim * depth
    sh_ *= 1 + 0.045 * _grain_for(W, H)[y0:y1, x0:x1]
    rgb_ = np.clip(arr[..., :3] * sh_[..., None], 0, 1)
    off = int(7 * s * depth)
    sh = _blur(a, 6 * s)
    sh2 = np.zeros_like(sh)
    dx = off // 2
    sh2[off:, dx:] = sh[:sh.shape[0] - off or None, :sh.shape[1] - dx or None]
    sh = sh2 * 0.38 * depth
    b = np.asarray(base.crop((x0, y0, x1, y1)), np.float32) / 255.0
    ba = b[..., 3]
    b[..., :3] *= (1 - sh * (1 - a))[..., None]
    out_a = a + ba * (1 - a)
    rgb_o = (rgb_ * a[..., None] + b[..., :3] * (ba * (1 - a))[..., None]) / np.maximum(out_a, 1e-6)[..., None]
    o = np.concatenate([rgb_o, out_a[..., None]], axis=2)
    base.paste(Image.fromarray((np.clip(o, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGBA'), (x0, y0))
    return base


def _crop(img, piv, m=4):
    box = img.getbbox()
    if box is None:
        return None, None
    box = (max(0, box[0] - m), max(0, box[1] - m), min(img.width, box[2] + m), min(img.height, box[3] + m))
    return img.crop(box), (piv[0] - box[0], piv[1] - box[1])


def make_part(layers, pivot, clip=None):
    """Draw [(fn(P), depth)] in absolute units with `pivot` (unit point) mid-canvas; returns (cropped RGBA, pivot px).
    clip(P) draws a mask the finished part is cut to."""
    _ORG[0], _ORG[1] = pivot[0] - 0.5, pivot[1] - 0.5
    _STRAIGHT[0] = True
    try:
        img = Image.new('RGBA', (OUT, OUT), (0, 0, 0, 0))
        for fn, d in layers:
            lay(img, fn, d)
        if clip is not None:
            p = Piece()
            clip(p)
            m = p.mask().reduce(2)
            img.putalpha(ImageChops.multiply(img.getchannel('A'), m))
    finally:
        _ORG[0] = _ORG[1] = 0.0
        _STRAIGHT[0] = False
    return _crop(img, (OUT / 2, OUT / 2))


def yaw_f(u, k):
    """Turn map on [-1, 1]: keeps both edges, moves the centre to k and squeezes the far (right) side, like a face
    turned to screen-right. Monotonic for k < 0.5, so nothing folds or tears."""
    return u + k * (1 - u * u)


def yaw_warp(im, cx, R, k, squeeze=1.0, far_shade=0.1):
    """Turn a front-drawn part about a vertical axis through column cx (px): columns within R px of it are remapped by
    yaw_f (k = turn amount, 0 = none), the far side is shaded a little, and squeeze narrows the result."""
    if not k and squeeze == 1.0:
        return im
    a = np.asarray(im.convert('RGBa'), np.float32)
    H, W = a.shape[:2]
    up = (np.arange(W) + 0.5 - cx) / (R * squeeze)  # output position, normalised
    src = up.copy()
    inside = np.abs(up) <= 1
    if k:
        q = up[inside]
        src[inside] = (1 - np.sqrt(np.maximum(0, 1 - 4 * k * (q - k)))) / (2 * k)
    sx = np.clip(cx + src * R - 0.5, 0, W - 1)
    i0 = np.floor(sx).astype(int)
    i1 = np.minimum(i0 + 1, W - 1)
    f = (sx - i0)[None, :, None]
    out = a[:, i0] * (1 - f) + a[:, i1] * f
    if far_shade and k:
        sh = 1 - far_shade * np.clip(up, 0, 1) ** 1.5
        out[..., :3] *= sh[None, :, None]
    return Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8), 'RGBa').convert('RGBA')


def hull_points(im, n=16):
    """A few points on the convex hull of the opaque pixels (for grounding and bounds in the renderer)."""
    a = np.asarray(im.getchannel('A')) > 96
    ys, xs = np.nonzero(a)
    if len(xs) == 0:
        return []
    pts = []
    for k in range(n):
        t = 2 * math.pi * k / n
        d = xs * math.cos(t) + ys * math.sin(t)
        i = int(np.argmax(d))
        pts.append((int(xs[i]), int(ys[i])))
    return sorted(set(pts), key=pts.index)


def _cap_limb(P, x, y0, y1, r0, r1, c):
    """A vertical limb segment with round ends centred on both joints, so it can turn about either end without a gap."""
    P.circle(x, y0, r0, c)
    P.circle(x, y1, r1, c)
    P.poly([(x - r0, y0), (x + r0, y0), (x + r1, y1), (x - r1, y1)], c)


TAILS = {'fox': 'bushy', 'cat': 'long', 'dog': 'wag', 'bear': 'stub', 'mouse': 'thin', 'hare': 'puff', 'pig': 'curl',
         'owl': 'feathers', 'salmon': 'fin', 'imp': 'arrow', 'monster': 'spikes', 'sheep': 'puff'}
BODY_VIEWS = {  # head / torso turn (yaw_f k), torso squeeze, lateral factor for shoulders and hips (None: follow the turn)
    'q34': dict(head=0.2, torso=0.2, squeeze=1.0, lat=None),
    'side': dict(head=0.4, torso=0.4, squeeze=0.8, lat=0.1),
}
HAND_SHAPES = ['relaxed', 'open', 'fist', 'point', 'flat']


class Body:
    """Builds every part of one full-body puppet. parts(view) -> list of part dicts (see build_body for the export)."""

    def __init__(self, spec):
        self.spec = spec
        c = Character(spec)
        c.body_ref = self
        self.c = c
        s = c.s
        self.s = s
        kid = s['age'] == 'kid'
        self.kit = c.kit
        self.animal = s['kind'] == 'animal'
        k = 0.8 if kid else (0.94 if s['age'] == 'young' else 1.0)
        self.k = k
        W = {'slim': 0.16, 'normal': 0.172, 'broad': 0.205}[s['build']] * (0.88 if kid else 1.0)
        if self.kit in ('bear', 'monster', 'pig'):
            W *= 1.1
        self.W = W
        c.W = W
        self.sh_y = c.sh_y
        self.waist = self.sh_y + 0.2 * (0.84 if kid else 1.0)
        self.hip = self.waist + 0.05
        self.hip_dx = W * 0.47
        self.arm_w = (0.06 if s['build'] == 'broad' else 0.054) * (0.86 if kid else 1.0)
        self.sho_dx, self.sho_y = W * 0.84, self.sh_y + 0.042
        self.Lua, self.Lla = 0.122 * k, 0.108 * k
        self.leg_w = (0.074 if s['build'] == 'broad' else 0.068) * (0.88 if kid else 1.0)
        legk = 0.86 if self.animal else 1.0
        self.Lth, self.Lsh = 0.13 * k * legk, 0.125 * k * legk
        G = c.G
        self.head_piv = (0.5, G.chin - 0.04)
        self.neck_drop = 0.035 if s['kind'] == 'person' else 0.03  # the bust's neck is long for a narrow body
        self.skin = c.skin
        o = s['outfit']
        shirt = col(s.get('shirt', 'white'))
        sl = {'suit': (c.o1, 'long'), 'labcoat': ('#ebe7df', 'long'), 'vest': (shirt, 'long'), 'hoodie': (c.o1, 'long'),
              'overalls': (c.o2, 'long'), 'dress': (c.o1, 'short'), 'uniform': (c.o1, 'long'), 'chef': ('#ece8df', 'long'),
              'robe': (c.o1, 'long'), 'tshirt': (c.o1, 'short'), 'shirt': (c.o1, 'long'), 'sweater': (c.o1, 'long'),
              'spacesuit': (col(s.get('o1', 'white')), 'long')}[o]
        self.sleeve = col(s.get('sleeve')) or sl[0]
        self.sleeve_len = s.get('sleeve_len', sl[1])
        rnd = random.Random(s['name'] + 'body')
        casual = ['denim', 'charcoal', 'khaki', 'navy', 'coffee', 'slate']
        casual = [x for x in casual if abs(lum(col(x)) - lum(c.o1)) > 18] or ['charcoal']
        tr = {'suit': c.o1, 'uniform': c.o1, 'overalls': c.o1, 'spacesuit': col(s.get('o1', 'white')),
              'chef': 'charcoal', 'robe': 'charcoal', 'labcoat': 'charcoal', 'vest': shade(c.o1, 0.55),
              'dress': None}.get(o, rnd.choice(casual))
        self.trousers = col(s.get('trousers') or tr) if tr else None
        if o == 'vest' and not s.get('trousers'):
            self.trousers = col('charcoal') if lum(c.o1) > 90 else mix(c.o1, '#38363a', 0.5)
        shoes = {'suit': 'black', 'uniform': 'black', 'vest': 'black', 'spacesuit': '#a9adb0', 'chef': 'charcoal',
                 'dress': rnd.choice(['wine', 'black', 'coffee', 'navy'])}.get(o, rnd.choice(['coffee', 'chestnut', 'charcoal',
                                                                                              'rust', 'navy', 'black']))
        self.shoes = col(s.get('shoes', shoes))
        self.glove = '#d5d0c6' if o == 'spacesuit' else None
        self.paws = self.animal or self.kit in ('imp', 'monster', 'sheep')
        self.tail = TAILS.get(self.kit)

    # ------------------------------------------------------------ geometry of the rest pose (absolute units)
    def joints(self):
        x0 = 0.5
        J = {
            'pelvis': (None, (x0, self.waist)),
            'torso': ('pelvis', (x0, self.waist)),
            'neck': ('torso', (x0, self.sh_y)),
            'head': ('torso', (x0, self.head_piv[1] + self.neck_drop)),
            'hair_back': ('head', (x0, self.head_piv[1] + self.neck_drop)),
        }
        for side, sx in (('L', -1), ('R', 1)):
            J['upper_arm_' + side] = ('torso', (x0 + sx * self.sho_dx, self.sho_y))
            J['lower_arm_' + side] = ('upper_arm_' + side, (x0 + sx * self.sho_dx, self.sho_y + self.Lua))
            J['hand_' + side] = ('lower_arm_' + side, (x0 + sx * self.sho_dx, self.sho_y + self.Lua + self.Lla))
            J['thigh_' + side] = ('pelvis', (x0 + sx * self.hip_dx, self.hip))
            J['shin_' + side] = ('thigh_' + side, (x0 + sx * self.hip_dx, self.hip + self.Lth))
            J['foot_' + side] = ('shin_' + side, (x0 + sx * self.hip_dx, self.hip + self.Lth + self.Lsh))
        if self.tail:
            J['tail'] = ('pelvis', (x0, self.hip - 0.01))
        if self.kit == 'imp':
            J['wings'] = ('torso', (x0, self.sh_y + 0.07))
        return J

    # ------------------------------------------------------------ torso, pelvis, neck
    def torso_layers(self):
        c, s = self.c, self.s
        out = []
        if s['outfit'] == 'hoodie':
            out.append((c.hood, 0.9))
        out += list(OUTFIT_DRAW[s['outfit']](c))
        if 'scarf' in c.acc_names():
            out.append((c.scarf, 1.0))
        for name in ('necklace', 'stethoscope', 'lanyard', 'bowtie', 'flower'):
            if name in c.acc_names():
                out.append((getattr(c, 'acc_' + name), 0.6))
        return out

    def torso_clip(self, P):
        c = self.c
        P.poly(c.torso_pts('crew', W=self.W * 1.04), 'white')
        P.poly([(0, 0), (1, 0), (1, self.sh_y + 0.03), (0, self.sh_y + 0.03)], 'white')
        P.poly([(0.5 - self.W * 1.05, 0), (0.5 + self.W * 1.05, 0), (0.5 + self.W * 1.05, self.sh_y + 0.1),
                (0.5 - self.W * 1.05, self.sh_y + 0.1)], 'white')

    def pelvis_layers(self):
        s, c, W = self.s, self.c, self.W
        wy, hy, o = self.waist, self.hip, s['outfit']
        k = 0.82 if s['age'] == 'kid' else 1.0
        out = []
        tr = self.trousers

        def pants(P):
            P.blob([(0.5 - W * 0.84, wy - 0.035), (0.5 + W * 0.84, wy - 0.035), (0.5 + W * 0.9, hy + 0.01),
                    (0.5 + W * 0.7, hy + 0.05), (0.5, hy + 0.035), (0.5 - W * 0.7, hy + 0.05), (0.5 - W * 0.9, hy + 0.01)],
                   tr or self.skin, n=6)
            with P.clip():
                P.stitches([(0.5 + 0.01, wy + 0.0), (0.5 + 0.012, hy + 0.025)], shade(tr or self.skin, 0.62), smooth=False)
        if o == 'dress':
            L = min(0.24 * k, 0.62 * (self.Lth + self.Lsh))

            def skirt(P):
                P.blob([(0.5 - W * 0.78, wy - 0.03), (0.5 + W * 0.78, wy - 0.03), (0.5 + W * 1.02, wy + L * 0.5),
                        (0.5 + W * 1.3, wy + L), (0.5, wy + L + 0.012), (0.5 - W * 1.3, wy + L)
                        , (0.5 - W * 1.02, wy + L * 0.5)], c.o1, n=8)
                with P.clip():
                    pat = s.get('pattern', 'dots')
                    if pat == 'dots':
                        for i in range(-8, 9):
                            for j in range(8):
                                P.circle(0.5 + i * 0.05 + (0.025 if j % 2 else 0), wy + j * 0.045, 0.008, c.o2)
                    elif pat == 'flowers':
                        r = random.Random(s['name'] + 'skirt')
                        for _ in range(18):
                            x, y = 0.5 + (r.random() - 0.5) * W * 2.6, wy + r.random() * L
                            for q in range(5):
                                a = q * 1.2566
                                P.circle(x + 0.012 * math.cos(a), y + 0.012 * math.sin(a), 0.009, c.o2)
                            P.circle(x, y, 0.006, c.o3)
                    elif pat == 'ikat':
                        for i in range(-8, 9):
                            for j in range(6):
                                x, y = 0.5 + i * 0.05, wy + 0.02 + j * 0.06
                                P.poly([(x, y - 0.025), (x + 0.018, y), (x, y + 0.025), (x - 0.018, y)],
                                       c.o2 if (i + j) % 2 else c.o3)
                    P.stitches([(0.5 - W * 1.4, wy + L - 0.018), (0.5, wy + L - 0.006), (0.5 + W * 1.4, wy + L - 0.018)],
                               shade(c.o1, 0.6))
            out.append((skirt, 1.0))
        elif o == 'robe':
            L = min(0.32 * k, 0.8 * (self.Lth + self.Lsh))
            o1, o2, o3 = c.o1, c.o2, c.o3

            def robe(P):
                P.blob([(0.5 - W * 0.82, wy - 0.03), (0.5 + W * 0.82, wy - 0.03), (0.5 + W * 1.0, wy + L * 0.6),
                        (0.5 + W * 1.08, wy + L), (0.5, wy + L + 0.006), (0.5 - W * 1.08, wy + L), (0.5 - W * 1.0, wy + L * 0.6)],
                       o1, n=6)
                with P.clip():
                    for i in range(-14, 15):
                        x = 0.5 + i * 0.03
                        P.line([(x, wy - 0.05), (x, wy + L + 0.05)], o2 if i % 3 == 0 else (o3 if i % 3 == 1 else o1), 0.012)
                    P.line([(0.5 + 0.004, wy - 0.05), (0.5 + 0.004, wy + L + 0.05)], col(s.get('trim', 'black')), 0.024)
                    P.stitches([(0.5 + 0.004, wy - 0.05), (0.5 + 0.004, wy + L + 0.05)], 'gold', smooth=False, w=0.004)
                    P.line([(0.5 - W * 1.2, wy + L - 0.01), (0.5 + W * 1.2, wy + L - 0.01)], col(s.get('trim', 'black')), 0.02)
            out.append((robe, 1.0))
        elif o == 'labcoat':
            L = min(0.17 * k, 0.55 * (self.Lth + self.Lsh))
            wc = '#ebe7df'
            out.append((pants, 0.8))

            def tails(P):
                for sx in (-1, 1):
                    P.blob([(0.5 + sx * 0.004, wy - 0.03), (0.5 + sx * W * 0.84, wy - 0.03), (0.5 + sx * W * 1.0, wy + L * 0.6),
                            (0.5 + sx * W * 1.04, wy + L), (0.5 + sx * 0.02, wy + L), (0.5 + sx * 0.008, wy + L * 0.5)], wc, n=5)
                with P.clip():
                    x0 = 0.5 + W * 0.3
                    P.blob([(x0, wy + 0.04), (x0 + 0.09, wy + 0.04), (x0 + 0.088, wy + 0.11), (x0 + 0.004, wy + 0.11)],
                           '#dcd6cb', n=3)
                    P.stitches([(0.5 - W * 1.1, wy + L - 0.015), (0.5 + W * 1.1, wy + L - 0.015)], '#bdb6a8', smooth=False)
            out.append((tails, 1.0))
        else:
            out.append((pants, 1.0))
            if o in ('uniform', 'shirt', 'spacesuit') and tr:
                def belt(P):
                    bc = '#a9adb0' if o == 'spacesuit' else ('#3b3134' if lum(tr) > 70 else '#6a5040')
                    P.blob([(0.5 - W * 0.86, wy + 0.046), (0.5 + W * 0.86, wy + 0.046), (0.5 + W * 0.87, wy + 0.076),
                            (0.5 - W * 0.87, wy + 0.076)], bc, n=3)
                    P.blob([(0.5 - 0.02, wy + 0.044), (0.5 + 0.02, wy + 0.044), (0.5 + 0.02, wy + 0.078), (0.5 - 0.02, wy + 0.078)],
                           '#c9a245' if o != 'spacesuit' else '#7e8387', n=3)
                out.append((belt, 0.5))
            if o == 'chef':
                def check(P):
                    P.blob([(0.5 - W * 0.84, wy - 0.035), (0.5 + W * 0.84, wy - 0.035), (0.5 + W * 0.9, hy + 0.01),
                            (0.5 + W * 0.7, hy + 0.05), (0.5, hy + 0.035), (0.5 - W * 0.7, hy + 0.05), (0.5 - W * 0.9, hy + 0.01)],
                           tr, n=6)
                out[0] = (pants, 1.0)
        return out

    def neck_layers(self):
        return [(self.c.neck, 0.7)]

    # ------------------------------------------------------------ arms and hands
    def _sleeve_detail(self, P, x, y0, y1, colr):
        P.stitches([(x + self.arm_w * 0.28, y0 + 0.01), (x + self.arm_w * 0.24, y1 - 0.01)], shade(colr, 0.66), smooth=False)

    def upper_arm_layers(self, x, y):
        r0, r1 = self.arm_w * 0.6, self.arm_w * 0.5
        y1 = y + self.Lua
        sl, out = self.sleeve, []
        robot = self.s.get('robot')
        if robot:
            def arm(P):
                _cap_limb(P, x, y, y1, r0 * 0.85, r1 * 0.8, shade(self.skin, 0.88))
                P.circle(x, y, r0 * 0.55, shade(self.skin, 0.7))
            return [(arm, 0.9)]
        if self.sleeve_len == 'short':
            def skin(P):
                _cap_limb(P, x, y, y1, r0 * 0.9, r1 * 0.95, self.skin)
            out.append((skin, 0.8))

            def sleeve(P):
                yb = y + self.Lua * 0.5
                P.circle(x, y, r0 * 1.05, sl)
                P.poly([(x - r0 * 1.05, y), (x + r0 * 1.05, y), (x + r0 * 1.12, yb), (x - r0 * 1.12, yb)], sl)
                with P.clip():
                    P.line([(x - r0 * 1.2, yb - 0.01), (x + r0 * 1.2, yb - 0.01)], shade(sl, 0.8), 0.008)
            out.append((sleeve, 1.0))
            return out

        def sleeve(P):
            _cap_limb(P, x, y, y1, r0, r1, sl)
            with P.clip():
                self._sleeve_detail(P, x, y, y1, sl)
                if self.s['outfit'] == 'robe':
                    for i in range(-3, 4):
                        P.line([(x + i * 0.018, y - 0.05), (x + i * 0.018, y1 + 0.05)],
                               self.c.o2 if i % 3 == 0 else (self.c.o3 if i % 3 == 1 else self.c.o1), 0.008)
        out.append((sleeve, 1.0))
        return out

    def lower_arm_layers(self, x, y):
        r0, r1 = self.arm_w * 0.5, self.arm_w * 0.44
        y1 = y + self.Lla
        sl = self.sleeve
        if self.s.get('robot'):
            def arm(P):
                _cap_limb(P, x, y, y1, r0 * 0.8, r1 * 0.85, shade(self.skin, 0.95))
                P.circle(x, y, r0 * 0.45, shade(self.skin, 0.7))
            return [(arm, 0.9)]
        if self.sleeve_len == 'short':
            def skin(P):
                _cap_limb(P, x, y, y1, r0 * 0.95, r1 * 0.92, self.skin)
            return [(skin, 0.8)]
        wide = self.s['outfit'] in ('robe', 'labcoat') or self.kit == 'owl'

        def sleeve(P):
            _cap_limb(P, x, y, y1, r0, r1 * (1.25 if wide else 1.0), sl)
            with P.clip():
                self._sleeve_detail(P, x, y, y1, sl)
                if self.s['outfit'] == 'robe':
                    for i in range(-3, 4):
                        P.line([(x + i * 0.018, y - 0.05), (x + i * 0.018, y1 + 0.05)],
                               self.c.o2 if i % 3 == 0 else (self.c.o3 if i % 3 == 1 else self.c.o1), 0.008)

        def cuff(P):
            cc = self.glove or shade(sl, 0.86)
            if self.s['outfit'] == 'robe':
                cc = col(self.s.get('trim', 'black'))
            if self.s['outfit'] == 'sweater':
                cc = shade(sl, 0.82)
            rr = r1 * (1.25 if wide else 1.0) * 1.06
            P.blob([(x - rr, y1 - 0.024), (x + rr, y1 - 0.024), (x + rr, y1 + 0.008), (x - rr, y1 + 0.008)], cc, n=3)
            if self.s['outfit'] == 'sweater':
                with P.clip():
                    for i in range(-5, 6):
                        P.line([(x + i * 0.007, y1 - 0.03), (x + i * 0.007, y1 + 0.01)], shade(sl, 0.7), 0.0025)
        return [(sleeve, 1.0), (cuff, 0.5)]

    def hand_layers(self, x, y, shape='relaxed'):
        """A hand hanging down from the wrist at (x, y), thumb towards +x (forward)."""
        hc = self.glove or self.skin
        if self.s.get('robot'):
            hc = shade(self.skin, 0.8)
        aw = self.arm_w
        pad = self.c.skin2 or shade(hc, 0.82)
        kit = self.kit
        line = shade(hc, 0.74)
        cy = y + aw * 0.72

        if kit == 'owl':  # wing tip: a fan of three feathers
            spread = {'relaxed': 0.25, 'open': 0.7, 'fist': 0.12, 'point': 0.15, 'flat': 0.4}[shape]

            def wing(P):
                for i, a in enumerate((-spread, 0, spread)):
                    L = aw * (1.75 if i == 1 else 1.45)
                    ex, ey = x + math.sin(a) * L, y + math.cos(a) * L
                    P.taper([(x, y - 0.005), ((x + ex) / 2, (y + ey) / 2), (ex, ey)], shade(self.skin, 0.9 + 0.06 * i),
                            aw * 0.55, aw * 0.5, aw * 0.12)
            return [(wing, 0.8)]
        if kit == 'salmon':
            spread = {'relaxed': 0.0, 'open': 0.4, 'fist': -0.1, 'point': 0.0, 'flat': 0.1}[shape]

            def fin(P):
                P.blob([(x - aw * 0.45, y - 0.01), (x + aw * 0.45, y - 0.01), (x + aw * (0.75 + spread), y + aw * 1.5),
                        (x, y + aw * 1.25), (x - aw * (0.75 + spread), y + aw * 1.5)], self.c.skin2 or self.skin, n=6)
                with P.clip():
                    for i in (-2, -1, 0, 1, 2):
                        P.line([(x, y), (x + i * aw * 0.3, y + aw * 1.5)], shade(self.c.skin2 or self.skin, 0.8), 0.003)
            return [(fin, 0.8)]

        def palm(P, closed=False):
            if closed:
                P.blob([(x - aw * 0.48, y - 0.004), (x + aw * 0.48, y - 0.004), (x + aw * 0.58, cy), (x + aw * 0.4, cy + aw * 0.5),
                        (x - aw * 0.4, cy + aw * 0.5), (x - aw * 0.56, cy)], hc, n=6)
            else:
                P.blob([(x - aw * 0.48, y - 0.004), (x + aw * 0.48, y - 0.004), (x + aw * 0.6, cy + aw * 0.1),
                        (x + aw * 0.4, cy + aw * 0.72), (x - aw * 0.4, cy + aw * 0.72), (x - aw * 0.58, cy + aw * 0.1)], hc, n=6)

        def thumb(P, out=0.0):
            P.taper([(x + aw * 0.4, y + aw * 0.25), (x + aw * (0.68 + out), cy - aw * 0.05 + out * 0.2 * aw),
                     (x + aw * (0.72 + out * 1.3), cy + aw * (0.3 - out * 0.3))], hc, aw * 0.36, aw * 0.3, aw * 0.26)

        def toes(P, n, spread, L):
            for i in range(n):
                t = (i - (n - 1) / 2) / max(1, (n - 1) / 2)
                a = t * spread
                bx, by = x + t * aw * 0.32, cy + aw * 0.35
                ex, ey = bx + math.sin(a) * L, by + math.cos(a) * L
                P.line([(bx, by), (ex, ey)], hc, aw * (0.3 if not self.paws else 0.36))

        def creases(P, closed):
            with P.clip():
                if closed:
                    for i in range(3):
                        P.line([(x - aw * 0.4, cy + aw * (0.0 + 0.16 * i)), (x + aw * 0.25, cy + aw * (0.05 + 0.16 * i))], line,
                               0.0032)
                else:
                    for i in (-1, 0, 1):
                        P.line([(x + i * aw * 0.2, cy + aw * 0.35), (x + i * aw * 0.22, cy + aw * 0.68)], line, 0.0032)
                if self.paws:
                    P.ellipse(x, cy + aw * 0.05, aw * 0.26, aw * 0.2, pad)

        def hand(P):
            if shape in ('relaxed', 'flat'):
                palm(P)
                thumb(P, 0.0 if shape == 'relaxed' else 0.1)
                creases(P, False)
            elif shape == 'open':
                palm(P, True)
                toes(P, 4, 0.5, aw * 0.75)
                thumb(P, 0.4)
                creases(P, True)
            elif shape == 'fist':
                palm(P, True)
                thumb(P, -0.12)
                creases(P, True)
            elif shape == 'point':
                palm(P, True)
                P.line([(x + aw * 0.12, cy + aw * 0.3), (x + aw * 0.12, cy + aw * 1.15)], hc, aw * 0.3)
                thumb(P, -0.12)
                creases(P, True)
        return [(hand, 0.8)]

    # ------------------------------------------------------------ legs and feet
    def leg_colour(self):
        return self.trousers or (self.skin if self.paws else mix(self.skin, '#d8cfc4', 0.15))

    def thigh_layers(self, x, y):
        r0, r1 = self.leg_w * 0.56, self.leg_w * 0.5
        y1 = y + self.Lth
        lc = self.leg_colour()

        def thigh(P):
            _cap_limb(P, x, y - 0.01, y1, r0, r1, lc)
            if self.trousers:
                with P.clip():
                    P.stitches([(x + r0 * 0.55, y), (x + r1 * 0.55, y1)], shade(lc, 0.66), smooth=False)
        return [(thigh, 1.0)]

    def shin_layers(self, x, y):
        r0, r1 = self.leg_w * 0.5, self.leg_w * 0.44
        y1 = y + self.Lsh
        lc = self.leg_colour()
        out = []

        def shin(P):
            _cap_limb(P, x, y, y1, r0, r1, lc)
            if self.trousers:
                with P.clip():
                    P.stitches([(x + r0 * 0.55, y), (x + r1 * 0.55, y1)], shade(lc, 0.66), smooth=False)
        out.append((shin, 1.0))
        if self.trousers and not self.paws:
            def hem(P):
                rr = r1 * 1.12
                P.blob([(x - rr, y1 - 0.018), (x + rr, y1 - 0.018), (x + rr * 1.04, y1 + 0.012), (x - rr * 1.04, y1 + 0.012)],
                       shade(lc, 0.9), n=3)
            out.append((hem, 0.5))
        if self.s['outfit'] == 'dress' and not self.paws:
            def sock(P):
                P.blob([(x - r1 * 1.02, y1 - 0.022), (x + r1 * 1.02, y1 - 0.022), (x + r1 * 1.05, y1 + 0.01),
                        (x - r1 * 1.05, y1 + 0.01)], 'white' if self.s['age'] == 'kid' else shade(self.skin, 0.95), n=3)
            out.append((sock, 0.4))
        return out

    def foot_layers(self, x, y, view):
        lw = self.leg_w
        if self.paws or self.kit == 'owl':
            fc = self.skin
            if self.kit == 'owl':
                fc = col('mustard')
            elif self.kit == 'frog':
                fc = shade(self.skin, 0.95)
            elif self.kit in ('sheep', 'pig'):
                fc = self.c.skin2 if self.kit == 'sheep' else shade(self.skin, 0.9)
            elif self.kit == 'robot':
                fc = shade(self.skin, 0.75)

            def paw(P):
                if self.kit == 'owl' or self.kit == 'frog':
                    n = 3
                    for i in range(n):
                        a = (i - 1) * (0.45 if view == 'q34' else 0.3) + (0.35 if view == 'q34' else 1.2)
                        L = lw * (0.95 if self.kit == 'owl' else 1.05)
                        P.line([(x, y + lw * 0.2), (x + math.sin(a) * L, y + lw * 0.2 + math.cos(a) * L * 0.45 + 0.012)],
                               fc, lw * (0.22 if self.kit == 'owl' else 0.32))
                    if self.kit == 'frog':
                        P.blob([(x, y + 0.004), (x + lw * 1.05, y + lw * 0.3), (x + lw * 0.9, y + lw * 0.62), (x - lw * 0.15, y + lw * 0.55)],
                               fc, n=6)
                    P.circle(x, y + lw * 0.22, lw * 0.32, fc)
                    return
                toe = lw * (0.55 if view == 'q34' else 0.85)
                P.blob([(x - lw * 0.5, y - 0.006), (x + lw * 0.2, y - 0.01), (x + toe + lw * 0.35, y + lw * 0.3),
                        (x + toe + lw * 0.3, y + lw * 0.62), (x - lw * 0.45, y + lw * 0.62)], fc, n=7)
                with P.clip():
                    for i in range(3):
                        tx = x + toe + lw * (0.05 - 0.17 * i)
                        P.line([(tx, y + lw * 0.42), (tx + lw * 0.08, y + lw * 0.66)], shade(fc, 0.7), 0.003)
            return [(paw, 0.9)]
        sc = self.shoes
        toe = lw * (0.62 if view == 'q34' else 0.95)

        def shoe(P):
            P.blob([(x - lw * 0.55, y - 0.002), (x + lw * 0.3, y - 0.008), (x + toe + lw * 0.3, y + lw * 0.3),
                    (x + toe + lw * 0.34, y + lw * 0.58), (x - lw * 0.55, y + lw * 0.58)], sc, n=7)
            with P.clip():
                P.poly([(x - lw, y + lw * 0.47), (x + toe + lw, y + lw * 0.47), (x + toe + lw, y + lw), (x - lw, y + lw)],
                       shade(sc, 0.62) if lum(sc) > 60 else mix(sc, '#d8d0c0', 0.35))
                if self.s['outfit'] not in ('suit', 'uniform', 'vest', 'dress', 'spacesuit'):
                    for i in range(3):
                        lx = x + lw * (0.05 + 0.16 * i)
                        P.line([(lx, y + lw * 0.08 + i * 0.006), (lx + lw * 0.16, y + lw * 0.02 + i * 0.006)], '#ece6d9', 0.0035)
        return [(shoe, 0.9)]

    def sole_points(self, x, y, view):
        lw = self.leg_w
        toe = lw * (0.62 if view == 'q34' else 0.95)
        yb = y + lw * (0.6 if not (self.kit in ('owl', 'frog')) else 0.62)
        return [(x - lw * 0.45, yb), (x + toe + lw * 0.25, yb)]

    # ------------------------------------------------------------ tail and wings (drawn pointing back, screen-left)
    def tail_layers(self, x, y):
        t, fc, f2 = self.tail, self.skin, self.c.skin2 or mix(self.skin, '#ffffff', 0.5)

        def tail(P):
            if t == 'bushy':
                pts = [(x + 0.01, y - 0.01), (x - 0.08, y + 0.03), (x - 0.17, y - 0.02), (x - 0.21, y - 0.1), (x - 0.17, y - 0.07),
                       (x - 0.1, y - 0.015), (x - 0.02, y - 0.03)]
                P.blob([(x + 0.01, y - 0.02), (x - 0.06, y + 0.035), (x - 0.15, y + 0.025), (x - 0.22, y - 0.05),
                        (x - 0.22, y - 0.12), (x - 0.15, y - 0.06), (x - 0.07, y - 0.035)], fc, n=8)
                with P.clip():
                    P.circle(x - 0.225, y - 0.09, 0.06, f2)
            elif t == 'long':
                P.taper([(x, y), (x - 0.08, y + 0.02), (x - 0.14, y - 0.04), (x - 0.15, y - 0.13)], fc, 0.03, 0.026, 0.02)
            elif t == 'wag':
                P.taper([(x, y), (x - 0.06, y - 0.03), (x - 0.1, y - 0.1)], fc, 0.036, 0.03, 0.012)
            elif t == 'stub':
                P.circle(x - 0.02, y - 0.005, 0.03, fc)
            elif t == 'thin':
                P.taper([(x, y), (x - 0.07, y + 0.03), (x - 0.14, y - 0.01), (x - 0.18, y + 0.05), (x - 0.24, y + 0.03)],
                        mix(fc, '#d99aa6', 0.6), 0.014, 0.01, 0.005)
            elif t == 'puff':
                P.circle(x - 0.025, y - 0.01, 0.038, '#f1ebdf' if self.kit == 'sheep' else f2)
            elif t == 'curl':
                pts = [(x - 0.02 - 0.03 * (1 - i / 24) * math.cos(i * 0.5) - i * 0.0015,
                        y - 0.01 - 0.03 * (1 - i / 24) * math.sin(i * 0.5)) for i in range(25)]
                P.line(pts, fc, 0.011)
            elif t == 'feathers':
                for i, a in enumerate((-0.35, 0.0, 0.35)):
                    P.taper([(x, y - 0.01), (x - 0.07 + a * 0.05, y + 0.06 + a * 0.06)], shade(fc, 0.85 + 0.05 * i), 0.035, 0.01)
            elif t == 'fin':
                P.taper([(x, y), (x - 0.06, y + 0.02)], fc, 0.04, 0.025)
                P.blob([(x - 0.06, y + 0.02), (x - 0.13, y - 0.04), (x - 0.11, y + 0.025), (x - 0.13, y + 0.09)], f2, n=6)
            elif t == 'arrow':
                P.taper([(x, y), (x - 0.08, y + 0.04), (x - 0.15, y - 0.02), (x - 0.17, y - 0.1)], shade(fc, 0.85), 0.012, 0.009, 0.007)
                P.poly([(x - 0.17, y - 0.135), (x - 0.2, y - 0.08), (x - 0.17, y - 0.095), (x - 0.145, y - 0.075)], shade(fc, 0.85))
            elif t == 'spikes':
                P.taper([(x, y), (x - 0.06, y + 0.02), (x - 0.11, y - 0.01)], fc, 0.05, 0.035, 0.012)
                for i in range(3):
                    P.poly([(x - 0.03 - i * 0.03, y - 0.005), (x - 0.045 - i * 0.03, y - 0.04), (x - 0.06 - i * 0.03, y - 0.0)], f2)
        return [(tail, 0.9)]

    def wing_layers(self, x, y):
        wc = shade(self.skin, 0.75)

        def wings(P):
            for sx in (-1, 1):
                pts = [(x, y), (x + sx * 0.12, y - 0.1), (x + sx * 0.24, y - 0.06), (x + sx * 0.2, y + 0.0), (x + sx * 0.16, y - 0.01),
                       (x + sx * 0.12, y + 0.04), (x + sx * 0.08, y + 0.02), (x + sx * 0.03, y + 0.07)]
                P.poly(pts, wc)
                with P.clip():
                    for e in pts[2::2]:
                        P.line([(x + sx * 0.12, y - 0.1), e], shade(wc, 0.7), 0.004)
        return [(wings, 0.7)]

    # ------------------------------------------------------------ assembling
    def build(self):
        """Renders every part in the rest pose. Returns dict: views -> list of parts; 'head' states; hand variants."""
        c = self.c
        J = self.joints()
        P = {}
        # head: the bust's head-only render (talking states stay usable)
        _STRAIGHT[0] = True
        try:
            _c, out, _full = render_all(self.spec, head_only=True)
            hair = HAIR_DRAW.get(self.s['hair'])
            hb = None
            if hair and hair.get('back'):
                hb = Image.new('RGBA', (OUT, OUT), (0, 0, 0, 0))
                lay(hb, lambda Pc: hair['back'](c, Pc), 0.9)
        finally:
            _STRAIGHT[0] = False
        hp = (self.head_piv[0] * OUT, self.head_piv[1] * OUT)
        self.head_states = out
        self.hair_back_img = hb
        P['torso'] = make_part(self.torso_layers(), J['torso'][1], clip=self.torso_clip)
        P['pelvis'] = make_part(self.pelvis_layers(), J['pelvis'][1])
        P['neck'] = make_part(self.neck_layers(), J['neck'][1],
                              clip=lambda Pc: Pc.poly([(0, 0), (1, 0), (1, self.sh_y + 0.04), (0, self.sh_y + 0.04)], 'white'))
        for side in 'LR':
            x, y = J['upper_arm_' + side][1]
            P['upper_arm_' + side] = make_part(self.upper_arm_layers(x, y), (x, y))
            x, y = J['lower_arm_' + side][1]
            P['lower_arm_' + side] = make_part(self.lower_arm_layers(x, y), (x, y))
            x, y = J['hand_' + side][1]
            for shp in HAND_SHAPES:
                P['hand_%s:%s' % (side, shp)] = make_part(self.hand_layers(x, y, shp), (x, y))
            x, y = J['thigh_' + side][1]
            P['thigh_' + side] = make_part(self.thigh_layers(x, y), (x, y))
            x, y = J['shin_' + side][1]
            P['shin_' + side] = make_part(self.shin_layers(x, y), (x, y))
            x, y = J['foot_' + side][1]
            for v in BODY_VIEWS:
                P['foot_%s@%s' % (side, v)] = make_part(self.foot_layers(x, y, v), (x, y))
        if self.tail:
            P['tail'] = make_part(self.tail_layers(*J['tail'][1]), J['tail'][1])
        if 'wings' in J:
            P['wings'] = make_part(self.wing_layers(*J['wings'][1]), J['wings'][1])
        self.P = P
        self.J = J
        self.head_px = hp
        return P


BODY_Z = ['tail', 'wings', 'hair_back', 'upper_arm_R', 'hand_R', 'lower_arm_R', 'foot_R', 'shin_R', 'thigh_R', 'foot_L',
          'shin_L', 'thigh_L', 'pelvis', 'neck', 'torso', 'head', 'upper_arm_L', 'hand_L', 'lower_arm_L']
FAR_SHADE = 0.86  # far-side limbs are a touch darker
BODY_SCALE = 0.75  # parts are exported at 768 px per unit (the bust is 1024): full figure about 900 px tall


def _darken(im, k):
    a = np.asarray(im, np.float32).copy()
    a[..., :3] *= k
    return Image.fromarray(np.clip(a + 0.5, 0, 255).astype(np.uint8), 'RGBA')


def build_body(spec, root):
    """Render one character's full-body rig into root/<name>/: rig.json and part PNGs. Returns the rig dict."""
    import json
    import os
    b = Body(spec)
    P = b.build()
    J = b.J
    name = spec['name']
    d = os.path.join(root, name)
    os.makedirs(d, exist_ok=True)

    def save(im, fn):
        im.save(os.path.join(d, fn), optimize=True)
        return fn

    ks = BODY_SCALE

    def rs(im):
        return im.resize((max(1, round(im.width * ks)), max(1, round(im.height * ks))), Image.LANCZOS) if ks != 1 else im

    def entry(im, piv, fn):
        im = rs(im)
        return {'file': save(im, fn), 'pivot': [round(piv[0] * ks, 1), round(piv[1] * ks, 1)], 'hull': hull_points(im)}

    shared = {}
    for k, (im, piv) in P.items():
        if '@' in k or k in ('torso', 'pelvis', 'neck') or im is None:
            continue
        part, _, shp = k.partition(':')
        if part.endswith('_R'):
            im = _darken(im, FAR_SHADE)
        shared[k] = entry(im, piv, k.replace(':', '_') + '.png')
    head = b.head_states
    hb = head['base']
    box = hb.getbbox()
    for v in head.values():
        bb = v.getbbox()
        if bb:
            box = (min(box[0], bb[0]), min(box[1], bb[1]), max(box[2], bb[2]), max(box[3], bb[3]))
    box = (max(0, box[0] - 4), max(0, box[1] - 4), min(OUT, box[2] + 4), min(OUT, box[3] + 4))
    hcx = OUT / 2 - box[0]
    hR = max(hcx, box[2] - OUT / 2)
    hpiv = (b.head_px[0] - box[0], b.head_px[1] - box[1])
    rig = {'name': name, 'px_per_unit': OUT * ks, 'hand_shapes': HAND_SHAPES, 'visemes': VISEMES, 'expressions': EXPRESSIONS,
           'views': {}}
    for view, prm in BODY_VIEWS.items():
        V = {'root': 'pelvis', 'parts': {}}
        # head and its talking states, turned
        hbw = yaw_warp(hb.crop(box), hcx, hR, prm['head'])  # noqa
        V['parts']['head'] = dict(entry(hbw, hpiv, 'head_%s.png' % view))
        states = {}
        for k, im in head.items():
            if k in ('base', 'expr_neutral'):  # expr_neutral would equal the base
                continue
            w = rs(yaw_warp(im.crop(box), hcx, hR, prm['head']))
            bb = w.getbbox()
            if bb is None:
                continue
            states[k] = {'file': save(w.crop(bb), 'head_%s_%s.png' % (view, k)), 'at': [bb[0], bb[1]]}
        V['head_states'] = states
        if b.hair_back_img is not None:
            hbb = b.hair_back_img.crop(box)
            hbw2 = yaw_warp(hbb, hcx, hR, prm['head'])
            V['parts']['hair_back'] = entry(hbw2, hpiv, 'hair_back_%s.png' % view)
        # torso, pelvis, neck: turned about their centre column
        for k in ('torso', 'pelvis', 'neck'):
            im, piv = P[k]
            if im is None:
                continue
            R = max(piv[0], im.width - piv[0])
            if k == 'torso':
                R = b.W * 1.02 * OUT
            kk = prm['torso'] if k != 'neck' else prm['torso'] * 0.5
            w = yaw_warp(im, piv[0], R, kk, prm['squeeze'], far_shade=0.08 if k != 'neck' else 0)
            w2, piv2 = _crop(w, piv, 2)
            V['parts'][k] = entry(w2, piv2, '%s_%s.png' % (k, view))
        for k, e in shared.items():
            part, _, shp = k.partition(':')
            if shp:
                V['parts'].setdefault(part, {'variants': {}})['variants'][shp] = e
            else:
                V['parts'][part] = dict(e)
        for side in 'LR':
            im, piv = P['foot_%s@%s' % (side, view)]
            if side == 'R':
                im = _darken(im, FAR_SHADE)
            V['parts']['foot_' + side] = entry(im, piv, 'foot_%s_%s.png' % (side, view))
        # where every pivot sits in this view (units), then offsets from the parent pivot in px
        kt = prm['torso']
        Rt = b.W * 1.02
        pos = {}

        def place(n):
            if n in pos:
                return pos[n]
            par, (x, y) = J[n]
            base = n.rsplit('_', 1)[0]
            if base in ('upper_arm', 'thigh'):
                if prm['lat'] is None:
                    x = 0.5 + Rt * prm['squeeze'] * yaw_f((x - 0.5) / Rt, kt)
                else:
                    x = 0.5 + (x - 0.5) * prm['lat'] + (0.015 if base == 'upper_arm' else 0.0)
            elif base in ('lower_arm', 'hand', 'shin', 'foot'):
                x = place(par)[0]
            elif n == 'tail':
                x = 0.5 - (0.5 + kt) * b.W * prm['squeeze']
            elif n == 'wings':
                x = 0.5 - kt * b.W * 1.2 * prm['squeeze']
            pos[n] = (x, y)
            return pos[n]
        for n in J:
            place(n)
        for n, (par, _xy) in J.items():
            if n not in V['parts']:
                continue
            e = V['parts'][n]
            e['parent'] = par
            e['z'] = BODY_Z.index(n)
            if par:
                e['offset'] = [round((pos[n][0] - pos[par][0]) * OUT * ks, 1), round((pos[n][1] - pos[par][1]) * OUT * ks, 1)]
            if n.endswith('_R') or n.endswith('_L'):
                e['side'] = n[-1]
        fx, fy = J['foot_L'][1]
        sp = b.sole_points(fx, fy, view)
        V['soles'] = [[round((x - fx) * OUT * ks, 1), round((y - fy) * OUT * ks, 1)] for x, y in sp]
        V['waist_dx'] = round(b.W * 0.86 * prm['squeeze'] * OUT * ks, 1)
        V['ground'] = round((sp[0][1] - b.waist) * OUT * ks, 1)  # root pivot to the floor in the rest pose, px
        V['height'] = round((sp[0][1] - b.c.G.top + 0.04) * OUT * ks, 1)
        rig['views'][view] = V
    rig['anchors'] = {'mouth': [0, round((b.c.mouth_y - b.head_piv[1]) * OUT * ks, 1)],
                      'eyes_y': round((b.c.eye_y - b.head_piv[1]) * OUT * ks, 1),
                      'head_top': round((b.c.G.top - b.head_piv[1]) * OUT * ks, 1)}
    rig['dims'] = {n: round(getattr(b, n) * OUT * ks, 1) for n in ('W', 'Lua', 'Lla', 'Lth', 'Lsh', 'arm_w', 'leg_w')}
    rig['kind'] = b.s['kind'] if b.s['kind'] != 'animal' else 'animal:' + b.kit
    rig['has'] = {'tail': b.tail, 'wings': 'wings' in J, 'mic': 'mic' in b.c.acc_names()}
    with open(os.path.join(d, 'rig.json'), 'w') as f:
        json.dump(rig, f, ensure_ascii=False, indent=1)
    return rig


def build_props(root):
    """Felt props used by poses: phone and mic (held, pivot = grip), laptop (pivot = middle of the base's underside),
    stool (pivot = middle of the seat top). Written to root/_props/."""
    import json
    import os
    d = os.path.join(root, '_props')
    os.makedirs(d, exist_ok=True)
    meta = {}

    def phone(P):
        P.blob([(0.47, 0.44), (0.53, 0.44), (0.53, 0.56), (0.47, 0.56)], '#2f2d33', n=3)

    def phone_screen(P):
        P.blob([(0.476, 0.448), (0.524, 0.448), (0.524, 0.548), (0.476, 0.548)], '#7fa9b8', n=3)
        P.circle(0.5, 0.553, 0.003, '#8a888c')

    def mic(P):
        P.line([(0.5, 0.43), (0.5, 0.55)], '#2f2d31', 0.022)
        P.blob([(0.483, 0.47), (0.517, 0.47), (0.519, 0.505), (0.481, 0.505)], col('tomato'), n=4)
        P.circle(0.5, 0.425, 0.033, '#4a484c')

    def mic_grille(P):
        with P.clip(shape_mask(lambda Q: Q.circle(0.5, 0.425, 0.033, 'white'))):
            for k in range(-3, 4):
                P.line([(0.46, 0.425 + k * 0.01), (0.54, 0.425 + k * 0.01)], '#2a282c', 0.003)
        P.circle(0.49, 0.41, 0.008, '#8a888c')

    def laptop(P):
        P.blob([(0.39, 0.5), (0.61, 0.5), (0.6, 0.515), (0.4, 0.515)], '#9aa0a6', n=2)  # base, seen edge-on
        P.poly([(0.44, 0.505), (0.6, 0.505), (0.585, 0.37), (0.43, 0.37)], '#b8bec2')    # lid, its back to us

    def laptop_logo(P):
        P.circle(0.512, 0.435, 0.012, '#d8dcdf')

    def stool(P):
        wood = col('ochre')
        for x0, x1 in ((0.44, 0.42), (0.56, 0.58)):
            P.line([(x0, 0.52), (x1, 0.66)], shade(wood, 0.82), 0.022)
        P.line([(0.43, 0.6), (0.57, 0.6)], shade(wood, 0.75), 0.014)
        P.blob([(0.38, 0.5), (0.62, 0.5), (0.62, 0.53), (0.38, 0.53)], wood, n=3)

    for name, layers, piv, extra in (
            ('phone', [(phone, 0.8), (phone_screen, 0.3)], (0.5, 0.5), {'grip': 0.7, 'angle': 0}),
            ('mic', [(mic, 0.8), (mic_grille, 0.3)], (0.5, 0.5), {'grip': 0.75, 'angle': 0}),
            ('laptop', [(laptop, 0.9), (laptop_logo, 0.3)], (0.5, 0.515), {}),
            ('stool', [(stool, 1.0)], (0.5, 0.5), {})):
        _ORG[0] = _ORG[1] = 0.0
        im, pv = make_part(layers, piv)
        im.save(os.path.join(d, name + '.png'), optimize=True)
        meta[name] = dict(file=name + '.png', pivot=[round(pv[0], 1), round(pv[1], 1)], hull=hull_points(im), **extra)
    with open(os.path.join(d, 'props.json'), 'w') as f:
        json.dump(meta, f, indent=1)
    return meta
