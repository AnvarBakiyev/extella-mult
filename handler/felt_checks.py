"""Composition checks for --check: a character outside the frame, an object too small to read. They warn, they never stop a film."""
from PIL import Image, ImageDraw
from .draw import Ctx

SMALL = 3.0  # an object should cover at least this much of the frame, in percent of its bounding box
# things that are small on purpose, or that only frame the picture
DECOR = {'felt_sun', 'puff_cloud', 'bush', 'gift', 'flowers', 'toys', 'fish', 'seaweed', 'bunting', 'garland', 'fence'}
W, H = 480, 201


def _blank():
    c = Ctx(W, H)
    c.img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    c.d = ImageDraw.Draw(c.img)
    c.pieces = []

    def piece():
        p = _blank()
        c.pieces.append(p)
        return p
    c.piece = piece
    return c


def _box(c):
    """The box of everything drawn on a layer and its pieces, clipped to the frame."""
    boxes = [b for b in [c.img.getbbox()] + [_box(p) for p in c.pieces] if b]
    if not boxes:
        return None
    return min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)


def _element_warnings(prog):
    from .felt_elements import FE
    out, seen = [], set()
    for sc in prog.scenes:
        for name, params in sc.elements:
            key = (name, tuple(sorted(params.items(), key=str)))
            if key in seen:
                continue
            seen.add(key)
            best = 0.0
            for tl in (0.0, (sc.t1 - sc.t0) / 2):  # a moving thing counts at its best moment
                layer = _blank()
                FE[name](layer, sc.t0 + tl, tl, params)
                b = _box(layer)
                if b:
                    best = max(best, (b[2] - b[0]) * (b[3] - b[1]) * 100.0 / (W * H))
            if best == 0.0:
                out.append(f"line {sc.line}: {name} is outside the frame; move it in with x= and y=")
            elif best < SMALL and name not in DECOR:
                out.append(f"line {sc.line}: {name} covers only {best:.1f}% of the frame, less than {SMALL:g}%; make it bigger with s= (r= for a round thing) or leave it out")
    return out


def _reach(st):
    """Left, right and top of a character around its place, in its own units."""
    from .felt_actors import PEOPLE
    if st.words[1] == 'sleep':
        return -0.3, 1.0, 0.5
    if st.words[0] in PEOPLE:
        return -0.2, 0.2, 1.0
    return -0.5, 0.5, 0.95


def _seen(st, f, ar):
    """How much of the character's box is inside the frame at this moment, from 0 to 1."""
    from .felt_actors import _place, _size
    x, y, _ = _place(st, f)
    s = _size(st)
    lo, hi, top = _reach(st)
    x0, x1, y0, y1 = x + lo * s * ar, x + hi * s * ar, y - top * s, y
    w = max(0.0, min(x1, 1.0) - max(x0, 0.0)) / (x1 - x0)
    h = max(0.0, min(y1, 1.0) - max(y0, 0.0)) / (y1 - y0)
    return w * h


def _actor_warnings(prog):
    ar = prog.size[1] / prog.size[0]
    out = []
    for st in prog.stmts:
        if st.kind != 'actor':
            continue
        moves = st.frm is not None and st.to is not None
        seen = [_seen(st, f, ar) for f in (0.0, 0.25, 0.5, 0.75, 1.0)]
        if max(seen) < 0.5 if moves else seen[0] < 0.6:  # coming in or going out is fine as long as it is seen on the way
            out.append(f"line {st.line}: {st.words[0]} {st.words[1]} at {st.t0:g}-{st.t1:g}s is outside the frame, or most of it is; check x, y= and size=")
    return out


def composition_warnings(prog):
    return _element_warnings(prog) + _actor_warnings(prog)
