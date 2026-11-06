"""Felt effects: small felt pieces that fall, rise or flutter. Each piece goes on its own felt layer when it is large."""
import math
import numpy as np
from .draw import Local

FX = {}


def effect(name):
    def deco(fn):
        FX[name] = fn
        return fn
    return deco


def _rng(st, k=0):
    return np.random.default_rng(int(st.params.get('seed', 5)) + k)


def _count(st, d):
    return int(st.params.get('count', d))


_GLYPHS = {}
LETTER_COLORS = ('#f28b6b', '#f6c453', '#4f9fd0', '#f2a0b8', '#8cc26a', '#a98bd8', '#f4a05a', '#e0526f')


def _puffy_glyph(ch, px):
    """One letter as a puffy felt cut-out: the open Caveat font (OFL), thickened and rounded so it reads like a stuffed letter."""
    key = (ch, px)
    if key not in _GLYPHS:
        import os
        from PIL import Image, ImageDraw, ImageFont
        from scipy.ndimage import gaussian_filter
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'fonts', 'Caveat.ttf')
        fnt = ImageFont.truetype(path, px)
        try:
            fnt.set_variation_by_axes([700])
        except Exception:
            pass
        l, tp, r, b = fnt.getbbox(ch)
        pad = int(px * 0.18)
        im = Image.new('L', (r - l + 2 * pad, b - tp + 2 * pad), 0)
        ImageDraw.Draw(im).text((pad - l, pad - tp), ch, font=fnt, fill=255)
        a = np.asarray(im, np.float32) / 255.0
        a = gaussian_filter(a, px * 0.02)
        a = np.clip((a - 0.3) * 6, 0, 1)
        a = gaussian_filter(a, 1.2)
        _GLYPHS[key] = (a, pad - l, pad - tp, fnt.getlength(ch))
    return _GLYPHS[key]


def _say_font(px):
    if ('say', px) not in _GLYPHS:
        import os
        from PIL import ImageFont
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'fonts', 'Caveat.ttf')
        fnt = ImageFont.truetype(path, px)
        try:
            fnt.set_variation_by_axes([700])
        except Exception:
            pass
        _GLYPHS[('say', px)] = fnt
    return _GLYPHS[('say', px)]


def _say_wrap(fnt, text, width):
    """Break the words to fit width; a \\n in the line always breaks."""
    out = []
    for para in text.split('\n'):
        cur = ''
        for w in para.split():
            nxt = (cur + ' ' + w).strip()
            if cur and fnt.getlength(nxt) > width:
                out.append(cur)
                cur = w
            else:
                cur = nxt
        out.append(cur)
    return out


def _say_tip(ctx, prog, st, t):
    """Where the bubble's tail points: just above the speaker's head at time t, following it while it moves."""
    from .felt_actors import _place, PEOPLE, ANIMALS
    if st.pos is not None:
        from .actors import _lerp_pos
        return _lerp_pos(st, 0.0, 0.5)
    name = st.words[0]
    lines = [a for a in prog.stmts if a.kind == 'actor' and a.words[0] == name and a.scene is st.scene]
    a = next((a for a in lines if a.t0 <= t < a.t1), None) or min(lines, key=lambda a: min(abs(t - a.t0), abs(t - a.t1)))
    x, y, facing = _place(a, min(1.0, max(0.0, (t - a.t0) / (a.t1 - a.t0))))
    act = a.words[1]
    if name in PEOPLE:
        s, dx, top = a.params.get('size', 0.36), 0.02, 1.0 - (0.22 if act == 'sit' else 0.0)
    elif name in ANIMALS:
        s = a.params.get('size', 0.22)
        dx, top = (0.05, 1.02) if act == 'sit' else (0.2, 0.95)
        top += {'long': 0.32, 'pointy': 0.1, 'round': 0.05, 'big': 0.12, 'bulge': 0.1, 'comb': 0.08, 'small': 0.05}.get(ANIMALS[name][2], 0.0)
    else:
        s, dx, top = a.params.get('size', 0.1), 0.25, 0.8
    if act == 'jump':
        top += 0.22
    if act == 'sleep':
        dx, top = 0.0, 0.42
    return x + dx * s * ctx.ar * facing, y - (top + 0.05) * s


