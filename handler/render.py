"""Frame assembly, camera, fades, multiprocessing render and ffmpeg muxing."""
import math
import os
import subprocess
import sys
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw
from .draw import Ctx, ease
from .elements import ELEMENTS
from .actors import ACTORS
from .effects import EFFECTS

from .config import ffmpeg as _ffmpeg
FFMPEG = _ffmpeg()
SUPER = 2  # internal supersampling factor
SUPER_FELT = float(os.environ.get('MULT_SUPER_FELT', 1))  # felt is soft; 1 is ~3x faster, see felt.py edge smoothing


def _progress(st, t):
    return (t - st.t0) / max(st.t1 - st.t0, 1e-6)


def camera_for(prog, sc, t):
    """Return (zoom, cx, cy) with cx, cy = view centre in normalized coords."""
    zoom, cx, cy = 1.0, 0.5, 0.5
    for st in prog.stmts:
        if st.kind != 'camera' or getattr(st, 'scene', None) is not sc:
            continue
        f = ease(min(1.0, max(0.0, _progress(st, t))))
        if t < st.t0:
            f = 0.0
        mv = st.words[0]
        if mv == 'pan':
            amt = st.params.get('amount', 0.12)
            zoom = max(zoom, st.params.get('zoom', 1.15))
            d = st.words[1]
            if d == 'down':
                cy = 0.5 - amt / 2 + amt * f
            elif d == 'up':
                cy = 0.5 + amt / 2 - amt * f
            elif d == 'right':
                cx = 0.5 - amt / 2 + amt * f
            elif d == 'left':
                cx = 0.5 + amt / 2 - amt * f
        elif mv == 'zoom':
            a, b = st.params['range']
            zoom = a + (b - a) * f
            if 'center' in st.params:
                cx, cy = st.params['center']
        elif mv == 'shake':
            if st.t0 <= t <= st.t1:
                amp = st.params.get('amount', 0.01) * (1 - f)
                cx += amp * math.sin(t * 61)
                cy += amp * math.cos(t * 53)
    return zoom, cx, cy


def render_frame(prog, t, out_size):
    sup = SUPER_FELT if prog.style == 'felt' else SUPER
    W, H = int(out_size[0] * sup), int(out_size[1] * sup)
    ctx = Ctx(W, H)
    sc = next((s for s in prog.scenes if s.t0 <= t < s.t1), prog.scenes[-1])
    tl = t - sc.t0
    if prog.style in ('3d', 'toon'):  # the shot was rendered by Blender; text and fades are drawn over it
        bg = Image.open(os.path.join(prog.bg_dir, f'{int(round(t * prog.fps)):05d}.png')).convert('RGBA')
        ctx.img.paste(bg.resize((W, H), Image.LANCZOS))
    felt = prog.style == 'felt' or (getattr(prog, 'look', '') == 'felt' and prog.style == '2d')
    elems, acts, effs = ELEMENTS, ACTORS, EFFECTS
    if prog.style == 'felt':
        from .felt_elements import FE
        from .felt_actors import FA
        from .felt_effects import FX
        elems, acts, effs = FE, FA, FX
    if felt:
        from .felt import felt_composite

        def blank():
            lc = Ctx(W, H)
            lc.img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            lc.d = ImageDraw.Draw(lc.img)
            lc.pieces = []

            def piece():  # a body part on its own felt layer
                pc = blank()
                lc.pieces.append(pc)
                return pc
            lc.piece = piece
            return lc

        night = prog.style == 'felt' and not any(n == 'room' for n, _ in sc.elements) and any(n == 'sky' and p.get('time') == 'night' for n, p in sc.elements)
        room_night = prog.style == 'felt' and any(n == 'room' and p.get('time') == 'night' for n, p in sc.elements)
        tint = (0.55, 0.6, 0.85) if night else ((0.82, 0.78, 0.72) if room_night else None)

        def shade(img):
            if tint is None:
                return
            import numpy as np
            a = np.asarray(img, np.float32)
            a[..., :3] *= tint
            img.paste(Image.fromarray(a.astype(np.uint8), 'RGBA'))

        # scene elements that come out the same as in the previous frame (the still background) are taken from a cache
        # instead of being felted again; a picture is cached once its layers have been seen twice in a row
        prefix = []
        still = [True]

        def layer(draw, depth=1.0, keep=False, cache=False):
            lc = blank()
            draw(lc)
            if not keep:
                shade(lc.img)
                for pc in lc.pieces:
                    shade(pc.img)
            key = None
            if cache and still[0]:
                prefix.append(hash((depth, lc.img.tobytes()) + tuple(pc.img.tobytes() for pc in lc.pieces)))
                key = (id(sc), tuple(prefix))
                if key in _STILL:
                    ctx.img = _STILL[key].copy()
                    ctx.d = ImageDraw.Draw(ctx.img)
                    return
            else:
                still[0] = False
            ctx.img = felt_composite(ctx.img, lc.img, depth)
            for pc in lc.pieces:
                ctx.img = felt_composite(ctx.img, pc.img, 0.7)
            ctx.d = ImageDraw.Draw(ctx.img)
            if key is not None:
                if _SEEN.get(key):
                    if len(_STILL) > 40:
                        _STILL.clear()
                    _STILL[key] = ctx.img.copy()
                else:
                    if len(_SEEN) > 2000:
                        _SEEN.clear()
                    _SEEN[key] = True
                    still[0] = False
    order = list(sc.elements)
    if prog.style == 'felt':  # depth order whatever order the program lists them in: sky, far, ground, the rest
        DEPTH = {'sky': 0, 'felt_sky': 0, 'room': 0, 'mountains': 1, 'planet': 1, 'rainbow': 1, 'felt_sun': 1, 'puff_cloud': 1,
                 'hills': 2, 'ground': 2, 'snow_ground': 2, 'moon_ground': 2, 'felt_sea': 2, 'river': 3}
        order = sorted(order, key=lambda e: DEPTH.get(e[0], 4))
        if any(n == 'room' for n, _ in order):
            order = [e for e in order if e[0] not in ('sky', 'felt_sky')]
    for k, (name, params) in enumerate([] if prog.style in ('3d', 'toon') else order):
        if felt:
            layer(lambda c, name=name, params=params: elems[name](c, t, tl, params), 0.35 if k == 0 else 1.0, keep=(name in ('sky', 'felt_sky')), cache=True)
        else:
            elems[name](ctx, t, tl, params)
    # actors, effects, text in program order; 'hold=1' keeps an effect at its end state until the scene ends
    for st in prog.stmts:
        if st.kind not in ('actor', 'effect', 'text') or getattr(st, 'scene', None) is not sc:
            continue
        active = st.t0 <= t < st.t1
        held = st.params.get('hold', 0) and t >= st.t1
        if not (active or held):
            continue
        f = min(1.0, _progress(st, t))
        if st.kind == 'actor':
            if prog.style not in ('3d', 'toon'):
                if felt:
                    layer(lambda c, st=st, f=f: acts[st.words[0]][0](c, t, tl, st, f))
                else:
                    ACTORS[st.words[0]][0](ctx, t, tl, st, f)
        elif st.kind == 'effect':
            if felt:
                layer(lambda c, st=st, f=f: effs[st.words[0]](c, t, tl, st, f), 0.6)
            else:
                EFFECTS[st.words[0]](ctx, t, tl, st, f)
        elif felt and prog.style == 'felt' and 'font' in st.words:
            from .felt_effects import felt_letters
            layer(lambda c, st=st, f=f: felt_letters(c, t, tl, st, f), 1.0, keep=True)
        else:
            EFFECTS['font_text' if 'font' in st.words else 'handwrite'](ctx, t, tl, st, f)
    # speech bubbles go last, over everything, so the words are never covered
    from .felt_effects import say_layouts, say_cloud, say_words
    for lay in say_layouts(ctx, t, prog, sc):
        before = ctx.img.copy() if lay['opacity'] < 1 else None
        layer(lambda c, lay=lay: say_cloud(c, lay), 1.0, keep=True)
        say_words(ctx, lay)
        if before is not None:
            ctx.img = Image.blend(before, ctx.img, lay['opacity'])
            ctx.d = ImageDraw.Draw(ctx.img)
    # camera: crop and resample
    zoom, cx, cy = camera_for(prog, sc, t) if prog.style not in ('3d', 'toon') else (1.0, 0.5, 0.5)
    cw, ch = W / zoom, H / zoom
    x0 = min(max(cx * W - cw / 2, 0), W - cw)
    y0 = min(max(cy * H - ch / 2, 0), H - ch)
    img = ctx.img.convert('RGB').resize(out_size, Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch))
    # fades
    dark = 0.0
    for st in prog.stmts:
        if st.kind == 'fade' and st.t0 <= t <= st.t1:
            f = _progress(st, t)
            dark = max(dark, 1 - f if st.words[0] == 'in' else f)
        elif st.kind == 'fade' and st.words[0] == 'in' and t < st.t0:
            dark = 1.0
    if dark > 0:
        arr = np.asarray(img, np.float32) * (1 - dark)
        img = Image.fromarray(arr.astype(np.uint8))
    return img


