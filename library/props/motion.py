"""Camera moves and transitions for a Pillow frame pipeline.

Conventions
- t is progress in [0, 1] over the move or transition (the caller maps frame numbers to t).
- Camera moves:  fn(frame_img, t, params=None) -> frame   (same size as the input, RGB)
- Transitions:   fn(img_a, img_b, t, params=None) -> frame (a at t=0, b at t=1)
- params is a dict; every key is optional. 'ease' picks a curve from EASES (name or function).
- Parallax takes a list of 3 RGBA layers (back, middle, front) instead of one frame.

Only Pillow + numpy (+ scipy for 1-D blur) are used.
"""
import math
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter
from scipy.ndimage import uniform_filter1d


# ------------------------------------------------------------------ easing
def linear(t):
    return t


def ease_in(t):
    return t * t * t


def ease_out(t):
    return 1 - (1 - t) ** 3


def ease_in_out(t):
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def ease_out_expo(t):
    return 1.0 if t >= 1 else 1 - 2 ** (-10 * t)


def ease_back(t, s=1.70158):
    """Overshoots past 1 and settles (out-back)."""
    t -= 1
    return t * t * ((s + 1) * t + s) + 1


def ease_in_back(t, s=1.70158):
    """Pulls back below 0 before going (in-back)."""
    return t * t * ((s + 1) * t - s)


def ease_elastic(t):
    """Springs past the target a few times (out-elastic)."""
    if t <= 0 or t >= 1:
        return float(t >= 1)
    return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi / 3)) + 1


def ease_bounce(t):
    """Drops and bounces on the target (out-bounce)."""
    n, d = 7.5625, 2.75
    if t < 1 / d:
        return n * t * t
    if t < 2 / d:
        t -= 1.5 / d
        return n * t * t + 0.75
    if t < 2.5 / d:
        t -= 2.25 / d
        return n * t * t + 0.9375
    t -= 2.625 / d
    return n * t * t + 0.984375


EASES = dict(linear=linear, in_=ease_in, out=ease_out, in_out=ease_in_out, expo=ease_out_expo, back=ease_back,
             in_back=ease_in_back, elastic=ease_elastic, bounce=ease_bounce)


def _ease(p, default='in_out'):
    e = (p or {}).get('ease', default)
    return EASES[e] if isinstance(e, str) else e


def _clamp(t):
    return max(0.0, min(1.0, t))


def lerp(a, b, t):
    return a + (b - a) * t


# ------------------------------------------------------------------ core view transform
def view(img, cx=0.5, cy=0.5, zoom=1.0, angle=0.0, dx=0.0, dy=0.0, fill=(0, 0, 0)):
    """Look at img through a virtual camera: centre (cx, cy) in 0..1, zoom > 1 goes closer, angle in degrees
    (camera roll), dx/dy shift the picture by a fraction of its size. Returns an RGB image of the same size."""
    img = img.convert('RGB')
    W, H = img.size
    a = math.radians(angle)
    ca, sa = math.cos(a) / zoom, math.sin(a) / zoom
    # output pixel (x, y) -> source pixel: rotate/scale around the output centre, then move to the camera centre
    ox, oy = W / 2, H / 2
    sx, sy = cx * W - dx * W, cy * H - dy * H
    coeffs = (ca, -sa, sx - ca * ox + sa * oy, sa, ca, sy - sa * ox - ca * oy)
    return img.transform((W, H), Image.AFFINE, coeffs, resample=Image.BICUBIC, fillcolor=fill)


def cover_zoom(angle, w, h):
    """The zoom that keeps a rotated frame free of empty corners."""
    a = abs(math.radians(angle))
    c, s = math.cos(a), math.sin(a)
    return max(c + (h / w) * s, c + (w / h) * s)


def _noise(t, seed, octaves=3):
    """Smooth 1-D noise in about -1..1 from summed sines with irrational frequencies."""
    v = 0.0
    for k in range(octaves):
        f = (1.7 + seed * 0.37) * (2.13 ** k)
        v += math.sin(t * f + seed * 12.9898 + k * 78.233) / (k + 1)
    return v / 1.83