def say_layout(ctx, t, st, prog):
    """'<actor> say "Привет, котик!" 3-5s': a felt speech bubble over the speaker with a tail pointing at its head. The bubble
    fades in and out, follows the speaker and wraps long lines (Cyrillic and \\n too). Two bubbles that would touch are moved
    apart by themselves and --check warns about it. Params: size (letter height, 0.05),
    width (widest line as a fraction of the frame, 0.26), side=left|right, color, at x,y (a bubble with no speaker in the frame)."""
    W, H = ctx.W, ctx.H
    fade = min(0.3, (st.t1 - st.t0) / 3)
    op = min(1.0, (t - st.t0) / fade, (st.t1 - t) / fade)
    op = op * op * (3 - 2 * op)
    px = max(8, int(st.params.get('size', 0.05) * H * 1.25))
    fnt = _say_font(px)
    lines = _say_wrap(fnt, st.text, st.params.get('width', 0.26) * W)
    lh = px * 0.95
    pad = px * 0.62
    bw = max(fnt.getlength(s) for s in lines) + 2 * pad
    bh = lh * len(lines) + 2 * pad * 0.8
    tx, ty = _say_tip(ctx, prog, st, t)
    tx, ty = tx * W, ty * H
    side = {'left': -1, 'right': 1}.get(st.params.get('side'), 1 if tx < W / 2 else -1)
    m = 0.02 * H
    left = min(max(tx + side * bw * 0.18 - bw / 2, m + px * 0.5), W - m - px * 0.5 - bw)
    bottom = ty - 0.085 * H + (1 - op) * 0.012 * H
    bottom = max(bottom, bh + m + px * 0.5)
    return dict(opacity=op, px=px, fnt=fnt, lines=lines, lh=lh, left=left, right=left + bw, top=bottom - bh, bottom=bottom, tip=(tx, ty),
                color=st.params.get('color', '#fffaf0'), ink=st.params.get('one_color', '#4a3228'), start_x=_say_tip(ctx, prog, st, st.t0)[0])


def _say_hit(a, b):
    g = a['px'] * 0.9  # the puffs stick out past the box
    return a['left'] < b['right'] + g and b['left'] < a['right'] + g and a['top'] < b['bottom'] + g and b['top'] < a['bottom'] + g


def _say_push(ctx, a, b, w):
    """Slide two touching bubbles apart, half the overlap each, or all of it when one is against the frame's edge. With no
    room sideways the later one rises over the earlier. w < 1 while a bubble is fading: that is what makes the slide smooth."""
    later, first = (b, a) if a['order'] < b['order'] else (a, b)
    if a['start_x'] > b['start_x']:
        a, b = b, a
    g = a['px'] * 0.95
    m = 0.02 * ctx.H + a['px'] * 0.5
    need = (a['right'] + g - b['left']) * w
    if need <= 0:
        return
    da = max(0.0, min(need / 2, a['left'] - m))
    db = max(0.0, min(need - da, ctx.W - m - b['right']))
    da = max(0.0, min(need - db, a['left'] - m))
    a['left'] -= da
    a['right'] -= da
    b['left'] += db
    b['right'] += db
    if da + db < need - 1:
        lift = max(0.0, min(later['bottom'] - first['top'] + g, later['top'] - m)) * w
        later['top'] -= lift
        later['bottom'] -= lift


def say_layouts(ctx, t, prog, sc, full=False):
    """All the bubbles to draw at time t, already moved apart. full=True ignores the fades (used by --check)."""
    says = sorted((s for s in prog.stmts if s.kind == 'say' and s.scene is sc and s.t0 <= t < s.t1), key=lambda s: (s.t0, s.line))
    lays = [say_layout(ctx, t, s, prog) for s in says]
    for i, lay in enumerate(lays):
        lay['order'], lay['st'] = i, says[i]
    for _ in range(4):
        for i, a in enumerate(lays):
            for b in lays[i + 1:]:
                if _say_hit(a, b):
                    _say_push(ctx, a, b, 1.0 if full else min(a['opacity'], b['opacity']))
    return lays


class _Frame:
    def __init__(self, size):
        self.W, self.H = size
        self.ar = self.H / self.W


