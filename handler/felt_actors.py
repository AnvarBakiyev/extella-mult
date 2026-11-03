"""Felt characters. Each body part is drawn on its own piece (ctx.piece()), so the felt pass gives every piece its own
rounded edge and shadow, like an applique. Local units: 1 = the character's height, feet at v=0, top of the head near v=-1."""
import math
from .draw import Local

FA = {}
PEOPLE = {  # skin, hair, top, bottom, shoes, hair style
    'girl': ('#f6d2b6', '#5a3826', '#69c3c8', '#3f5f9a', '#ffffff', 'curls'),
    'boy': ('#e9bf9c', '#2f2420', '#f2a541', '#4a6aa8', '#7a4a2a', 'short'),
    'mom': ('#f3cfb2', '#8a4a2a', '#e06c8c', '#e06c8c', '#6a3a2a', 'bun'),
    'dad': ('#e2b48f', '#3a2a22', '#5f9e6e', '#45506a', '#3a2a22', 'short'),
    'granny': ('#f1d6c0', '#d8d8dc', '#9b7bc4', '#9b7bc4', '#6a5a7a', 'bun'),
    'grandpa': ('#e8c4a4', '#cfcfd4', '#c9834f', '#5a5a64', '#3a2a22', 'bald'),
}
ANIMALS = {  # fur, belly, ear shape, tail shape
    'cat': ('#9aa0ad', '#eef0f4', 'pointy', 'long'),
    'fox': ('#ec8a3e', '#fbf1e2', 'pointy', 'bushy'),
    'dog': ('#c99a62', '#f4e6cf', 'floppy', 'short'),
    'bunny': ('#f2eee8', '#ffd9e2', 'long', 'puff'),
    'bear': ('#9a6a46', '#d9b48a', 'round', 'none'),
}
PERSON_ACTIONS = ['stand', 'walk', 'run', 'wave', 'jump', 'sit', 'dance', 'look_up']
ANIMAL_ACTIONS = ['stand', 'walk', 'run', 'jump', 'sit', 'look_up']


def actor(name, actions):
    def deco(fn):
        FA[name] = (fn, actions)
        return fn
    return deco


def _place(st, f):
    from .actors import _lerp_pos, _facing
    x, y = _lerp_pos(st, f, st.params.get('y', 0.86))
    return x, y, _facing(st)


def _dark(c, k=0.75):
    return '#%02x%02x%02x' % tuple(int(int(c[i:i + 2], 16) * k) for i in (1, 3, 5))


def _limb(L, a, b, w, col):
    L.line([a, b], col, w)


def _pose(action, t, tl, dur):
    """Angles in radians (0 = straight down) and body offsets for one moment of an action."""
    ph = t * 2 * math.pi
    P = dict(leg_b=0.12, leg_f=-0.12, arm_b=0.2, arm_f=-0.2, bob=0.004 * math.sin(ph * 0.5), lean=0.0, lift=0.0, sit=0.0, head=0.0)
    if action == 'walk':
        sw = math.sin(ph * 1.6)
        P.update(leg_b=0.45 * sw, leg_f=-0.45 * sw, arm_b=-0.5 * sw, arm_f=0.5 * sw, bob=0.012 * abs(math.cos(ph * 1.6)))
    elif action == 'run':
        sw = math.sin(ph * 2.6)
        P.update(leg_b=0.8 * sw, leg_f=-0.8 * sw, arm_b=-0.9 * sw, arm_f=0.9 * sw, bob=0.03 * abs(math.cos(ph * 2.6)), lean=0.12)
    elif action == 'wave':
        P.update(arm_f=-2.6 + 0.35 * math.sin(ph * 2.2), arm_b=0.15)
    elif action == 'jump':
        k = abs(math.sin(math.pi * ((tl * 1.4) % 1.0)))
        P.update(lift=0.22 * k, arm_b=-2.3 * k + 0.2, arm_f=2.3 * k - 0.2, leg_b=0.3 * k, leg_f=-0.3 * k)
    elif action == 'sit':
        P.update(sit=1.0, leg_b=-1.45, leg_f=-1.45, arm_b=-0.5, arm_f=-0.5)
    elif action == 'dance':
        sw = math.sin(ph * 1.8)
        P.update(arm_b=-2.4 + 0.5 * sw, arm_f=2.4 + 0.5 * sw, leg_b=0.25 * sw, leg_f=-0.25 * sw, lean=0.12 * sw, bob=0.02 * abs(sw))
    elif action == 'look_up':
        P.update(head=-0.35)
    return P


