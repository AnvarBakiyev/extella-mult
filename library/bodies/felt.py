"""look=felt (v3, needle-felted wool puppets): every element is drawn on its own layer and turned into a piece of
felted wool.

Per piece (felt_composite):
  1. rounder silhouette: sharp corners are smoothed (blur + re-threshold of the alpha), thin lines are kept; the
     rounding radius is a bit larger than in v2 so edges read thicker
  2. fibrous edge: the piece is domain-warped by a fibrous noise field, so its outline and its inner colour borders
     break up into wool instead of a clean cut; a fuzzy halo of the piece colour sits around it
  3. stray fibres: many thin curved hairs start just inside the outline and stick out (denser and longer than v2:
     up to ~22 px on hair and fur); a few fibres of what lies beneath cross over the new piece's border
  4. wool surface: a cached tile of layered micro-fibres, oriented fibre fields that follow the form (tangent to the
     outline), a low-frequency heather, uneven density and small needle pits
  5. volume: a pillow height (or a ball for noses, buttons and eyes) plus a bump map (pits, density noise, knit
     stitches, fleece pills) gives the normals; key light from the top-left, wrap-around occlusion at the rim,
     warm subsurface shadows, a broad specular-free sheen on top-lit areas; under the piece a contact crease, a soft
     cast shadow and a wide ambient-occlusion shadow
  6. garment weaves: 'knit' (V-stitch columns with ribs), 'fleece' (soft, pilled), 'suit' (dense pressed felt)

Everything is deterministic: the random streams are seeded from a per-frame piece counter (begin(seed)), the number of
random draws depends only on the piece itself (never on what lies beneath), so the same piece drawn in two frames
comes out identical and the talking overlays stay pixel-exact.
"""
import math

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import distance_transform_edt, gaussian_filter, label, map_coordinates
from scipy.ndimage import maximum as nd_maximum

# kind -> parameters
#   dens: stray hairs per 100 px of outline, maxlen: their max length (px at 1024), tex: micro-fibre texture strength,
#   warp: outline warp px, surf: bump strength (pits, uneven density), dir: oriented-fibre strength,
#   prof: height profile ('pillow' | 'dome'), weave: None | 'knit' | 'fleece' | 'suit', cross: fibres of the layer
#   beneath that cross over this piece's border (per 100 px), halo: fuzzy halo strength
_F = dict(dens=44, maxlen=11, tex=1.0, warp=1.25, surf=1.0, dir=0.055, prof='pillow', weave=None, cross=7, halo=0.55)
KINDS = {
    'felt': dict(_F),
    'suit': dict(_F, dens=34, maxlen=8, tex=0.85, warp=1.0, surf=0.5, dir=0.05, weave='suit', cross=5),
    'knit': dict(_F, dens=52, maxlen=12, tex=0.8, warp=1.4, surf=0.7, dir=0.04, weave='knit', cross=8, halo=0.6),
    'fleece': dict(_F, dens=70, maxlen=8, tex=0.55, warp=1.6, surf=0.8, dir=0.03, weave='fleece', cross=9, halo=0.75),
    'skin': dict(_F, dens=28, maxlen=8, tex=0.8, warp=1.0, surf=0.55, dir=0.04, cross=5, halo=0.5),
    'hair': dict(_F, dens=130, maxlen=19, tex=1.4, warp=2.2, surf=0.9, dir=0.09, cross=10, halo=0.7),
    'fur': dict(_F, dens=110, maxlen=17, tex=1.2, warp=2.0, surf=0.9, dir=0.05, cross=10, halo=0.7),
    'brow': dict(_F, dens=90, maxlen=8, tex=1.1, warp=1.6, surf=0.5, dir=0.0, cross=0, halo=0.5),
    'ball': dict(_F, dens=20, maxlen=6, tex=0.9, warp=0.8, surf=0.6, dir=0.015, prof='dome', cross=0, halo=0.45),
    'eye': dict(_F, dens=3, maxlen=3, tex=0.3, warp=0.45, surf=0.25, dir=0.0, prof='dome', cross=0, halo=0.0),
    'bead': dict(_F, dens=0, maxlen=0, tex=0.2, warp=0.3, surf=0.1, dir=0.0, prof='dome', cross=0, halo=0.0),
    'fine': dict(_F, dens=6, maxlen=4, tex=0.55, warp=0.7, surf=0.4, dir=0.0, cross=0, halo=0.35),
    'hard': dict(_F, dens=0, maxlen=0, tex=0.25, warp=0.0, surf=0.0, dir=0.0, cross=0, halo=0.0),
    'glint': None,  # glossy highlight on an eye bead: no wool, no shadow
}

