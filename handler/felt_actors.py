"""Felt characters. Each body part is drawn on its own piece (ctx.piece()), so the felt pass gives every piece its own
rounded edge and shadow, like an applique. Local units: 1 = the character's height, feet at v=0, top of the head near v=-1."""
import math
from .draw import Local, bezier, ease

FA = {}
PEOPLE = {  # skin, hair, top, bottom, shoes, hair style, outfit, extra
    'girl': ('#f7dcc4', '#8a5a3a', '#e8708e', '#f6c453', '#5a3a2a', 'bob', 'coat', ''),
    'boy': ('#efc9a6', '#3a2a22', '#f2a541', '#4a6aa8', '#7a4a2a', 'short', 'suit', ''),
    'mom': ('#f5d6bc', '#8a4a2a', '#e06c8c', '#e06c8c', '#6a3a2a', 'bun', 'dress', ''),
    'dad': ('#e8bd98', '#3a2a22', '#5f9e6e', '#45506a', '#3a2a22', 'short', 'suit', ''),
    'granny': ('#f3dcc8', '#d8d8dc', '#9b7bc4', '#9b7bc4', '#6a5a7a', 'bun', 'dress', 'glasses'),
    'grandpa': ('#ecc9a9', '#cfcfd4', '#c9834f', '#5a5a64', '#3a2a22', 'bald', 'suit', 'moustache'),
    'doctor': ('#f3d6bc', '#3a2a22', '#f4f6f8', '#7fb6e8', '#4a5a6a', 'short', 'coat', 'doctor'),
}
ANIMALS = {  # fur, belly, ears, tail, muzzle, feet: everything else comes from the shared base in _animal
    'cat': ('#9aa0ad', '#eef0f4', 'pointy', 'long', 'cat', ''),
    'fox': ('#ec8a3e', '#fbf1e2', 'pointy', 'bushy', 'fox', ''),
    'dog': ('#c99a62', '#f4e6cf', 'floppy', 'short', 'dog', ''),
    'bunny': ('#f2eee8', '#ffd9e2', 'long', 'puff', 'bunny', ''),
    'bear': ('#9a6a46', '#d9b48a', 'round', 'none', 'bear', ''),
    'hedgehog': ('#6b4a36', '#f4e6cf', 'small', 'tufts', 'snout', ''),  # fur is the coat of spines; color= changes it
    'mouse': ('#b9aca0', '#f1e8e0', 'big', 'thin', 'mouse', ''),
    'frog': ('#7cc45a', '#dcf2ae', 'bulge', 'none', 'frog', ''),
    'hen': ('#f4e2c0', '#fff7e6', 'comb', 'feathers', 'beak', '#f08a3a'),  # feet: two feet of this colour instead of four legs
    'elephant': ('#9aa6c8', '#d8dfee', 'flap', 'thin', 'trunk', ''),
}
PAIR_ACTIONS = ['hug', 'give', 'hold_hands']
PERSON_ACTIONS = ['stand', 'walk', 'run', 'wave', 'jump', 'sit', 'dance', 'look_up', 'sleep'] + PAIR_ACTIONS
ANIMAL_ACTIONS = ['stand', 'walk', 'run', 'jump', 'sit', 'look_up', 'sleep'] + PAIR_ACTIONS
HELD = ['lantern', 'balloon', 'flower', 'book', 'gift', 'umbrella', 'ball', 'medicine']
FACE_MOODS = ['happy', 'sad', 'surprised', 'sleepy']
SKINS = {'light': '#f7dcc4', 'tan': '#e3b48c', 'brown': '#b67f55', 'dark': '#7d5236'}
HAIRSTYLES = ['bob', 'bun', 'short', 'bald', 'braids', 'ponytail', 'curly', 'afro']


def actor(name, actions):
    def deco(fn):
        FA[name] = (fn, actions)
        return fn
    return deco


class _Turned(Local):
    """A Local turned by rot radians around (pu, pv), which lands on (tu, tv): a head lying on a pillow."""

    def __init__(self, ctx, x, y, s, flip, rot, pivot, to):
        super().__init__(ctx, x, y, s, flip)
        self.rot, self.pivot, self.to = rot, pivot, to

    def pt(self, u, v):
        du, dv = u - self.pivot[0], v - self.pivot[1]
        c, n = math.cos(self.rot), math.sin(self.rot)
        return super().pt(self.to[0] + du * c - dv * n, self.to[1] + du * n + dv * c)

    def ellipse(self, u, v, ru, rv, color, angle=0.0):
        super().ellipse(u, v, ru, rv, color, angle + self.rot)


def _plain(st, t):
    """Where a line of its own puts the character at time t."""
    from .actors import _lerp_pos
    return _lerp_pos(st, min(1.0, max(0.0, (t - st.t0) / (st.t1 - st.t0))), st.params.get('y', 0.86))


def _line_at(lines, t):
    return next((a for a in lines if a.t0 <= t < a.t1), None) or min(lines, key=lambda a: min(abs(t - a.t0), abs(t - a.t1)))


def _pair_of(st, t):
    """The hug, give or hold_hands this line takes part in at time t: its own, or the one where it is the partner."""
    if st.words[1] in PAIR_ACTIONS:
        return st
    return next((p for p in st.pairs if p.t0 <= t < p.t1), None)


def _size(st):
    return st.params.get('size', 0.36 if st.words[0] in PEOPLE else 0.22)


def _front(st, act):
    """How far the character reaches forward of its x, in its own units."""
    if st.words[0] in PEOPLE:
        return 0.2
    return 0.3 if act == 'sit' else 0.42


def _rear(st, act):
    """How far the character reaches behind its x, in its own units."""
    return 0.22 if act == 'sit' else 0.28


def _from_behind(p):
    """An animal is hugged from behind, with an arm round its body: a hug from the front would cover its muzzle."""
    return p.words[1] == 'hug' and p.words[2] not in PEOPLE