def say_warnings(prog):
    """What --check says about bubbles that touch: moved apart automatically, or no room left to do it."""
    out, c = [], _Frame(prog.size)
    says = sorted((s for s in prog.stmts if s.kind == 'say'), key=lambda s: (s.t0, s.line))
    for i, a in enumerate(says):
        for b in says[i + 1:]:
            if a.scene is not b.scene or b.t0 >= a.t1:
                continue
            times = [b.t0 + 0.25 * k for k in range(int((min(a.t1, b.t1) - b.t0) / 0.25) + 1)]
            times = [t for t in times if t < min(a.t1, b.t1)]
            def placed(t):
                both = [x for x in say_layouts(c, t, prog, a.scene, full=True) if x['st'] in (a, b)]
                return _say_hit(both[0], both[1])
            stuck = next((t for t in times if placed(t)), None)
            moved = next((t for t in times if _say_hit(say_layout(c, t, a, prog), say_layout(c, t, b, prog))), None)
            if stuck is not None:
                out.append(f"line {b.line}: the bubbles of {a.words[0]} (line {a.line}) and {b.words[0]} overlap at {stuck:g}s and there is no room to move them apart; shorten a line or say them one after the other")
            elif moved is not None:
                out.append(f"line {b.line}: the bubbles of {a.words[0]} (line {a.line}) and {b.words[0]} would overlap at {moved:g}s; they are moved apart, say them one after the other to keep each over its speaker")
    return out


def say_cloud(ctx, lay):
    """The bubble itself: one felt piece, a puffy rounded cloud and its curved tail."""
    d = ctx.d
    l, r, tp, b, col = lay['left'], lay['right'], lay['top'], lay['bottom'], lay['color']
    rad = lay['px'] * 0.5
    d.rounded_rectangle([l, tp, r, b], radius=rad * 1.4, fill=col)
    nx = max(2, int((r - l) / (rad * 1.75)))
    ny = max(1, int((b - tp) / (rad * 1.75)))
    for k in range(nx + 1):
        x = l + rad + (r - l - 2 * rad) * k / nx
        for y in (tp - rad * 0.05, b + rad * 0.05):
            d.ellipse([x - rad, y - rad, x + rad, y + rad], fill=col)
    for k in range(ny + 1):
        y = tp + rad + (b - tp - 2 * rad) * k / ny
        for x in (l - rad * 0.05, r + rad * 0.05):
            d.ellipse([x - rad, y - rad, x + rad, y + rad], fill=col)
    tx, ty = lay['tip']
    half = rad * 1.5
    base = min(max(tx, l + rad * 2.2), r - rad * 2.2)
    bend = (base - tx) * 0.35
    edge = lambda x0: [((1 - u) ** 2 * x0 + 2 * u * (1 - u) * (tx + bend) + u * u * tx, (1 - u) ** 2 * (b - rad) + 2 * u * (1 - u) * ((b + ty) / 2) + u * u * ty) for u in [i / 10 for i in range(11)]]
    d.polygon(edge(base - half) + edge(base + half)[::-1], fill=col)


def say_words(ctx, lay):
    """The words go on top of the cloud, flat and dark, so they stay easy to read."""
    cx = (lay['left'] + lay['right']) / 2
    y0 = (lay['top'] + lay['bottom']) / 2 - lay['lh'] * len(lay['lines']) / 2
    for i, s in enumerate(lay['lines']):
        ctx.d.text((cx, y0 + lay['lh'] * (i + 0.5)), s, font=lay['fnt'], fill=lay['ink'], anchor='mm')