def _person(ctx, t, tl, st, f, look):
    skin, hair, top, bottom, shoes, style = look
    top = st.params.get('color', top)
    hair = st.params.get('hair', hair)
    x, y, facing = _place(st, f)
    s = st.params.get('size', 0.36)
    P = _pose(st.words[1], t + (x * 3.1), tl, st.t1 - st.t0)
    yb = y - (P['bob'] + P['lift'] + 0.28 * P['sit']) * s
    piece = lambda: Local(ctx.piece(), x, yb, s, facing)
    hip = (0.0, -0.3)
    shoulder = (0.02, -0.6)

    def leg(L, a, col_shade=1.0):
        kx, ky = hip[0] + 0.28 * math.sin(a), hip[1] + 0.28 * math.cos(a)
        _limb(L, hip, (kx, ky), 0.075, _dark(bottom, col_shade) if style != 'bun' or bottom != top else _dark(skin, col_shade))
        L.ellipse(kx + 0.03, ky + 0.01, 0.055, 0.03, _dark(shoes, col_shade))

    def arm(L, a, col_shade=1.0):
        hx, hy = shoulder[0] + 0.27 * math.sin(a), shoulder[1] + 0.27 * math.cos(a)
        _limb(L, shoulder, (hx, hy), 0.065, _dark(top, col_shade))
        L.circle(hx, hy, 0.04, _dark(skin, col_shade))
    leg(piece(), P['leg_b'], 0.82)
    arm(piece(), P['arm_b'], 0.82)
    L = piece()
    lean = P['lean']
    sx = lean * 0.3
    if bottom == top:  # dress: rounded shoulders, flared hem
        L.ellipse(0.01 + sx, -0.6, 0.12, 0.06, top)
        L.poly([(-0.11 + sx, -0.6), (0.13 + sx, -0.6), (0.2, -0.27), (-0.18, -0.27)], top)
        L.ellipse(0.01, -0.27, 0.19, 0.03, top)
    else:
        L.ellipse(0.01 + sx, -0.6, 0.12, 0.06, top)
        L.poly([(-0.11 + sx, -0.6), (0.13 + sx, -0.6), (0.13, -0.32), (-0.11, -0.32)], top)
        L.ellipse(0.01, -0.31, 0.12, 0.04, bottom)
    leg(piece(), P['leg_f'])
    # head
    H = piece()
    hx, hy = 0.02 + lean * 0.4, -0.8
    if style == 'curls':
        for dx, dy, r in ((-0.12, -0.02, 0.07), (-0.11, 0.08, 0.06), (0.12, 0.08, 0.06), (-0.04, -0.13, 0.1), (0.07, -0.12, 0.09)):
            H.circle(hx + dx, hy + dy, r, hair)
    elif style == 'bun':
        H.circle(hx - 0.06, hy - 0.17, 0.065, hair)
    H.circle(hx, hy, 0.15, skin)
    Hh = piece()
    if style in ('short', 'curls', 'bun'):
        Hh.poly([(hx - 0.155, hy - 0.01), (hx - 0.1, hy - 0.13), (hx, hy - 0.165), (hx + 0.11, hy - 0.12), (hx + 0.155, hy - 0.03), (hx + 0.06, hy - 0.08), (hx - 0.05, hy - 0.06)], hair)
    elif style == 'bald':
        Hh.ellipse(hx - 0.13, hy - 0.02, 0.03, 0.05, hair)
    # face (flat, part of the head piece above)
    F = piece()
    blink = (t * 0.37 + x) % 1.0 < 0.04
    ey = hy - 0.01 + P['head'] * 0.05
    for ex in (0.035, 0.1):
        if blink:
            F.line([(hx + ex - 0.015, ey), (hx + ex + 0.015, ey)], '#3a2a2a', 0.012)
        else:
            F.circle(hx + ex, ey, 0.017, '#2e2222')
    F.circle(hx + 0.12, hy + 0.05, 0.025, '#f2a0a0')
    F.curve([(hx + 0.04, hy + 0.06), (hx + 0.07, hy + 0.085), (hx + 0.1, hy + 0.06)], '#8a3a3a', 0.012)
    arm(piece(), P['arm_f'])
    held = st.params.get('holds')
    if held:
        a = P['arm_f']
        hx, hy = shoulder[0] + 0.27 * math.sin(a), shoulder[1] + 0.27 * math.cos(a)
        _held(piece(), hx, hy, str(held), t)