def _pair_slide(p):
    return min(0.45, (p.t1 - p.t0) * 0.3)


def _pair_x(p, t):
    """The one who starts a pair action comes up to the partner at the start and, if it has a next line, goes to it at the end."""
    m = _line_at(p.mates, t)
    mx = _plain(m, t)[0]
    home = p.home[0]
    reach = _front(p, 'stand') * _size(p) + (_rear if _from_behind(p) else _front)(m, m.words[1]) * _size(m)
    near = {'hug': reach * 0.85, 'give': reach + 0.2 * min(_size(p), _size(m)), 'hold_hands': reach + 0.3 * min(_size(p), _size(m))}[p.words[1]]
    spot = mx + (1 if home >= mx else -1) * near * p.ar
    slide = _pair_slide(p)
    if t < p.t0 + slide:
        return home + (spot - home) * ease((t - p.t0) / slide)
    if p.after is not None and t > p.t1 - slide:
        return p.after + (spot - p.after) * ease((p.t1 - t) / slide)
    return spot


def _act(st, t):
    """What the body does at time t: in a pair action it stands, or walks while it comes up or goes along with the partner."""
    w = st.words[1]
    if w not in PAIR_ACTIONS:
        return w
    m = _line_at(st.mates, t).words[1]
    if m in ('walk', 'run'):
        return m
    slide = _pair_slide(st)
    return 'walk' if t < st.t0 + slide or (st.after is not None and t > st.t1 - slide) else 'stand'


def _place(st, f):
    from .actors import _lerp_pos, _facing
    t = st.t0 + f * (st.t1 - st.t0)
    if st.words[1] in PAIR_ACTIONS:
        m = _line_at(st.mates, t)
        x, mx = _pair_x(st, t), _plain(m, t)[0]
        if st.words[1] == 'hold_hands' and m.words[1] in ('walk', 'run'):
            return x, st.home[1], _facing(m)
        return x, st.home[1], 1 if mx >= x else -1
    x, y = _lerp_pos(st, f, st.params.get('y', 0.86))
    p = _pair_of(st, t)
    if p and not (p.words[1] == 'hold_hands' and st.words[1] in ('walk', 'run')):
        towards = 1 if _pair_x(p, t) >= x else -1
        return x, y, -towards if _from_behind(p) else towards
    return x, y, _facing(st)


def _shoulder(st, act, x, y, facing, ar):
    """Where an arm or a paw starts, in frame coordinates."""
    if st.words[0] in PEOPLE:
        u, v = 0.02, -0.56
    else:
        u, v = (0.1, -0.42) if act == 'sit' else (0.18, -0.35)
    return x + u * _size(st) * ar * facing, y + v * _size(st)


def _aims(st, t, x, y, facing):
    """Where this character's hands go at time t in a pair action, in its own units: {'front': (u, v), 'back': (u, v)}, and
    'item', what its hand holds during a give. Empty outside a pair action."""
    p = _pair_of(st, t)
    if p is None:
        return {}
    ar, m = p.ar, _line_at(p.mates, t)
    px, (mx, my) = _pair_x(p, t), _plain(m, t)
    a = _shoulder(p, _act(p, t), px, p.home[1], 1 if mx >= px else -1, ar)
    b = _shoulder(m, m.words[1], mx, my, 1 if px >= mx else -1, ar)
    mine, other = (a, b) if st is p else (b, a)
    s, so = _size(st), _size(m if st is p else p)
    side = 1 if other[0] >= mine[0] else -1

    def local(fx, fy):
        return (fx - x) / (s * ar * facing), (fy - y) / s
    if _from_behind(p):
        if st is not p:
            return {}
        u, v = -0.02, -0.3
        fx, fy = mx + u * so * ar * side, my + v * so
        return {'front': local(fx, fy), 'back': local(fx + side * 0.1 * so * ar, fy - 0.06 * so)}
    if p.words[1] == 'hug':  # round the other one's back
        fx, fy = other[0] + side * 0.07 * so * ar, other[1] + 0.03 * so
        return {'front': local(fx, fy), 'back': local(fx, fy - 0.08 * so)}
    if p.words[1] == 'hold_hands':
        grip = local((a[0] + b[0]) / 2, max(a[1], b[1]) + 0.16 * min(s, so))
        return {'front' if grip[0] >= 0 else 'back': grip}
    f = (t - p.t0) / (p.t1 - p.t0)
    rest = mine[0] + side * 0.14 * s * ar, mine[1] + 0.2 * s
    meet = (a[0] + b[0]) / 2, max(a[1], b[1]) + 0.04 * min(s, so)
    k = math.sin(math.pi * min(1.0, f))
    return {'front': local(rest[0] + (meet[0] - rest[0]) * k, rest[1] + (meet[1] - rest[1]) * k), 'item': p.words[3] if (st is p) == (f < 0.5) else None}


def _reach(start, hand, longest=0.55):
    """A hand that would pull the arm too long stops at the arm's end."""
    du, dv = hand[0] - start[0], hand[1] - start[1]
    n = math.hypot(du, dv)
    return hand if n <= longest else (start[0] + du * longest / n, start[1] + dv * longest / n)


def _paw(L, start, hand, fur, pad):
    """An animal's arm, drawn only when it is needed: a hug, a hand to hold, something to carry."""
    hand = _reach(start, hand)
    L.line([start, hand], fur, 0.09)
    L.ellipse(hand[0], hand[1], 0.05, 0.045, pad)
    return hand


