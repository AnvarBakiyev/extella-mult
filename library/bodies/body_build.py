"""Full-body puppets: rigs for the cast, base PNGs, contact sheets and demo videos.

    python3 body_build.py rigs [names]   # body/<name>/rig.json + part PNGs, body/_props   (about 10 s per character)
    python3 body_build.py base           # body/<name>/full_q34.png (front three-quarter, standing) + body/body.json
    python3 body_build.py sheets         # body_sheets/<name>.jpg: every pose and cycle, both views (DEMO_CAST)
    python3 body_build.py demo           # body_demo/<name>.mp4: 20 s walk / wave / shrug / dance / jump / run (DEMO_CAST)
    python3 body_build.py all
"""
import json
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim as A  # noqa: E402
import charlib as L  # noqa: E402
from characters import CAST  # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))
BODY = os.path.join(ROOT, 'body')
DEMO_CAST = ['aigul', 'timur', 'oleg_petrovich', 'stas_intern', 'zarina', 'daniyar_dev', 'hr_imp', 'auditor_crow',
             'doctor_maria', 'nurse_gulya', 'vet_bear', 'astronaut_asel', 'chef_gogi', 'baker_olga', 'granny_zina',
             'kid_sonya', 'kid_arman', 'fox_lisa', 'cat_boss', 'dog_sheriff', 'owl_judge', 'frog_prince', 'mouse_kid',
             'pig_singer', 'salmon_anchor', 'robot_bolt', 'monster_fifi', 'sheep_poet', 'wizard_merlan', 'hare_coward']
SPEC = {s['name']: s for s in CAST}


def font(sz):
    for p in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/dejavu/DejaVuSans.ttf'):
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


def _rig(name):
    L.build_body(SPEC[name], BODY)
    return name


def rigs(names):
    L.build_props(BODY)
    with Pool(int(os.environ.get('JOBS', os.cpu_count() or 2))) as p:
        for i, n in enumerate(p.imap_unordered(_rig, names)):
            print('rig', i + 1, len(names), n, flush=True)


def _base(name):
    p = A.Puppet(name, 'q34', scale=1.0)
    im, (ox, oy) = p.image(A.play('stand', 1.0, p))
    im.save(os.path.join(BODY, name, 'full_q34.png'), optimize=True)
    r = p.rig
    return name, {'kind': r['kind'], 'rig': '%s/rig.json' % name, 'full_q34': '%s/full_q34.png' % name,
                  'full_size': list(im.size), 'ground_at': [ox, oy], 'about': SPEC[name]['about'],
                  'voice': SPEC[name]['voice'], 'has': r['has'], 'height_px': r['views']['q34']['height']}


def base(names):
    with Pool(int(os.environ.get('JOBS', os.cpu_count() or 2))) as p:
        out = dict(p.imap_unordered(_base, names))
    index = {
        'about': 'Full-body felt puppets on a 2D rig (charlib.Body / anim.Puppet). See BODY.md.',
        'views': list(L.BODY_VIEWS), 'px_per_unit': 1024 * L.BODY_SCALE,
        'poses': list(A.POSES), 'cycles': list(A.CYCLES), 'hand_shapes': L.HAND_SHAPES,
        'visemes': L.VISEMES, 'expressions': L.EXPRESSIONS, 'props': ['phone', 'mic', 'laptop', 'stool'],
        'demo_cast': DEMO_CAST,
        'characters': {n: out[n] for n in names},
    }
    with open(os.path.join(BODY, 'body.json'), 'w') as f:
        json.dump(index, f, ensure_ascii=False, indent=1)
    print('base', len(out))


def sheet_pose(name, c):
    clip = A.clip(c)
    return clip.hold if c in A.POSES else clip.keys[1][0]