def felt_letters(ctx, t, tl, st, f):
    """'text ... font' in felt: every letter is its own stuffed felt piece in its own colour, popping in one by one;
    centred at x,y; size = letter height as a fraction of the frame; color=#rrggbb makes them all one colour."""
    from PIL import Image
    x, y = st.pos if isinstance(st.pos, tuple) else (0.5, 0.5)
    px = max(8, int(st.params.get('size', 0.12) * ctx.H * 1.25))
    one = st.params.get('one_color')
    text = st.text
    track = px * 0.06
    adv = [_puffy_glyph(ch, px)[3] + track for ch in text]
    total = sum(adv) - track
    cx0 = x * ctx.W - total / 2
    n = max(1, sum(1 for ch in text if ch != ' '))
    shown = min(n, max(f * 1.08 * n, (t - st.t0) * 8))  # at least 8 letters a second, so a long title is read before it fades
    i = 0
    pen = cx0
    for ch, w in zip(text, adv):
        if ch != ' ':
            k = min(1.0, max(0.0, (shown - i) * 2.5))
            if k > 0:
                a, ox, oy, _ = _puffy_glyph(ch, px)
                col = one or LETTER_COLORS[i % len(LETTER_COLORS)]
                rgb_ = tuple(int(col[j:j + 2], 16) for j in (1, 3, 5))
                g = np.zeros(a.shape + (4,), np.uint8)
                g[..., :3] = rgb_
                g[..., 3] = (a * 255).astype(np.uint8)
                im = Image.fromarray(g, 'RGBA').rotate(((i * 37) % 5 - 2) * 1.0, resample=Image.BICUBIC, expand=False)
                bounce = (1 - k) * px * 0.25
                pc = ctx.piece() if hasattr(ctx, 'piece') else ctx
                pc.img.alpha_composite(im, (int(pen - ox), int(y * ctx.H - px * 0.62 - oy - bounce)))
            i += 1
        pen += w


@effect('snow')
def snow(ctx, t, tl, st, f):
    """Felt snowflakes falling over the whole frame."""
    r = _rng(st)
    for i in range(_count(st, 60)):
        x0, sp, sz, ph = r.random(), 0.04 + 0.05 * r.random(), 0.006 + 0.01 * r.random(), r.random() * 6
        y = (r.random() + tl * sp) % 1.1 - 0.05
        ctx.circle(x0 + 0.02 * math.sin(tl * 1.5 + ph), y, sz, '#ffffff')


@effect('rain')
def rain(ctx, t, tl, st, f):
    """Felt rain drops."""
    r = _rng(st)
    for i in range(_count(st, 70)):
        x, sp = r.random(), 0.5 + 0.3 * r.random()
        y = (r.random() + tl * sp) % 1.1 - 0.05
        ctx.ellipse(x, y, 0.004, 0.012, '#7fb6e8')


@effect('hearts')
def hearts(ctx, t, tl, st, f):
    """Hearts float up from at=x,y."""
    x0, y0 = st.params.get('at', (0.5, 0.6))
    r = _rng(st)
    for i in range(_count(st, 7)):
        d = (tl * 0.6 + i / 7) % 1.0
        x, y, s = x0 + (r.random() - 0.5) * 0.25 + 0.02 * math.sin(tl * 3 + i), y0 - d * 0.45, 0.03 + 0.02 * r.random()
        L = Local(ctx.piece(), x, y, s * (1 - 0.3 * d), 1)
        L.circle(-0.25, -0.1, 0.32, '#f06a8a')
        L.circle(0.25, -0.1, 0.32, '#f06a8a')
        L.poly([(-0.55, 0.0), (0.55, 0.0), (0.0, 0.6)], '#f06a8a')


@effect('sparkles')
def sparkles(ctx, t, tl, st, f):
    """Twinkling four-point stars around at=x,y (radius r)."""
    x0, y0 = st.params.get('at', (0.5, 0.4))
    rad = st.params.get('r', 0.2)
    r = _rng(st)
    for i in range(_count(st, 10)):
        a, d, ph = r.random() * 6.28, rad * math.sqrt(r.random()), r.random() * 6
        s = 0.018 * (0.4 + 0.6 * abs(math.sin(tl * 3 + ph)))
        L = Local(ctx, x0 + d * math.cos(a) * ctx.ar, y0 + d * math.sin(a), s, 1)
        L.poly([(0, -1), (0.25, -0.25), (1, 0), (0.25, 0.25), (0, 1), (-0.25, 0.25), (-1, 0), (-0.25, -0.25)], '#fff2a8')


@effect('leaves')
def leaves(ctx, t, tl, st, f):
    """Autumn leaves drifting down."""
    r = _rng(st)
    cols = ('#e8833a', '#d9542f', '#f2b64a', '#a8c45a')
    for i in range(_count(st, 14)):
        x0, sp, ph = r.random(), 0.06 + 0.05 * r.random(), r.random() * 6
        y = (r.random() + tl * sp) % 1.1 - 0.05
        L = Local(ctx.piece(), x0 + 0.04 * math.sin(tl * 1.3 + ph), y, 0.025, 1)
        L.ellipse(0, 0, 0.6, 0.3, cols[i % 4], angle=math.sin(tl * 2 + ph))