def _sleeper(ctx, t, st, f, length, head):
    """Lying down: a pillow, a blanket over the body that rises and falls with the breath, the head on the pillow."""
    x, y, facing = _place(st, f)
    s = _size(st)
    piece = lambda: Local(ctx.piece(), x, y, s, facing)
    piece().ellipse(-0.02, -0.07, 0.27, 0.09, '#fbf6ee')
    col = st.params.get('blanket', '#9fc8e8')
    b = 0.014 * math.sin(t * 1.7)
    hump = bezier([(0.1, 0.02), (0.14, -0.4 - b), (length * 0.75, -0.34 - b), (length, 0.02)])
    piece().poly(hump, col)
    piece().curve([(0.15, -0.12), (0.2, -0.26 - b), (0.3, -0.27 - b)], _mix(col, '#ffffff', 0.5), 0.05)
    head(lambda: _Turned(ctx.piece(), x, y, s, facing, -1.3, (0.0, 0.0), (0.0, -0.19)))


def _dark(c, k=0.75):
    return '#%02x%02x%02x' % tuple(int(int(c[i:i + 2], 16) * k) for i in (1, 3, 5))


def _mix(a, b, k):
    return '#%02x%02x%02x' % tuple(int(int(a[i:i + 2], 16) * (1 - k) + int(b[i:i + 2], 16) * k) for i in (1, 3, 5))


def _pose(action, t, tl, dur):
    """Angles in radians (0 = straight down) and body offsets for one moment of an action."""
    ph = t * 2 * math.pi
    P = dict(leg_b=0.12, leg_f=-0.12, arm_b=0.2, arm_f=-0.2, bob=0.004 * math.sin(ph * 0.5), lean=0.0, lift=0.0, sit=0.0, head=0.0, tuck=0.0)
    if action == 'walk':
        sw = math.sin(ph * 1.6)
        P.update(leg_b=0.45 * sw, leg_f=-0.45 * sw, arm_b=-0.5 * sw, arm_f=0.5 * sw, bob=0.012 * abs(math.cos(ph * 1.6)))
    elif action == 'run':
        sw = math.sin(ph * 2.6)
        P.update(leg_b=0.8 * sw, leg_f=-0.8 * sw, arm_b=-0.9 * sw, arm_f=0.9 * sw, bob=0.03 * abs(math.cos(ph * 2.6)), lean=0.12)
    elif action == 'wave':
        P.update(arm_f=2.5 + 0.17 * math.sin(ph * 2.2), arm_b=0.15)  # one hand up, beside the head
    elif action == 'jump':
        k = abs(math.sin(math.pi * ((tl * 1.4) % 1.0)))
        P.update(lift=0.22 * k, arm_b=-2.3 - 0.35 * k, arm_f=2.3 + 0.35 * k, leg_b=-0.12, leg_f=0.12, tuck=k)
    elif action == 'sit':
        P.update(sit=1.0, leg_b=1.45, leg_f=1.45, arm_b=0.35, arm_f=0.55)
    elif action == 'dance':
        sw = math.sin(ph * 1.8)
        P.update(arm_b=-2.35 - 0.32 * sw, arm_f=2.35 - 0.32 * sw, leg_b=0.25 * sw, leg_f=-0.25 * sw, lean=0.12 * sw, bob=0.02 * abs(sw))  # both up, one higher in turn
    elif action == 'look_up':
        P.update(head=-0.35)
    return P


def _mood_eye(F, cx, cy, r, mood, col):
    """surprised: a round white eye with a small pupil; sleepy: a closed eye, an arc that sags in the middle."""
    if mood == 'surprised':
        F.circle(cx, cy, r * 1.7, col)
        F.circle(cx, cy, r * 1.45, '#ffffff')
        F.circle(cx, cy, r * 0.75, col)
    else:
        F.curve([(cx - r * 1.25, cy - r * 0.3), (cx, cy + r * 1.1), (cx + r * 1.25, cy - r * 0.3)], col, r * 0.55)


def _sad_brows(F, xs, y, r, col):
    """Brows like a little roof: the inner ends go up. xs: the eyes; one eye (a bird) has its inner end towards the beak."""
    mid = sum(xs) / len(xs) if len(xs) > 1 else xs[0] + 1
    for cx in xs:
        sgn = 1 if cx < mid else -1
        F.line([(cx - sgn * r * 1.3, y + r * 0.55), (cx + sgn * r * 1.2, y - r * 0.55)], col, r * 0.6)


def _tear(F, x, y, r, t):
    """A tear that rolls down from under the eye, again and again."""
    y += r * 3.2 * ((t * 0.55) % 1.0)
    F.poly([(x, y - r * 1.9), (x + r * 0.8, y - r * 0.35), (x - r * 0.8, y - r * 0.35)], '#6fc0f2')
    F.circle(x, y, r, '#6fc0f2')
    F.circle(x - r * 0.3, y - r * 0.25, r * 0.28, '#ffffff')


def _mouth(F, mood, cx, y, w, d, lw, col='#3a2828', smile=True):
    """The mouth of a mood: a smile (w wide each way, d deep), the same arc turned over, a round 'o', a small quiet line.
    smile=False: this face shows no mouth while it is happy."""
    if mood == 'sad':
        w = min(w * 1.25, 0.13)  # a frog's wide smile, turned over, would run off its face
        F.curve([(cx - w, y + d), (cx, y - d * 0.7), (cx + w, y + d)], col, lw * 1.15)
    elif mood == 'surprised':
        rx = max(0.022, min(w * 0.7, 0.055))
        F.ellipse(cx, y + d * 0.5, rx, rx * 1.3, col)
        F.ellipse(cx, y + d * 0.5 + rx * 0.3, rx * 0.6, rx * 0.75, '#c0505a')
    elif mood == 'sleepy':
        F.curve([(cx - w * 0.6, y + d * 0.4), (cx, y + d * 0.7), (cx + w * 0.6, y + d * 0.4)], col, lw)
    elif smile:
        F.curve([(cx - w, y), (cx, y + d), (cx + w, y)], col, lw)


