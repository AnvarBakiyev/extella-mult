"""look=felt: every element, actor and effect is drawn on its own layer and turned into a felt / plasticine cut-out:
soft rounded edges lit from the top-left, a fibrous grain, a soft shadow on the layers beneath."""
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

_grain = {}


def _grain_for(w, h):
    if (w, h) not in _grain:
        rng = np.random.default_rng(7)
        k = h / 1608.0  # tuned for the 2x supersampled frame; finer and fainter when drawn at the final size
        fine = gaussian_filter(rng.standard_normal((h, w)).astype(np.float32), 0.8 * k)
        fibre = gaussian_filter(rng.standard_normal((h, w)).astype(np.float32), (0.6 * k, 2.5 * k))  # short horizontal fibres
        g = (0.6 * fine / (fine.std() + 1e-6) + 0.4 * fibre / (fibre.std() + 1e-6)) * (0.6 if k < 0.75 else 1.0)
        _grain[(w, h)] = g
    return _grain[(w, h)]


def _blur(a, sigma):
    """Gaussian blur done at half (or quarter) resolution and scaled back: the blur is soft, so the loss is invisible
    and it is 4-16x cheaper."""
    k = 4 if sigma >= 8 else 2
    h, w = a.shape
    if sigma < 3 or h < 4 * k or w < 4 * k:
        return gaussian_filter(a, sigma, mode='nearest')
    im = Image.fromarray(a, 'F')
    small = np.asarray(im.resize((max(1, w // k), max(1, h // k)), Image.BILINEAR), np.float32)
    small = gaussian_filter(small, sigma / k, mode='nearest')
    return np.asarray(Image.fromarray(small, 'F').resize((w, h), Image.BILINEAR), np.float32)


def felt_composite(base, layer, depth=1.0):
    """Composite one RGBA layer onto base (RGBA, same size) as a felt cut-out. depth scales the bevel and the shadow.
    Only the box around what the layer drew is processed."""
    W, H = layer.size
    box = layer.getbbox()
    if box is None:
        return base
    s = H / 804.0  # sizes are tuned for an 804-px frame
    m = int(40 * s * max(depth, 0.3))
    x0, y0, x1, y1 = max(0, box[0] - m), max(0, box[1] - m), min(W, box[2] + m), min(H, box[3] + m)
    arr = np.asarray(layer.crop((x0, y0, x1, y1)), np.float32) / 255.0
    a = arr[..., 3]
    if H < 1200:  # no supersampling: soften the drawn edge by a pixel so it does not stair-step
        a = gaussian_filter(a, 0.7)
        arr[..., 3] = a
    # bevel: a blurred alpha is a height map; light from the top-left
    hgt = _blur(a, 9 * s)
    gy, gx = np.gradient(hgt)
    light = -(gx * 0.7 + gy * 0.7) * 22 * s * depth
    rim = np.clip(1 - hgt * 1.8, 0, 1) * a  # darker towards the edge, like a rounded pad
    shade = 1 + np.clip(light, -0.35, 0.35) - 0.18 * rim * depth
    shade *= 1 + 0.045 * _grain_for(W, H)[y0:y1, x0:x1]
    rgb = np.clip(arr[..., :3] * shade[..., None], 0, 1)
    # soft shadow on what lies beneath
    off = int(7 * s * depth)
    sh = _blur(a, 6 * s)
    sh2 = np.zeros_like(sh)  # shift down-right without wrapping around
    dx = off // 2
    sh2[off:, dx:] = sh[:sh.shape[0] - off or None, :sh.shape[1] - dx or None]
    sh = sh2 * 0.38 * depth
    reg = base.crop((x0, y0, x1, y1))
    b = np.asarray(reg, np.float32) / 255.0
    b[..., :3] *= (1 - sh * (1 - a))[..., None]
    b[..., :3] = b[..., :3] * (1 - a[..., None]) + rgb * a[..., None]
    b[..., 3] = np.maximum(b[..., 3], a)
    base.paste(Image.fromarray((b * 255).astype(np.uint8), 'RGBA'), (x0, y0))
    return base