_state = {'n': 0, 'seed': 0}
_cache = {}
TN = 1024  # tile size of every cached field


def begin(seed):
    """Start a new deterministic piece sequence (call before drawing a bare body or a frame's face pieces)."""
    _state['n'] = 0
    _state['seed'] = seed


def _next_rng():
    _state['n'] += 1
    return np.random.default_rng((_state['seed'] * 1000 + _state['n']) * 7919 + 13)


def _norm(f):
    f = f - f.mean()
    return (f / (f.std() + 1e-6)).astype(np.float32)


# ---------------------------------------------------------------- cached fields (one per process)
def _felt_tile(N=TN):
    """RGB multiplicative wool texture around 1.0: layered short random fibres, each with its own tint."""
    if ('tile', N) in _cache:
        return _cache[('tile', N)]
    rng = np.random.default_rng(11)
    S = 2 * N
    im = Image.new('RGB', (S, S), (128, 128, 128))
    d = ImageDraw.Draw(im, 'RGBA')
    for layer, (count, lmin, lmax, amin, amax, w, vamp) in enumerate(((150000, 6, 22, 22, 50, 1, 50),
                                                                      (40000, 10, 34, 18, 40, 2, 34))):
        x0 = rng.uniform(0, S, count)
        y0 = rng.uniform(0, S, count)
        ang = rng.uniform(0, math.pi, count)
        ln = rng.uniform(lmin, lmax, count)
        bend = rng.normal(0, 0.5, count)
        val = rng.normal(0, 1, count)
        tint = rng.normal(0, 1, (count, 3))
        al = rng.uniform(amin, amax, count)
        for i in range(count):
            v = 128 + vamp * val[i]
            c = tuple(int(np.clip(v + 10 * tint[i, k], 0, 255)) for k in range(3)) + (int(al[i]),)
            a, L_, b = ang[i], ln[i], bend[i]
            pts = []
            for t in (-0.5, -0.17, 0.17, 0.5):
                aa = a + b * t
                pts.append((x0[i] + math.cos(aa) * L_ * t, y0[i] + math.sin(aa) * L_ * t))
            d.line(pts, fill=c, width=w)
    arr = np.asarray(im.resize((N, N), Image.BOX), np.float32) / 128.0 - 1
    # clumps: felted wool is denser / lighter in soft patches
    cl = gaussian_filter(rng.standard_normal((N, N)).astype(np.float32), 2.5, mode='wrap')
    cl /= cl.std() + 1e-6
    arr = arr / (arr.std() + 1e-6) * 0.075 + 0.025 * cl[..., None]
    arr = 1 + np.tanh(arr * 6) / 6
    # heather: two low-frequency fields mix in a warmer-lighter and a cooler-darker tone
    h1 = gaussian_filter(rng.standard_normal((N, N)).astype(np.float32), 18, mode='wrap')
    h2 = gaussian_filter(rng.standard_normal((N, N)).astype(np.float32), 6, mode='wrap')
    h1 /= h1.std() + 1e-6
    h2 /= h2.std() + 1e-6
    _cache[('tile', N)] = (arr.astype(np.float32), h1, h2)
    return _cache[('tile', N)]


def _warp_field(N=TN):
    """Fibrous displacement (dx, dy), unit std: anisotropic noise at several random orientations."""
    if ('warp', N) in _cache:
        return _cache[('warp', N)]
    rng = np.random.default_rng(23)
    out = []
    for _ in range(2):
        f = np.zeros((N, N), np.float32)
        for sig in ((0.7, 3.5), (3.5, 0.7), (1.2, 1.2)):
            f += gaussian_filter(rng.standard_normal((N, N)).astype(np.float32), sig, mode='wrap')
        f += 0.6 * gaussian_filter(rng.standard_normal((N, N)).astype(np.float32), 5, mode='wrap') * 3
        out.append(f / (f.std() + 1e-6))
    _cache[('warp', N)] = out
    return out


def _oriented_fibres(N=TN):
    """Four periodic fibre fields (0, 45, 90, 135 degrees): white noise filtered in the Fourier domain with an
    anisotropic gaussian (long along the fibre, thin across), then sharpened so single fibres stand out."""
    if 'orient' in _cache:
        return _cache['orient']
    rng = np.random.default_rng(31)
    fy = np.fft.fftfreq(N)[:, None].astype(np.float32)
    fx = np.fft.fftfreq(N)[None, :].astype(np.float32)
    out = []
    for k in range(4):
        th = k * math.pi / 4
        fa = fx * math.cos(th) + fy * math.sin(th)   # frequency along the fibre
        fc = -fx * math.sin(th) + fy * math.cos(th)  # across
        G = np.exp(-2 * math.pi ** 2 * (7.0 ** 2 * fa ** 2 + 0.75 ** 2 * fc ** 2))
        n = rng.standard_normal((N, N)).astype(np.float32)
        f = np.real(np.fft.ifft2(np.fft.fft2(n) * G)).astype(np.float32)
        f = _norm(f)
        f = np.sign(f) * np.abs(f) ** 1.4  # crisper fibres
        out.append(_norm(f))
    _cache['orient'] = out
    return out