@effect('bubbles')
def bubbles(ctx, t, tl, st, f):
    """Bubbles rise from at=x,y."""
    x0, y0 = st.params.get('at', (0.5, 0.9))
    r = _rng(st)
    for i in range(_count(st, 12)):
        d = (tl * 0.25 + r.random()) % 1.0
        s = 0.012 + 0.02 * r.random()
        c = ctx.piece()
        c.circle(x0 + (r.random() - 0.5) * 0.3 + 0.02 * math.sin(tl * 2 + i), y0 - d * 0.8, s, '#cfeaf8')


@effect('balloons')
def balloons(ctx, t, tl, st, f):
    """Balloons rise from the bottom over the effect's time."""
    r = _rng(st)
    cols = ('#f06a6a', '#f6c453', '#7fb6e8', '#9bd27a', '#c39be0')
    for i in range(_count(st, 6)):
        x = 0.1 + 0.8 * r.random()
        y = 1.15 - f * (0.9 + 0.4 * r.random()) - 0.1 * r.random()
        L = Local(ctx.piece(), x + 0.015 * math.sin(tl * 1.4 + i), y, 0.06, 1)
        L.line([(0, 0.55), (0.05, 1.3)], '#6a6a6a', 0.03)
        L.ellipse(0, 0, 0.42, 0.55, cols[i % 5])


@effect('butterflies')
def butterflies(ctx, t, tl, st, f):
    """Butterflies flutter around at=x,y."""
    x0, y0 = st.params.get('at', (0.5, 0.5))
    r = _rng(st)
    cols = ('#f2a0c8', '#f6d353', '#9fd0ee')
    for i in range(_count(st, 3)):
        ph = r.random() * 6
        x = x0 + 0.12 * math.sin(tl * 0.7 + ph) * ctx.ar * 2
        y = y0 + 0.06 * math.sin(tl * 1.1 + ph * 2)
        flap = abs(math.sin(tl * 12 + ph))
        L = Local(ctx.piece(), x, y, 0.035, 1)
        L.ellipse(-0.35 * flap, -0.2, 0.4 * flap + 0.08, 0.35, cols[i % 3])
        L.ellipse(0.35 * flap, -0.2, 0.4 * flap + 0.08, 0.35, cols[i % 3])
        L.ellipse(0, 0, 0.08, 0.35, '#5a4040')


@effect('notes')
def notes(ctx, t, tl, st, f):
    """Music notes float up from at=x,y."""
    x0, y0 = st.params.get('at', (0.5, 0.5))
    for i in range(_count(st, 4)):
        d = (tl * 0.5 + i / 4) % 1.0
        L = Local(ctx.piece(), x0 + 0.08 * math.sin(i * 2 + tl), y0 - d * 0.35, 0.04, 1)
        L.ellipse(0, 0, 0.32, 0.24, '#5a4a8a', angle=-0.4)
        L.line([(0.27, -0.05), (0.27, -1.0)], '#5a4a8a', 0.1)
        L.line([(0.27, -1.0), (0.6, -0.8)], '#5a4a8a', 0.1)


@effect('smoke')
def smoke(ctx, t, tl, st, f):
    """Puffy felt smoke clouds that billow out sideways and up from at=x,y (a rocket launch, a crash, a cough);
    r = how far they spread; color=#efebe4."""
    x0, y0 = st.params.get('at', (0.5, 0.85))
    R = st.params.get('r', 0.25)
    col = st.params.get('color', '#efebe4')
    r = _rng(st, 3)
    g = min(1.0, tl / 1.2)  # grows for the first second
    for i in range(_count(st, 12)):
        side = -1 if i % 2 else 1
        d = r.random()
        x = x0 + side * d * R * g * ctx.H / ctx.W * 1.6
        y = y0 - (0.05 + 0.25 * r.random()) * R * g - 0.01 * tl
        sz = (0.03 + 0.05 * r.random()) * (0.5 + g) * (1 + 0.05 * math.sin(tl * 2 + i))
        pc = ctx.piece()
        pc.circle(x, y, sz, col)
        pc.circle(x + 0.4 * sz * ctx.H / ctx.W, y - 0.3 * sz, sz * 0.7, col)