def _soft(points, r=0.045):
    """A polygon with its corners rounded off, for bodies that look stuffed rather than cut with a ruler."""
    out = []
    for i, (x, y) in enumerate(points):
        ends = []
        for ox, oy in (points[i - 1], points[(i + 1) % len(points)]):
            n = math.hypot(ox - x, oy - y)
            k = min(r, n / 2) / n
            ends.append((x + (ox - x) * k, y + (oy - y) * k))
        out += bezier([ends[0], (x, y), ends[1]], 6)
    return out


def _hand(L, ax, ay, dx, dy, col):
    """A mitten along the arm's direction, with a thumb on the side that faces forward."""
    n = math.hypot(dx, dy) or 1.0
    dx, dy = dx / n, dy / n
    tx, ty = (-dy, dx) if dx * 0 - dy >= 0 else (dy, -dx)
    L.ellipse(ax + dx * 0.018, ay + dy * 0.018, 0.058, 0.043, col, angle=math.atan2(dy, dx))
    L.ellipse(ax + tx * 0.04 + dx * 0.005, ay + ty * 0.04 + dy * 0.005, 0.032, 0.019, col, angle=math.atan2(dy + ty * 0.8, dx + tx * 0.8))


def _doll_body(piece, outfit, top, bottom, sx):
    """The clothes, in simple coloured layers with soft corners: coat over a dress, shirt and trousers, or a dress with a belt."""
    if outfit == 'coat':
        piece().poly(_soft([(-0.09 + sx, -0.58), (0.12 + sx, -0.58), (0.23, -0.25), (-0.2, -0.25)]), bottom)
        piece().poly(_soft([(-0.1 + sx, -0.59), (-0.005 + sx, -0.59), (-0.03, -0.27), (-0.2, -0.27)], 0.03), top)
        piece().poly(_soft([(0.05 + sx, -0.59), (0.13 + sx, -0.59), (0.22, -0.27), (0.075, -0.27)], 0.03), top)
        Bt = piece()
        for by in (-0.5, -0.42, -0.34):
            Bt.circle(0.025 + sx * (1 + by), by, 0.017, '#3a2a2a')
    elif outfit == 'suit':
        piece().poly(_soft([(-0.11 + sx, -0.59), (0.14 + sx, -0.59), (0.15, -0.26), (-0.12, -0.26)]), top)
        piece().poly(_soft([(-0.125, -0.31), (0.155, -0.31), (0.155, -0.25), (-0.125, -0.25)], 0.025), bottom)
        Bt = piece()
        for by in (-0.5, -0.42):
            Bt.circle(0.015 + sx * (1 + by), by, 0.015, _dark(top, 0.6))
    else:
        piece().poly(_soft([(-0.1 + sx, -0.59), (0.13 + sx, -0.59), (0.24, -0.2), (-0.21, -0.2)]), top)
        piece().poly([(-0.135 + sx * 0.5, -0.45), (0.165 + sx * 0.5, -0.45), (0.175, -0.4), (-0.145, -0.4)], _mix(top, '#ffffff', 0.55))


def _doll_head(piece, hx, hy, skin, hair, style, extra, ey, blink, mood, t):
    """Every person has the same head: an oval face, hair in one layer, button eyes, round cheeks. Only the hair and extras differ."""
    if style == 'braids':
        piece().ellipse(hx + 0.005, hy - 0.02, 0.16, 0.165, hair)
        for sgn in (-1, 1):
            B = piece()
            for k in range(4):
                B.circle(hx + 0.012 + sgn * (0.155 + 0.012 * k), hy + 0.06 + 0.058 * k, 0.04 - 0.004 * k, hair)
            piece().circle(hx + 0.012 + sgn * 0.205, hy + 0.27, 0.026, '#e0526f')
    elif style == 'ponytail':
        piece().ellipse(hx - 0.2, hy + 0.03, 0.065, 0.17, hair, angle=0.3)
        piece().ellipse(hx + 0.005, hy - 0.02, 0.165, 0.17, hair)
    elif style == 'curly':
        Hb = piece()
        for k in range(14):
            a_ = math.pi * (0.85 + 1.3 * k / 13)
            Hb.circle(hx + 0.01 + 0.15 * math.cos(a_), hy + 0.0 + 0.16 * math.sin(a_), 0.062, hair)
    elif style == 'afro':
        piece().ellipse(hx + 0.01, hy - 0.05, 0.25, 0.23, hair)
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
    elif style in ('short', 'braids', 'ponytail'):
        piece().ellipse(hx + 0.015, hy - 0.105, 0.135, 0.052, hair)
    elif style == 'afro':
        piece().ellipse(hx + 0.012, hy - 0.11, 0.14, 0.05, hair)
    elif style == 'curly':
        Hf = piece()
        for ex in (-0.09, -0.03, 0.04, 0.1):
            Hf.circle(hx + ex + 0.01, hy - 0.11, 0.045, hair)
    F = piece()
    if mood == 'sad':  # the eyes sit a little lower, so the brows fit under the fringe
        ey += 0.012
        _sad_brows(F, [hx - 0.035, hx + 0.065], ey - 0.042, 0.022, '#3a2a2a')
    for ex in (-0.035, 0.065):
        if mood in ('surprised', 'sleepy'):
            _mood_eye(F, hx + ex, ey, 0.021, mood, '#2a2020')
        elif blink:
            F.line([(hx + ex - 0.018, ey), (hx + ex + 0.018, ey)], '#3a2a2a', 0.012)
        else:
            F.ellipse(hx + ex, ey, 0.019, 0.024, '#2a2020')
            F.circle(hx + ex + 0.006, ey - 0.008, 0.006, '#ffffff')
    deep = int(skin[1:3], 16) < 200  # on darker skin the cheeks are warmer and the mouth darker, so both still show
    for ex in (-0.075, 0.105):
        F.circle(hx + ex, hy + 0.075, 0.027, _mix(skin, '#e8607a', 0.5) if deep else '#f4a0aa')
    if extra == 'moustache':
        F.ellipse(hx - 0.01, hy + 0.08, 0.04, 0.016, hair)
        F.ellipse(hx + 0.05, hy + 0.08, 0.04, 0.016, hair)
        _mouth(F, mood, hx + 0.02, hy + 0.112, 0.0175, 0.02, 0.01, '#4a1c1c' if deep else '#8a3a3a', smile=False)
    else:
        _mouth(F, mood, hx + 0.0175, hy + 0.085, 0.0175, 0.02, 0.01, '#4a1c1c' if deep else '#8a3a3a')
    if extra == 'glasses':
        for ex in (-0.035, 0.065):
            for k in range(14):
                a_ = k * 0.449
                F.circle(hx + ex + 0.04 * math.cos(a_), ey + 0.04 * math.sin(a_), 0.005, '#5a4a6a')
        F.line([(hx + 0.005, ey), (hx + 0.025, ey)], '#5a4a6a', 0.008)
    if mood == 'sad':
        _tear(F, hx - 0.06, ey + 0.045, 0.016, t)
    if extra == 'doctor':  # a white cap with a red cross
        C = piece()
        C.ellipse(hx + 0.012, hy - 0.15, 0.115, 0.055, '#fbfbf6')
        C.line([(hx + 0.012, hy - 0.175), (hx + 0.012, hy - 0.125)], '#e0526f', 0.018)
        C.line([(hx - 0.013, hy - 0.15), (hx + 0.037, hy - 0.15)], '#e0526f', 0.018)