def _bump_fields(N=TN):
    """Height detail in px (at 1024) with its gradient, periodic:
       base   needle pits (small sharp dimples) + uneven density (low and mid frequency lumps)
       knit   V-stitch columns (knit-sweater ribs), slightly jittered, plus per-stitch tone
       fleece soft pills
    Returns dict name -> (height, gy, gx, albedo multiplier)."""
    if 'bump' in _cache:
        return _cache['bump']
    rng = np.random.default_rng(47)
    out = {}
    # pits: sparse impulses -> small gaussian dips
    imp = (rng.random((N, N)) < 0.011).astype(np.float32) * rng.uniform(0.5, 1.0, (N, N)).astype(np.float32)
    pits = gaussian_filter(imp, 1.5, mode='wrap')
    pits /= pits.max() + 1e-6
    d1 = _norm(gaussian_filter(rng.standard_normal((N, N)).astype(np.float32), 26, mode='wrap'))
    d2 = _norm(gaussian_filter(rng.standard_normal((N, N)).astype(np.float32), 8, mode='wrap'))
    hb = -0.9 * pits + 1.5 * d1 + 0.45 * d2
    alb = 1 - 0.06 * np.clip(pits * 1.6, 0, 1) + 0.035 * d2 + 0.03 * d1
    gy, gx = np.gradient(hb)
    out['base'] = (hb, gy, gx, alb.astype(np.float32))

    # knit: ncol columns of V stitches (2 legs per column), nrow rows; both divide the tile exactly
    ncol, nrow = 80, 124
    wx, wy = _warp_field()
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    xj = xx + 0.7 * wx
    yj = yy + 0.7 * wy
    u = xj * ncol / N
    fxp = u - np.floor(u)                       # 0..1 across a column
    lx = np.abs(fxp - 0.5) * 2                  # 0 at the V's centre seam, 1 at the column edge
    v = yj * nrow / N - 0.55 * lx               # legs rise outwards: a V pointing down
    fyp = v - np.floor(v)
    leg = np.maximum(np.sin(np.pi * np.clip(lx, 0, 1)), 0) ** 0.7  # each leg is a lump between seam and edge
    row = np.maximum(np.sin(np.pi * fyp), 0) ** 0.8
    hk = leg * row
    col_id = np.floor(u).astype(np.int64) % ncol
    row_id = np.floor(v).astype(np.int64) % nrow
    side = (fxp > 0.5).astype(np.int64)
    tone = np.random.default_rng(5).normal(0, 1, (ncol, nrow, 2)).astype(np.float32)[col_id, row_id, side]
    hk = 2.4 * hk
    alb_k = (0.80 + 0.20 * leg * row) * (1 + 0.045 * tone)
    gy, gx = np.gradient(hk)
    out['knit'] = (hk, gy, gx, alb_k.astype(np.float32))

    # fleece: soft pills and a velvety surface
    impf = (rng.random((N, N)) < 0.0035).astype(np.float32) * rng.uniform(0.6, 1.0, (N, N)).astype(np.float32)
    pills = gaussian_filter(impf, 2.0, mode='wrap')
    pills /= pills.max() + 1e-6
    hf = 2.2 * pills + 1.4 * d2
    alb_f = 1 + 0.07 * pills - 0.02 * d2
    gy, gx = np.gradient(hf)
    out['fleece'] = (hf, gy, gx, alb_f.astype(np.float32))

    # pressed suit felt: finer, flatter density variation
    d3 = _norm(gaussian_filter(rng.standard_normal((N, N)).astype(np.float32), 3.5, mode='wrap'))
    hs = 0.45 * d3
    gy, gx = np.gradient(hs)
    out['suit'] = (hs, gy, gx, (1 + 0.03 * d3).astype(np.float32))
    _cache['bump'] = out
    return out


def warm_up():
    _felt_tile()
    _warp_field()
    _oriented_fibres()
    _bump_fields()


def _tilecrop(arr, x0, y0, w, h, ox, oy):
    N = arr.shape[0]
    ys = (np.arange(y0, y0 + h) + oy) % N
    xs = (np.arange(x0, x0 + w) + ox) % N
    return arr[np.ix_(ys, xs)]


