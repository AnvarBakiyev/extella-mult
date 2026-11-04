"""Render every prop in props_lib through feltlook's felt v2+ composite to png/<category>/<name>.png and make a
contact sheet per category (contact-<category>.png). Set EXTELLA_MULT to the extella-mult checkout if it is not next
to this repo.

    python render_props.py                 # everything
    python render_props.py food plants     # some categories
    python render_props.py --only apple    # one prop
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'feltlook'))
sys.path.insert(0, HERE)
import feltlook as FL  # noqa: E402  felt v2+ (shared with plates, effects and characters)
import props_lib  # noqa: E402

# which wool each prop is made of (the felt pass picks fibres, texture and volume by kind)
KIND_BY_NAME = {
    'foliage': ('grass_', 'bush_', 'tree_', 'clover', 'reeds', 'cattail', 'leaf_', 'houseplant_hanging', 'potted_plant',
                'succulent_pot', 'broccoli', 'cabbage'),
    'cloud': ('cloud_', 'smoke_puff', 'steam'),
    'snow': ('snowman', 'snowflake', 'iceberg', 'tree_snowy_fir'),
    'knit': ('carpet', 'round_rug', 'scarf', 'beanie', 'mitten', 'sock', 'tshirt', 'dress'),
    'fur': ('baursaki',),
}


def prop_kind(name):
    for kind, keys in KIND_BY_NAME.items():
        if any(name == k or (k.endswith('_') and name.startswith(k)) for k in keys):
            return kind
    return 'felt'


def felt_composite(base, layer, depth, kind='felt'):
    """felt v2+ piece at prop scale (512 px canvas, felt sizes as on a 804-px frame)."""
    return FL.felt_composite(base, layer, depth, kind=kind, s=props_lib.S / 804.0 * 1.25)

MARGIN = 14


def felt_prop(cat, name, seed=1):
    """The prop as one RGBA image (512x512, transparent), each layer felted over the ones below."""
    c = props_lib.Canvas(seed)
    props_lib.PROPS[cat][name](c)
    base = Image.new('RGBA', (props_lib.S, props_lib.S), (0, 0, 0, 0))
    FL.begin(seed * 100003 + sum(ord(ch) * (i + 1) for i, ch in enumerate(cat + name)))
    kind = prop_kind(name)
    for i, (layer, depth) in enumerate(c.frame()):
        # the body is made of the prop's wool; thin detail layers on top are plain felt
        base = felt_composite(base, layer, depth, kind if (i == 0 or depth >= 0.7 or kind == 'foliage') else 'felt')
    return base


def crop(img):
    box = img.getchannel('A').point(lambda v: 255 if v > 8 else 0).getbbox()
    if not box:
        return img
    x0, y0, x1, y1 = box
    return img.crop((max(0, x0 - MARGIN), max(0, y0 - MARGIN), min(img.width, x1 + MARGIN), min(img.height, y1 + MARGIN)))


def checker(w, h, a=(246, 244, 239), b=(232, 229, 222), n=16):
    im = Image.new('RGB', (w, h), a)
    d = ImageDraw.Draw(im)
    for y in range(0, h, n):
        for x in range((y // n % 2) * n, w, 2 * n):
            d.rectangle([x, y, x + n - 1, y + n - 1], fill=b)
    return im


def font(sz):
    for f in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/Library/Fonts/Arial.ttf'):
        if os.path.exists(f):
            return ImageFont.truetype(f, sz)
    return ImageFont.load_default()


def contact(cat, items, out, cell=220, cols=6):
    rows = (len(items) + cols - 1) // cols
    W, H = cols * cell, rows * (cell + 26) + 50
    sheet = checker(W, H)
    d = ImageDraw.Draw(sheet)
    d.text((14, 12), '%s  (%d props)' % (cat, len(items)), fill=(60, 60, 64), font=font(24))
    f = font(15)
    for k, (name, img) in enumerate(items):
        x, y = (k % cols) * cell, 50 + (k // cols) * (cell + 26)
        im = img.copy()
        im.thumbnail((cell - 16, cell - 16), Image.LANCZOS)
        sheet.paste(im, (x + (cell - im.width) // 2, y + (cell - im.height) // 2), im)
        tw = d.textlength(name, font=f)
        d.text((x + (cell - tw) / 2, y + cell + 2), name, fill=(70, 70, 74), font=f)
    sheet.save(out)


def main(argv):
    only = None
    if '--only' in argv:
        only = argv[argv.index('--only') + 1]
        argv = [a for a in argv if a not in ('--only', only)]
    cats = argv or list(props_lib.PROPS)
    total = 0
    for cat in cats:
        items = []
        os.makedirs(os.path.join(HERE, 'png', cat), exist_ok=True)
        for name in props_lib.PROPS[cat]:
            if only and name != only:
                continue
            img = crop(felt_prop(cat, name))
            img.save(os.path.join(HERE, 'png', cat, name + '.png'), optimize=True)
            items.append((name, img))
        if items and not only:
            contact(cat, items, os.path.join(HERE, 'contact-%s.png' % cat))
        total += len(items)
        print(cat, len(items))
    print('total', total)


if __name__ == '__main__':
    main(sys.argv[1:])