def _doll(ctx, t, tl, st, f, look):
    """The base of every person, a felt doll: oval face, one layer of hair, clothes in coloured layers, soft limbs, mittens.
    People differ only by colours, hair, outfit and one extra (glasses, moustache). Anyone can look different: skin=light|tan|brown|dark
    or #rrggbb, hair=#rrggbb, hairstyle=bob|bun|short|bald|braids|ponytail|curly|afro, color=#rrggbb for the clothes.
    wave: one hand up beside the head; dance: both hands up, one higher in turn; jump: both hands up, legs tucked in the air.
    mood=happy|sad|surprised|sleepy sets the face: happy is the usual smile; sad has roof-like brows, a mouth turned down and
    a tear; surprised has round eyes and an 'o' mouth; sleepy has closed eyes, arcs. A new mood is a new line with its own seconds.
    hug, give and hold_hands work for any two people or animals: 'girl hug cat 3-5s', 'girl give cat ball 2-3s', 'girl hold_hands boy
    3-6s'. The first one comes up to the second, who must be in the frame and within 0.3 of the frame; both turn to each other and
    reach out; an animal is hugged from behind, so its muzzle stays in view. After a give the second one keeps the thing until the scene ends. If the second one walks, hold_hands walks along.
    sleep lies down under a blanket, eyes closed: 'boy sleep 8-14s' on the bed of the scene, 'cat sleep at 0.6 8-14s y=0.97' anywhere."""
    skin, hair, top, bottom, shoes, style, outfit, extra = look
    top = st.params.get('color', top)
    hair = st.params.get('hair', hair)
    skin = SKINS.get(st.params.get('skin'), st.params.get('skin', skin))
    style = st.params.get('hairstyle', style)
    if st.words[1] == 'sleep':
        _sleeper(ctx, t, st, f, 1.0, lambda piece: _doll_head(piece, 0.0, 0.0, skin, hair, style, extra, 0.02, False, st.params.get('mood', 'sleepy'), t))
        return
    x, y, facing = _place(st, f)
    s = st.params.get('size', 0.36)
    act = _act(st, t)
    P = _pose(act, t + (x * 3.1), tl, st.t1 - st.t0)
    mood = st.params.get('mood', 'happy')
    aims = _aims(st, t, x, y, facing)
    if aims and _pair_of(st, t).words[1] == 'hug':
        P['lean'] = 0.1
    yb = y - (P['bob'] + P['lift'] - 0.22 * P['sit']) * s  # sitting: the seat, not the feet, rests on the y line
    piece = lambda: Local(ctx.piece(), x, yb, s, facing)
    hip, shoulder = (0.01, -0.3), (0.02, -0.56)
    legs_col = {'coat': _dark(bottom, 0.92), 'suit': bottom}.get(outfit, skin)

    def leg(a, shade, dx):
        L = piece()
        h = (hip[0] + dx, hip[1])
        up, down = a + 1.05 * P['tuck'], a - 0.75 * P['tuck']  # tucked: the knee forward, the shin back under it
        nx, ny = h[0] + 0.135 * math.sin(up), h[1] + 0.135 * math.cos(up)
        kx, ky = nx + 0.135 * math.sin(down), ny + 0.135 * math.cos(down)
        L.line([h, (nx, ny), (kx, ky)], _dark(legs_col, shade), 0.09)
        if P['sit']:  # legs stretched out in front: the sole faces forward, toes up
            L.ellipse(kx + 0.01, ky - 0.04, 0.045, 0.065, _dark(shoes, shade))
        else:
            L.ellipse(kx + 0.025, ky - 0.005, 0.065, 0.045, _dark(shoes, shade))
            L.line([(kx - 0.035, ky - 0.05), (kx + 0.04, ky - 0.05)], _dark(shoes, shade), 0.035)

    def arm(a, shade, aim=None):
        L = piece()
        if aim:  # reaching for the partner: a soft arm that sags a little on its way
            start = shoulder[0] + 0.07 * (1 if aim[0] >= 0 else -1), shoulder[1]
            ax, ay = _reach(start, aim)
            L.curve([start, ((start[0] + ax) / 2, (start[1] + ay) / 2 + 0.04), (ax, ay)], _dark(top, shade), 0.085)
            _hand(L, ax, ay, ax - start[0], ay - start[1], _dark(skin, shade))
            return ax, ay
        up = min(1.0, max(0.0, (abs(a) - 1.2) / 0.7))  # a raised arm starts at the edge of the body and reaches past the head
        out = math.copysign(up, a)
        sx0, sy0 = shoulder[0] + 0.1 * out + P['lean'] * 0.3 * up, shoulder[1]
        n = 0.24 + 0.17 * up
        ax, ay = sx0 + n * math.sin(a), sy0 + n * math.cos(a)
        L.curve([(sx0, sy0), ((sx0 + ax) / 2 + 0.07 * out, (sy0 + ay) / 2 + 0.03 * up), (ax, ay)], _dark(top, shade), 0.085)
        _hand(L, ax, ay, ax - sx0, ay - sy0, _dark(skin, shade))
        return ax, ay
    legs_b, legs_f = (P['leg_b'], P['leg_f']) if act not in ('stand', 'wave', 'look_up') else (0.0, 0.0)
    leg(legs_b, 0.85, -0.055)
    arm(P['arm_b'], 0.85, aims.get('back'))
    leg(legs_f, 1.0, 0.06)
    sx = P['lean'] * 0.3
    _doll_body(piece, outfit, top, bottom, sx)
    hx, hy = 0.02 + P['lean'] * 0.4, -0.78
    _doll_head(piece, hx, hy, skin, hair, style, extra, hy + 0.02 + P['head'] * 0.05, (t * 0.37 + x) % 1.0 < 0.04, mood, t)
    ax, ay = arm(P['arm_f'], 1.0, aims.get('front'))
    held = aims['item'] if 'item' in aims else st.params.get('holds')
    if held:
        _held(piece(), ax, ay, str(held), t)


