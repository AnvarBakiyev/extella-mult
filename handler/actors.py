"""Actors: characters with named actions. draw(ctx, t, tl, st, f) where f = progress 0..1 in the action.
Character art is drawn in a Local frame: 1 unit = the character's size, origin at the ground point."""
import math
from .draw import ease

ACTORS = {}
POSITIONS = {'offleft': (-0.25, None), 'left': (0.2, None), 'center': (0.5, None), 'right': (0.8, None),
             'offright': (1.25, None), 'center_left': (0.35, None), 'center_right': (0.65, None)}

FOX = dict(fur='#e4772b', fur_dark='#c75f1e', white='#f8f1e4', ear='#3a2420', eye='#f0b03c', iris='#7a4a10',
           nose='#2a1a18', line='#5a3018')


def actor(name, actions):
    def deco(fn):
        ACTORS[name] = (fn, actions)
        return fn
    return deco


def fox_side(ctx, x, y, s, phase, facing=1, gait='walk', C=FOX):
    """Side view. (x,y) = ground point under the chest; s = body height; facing=1 looks right."""
    L = ctx.local(x, y, s, facing)
    amp = 1.0 if gait == 'run' else 0.6
    bob = 0.03 * abs(math.sin(phase * 2))
    cy = -0.5 - bob
    swing = 0.1 * math.sin(phase + 1.0)
    L.curve([(-0.4, cy + 0.05), (-0.85, cy + 0.12 + swing), (-1.1, cy - 0.25 + swing)], C['fur'], 0.24)
    L.circle(-1.1, cy - 0.25 + swing, 0.13, C['white'])
    legs = [(-0.32, 0.0, C['fur_dark']), (0.32, math.pi, C['fur_dark']), (-0.25, math.pi, C['fur']), (0.28, 0.0, C['fur'])]
    for lx, ph, col in legs:
        sw = amp * 0.22 * math.sin(phase + ph)
        lift = 0.08 * max(0.0, math.sin(phase + ph)) * amp
        L.line([(lx, cy + 0.12), (lx + sw, -lift)], col, 0.11)
        L.circle(lx + sw, -lift, 0.06, C['ear'])
    L.ellipse(0, cy, 0.55, 0.27, C['fur'])
    L.ellipse(0.08, cy + 0.12, 0.4, 0.14, C['white'])
    L.ellipse(0.45, cy - 0.12, 0.3, 0.2, C['fur'], angle=-0.5)
    hx, hy, r = 0.6, cy - 0.38, 0.25
    H = ctx.local(*L.pt(hx, hy), s * r, facing)
    for sd in (-0.15, 0.2):
        H.poly([(sd, -0.6), (sd + 0.1, -1.9), (sd + 0.55, -0.7)], C['fur'])
    for sd in (-0.08, 0.27):
        H.poly([(sd, -0.8), (sd + 0.1, -1.6), (sd + 0.38, -0.85)], C['ear'])
    H.circle(0, 0, 1.0, C['fur'])
    H.poly([(0.3, -0.5), (1.5, 0.35), (0.2, 0.95)], C['fur'])
    H.poly([(0.5, 0.1), (1.5, 0.35), (0.2, 0.95)], C['white'])
    H.circle(1.45, 0.33, 0.14, C['nose'])
    ex, ey = 0.45, -0.1
    H.ellipse(ex, ey, 0.2, 0.26, C['iris'])
    H.ellipse(ex, ey + 0.02, 0.16, 0.2, C['eye'])
    H.ellipse(ex + 0.03, ey + 0.05, 0.09, 0.13, C['nose'])
    H.circle(ex - 0.03, ey - 0.1, 0.05, '#ffffff')


def fox_sit(ctx, x, y, s, t, facing=1, C=FOX):
    """Sitting fox, three-quarter view facing camera. (x,y) = ground centre, s = height."""
    L = ctx.local(x, y, s, facing)
    br = 0.01 * math.sin(t * 2.0)
    L.curve([(-0.25, -0.1), (-0.7, -0.05), (-0.5, 0.02), (0.2, 0.03)], C['fur'], 0.17)
    L.circle(0.2, 0.03, 0.09, C['white'])
    L.ellipse(-0.1, -0.22, 0.42, 0.24, C['fur'])
    L.ellipse(0.05, -0.5 + br, 0.28, 0.45, C['fur'])
    L.ellipse(0.1, -0.4 + br, 0.19, 0.33, C['white'])
    for dx in (0.02, 0.2):
        L.line([(dx, -0.35), (dx, -0.02)], C['fur'], 0.1)
        L.circle(dx, -0.02, 0.06, C['ear'])
    fox_head(ctx, *L.pt(0.12, -0.92 + br), s * 0.62, t, C=C, look=(0.1 * facing, 0.05))


