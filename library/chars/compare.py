"""Side-by-side sheet of the look versions: v1 paper cut-out, v2 felt, v3 felt (current chars/).

    python3 compare.py [v1-ref] [v2-ref]      -> sheets/compare_felt3.jpg
defaults: v1 = origin/puppet-characters-code, v2 = origin/puppet-characters-felt2.
Per character: v1 / v2 / v3 whole bust at video size (300 px, as in a 1080p frame) and v1 / v2 / v3 face crops at
100 %. Two characters per row, 12 characters.
"""
import io
import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw

from sheets import BG, INK, font

ROOT = os.path.dirname(os.path.abspath(__file__))
PICK = ['aigul', 'salmon_anchor', 'fox_detective', 'granny_zina', 'amara_anchor', 'shepherd_sheep', 'owl_judge',
        'robot_boss', 'chef_gogi', 'kid_sonya', 'monster_fifi', 'astronaut_asel']


def from_git(name, ref):
    top = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], cwd=ROOT, text=True).strip()
    rel = os.path.relpath(os.path.join(ROOT, 'chars', name, 'base.png'), top)
    data = subprocess.check_output(['git', 'show', '%s:%s' % (ref, rel)], cwd=ROOT)
    return Image.open(io.BytesIO(data)).convert('RGBA')


def on_bg(im):
    bg = Image.new('RGBA', im.size, BG + (255,))
    bg.alpha_composite(im)
    return bg.convert('RGB')


def main(ref1, ref2):
    V, C, g = 300, 300, 8
    f, fb = font(17), font(26)
    rows = len(PICK) // 2
    cellw = 3 * V + 3 * C + 5 * g + 14
    W, H = 2 * cellw + 30, rows * (V + 34) + 64
    sheet = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(sheet)
    d.text((W // 2, 16), 'v1 paper cut-out  /  v2 felt  /  v3 felt  -  whole bust at video size, face at 100 %',
           fill=INK, font=fb, anchor='mt')
    for i, n in enumerate(PICK):
        ims = [from_git(n, ref1), from_git(n, ref2), Image.open(os.path.join(ROOT, 'chars', n, 'base.png')).convert('RGBA')]
        meta = json.load(open(os.path.join(ROOT, 'chars', n, 'char.json')))
        cy = int(meta['anchors']['head_center'][1] * 1024)
        box = (512 - C // 2, cy - C // 2 - 10, 512 + C // 2, cy + C // 2 - 10)
        x, y = (i % 2) * (cellw + 20) + 10, 64 + (i // 2) * (V + 34)
        tiles = [on_bg(im).resize((V, V), Image.LANCZOS) for im in ims] + [on_bg(im).crop(box) for im in ims]
        labels = ['v1', 'v2', 'v3', 'v1 100%', 'v2 100%', 'v3 100%']
        xx = x
        for k, (t, lab) in enumerate(zip(tiles, labels)):
            sheet.paste(t, (xx, y))
            d.text((xx + 7, y + 5), lab, fill=INK, font=f)
            xx += t.size[0] + (g if k != 2 else g + 14)
        d.text((x + cellw // 2, y + V + 7), n, fill=INK, font=f, anchor='mt')
    sheet.save(os.path.join(ROOT, 'sheets', 'compare_felt3.jpg'), quality=88)


if __name__ == '__main__':
    a = sys.argv[1:]
    main(a[0] if a else 'origin/puppet-characters-code', a[1] if len(a) > 1 else 'origin/puppet-characters-felt2')