def _held(L, hx, hy, what, t):
    """Something in the front hand: lantern balloon flower book gift umbrella ball medicine."""
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
    elif what == 'medicine':
        L.poly([(hx - 0.04, hy - 0.11), (hx + 0.04, hy - 0.11), (hx + 0.04, hy + 0.02), (hx - 0.04, hy + 0.02)], '#7fc4e8')
        L.poly([(hx - 0.022, hy - 0.15), (hx + 0.022, hy - 0.15), (hx + 0.022, hy - 0.11), (hx - 0.022, hy - 0.11)], '#fbfbf6')
        L.line([(hx - 0.022, hy - 0.05), (hx + 0.022, hy - 0.05)], '#e0526f', 0.016)
        L.line([(hx, hy - 0.072), (hx, hy - 0.028)], '#e0526f', 0.016)
    elif what == 'ball':
        L.circle(hx, hy - 0.05, 0.075, '#e0526f')
        L.curve([(hx - 0.07, hy - 0.05), (hx, hy - 0.02), (hx + 0.07, hy - 0.05)], '#fff4d8', 0.02)
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


def _muzzle_cat(M, F, hx, hy, hr, belly, fur, mood):
    M.ellipse(hx + 0.03, hy + hr * 0.4, hr * 0.38, hr * 0.27, belly)
    F.poly([(hx + 0.0, hy + hr * 0.2), (hx + 0.06, hy + hr * 0.2), (hx + 0.03, hy + hr * 0.32)], '#e88aa3')
    _mouth(F, mood, hx + 0.03, hy + hr * 0.46, 0.04, hr * 0.08, 0.011)
    _whiskers(F, hx, hy, hr)


def _muzzle_fox(M, F, hx, hy, hr, belly, fur, mood):
    M.ellipse(hx - hr * 0.36, hy + hr * 0.36, hr * 0.42, hr * 0.32, belly)
    M.ellipse(hx + hr * 0.56, hy + hr * 0.36, hr * 0.42, hr * 0.32, belly)
    M.poly([(hx - hr * 0.5, hy + hr * 0.5), (hx + hr * 0.7, hy + hr * 0.5), (hx + 0.05, hy + hr * 0.9)], belly)
    F.ellipse(hx + 0.05, hy + hr * 0.42, 0.04, 0.03, '#2a2020')
    _mouth(F, mood, hx + 0.05, hy + hr * 0.58, 0.04, hr * 0.08, 0.011, smile=False)


def _muzzle_dog(M, F, hx, hy, hr, belly, fur, mood):
    M.ellipse(hx + 0.03, hy + hr * 0.44, hr * 0.58, hr * 0.4, belly)
    F.ellipse(hx + 0.03, hy + hr * 0.24, 0.058, 0.04, '#2a2020')
    F.line([(hx + 0.03, hy + hr * 0.36), (hx + 0.03, hy + hr * 0.5)], '#3a2828', 0.011)
    _mouth(F, mood, hx + 0.03, hy + hr * 0.52, 0.08, hr * 0.12, 0.012)


def _muzzle_bunny(M, F, hx, hy, hr, belly, fur, mood):
    M.ellipse(hx + 0.03, hy + hr * 0.4, hr * 0.34, hr * 0.26, '#ffffff')
    F.ellipse(hx + 0.03, hy + hr * 0.26, 0.03, 0.022, '#e88aa3')
    F.line([(hx + 0.03, hy + hr * 0.34), (hx + 0.03, hy + hr * 0.46)], '#3a2828', 0.009)
    if mood == 'happy':
        F.poly([(hx + 0.008, hy + hr * 0.47), (hx + 0.052, hy + hr * 0.47), (hx + 0.052, hy + hr * 0.6), (hx + 0.008, hy + hr * 0.6)], '#ffffff')
        F.line([(hx + 0.03, hy + hr * 0.47), (hx + 0.03, hy + hr * 0.6)], '#c8c0c8', 0.005)
    else:
        _mouth(F, mood, hx + 0.03, hy + hr * 0.5, 0.04, hr * 0.08, 0.01)


def _muzzle_bear(M, F, hx, hy, hr, belly, fur, mood):
    M.ellipse(hx + 0.03, hy + hr * 0.42, hr * 0.5, hr * 0.42, belly)
    F.ellipse(hx + 0.03, hy + hr * 0.26, 0.05, 0.034, '#3a2828')
    _mouth(F, mood, hx + 0.03, hy + hr * 0.54, 0.05, hr * 0.09, 0.012)