def fox_head(ctx, hx, hy, s, t, C=FOX, look=(0.0, 0.0), blink=True):
    """Front-facing fox head, radius ~0.5*s, centred at (hx,hy)."""
    H = ctx.local(hx, hy, s * 0.5)
    for sd in (-1, 1):
        H.poly([(sd * 0.3, -0.6), (sd * 0.75, -1.55), (sd * 0.95, -0.45)], C['fur'])
        H.poly([(sd * 0.42, -0.7), (sd * 0.72, -1.35), (sd * 0.85, -0.55)], C['ear'])
    H.ellipse(0, 0, 1.0, 0.92, C['fur'])
    H.ellipse(0, -0.3, 0.8, 0.55, C['fur'])
    pts = []
    for i in range(25):
        a = math.pi * i / 24
        rr = 1.08 if i % 2 == 0 else 0.96
        pts.append((-rr * math.cos(a), 0.18 + rr * 0.78 * math.sin(a)))
    pts = [(-0.95, 0.05)] + pts + [(0.95, 0.05), (0.8, -0.12), (0.4, 0.12), (0, 0.3), (-0.4, 0.12), (-0.8, -0.12)]
    H.poly(pts, C['white'])
    bl = 1.0
    if blink:
        cyc = (t * 0.37) % 1.0
        if cyc > 0.94:
            bl = max(0.08, abs(math.cos((cyc - 0.94) / 0.06 * math.pi)))
    for sd in (-1, 1):
        ex, ey = sd * 0.4 + look[0] * 0.1, -0.02 + look[1] * 0.1
        H.ellipse(ex, ey, 0.25, 0.3 * bl, C['iris'])
        H.ellipse(ex, ey + 0.02, 0.2, 0.25 * bl, C['eye'])
        H.ellipse(ex + look[0] * 0.06, ey + 0.05 + look[1] * 0.08, 0.11, 0.17 * bl, C['nose'])
        if bl > 0.5:
            H.circle(ex - 0.08, ey - 0.1, 0.06, '#ffffff')
            H.circle(ex + 0.08, ey + 0.1, 0.03, '#ffffff')
    H.ellipse(0, 0.45, 0.1, 0.07, C['nose'])
    H.curve([(0, 0.5), (0.08, 0.64), (0.18, 0.57)], C['line'], 0.015)
    H.curve([(0, 0.5), (-0.08, 0.64), (-0.18, 0.57)], C['line'], 0.015)


def _lerp_pos(st, f, default_y):
    def val(pos):
        if pos is None:
            return (0.5, default_y)
        if isinstance(pos, tuple):
            return (pos[0], default_y if pos[1] is None else pos[1])
        return (POSITIONS[pos][0], default_y)
    if st.pos is not None:
        return val(st.pos)
    a, b = val(st.frm), val(st.to)
    return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)


def _facing(st):
    if st.frm is not None and st.to is not None:
        a = POSITIONS[st.frm][0] if isinstance(st.frm, str) else st.frm[0]
        b = POSITIONS[st.to][0] if isinstance(st.to, str) else st.to[0]
        return int(st.params.get('facing', 1 if b >= a else -1))
    return int(st.params.get('facing', 1))


@actor('fox', ['walk', 'run', 'sit', 'closeup', 'stand'])
def fox(ctx, t, tl, st, f):
    action = st.words[1]
    size = st.params.get('size', 0.18)
    x, y = _lerp_pos(st, f, st.params.get('y', 0.8))
    facing = _facing(st)
    if action in ('walk', 'run'):
        fox_side(ctx, x, y, size, t * (7.0 if action == 'walk' else 13.0), facing, action)
    elif action == 'stand':
        fox_side(ctx, x, y, size, 0.3, facing, 'walk')
    elif action == 'sit':
        fox_sit(ctx, x, y, size, t, facing)
    elif action == 'closeup':
        look = (0.0, -0.9 * ease((tl - 0.8) / 1.5) * st.params.get('lookup', 1))
        L = ctx.local(x, y, size)
        L.ellipse(0, 0.9, 0.5, 0.5, FOX['fur'])
        L.ellipse(0, 0.9, 0.38, 0.45, FOX['white'])
        fox_head(ctx, x, y, size, t, look=look)


CAT = dict(fur='#8a8a92', fur_dark='#5e5e68', white='#f2f0ee', ear='#d9a0a8', eye='#8fc46a', nose='#d98a90', line='#3a3a40')


