"""Felt characters. Each body part is drawn on its own piece (ctx.piece()), so the felt pass gives every piece its own
rounded edge and shadow, like an applique. Local units: 1 = the character's height, feet at v=0, top of the head near v=-1."""
import math
from .draw import Local

FA = {}
PEOPLE = {  # skin, hair, top, bottom, shoes, hair style, outfit, extra
    'girl': ('#f7dcc4', '#8a5a3a', '#e8708e', '#f6c453', '#5a3a2a', 'bob', 'coat', ''),
    'boy': ('#efc9a6', '#3a2a22', '#f2a541', '#4a6aa8', '#7a4a2a', 'short', 'suit', ''),
    'mom': ('#f5d6bc', '#8a4a2a', '#e06c8c', '#e06c8c', '#6a3a2a', 'bun', 'dress', ''),
    'dad': ('#e8bd98', '#3a2a22', '#5f9e6e', '#45506a', '#3a2a22', 'short', 'suit', ''),
    'granny': ('#f3dcc8', '#d8d8dc', '#9b7bc4', '#9b7bc4', '#6a5a7a', 'bun', 'dress', 'glasses'),
    'grandpa': ('#ecc9a9', '#cfcfd4', '#c9834f', '#5a5a64', '#3a2a22', 'bald', 'suit', 'moustache'),
}
ANIMALS = {  # fur, belly, ears, tail, muzzle, feet: everything else comes from the shared base in _animal
    'cat': ('#9aa0ad', '#eef0f4', 'pointy', 'long', 'cat', ''),
    'fox': ('#ec8a3e', '#fbf1e2', 'pointy', 'bushy', 'fox', ''),
    'dog': ('#c99a62', '#f4e6cf', 'floppy', 'short', 'dog', ''),
    'bunny': ('#f2eee8', '#ffd9e2', 'long', 'puff', 'bunny', ''),
    'bear': ('#9a6a46', '#d9b48a', 'round', 'none', 'bear', ''),
    'hedgehog': ('#c9a27a', '#f4e6cf', 'small', 'spines', 'hedgehog', ''),
    'mouse': ('#b9aca0', '#f1e8e0', 'big', 'thin', 'mouse', ''),
    'frog': ('#7cc45a', '#dcf2ae', 'bulge', 'none', 'frog', ''),
    'hen': ('#f4e2c0', '#fff7e6', 'comb', 'feathers', 'beak', '#f08a3a'),  # feet: two feet of this colour instead of four legs
    'elephant': ('#9aa6c8', '#d8dfee', 'flap', 'thin', 'trunk', ''),
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


def _mix(a, b, k):
    return '#%02x%02x%02x' % tuple(int(int(a[i:i + 2], 16) * (1 - k) + int(b[i:i + 2], 16) * k) for i in (1, 3, 5))


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


def _doll_body(piece, outfit, top, bottom, sx):
    """The clothes, in simple coloured layers: coat over a dress, shirt and trousers, or a dress with a belt."""
    if outfit == 'coat':
        piece().poly([(-0.09 + sx, -0.58), (0.12 + sx, -0.58), (0.23, -0.25), (-0.2, -0.25)], bottom)
        piece().poly([(-0.1 + sx, -0.59), (-0.005 + sx, -0.59), (-0.03, -0.27), (-0.2, -0.27)], top)
        piece().poly([(0.05 + sx, -0.59), (0.13 + sx, -0.59), (0.22, -0.27), (0.075, -0.27)], top)
        Bt = piece()
        for by in (-0.5, -0.42, -0.34):
            Bt.circle(0.025 + sx * (1 + by), by, 0.017, '#3a2a2a')
    elif outfit == 'suit':
        piece().poly([(-0.11 + sx, -0.59), (0.14 + sx, -0.59), (0.15, -0.26), (-0.12, -0.26)], top)
        piece().poly([(-0.125, -0.31), (0.155, -0.31), (0.155, -0.25), (-0.125, -0.25)], bottom)
        Bt = piece()
        for by in (-0.5, -0.42):
            Bt.circle(0.015 + sx * (1 + by), by, 0.015, _dark(top, 0.6))
    else:
        piece().poly([(-0.1 + sx, -0.59), (0.13 + sx, -0.59), (0.24, -0.2), (-0.21, -0.2)], top)
        piece().poly([(-0.135 + sx * 0.5, -0.45), (0.165 + sx * 0.5, -0.45), (0.175, -0.4), (-0.145, -0.4)], _mix(top, '#ffffff', 0.55))


def _doll_head(piece, hx, hy, skin, hair, style, extra, ey, blink):
    """Every person has the same head: an oval face, hair in one layer, button eyes, round cheeks. Only the hair and extras differ."""
    if style in ('bob', 'bun'):
        Hb = piece()
        Hb.ellipse(hx - 0.005, hy - 0.005, 0.19, 0.18, hair)
        if style == 'bob':
            Hb.ellipse(hx - 0.12, hy + 0.1, 0.085, 0.075, hair)
            Hb.ellipse(hx + 0.13, hy + 0.1, 0.08, 0.075, hair)
        else:
            piece().circle(hx - 0.02, hy - 0.2, 0.075, hair)
    elif style == 'short':
        piece().ellipse(hx + 0.005, hy - 0.02, 0.16, 0.165, hair)
    elif style == 'bald':
        Hb = piece()
        Hb.ellipse(hx - 0.13, hy + 0.0, 0.05, 0.07, hair)
        Hb.ellipse(hx + 0.145, hy + 0.0, 0.05, 0.07, hair)
    piece().ellipse(hx + 0.01, hy + 0.025, 0.135, 0.15, skin)
    if style in ('bob', 'bun'):
        piece().ellipse(hx + 0.005, hy - 0.1, 0.165, 0.072, hair)
    elif style == 'short':
        piece().ellipse(hx + 0.015, hy - 0.105, 0.135, 0.052, hair)
    F = piece()
    for ex in (-0.035, 0.065):
        if blink:
            F.line([(hx + ex - 0.018, ey), (hx + ex + 0.018, ey)], '#3a2a2a', 0.012)
        else:
            F.ellipse(hx + ex, ey, 0.019, 0.024, '#2a2020')
            F.circle(hx + ex + 0.006, ey - 0.008, 0.006, '#ffffff')
    for ex in (-0.075, 0.105):
        F.circle(hx + ex, hy + 0.075, 0.027, '#f4a0aa')
    if extra == 'moustache':
        F.ellipse(hx - 0.01, hy + 0.08, 0.04, 0.016, hair)
        F.ellipse(hx + 0.05, hy + 0.08, 0.04, 0.016, hair)
    else:
        F.curve([(hx + 0.0, hy + 0.085), (hx + 0.015, hy + 0.105), (hx + 0.035, hy + 0.085)], '#8a3a3a', 0.01)
    if extra == 'glasses':
        for ex in (-0.035, 0.065):
            for k in range(14):
                a_ = k * 0.449
                F.circle(hx + ex + 0.04 * math.cos(a_), ey + 0.04 * math.sin(a_), 0.005, '#5a4a6a')
        F.line([(hx + 0.005, ey), (hx + 0.025, ey)], '#5a4a6a', 0.008)


def _doll(ctx, t, tl, st, f, look):
    """The base of every person, a felt doll: oval face, one layer of hair, clothes in coloured layers, soft limbs, mittens.
    People differ only by colours, hair, outfit and one extra (glasses, moustache)."""
    skin, hair, top, bottom, shoes, style, outfit, extra = look
    top = st.params.get('color', top)
    hair = st.params.get('hair', hair)
    x, y, facing = _place(st, f)
    s = st.params.get('size', 0.36)
    P = _pose(st.words[1], t + (x * 3.1), tl, st.t1 - st.t0)
    yb = y - (P['bob'] + P['lift'] + 0.28 * P['sit']) * s
    piece = lambda: Local(ctx.piece(), x, yb, s, facing)
    hip, shoulder = (0.01, -0.3), (0.02, -0.56)
    legs_col = {'coat': _dark(bottom, 0.92), 'suit': bottom}.get(outfit, skin)

    def leg(a, shade, dx):
        L = piece()
        h = (hip[0] + dx, hip[1])
        kx, ky = h[0] + 0.27 * math.sin(a), h[1] + 0.27 * math.cos(a)
        L.line([h, (kx, ky)], _dark(legs_col, shade), 0.09)
        L.ellipse(kx + 0.025, ky - 0.005, 0.065, 0.045, _dark(shoes, shade))
        L.line([(kx - 0.035, ky - 0.05), (kx + 0.04, ky - 0.05)], _dark(shoes, shade), 0.035)

    def arm(a, shade):
        L = piece()
        ax, ay = shoulder[0] + 0.24 * math.sin(a), shoulder[1] + 0.24 * math.cos(a)
        L.line([shoulder, (ax, ay)], _dark(top, shade), 0.085)
        L.ellipse(ax, ay + 0.01, 0.045, 0.05, _dark(skin, shade))
        return ax, ay
    legs_b, legs_f = (P['leg_b'], P['leg_f']) if st.words[1] not in ('stand', 'wave', 'look_up') else (0.0, 0.0)
    leg(legs_b, 0.85, -0.055)
    arm(P['arm_b'], 0.85)
    leg(legs_f, 1.0, 0.06)
    sx = P['lean'] * 0.3
    _doll_body(piece, outfit, top, bottom, sx)
    hx, hy = 0.02 + P['lean'] * 0.4, -0.78
    _doll_head(piece, hx, hy, skin, hair, style, extra, hy + 0.02 + P['head'] * 0.05, (t * 0.37 + x) % 1.0 < 0.04)
    ax, ay = arm(P['arm_f'], 1.0)
    held = st.params.get('holds')
    if held:
        _held(piece(), ax, ay, str(held), t)


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


def _ears_pointy(E, Ei, hx, hy, hr, fur, belly):
    for ex in (-0.13, 0.11):
        E.poly([(hx + ex - 0.09, hy - hr * 0.55), (hx + ex + 0.09, hy - hr * 0.62), (hx + ex, hy - hr - 0.12)], fur)
        Ei.poly([(hx + ex - 0.045, hy - hr * 0.68), (hx + ex + 0.045, hy - hr * 0.72), (hx + ex, hy - hr - 0.05)], belly)


def _ears_long(E, Ei, hx, hy, hr, fur, belly):
    for ex in (-0.08, 0.08):
        E.ellipse(hx + ex, hy - hr - 0.14, 0.065, 0.19, fur, angle=ex * 1.5)
        Ei.ellipse(hx + ex, hy - hr - 0.13, 0.03, 0.13, '#f4b8c4', angle=ex * 1.5)


def _ears_round(E, Ei, hx, hy, hr, fur, belly):
    for ex in (-0.17, 0.17):
        E.circle(hx + ex, hy - hr * 0.8, 0.09, fur)
        Ei.circle(hx + ex, hy - hr * 0.8, 0.045, belly)


def _ears_floppy(E, Ei, hx, hy, hr, fur, belly):
    for ex in (-1, 1):
        E.ellipse(hx + ex * (hr - 0.02), hy + 0.02, 0.07, 0.15, _dark(fur, 0.72), angle=-0.25 * ex)


def _tail_long(T, x, y, t, fur, belly):
    T.curve([(x + 0.04, y), (x - 0.14, y - 0.04), (x - 0.18, y - 0.28 + 0.04 * math.sin(t * 3)), (x - 0.1, y - 0.36)], fur, 0.085)


def _tail_bushy(T, x, y, t, fur, belly):
    w = 0.04 * math.sin(t * 3)
    T.ellipse(x - 0.08, y - 0.12 + w, 0.18, 0.1, fur, angle=-0.7)
    T.ellipse(x - 0.2, y - 0.26 + w, 0.07, 0.06, belly, angle=-0.7)


def _tail_short(T, x, y, t, fur, belly):
    T.ellipse(x, y - 0.08, 0.09, 0.05, fur, angle=-0.8 + 0.3 * math.sin(t * 9))


def _tail_puff(T, x, y, t, fur, belly):
    T.circle(x + 0.02, y + 0.02, 0.09, '#ffffff')


def _tail_none(T, x, y, t, fur, belly):
    pass


def _muzzle_cat(M, F, hx, hy, hr, belly, fur):
    M.ellipse(hx + 0.03, hy + hr * 0.4, hr * 0.38, hr * 0.27, belly)
    F.poly([(hx + 0.0, hy + hr * 0.2), (hx + 0.06, hy + hr * 0.2), (hx + 0.03, hy + hr * 0.32)], '#e88aa3')
    F.curve([(hx - 0.01, hy + hr * 0.46), (hx + 0.03, hy + hr * 0.54), (hx + 0.07, hy + hr * 0.46)], '#3a2828', 0.011)
    _whiskers(F, hx, hy, hr)


def _muzzle_fox(M, F, hx, hy, hr, belly, fur):
    M.ellipse(hx - hr * 0.36, hy + hr * 0.36, hr * 0.42, hr * 0.32, belly)
    M.ellipse(hx + hr * 0.56, hy + hr * 0.36, hr * 0.42, hr * 0.32, belly)
    M.poly([(hx - hr * 0.5, hy + hr * 0.5), (hx + hr * 0.7, hy + hr * 0.5), (hx + 0.05, hy + hr * 0.9)], belly)
    F.ellipse(hx + 0.05, hy + hr * 0.42, 0.04, 0.03, '#2a2020')


def _muzzle_dog(M, F, hx, hy, hr, belly, fur):
    M.ellipse(hx + 0.03, hy + hr * 0.44, hr * 0.58, hr * 0.4, belly)
    F.ellipse(hx + 0.03, hy + hr * 0.24, 0.058, 0.04, '#2a2020')
    F.line([(hx + 0.03, hy + hr * 0.36), (hx + 0.03, hy + hr * 0.5)], '#3a2828', 0.011)
    F.curve([(hx - 0.05, hy + hr * 0.52), (hx + 0.03, hy + hr * 0.64), (hx + 0.11, hy + hr * 0.52)], '#3a2828', 0.012)


def _muzzle_bunny(M, F, hx, hy, hr, belly, fur):
    M.ellipse(hx + 0.03, hy + hr * 0.4, hr * 0.34, hr * 0.26, '#ffffff')
    F.ellipse(hx + 0.03, hy + hr * 0.26, 0.03, 0.022, '#e88aa3')
    F.line([(hx + 0.03, hy + hr * 0.34), (hx + 0.03, hy + hr * 0.46)], '#3a2828', 0.009)
    F.poly([(hx + 0.008, hy + hr * 0.47), (hx + 0.052, hy + hr * 0.47), (hx + 0.052, hy + hr * 0.6), (hx + 0.008, hy + hr * 0.6)], '#ffffff')
    F.line([(hx + 0.03, hy + hr * 0.47), (hx + 0.03, hy + hr * 0.6)], '#c8c0c8', 0.005)


def _muzzle_bear(M, F, hx, hy, hr, belly, fur):
    M.ellipse(hx + 0.03, hy + hr * 0.42, hr * 0.5, hr * 0.42, belly)
    F.ellipse(hx + 0.03, hy + hr * 0.26, 0.05, 0.034, '#3a2828')
    F.curve([(hx - 0.02, hy + hr * 0.54), (hx + 0.03, hy + hr * 0.63), (hx + 0.08, hy + hr * 0.54)], '#3a2828', 0.012)


def _ears_small(E, Ei, hx, hy, hr, fur, belly):
    for ex in (-0.15, 0.17):
        E.circle(hx + ex, hy - hr * 0.8, 0.06, fur)
        Ei.circle(hx + ex, hy - hr * 0.8, 0.03, belly)


def _ears_big(E, Ei, hx, hy, hr, fur, belly):
    for ex in (-0.2, 0.22):
        E.circle(hx + ex, hy - hr * 0.8, 0.15, fur)
        Ei.circle(hx + ex, hy - hr * 0.8, 0.09, '#f4b8c4')


def _ears_bulge(E, Ei, hx, hy, hr, fur, belly):
    """No ears: the bumps on a frog's head that hold its eyes."""
    for ex in (-0.11, 0.15):
        E.circle(hx + ex, hy - hr * 0.72, 0.105, fur)
        Ei.circle(hx + ex, hy - hr * 0.72, 0.072, '#ffffff')


def _ears_comb(E, Ei, hx, hy, hr, fur, belly):
    """No ears: a hen's red comb."""
    for ex, dy in ((-0.08, 0.0), (0.0, 0.03), (0.08, 0.0)):
        E.circle(hx + ex, hy - hr - dy, 0.065, '#e0526f')


def _ears_flap(E, Ei, hx, hy, hr, fur, belly):
    for ex in (-0.27, 0.31):
        E.ellipse(hx + ex, hy - 0.02, 0.2, 0.25, _dark(fur, 0.9))
        Ei.ellipse(hx + ex, hy - 0.01, 0.12, 0.16, '#f4c8d4')


def _tail_thin(T, x, y, t, fur, belly):
    T.curve([(x + 0.04, y), (x - 0.12, y + 0.02), (x - 0.22, y - 0.1 + 0.04 * math.sin(t * 3)), (x - 0.3, y - 0.02)], _mix(fur, '#f4b8c4', 0.4), 0.04)


def _tail_feathers(T, x, y, t, fur, belly):
    for k, a in enumerate((-1.0, -0.65, -0.3)):
        T.ellipse(x - 0.04, y - 0.1 - 0.05 * k, 0.17, 0.07, _dark(fur, 0.92), angle=a)


def _tail_spines(T, x, y, t, fur, belly):
    """No tail: a hedgehog's coat of spines, behind its body and head."""
    cx, cy, n = x + 0.24, y - 0.1, 22
    pts = []
    for k in range(2 * n):
        a = math.pi * k / n
        r = 0.56 if k % 2 == 0 else 0.44
        pts.append((cx + r * math.cos(a), cy + r * 0.86 * math.sin(a)))
    T.poly(pts, _dark(fur, 0.55))


def _whiskers(F, hx, hy, hr, col='#5a5a66'):
    for sgn, ex in ((-1, -0.09), (1, 0.15)):
        for dy in (0.02, 0.07):
            F.line([(hx + ex, hy + hr * 0.3 + dy), (hx + ex + sgn * 0.13, hy + hr * 0.27 + dy * 1.6)], col, 0.007)


def _muzzle_hedgehog(M, F, hx, hy, hr, belly, fur):
    M.ellipse(hx + 0.05, hy + hr * 0.42, hr * 0.46, hr * 0.32, belly)
    F.circle(hx + 0.05, hy + hr * 0.28, 0.04, '#2a2020')
    F.curve([(hx + 0.0, hy + hr * 0.52), (hx + 0.05, hy + hr * 0.6), (hx + 0.1, hy + hr * 0.52)], '#3a2828', 0.011)


def _muzzle_mouse(M, F, hx, hy, hr, belly, fur):
    M.ellipse(hx + 0.03, hy + hr * 0.42, hr * 0.34, hr * 0.26, belly)
    F.circle(hx + 0.03, hy + hr * 0.3, 0.03, '#e88aa3')
    F.curve([(hx - 0.01, hy + hr * 0.5), (hx + 0.03, hy + hr * 0.57), (hx + 0.07, hy + hr * 0.5)], '#3a2828', 0.01)
    _whiskers(F, hx, hy, hr)


def _muzzle_frog(M, F, hx, hy, hr, belly, fur):
    F.circle(hx - 0.0, hy + hr * 0.08, 0.012, '#3a5a2a')
    F.circle(hx + 0.06, hy + hr * 0.08, 0.012, '#3a5a2a')
    F.curve([(hx - 0.14, hy + hr * 0.28), (hx + 0.03, hy + hr * 0.62), (hx + 0.2, hy + hr * 0.28)], '#2f6a3a', 0.016)


def _muzzle_beak(M, F, hx, hy, hr, belly, fur):
    M.poly([(hx - 0.04, hy + hr * 0.14), (hx + 0.12, hy + hr * 0.14), (hx + 0.04, hy + hr * 0.5)], '#f08a3a')
    F.ellipse(hx + 0.04, hy + hr * 0.66, 0.035, 0.05, '#e0526f')


def _muzzle_trunk(M, F, hx, hy, hr, belly, fur):
    M.curve([(hx + 0.03, hy + hr * 0.1), (hx + 0.05, hy + hr * 0.8), (hx + 0.2, hy + hr * 1.2), (hx + 0.32, hy + hr * 0.95)], _mix(fur, belly, 0.2), 0.12, n=30)
    for k in (0.35, 0.55, 0.75):
        F.line([(hx - 0.02, hy + hr * k), (hx + 0.09, hy + hr * k)], _dark(fur, 0.75), 0.008)


EARS = {'pointy': _ears_pointy, 'long': _ears_long, 'round': _ears_round, 'floppy': _ears_floppy, 'small': _ears_small,
        'big': _ears_big, 'bulge': _ears_bulge, 'comb': _ears_comb, 'flap': _ears_flap}
TAILS = {'long': _tail_long, 'bushy': _tail_bushy, 'short': _tail_short, 'puff': _tail_puff, 'none': _tail_none,
         'thin': _tail_thin, 'feathers': _tail_feathers, 'spines': _tail_spines}
MUZZLES = {'cat': _muzzle_cat, 'fox': _muzzle_fox, 'dog': _muzzle_dog, 'bunny': _muzzle_bunny, 'bear': _muzzle_bear,
           'hedgehog': _muzzle_hedgehog, 'mouse': _muzzle_mouse, 'frog': _muzzle_frog, 'beak': _muzzle_beak, 'trunk': _muzzle_trunk}


def _eyes(F, hx, hy, hr, x, t, gaps=(-0.07, 0.12)):
    """Button eyes with a glint, the same for every animal and bird; they blink now and then."""
    blink = (t * 0.33 + x) % 1.0 < 0.04
    ey = hy - hr * 0.12
    for ex in gaps:
        if blink:
            F.line([(hx + ex - 0.025, ey), (hx + ex + 0.025, ey)], '#2a2020', 0.016)
        else:
            F.circle(hx + ex, ey, 0.04, '#231a1a')
            F.circle(hx + ex + 0.013, ey - 0.014, 0.012, '#ffffff')


def _animal(ctx, t, tl, st, f, look):
    """The base of every animal: a big round head, a small body with a pale belly, short thick legs with pads, button eyes
    and round cheeks. An animal is only its colours, ears, tail, muzzle and, for a hen, two feet."""
    fur, belly, ears, tail, muzzle, feet = look
    fur = st.params.get('color', fur)
    x, y, facing = _place(st, f)
    s = st.params.get('size', 0.22)
    P = _pose(st.words[1], t + x * 2.3, tl, st.t1 - st.t0)
    yb = y - (P['bob'] * 1.5 + P['lift']) * s
    piece = lambda: Local(ctx.piece(), x, yb, s, facing)
    sit = st.words[1] == 'sit'
    paw = _mix(belly, fur, 0.35)
    moving = st.words[1] in ('walk', 'run')
    step = math.sin((t + x * 2.3) * 2 * math.pi * (2.6 if st.words[1] == 'run' else 1.6)) if moving else 0.0

    def stub(L, cx, lift, shade):
        L.ellipse(cx, -0.1 - lift, 0.075, 0.11, _dark(fur, shade))
        L.ellipse(cx + 0.01, -0.02 - lift, 0.07, 0.035, _dark(paw, shade))
    if sit:
        bx, by, brx, bry = -0.02, -0.3, 0.22, 0.25
        hx, hy, hr = 0.05, -0.72, 0.27
    else:
        bx, by, brx, bry = -0.04, -0.33 - P['lean'] * 0.1, 0.28, 0.2
        hx, hy, hr = 0.2, -0.66, 0.26
    hy += P['head'] * 0.12
    if not sit and not feet:
        Lb = piece()
        stub(Lb, -0.2, max(0, -step) * 0.05, 0.8)
        stub(Lb, 0.1, max(0, step) * 0.05, 0.8)
    TAILS[tail](piece(), bx - brx, by, t, fur, belly)
    piece().ellipse(bx, by, brx, bry, fur)
    piece().ellipse(bx + 0.06, by + 0.04, brx * 0.58, bry * 0.66, belly)
    if feet:
        for cx, lift in ((bx - 0.06, max(0, step)), (bx + 0.14, max(0, -step))):
            L1 = piece()
            L1.ellipse(cx, -0.09 - lift * 0.05, 0.035, 0.08, feet)
            L1.ellipse(cx + 0.03, -0.025 - lift * 0.05, 0.08, 0.03, feet)
    elif sit:
        piece().ellipse(bx - 0.13, -0.07, 0.13, 0.075, _dark(fur, 0.9))
        for cx in (bx + 0.0, bx + 0.17):
            L1 = piece()
            L1.ellipse(cx, -0.1, 0.062, 0.1, fur)
            L1.ellipse(cx + 0.01, -0.025, 0.06, 0.032, paw)
    else:
        Lf = piece()
        stub(Lf, -0.13, max(0, step) * 0.05, 1.0)
        stub(Lf, 0.17, max(0, -step) * 0.05, 1.0)
    if ears != 'floppy':
        EARS[ears](piece(), piece(), hx, hy, hr, fur, belly)
    piece().circle(hx, hy, hr, fur)
    if ears == 'floppy':
        EARS[ears](piece(), piece(), hx, hy, hr, fur, belly)
    M, F = piece(), piece()
    MUZZLES[muzzle](M, F, hx, hy, hr, belly, fur)
    if ears == 'bulge':
        _eyes(F, hx, hy - hr * 0.6, hr, x, t, gaps=(-0.11, 0.15))
    else:
        _eyes(F, hx, hy, hr, x, t)
    for ex in (-0.15, 0.2):
        F.circle(hx + ex, hy + hr * 0.3, 0.04, '#f4a6b4')


def _bird(ctx, t, tl, st, f):
    """A bird on the same base: a big round head, a small body with a pale belly, button eye, cheek; a wing and a beak instead of legs and muzzle."""
    x, y, facing = _place(st, f)
    s = st.params.get('size', 0.1)
    col = st.params.get('color', '#f2c14e')
    fly = st.words[1] == 'fly'
    flap = math.sin(t * 2 * math.pi * 3) if fly else 0.2
    yb = y + 0.01 * math.sin(t * 5)
    piece = lambda: Local(ctx.piece(), x, yb, s, facing)
    hx, hy, hr = 0.2, -0.68, 0.27
    if not fly:
        Lg = piece()
        for cx in (-0.08, 0.08):
            Lg.ellipse(cx, -0.04, 0.08, 0.04, '#f08a3a')
    piece().poly([(-0.18, -0.46), (-0.5, -0.6), (-0.46, -0.32)], _dark(col, 0.8))
    piece().ellipse(-0.02, -0.34, 0.3, 0.27, col)
    piece().ellipse(0.05, -0.28, 0.17, 0.17, _mix(col, '#ffffff', 0.7))
    piece().circle(hx, hy, hr, col)
    piece().poly([(hx + hr * 0.75, hy - 0.04), (hx + hr + 0.17, hy + 0.04), (hx + hr * 0.75, hy + 0.11)], '#f08a3a')
    piece().ellipse(-0.08, -0.38 - 0.16 * flap, 0.2, 0.1, _dark(col, 0.82), angle=-0.5 * flap)
    F = piece()
    _eyes(F, hx, hy, hr, x, t, gaps=(0.08,))
    F.circle(hx - 0.04, hy + hr * 0.3, 0.04, '#f4a6b4')


for _n, _look in PEOPLE.items():
    actor(_n, PERSON_ACTIONS)(lambda ctx, t, tl, st, f, _look=_look: _doll(ctx, t, tl, st, f, _look))
for _n, _look in ANIMALS.items():
    actor(_n, ANIMAL_ACTIONS)(lambda ctx, t, tl, st, f, _look=_look: _animal(ctx, t, tl, st, f, _look))
actor('bird', ['fly', 'stand'])(_bird)