def _held(L, hx, hy, what, t):
    """Something in the front hand: lantern balloon flower book gift umbrella."""
    if what == 'lantern':
        L.line([(hx, hy), (hx, hy + 0.05)], '#5a4a3a', 0.012)
        L.poly([(hx - 0.075, hy + 0.05), (hx + 0.075, hy + 0.05), (hx, hy + 0.0)], '#3a3a4a')
        L.poly([(hx - 0.065, hy + 0.05), (hx + 0.065, hy + 0.05), (hx + 0.055, hy + 0.22), (hx - 0.055, hy + 0.22)], '#ffd84a')
        L.ellipse(hx, hy + 0.135, 0.03, 0.05, '#fff6c8')
        L.poly([(hx - 0.07, hy + 0.22), (hx + 0.07, hy + 0.22), (hx + 0.07, hy + 0.25), (hx - 0.07, hy + 0.25)], '#3a3a4a')
    elif what == 'balloon':
        L.line([(hx, hy), (hx + 0.04, hy - 0.75)], '#6a6a6a', 0.006)
        L.ellipse(hx + 0.04, hy - 0.86, 0.08, 0.1, '#f06a6a')
    elif what == 'flower':
        L.line([(hx, hy), (hx + 0.01, hy - 0.12)], '#4f9a45', 0.012)
        for k in range(5):
            ang = k * 1.2566
            L.circle(hx + 0.01 + 0.025 * math.cos(ang), hy - 0.13 + 0.025 * math.sin(ang), 0.022, '#f28bb0')
        L.circle(hx + 0.01, hy - 0.13, 0.018, '#f6c453')
    elif what == 'book':
        L.poly([(hx - 0.05, hy - 0.02), (hx + 0.06, hy - 0.04), (hx + 0.06, hy + 0.06), (hx - 0.05, hy + 0.08)], '#5a7fc4')
    elif what == 'gift':
        L.poly([(hx - 0.05, hy - 0.05), (hx + 0.05, hy - 0.05), (hx + 0.05, hy + 0.05), (hx - 0.05, hy + 0.05)], '#f28bb0')
        L.line([(hx, hy - 0.05), (hx, hy + 0.05)], '#f6d353', 0.015)
    elif what == 'umbrella':
        L.line([(hx, hy), (hx, hy - 0.4)], '#5a4a3a', 0.01)
        L.poly([(hx - 0.22, hy - 0.4), (hx - 0.15, hy - 0.5), (hx, hy - 0.56), (hx + 0.15, hy - 0.5), (hx + 0.22, hy - 0.4)], '#e05a5a')


