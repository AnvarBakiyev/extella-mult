"""Contact sheets of full.jpg: python sheets.py plates/ sheets/ [--per 24] [--only biome,biome] [--prefix sheet]"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont


def font(sz):
    for p in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/System/Library/Fonts/Supplemental/Arial.ttf'):
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


def sheets(root, out, per=24, cols=4, tw=480, prefix='sheet', only=None):
    names = sorted(n for n in os.listdir(root) if os.path.exists(os.path.join(root, n, 'full.jpg')))
    if only:  # keep the plates of these biomes
        names = [n for n in names if json.load(open(os.path.join(root, n, 'plate.json')))['biome'] in only]
    os.makedirs(out, exist_ok=True)
    th, lab = tw * 9 // 16, 22
    f = font(15)
    files = []
    for i in range(0, len(names), per):
        chunk = names[i:i + per]
        rows = (len(chunk) + cols - 1) // cols
        sh = Image.new('RGB', (cols * (tw + 8) + 8, rows * (th + lab + 8) + 8), (245, 242, 236))
        d = ImageDraw.Draw(sh)
        for k, n in enumerate(chunk):
            im = Image.open(os.path.join(root, n, 'full.jpg')).convert('RGB').resize((tw, th), Image.LANCZOS)
            x, y = 8 + (k % cols) * (tw + 8), 8 + (k // cols) * (th + lab + 8)
            sh.paste(im, (x, y))
            d.text((x + 2, y + th + 3), n, fill=(40, 40, 40), font=f)
        p = os.path.join(out, f'{prefix}_{i // per + 1:02d}.jpg')
        sh.save(p, quality=85)
        files.append(p)
    return files


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    argv = sys.argv[1:]
    args = [a for i, a in enumerate(argv) if not a.startswith('--') and not (i and argv[i - 1] in ('--per', '--only', '--prefix'))]
    opt = {k: argv[argv.index(k) + 1] for k in ('--per', '--only', '--prefix') if k in argv}
    print('\n'.join(sheets(args[0], args[1], per=int(opt.get('--per', 24)), prefix=opt.get('--prefix', 'sheet'),
                           only=set(opt['--only'].split(',')) if '--only' in opt else None)))