def _hblur(img, radius):
    """Horizontal motion blur (box) of the given radius in pixels."""
    if radius < 1:
        return img
    a = np.asarray(img.convert('RGB'), np.float32)
    a = uniform_filter1d(a, size=int(radius) * 2 + 1, axis=1, mode='nearest')
    return Image.fromarray(a.astype(np.uint8), 'RGB')


# ------------------------------------------------------------------ camera moves
def push(frame, t, p=None):
    """Push in: zoom from 1 to params zoom (1.35) towards cx, cy."""
    p = p or {}
    e = _ease(p)(_clamp(t))
    z = lerp(1.0, p.get('zoom', 1.35), e)
    return view(frame, lerp(0.5, p.get('cx', 0.5), e), lerp(0.5, p.get('cy', 0.5), e), z)


def pull(frame, t, p=None):
    """Pull out: start at params zoom (1.35) on cx, cy and open to the full frame."""
    p = p or {}
    e = _ease(p)(_clamp(t))
    z = lerp(p.get('zoom', 1.35), 1.0, e)
    return view(frame, lerp(p.get('cx', 0.5), 0.5, e), lerp(p.get('cy', 0.5), 0.5, e), z)


def pan(frame, t, p=None):
    """Pan across the frame: the camera, zoomed by params zoom (1.3), travels from (x0, y0) to (x1, y1) in 0..1."""
    p = p or {}
    e = _ease(p)(_clamp(t))
    z = p.get('zoom', 1.3)
    m = 0.5 / z  # keep the view inside the picture
    x = lerp(p.get('x0', m), p.get('x1', 1 - m), e)
    y = lerp(p.get('y0', 0.5), p.get('y1', 0.5), e)
    return view(frame, min(max(x, m), 1 - m), min(max(y, m), 1 - m), z)


def parallax(layers, t, p=None):
    """Orbit-like parallax for 3 RGBA layers [back, middle, front]: the camera swings sideways (and a little in depth),
    nearer layers move more. params: swing (0.06 of the width), turns (0.5 = one swing), bg (RGB under the back)."""
    p = p or {}
    W, H = layers[0].size
    ang = 2 * math.pi * p.get('turns', 0.5) * _clamp(t)
    sw = p.get('swing', 0.06)
    out = Image.new('RGB', (W, H), p.get('bg', (0, 0, 0)))
    for k, (lay, depth) in enumerate(zip(layers, p.get('depths', (0.25, 0.6, 1.0)))):
        dx = -sw * depth * math.sin(ang)
        z = 1.0 + 0.12 * depth + 0.04 * depth * (1 - math.cos(ang))  # zoom so edges never show
        lay = lay.convert('RGBA')
        k = 1 / z
        coeffs = (k, 0, W / 2 - dx * W - k * W / 2, 0, k, H / 2 - k * H / 2)
        moved = lay.transform((W, H), Image.AFFINE, coeffs, resample=Image.BICUBIC, fillcolor=(0, 0, 0, 0))
        out.paste(moved, (0, 0), moved)
    return out


def whip_pan(img_a, img_b, t, p=None):
    """Whip pan from a to b: a fast slide with heavy horizontal motion blur peaking in the middle.
    params: direction (1 = camera turns right, picture moves left), blur (0.18 of the width at the peak)."""
    p = p or {}
    W, H = img_a.size
    d = p.get('direction', 1)
    e = ease_in_out(_clamp(t))
    strip = Image.new('RGB', (2 * W, H))
    strip.paste(img_a.convert('RGB'), (0, 0) if d > 0 else (W, 0))
    strip.paste(img_b.convert('RGB'), (W, 0) if d > 0 else (0, 0))
    off = int(round(e * W)) if d > 0 else int(round((1 - e) * W))
    frame = strip.crop((off, 0, off + W, H))
    speed = math.sin(math.pi * _clamp(t)) ** 2
    return _hblur(frame, speed * p.get('blur', 0.18) * W)


