"""Contact sheets and 6-second viseme demos (one per 10 characters), from the rendered chars/ folder.

    python3 sheets.py
sheets/cast_<k>.jpg     all bases, 40 per sheet, with names
sheets/frames_<k>.jpg   10 characters per sheet x every frame (base, 6 visemes, blink, 4 expressions)
demo/demo_<k>.mp4       10 characters on a 5x2 grid talking (cycling visemes) and blinking, 6 s at 25 fps
"""
import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from characters import CAST  # noqa: E402
import charlib as L  # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))
BG = (233, 228, 218)


def font(sz):
    for p in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/dejavu/DejaVuSans.ttf'):
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


def load(name, key):
    return Image.open(os.path.join(ROOT, 'chars', name, key + '.png')).convert('RGBA')


def names():
    return [s['name'] for s in CAST if os.path.exists(os.path.join(ROOT, 'chars', s['name'], 'char.json'))]


def cast_sheets(ns, per=40, cols=8, S=300):
    f = font(18)
    for k in range(0, len(ns), per):
        chunk = ns[k:k + per]
        rows = (len(chunk) + cols - 1) // cols
        sheet = Image.new('RGB', (cols * S, rows * (S + 30)), BG)
        d = ImageDraw.Draw(sheet)
        for i, n in enumerate(chunk):
            im = load(n, 'base').resize((S, S), Image.LANCZOS)
            x, y = (i % cols) * S, (i // cols) * (S + 30)
            sheet.paste(im, (x, y), im)
            d.text((x + S // 2, y + S + 4), n, fill=(60, 55, 60), font=f, anchor='mt')
        sheet.save(os.path.join(ROOT, 'sheets', 'cast_%02d.jpg' % (k // per + 1)), quality=88)


def frame_sheets(ns, per=10, S=200):
    keys = ['base'] + ['mouth_' + v for v in L.VISEMES[1:]] + ['blink'] + ['expr_' + e for e in L.EXPRESSIONS[1:]]
    labels = ['base'] + L.VISEMES[1:] + ['blink'] + L.EXPRESSIONS[1:]
    f = font(16)
    for k in range(0, len(ns), per):
        chunk = ns[k:k + per]
        sheet = Image.new('RGB', (len(keys) * S + 150, len(chunk) * S + 26), BG)
        d = ImageDraw.Draw(sheet)
        for i, lab in enumerate(labels):
            d.text((150 + i * S + S // 2, 6), lab, fill=(60, 55, 60), font=f, anchor='mt')
        for j, n in enumerate(chunk):
            base = load(n, 'base')
            d.text((8, 26 + j * S + S // 2), n, fill=(60, 55, 60), font=f, anchor='lm')
            for i, key in enumerate(keys):
                im = base if key == 'base' else L.compose(base, load(n, key))
                im = im.resize((S, S), Image.LANCZOS)
                sheet.paste(im, (150 + i * S, 26 + j * S), im)
        sheet.save(os.path.join(ROOT, 'sheets', 'frames_%02d.jpg' % (k // per + 1)), quality=88)


# a pseudo sentence: visemes with durations in frames (25 fps)
TALK = [('closed', 3), ('MBP', 2), ('A', 3), ('E', 2), ('O', 3), ('closed', 2), ('U', 2), ('A', 4), ('E', 3), ('MBP', 2),
        ('O', 3), ('A', 3), ('closed', 6), ('E', 3), ('A', 2), ('U', 3), ('O', 2), ('MBP', 3), ('A', 3), ('closed', 8)]


def demo(ns, idx, W=1600, H=720, fps=25, secs=6):
    cols, S = 5, 300
    cells = []
    for n in ns:
        base = load(n, 'base').resize((S, S), Image.LANCZOS)
        ov = {v: L.compose(load(n, 'base'), load(n, 'mouth_' + v)).resize((S, S), Image.LANCZOS) for v in L.VISEMES}
        blink = {v: L.compose(load(n, 'base'), load(n, 'mouth_' + v), load(n, 'blink')).resize((S, S), Image.LANCZOS)
                 for v in L.VISEMES}
        cells.append((n, base, ov, blink))
    seq = []
    for v, d in TALK:
        seq += [v] * d
    f = font(20)
    path = os.path.join(ROOT, 'demo', 'demo_%02d.mp4' % idx)
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H), '-r', str(fps),
           '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '23', '-preset', 'medium', path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    bgimg = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(bgimg)
    for i, (n, *_r) in enumerate(cells):
        x, y = (i % cols) * (W // cols), (i // cols) * (H // 2)
        d.text((x + W // cols // 2, y + S + 12), n, fill=(60, 55, 60), font=f, anchor='mt')
    for t in range(fps * secs):
        fr = bgimg.copy()
        for i, (n, base, ov, blink) in enumerate(cells):
            off = (i * 7) % len(seq)
            v = seq[(t + off) % len(seq)]
            bl = ((t + i * 11) % 70) < 3
            im = (blink if bl else ov)[v]
            x, y = (i % cols) * (W // cols) + (W // cols - S) // 2, (i // cols) * (H // 2) + 6
            fr.paste(im, (x, y), im)
        p.stdin.write(fr.tobytes())
    p.stdin.close()
    p.wait()


if __name__ == '__main__':
    os.makedirs(os.path.join(ROOT, 'sheets'), exist_ok=True)
    os.makedirs(os.path.join(ROOT, 'demo'), exist_ok=True)
    ns = names()
    what = sys.argv[1:] or ['cast', 'frames', 'demo']
    if 'cast' in what:
        cast_sheets(ns)
    if 'frames' in what:
        frame_sheets(ns)
    if 'demo' in what:
        for k in range(0, len(ns), 10):
            demo(ns[k:k + 10], k // 10 + 1)
    print('done', len(ns))
