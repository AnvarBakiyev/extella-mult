"""Parallax demo: slides a camera across a few plates, moving each layer by its own parallax factor.
python parallax.py out.mp4 plates/<a> plates/<b> ... [--sec 2] [--fps 30]"""
import json
import os
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image

W, H = 1920, 1080
ZOOM = 1.08          # layers are scaled up a little so a pan never shows an edge
PAN = 70             # px of shift for a layer with parallax 1.0 at the ends of the move


def ease(t):
    return t * t * (3 - 2 * t)


def load(d):
    meta = json.load(open(os.path.join(d, 'plate.json')))
    layers = []
    for l in meta['layers']:
        im = Image.open(os.path.join(d, l['file'])).convert('RGBA')
        layers.append((im, l['parallax']))
    return meta, layers


def frame(layers, u):
    out = None
    for im, p in layers:
        dx = -u * p * PAN
        # scale about the centre, then shift
        a = 1 / ZOOM
        cx, cy = W / 2, H / 2
        m = (a, 0, cx - a * cx - a * dx, 0, a, cy - a * cy)
        fr = im.transform((W, H), Image.AFFINE, m, resample=Image.BILINEAR)
        out = fr if out is None else Image.alpha_composite(out, fr)
    return out.convert('RGB')


def main():
    argv = sys.argv[1:]
    args = [a for i, a in enumerate(argv) if not a.startswith('--') and not (i and argv[i - 1] in ('--sec', '--fps'))]
    sec = float(sys.argv[sys.argv.index('--sec') + 1]) if '--sec' in sys.argv else 2.0
    fps = int(sys.argv[sys.argv.index('--fps') + 1]) if '--fps' in sys.argv else 30
    out, dirs = args[0], args[1:]
    ff = shutil.which('ffmpeg') or 'ffmpeg'
    p = subprocess.Popen([ff, '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(fps),
                          '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '24', '-preset', 'medium', out],
                         stdin=subprocess.PIPE)
    n = int(sec * fps)
    fade = int(0.25 * fps)
    prev_last = None
    for k, d in enumerate(dirs):
        _, layers = load(d)
        direction = 1 if k % 2 == 0 else -1
        for i in range(n):
            u = direction * (2 * ease(i / (n - 1)) - 1)
            fr = frame(layers, u)
            if prev_last is not None and i < fade:
                fr = Image.blend(prev_last, fr, (i + 1) / (fade + 1))
            p.stdin.write(fr.tobytes())
            if i == n - 1:
                prev_last = fr
        print(d, flush=True)
    p.stdin.close()
    p.wait()


if __name__ == '__main__':
    main()