def _sheet(name):
    clips = list(A.POSES) + list(A.CYCLES)
    cw, ch, cols = 300, 420, 7
    f, fb = font(17), font(26)
    rows = 2 * ((len(clips) + cols - 1) // cols)
    sheet = Image.new('RGB', (cols * cw, rows * ch + 50), (233, 228, 218))
    d = ImageDraw.Draw(sheet)
    d.text((12, 10), '%s - poses and cycles (rows 1-3 front three-quarter, rows 4-6 side)' % name, fill=(50, 45, 50), font=fb)
    sc = A.Scene(cw, ch, floor=0.9)
    for vi, view in enumerate(('q34', 'side')):
        p = A.Puppet(name, view, scale=0.3)
        for i, c in enumerate(clips):
            pose = A.play(c, sheet_pose(name, c), p)
            im = Image.fromarray(sc.frame([(p, pose, cw // 2 + (40 if c == 'fall' else 0), int(ch * 0.9), False)]))
            ImageDraw.Draw(im).text((8, 6), c.replace('_', ' '), fill=(40, 36, 40), font=f)
            r = vi * (rows // 2) + i // cols
            sheet.paste(im, ((i % cols) * cw, 50 + r * ch))
    os.makedirs(os.path.join(ROOT, 'body_sheets'), exist_ok=True)
    sheet.save(os.path.join(ROOT, 'body_sheets', name + '.jpg'), quality=86)
    return name


# ---------------------------------------------------------------- the 20 s demo
TALK = [('closed', 3), ('MBP', 2), ('A', 3), ('E', 2), ('O', 3), ('closed', 2), ('U', 2), ('A', 4), ('E', 3), ('MBP', 2),
        ('O', 3), ('A', 3), ('closed', 6), ('E', 3), ('A', 2), ('U', 3), ('O', 2), ('MBP', 3), ('A', 3), ('closed', 8)]
SEG = [  # (start s, end s, clip, view, talking)
    (0.0, 3.6, 'walk', 'side', False),
    (3.6, 6.6, 'wave', 'q34', True),
    (6.6, 9.0, 'shrug', 'q34', True),
    (9.0, 13.0, 'dance', 'q34', False),
    (13.0, 14.4, 'jump', 'q34', False),
    (14.4, 20.0, 'run', 'side', False),
]


def _demo(name, W=960, H=540, fps=25):
    sc = A.Scene(W, H, floor=0.84)
    gy = int(H * 0.9)
    pp = {v: A.Puppet(name, v, scale=0.4) for v in ('q34', 'side')}
    talk = []
    for v, n in TALK:
        talk += [v] * n
    walk_speed = A.stride(pp['side'], 'walk') * 0.4 / A.clip('walk').length   # px per second, no foot sliding
    run_speed = A.stride(pp['side'], 'run') * 0.4 / A.clip('run').length
    x_center = W * 0.5
    x_walk0 = x_center - walk_speed * 3.6
    path = os.path.join(ROOT, 'body_demo', name + '.mp4')
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H), '-r', str(fps),
           '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '26', '-preset', 'medium', path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    f = font(22)
    label = Image.new('RGBA', (W, 40), (0, 0, 0, 0))
    ImageDraw.Draw(label).text((16, 10), name, fill=(70, 62, 66, 255), font=f)
    prev_end = None
    for i in range(int(20 * fps)):
        t = i / fps
        for k, (t0, t1, c, view, talking) in enumerate(SEG):
            if t0 <= t < t1 or k == len(SEG) - 1:
                break
        p = pp[view]
        lt = t - t0
        pose = A.play(c, lt, p)
        flip = False
        x = x_center
        if c == 'walk':
            x = x_walk0 + walk_speed * lt
        elif c == 'run':
            span = W + 300
            x = (x_center + run_speed * lt + 150) % span - 150
        # ease out of the previous clip's last pose over 0.3 s
        if k > 0 and lt < 0.3:
            pt0, pt1, pc, pv, _ = SEG[k - 1]
            prev = A.play(pc, pt1 - pt0, pp[pv])
            pose = A.blend(prev, pose, A.EASE['inout'](lt / 0.3))
        kw = {}
        if talking:
            kw['mouth'] = talk[i % len(talk)]
            kw['expr'] = 'happy' if c == 'wave' else 'neutral'
        if (i % 90) < 3 and 'blink' not in pose:
            kw['blink'] = True
        fr = sc.frame([(p, pose, x, gy, flip, kw)])
        im = Image.fromarray(fr)
        im.paste(label, (0, 0), label)
        proc.stdin.write(im.tobytes())
    proc.stdin.close()
    proc.wait()
    return name


def run_pool(fn, names):
    with Pool(int(os.environ.get('JOBS', os.cpu_count() or 2))) as p:
        for i, n in enumerate(p.imap_unordered(fn, names)):
            print(fn.__name__, i + 1, len(names), n, flush=True)


if __name__ == '__main__':
    what = sys.argv[1] if len(sys.argv) > 1 else 'all'
    names = sys.argv[2:] or [s['name'] for s in CAST]
    demo_names = sys.argv[2:] or DEMO_CAST
    if what in ('rigs', 'all'):
        rigs(names)
    if what in ('base', 'all'):
        base([n for n in names if os.path.exists(os.path.join(BODY, n, 'rig.json'))])
    if what in ('sheets', 'all'):
        run_pool(_sheet, demo_names)
    if what in ('demo', 'all'):
        os.makedirs(os.path.join(ROOT, 'body_demo'), exist_ok=True)
        run_pool(_demo, demo_names)