def _ears_small(E, Ei, hx, hy, hr, fur, belly):
    for ex in (-0.13, 0.17):
        E.circle(hx + ex, hy - hr * 0.95, 0.06, _mix(belly, fur, 0.2))
        Ei.circle(hx + ex, hy - hr * 0.95, 0.03, '#f4b8c4')


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


def _tail_tufts(T, x, y, t, fur, belly):
    """No tail: a hedgehog's coat, soft round tufts along its back."""
    for k in range(9):
        a = math.pi * (0.5 + 1.0 * k / 8)
        T.circle(x + 0.3 + 0.36 * math.cos(a), y - 0.03 + 0.28 * math.sin(a), 0.1, fur)


def _whiskers(F, hx, hy, hr, col='#5a5a66'):
    for sgn, ex in ((-1, -0.09), (1, 0.15)):
        for dy in (0.02, 0.07):
            F.line([(hx + ex, hy + hr * 0.3 + dy), (hx + ex + sgn * 0.13, hy + hr * 0.27 + dy * 1.6)], col, 0.007)


def _muzzle_snout(M, F, hx, hy, hr, belly, fur, mood):
    """A hedgehog's face: dark tufts round the back of the head, a pale face that narrows into a cone, a black bead nose."""
    for k in range(7):
        a = math.pi * (0.85 + 0.75 * k / 6)
        M.circle(hx + hr * 0.98 * math.cos(a), hy + hr * 0.98 * math.sin(a), 0.07, fur)
    M.ellipse(hx + hr * 0.2, hy + hr * 0.2, hr * 0.82, hr * 0.74, belly)
    M.poly([(hx + hr * 0.4, hy + hr * 0.02), (hx + hr * 1.5, hy + hr * 0.42), (hx + hr * 1.5, hy + hr * 0.56), (hx + hr * 0.4, hy + hr * 0.92)], belly)
    F.circle(hx + hr * 1.55, hy + hr * 0.49, 0.048, '#2a2020')
    F.circle(hx + hr * 1.5, hy + hr * 0.42, 0.013, '#ffffff')
    _mouth(F, mood, hx + hr * 0.68, hy + hr * 0.68, 0.05, hr * 0.1, 0.011)


def _muzzle_mouse(M, F, hx, hy, hr, belly, fur, mood):
    M.ellipse(hx + 0.03, hy + hr * 0.42, hr * 0.34, hr * 0.26, belly)
    F.circle(hx + 0.03, hy + hr * 0.3, 0.03, '#e88aa3')
    _mouth(F, mood, hx + 0.03, hy + hr * 0.5, 0.04, hr * 0.07, 0.01)
    _whiskers(F, hx, hy, hr)


def _muzzle_frog(M, F, hx, hy, hr, belly, fur, mood):
    F.circle(hx - 0.0, hy + hr * 0.08, 0.012, '#3a5a2a')
    F.circle(hx + 0.06, hy + hr * 0.08, 0.012, '#3a5a2a')
    _mouth(F, mood, hx + 0.03, hy + hr * 0.28, 0.17, hr * 0.34, 0.016, '#2f6a3a')


def _muzzle_beak(M, F, hx, hy, hr, belly, fur, mood):
    if mood == 'surprised':  # the beak opens
        M.ellipse(hx + 0.04, hy + hr * 0.4, 0.06, 0.05, '#7a2a2a')
        M.poly([(hx - 0.05, hy + hr * 0.14), (hx + 0.13, hy + hr * 0.14), (hx + 0.04, hy + hr * 0.36)], '#f08a3a')
        M.poly([(hx - 0.02, hy + hr * 0.5), (hx + 0.1, hy + hr * 0.5), (hx + 0.04, hy + hr * 0.72)], '#f08a3a')
        F.ellipse(hx + 0.04, hy + hr * 0.84, 0.03, 0.04, '#e0526f')
        return
    M.poly([(hx - 0.04, hy + hr * 0.14), (hx + 0.12, hy + hr * 0.14), (hx + 0.04, hy + hr * 0.5)], '#f08a3a')
    F.ellipse(hx + 0.04, hy + hr * 0.66, 0.035, 0.05, '#e0526f')


def _muzzle_trunk(M, F, hx, hy, hr, belly, fur, mood):
    """A long trunk: thick at the face, thinner to the tip, down past the chin and curling up in front, with folds across it."""
    path = bezier([(hx + 0.04, hy + hr * 0.05), (hx + 0.1, hy + hr * 1.5), (hx + 0.16, hy + hr * 2.7), (hx + 0.62, hy + hr * 2.3), (hx + 0.6, hy + hr * 1.2)], 60)
    col = _dark(fur, 0.9)
    for k, (px, py) in enumerate(path):
        M.circle(px, py, 0.085 - 0.04 * k / 60, col)
    for k in range(6, 54, 8):
        (ax, ay), (bx, by) = path[k], path[k + 1]
        n = math.hypot(bx - ax, by - ay)
        r = 0.07 - 0.035 * k / 60
        nx, ny = (by - ay) / n * r, (ax - bx) / n * r
        F.line([(ax - nx, ay - ny), (ax + nx, ay + ny)], _dark(fur, 0.68), 0.01)
    F.ellipse(path[-1][0], path[-1][1] - 0.012, 0.024, 0.012, _dark(fur, 0.5))
    _mouth(F, mood, hx - 0.09, hy + hr * 0.62, 0.04, hr * 0.08, 0.011, smile=False)


EARS = {'pointy': _ears_pointy, 'long': _ears_long, 'round': _ears_round, 'floppy': _ears_floppy, 'small': _ears_small,
        'big': _ears_big, 'bulge': _ears_bulge, 'comb': _ears_comb, 'flap': _ears_flap}
