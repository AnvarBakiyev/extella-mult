"""Where the code-built library lives and how to look things up in it.

The library is the set of folders made by the puppet-* branches:
  puppet-characters-code/chars/<name>/      code_char: base.png, mouth_<viseme>.png, blink.png, expr_<mood>.png, char.json
  puppet-plates-code/plates/<name>/         plate: sky/far/mid/near/fg.png + plate.json (parallax per layer)
  puppet-procedural/png/<category>/<n>.png  prop
  puppet-procedural/motion.py               camera moves and transitions
  puppet-effects-code/seq/<name>/%04d.png   effect frames, effects.json
  puppet-oss/media/{sfx,music,fonts}/       CC0 sounds and music, OFL fonts

The root is, in this order: $PUPPET_LIB, ~/extella-mult/assets/lib (an installed device), or the `mult/` folder of
this repository (the handler sits in mult/puppet-handler/handler).
"""
import functools
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HANDLER_ROOT = os.path.dirname(HERE)                 # mult/puppet-handler
REPO_MULT = os.path.dirname(HANDLER_ROOT)            # mult/


def lib_root():
    for p in (os.environ.get('PUPPET_LIB'), os.path.expanduser('~/extella-mult/assets/lib'), REPO_MULT):
        if p and os.path.isdir(os.path.join(p, 'puppet-characters-code')):
            return p
    return REPO_MULT


def _p(*parts):
    return os.path.join(lib_root(), *parts)


@functools.lru_cache(None)
def chars():
    d = _p('puppet-characters-code', 'chars')
    return {n: os.path.join(d, n) for n in sorted(os.listdir(d))
            if os.path.isfile(os.path.join(d, n, 'char.json'))} if os.path.isdir(d) else {}


@functools.lru_cache(None)
def char_info(name):
    return json.load(open(os.path.join(chars()[name], 'char.json'), encoding='utf-8'))


@functools.lru_cache(None)
def plates():
    d = _p('puppet-plates-code', 'plates')
    return {n: os.path.join(d, n) for n in sorted(os.listdir(d))
            if os.path.isfile(os.path.join(d, n, 'plate.json'))} if os.path.isdir(d) else {}


@functools.lru_cache(None)
def plate_info(name):
    return json.load(open(os.path.join(plates()[name], 'plate.json'), encoding='utf-8'))


@functools.lru_cache(None)
def procedural_props():
    """name -> png; also 'category/name'."""
    d = _p('puppet-procedural', 'png')
    out = {}
    for f in sorted(glob.glob(os.path.join(d, '*', '*.png'))):
        cat = os.path.basename(os.path.dirname(f))
        n = os.path.basename(f)[:-4]
        out.setdefault(n, f)
        out[f'{cat}/{n}'] = f
    return out


@functools.lru_cache(None)
def effects():
    p = _p('puppet-effects-code', 'effects.json')
    if not os.path.isfile(p):
        return {}
    base = os.path.dirname(p)
    out = {}
    for e in json.load(open(p, encoding='utf-8'))['effects']:
        seq = os.path.join(base, os.path.dirname(e['seq']))
        if os.path.isdir(seq):
            e = dict(e, dir=seq, files=sorted(glob.glob(os.path.join(seq, '*.png'))))
            out[e['name']] = e
    return out


def _media(kind, exts):
    d = _p('puppet-oss', 'media', kind)
    out = {}
    for f in sorted(glob.glob(os.path.join(d, '*'))):
        n, e = os.path.splitext(os.path.basename(f))
        if e.lower() in exts:
            out[n] = f
    return out


@functools.lru_cache(None)
def sfx():
    return _media('sfx', ('.ogg', '.wav', '.mp3', '.flac'))


@functools.lru_cache(None)
def music_files():
    return _media('music', ('.ogg', '.wav', '.mp3', '.flac'))


@functools.lru_cache(None)
def fonts():
    """family -> ttf (the first regular-looking file of each family folder)."""
    out = {}
    for d in sorted(glob.glob(_p('puppet-oss', 'media', 'fonts', '*'))):
        fs = sorted(glob.glob(os.path.join(d, '*.ttf')), key=lambda f: ('Italic' in f, 'Bold' in f, len(f)))
        if fs:
            out[os.path.basename(d)] = fs[0]
    return out


def default_font():
    for p in (os.path.join(HANDLER_ROOT, 'assets', 'fonts', 'Caveat.ttf'), fonts().get('caveat')):
        if p and os.path.isfile(p):
            return p
    return None


@functools.lru_cache(None)
def motion():
    """puppet-procedural/motion.py as a module (camera moves and transitions)."""
    d = _p('puppet-procedural')
    if d not in sys.path:
        sys.path.insert(0, d)
    import motion as m
    return m


def near(name, names, k=5):
    """A few names close to a misspelt one, for error messages."""
    import difflib
    names = list(names)
    hits = difflib.get_close_matches(name, names, n=k, cutoff=0.5)
    if len(hits) < k:
        hits += [n for n in names if name and (name in n or n.split('-')[0] == name.split('-')[0]) and n not in hits][:k - len(hits)]
    return hits
