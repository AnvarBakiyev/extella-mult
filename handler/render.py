"""Frame assembly, camera, fades, multiprocessing render and ffmpeg muxing."""
import math
import os
import subprocess
import sys
from multiprocessing import Pool
import numpy as np
from PIL import Image
from .draw import Ctx, ease
from .elements import ELEMENTS
from .actors import ACTORS
from .effects import EFFECTS

from .config import ffmpeg as _ffmpeg
FFMPEG = _ffmpeg()
SUPER = 2  # internal supersampling factor


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
    W, H = out_size[0] * SUPER, out_size[1] * SUPER
    ctx = Ctx(W, H)
    sc = next((s for s in prog.scenes if s.t0 <= t < s.t1), prog.scenes[-1])
    tl = t - sc.t0
    if prog.style in ('3d', 'toon'):  # the shot was rendered by Blender; text and fades are drawn over it
        bg = Image.open(os.path.join(prog.bg_dir, f'{int(round(t * prog.fps)):05d}.png')).convert('RGBA')
        ctx.img.paste(bg.resize((W, H), Image.LANCZOS))
    for name, params in ([] if prog.style in ('3d', 'toon') else sc.elements):
        ELEMENTS[name](ctx, t, tl, params)
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
                ACTORS[st.words[0]][0](ctx, t, tl, st, f)
        elif st.kind == 'effect':
            EFFECTS[st.words[0]](ctx, t, tl, st, f)
        else:
            EFFECTS['font_text' if 'font' in st.words else 'handwrite'](ctx, t, tl, st, f)
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
        for _ in pool.imap_unordered(_job, jobs, chunksize=4):
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