def crash_zoom(frame, t, p=None):
    """Crash zoom: a violent zoom into (cx, cy) that lands in the first third, with a zoom blur while moving.
    params: zoom (2.2), cx, cy, blur (6 samples)."""
    p = p or {}
    t = _clamp(t)
    e = ease_out_expo(min(1.0, t * 3))
    z1 = p.get('zoom', 2.2)
    cx, cy = p.get('cx', 0.5), p.get('cy', 0.5)
    z = lerp(1.0, z1, e)
    speed = (1 - e)
    n = int(p.get('blur', 6) * speed) + 1
    if n <= 1:
        return view(frame, lerp(0.5, cx, e), lerp(0.5, cy, e), z)
    acc = None
    for k in range(n):
        zk = z * (1 - 0.08 * speed * k / n)
        f = np.asarray(view(frame, lerp(0.5, cx, e), lerp(0.5, cy, e), zk), np.float32)
        acc = f if acc is None else acc + f
    return Image.fromarray((acc / n).astype(np.uint8), 'RGB')


def handheld(frame, t, p=None):
    """Handheld wander: slow organic drift in x, y and roll. params: amount (1.0), time (seconds, for the noise
    phase; defaults to t * 4), seed."""
    p = p or {}
    k = p.get('amount', 1.0)
    s = p.get('seed', 3)
    tt = p.get('time', t * 4)
    dx = 0.012 * k * _noise(tt, s)
    dy = 0.010 * k * _noise(tt, s + 1)
    ang = 0.7 * k * _noise(tt * 0.8, s + 2)
    z = 1.04 + 0.01 * k
    return view(frame, 0.5, 0.5, z * cover_zoom(ang, *frame.size), ang, dx, dy)


def dutch_tilt(frame, t, p=None):
    """Dutch tilt: roll the camera to params angle (12 degrees) with a cover zoom so no corner is empty."""
    p = p or {}
    e = _ease(p)(_clamp(t))
    ang = p.get('angle', 12) * e
    return view(frame, 0.5, 0.5, cover_zoom(ang, *frame.size) * lerp(1, p.get('zoom', 1.05), e), ang)


def rack_focus(frame, t, p=None):
    """Fake rack focus: focus moves from the background to the foreground (or back with reverse=1).
    params: mask (L image, white = foreground; default: lower-centre ellipse), blur (8 px at full defocus)."""
    p = p or {}
    W, H = frame.size
    e = _ease(p)(_clamp(t))
    if p.get('reverse'):
        e = 1 - e
    mask = p.get('mask')
    if mask is None:
        mask = Image.new('L', (W, H), 0)
        ImageDraw.Draw(mask).ellipse([W * 0.25, H * 0.35, W * 0.75, H * 1.1], fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(H * 0.05))
    b = p.get('blur', 8)
    frame = frame.convert('RGB')
    fg_blur = frame.filter(ImageFilter.GaussianBlur(b * (1 - e))) if b * (1 - e) > 0.3 else frame
    bg_blur = frame.filter(ImageFilter.GaussianBlur(b * e)) if b * e > 0.3 else frame
    return Image.composite(fg_blur, bg_blur, mask.resize((W, H)))


def shake(frame, t, p=None):
    """Shake with decay: a hit at t=0 that dies away. params: amount (0.03 of the frame), decay (5), freq (40),
    roll (2 degrees)."""
    p = p or {}
    t = _clamp(t)
    k = p.get('amount', 0.03) * math.exp(-p.get('decay', 5) * t)
    f = p.get('freq', 40)
    dx = k * math.sin(t * f * 1.0 + 1.3)
    dy = k * math.sin(t * f * 1.3 + 0.4)
    ang = p.get('roll', 2) * (k / max(p.get('amount', 0.03), 1e-6)) * math.sin(t * f * 0.9)
    return view(frame, 0.5, 0.5, cover_zoom(ang, *frame.size) * (1 + 2.2 * k), ang, dx, dy)


def slowmo_time(t, start=0.4, length=0.2, factor=0.2):
    """Time remap for a slow-motion hold: playback speed drops to factor between start and start+length (both in
    output time 0..1) and recovers smoothly. Returns source time 0..1; feed it to your scene renderer."""
    # speed profile v(u) = 1 - (1 - factor) * bump(u); integrate numerically and normalise
    n = 400
    us = np.linspace(0, 1, n + 1)
    bump = np.clip(1 - np.abs((us - (start + length / 2)) / (length / 2 + 0.05)), 0, 1)
    bump = bump * bump * (3 - 2 * bump)
    v = 1 - (1 - factor) * bump
    cum = np.concatenate([[0], np.cumsum((v[1:] + v[:-1]) / 2)])
    cum /= cum[-1]
    return float(np.interp(_clamp(t), us, cum))