_PROG = None
_STILL = {}  # per worker: (scene, layer hashes) -> picture after those layers
_SEEN = {}


def _init(prog):
    global _PROG
    _PROG = prog


def _job(args):
    i, t, size, path = args
    render_frame(_PROG, t, size).save(path, compress_level=1)
    return i


def render_film(prog, out_path, size=None, procs=6, frames_dir=None, step=1, audio=True):
    from .audio import render_audio
    size = size or prog.size
    fps = prog.fps / step
    n = int(round(prog.length * prog.fps))
    frames_dir = frames_dir or out_path + '_frames'
    os.makedirs(frames_dir, exist_ok=True)
    if prog.style in ('3d', 'toon'):
        from .lib3d import render_backgrounds
        prog.bg_dir = frames_dir + '_3d'
        render_backgrounds(prog, prog.bg_dir, size)
    jobs = [(k, i / prog.fps, size, os.path.join(frames_dir, f'{k:05d}.png')) for k, i in enumerate(range(0, n, step))]
    done = 0
    with Pool(procs, initializer=_init, initargs=(prog,)) as pool:
        for _ in pool.imap_unordered(_job, jobs, chunksize=max(4, len(jobs) // (procs * 3))):
            done += 1
            if done % 50 == 0 or done == len(jobs):
                print(f'  frames {done}/{len(jobs)}', file=sys.stderr, flush=True)
    wav = out_path + '.wav'
    cmd = [FFMPEG, '-y', '-loglevel', 'error', '-framerate', f'{fps:g}', '-i', os.path.join(frames_dir, '%05d.png')]
    if audio:
        render_audio(prog, wav)
        cmd += ['-i', wav, '-c:a', 'aac', '-b:a', '192k', '-shortest']
    cmd += ['-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-r', f'{fps:g}', '-movflags', '+faststart', out_path]
    subprocess.run(cmd, check=True)
    for f in os.listdir(frames_dir):
        os.remove(os.path.join(frames_dir, f))
    os.rmdir(frames_dir)
    if prog.style in ('3d', 'toon'):
        import shutil
        shutil.rmtree(prog.bg_dir, ignore_errors=True)
    if audio and os.path.exists(wav):
        os.remove(wav)
