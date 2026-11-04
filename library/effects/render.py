"""Render the library: transparent PNG sequences, preview mp4s over felt, effects.json, contact sheet, showcase.

    python3 render.py                 # everything (4 processes)
    python3 render.py snow_light hail # only these effects
    python3 render.py --sheet         # only contact sheet + showcase from existing sequences
"""
import json
import os
import shutil
import subprocess
import sys
import time
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import effects_lib as E  # noqa: E402
from feltcore import felt_background  # noqa: E402

SEQ = os.path.join(HERE, 'seq')
PREV = os.path.join(HERE, 'preview')
PW, PH = 960, 540  # preview size


def frame_times(e):
    n = int(round(e['dur'] * e['fps']))
    if e['loop']:
        return [i / e['fps'] for i in range(n)]
    return [min(e['dur'], i / e['fps']) for i in range(n + 1)]


def render_one(name):
    e = E.EFFECTS[name]
    W, H = int(1920 * e['scale']), int(1080 * e['scale'])
    d = os.path.join(SEQ, name)
    os.makedirs(d, exist_ok=True)
    for f in os.listdir(d):
        os.remove(os.path.join(d, f))
    E.clear_cache()
    ts = frame_times(e)
    bg = felt_background(PW, PH).convert('RGBA')
    os.makedirs(PREV, exist_ok=True)
    out = os.path.join(PREV, name + '.mp4')
    reps = 3 if e['loop'] and e['dur'] <= 1.5 else (2 if e['loop'] else 1)
    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{PW}x{PH}', '-r', str(e['fps']),
                           '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '24', '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
                           out], stdin=subprocess.PIPE)
    t0 = time.time()
    prev_frames = []
    for i, t in enumerate(ts):
        im = E.render(name, t, {'W': W, 'H': H})
        im.save(os.path.join(d, '%04d.png' % i), compress_level=7)
        p = bg.copy()
        p.alpha_composite(im.resize((PW, PH), Image.LANCZOS) if (W, H) != (PW, PH) else im)
        prev_frames.append(p.convert('RGB').tobytes())
    for r in range(reps):
        for b in prev_frames:
            ff.stdin.write(b)
    if not e['loop']:
        for _ in range(int(e['fps'] * 0.6)):
            ff.stdin.write(prev_frames[-1])
    ff.stdin.close()
    ff.wait()
    if shutil.which('pngquant'):  # storage only: 256-colour palette PNG with alpha, visually lossless on felt, ~3.5x smaller
        files = sorted(os.path.join(d, f) for f in os.listdir(d))
        for k in range(0, len(files), 40):
            subprocess.run(['pngquant', '--quality=65-95', '--speed', '3', '--force', '--ext', '.png'] + files[k:k + 40],
                           stderr=subprocess.DEVNULL)
    else:  # same storage trick without the binary: libimagequant via the imagequant wheel (pip install imagequant)
        try:
            import imagequant
            for f in sorted(os.listdir(d)):
                fp = os.path.join(d, f)
                q = imagequant.quantize_pil_image(Image.open(fp).convert('RGBA'), dithering_level=1.0, max_colors=256,
                                                  min_quality=65, max_quality=95)
                q.save(fp, optimize=True)
        except ImportError:
            pass
    size = sum(os.path.getsize(os.path.join(d, f)) for f in os.listdir(d))
    return name, len(ts), W, H, size, time.time() - t0


def write_json(stats):
    items = []
    for name, e in E.EFFECTS.items():
        st = stats.get(name)
        items.append(dict(name=name, category=e['cat'], about=e['about'],
                          params=dict(seed=1, **{k: (list(v) if isinstance(v, tuple) else v) for k, v in e['params'].items()}),
                          loop=e['loop'], duration=e['dur'], fps=e['fps'],
                          frames=st[1] if st else None, size=[st[2], st[3]] if st else None,
                          seq='seq/%s/%%04d.png' % name, preview='preview/%s.mp4' % name,
                          function='effects_lib.%s(t, params)' % name))
    with open(os.path.join(HERE, 'effects.json'), 'w') as f:
        json.dump(dict(count=len(items), frame='RGBA 1920x1080 (scale<1 effects stored smaller; render() makes any size)',
                       effects=items), f, ensure_ascii=False, indent=1)


