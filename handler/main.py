"""CLI: python -m handler.main FILM.scene [--check] [--out film.mp4] [--preview] [--procs 6] [--frames t1,t2,...] [--dir DIR]"""
import argparse
import os
import re
import sys
from .parser import parse, SceneError
from .validate import validate
from .render import render_film, render_frame


def load(path):
    with open(path, encoding='utf-8') as f:
        return validate(parse(f.read()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('scene')
    ap.add_argument('--check', action='store_true', help='validate only')
    ap.add_argument('--out', default=None)
    ap.add_argument('--preview', action='store_true', help='render at 1/3 size, every 4th frame, no audio')
    ap.add_argument('--procs', type=int, default=6)
    ap.add_argument('--frames', default=None, help='comma-separated times in seconds; dump PNG stills instead of a film')
    ap.add_argument('--dir', default='stills')
    ap.add_argument('--no-audio', action='store_true', help='puppet: do not need or use voice recordings (lines are silent, mouths follow the text)')
    ap.add_argument('--size', default=None, help='puppet: render at WxH instead of the film size, e.g. 640x360')
    a = ap.parse_args()
    head = open(a.scene, encoding='utf-8').read() if os.path.isfile(a.scene) else ''
    if re.search(r'^\s*film\b.*\bstyle=puppet\b', head, re.M):
        from .puppet import parse_puppet, render_puppet, PuppetError
        try:
            prog = parse_puppet(head, no_audio=a.no_audio)
        except PuppetError as e:
            print(f'ERROR: {e}', file=sys.stderr)
            sys.exit(2)
        for w in prog['warnings']:
            print(f'warning: {w}', file=sys.stderr)
        print(f"ok: '{prog['title']}' {prog['length']:g}s, {len(prog['shots'])} shots, {len(prog['casts'])} cast, "
              f"{prog['size'][0]}x{prog['size'][1]} @ {prog['fps']} fps" + (', no voices' if prog['voices_off'] else ''), file=sys.stderr)
        if a.check:
            return
        size = tuple(int(x) for x in a.size.split('x')) if a.size else None
        if a.frames:
            for p in render_puppet(prog, a.dir, preview=a.preview, no_audio=a.no_audio, size=size,
                                   frames=[float(x) for x in a.frames.split(',')]):
                print(p, file=sys.stderr)
            return
        out = a.out or os.path.splitext(a.scene)[0] + ('_preview.mp4' if a.preview else '.mp4')
        render_puppet(prog, out, preview=a.preview, no_audio=a.no_audio, size=size)
        print(f'wrote {out}', file=sys.stderr)
        return
    try:
        prog = load(a.scene)
    except SceneError as e:
        print(f'ERROR: {e}', file=sys.stderr)
        sys.exit(2)
    except FileNotFoundError:
        print(f'ERROR: file {a.scene} not found', file=sys.stderr)
        sys.exit(2)
    print(f"ok: '{prog.title}' {prog.length:g}s, {len(prog.scenes)} scenes, {prog.size[0]}x{prog.size[1]} @ {prog.fps} fps", file=sys.stderr)
    if a.check:
        return
    if a.frames:
        os.makedirs(a.dir, exist_ok=True)
        size = (prog.size[0] // 2, prog.size[1] // 2) if a.preview else prog.size
        for ts in a.frames.split(','):
            t = float(ts)
            p = os.path.join(a.dir, f'{t:06.2f}.png')
            render_frame(prog, t, size).save(p)
            print(p, file=sys.stderr)
        return
    out = a.out or os.path.splitext(a.scene)[0] + ('_preview.mp4' if a.preview else '.mp4')
    if a.preview:
        render_film(prog, out, size=(prog.size[0] // 3 // 2 * 2, prog.size[1] // 3 // 2 * 2), procs=a.procs, step=4, audio=False)
    else:
        render_film(prog, out, procs=a.procs)
    print(f'wrote {out}', file=sys.stderr)


if __name__ == '__main__':
    main()
