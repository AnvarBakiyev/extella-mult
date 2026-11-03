"""Drawing primitives on a normalized canvas.

Coordinates: x in [0,1] of width, y in [0,1] of height; sizes in units of height.
The canvas is a PIL RGBA image at internal resolution (W, H).
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import gaussian_filter

_noise_cache = {}


def fbm(w, h, seed, octaves=(4, 12, 36), weights=(1.0, 0.5, 0.25)):
    """Cached cloudy noise in [0,1], computed at 1/4 size and upscaled."""
    key = (w, h, seed, octaves, weights)
    if key in _noise_cache:
        return _noise_cache[key]
    sw, sh = max(8, w // 4), max(8, h // 4)
    rng = np.random.default_rng(seed)
    acc = np.zeros((sh, sw), np.float32)
    for sig, wt in zip(octaves, weights):
        acc += wt * gaussian_filter(rng.random((sh, sw), dtype=np.float32), sig / 4)
    acc -= acc.min()
    acc /= max(acc.max(), 1e-6)
    img = Image.fromarray((acc * 255).astype(np.uint8)).resize((w, h), Image.BILINEAR)
    out = np.asarray(img, np.float32) / 255
    _noise_cache[key] = out
    return out


def rgb(c):
    """'#rrggbb' or (r,g,b) -> tuple."""
    if isinstance(c, str):
        c = c.lstrip('#')
        return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))
    return tuple(int(v) for v in c)


def mix(a, b, t):
    a, b = rgb(a), rgb(b)
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def ease(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


class Ctx:
    """A frame canvas with normalized-coordinate helpers."""

    def __init__(self, W, H):
        self.W, self.H = W, H
        self.img = Image.new('RGBA', (W, H), (0, 0, 0, 255))
        self.d = ImageDraw.Draw(self.img)

    # ---- coordinate helpers
    @property
    def ar(self):
        return self.H / self.W

    def local(self, x, y, s, flip=1):
        return Local(self, x, y, s, flip)

    def P(self, x, y):
        return (x * self.W, y * self.H)

    def S(self, s):
        return s * self.H

    def pts(self, points):
        return [self.P(x, y) for x, y in points]

    # ---- opaque primitives (fast, PIL)
    def circle(self, x, y, r, color, outline=None, width=0):
        cx, cy, rr = x * self.W, y * self.H, r * self.H
        self.d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=rgb(color),
                       outline=rgb(outline) if outline else None, width=int(width * self.H))

    def ellipse(self, x, y, rx, ry, color, angle=0.0):
        if abs(angle) < 1e-6:
            cx, cy = x * self.W, y * self.H
            self.d.ellipse([cx - rx * self.H, cy - ry * self.H, cx + rx * self.H, cy + ry * self.H], fill=rgb(color))
        else:
            n = 40
            ps = []
            for i in range(n):
                a = 2 * math.pi * i / n
                ex, ey = rx * math.cos(a), ry * math.sin(a)
                px = ex * math.cos(angle) - ey * math.sin(angle)
                py = ex * math.sin(angle) + ey * math.cos(angle)
                ps.append((x * self.W + px * self.H, y * self.H + py * self.H))
            self.d.polygon(ps, fill=rgb(color))

    def poly(self, points, color, outline=None, width=0):
        self.d.polygon(self.pts(points), fill=rgb(color) if color else None,
                       outline=rgb(outline) if outline else None, width=max(1, int(width * self.H)) if outline else 0)

    def rect(self, x0, y0, x1, y1, color):
        x0, x1 = sorted((x0 * self.W, x1 * self.W))
        y0, y1 = sorted((y0 * self.H, y1 * self.H))
        self.d.rectangle([x0, y0, x1, y1], fill=rgb(color))

    def line(self, points, color, width):
        w = max(1, int(round(width * self.H)))
        self.d.line(self.pts(points), fill=rgb(color), width=w, joint='curve')
        # round caps
        for (x, y) in (points[0], points[-1]):
            self.circle(x, y, width / 2, color)

    def curve(self, ctrl, color, width, n=24):
        """Quadratic/cubic bezier polyline from control points."""
        self.line(bezier(ctrl, n), color, width)

    # ---- soft primitives (numpy layers)
    def layer(self, alpha, color):
        """Composite a flat color with a float alpha mask (H,W) in [0,1]."""
        a = np.clip(alpha, 0, 1)
        if a.max() <= 0:
            return
        col = np.zeros((self.H, self.W, 4), np.uint8)
        col[..., :3] = rgb(color)
        col[..., 3] = (a * 255).astype(np.uint8)
        self.img.alpha_composite(Image.fromarray(col, 'RGBA'))

    def layer_rgb(self, rgb_arr, alpha):
        col = np.zeros((self.H, self.W, 4), np.uint8)
        col[..., :3] = np.clip(rgb_arr, 0, 255).astype(np.uint8)
        col[..., 3] = (np.clip(alpha, 0, 1) * 255).astype(np.uint8)
        self.img.alpha_composite(Image.fromarray(col, 'RGBA'))

    def glow(self, x, y, r, color, strength=1.0, power=2.0):
        """Radial glow centred at (x,y) with radius r (height units)."""
        yy, xx = self.grid()
        d = np.hypot(xx - x * self.W, yy - y * self.H) / (r * self.H)
        a = np.clip(1 - d, 0, 1) ** power * strength
        self.layer(a, color)

    def grid(self):
        return np.mgrid[0:self.H, 0:self.W].astype(np.float32)

    def gradient(self, stops, alpha=1.0, horizontal=False):
        """Vertical (or horizontal) gradient over whole canvas. stops: [(pos, color), ...]"""
        n = self.W if horizontal else self.H
        t = np.linspace(0, 1, n, dtype=np.float32)
        arr = np.zeros((n, 3), np.float32)
        cols = [(p, np.array(rgb(c), np.float32)) for p, c in stops]
        for ch in range(3):
            arr[:, ch] = np.interp(t, [p for p, _ in cols], [c[ch] for _, c in cols])
        if horizontal:
            full = np.broadcast_to(arr[None, :, :], (self.H, self.W, 3))
        else:
            full = np.broadcast_to(arr[:, None, :], (self.H, self.W, 3))
        self.layer_rgb(full, np.full((self.H, self.W), alpha, np.float32))

    def blur(self, radius):
        self.img = self.img.filter(ImageFilter.GaussianBlur(radius * self.H))
        self.d = ImageDraw.Draw(self.img)

    def tint(self, color, amount):
        self.layer(np.full((self.H, self.W), amount, np.float32), color)

    def vignette(self, strength=0.5):
        yy, xx = self.grid()
        d = np.hypot((xx / self.W - 0.5) * 1.3, yy / self.H - 0.5)
        self.layer(np.clip(d - 0.35, 0, 1) * strength, '#000000')

    def mask_from(self, fn):
        """Draw with fn(ImageDraw) on an L image, return float mask."""
        m = Image.new('L', (self.W, self.H), 0)
        fn(ImageDraw.Draw(m), self)
        return np.asarray(m, np.float32) / 255

    def soft_shape(self, fn, color, blur, alpha=1.0):
        m = self.mask_from(fn)
        if blur > 0:
            m = gaussian_filter(m, blur * self.H)
        self.layer(m * alpha, color)


class Local:
    """Uniform-unit frame: (u,v) -> canvas (x + u*s*H/W*flip, y + v*s); sizes scale by s. Lets props be drawn once, placed anywhere."""

    def __init__(self, ctx, x, y, s, flip=1):
        self.c, self.x, self.y, self.s, self.f = ctx, x, y, s, flip

    def pt(self, u, v):
        return (self.x + u * self.s * self.c.ar * self.f, self.y + v * self.s)

    def circle(self, u, v, r, color):
        self.c.circle(*self.pt(u, v), r * self.s, color)

    def ellipse(self, u, v, ru, rv, color, angle=0.0):
        self.c.ellipse(*self.pt(u, v), ru * self.s, rv * self.s, color, angle * self.f)

    def poly(self, points, color, outline=None, width=0):
        self.c.poly([self.pt(u, v) for u, v in points], color, outline, width * self.s)

    def line(self, points, color, width):
        self.c.line([self.pt(u, v) for u, v in points], color, width * self.s)

    def curve(self, ctrl, color, width, n=24):
        self.c.curve([self.pt(u, v) for u, v in ctrl], color, width * self.s, n)

    def glow(self, u, v, r, color, strength=1.0, power=2.0):
        self.c.glow(*self.pt(u, v), r * self.s, color, strength, power)


def bezier(ctrl, n=24):
    """Evaluate a bezier curve of any order given control points [(x,y),...]."""
    out = []
    k = len(ctrl) - 1
    for i in range(n + 1):
        t = i / n
        x = y = 0.0
        for j, (px, py) in enumerate(ctrl):
            b = math.comb(k, j) * (1 - t) ** (k - j) * t ** j
            x += b * px
            y += b * py
        out.append((x, y))
    return out


def smooth_path(points, n_per=8):
    """Catmull-Rom spline through points."""
    if len(points) < 3:
        return points
    p = [points[0]] + list(points) + [points[-1]]
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for k in range(n_per):
            t = k / n_per
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    out.append(points[-1])
    return out