def slowmo_hold(frame_at, t, p=None):
    """Slow-motion hold: frame_at(src_t) renders the scene at source time; output time t is remapped by slowmo_time
    and, while slow, the camera creeps in and the frame gets a soft vignette. params: start, length, factor, zoom."""
    p = p or {}
    st = slowmo_time(t, p.get('start', 0.4), p.get('length', 0.2), p.get('factor', 0.2))
    img = frame_at(st).convert('RGB')
    mid = p.get('start', 0.4) + p.get('length', 0.2) / 2
    k = max(0.0, 1 - abs(_clamp(t) - mid) / (p.get('length', 0.2) / 2 + 0.08))
    k = k * k * (3 - 2 * k)
    img = view(img, 0.5, 0.5, 1 + p.get('zoom', 0.06) * k)
    return vignette(img, 0.45 * k) if k > 0.01 else img


def vignette(frame, strength=0.4):
    """Darken the corners (helper used by slowmo_hold, also handy on its own)."""
    W, H = frame.size
    y, x = np.ogrid[0:H, 0:W]
    r = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
    m = 1 - strength * np.clip((r - 0.55) / 0.8, 0, 1) ** 1.5
    a = np.asarray(frame.convert('RGB'), np.float32) * m[..., None]
    return Image.fromarray(a.astype(np.uint8), 'RGB')


# ------------------------------------------------------------------ transitions
def iris(img_a, img_b, t, p=None):
    """Iris: a circle closes on a to black (first half) and opens on b (second half). params: cx, cy, color,
    cx2/cy2 for where it opens on b."""
    p = p or {}
    t = _clamp(t)
    W, H = img_a.size
    R = math.hypot(W, H) / 2 * 1.05
    col = p.get('color', (0, 0, 0))
    if t < 0.5:
        img, r, cx, cy = img_a, R * (1 - ease_in(t * 2)), p.get('cx', 0.5), p.get('cy', 0.5)
    else:
        img, r, cx, cy = img_b, R * ease_out(t * 2 - 1), p.get('cx2', p.get('cx', 0.5)), p.get('cy2', p.get('cy', 0.5))
    m = Image.new('L', (W * 2, H * 2), 0)
    ImageDraw.Draw(m).ellipse([(cx * W - r) * 2, (cy * H - r) * 2, (cx * W + r) * 2, (cy * H + r) * 2], fill=255)
    m = m.resize((W, H), Image.BILINEAR)
    return Image.composite(img.convert('RGB'), Image.new('RGB', (W, H), col), m)


def iris_out(frame, t, p=None):
    """Iris out to black on one frame (closes as t goes 0 -> 1)."""
    return iris(frame, frame, _clamp(t) / 2, p)


def iris_in(frame, t, p=None):
    """Iris in from black on one frame (opens as t goes 0 -> 1)."""
    return iris(frame, frame, 0.5 + _clamp(t) / 2, p)


def wipe(img_a, img_b, t, p=None):
    """Wipe from a to b with a soft edge. params: direction 'left' (b comes in from the right edge moving left) or
    'right' (b comes in from the left), soft (0.03 of the width), ease."""
    p = p or {}
    W, H = img_a.size
    e = _ease(p, 'in_out')(_clamp(t))
    soft = max(1.0, p.get('soft', 0.03) * W)
    x = np.arange(W, dtype=np.float32)
    if p.get('direction', 'right') == 'right':
        edge = -soft + e * (W + 2 * soft)
        m = np.clip((edge - x) / soft + 0.5, 0, 1)
    else:
        edge = W + soft - e * (W + 2 * soft)
        m = np.clip((x - edge) / soft + 0.5, 0, 1)
    mask = Image.fromarray((np.broadcast_to(m, (H, W)) * 255).astype(np.uint8), 'L')
    return Image.composite(img_b.convert('RGB'), img_a.convert('RGB'), mask)