TAILS = {'long': _tail_long, 'bushy': _tail_bushy, 'short': _tail_short, 'puff': _tail_puff, 'none': _tail_none,
         'thin': _tail_thin, 'feathers': _tail_feathers, 'tufts': _tail_tufts}
MUZZLES = {'cat': _muzzle_cat, 'fox': _muzzle_fox, 'dog': _muzzle_dog, 'bunny': _muzzle_bunny, 'bear': _muzzle_bear,
           'snout': _muzzle_snout, 'mouse': _muzzle_mouse, 'frog': _muzzle_frog, 'beak': _muzzle_beak, 'trunk': _muzzle_trunk}


def _eyes(F, hx, hy, hr, x, t, mood, gaps=(-0.07, 0.12)):
    """Button eyes with a glint, the same for every animal and bird; they blink now and then. The mood changes them, see _animal."""
    blink = (t * 0.33 + x) % 1.0 < 0.04
    ey = hy - hr * 0.12
    if mood == 'sad':
        _sad_brows(F, [hx + ex for ex in gaps], ey - 0.08, 0.036, '#3a2828')
    for ex in gaps:
        if mood in ('surprised', 'sleepy'):
            _mood_eye(F, hx + ex, ey, 0.036, mood, '#231a1a')
        elif blink:
            F.line([(hx + ex - 0.025, ey), (hx + ex + 0.025, ey)], '#2a2020', 0.016)
        else:
            F.circle(hx + ex, ey, 0.04, '#231a1a')
            F.circle(hx + ex + 0.013, ey - 0.014, 0.012, '#ffffff')
    if mood == 'sad':
        _tear(F, hx + gaps[0] - 0.03, ey + 0.085, 0.026, t)


def _animal(ctx, t, tl, st, f, look):
    """The base of every animal: a big round head, a small body with a pale belly, short thick legs with pads, button eyes
    and round cheeks. An animal is only its colours, ears, tail, muzzle and, for a hen, two feet.
    mood=happy|sad|surprised|sleepy sets the face as for people: happy is the usual look; sad has roof-like brows, a mouth turned
    down and a tear; surprised has round eyes and an 'o' mouth (a hen opens its beak); sleepy has closed eyes, arcs.
    hug, give, hold_hands and sleep work as for people, see _doll: an animal then shows a paw. holds= also shows a paw with the thing."""
    fur, belly, ears, tail, muzzle, feet = look
    fur = st.params.get('color', fur)
    if st.words[1] == 'sleep':
        _sleeper(ctx, t, st, f, 0.85, lambda piece: _animal_head(piece, 0.0, 0.0, 0.26, fur, belly, ears, muzzle, 0.0, t, st.params.get('mood', 'sleepy')))
        return
    x, y, facing = _place(st, f)
    s = st.params.get('size', 0.22)
    act = _act(st, t)
    P = _pose(act, t + x * 2.3, tl, st.t1 - st.t0)
    mood = st.params.get('mood', 'happy')
    yb = y - (P['bob'] * 1.5 + P['lift']) * s
    piece = lambda: Local(ctx.piece(), x, yb, s, facing)
    sit = act == 'sit'
    paw = _mix(belly, fur, 0.35)
    moving = act in ('walk', 'run')
    step = math.sin((t + x * 2.3) * 2 * math.pi * (2.6 if act == 'run' else 1.6)) if moving else 0.0

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
    _animal_head(piece, hx, hy, hr, fur, belly, ears, muzzle, x, t, mood)
    _carry(piece, st, t, x, yb, facing, (0.1, -0.42) if sit else (0.18, -0.35), fur, paw)


def _carry(piece, st, t, x, y, facing, start, fur, pad):
    """An animal's paw: reaching for the partner in a pair action, or held out with what it holds."""
    aims = _aims(st, t, x, y, facing)
    held = aims['item'] if 'item' in aims else st.params.get('holds')
    hand = aims.get('front') or aims.get('back') or ((start[0] + 0.24, start[1] + 0.02) if held else None)
    if hand is None:
        return
    hx, hy = _paw(piece(), start, hand, fur, pad)
    if held:
        _held(piece(), hx, hy, str(held), t)


def _animal_head(piece, hx, hy, hr, fur, belly, ears, muzzle, x, t, mood):
    """Ears, the round head, the muzzle, eyes and cheeks of an animal."""
    if ears != 'floppy':
        EARS[ears](piece(), piece(), hx, hy, hr, fur, belly)
    piece().circle(hx, hy, hr, fur)
    if ears == 'floppy':
        EARS[ears](piece(), piece(), hx, hy, hr, fur, belly)
    M, F = piece(), piece()
    MUZZLES[muzzle](M, F, hx, hy, hr, belly, fur, mood)
    if ears == 'bulge':
        _eyes(F, hx, hy - hr * 0.6, hr, x, t, mood, gaps=(-0.11, 0.15))
    else:
        _eyes(F, hx, hy, hr, x, t, mood)
    for ex in (-0.15, 0.2):
        F.circle(hx + ex, hy + hr * 0.3, 0.04, '#f4a6b4')


def _bird(ctx, t, tl, st, f):
    """A bird on the same base: a big round head, a small body with a pale belly, button eye, cheek; a wing and a beak instead of legs and muzzle.
    mood= works as for animals, on the eye and brow only: a beak has no mouth to change."""
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
    _eyes(F, hx, hy, hr, x, t, st.params.get('mood', 'happy'), gaps=(0.08,))
    F.circle(hx - 0.04, hy + hr * 0.3, 0.04, '#f4a6b4')


for _n, _look in PEOPLE.items():
    actor(_n, PERSON_ACTIONS)(lambda ctx, t, tl, st, f, _look=_look: _doll(ctx, t, tl, st, f, _look))
for _n, _look in ANIMALS.items():
    actor(_n, ANIMAL_ACTIONS)(lambda ctx, t, tl, st, f, _look=_look: _animal(ctx, t, tl, st, f, _look))
actor('bird', ['fly', 'stand'])(_bird)