def cat_sit(ctx, x, y, s, t, facing=1, reach=0.0, C=CAT):
    """Sitting cat, three-quarter view; reach 0..1 extends a front paw forward (to knock something)."""
    L = ctx.local(x, y, s, facing)
    br = 0.01 * math.sin(t * 2.5)
    tail_wag = 0.08 * math.sin(t * 1.8)
    L.curve([(-0.3, -0.1), (-0.8, -0.2 + tail_wag), (-0.95, -0.6 + tail_wag), (-0.75, -0.85)], C['fur'], 0.11)
    L.ellipse(-0.1, -0.22, 0.4, 0.22, C['fur'])
    L.ellipse(0.05, -0.5 + br, 0.27, 0.42, C['fur'])
    L.ellipse(0.1, -0.38 + br, 0.17, 0.3, C['white'])
    for i in range(3):  # stripes on the back
        L.curve([(-0.35 + i * 0.1, -0.5 + i * 0.05), (-0.25 + i * 0.1, -0.6 + i * 0.05), (-0.1 + i * 0.1, -0.52 + i * 0.05)], C['fur_dark'], 0.03)
    L.line([(0.0, -0.35), (0.0, -0.02)], C['fur'], 0.1)
    L.circle(0.0, -0.02, 0.06, C['fur'])
    # reaching paw
    px, py = 0.2 + 0.75 * reach, -0.02 - 0.45 * reach
    L.curve([(0.2, -0.4), (0.2 + 0.4 * reach, -0.4 - 0.2 * reach), (px, py)], C['fur'], 0.1)
    L.circle(px, py, 0.065, C['white'])
    cat_head(ctx, *L.pt(0.12, -0.88 + br), s * 0.55, t, facing, C, look=(0.15 + 0.3 * reach, 0.1))


def cat_head(ctx, hx, hy, s, t, facing=1, C=CAT, look=(0.0, 0.0)):
    H = ctx.local(hx, hy, s * 0.5, facing)
    for sd in (-1, 1):
        H.poly([(sd * 0.35, -0.55), (sd * 0.75, -1.35), (sd * 0.98, -0.35)], C['fur'])
        H.poly([(sd * 0.48, -0.62), (sd * 0.74, -1.15), (sd * 0.86, -0.45)], C['ear'])
    H.ellipse(0, 0, 1.05, 0.9, C['fur'])
    H.ellipse(0, 0.35, 0.7, 0.5, C['white'])
    for sd in (-1, 1):
        H.curve([(sd * 0.25, -0.75), (sd * 0.3, -0.5), (sd * 0.2, -0.3)], C['fur_dark'], 0.07)
    H.curve([(0, -0.85), (0.02, -0.6), (0, -0.4)], C['fur_dark'], 0.07)
    bl = 1.0
    cyc = (t * 0.31) % 1.0
    if cyc > 0.95:
        bl = max(0.1, abs(math.cos((cyc - 0.95) / 0.05 * math.pi)))
    for sd in (-1, 1):
        ex, ey = sd * 0.42 + look[0] * 0.08, -0.05 + look[1] * 0.08
        H.ellipse(ex, ey, 0.22, 0.24 * bl, C['line'])
        H.ellipse(ex, ey, 0.18, 0.2 * bl, C['eye'])
        H.ellipse(ex + look[0] * 0.05, ey, 0.06, 0.16 * bl, C['line'])
        if bl > 0.5:
            H.circle(ex - 0.07, ey - 0.08, 0.05, '#ffffff')
    H.poly([(-0.1, 0.3), (0.1, 0.3), (0, 0.42)], C['nose'])
    H.curve([(0, 0.42), (-0.08, 0.55), (-0.2, 0.48)], C['line'], 0.015)
    H.curve([(0, 0.42), (0.08, 0.55), (0.2, 0.48)], C['line'], 0.015)
    for sd in (-1, 1):
        for dy in (-0.05, 0.08):
            H.line([(sd * 0.35, 0.35 + dy), (sd * 1.3, 0.25 + dy * 2)], C['white'], 0.012)


@actor('cat', ['sit', 'paw', 'look'])
def cat(ctx, t, tl, st, f):
    action = st.words[1]
    size = st.params.get('size', 0.3)
    x, y = _lerp_pos(st, f, st.params.get('y', 0.8))
    facing = _facing(st)
    if action == 'sit':
        cat_sit(ctx, x, y, size, t, facing)
    elif action == 'paw':
        # reach out slowly, hold, then pull back fast
        reach = ease(f / 0.6) if f < 0.6 else ease((1 - f) / 0.15) if f > 0.85 else 1.0
        cat_sit(ctx, x, y, size, t, facing, reach=reach)
    elif action == 'look':
        cat_sit(ctx, x, y, size, t, facing, reach=0.0)