def wipe_left(img_a, img_b, t, p=None):
    return wipe(img_a, img_b, t, dict(p or {}, direction='left'))


def wipe_right(img_a, img_b, t, p=None):
    return wipe(img_a, img_b, t, dict(p or {}, direction='right'))


def cross_dissolve(img_a, img_b, t, p=None):
    """Cross-dissolve a into b."""
    return Image.blend(img_a.convert('RGB'), img_b.convert('RGB'), _ease(p, 'linear')(_clamp(t)))


def dip(img_a, img_b, t, p=None):
    """Dip to a colour: a fades to params color (black) by the middle, then b fades up."""
    p = p or {}
    t = _clamp(t)
    col = Image.new('RGB', img_a.size, p.get('color', (0, 0, 0)))
    if t < 0.5:
        return Image.blend(img_a.convert('RGB'), col, ease_in_out(t * 2))
    return Image.blend(col, img_b.convert('RGB'), ease_in_out(t * 2 - 1))


def dip_to_black(img_a, img_b, t, p=None):
    return dip(img_a, img_b, t, dict(p or {}, color=(0, 0, 0)))


def dip_to_white(img_a, img_b, t, p=None):
    return dip(img_a, img_b, t, dict(p or {}, color=(250, 248, 242)))


def page_turn(img_a, img_b, t, p=None):
    """Page-turn-like slide: a folds away towards the left edge like a page (narrows, darkens towards the fold, with
    a bright curl strip and a shadow cast on b)."""
    p = p or {}
    W, H = img_a.size
    e = _ease(p, 'in_out')(_clamp(t))
    out = img_b.convert('RGB').copy()
    w = int(round(W * math.cos(e * math.pi / 2)))  # projected width of the turning page
    if w > 1:
        page = img_a.convert('RGB').resize((w, H), Image.BILINEAR)
        g = np.linspace(1.0, 1.0 - 0.55 * e, w, dtype=np.float32)  # darker towards the fold (right edge)
        page = Image.fromarray((np.asarray(page, np.float32) * g[None, :, None]).astype(np.uint8), 'RGB')
        # shadow cast on b to the right of the page
        sw = int(W * 0.08 * math.sin(e * math.pi))
        if sw > 1:
            a = np.asarray(out, np.float32)
            x0, x1 = w, min(W, w + sw)
            fall = np.linspace(0.55, 1.0, x1 - x0, dtype=np.float32)
            a[:, x0:x1] *= fall[None, :, None]
            out = Image.fromarray(a.astype(np.uint8), 'RGB')
        out.paste(page, (0, 0))
        cw = max(2, int(W * 0.012 * math.sin(e * math.pi)))
        curl = Image.new('RGB', (cw, H), (245, 242, 235))
        out.paste(curl, (max(0, w - cw), 0))
    return out


def slide(img_a, img_b, t, p=None):
    """Plain slide (push transition): b pushes a out. params: direction 'left' | 'right' | 'up' | 'down', ease."""
    p = p or {}
    W, H = img_a.size
    e = _ease(p, 'in_out')(_clamp(t))
    d = p.get('direction', 'left')
    out = Image.new('RGB', (W, H))
    if d in ('left', 'right'):
        s = -1 if d == 'left' else 1
        o = int(round(e * W)) * s
        out.paste(img_a.convert('RGB'), (o, 0))
        out.paste(img_b.convert('RGB'), (o - s * W, 0))
    else:
        s = -1 if d == 'up' else 1
        o = int(round(e * H)) * s
        out.paste(img_a.convert('RGB'), (0, o))
        out.paste(img_b.convert('RGB'), (0, o - s * H))
    return out


CAMERA = dict(push=push, pull=pull, pan=pan, crash_zoom=crash_zoom, handheld=handheld, dutch_tilt=dutch_tilt,
              rack_focus=rack_focus, shake=shake, iris_in=iris_in, iris_out=iris_out)
TRANSITIONS = dict(whip_pan=whip_pan, iris=iris, wipe_left=wipe_left, wipe_right=wipe_right, cross_dissolve=cross_dissolve,
                   dip_to_black=dip_to_black, dip_to_white=dip_to_white, page_turn=page_turn, slide=slide)