def _font(sz):
    for p in ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'):
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


def seq_frame(name, t, start=0.0):
    """Frame of a stored sequence at showcase time t (loops wrap, one-shots play once from `start` and hold)."""
    e = E.EFFECTS[name]
    d = os.path.join(SEQ, name)
    n = len(os.listdir(d))
    i = int((t - start) * e['fps'])
    i = i % n if e['loop'] else max(0, min(n - 1, i))
    return Image.open(os.path.join(d, '%04d.png' % i))


def contact_sheet():
    names = list(E.EFFECTS)
    cols = 10
    tw, th, lab = 384, 216, 30
    rows = (len(names) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * tw, rows * (th + lab)), (60, 56, 64))
    bg = felt_background(tw, th).convert('RGBA')
    font = _font(17)
    dr = ImageDraw.Draw(sheet)
    for k, n in enumerate(names):
        e = E.EFFECTS[n]
        t = e['dur'] * (0.45 if e['loop'] else 0.6)
        im = seq_frame(n, t).convert('RGBA').resize((tw, th), Image.LANCZOS)
        tile = bg.copy()
        tile.alpha_composite(im)
        x, y = (k % cols) * tw, (k // cols) * (th + lab)
        sheet.paste(tile.convert('RGB'), (x, y))
        dr.text((x + 8, y + th + 5), n, fill=(240, 232, 214), font=font)
    sheet.save(os.path.join(HERE, 'contact_sheet.jpg'), quality=88)


def showcase(seconds=30.0, fps=24):
    """30 s: 11 pages of a 3x3 grid (9 effects each, all 99), every tile labelled."""
    names = list(E.EFFECTS)
    per = 9
    pages = [names[i:i + per] for i in range(0, len(names), per)]
    seg = seconds / len(pages)
    W, H = 1920, 1080
    tw, th = 640, 360
    bg = felt_background(tw, th).convert('RGBA')
    font = _font(22)
    out = os.path.join(HERE, 'showcase.mp4')
    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(fps), '-i', '-',
                           '-c:v', 'libx264', '-preset', 'medium', '-crf', '23', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out],
                          stdin=subprocess.PIPE)
    total = int(seconds * fps)
    for fi in range(total):
        t = fi / fps
        pi = min(len(pages) - 1, int(t / seg))
        lt = t - pi * seg
        frame = Image.new('RGB', (W, H))
        dr = ImageDraw.Draw(frame)
        for k, n in enumerate(pages[pi]):
            e = E.EFFECTS[n]
            im = seq_frame(n, lt, start=0.1 if not e['loop'] else 0).convert('RGBA').resize((tw, th), Image.BILINEAR)
            tile = bg.copy()
            tile.alpha_composite(im)
            x, y = (k % 3) * tw, (k // 3) * th
            frame.paste(tile.convert('RGB'), (x, y))
            dr.rectangle((x, y + th - 34, x + 12 + 13 * len(n), y + th), fill=(50, 46, 54))
            dr.text((x + 7, y + th - 30), n, fill=(240, 232, 214), font=font)
        for k in range(1, 3):
            dr.line([(k * tw, 0), (k * tw, H)], fill=(50, 46, 54), width=3)
            dr.line([(0, k * th), (W, k * th)], fill=(50, 46, 54), width=3)
        ff.stdin.write(frame.tobytes())
    ff.stdin.close()
    ff.wait()


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    statf = os.path.join(HERE, '.render_stats.json')
    stats = json.load(open(statf)) if os.path.exists(statf) else {}
    if '--sheet' not in sys.argv:
        names = args or list(E.EFFECTS)
        names.sort(key=lambda n: -E.EFFECTS[n]['dur'] * E.EFFECTS[n]['fps'])
        with Pool(4) as pool:
            for st in pool.imap_unordered(render_one, names):
                stats[st[0]] = list(st)
                print('%-22s %3d frames %4dx%-4d %6.1f MB %5.1fs' % (st[0], st[1], st[2], st[3], st[4] / 1e6, st[5]), flush=True)
        json.dump(stats, open(statf, 'w'))
    write_json(stats)
    if not args:
        contact_sheet()
        showcase()


if __name__ == '__main__':
    main()
