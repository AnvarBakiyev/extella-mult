"""Checks library/ before a pull request: set names, picture sizes, variants against their base, set.json, media
attribution, char.json. python3 tools/check_library.py [library]  exits 1 when something is wrong."""
import json, os, re, sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'library')
NAME = re.compile(r'^[a-z][a-z0-9_]{1,40}$')
SIZES = {(1280, 720), (1920, 1080)}
LICENCES = ('CC0', 'CC BY', 'CC BY-SA', 'OFL', 'ours')
errors = []


def err(msg):
    errors.append(msg)


def check_sets():
    from PIL import Image
    d = os.path.join(ROOT, 'sets')
    for n in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        p = os.path.join(d, n)
        if not os.path.isdir(p):
            continue
        if not NAME.match(n):
            err(f'sets/{n}: the name must be lowercase a-z0-9_ and say what the picture is')
        base = os.path.join(p, 'base.png')
        if not os.path.isfile(base):
            err(f'sets/{n}: base.png is missing'); continue
        try:
            b = Image.open(base); b.load()
        except Exception as e:
            err(f'sets/{n}/base.png: cannot be read ({e})'); continue
        if b.size not in SIZES:
            err(f'sets/{n}/base.png: {b.size[0]}x{b.size[1]}, use 1280x720 or 1920x1080')
        for v in ('open', 'mid', 'blink'):
            f = os.path.join(p, v + '.png')
            if os.path.isfile(f):
                try:
                    im = Image.open(f); im.load()
                except Exception as e:
                    err(f'sets/{n}/{v}.png: cannot be read ({e})'); continue
                if im.size != b.size:
                    err(f'sets/{n}/{v}.png: size {im.size} differs from base.png {b.size}; the variants are the same frame')
        sj = os.path.join(p, 'set.json')
        if not os.path.isfile(sj):
            err(f'sets/{n}: set.json is missing'); continue
        try:
            j = json.load(open(sj, encoding='utf-8'))
        except Exception as e:
            err(f'sets/{n}/set.json: not valid JSON ({e})'); continue
        if not isinstance(j.get('about'), str) or len(j['about']) < 8:
            err(f'sets/{n}/set.json: "about" must say who or what, where, for which scenes')
        if j.get('talks') and not os.path.isfile(os.path.join(p, 'open.png')):
            err(f'sets/{n}: talks=true but there is no open.png')
        if 'license' in j and not any(j['license'].startswith(l) for l in LICENCES):
            err(f'sets/{n}/set.json: license must be one of {", ".join(LICENCES)}')
        for f in os.listdir(p):
            if f not in ('base.png', 'open.png', 'mid.png', 'blink.png', 'set.json'):
                err(f'sets/{n}/{f}: unexpected file; a set holds base/open/mid/blink.png and set.json')


def check_media():
    d = os.path.join(ROOT, 'media')
    if not os.path.isdir(d):
        return
    # a file is accounted for when ATTRIBUTION.md (credits) or INDEX.md (per-file source and licence) names it
    text = ''
    for f in ('ATTRIBUTION.md', 'INDEX.md'):
        p = os.path.join(d, f)
        text += open(p, encoding='utf-8').read() if os.path.isfile(p) else ''
    if not text:
        err('media/ATTRIBUTION.md is missing')
    for kind in ('sfx', 'music', 'fonts', 'overlays', 'textures'):
        k = os.path.join(d, kind)
        for f in sorted(os.listdir(k)) if os.path.isdir(k) else []:
            if f.startswith('.') or os.path.isdir(os.path.join(k, f)):
                continue
            if f not in text:
                err(f'media/{kind}/{f}: not listed in media/ATTRIBUTION.md or media/INDEX.md (what it is, source, licence)')
            if not NAME.match(os.path.splitext(f)[0].lower()):
                err(f'media/{kind}/{f}: the name must be lowercase a-z0-9_')


def check_chars():
    d = os.path.join(ROOT, 'chars', 'chars')
    for n in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        cj = os.path.join(d, n, 'char.json')
        if not os.path.isfile(cj):
            continue
        try:
            j = json.load(open(cj, encoding='utf-8'))
        except Exception as e:
            err(f'chars/{n}/char.json: not valid JSON ({e})'); continue
        if j.get('name') != n:
            err(f'chars/{n}/char.json: "name" must be {n}')
        for k in ('about', 'palette', 'parts'):
            if k not in j:
                err(f'chars/{n}/char.json: "{k}" is missing')


check_sets()
check_media()
check_chars()
if errors:
    print('\n'.join(errors))
    print(f'\n{len(errors)} problem(s)')
    sys.exit(1)
print('library ok')