def _blur(a, sigma):
    """Gaussian blur done at reduced resolution for big sigmas (soft, so the loss is invisible)."""
    k = 4 if sigma >= 8 else 2
    h, w = a.shape
    if sigma < 3 or h < 4 * k or w < 4 * k:
        return gaussian_filter(a, sigma, mode='nearest')
    im = Image.fromarray(np.ascontiguousarray(a, np.float32), 'F')
    small = np.asarray(im.resize((max(1, w // k), max(1, h // k)), Image.BILINEAR), np.float32)
    small = gaussian_filter(small, sigma / k, mode='nearest')
    return np.asarray(Image.fromarray(small, 'F').resize((w, h), Image.BILINEAR), np.float32)


def _smoothstep(x, e0, e1):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------- fibres
def _edge_points(a, rng, density, s, cap):
    """Random points on the outline of a, with the outward normal. Draws depend only on a."""
    edge = (a > 0.25) & (a < 0.75)
    ys, xs = np.nonzero(edge)
    if len(ys) < 8:
        return None
    n = min(int(len(ys) / 1.6 * density / 100.0), cap)
    if n <= 0:
        return None
    pick = rng.integers(0, len(ys), n)
    ys, xs = ys[pick].astype(np.float32), xs[pick].astype(np.float32)
    hs = _blur(a, 2.5 * s)
    gy, gx = np.gradient(hs)
    nx, ny = -gx[ys.astype(int), xs.astype(int)], -gy[ys.astype(int), xs.astype(int)]  # outward normal
    nn = np.hypot(nx, ny) + 1e-6
    return xs, ys, nx / nn, ny / nn, n


def _stray_fibres(rgb, a, rng, density, maxlen, s):
    """Curved hairs along the outline, drawn 2x supersampled. Returns premultiplied (rgb*a, a) float arrays."""
    h, w = a.shape
    if density <= 0:
        return None
    ep = _edge_points(a, rng, density, s, 16000)
    if ep is None:
        return None
    xs, ys, nx, ny, n = ep
    base_ang = np.arctan2(ny, nx) + rng.normal(0, 0.7, n)
    ln = (2 + (maxlen - 2) * rng.random(n) ** 1.45) * s / 1.27
    bend = rng.normal(0, 0.9, n)
    # colour: sampled a few px inside the piece
    sx = np.clip((xs - nx * 3 * s).astype(int), 0, w - 1)
    sy = np.clip((ys - ny * 3 * s).astype(int), 0, h - 1)
    cc = rgb[sy, sx]
    lift = rng.normal(0.08, 0.15, n)[:, None]
    cc = np.clip(cc * (1 + lift) * (1 + 0.05 * rng.normal(0, 1, (n, 3))) + 0.035 * np.clip(lift, 0, 1), 0, 1)
    al = rng.uniform(0.35, 0.9, n)
    start_in = rng.uniform(0.5, 3.0, n) * s
    xs = xs - np.cos(base_ang) * start_in
    ys = ys - np.sin(base_ang) * start_in
    return _strokes(w, h, xs, ys, base_ang, ln, bend, cc, al)


def _cross_fibres(brgb, ba, a, rng, density, maxlen, s):
    """Fibres of the layer beneath that cross over the new piece's border (pointing inwards). The random draws
    depend only on the piece's alpha; the colour and the opacity come from what lies beneath, so a fibre simply
    vanishes where nothing is beneath."""
    h, w = a.shape
    ep = _edge_points(a, rng, density, s, 4000)
    if ep is None:
        return None
    xs, ys, nx, ny, n = ep
    ang = np.arctan2(-ny, -nx) + rng.normal(0, 0.6, n)  # inwards
    ln = (2.5 + (maxlen * 0.75 - 2.5) * rng.random(n) ** 1.3) * s / 1.27
    bend = rng.normal(0, 0.8, n)
    out_d = rng.uniform(2.0, 4.5, n) * s
    lift = rng.normal(0.05, 0.12, n)[:, None]
    al = rng.uniform(0.35, 0.8, n)
    sx = np.clip((xs + nx * out_d).astype(int), 0, w - 1)
    sy = np.clip((ys + ny * out_d).astype(int), 0, h - 1)
    under = ba[sy, sx]
    cc = brgb[sy, sx] / np.maximum(under[:, None], 1e-3)
    cc = np.clip(cc * (1 + lift), 0, 1)
    al = al * np.clip((under - 0.9) * 10, 0, 1)
    xs = xs + nx * out_d * 0.6
    ys = ys + ny * out_d * 0.6
    return _strokes(w, h, xs, ys, ang, ln, bend, cc, al)


def _strokes(w, h, xs, ys, ang, ln, bend, cc, al, centred=False):
    """Curved 3-segment strokes, 2x supersampled; returns premultiplied (rgb*a, a)."""
    K = 2
    im = Image.new('RGBA', (w * K, h * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(im, 'RGBA')
    ci = (np.clip(cc, 0, 1) * 255).astype(int)
    ai = (np.clip(al, 0, 1) * 255).astype(int)
    for i in range(len(xs)):
        if ai[i] <= 0:
            continue
        a0, L_, b = ang[i], ln[i], bend[i]
        px, py = xs[i], ys[i]
        if centred:
            px -= math.cos(a0) * L_ / 2
            py -= math.sin(a0) * L_ / 2
        pts = [(px * K, py * K)]
        for t in (0.33, 0.66, 1.0):
            aa = a0 + b * t
            px += math.cos(aa) * L_ / 3
            py += math.sin(aa) * L_ / 3
            pts.append((px * K, py * K))
        d.line(pts, fill=(ci[i, 0], ci[i, 1], ci[i, 2], ai[i]), width=1 if i % 3 else 2)
    f = np.asarray(im.convert('RGBa').reduce(K), np.float32) / 255.0
    return f[..., :3], f[..., 3]


def _inner_strands(rgb, a, rng, s, per_px):
    """Hair / fur: strands inside the piece that run along its outline (tangent to the blurred alpha), some lighter
    (catching the light), some darker."""
    h, w = a.shape
    ys, xs = np.nonzero(a > 0.9)
    n = min(int(len(ys) * per_px), 18000)
    if n < 10:
        return None
    pick = rng.integers(0, len(ys), n)
    ys, xs = ys[pick], xs[pick]
    hb = _blur(a, 10 * s)
    gy, gx = np.gradient(hb)
    ang = np.arctan2(gy[ys, xs], gx[ys, xs]) + math.pi / 2 + rng.normal(0, 0.35, n)
    ln = rng.uniform(10, 34, n) * s / 1.27
    bend = rng.normal(0, 0.5, n)
    cc = rgb[ys, xs]
    lift = np.where(rng.random(n) < 0.55, rng.uniform(0.12, 0.38, n), -rng.uniform(0.12, 0.35, n))[:, None]
    cc = cc * (1 + lift) + 0.04 * np.clip(lift, 0, 1)
    al = rng.uniform(0.2, 0.5, n)
    return _strokes(w, h, xs.astype(np.float32), ys.astype(np.float32), ang, ln, bend, cc, al, centred=True)


def _glint(base, layer):
    """A glossy highlight (eye beads): composited with a slight softening, no wool, no shadow."""
    box = layer.getbbox()
    if box is None:
        return base
    x0, y0 = max(0, box[0] - 4), max(0, box[1] - 4)
    x1, y1 = min(base.size[0], box[2] + 4), min(base.size[1], box[3] + 4)
    arr = np.asarray(layer.crop((x0, y0, x1, y1)).convert('RGBa'), np.float32) / 255.0
    arr = np.stack([gaussian_filter(arr[..., k], 0.6) for k in range(4)], -1)
    b = np.asarray(base.crop((x0, y0, x1, y1)).convert('RGBa'), np.float32) / 255.0
    a = arr[..., 3:4]
    b = b * (1 - a) + arr
    out = Image.fromarray((np.clip(b, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGBa').convert('RGBA')
    base.paste(out, (x0, y0))
    return base


# ---------------------------------------------------------------- the composite
def felt_composite(base, layer, depth=1.0, kind='felt'):
    """Composite one RGBA layer onto base (RGBA, same size) as a piece of felted wool. depth scales the volume and
    the shadow, kind (see KINDS) the fibres, the surface, the height profile and the garment weave."""
    if kind == 'glint':
        return _glint(base, layer)
    W, H = layer.size
    box = layer.getbbox()
    if box is None:
        return base
    rng = _next_rng()
    K = KINDS.get(kind) or KINDS['felt']
    dens, maxlen, tex_k, warp_px = K['dens'], K['maxlen'], K['tex'], K['warp']
    dome = K['prof'] == 'dome'
    s = H / 804.0  # sizes tuned for an 804-px frame (1.27 at 1024)
    m = int(max(48 * s * max(depth, 0.3), (maxlen + 8) * s))
    x0, y0, x1, y1 = max(0, box[0] - m), max(0, box[1] - m), min(W, box[2] + m), min(H, box[3] + m)
    w, h = x1 - x0, y1 - y0
    arr = np.asarray(layer.crop((x0, y0, x1, y1)).convert('RGBa'), np.float32) / 255.0  # premultiplied
    a0 = arr[..., 3]
    size = math.sqrt(max(1.0, float(a0.sum())))  # rough piece scale in px
    small = size < 40 * s

    # 1. rounder silhouette: blur + re-threshold, but never erase thin parts
    if not small and kind != 'hard':
        sig = 2.8 * s
        ab = gaussian_filter(a0, sig)
        rounded = _smoothstep(ab, 0.3, 0.7)
        thin = gaussian_filter((a0 > 0.5).astype(np.float32), 3 * s) < 0.55  # line-like region
        a0 = np.where(thin, a0, rounded)
        arr[..., 3] = a0
    else:
        a0 = gaussian_filter(a0, 0.6)
        arr[..., 3] = a0

    # 2. fibrous domain warp of colour and outline
    ox, oy = int(rng.integers(0, TN)), int(rng.integers(0, TN))
    if warp_px > 0:
        wx, wy = _warp_field()
        amp = warp_px * s / 1.27 * (0.6 if small else 1.0)
        dx = _tilecrop(wx, x0, y0, w, h, ox, oy) * amp
        dy = _tilecrop(wy, x0, y0, w, h, oy, ox) * amp
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        coords = [yy + dy, xx + dx]
        arr = np.stack([map_coordinates(arr[..., k], coords, order=1, mode='constant') for k in range(4)], -1)
    a = np.clip(arr[..., 3], 0, 1)
    rgb = np.where(a[..., None] > 1e-3, arr[..., :3] / np.maximum(a[..., None], 1e-3), 0)
    rgb = np.clip(rgb, 0, 1)

    # 4. felt colour: slight desaturation, heather, micro-fibre texture, oriented fibres, uneven density
    tile, h1, h2 = _felt_tile()
    lum = rgb @ np.array([0.3, 0.55, 0.15], np.float32)
    rgb = rgb + (lum[..., None] - rgb) * 0.12
    if kind != 'hard':
        t1 = _tilecrop(h1, x0, y0, w, h, ox, oy)[..., None]
        t2 = _tilecrop(h2, x0, y0, w, h, oy, ox)[..., None]
        warm = np.array([1.035, 1.0, 0.95], np.float32)
        cool = np.array([0.97, 0.99, 1.03], np.float32)
        hk = tex_k * (1 - 0.6 * np.clip(lum - 0.65, 0, 0.3)[..., None] / 0.3)
        mm = np.clip(t1 * 0.6, -1, 1)
        rgb = rgb * np.where(mm > 0, 1 + hk * mm * (warm - 1) * 1.3, 1 + hk * (-mm) * (cool - 1) * 1.3)
        rgb = rgb * (1 + hk * (0.03 * t1 + 0.03 * t2))
    tex = np.stack([_tilecrop(tile[..., k], x0, y0, w, h, ox, oy) for k in range(3)], -1)
    tk = tex_k * (0.8 + 1.4 * np.clip(0.45 - lum, 0, 0.45) - 0.45 * np.clip(lum - 0.62, 0, 0.3) / 0.3)[..., None]
    rgb = rgb * (1 + (tex - 1) * tk)

    inside = a > 0.5
    dist = distance_transform_edt(inside).astype(np.float32)
    # oriented fibres that follow the form: tangent of the (blurred) outline picks one of four fibre fields
    if K['dir'] > 0 and not small:
        R0 = max(4.0, min(130 * s, size * 0.36))
        sd = max(3.0, 0.3 * R0)
        ab = _blur(a, sd)
        gy, gx = np.gradient(ab)
        gm = np.hypot(gx, gy)
        strength = np.clip(gm * sd / 0.4 * 1.6, 0, 1)
        th = np.arctan2(gy, gx) + math.pi / 2  # tangent
        fib = _oriented_fibres()
        df = np.zeros((h, w), np.float32)
        wsum = np.zeros((h, w), np.float32) + 1e-4
        for k in range(4):
            wk = np.clip(np.cos(2 * (th - k * math.pi / 4)), 0, 1) ** 2
            df += wk * _tilecrop(fib[k], x0, y0, w, h, oy, ox)
            wsum += wk
        df /= wsum
        dark_k = (1 + 0.8 * np.clip(0.4 - lum, 0, 0.4)) * (1 - 0.6 * _smoothstep(lum, 0.55, 0.85))
        rgb = rgb * (1 + K['dir'] * (0.35 + 0.65 * strength) * df * dark_k)[..., None]

    # 5. volume: height profile + bump map -> normals
    bumps = _bump_fields()
    if dome:
        lab, nlab = label(inside)
        # a smooth ball: blurred mask (no medial-axis creases of a distance field), normalised per blob
        R = float(max(3.0, dist.max()))
        hb = gaussian_filter(inside.astype(np.float32), 0.42 * R)
        if nlab > 0:
            pk = np.asarray(nd_maximum(hb, lab, np.arange(1, nlab + 1)), np.float32)
            pk = np.concatenate([[1.0], np.maximum(pk, 1e-3)])[lab]
        else:
            pk = np.ones_like(hb)
        t = np.clip((hb / pk - 0.42) / 0.58, 0, 1)
        hgt = np.sqrt(np.clip(1 - (1 - t) ** 2, 0, 1)) * a
        k = R * 1.05
    else:
        R = max(4.0, min(130 * s, size * 0.36)) * (0.5 + 0.5 * min(depth, 1.2))
        hgt = np.sqrt(np.clip(1 - np.exp(-dist / R), 0, 1))  # 0 at the outline, -> 1 inside: a pillow
        hgt = _blur(hgt, 0.25 * R) * a
        k = R * 1.45
    gy, gx = np.gradient(hgt)
    bgx = np.zeros_like(gx)
    bgy = np.zeros_like(gy)
    alb = np.ones_like(gx)
    surf = K['surf'] * (0.6 if small else 1.0)
    if surf > 0:
        _, by, bx, ba_ = bumps['base']
        bgx += surf * _tilecrop(bx, x0, y0, w, h, ox, oy) * s / 1.27
        bgy += surf * _tilecrop(by, x0, y0, w, h, ox, oy) * s / 1.27
        alb *= 1 + surf * (_tilecrop(ba_, x0, y0, w, h, ox, oy) - 1)
    if K['weave']:
        _, by, bx, ba_ = bumps[K['weave']]
        # weaves keep their orientation (columns run down the garment), only shifted
        wox, woy = ox % 64, oy % 64
        bgx += _tilecrop(bx, x0, y0, w, h, wox, woy)
        bgy += _tilecrop(by, x0, y0, w, h, wox, woy)
        alb *= _tilecrop(ba_, x0, y0, w, h, wox, woy)
    inner = np.clip((a - 0.3) / 0.7, 0, 1) * _smoothstep(dist, 0.0, 3.0 * s)  # no bumps on the fuzzy rim
    nx, ny = -(gx * k + bgx * inner), -(gy * k + bgy * inner)
    nz = np.ones_like(nx)
    nn = np.sqrt(nx * nx + ny * ny + nz * nz)
    L = np.array([-0.55, -0.6, 0.58], np.float32)
    L /= np.linalg.norm(L)
    lam = (nx * L[0] + ny * L[1] + nz * L[2]) / nn
    flat_lam = L[2]
    vol = min(1.0, 0.45 + 0.6 * depth)
    if dome:
        vol = max(vol, 0.85)
    lit = 1 + (lam - flat_lam) * 1.75 * vol
    rim = (1 - hgt) * a  # towards the outline: occluded, darker and warmer
    ao = 0.30 * rim * min(1.0, 0.4 + 0.7 * depth)
    lo = 0.6 if kind in ('eye', 'bead') else 0.45
    shade = np.clip(lit, lo, 1.35) * (1 - ao)
    rgb = rgb * (shade * alb)[..., None]
    if kind != 'hard':
        # subsurface warmth: shadowed wool (and skin) keeps some saturated warm light
        dark = np.clip(1 - shade, 0, 0.55)[..., None]
        warmk = 0.6 if kind == 'skin' else 0.28
        rgb = rgb + dark * warmk * np.array([0.10, 0.025, -0.02], np.float32) * (0.4 + rgb)
        # broad, specular-free sheen: top-lit fibres catch a soft desaturated light (stronger where fibres show)
        sh_m = _smoothstep(lam - flat_lam, 0.02, 0.3) * min(depth, 1.0) * (1 if kind != 'eye' else 0.5)
        sh_m = sh_m * (0.8 + 1.6 * (tex[..., 1] - 1))  # the sheen sits on the fibres
        sheen_c = np.array([1.0, 0.97, 0.92], np.float32)
        rgb = rgb + (sheen_c - rgb) * (0.11 * np.clip(sh_m, 0, 1.3))[..., None]
    else:
        rgb = rgb + 0.035 * np.clip(lam - flat_lam, 0, 1)[..., None] * min(depth, 1.0)
    rgb = np.clip(rgb, 0, 1)
    if kind in ('hair', 'fur') and not small:
        st = _inner_strands(rgb, a, rng, s, 1 / 30.0 if kind == 'hair' else 1 / 70.0)
        if st is not None:
            srgb, sa = st
            sa = sa * np.clip((a - 0.5) * 2, 0, 1)
            rgb = rgb * (1 - sa[..., None]) + srgb * np.clip((a - 0.5) * 2, 0, 1)[..., None]
            rgb = np.clip(rgb, 0, 1)

    # 3. halo + stray fibres
    ab2 = _blur(a, 4.0 * s)
    halo = np.clip(ab2 - a, 0, 1) * (K['halo'] if dens > 0 else 0.0) * min(1.0, dens / 30 + 0.3)
    hcol = _blur_rgb(rgb, a, 2.6 * s)
    fib = _stray_fibres(rgb, a, rng, dens * (0.5 if small else 1.0), maxlen * (0.6 if small else 1.0), s) \
        if dens > 0 else None

    reg = base.crop((x0, y0, x1, y1))
    b = np.asarray(reg.convert('RGBa'), np.float32) / 255.0  # premultiplied
    cross = None
    if K['cross'] > 0 and not small:
        cross = _cross_fibres(b[..., :3], b[..., 3], a, rng, K['cross'], max(maxlen, 8), s)

    # soft shadow, contact crease and ambient occlusion on what lies beneath
    off = int(7 * s * depth)
    sh = _blur(a, 6.5 * s)
    sh2 = np.zeros_like(sh)
    dxo = off // 2
    if off > 0:
        sh2[off:, dxo:] = sh[:sh.shape[0] - off, :sh.shape[1] - dxo or None]
    else:
        sh2 = sh
    face = kind in ('eye', 'bead', 'fine', 'brow')
    occ = _blur(a, (7 if face else 16) * s)
    crease = _blur(a, 2.2 * s)
    dk = min(depth, 1.0)
    sh = np.clip(sh2 * 0.42 * depth + occ * 0.24 * dk + crease * 0.22 * dk, 0, 0.68)
    if kind == 'eye' or kind == 'bead':
        sh *= 0.8

    b[..., :3] *= (1 - sh * (1 - a))[..., None]
    # halo (under the piece)
    b[..., :3] = b[..., :3] * (1 - halo[..., None]) + hcol * halo[..., None]
    b[..., 3] = b[..., 3] * (1 - halo) + halo
    # the piece
    b[..., :3] = b[..., :3] * (1 - a[..., None]) + rgb * a[..., None]
    b[..., 3] = b[..., 3] * (1 - a) + a
    # fibres of the layer beneath crossing the border, then this piece's own stray fibres
    for f in (cross, fib):
        if f is not None:
            frgb, fa = f
            b[..., :3] = b[..., :3] * (1 - fa[..., None]) + frgb
            b[..., 3] = b[..., 3] * (1 - fa) + fa
    out = Image.fromarray((np.clip(b, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGBa').convert('RGBA')
    base.paste(out, (x0, y0))
    return base


def _blur_rgb(rgb, a, sigma):
    """Colour spread outwards from the piece (for the halo)."""
    wa = _blur(a, sigma) + 1e-4
    return np.stack([_blur(rgb[..., k] * a, sigma) / wa for k in range(3)], -1)


# ---------------------------------------------------------------- whole-frame studio light
def studio_light(img):
    """Soft key light from the top-left, gentle falloff, a warm rim on the right-hand outline and a soft shadow
    behind the bust. A pure function of the frame, so every state gets exactly the same treatment where it is equal."""
    W, H = img.size
    key = ('studio', W, H)
    if key not in _cache:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        xx /= W
        yy /= H
        d = np.hypot(xx - 0.3, yy - 0.2)
        light = 1.12 - 0.34 * np.clip(d / 0.95, 0, 1) ** 1.5
        _cache[key] = light.astype(np.float32)
    light = _cache[key]
    f = np.asarray(img.convert('RGBa'), np.float32) / 255.0
    a = f[..., 3]
    rgb = f[..., :3] * light[..., None]
    # warm rim light from the right-back: thin band inside the outline, facing right
    ab = _blur(a, 5)
    gy, gx = np.gradient(ab)
    rim = np.clip(-gx * 14, 0, 1) * np.clip(1 - ab, 0, 1) * 2.0 * a
    rgb = rgb + rim[..., None] * np.array([0.20, 0.15, 0.09], np.float32) * a[..., None]
    rgb = np.minimum(rgb, a[..., None])
    # soft contact / drop shadow behind the bust (to the lower right)
    sh = _blur(a, 16)
    sh = np.roll(np.roll(sh, 10, 0), 7, 1)
    sh[:10] = 0
    sh[:, :7] = 0
    sha = np.clip(sh * 0.42, 0, 0.42) * (1 - a)
    out_a = a + sha
    out = np.concatenate([rgb, out_a[..., None]], -1)  # shadow colour is black: premultiplied rgb unchanged
    return Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGBa').convert('RGBA')