def _animal(ctx, t, tl, st, f, look):
    fur, belly, ears, tail = look
    fur = st.params.get('color', fur)
    x, y, facing = _place(st, f)
    s = st.params.get('size', 0.22)
    P = _pose(st.words[1], t + x * 2.3, tl, st.t1 - st.t0)
    yb = y - (P['bob'] * 1.5 + P['lift']) * s
    piece = lambda: Local(ctx.piece(), x, yb, s, facing)
    sit = st.words[1] == 'sit'
    legs_y = -0.25

    def legs(L, a, shade):
        for lx in (-0.22, 0.2):
            kx = lx + 0.12 * math.sin(a if lx > 0 else -a)
            L.line([(lx, legs_y), (kx, 0.0)], _dark(fur, shade), 0.09)
    if not sit:
        legs(piece(), P['leg_b'], 0.8)
    # tail
    T = piece()
    if tail == 'long':
        T.curve([(-0.3, -0.38), (-0.5, -0.45), (-0.55, -0.7 + 0.05 * math.sin(t * 3)), (-0.48, -0.8)], fur, 0.07)
    elif tail == 'bushy':
        T.ellipse(-0.45, -0.5 + 0.03 * math.sin(t * 3), 0.17, 0.08, fur, angle=-0.6)
        T.circle(-0.57, -0.6 + 0.03 * math.sin(t * 3), 0.05, belly)
    elif tail == 'short':
        T.ellipse(-0.36, -0.48, 0.08, 0.04, fur, angle=-0.8 + 0.3 * math.sin(t * 9))
    elif tail == 'puff':
        T.circle(-0.33, -0.4, 0.08, '#ffffff')
    B = piece()
    if sit:
        B.ellipse(-0.05, -0.32, 0.2, 0.26, fur)
        B.ellipse(0.03, -0.28, 0.1, 0.17, belly)
        B.ellipse(-0.1, -0.04, 0.14, 0.06, _dark(fur, 0.9))
    else:
        B.ellipse(0.0, -0.36 - P['lean'] * 0.1, 0.33, 0.17, fur)
        B.ellipse(0.04, -0.3, 0.2, 0.08, belly)
    if not sit:
        legs(piece(), P['leg_f'], 1.0)
    hx, hy = (0.12, -0.72) if sit else (0.3, -0.58)
    hy += P['head'] * 0.1
    E = piece()
    if ears == 'pointy':
        for ex in (-0.08, 0.06):
            E.poly([(hx + ex - 0.05, hy - 0.08), (hx + ex + 0.05, hy - 0.1), (hx + ex, hy - 0.25)], fur)
    elif ears == 'long':
        for ex in (-0.06, 0.05):
            E.ellipse(hx + ex, hy - 0.25, 0.045, 0.14, fur, angle=0.15 * ex * 10)
    elif ears == 'round':
        for ex in (-0.1, 0.1):
            E.circle(hx + ex, hy - 0.13, 0.065, fur)
    Hd = piece()
    Hd.circle(hx, hy, 0.17, fur)
    if ears == 'floppy':
        Hd.ellipse(hx - 0.13, hy + 0.0, 0.05, 0.11, _dark(fur, 0.75), angle=0.3)
    Hd.ellipse(hx + 0.08, hy + 0.06, 0.1, 0.07, belly)
    F = piece()
    blink = (t * 0.33 + x) % 1.0 < 0.04
    for ex in (0.02, 0.11):
        if blink:
            F.line([(hx + ex - 0.015, hy - 0.03), (hx + ex + 0.015, hy - 0.03)], '#2a2020', 0.012)
        else:
            F.circle(hx + ex, hy - 0.03, 0.022, '#2a2020')
    F.circle(hx + 0.16, hy + 0.04, 0.03, '#3a2828')


def _bird(ctx, t, tl, st, f):
    x, y, facing = _place(st, f)
    s = st.params.get('size', 0.1)
    col = st.params.get('color', '#f2c14e')
    flap = math.sin(t * 2 * math.pi * 3) if st.words[1] == 'fly' else 0.2
    yb = y + 0.01 * math.sin(t * 5)
    piece = lambda: Local(ctx.piece(), x, yb, s, facing)
    piece().ellipse(-0.05, -0.5 - 0.25 * flap, 0.22, 0.09, _dark(col, 0.8), angle=-0.6 * flap)
    B = piece()
    B.ellipse(0, -0.5, 0.3, 0.2, col)
    B.circle(0.25, -0.62, 0.15, col)
    B.poly([(0.38, -0.64), (0.5, -0.6), (0.38, -0.56)], '#f08a3a')
    piece().circle(0.28, -0.65, 0.03, '#2a2020')
    piece().ellipse(0.0, -0.5 + 0.25 * flap, 0.22, 0.09, _dark(col, 1.05), angle=0.6 * flap)


for _n, _look in PEOPLE.items():
    actor(_n, PERSON_ACTIONS)(lambda ctx, t, tl, st, f, _look=_look: _person(ctx, t, tl, st, f, _look))
for _n, _look in ANIMALS.items():
    actor(_n, ANIMAL_ACTIONS)(lambda ctx, t, tl, st, f, _look=_look: _animal(ctx, t, tl, st, f, _look))
actor('bird', ['fly', 'stand'])(_bird)
