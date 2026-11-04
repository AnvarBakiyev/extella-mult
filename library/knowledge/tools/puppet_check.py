#!/usr/bin/env python3
"""Check PUPPET programs with the real parser of the handler (handler/puppet.py, parse_puppet).

  python3 tools/puppet_check.py fewshot/*.scene               # stand-in sets (default when the device has none)
  python3 tools/puppet_check.py --device ep.scene             # the real sets in ~/extella-mult/assets/puppet
  python3 tools/puppet_check.py --handler ~/extella-mult ...  # use another copy of the handler

--stub-sets (the default without a device library) builds a stand-in library: every ch_/pl_ code of the
writers room plus the 63 device sets, any prop name is accepted, and voices count as recorded, so
LINES_TO_RECORD and the real-length timing check are skipped. Everything else is the handler's own check.
After the parser, a few extra lint checks run (music mood, camera values) that the parser leaves to render time.
Exit code 0 when every file passes.
"""
import argparse
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

MOODS = {'wonder', 'dark', 'bright', 'tense', 'cozy', 'calm'}
PANS = {'left', 'right', 'up', 'down', 'none'}


class AnyName(dict):
    """props_list() stand-in: every prop name exists."""
    def __contains__(self, k):
        return True

    def __getitem__(self, k):
        return k


def load(handler_dir, stub):
    sys.path.insert(0, str(handler_dir))
    try:
        import numpy, PIL.Image, scipy.signal  # noqa: F401  (needed for rendering, not for checking)
    except Exception:
        import types
        for name in ('numpy', 'PIL', 'PIL.Image', 'PIL.ImageFilter', 'scipy', 'scipy.signal'):
            m = types.ModuleType(name)
            m.__dict__.update(Image=None, ImageFilter=None, butter=None, lfilter=None, signal=m)
            sys.modules[name] = m
    from handler import puppet, audio
    if stub:
        import stubs
        puppet.SETS = stubs.build()
        puppet.props_list = lambda: AnyName()
        audio.voice_key = lambda: 'stub'  # every line counts as recordable, no LINES_TO_RECORD
    return puppet


def lint(prog):
    """Checks the parser does not make; they would fail or look wrong at render time."""
    errs = []
    for m in prog['music']:
        mood = str(m.params.get('mood', 'calm'))
        if mood not in MOODS:
            errs.append(f"line {m.n}: music mood={mood} does not exist; moods: {', '.join(sorted(MOODS))}")
        if m.t0 is None and m.at is None:
            errs.append(f"line {m.n}: music needs a range: music mood=bright 35-43s")
    for s in prog['shots']:
        P = s.params
        for k in ('push', 'pull', 'dutch', 'shake', 'snap', 'handheld'):
            if k in P and not isinstance(P[k], float):
                errs.append(f"line {s.n}: {k}={P[k]} must be a number")
        if 'snap' in P and isinstance(P['snap'], float) and not (s.t0 <= P['snap'] < s.t1):
            errs.append(f"line {s.n}: snap={P['snap']:g} is a film second and must fall inside this shot ({s.t0:g}-{s.t1:g}s)")
        if 'whip' in P and str(P['whip']) not in ('left', 'right'):
            errs.append(f"line {s.n}: whip must be left or right")
        if 'focus' in P and not re.fullmatch(r'0?\.\d+,0?\.\d+|[01],[01]', str(P['focus'])):
            errs.append(f"line {s.n}: focus=x,y with 0..1 values, e.g. focus=0.5,0.4")
        if isinstance(P.get('push'), float) and P['push'] > 0.3:
            errs.append(f"line {s.n}: push={P['push']:g} is too strong; use 0.02-0.16 (snap for a crash zoom)")
    return errs


def check_text(puppet, src):
    """Returns (ok, message, prog)."""
    try:
        prog = puppet.parse_puppet(src)
    except puppet.PuppetError as e:
        return False, str(e), None
    errs = lint(prog)
    if errs:
        return False, '; '.join(errs), prog
    return True, f"{len(prog['shots'])} shots, {len(prog['says'])} lines, {prog['length']:g}s", prog


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('files', nargs='+')
    ap.add_argument('--handler', default=str(HERE.parent / 'vendor'), help='folder that contains handler/puppet.py')
    g = ap.add_mutually_exclusive_group()
    g.add_argument('--stub-sets', action='store_true', help='stand-in sets named after the cast/places codes')
    g.add_argument('--device', action='store_true', help='use the real sets on this device')
    a = ap.parse_args()
    stub = a.stub_sets or not (a.device or os.path.isdir(os.path.expanduser('~/extella-mult/assets/puppet')))
    puppet = load(Path(a.handler).expanduser(), stub)
    bad = 0
    for f in a.files:
        ok, msg, _ = check_text(puppet, Path(f).read_text())
        print(('OK    ' if ok else 'ERROR ') + f + ': ' + msg)
        bad += not ok
    print(f"{len(a.files) - bad}/{len(a.files)} passed" + (' (stand-in sets)' if stub else ''))
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
