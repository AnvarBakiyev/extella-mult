"""style=puppet: felt puppet films from a short program.

Two kinds of picture:
- photo sets (generated once): a few stills of the same frame, base (mouth closed), open, mid, blink. Only the region
  where a variant differs from the base is pasted in, with a soft mask, so the rest of the picture never flickers.
  The mouth follows the loudness of the voice.
- code-built shots: a layered felt plate (puppet-plates-code) with one or more code-built busts
  (puppet-characters-code) cast on it. Layers move at their own parallax speed with the camera; the speaker's mouth
  follows Russian visemes (handler/visemes.py) laid over the loudness of the recording, or over a synthetic envelope
  when there is no recording.

Over the shots: props (felt cut-outs), animated felt effects, text, transitions between shots, fades; under them:
voices, CC0 sound effects and music, or the built-in synth music.

The language, one statement a line (# starts a comment):

film title="Лосось" style=puppet fps=24 size=1920x1080 [voices=off]
shot 0-6s: <set | plate | stage> push=0.05 pan=right focus=0.5,0.4 ...
cast <char> on <plate> at x,y [size=0.62] [facing=left|right] [mood=neutral] [as=<stage>]
cast <char> on <plate> at x,y body=full [size=0.7] ...: the whole puppet; x,y is where its feet stand
act <char> <move> A-Bs [to=x]: a full-body puppet moves (walk, run, wave, point, shrug, jump, dance, ...); to=x walks it there
say <set | char> "реплика" at 0.4s [who=voice] [mood=neutral|happy|angry|shocked] [file=...]
voice "реплика" at 12s [who=deep]
text "РЕКЛАМА" at 0.5,0.15 size=0.1 color=#ffffff [font=oswald] 30-33s
prop <name> at x,y size=0.15 [bob=0.01] 12-18s
prop <name> in=<char>.hand [size=0.12] 12-18s: a full-body puppet holds it (in=<char>.left_hand for the other hand)
fx <effect> 2-6s [at x,y] [opacity=1]
sfx <name> at 3.2s [gain=1]
music mood=tense key=D tempo=80 [A-Bs]  |  music file=<name> [A-Bs] [gain=0.5]
cut wipe|iris|dissolve|whip|dip [at] Xs [dur=0.6] [dir=left|right]
fade in 0-0.6s  |  fade out 50-51s
"""
import json
import math
import os
import re
import shlex
import subprocess

import numpy as np
from PIL import Image, ImageFilter

from . import library as lib
from . import visemes as V
from .config import ffmpeg

SR = 48000


def _load(path, size):
    return Image.open(path).convert('RGB').resize(size, Image.LANCZOS)


def diff_mask(base, var, thr=18, grow=9, feather=6):
    """Soft mask of where var differs from base: the face part that changed."""
    a = np.asarray(base, np.int16)
    b = np.asarray(var, np.int16)
    d = (np.abs(a - b).max(axis=2) > thr).astype(np.uint8) * 255
    m = Image.fromarray(d, 'L').filter(ImageFilter.MedianFilter(5)).filter(ImageFilter.MaxFilter(grow * 2 + 1))
    # keep only the big changed regions (eyes, mouth); small specks are re-drawn wool fibres and would flicker
    from scipy.ndimage import label
    arr = np.asarray(m) > 0
    lab, n = label(arr)
    if n == 0:
        return Image.new('L', base.size, 0)
    sizes = np.bincount(lab.ravel())[1:]
    keep = np.zeros_like(arr)
    for k in np.nonzero(sizes >= max(1500, sizes.max() * 0.08))[0]:
        keep |= lab == k + 1
    return Image.fromarray((keep * 255).astype(np.uint8), 'L').filter(ImageFilter.GaussianBlur(feather))


def _decode_mono(path):
    raw = subprocess.run([ffmpeg(), '-v', 'error', '-i', path, '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def mouth_track(wav, fps, n):
    """Photo sets, per frame: 0 closed, 1 half open, 2 open, from the voice loudness."""
    rms = V.loudness(_decode_mono(wav), SR, fps, n)
    return mouth_from_env(rms)


def mouth_from_env(rms):
    rms = np.asarray(rms, np.float64)
    top = np.percentile(rms[rms > 0], 90) if (rms > 0).any() else 1
    r = rms / (top + 1e-9)
    # a mouth flaps on syllables: wide open near loud local peaks, half open on the softer parts of a syllable,
    # closed in the dips and in silence; never held wide open for more than 3 frames
    out, run = [], 0
    for i in range(len(r)):
        lo, hi = max(0, i - 2), min(len(r), i + 3)
        peak = r[lo:hi].max()
        o = 0
        if r[i] > 0.2:
            o = 2 if (r[i] >= 0.85 * peak and r[i] > 0.45) else (1 if r[i] >= 0.45 * peak else 0)
        run = run + 1 if o == 2 else 0
        if run > 3:
            o, run = 1, 0
        out.append(o)
    return out


# ---------------------------------------------------------------------------------------------------------------
# the library on this device

SETS = os.path.expanduser('~/extella-mult/assets/puppet')
REPO_SETS = os.path.join(lib.HANDLER_ROOT, 'sets')   # set.json + thumb.jpg of every photo set, without the pictures
PROPS = os.path.expanduser('~/extella-mult/assets/props')
PANS = {'left': (-1, 0), 'right': (1, 0), 'up': (0, -1), 'down': (0, 1), 'none': (0, 0)}
MOODS = ('neutral', 'happy', 'angry', 'shocked')
FACING = ('left', 'right', 'front')
TRANSITIONS = {'wipe': 'wipe', 'wipe_left': 'wipe_left', 'wipe_right': 'wipe_right', 'iris': 'iris',
               'dissolve': 'cross_dissolve', 'whip': 'whip_pan', 'dip': 'dip_to_black', 'dip_white': 'dip_to_white',
               'page': 'page_turn', 'slide': 'slide'}
STATEMENTS = 'film, shot, cast, act, say, voice, text, prop, fx, sfx, music, cut, fade'
SUBJECT_PARALLAX = 0.8   # characters stand between the near (0.72) and the front (1.1) layers of a plate
OVERSCAN = 1.06          # plate layers are seen a little closer so a parallax move never shows an edge

_PROP_CACHE = {}


def _anim():
    """The full-body rig renderer (puppet-characters-body/anim.py), loaded on first use."""
    import importlib.util
    import sys
    if 'puppet_anim' not in sys.modules:
        spec = importlib.util.spec_from_file_location('puppet_anim', lib._p('puppet-characters-body', 'anim.py'))
        m = importlib.util.module_from_spec(spec)
        sys.modules['puppet_anim'] = m
        spec.loader.exec_module(m)
    return sys.modules['puppet_anim']


def body_chars():
    d = lib._p('puppet-characters-body', 'body')
    return {n for n in os.listdir(d) if os.path.isfile(os.path.join(d, n, 'rig.json'))} if os.path.isdir(d) else set()


def body_moves():
    a = _anim()
    return sorted(set(a.POSES) | set(a.CYCLES))


class PuppetError(Exception):
    pass


def props_list():
    """Felt cut-outs: the device folder first, then the code-drawn props (puppet-procedural/png)."""
    out = dict(lib.procedural_props())
    for root, _, files in os.walk(PROPS) if os.path.isdir(PROPS) else []:
        for f in files:
            if f.endswith('.png'):
                out[f[:-4]] = os.path.join(root, f)
    return out


def sets_list():
    """Photo sets: those with pictures on this device, and those described in the repository (sets/<name>/set.json)."""
    names = set()
    if os.path.isdir(SETS):
        names |= {d for d in os.listdir(SETS) if os.path.isfile(os.path.join(SETS, d, 'base.png'))}
    if os.path.isdir(REPO_SETS):
        names |= {d for d in os.listdir(REPO_SETS) if os.path.isfile(os.path.join(REPO_SETS, d, 'set.json'))}
    return sorted(names)


def set_info(name):
    for d in (SETS, REPO_SETS):
        p = os.path.join(d, name, 'set.json')
        if os.path.isfile(p):
            return json.load(open(p, encoding='utf-8'))
    return {}


def set_talks(name):
    return os.path.isfile(os.path.join(SETS, name, 'open.png')) or bool(set_info(name).get('talks'))


def set_has_pictures(name):
    return os.path.isfile(os.path.join(SETS, name, 'base.png'))


def resolve_plate(name):
    """A plate by its full name, or by its place (tv_studio -> the first tv_studio plate)."""
    ps = lib.plates()
    if name in ps:
        return name
    pre = [p for p in ps if p.split('-v')[0] == name]
    return pre[0] if pre else None


def _hint(name, names, what):
    near = lib.near(name, names)
    return f"; did you mean {', '.join(near)}?" if near else f"; run tools/puppet_find.py '{what}' to find one"


class Line:
    def __init__(self, kind, n, raw):
        self.kind, self.n, self.raw = kind, n, raw
        self.words, self.params, self.text = [], {}, None
        self.t0 = self.t1 = self.at = None
        self.pos = None


def _num(v):
    try:
        return float(v)
    except ValueError:
        return v


def _tokenize(n, raw):
    line = raw.split('#', 1)[0].strip() if not re.search(r'"[^"]*#', raw) else raw.strip()
    if not line:
        return None
    line = line.replace('：', ':')
    try:
        toks = shlex.split(line.replace(': ', ' : ', 1) if line.startswith('shot') else line)
    except ValueError:
        raise PuppetError(f'line {n}: unclosed quote')
    head = toks[0]
    L = Line(head, n, raw)
    for t in toks[1:]:
        m = re.fullmatch(r'(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)s', t)
        if m:
            if L.t0 is not None:
                raise PuppetError(f'line {n}: two time ranges on one line ({L.t0:g}-{L.t1:g}s and {t}); '
                                  f'put fade, act or text on a line of its own, e.g. fade in 0-0.6s')
            L.t0, L.t1 = float(m.group(1)), float(m.group(2))
        elif re.fullmatch(r'\d+(?:\.\d+)?s', t) and L.words and L.words[-1] == 'at':
            L.words.pop()
            L.at = float(t[:-1])
        elif re.fullmatch(r'\d+(?:\.\d+)?s', t) and head == 'cut' and L.at is None:
            L.at = float(t[:-1])
        elif re.fullmatch(r'-?\d*\.?\d+,-?\d*\.?\d+', t) and L.words and L.words[-1] == 'at':
            L.words.pop()
            L.pos = tuple(float(x) for x in t.split(','))
        elif '=' in t and not t.startswith('[') and not (L.text is None and ' ' in t and (head in ('voice', 'text') or (head == 'say' and L.words))):
            k, v = t.split('=', 1)
            if k == 'at' and re.fullmatch(r'-?\d*\.?\d+,-?\d*\.?\d+', v):
                L.pos = tuple(float(x) for x in v.split(','))
            else:
                L.params[k] = _num(v)
        elif t == ':':
            continue
        elif L.text is None and t != 'at' and ((head == 'say' and L.words) or head in ('voice', 'text')):
            L.text = t  # the words in quotes: after the speaker for say, first for voice and text
        else:
            L.words.append(t)
    return L


def _duration(path):
    r = subprocess.run([ffmpeg(), '-i', path], capture_output=True, text=True).stderr
    m = re.search(r'Duration: (\d+):(\d+):([\d.]+)', r)
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) if m else None


def parse_puppet(src, no_audio=False):
    """Parse and check a puppet film; errors say what to fix, with the line number.
    no_audio: voice recordings are neither needed nor used (lines are silent, mouths follow a synthetic envelope)."""
    from .audio import VOICES
    film, shots, casts, says, texts, fades, music, sfx, fx, cuts = {}, [], [], [], [], [], [], [], [], []
    acts = {}
    held = []
    warnings = []
    lines = [L for L in (_tokenize(n, raw) for n, raw in enumerate(src.splitlines(), 1)) if L is not None]
    for L in lines:
        if L.kind == 'film':
            film = L.params
    voices_off = no_audio or str(film.get('voices', 'on')) in ('off', '0', 'none')
    # first pass: everything except the shots, so that cast lines may come before or after their shots
    stages = {}
    for L in lines:
        n, head = L.n, L.kind
        if head in ('film', 'shot'):
            continue
        if head == 'cast':
            if len(L.words) < 3 or L.words[1] != 'on':
                raise PuppetError(f"line {n}: cast <character> on <plate> at x,y size=0.62 facing=left|right, "
                                  f"e.g. cast aigul on tv_studio-v0-day-clear at 0.3,0.55")
            who, plate = L.words[0], L.words[2]
            if who not in lib.chars():
                raise PuppetError(f"line {n}: no code character '{who}'" + _hint(who, lib.chars(), 'talking character ' + who))
            full = resolve_plate(plate)
            if not full:
                raise PuppetError(f"line {n}: no plate '{plate}'" + _hint(plate, lib.plates(), 'plate ' + plate))
            if L.pos is None:
                raise PuppetError(f"line {n}: where does {who} stand? add at x,y (head centre, 0..1 of the frame), e.g. at 0.3,0.55")
            x, y = L.pos
            if not (0 <= x <= 1 and 0 <= y <= 1):
                raise PuppetError(f"line {n}: at {x:g},{y:g} is off the frame; x and y go from 0 to 1")
            if str(L.params.get('facing', 'front')) not in FACING:
                raise PuppetError(f"line {n}: facing must be left or right (or front)")
            if str(L.params.get('mood', 'neutral')) not in MOODS:
                raise PuppetError(f"line {n}: mood must be one of {', '.join(MOODS)}")
            L.body = str(L.params.get('body', '')) == 'full'
            if L.body and who not in body_chars():
                raise PuppetError(f"line {n}: {who} has no full body yet; drop body=full to cast the bust")
            size = float(L.params.get('size', 0.7 if L.body else 0.62))
            if not 0.05 <= size <= 1.6:
                raise PuppetError(f"line {n}: size={size:g} is the bust height as a part of the frame height; use 0.3-1.0")
            stage = str(L.params.get('as', plate))
            st = stages.setdefault(stage, {'plate': full, 'cast': {}, 'n': n})
            if st['plate'] != full:
                raise PuppetError(f"line {n}: the stage '{stage}' is already on plate {st['plate']} (line {st['n']}); "
                                  f"give this one another name with as=<name>")
            if who in st['cast']:
                raise PuppetError(f"line {n}: {who} is already cast on {stage} (line {st['cast'][who].n}); "
                                  f"to stage the same plate twice, add as=<name> to one of the cast lines")
            L.stage, L.plate = stage, full
            st['cast'][who] = L
            casts.append(L)
            bottom = y + (1 - _head_frac(who)) * size
            if not L.body and bottom < 0.96:
                warnings.append(f"line {n}: the bust of {who} ends at {bottom:.2f} of the frame height and floats; "
                                f"move it down (larger y) or make it bigger (size=)")
        elif head in ('say', 'voice'):
            if L.at is None:
                raise PuppetError(f"line {n}: {head} needs a start time: ... at 2s")
            if head == 'say':
                if not L.words:
                    raise PuppetError(f"line {n}: say needs who speaks: a set (say salmon_studio \"...\" at 1s) "
                                      f"or a cast character (say aigul \"...\" at 1s mood=happy)")
                who = L.words[0]
                # a name that is both a code character and a picture set (oil_barrel) is the set unless it was cast
                is_cast = any(who in st['cast'] for st in stages.values())
                if who in lib.chars() and (is_cast or who not in sets_list()):
                    L.char = True
                    if not any(who in st['cast'] for st in stages.values()):
                        raise PuppetError(f"line {n}: {who} speaks but is not cast on any plate; add "
                                          f"cast {who} on <plate> at x,y")
                    mood = str(L.params.get('mood', 'neutral'))
                    if mood not in MOODS:
                        raise PuppetError(f"line {n}: mood must be one of {', '.join(MOODS)}")
                elif who in sets_list():
                    L.char = False
                    if not set_talks(who):
                        raise PuppetError(f"line {n}: set {who} has no talking mouth (open.png); use voice for an off-screen line")
                else:
                    raise PuppetError(f"line {n}: no set or code character '{who}'"
                                      + _hint(who, sets_list() + list(lib.chars()), 'talking character ' + who))
            # the voice: who=..., else the speaker's own voice; off screen: a leading [voice] tag, else the deep narrator
            if L.text and 'who' not in L.params and head == 'voice':
                m = re.match(r'\s*\[([a-z_]+)\]\s*', L.text)
                if m and m.group(1) in VOICES:
                    L.params['who'] = m.group(1)
                    L.text = L.text[m.end():]
            if L.text and 'who' not in L.params:
                if head == 'say' and L.char:
                    v = lib.char_info(L.words[0]).get('default_voice', 'narrator')
                    L.params['who'] = v if v in VOICES else 'narrator'
                else:
                    L.params['who'] = set_info(L.words[0]).get('voice', 'narrator') if head == 'say' else 'deep'
            if 'file' in L.params:
                if not os.path.isfile(os.path.expanduser(str(L.params['file']))):
                    if voices_off:
                        warnings.append(f"line {n}: file {L.params['file']} not found; silent, mouth follows the text")
                    else:
                        raise PuppetError(f"line {n}: file {L.params['file']} not found (check without recordings: --no-audio)")
            elif not L.text:
                raise PuppetError(f'line {n}: the words go in quotes: {head} ... "Привет!" at 2s who=narrator')
            else:
                who = str(L.params.get('who', 'narrator'))
                if who not in VOICES:
                    raise PuppetError(f"line {n}: unknown voice who={who}; voices: {', '.join(VOICES)}")
            says.append(L)
        elif head == 'text':
            if not L.text:
                raise PuppetError(f'line {n}: the words of a text go in quotes: text "..." at 0.5,0.2 size=0.08 color=#ffffff 3-6s')
            if L.t0 is None:
                raise PuppetError(f'line {n}: a text needs its time on screen, e.g. 3-6s at the end: text "{L.text[:20]}" at 0.5,0.9 3-6s')
            if 'font' in L.params and str(L.params['font']) not in lib.fonts():
                raise PuppetError(f"line {n}: no font '{L.params['font']}'; fonts: {', '.join(lib.fonts())}")
            texts.append(L)
        elif head == 'prop':  # prop coffee_cup at 0.7,0.8 size=0.15 12-18s: a felt cut-out placed over the shot
            if not L.words or L.words[0] not in props_list():
                nm = L.words[0] if L.words else ''
                raise PuppetError(f"line {n}: no prop '{nm}' on this device" + _hint(nm, props_list(), 'prop ' + nm))
            if L.t0 is None:
                raise PuppetError(f"line {n}: a prop needs its time: prop {L.words[0]} at 0.7,0.8 size=0.15 12-18s")
            if len(L.words) > 1:
                raise PuppetError(f"line {n}: a prop is either placed or held: prop {L.words[0]} at x,y size=0.15 A-Bs, "
                                  f"or prop {L.words[0]} in=<character>.hand A-Bs; '{' '.join(L.words[1:])}' is not part of it")
            if 'in' in L.params:
                m = re.fullmatch(r'([a-z0-9_]+)\.(hand|left_hand|right_hand)', str(L.params['in']))
                if not m:
                    raise PuppetError(f"line {n}: in= names who holds it: prop {L.words[0]} in=<character>.hand 12-18s")
                L.holder, L.side = m.group(1), 'L' if m.group(2) == 'left_hand' else 'R'
                held.append(L)
            else:
                texts.append(L)
        elif head == 'fx':
            if not L.words or L.words[0] not in lib.effects():
                nm = L.words[0] if L.words else ''
                raise PuppetError(f"line {n}: no effect '{nm}'" + _hint(nm, lib.effects(), 'effect ' + nm))
            if L.t0 is None:
                raise PuppetError(f"line {n}: an effect needs its time: fx {L.words[0]} 2-5s")
            fx.append(L)
        elif head == 'sfx':
            if not L.words or L.words[0] not in lib.sfx():
                nm = L.words[0] if L.words else ''
                raise PuppetError(f"line {n}: no sound '{nm}'" + _hint(nm, lib.sfx(), 'sfx ' + nm))
            if L.at is None:
                raise PuppetError(f"line {n}: a sound needs its time: sfx {L.words[0]} at 3s")
            sfx.append(L)
        elif head == 'cut':
            if not L.words or L.words[0] not in TRANSITIONS:
                raise PuppetError(f"line {n}: cut <transition> at Xs dur=0.6; transitions: {', '.join(TRANSITIONS)}")
            if L.at is None:
                raise PuppetError(f"line {n}: when? cut {L.words[0]} at 12s (at a shot boundary)")
            if 'dir' in L.params and str(L.params['dir']) not in ('left', 'right'):
                raise PuppetError(f"line {n}: dir must be left or right")
            cuts.append(L)
        elif head == 'fade':
            if not L.words or L.words[0] not in ('in', 'out') or L.t0 is None:
                raise PuppetError(f"line {n}: fade in 0-1s or fade out 40-41s")
            fades.append(L)
        elif head == 'act':  # act aigul walk 2-5s to=0.7
            if len(L.words) < 2:
                raise PuppetError(f"line {n}: act <character> <move> A-Bs, e.g. act aigul walk 2-5s to=0.7")
            who, mv = L.words[0], L.words[1]
            if mv not in body_moves():
                raise PuppetError(f"line {n}: no move '{mv}'; moves: {', '.join(body_moves())}")
            if L.t0 is None:
                raise PuppetError(f"line {n}: when? act {who} {mv} 2-5s")
            if 'to' in L.params and not isinstance(L.params['to'], float):
                raise PuppetError(f"line {n}: to= is the x the puppet walks to, 0..1, e.g. to=0.7")
            acts.setdefault(who, []).append(L)
        elif head == 'music':
            if 'file' in L.params:
                nm = str(L.params['file'])
                if nm not in lib.music_files() and not os.path.isfile(os.path.expanduser(nm)):
                    raise PuppetError(f"line {n}: no music '{nm}'" + _hint(nm, lib.music_files(), 'music ' + nm))
            music.append(L)
        else:
            raise PuppetError(f"line {n}: '{head}' is not a statement; statements: {STATEMENTS}")
    # the shots: a photo set, a stage made by cast lines, or a bare plate
    for L in lines:
        if L.kind != 'shot':
            continue
        n = L.n
        if L.t0 is None:
            raise PuppetError(f"line {n}: a shot needs its time: shot 0-6s: salmon_studio")
        if not L.words:
            raise PuppetError(f"line {n}: which set or plate does the shot show? e.g. shot 0-6s: salmon_studio "
                              f"or shot 0-6s: tv_studio-v0-day-clear")
        name = L.words[0]
        if name in stages:
            L.src, L.plate, L.cast = 'stage', stages[name]['plate'], list(stages[name]['cast'].values())
        elif name in sets_list():
            L.src = 'set'
            if not set_has_pictures(name) and name not in [x.words[0] for x in shots]:
                warnings.append(f"line {n}: set {name} has only its thumbnail on this device; the render uses thumb.jpg without a moving mouth")
        elif resolve_plate(name):
            L.src, L.plate, L.cast = 'plate', resolve_plate(name), []
        else:
            raise PuppetError(f"line {n}: no set, plate or cast stage '{name}' on this device"
                              + _hint(name, sets_list() + list(stages) + list(lib.plates()), 'plate ' + name))
        if str(L.params.get('pan', 'none')) not in PANS:
            raise PuppetError(f"line {n}: pan must be one of {', '.join(PANS)}")
        shots.append(L)
    if not shots:
        raise PuppetError('no shots: add shot 0-6s: <set or plate>')
    shots.sort(key=lambda s: s.t0)
    if shots[0].t0 != 0:
        raise PuppetError(f'line {shots[0].n}: the first shot must start at 0s')
    for a, b in zip(shots, shots[1:]):
        if abs(a.t1 - b.t0) > 1e-6:
            raise PuppetError(f'line {b.n}: shots must touch: the previous one ends at {a.t1:g}s, this one starts at {b.t0:g}s')
    length = shots[-1].t1
    stage_names = [s.words[0] for s in shots]
    for st, v in stages.items():
        if st not in stage_names:
            warnings.append(f"line {v['n']}: the stage '{st}' made by cast is never shown; add shot A-Bs: {st}")
    # a cast character speaks only when its stage is on screen
    for L in says:
        if L.kind == 'say' and getattr(L, 'char', False):
            sh = next((x for x in shots if x.t0 <= L.at < x.t1), None)
            if sh is not None and L.words[0] not in [c.words[0] for c in getattr(sh, 'cast', [])]:
                where = [s for s, v in stages.items() if L.words[0] in v['cast']]
                raise PuppetError(f"line {L.n}: {L.words[0]} speaks at {L.at:g}s, but the shot then (line {sh.n}, "
                                  f"{sh.words[0]}) does not have {L.words[0]} in it; show {', '.join(where)} at that "
                                  f"time or use voice for an off-screen line")
    for c in cuts:
        k = next((i for i, s in enumerate(shots[1:]) if abs(s.t0 - c.at) < 0.05), None)
        if k is None:
            raise PuppetError(f"line {c.n}: cut at {c.at:g}s is not where one shot meets the next; shot boundaries: "
                              + ', '.join(f'{s.t0:g}s' for s in shots[1:]))
        d = float(c.params.get('dur', 0.6))
        room = min(shots[k].t1 - shots[k].t0, shots[k + 1].t1 - shots[k + 1].t0)
        if not 0.05 <= d <= room:
            raise PuppetError(f"line {c.n}: dur={d:g}s does not fit: the shots on both sides last at least {room:g}s")
        c.at = shots[k + 1].t0
        c.dur = d
    # recordings: missing ones are listed for the person to record; real lengths must fit the timing
    missing = []
    from .audio import voice_key, voice_cache_path
    for L in says:
        L.audio = None
        if voices_off:
            continue
        if 'file' in L.params:
            L.audio = os.path.expanduser(str(L.params['file']))
        else:
            p = voice_cache_path(str(L.params.get('who', 'narrator')), L.text)
            if os.path.isfile(p) or voice_key():
                L.audio = p
            else:
                missing.append({'line': L.n, 'who': str(L.params.get('who', 'narrator')), 'text': L.text, 'file': p})
    if missing:
        raise PuppetError(f"{len(missing)} spoken line(s) are not recorded yet and this device has no ElevenLabs key. "
                          "Show the person the lines below; they record them with their own ElevenLabs and the film renders after that "
                          "(or check and render without voices: --no-audio, or film ... voices=off). "
                          "LINES_TO_RECORD " + json.dumps(missing, ensure_ascii=False))
    timed, synthetic = [], []
    for L in says:
        if L.audio and os.path.isfile(L.audio):
            d = _duration(L.audio)
            if d:
                timed.append((L, d))
        else:
            synthetic.append((L, V.estimate_seconds(L.text or '')))
    problems = _fit(timed, shots)
    if problems:
        raise PuppetError('the recorded lines do not fit the timing. Lengths: ' + '; '.join(f"line {L.n} {d:.1f}s" for L, d in timed)
                          + '. Problems: ' + '; '.join(problems) + '. Re-time the shots and the at= times to the real lengths '
                          '(start each line 0.3s after its shot begins, end the shot 0.4s after the line ends, shift everything after); do not change the words.')
    soft = _fit(synthetic, shots, slack=0.5)
    if soft:
        msg = ('without recordings a line takes about 6 syllables a second, so: ' + '; '.join(soft)
               + '. Shorten the words or give the line more time.')
        if no_audio and not str(film.get('voices', 'on')) in ('off', '0', 'none'):
            warnings.append(msg)   # the real recordings decide; the estimate is only a hint here
        else:
            raise PuppetError(msg)
    for who, al in acts.items():
        if not any(c.words[0] == who and c.body for c in casts):
            raise PuppetError(f"line {al[0].n}: {who} acts but is not cast with body=full; "
                              f"add cast {who} on <plate> at x,y body=full")
        al.sort(key=lambda L: L.t0)
    _check_crowding(casts, acts, length)
    for L in held:
        if not any(c.words[0] == L.holder and c.body for c in casts):
            raise PuppetError(f"line {L.n}: {L.holder} holds {L.words[0]} but is not cast with body=full; "
                              f"add cast {L.holder} on <plate> at x,y body=full")
    for L in says + texts + fades + fx + sfx:
        t = L.at if L.at is not None else L.t0
        if t < 0 or t >= length:
            raise PuppetError(f'line {L.n}: {L.kind} at {t:g}s is outside the film (0-{length:g}s)')
    size = tuple(int(x) for x in str(film.get('size', '1920x1080')).split('x'))
    return dict(title=str(film.get('title', '')), fps=int(film.get('fps', 24)), size=size, length=length,
                shots=shots, says=says, texts=texts, fades=fades, music=music, casts=casts, stages=stages,
                sfx=sfx, fx=fx, cuts=cuts, warnings=warnings, voices_off=voices_off, acts=acts, held=held,
                look=str(film.get('look', 'warm')))


def body_x(c, acts, t):
    """Where a full-body cast stands at time t: its at x, moved by walk/run acts with to=."""
    x = c.pos[0]
    for a in acts.get(c.words[0], []):
        tx = a.params.get('to')
        if tx is None or t < a.t0:
            continue
        x = tx if t >= a.t1 else x + (tx - x) * (t - a.t0) / max(1e-6, a.t1 - a.t0)
    return x


def _check_crowding(casts, acts, length):
    """Two full bodies on one stage must not stand inside each other: the eye reads it as one two-headed puppet."""
    by_stage = {}
    for c in casts:
        if c.body:
            by_stage.setdefault(str(c.params.get('as', c.words[2])), []).append(c)
    for st, cs in by_stage.items():
        for i, a in enumerate(cs):
            for b in cs[i + 1:]:
                gap = 0.12 * (float(a.params.get("size", 0.7)) + float(b.params.get("size", 0.7))) / 1.4
                for k in range(int(length * 4) + 1):
                    t = k / 4
                    d = abs(body_x(a, acts, t) - body_x(b, acts, t))
                    if d < gap:
                        raise PuppetError(f"line {b.n}: at {t:g}s {a.words[0]} and {b.words[0]} stand {d:.2f} apart on {st} "
                                          f"and overlap; keep full bodies at least {gap:.2f} apart (change to= or at x)")


def _fit(timed, shots, slack=0.25):
    problems = []
    timed = sorted(timed, key=lambda x: x[0].at)
    for i, (L, d) in enumerate(timed):
        end = L.at + d
        sh = next((x for x in shots if x.t0 <= L.at < x.t1), None)
        if L.kind == 'say' and sh is not None and end > sh.t1 + slack:
            problems.append(f"line {L.n}: the line lasts {d:.1f}s, so it ends at {end:.1f}s but its shot ends at {sh.t1:g}s")
        if i + 1 < len(timed) and end > timed[i + 1][0].at + 0.1 + (slack - 0.25):
            problems.append(f"line {L.n} ends at {end:.1f}s and overlaps line {timed[i + 1][0].n} that starts at {timed[i + 1][0].at:g}s")
    return problems


def _head_frac(name):
    """Where the head centre sits in the cropped bust, 0 top .. 1 bottom."""
    info = lib.char_info(name)
    bb = _char_bbox(name)
    hy = info.get('anchors', {}).get('head_center', [0.5, 0.44])[1] * info.get('size', [1024, 1024])[1]
    return (hy - bb[1]) / max(1, bb[3] - bb[1])


_BBOX = {}


def _char_bbox(name):
    if name not in _BBOX:
        _BBOX[name] = Image.open(os.path.join(lib.chars()[name], 'base.png')).getbbox() or (0, 0, 1024, 1024)
    return _BBOX[name]


# ---------------------------------------------------------------------------------------------------------------
# rendering

class BodyPuppet:
    """A full-body felt puppet (puppet-characters-body): rig parts posed by anim.play and scaled to the shot."""

    def __init__(self, name):
        A = _anim()
        self.A = A
        self.p = A.Puppet(name, view='q34', scale=0.5, root=lib._p('puppet-characters-body', 'body'))
        arr, (ox, oy) = self.p.render(A.play('stand', 0, self.p))
        img = A.to_image(arr)
        self.h0 = oy - img.getbbox()[1]   # standing height in rig px, feet to the top of the head

    def gait_time(self, move, dist_px, hpx):
        """Cycle time for walk/run after travelling dist_px on screen: one period per stride, so the planted foot stays put."""
        A, k = self.A, hpx / self.h0
        c = A.clip(move)
        return dist_px / max(1e-6, A.stride(self.p, move) * k) * c.loop[1]

    # moves whose arms only hang or swing: a held prop bends that forearm forward to carry it
    CARRY = {'idle', 'stand', 'walk', 'run', 'nod', 'head_shake', 'laugh', 'bow', 'thinking', 'jump', 'dance'}

    def sprite(self, move, t, mood, mouth, blink, hpx, flip, hold=()):
        """The posed puppet scaled to hpx tall, its ground point (ox, oy) and the palm centre of each side in hold."""
        A = self.A
        pose = A.play(move, t, self.p)
        if hold and move in self.CARRY:
            pose = dict(pose)
            for side in hold:
                pose['upper_arm_' + side] = pose.get('upper_arm_' + side, 0) * 0.3 + (12 if side == 'R' else -12)
                pose['lower_arm_' + side] = 78 if side == 'R' else -78
                pose['hand_' + side] = 0
        arr, (ox, oy) = self.p.render(pose, expr=mood, mouth=mouth, blink=blink)
        img = A.to_image(arr)
        k = hpx / self.h0
        hands = {}
        if hold:
            M, s = self.p.place(pose), self.p.scale
            for side in hold:
                hx, hy = self.p.anchor(M, 'hand_' + side)
                hands[side] = ((hx * s + ox) * k, (hy * s + oy) * k)
        img = img.resize((max(1, int(img.width * k)), max(1, int(img.height * k))), Image.LANCZOS)
        ox, oy = ox * k, oy * k
        if flip:
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
            ox = img.width - ox
            hands = {sd: (img.width - x, y) for sd, (x, y) in hands.items()}
        return img, ox, oy, hands


class Puppet:
    """A code-built bust: base + expression + mouth + blink overlays, cropped to the bust."""

    def __init__(self, name):
        self.name = name
        self.dir = lib.chars()[name]
        self.info = lib.char_info(name)
        self.bbox = _char_bbox(name)
        self._img = {}
        self._frames = {}

    def _part(self, f):
        if f not in self._img:
            p = os.path.join(self.dir, f)
            self._img[f] = Image.open(p).convert('RGBA') if os.path.isfile(p) else None
        return self._img[f]

    def frame(self, mood='neutral', viseme=None, blink=False):
        key = (mood, viseme, blink)
        if key not in self._frames:
            img = self._part('base.png').copy()
            fr = self.info.get('frames', {})
            if mood != 'neutral':
                o = self._part(fr.get('expressions', {}).get(mood, f'expr_{mood}.png'))
                if o is not None:
                    img.alpha_composite(o)
            if viseme:
                o = self._part(fr.get('visemes', {}).get(viseme, f'mouth_{viseme}.png'))
                if o is not None:
                    img.alpha_composite(o)
            if blink:
                o = self._part(fr.get('blink', 'blink.png'))
                if o is not None:
                    img.alpha_composite(o)
            self._frames[key] = img.crop(self.bbox)
        return self._frames[key]


class Renderer:
    def __init__(self, prog, size=None, preview=False, no_audio=False):
        self.prog = prog
        W, H = size or prog['size']
        if preview:
            W, H = W // 2 // 2 * 2, H // 2 // 2 * 2
        self.W, self.H = W, H
        self.fps = prog['fps']
        self.n = int(round(prog['length'] * self.fps))
        self.no_audio = no_audio or prog.get('voices_off')
        self.look = prog.get('look', 'warm')
        self.sets, self.plates, self.puppets = {}, {}, {}
        self.fx_cache = {}
        self._sprite = {}
        for sh in prog['shots']:
            if sh.src == 'set':
                self._load_set(sh.words[0])
            else:
                self._load_plate(sh.plate)
                for c in sh.cast:
                    key = ('body:' if getattr(c, 'body', False) else '') + c.words[0]
                    if key not in self.puppets:
                        self.puppets[key] = BodyPuppet(c.words[0]) if key.startswith('body:') else Puppet(c.words[0])
        self._tracks()

    # --- pictures
    def _load_set(self, name):
        if name in self.sets:
            return
        W, H = self.W, self.H
        d = os.path.join(SETS, name)
        parts = {}
        if os.path.isfile(os.path.join(d, 'base.png')):
            base = _load(os.path.join(d, 'base.png'), (W, H))
            for k in ('open', 'mid', 'blink'):
                p = os.path.join(d, k + '.png')
                if os.path.isfile(p):
                    v = _load(p, (W, H))
                    parts[k] = (v, diff_mask(base, v))
        elif os.path.isfile(os.path.join(REPO_SETS, name, 'thumb.jpg')):
            base = _load(os.path.join(REPO_SETS, name, 'thumb.jpg'), (W, H))
        else:
            base = Image.new('RGB', (W, H), (60, 55, 60))
        self.sets[name] = (base, parts)

    def _load_plate(self, name):
        if name in self.plates:
            return
        d = lib.plates()[name]
        info = lib.plate_info(name)
        layers = []
        for l in sorted(info['layers'], key=lambda l: l['z']):
            im = Image.open(os.path.join(d, l['file'])).convert('RGBA')
            # keep a little more than the output size so a push stays sharp, but not the full 1920 when rendering small
            k = min(1.0, max(self.W / im.width, self.H / im.height) * 1.35)
            if k < 1:
                im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
            layers.append((l['layer'], float(l['parallax']), im))
        self.plates[name] = layers

    # --- what each mouth does on each frame
    def _tracks(self):
        fps, n = self.fps, self.n
        self.mouth = {name: np.zeros(n, np.int8) for name in self.sets}        # photo sets: 0/1/2
        self.vis = {name.split(":")[-1]: [None] * n for name in self.puppets}                   # code chars: viseme or None
        self.mood = {name.split(":")[-1]: [None] * n for name in self.puppets}
        self.voice_clips = []
        for L in self.prog['says']:
            path = None if self.no_audio else getattr(L, 'audio', None)
            if path and os.path.isfile(path):
                sig = _decode_mono(path)
                self.voice_clips.append((L, sig))
                env = V.loudness(sig, SR, fps)
            else:
                env = V.synthetic_envelope(L.text or '', fps)
            if L.kind != 'say':
                continue
            f0 = int(round(L.at * fps))
            who = L.words[0]
            if getattr(L, 'char', False):
                tr = V.viseme_track(L.text or '', env)
                mood = str(L.params.get('mood', 'neutral'))
                for k, v in enumerate(tr):
                    if f0 + k < n:
                        self.vis[who][f0 + k] = v
                for k in range(len(tr) + int(0.4 * fps)):   # the mood holds a little after the line
                    if f0 + k < n:
                        self.mood[who][f0 + k] = mood
            elif who in self.mouth:
                tr = mouth_from_env(env)
                for k, o in enumerate(tr):
                    if f0 + k < n:
                        self.mouth[who][f0 + k] = max(self.mouth[who][f0 + k], o)

    # --- the camera
    def _camera(self, sh, t):
        tl = max(0.0, t - sh.t0)
        dur = sh.t1 - sh.t0
        e = 0.5 - 0.5 * math.cos(math.pi * min(1, tl / dur))
        P = sh.params
        z = 1 + float(P.get('push', 0.04 if 'pull' not in P else 0)) * e + (0.08 if P.get('pan', 'none') != 'none' else 0)
        if 'pull' in P:  # starts close and pulls back to the whole picture
            z += float(P['pull']) * (1 - e)
        if 'snap' in P:  # a sudden crash zoom at that second of the film
            k = (t - float(P['snap'])) / 0.12
            z += float(P.get('snapz', 0.35)) * (0 if k < 0 else min(1, k))
        dx, dy = PANS[str(P.get('pan', 'none'))]
        if 'focus' in P:
            fx, fy = (float(v) for v in str(P['focus']).split(','))
        elif getattr(sh, 'cast', None):
            fx = sum(c.pos[0] for c in sh.cast) / len(sh.cast)
            fy = sum(c.pos[1] for c in sh.cast) / len(sh.cast)
        else:
            fx, fy = 0.5, 0.45
        if P.get('handheld'):  # slow uneven wander, like a camera held by hand
            fx += 0.006 * (math.sin(t * 1.3) + 0.6 * math.sin(t * 2.9 + 1))
            fy += 0.005 * (math.sin(t * 1.7 + 2) + 0.5 * math.sin(t * 3.7))
            z = max(z, 1.04)
        return z, fx, fy, dx, dy, e

    @staticmethod
    def _window(z, fx, fy, dx, dy, e):
        """The visible part of a picture, in 0..1: (x0, y0, w, h)."""
        cw, ch = 1 / z, 1 / z
        x0 = min(max(fx - cw / 2 + dx * (1 - cw) * (e - 0.5), 0), 1 - cw)
        y0 = min(max(fy - ch / 2 + dy * (1 - ch) * (e - 0.5), 0), 1 - ch)
        return x0, y0, cw, ch

    def _post(self, img, sh, t):
        W, H = self.W, self.H
        P = sh.params
        tl = t - sh.t0
        if 'dutch' in P:  # a tilted horizon for unease; zoomed a little so the corners stay filled
            a = float(P['dutch'])
            r = math.radians(abs(a))
            k = max(math.cos(r) + (H / W) * math.sin(r), math.cos(r) + (W / H) * math.sin(r)) * 1.01  # covers the corners
            img = img.rotate(a, Image.BICUBIC, expand=False).resize((int(W * k), int(H * k)), Image.BICUBIC)
            img = img.crop(((img.width - W) // 2, (img.height - H) // 2, (img.width - W) // 2 + W, (img.height - H) // 2 + H))
        if 'whip' in P and 0 <= tl < 0.35:  # the shot slides in fast from one side with motion blur
            k = 1 - tl / 0.35
            off = int((1 if str(P['whip']) == 'left' else -1) * W * 0.6 * k * k)
            bl = img.filter(ImageFilter.BoxBlur(int(30 * k * W / 1920) + 1))
            moved = bl.transform((W, H), Image.AFFINE, (1, 0, off, 0, 1, 0), Image.BICUBIC, fillcolor=None)
            back = bl.transform((W, H), Image.AFFINE, (1, 0, off - (W if off > 0 else -W), 0, 1, 0), Image.BICUBIC)
            img = Image.composite(moved, back, moved.convert('L').point(lambda v: 255 if v > 0 else 0))
        if 'shake' in P:
            a = float(P['shake']) * W
            img = img.transform((W, H), Image.AFFINE, (1, 0, a * math.sin(t * 37), 0, 1, a * math.cos(t * 29)), Image.BICUBIC)
        return img

    def _set_frame(self, sh, t, i):
        name = sh.words[0]
        base, parts = self.sets[name]
        img = base
        m = self.mouth[name][min(i, self.n - 1)]
        if m:
            k = 'mid' if (m == 1 and 'mid' in parts) else 'open'
            if k in parts:
                img = Image.composite(parts[k][0], img, parts[k][1])
        tl = t - sh.t0
        if 'blink' in parts and not m and ((tl + 1.1) % 3.7) < 0.13:
            img = Image.composite(parts['blink'][0], img, parts['blink'][1])
        z, fx, fy, dx, dy, e = self._camera(sh, t)
        x0, y0, cw, ch = self._window(z, fx, fy, dx, dy, e)
        W, H = self.W, self.H
        return img.resize((W, H), Image.BICUBIC, box=(x0 * W, y0 * H, (x0 + cw) * W, (y0 + ch) * H))

    def _char_state(self, c, t, i):
        who = c.words[0]
        i = min(i, self.n - 1)
        v = self.vis[who][i]
        mood = self.mood[who][i] or str(c.params.get('mood', 'neutral'))
        talking = self.vis[who][max(0, i - 3):i + 4].count(None) < 7
        phase = (sum(map(ord, who)) % 37) / 10
        blink = (not talking) and ((t + phase) % 3.7) < 0.13
        return mood, ((v or 'closed') if talking else None), blink

    def _plate_frame(self, sh, t, i):
        W, H = self.W, self.H
        z, fx, fy, dx, dy, e = self._camera(sh, t)
        sx0, sy0, scw, sch = self._window(z * OVERSCAN, fx, fy, dx, dy, e)   # the subject plane
        scx, scy = sx0 + scw / 2, sy0 + sch / 2
        out = None
        layers = self.plates[sh.plate]
        for li, (lname, par, im) in enumerate(layers):
            k = par / SUBJECT_PARALLAX
            zl = OVERSCAN * (1 + (z - 1) * k)
            cx, cy = 0.5 + (scx - 0.5) * k, 0.5 + (scy - 0.5) * k
            cw, ch = 1 / zl, 1 / zl
            x0 = min(max(cx - cw / 2, 0), 1 - cw)
            y0 = min(max(cy - ch / 2, 0), 1 - ch)
            fr = im.resize((W, H), Image.BILINEAR, box=(x0 * im.width, y0 * im.height, (x0 + cw) * im.width, (y0 + ch) * im.height))
            if out is None:
                out = fr
            else:
                out.alpha_composite(fr)
            if lname == 'near' or (li == len(layers) - 2 and not any(l[0] == 'near' for l in layers)):
                dof = float(sh.params.get('dof', 0.004 if self.look != 'none' and sh.cast else 0))
                if dof > 0:   # the miniature's shallow focus: what stands behind the puppets goes soft
                    out = out.resize((W // 2, H // 2), Image.BILINEAR).filter(ImageFilter.GaussianBlur(dof * W / 2)).resize((W, H), Image.BILINEAR)
                self._draw_cast(out, sh, t, i, sx0, sy0, scw, sch)
        return out.convert('RGB')

    def _draw_cast(self, out, sh, t, i, x0, y0, cw, ch):
        W, H = self.W, self.H
        for c in sorted(sh.cast, key=lambda c: c.pos[1]):
            who = c.words[0]
            if getattr(c, 'body', False):
                self._draw_body(out, c, t, i, x0, y0, cw, ch)
                continue
            pup = self.puppets[who]
            state = self._char_state(c, t, i)
            size = float(c.params.get('size', 0.62))
            hpx = max(8, int(round(size * H / ch / 2)) * 2)
            facing = str(c.params.get('facing', 'front'))
            key = (who, state, hpx, facing)
            spr = self._sprite.get(key)
            if spr is None:
                src = pup.frame(*state)
                spr = src.resize((max(1, int(src.width * hpx / src.height)), hpx), Image.LANCZOS)
                if self.look != 'none':
                    spr = _volume(spr)
                if facing == 'left':
                    spr = spr.transpose(Image.FLIP_LEFT_RIGHT)
                if len(self._sprite) > 400:
                    self._sprite.clear()
                self._sprite[key] = spr
            hx, hy = c.pos
            hf = _head_frac(who)
            px = (hx - x0) / cw * W - spr.width / 2
            py = (hy - y0) / ch * H - hf * spr.height
            if self.look != 'none':
                _shadow(out, spr, px, py)
            out.alpha_composite(spr, (int(round(px)), int(round(py)))) if px >= 0 and py >= 0 and px + spr.width <= W and py + spr.height <= H \
                else _paste_clipped(out, spr, int(round(px)), int(round(py)))

    def _draw_body(self, out, c, t, i, x0, y0, cw, ch):
        """A full-body puppet: idle between acts, the act's move inside its range; to=x walks it there."""
        W, H = self.W, self.H
        who = c.words[0]
        bp = self.puppets['body:' + who]
        x, y = c.pos
        facing = str(c.params.get('facing', 'right'))
        move, mt, walked = 'idle', t, None
        for a in self.prog.get('acts', {}).get(who, []):
            tx = a.params.get('to')
            if t >= a.t1:
                if tx is not None:
                    facing = 'right' if tx > x else 'left' if tx < x else facing
                    x = tx
                continue
            if t >= a.t0:
                move, mt = a.words[1], t - a.t0
                if tx is not None:
                    facing = 'right' if tx > x else 'left' if tx < x else facing
                    walked = x
                    x = x + (tx - x) * (t - a.t0) / max(1e-6, a.t1 - a.t0)
            break
        mood, mouth, blink = self._char_state(c, t, i)
        hpx = float(c.params.get('size', 0.7)) * H / ch
        if move in ('walk', 'run') and walked is not None:
            mt = bp.gait_time(move, abs(x - walked) / cw * W, hpx)
        held = [L for L in self.prog.get('held', []) if L.holder == who and L.t0 <= t < L.t1]
        spr, ox, oy, hands = bp.sprite(move, mt, mood, mouth or 'closed', blink, hpx, facing == 'left',
                                       hold=tuple(dict.fromkeys(L.side for L in held)))
        px = (x - x0) / cw * W - ox
        py = (y - y0) / ch * H - oy
        if self.look != 'none':
            spr = _volume(spr)
            _shadow(out, spr, px, py, feet=(px + ox, py + oy, hpx * 0.28))
        _paste_clipped(out, spr, int(round(px)), int(round(py)))
        for L in held:   # the prop sits in the palm, over the puppet
            im = _held_prop(L.words[0], float(L.params.get('size', 0.12)) * H / ch, facing == 'left')
            hx, hy = hands[L.side]
            _paste_clipped(out, im, int(round(px + hx - im.width / 2)), int(round(py + hy - im.height * 0.55)))

    def shot_frame(self, sh, t, i):
        if sh.src == 'set':
            img = self._set_frame(sh, t, i)
        else:
            img = self._plate_frame(sh, t, i)
            if self.look != 'none':
                z, fx, fy, dx, dy, e = self._camera(sh, t)
                x0, y0, cw, ch = self._window(z * OVERSCAN, fx, fy, dx, dy, e)
                acts = self.prog.get('acts', {})
                centers = [(((body_x(c, acts, t) if getattr(c, 'body', False) else c.pos[0]) - x0) / cw,
                            (c.pos[1] - (0.3 if getattr(c, 'body', False) else 0) - y0) / ch) for c in sh.cast]
                img = _grade(_stage_light(img, sh.plate, centers), self.look)
        return self._post(img, sh, t)

    def _effect(self, L, t):
        e = lib.effects()[L.words[0]]
        k = int((t - L.t0) * e.get('fps', 24))
        nfr = len(e['files'])
        if nfr == 0:
            return None
        if e.get('loop', True) or L.params.get('loop'):
            k %= nfr
        elif k >= nfr:
            return None
        key = (L.words[0], k)
        im = self.fx_cache.get(key)
        if im is None:
            im = Image.open(e['files'][k]).convert('RGBA').resize((self.W, self.H), Image.BILINEAR)
            if len(self.fx_cache) > 300:
                self.fx_cache.clear()
            self.fx_cache[key] = im
        return im, e

    def frame(self, i):
        t = i / self.fps
        prog, W, H = self.prog, self.W, self.H
        shots = prog['shots']
        sh = next((s for s in shots if s.t0 <= t < s.t1), shots[-1])
        img = None
        for c in prog['cuts']:
            if c.at - c.dur / 2 <= t < c.at + c.dur / 2:
                a = next(s for s in shots if abs(s.t1 - c.at) < 1e-6)
                b = next(s for s in shots if abs(s.t0 - c.at) < 1e-6)
                fn = getattr(lib.motion(), TRANSITIONS[c.words[0]])
                p = {}
                if 'dir' in c.params:
                    p['direction'] = str(c.params['dir']) if c.words[0] == 'wipe' else (1 if c.params['dir'] == 'right' else -1)
                img = fn(self.shot_frame(a, t, i), self.shot_frame(b, t, i), (t - (c.at - c.dur / 2)) / c.dur, p).convert('RGB')
                break
        if img is None:
            img = self.shot_frame(sh, t, i)
        if prog['fx']:
            img = img.convert('RGBA')
            for L in prog['fx']:
                if L.t0 <= t < L.t1:
                    r = self._effect(L, t)
                    if r is None:
                        continue
                    im, e = r
                    op = float(L.params.get('opacity', 1))
                    if op < 1:
                        im = im.copy()
                        im.putalpha(im.getchannel('A').point(lambda v: int(v * op)))
                    if L.pos and e.get('params', {}).get('at'):
                        ax, ay = e['params']['at']
                        _paste_clipped(img, im, int((L.pos[0] - ax) * W), int((L.pos[1] - ay) * H))
                    else:
                        img.alpha_composite(im)
            img = img.convert('RGB')
        img = self._overlays(img, t)
        dark = 0.0
        for L in prog['fades']:
            if L.t0 <= t <= L.t1:
                f = (t - L.t0) / max(1e-6, L.t1 - L.t0)
                dark = max(dark, 1 - f if L.words[0] == 'in' else f)
            elif L.words[0] == 'out' and t > L.t1:
                dark = 1.0
        if dark > 0:
            img = Image.fromarray((np.asarray(img, np.float32) * (1 - dark)).astype(np.uint8))
        return img

    def _overlays(self, img, t):
        from PIL import ImageDraw, ImageFont
        W, H = self.W, self.H
        for L in self.prog['texts']:
            if not (L.t0 <= t < L.t1):
                continue
            if L.kind == 'prop':
                key = (L.words[0], float(L.params.get('size', 0.15)), H)
                if key not in _PROP_CACHE:
                    im = Image.open(props_list()[L.words[0]]).convert('RGBA')
                    hgt = max(2, int(key[1] * H))
                    im = im.crop(im.getbbox() or (0, 0, im.width, im.height))
                    im = im.resize((max(1, int(im.width * hgt / im.height)), hgt), Image.LANCZOS)
                    if L.params.get('flip'):
                        im = im.transpose(Image.FLIP_LEFT_RIGHT)
                    shd = Image.new('RGBA', im.size, (0, 0, 0, 0))
                    shd.putalpha(im.getchannel('A').point(lambda v: int(v * 0.35)).filter(ImageFilter.GaussianBlur(hgt * 0.03)))
                    _PROP_CACHE[key] = (im, shd)
                im, shd = _PROP_CACHE[key]
                x, y = L.pos or (0.5, 0.8)
                bob = float(L.params.get('bob', 0)) * H * math.sin(t * 3)  # bob=0.01 makes it float gently
                px, py = int(x * W - im.width / 2), int(y * H - im.height + bob)
                img = img.convert('RGBA')
                _paste_clipped(img, shd, px + int(im.height * 0.03), py + int(im.height * 0.04))
                _paste_clipped(img, im, px, py)
                img = img.convert('RGB')
                continue
            d = ImageDraw.Draw(img)
            px = max(6, int(float(L.params.get('size', 0.08)) * H * 1.25))
            fp = lib.fonts().get(str(L.params.get('font', ''))) or lib.default_font()
            fnt = ImageFont.truetype(fp, px) if fp else ImageFont.load_default()
            x, y = L.pos or (0.5, 0.2)
            bb = d.textbbox((0, 0), L.text, font=fnt)
            tx, ty = x * W - (bb[2] - bb[0]) / 2 - bb[0], y * H - (bb[3] - bb[1]) / 2 - bb[1]
            glow = Image.new('L', (W, H), 0)
            ImageDraw.Draw(glow).text((tx, ty + px * 0.04), L.text, font=fnt, fill=255)
            glow = glow.filter(ImageFilter.GaussianBlur(px * 0.12))
            halo = str(L.params.get('glow', '#000000'))  # a soft halo instead of a hard shadow: glow=#ffffff on dark text
            img = Image.composite(Image.new('RGB', (W, H), halo), img, glow.point(lambda v: int(v * float(L.params.get('halo', 0.55)))))
            d = ImageDraw.Draw(img)
            d.text((tx, ty), L.text, font=fnt, fill=str(L.params.get('color', '#ffffff')))
        return img

    # --- sound
    def audio(self, wav):
        from .audio import music_track
        prog = self.prog
        length = prog['length']
        buf = np.zeros((int(length * SR) + SR, 2), np.float32)
        for m in prog['music']:  # music plays over its own range: music mood=bright 35-43s (or from at= to the end)
            a = m.t0 if m.t0 is not None else (m.at or 0)
            b = m.t1 if m.t1 is not None else length
            if 'file' in m.params:
                nm = str(m.params['file'])
                sig = _decode_mono(lib.music_files().get(nm) or os.path.expanduser(nm))
                need = int((b - a) * SR)
                if len(sig) == 0:
                    continue
                if m.params.get('loop', 1) not in (0, 0.0, '0', 'no'):
                    sig = np.tile(sig, need // len(sig) + 1)
                tr = np.repeat(sig[:need, None], 2, axis=1) * float(m.params.get('gain', 0.5))
            else:
                tr = music_track([(0, m.params.get('mood', 'calm'), str(m.params.get('key', 'C')), float(m.params.get('tempo', 72)))], b - a)
                tr = tr[:int((b - a) * SR)] * float(m.params.get('gain', 0.6))
            f = min(len(tr), int(0.3 * SR))
            if f:
                tr[:f] *= np.linspace(0, 1, f)[:, None]
                tr[-f:] *= np.linspace(1, 0, f)[:, None]
            i = int(a * SR)
            buf[i:i + len(tr)] += tr[:len(buf) - i]
        for s in prog['sfx']:
            sig = _decode_mono(lib.sfx()[s.words[0]]) * float(s.params.get('gain', 0.8))
            i = int(s.at * SR)
            seg = sig[:max(0, len(buf) - i)]
            pan = float(s.params.get('pan', 0))
            buf[i:i + len(seg), 0] += seg * (1 - max(0, pan))
            buf[i:i + len(seg), 1] += seg * (1 + min(0, pan))
        vbuf = np.zeros_like(buf)
        for L, sig in self.voice_clips:
            sig = sig * float(L.params.get('gain', 1.0)) * 1.4
            i = int(L.at * SR)
            seg = sig[:max(0, len(vbuf) - i)]
            vbuf[i:i + len(seg)] += seg[:, None]
        if self.voice_clips:
            env = np.abs(vbuf).max(axis=1)
            k = int(0.25 * SR)
            env = np.convolve((env > 0.02).astype(np.float32), np.ones(k, np.float32) / k, mode='same')
            buf = buf * (1 - 0.7 * np.clip(env * 2, 0, 1))[:, None] + vbuf
        buf = np.tanh(buf[:int(length * SR)] * 1.1) * 0.9
        from scipy.io import wavfile
        wavfile.write(wav, SR, (buf * 32767).astype(np.int16))


def _held_prop(name, hpx, flip):
    key = ('held', name, int(hpx), flip)
    if key not in _PROP_CACHE:
        im = Image.open(props_list()[name]).convert('RGBA')
        im = im.crop(im.getbbox() or (0, 0, im.width, im.height))
        h = max(2, int(hpx))
        im = im.resize((max(1, int(im.width * h / im.height)), h), Image.LANCZOS)
        if flip:
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
        if len(_PROP_CACHE) > 200:
            _PROP_CACHE.clear()
        _PROP_CACHE[key] = im
    return _PROP_CACHE[key]


def _volume(spr, light=1.0):
    """Light a flat felt sprite like a miniature: darker towards its own edges (rounded form), a key light from
    the upper left. Keeps alpha."""
    a = np.asarray(spr.getchannel('A'), np.float32) / 255
    if a.max() == 0:
        return spr
    r = max(2, int(min(spr.size) * 0.05))
    b = np.asarray(spr.getchannel('A').filter(ImageFilter.GaussianBlur(r)), np.float32) / 255
    h, w = a.shape
    xs = np.linspace(0, 1, w, dtype=np.float32)[None, :]
    ys = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    f = (0.58 + 0.42 * np.clip(b * 1.25, 0, 1)) * (1.10 - 0.18 * xs) * (1.06 - 0.10 * ys)
    f = 1 + (f - 1) * light
    rgb = np.asarray(spr.convert('RGB'), np.float32) * f[..., None]
    out = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), 'RGB')
    out.putalpha(spr.getchannel('A'))
    return out


def _shadow(out, spr, px, py, feet=None):
    """A soft shadow behind a sprite (offset down-right) and, for full bodies, a contact shadow under the feet.
    Drawn on a small canvas around the sprite, blurred at half size: full-frame blurs cost seconds per film second."""
    off = max(2, int(spr.height * 0.025))
    pad = max(8, int(spr.height * 0.06))
    fw = feet[2] if feet else 0
    cw, ch = spr.width + 2 * pad + int(fw), spr.height + 2 * pad + off
    k = 2
    sh = Image.new('L', (cw // k + 1, ch // k + 1), 0)
    a = spr.getchannel('A').point(lambda v: v * 0.30).resize((max(1, spr.width // k), max(1, spr.height // k)))
    sh.paste(a, ((pad + off) // k, (pad + off // 2) // k), a)
    if feet is not None:
        from PIL import ImageDraw
        fx, fy = feet[0] - px + pad, feet[1] - py + pad
        ew, eh = fw * 1.3, max(4, fw * 0.22)
        ImageDraw.Draw(sh).ellipse(((fx - ew / 2) / k, (fy - eh / 2) / k, (fx + ew / 2) / k, (fy + eh / 2) / k), fill=150)
    sh = sh.filter(ImageFilter.GaussianBlur(max(1, spr.height * 0.012))).resize((cw, ch), Image.BILINEAR)
    lay = Image.new('RGBA', (cw, ch), (25, 15, 8, 255))
    lay.putalpha(sh)
    _paste_clipped(out, lay, int(px) - pad, int(py) - pad)


_VIG = {}


def _vignette(W, H):
    """Darker corners, as an RGB image for ImageChops.multiply."""
    if (W, H) not in _VIG:
        ys, xs = np.ogrid[0:H, 0:W]
        d = ((xs / W - 0.5) ** 2 * 1.2 + (ys / H - 0.5) ** 2 * 1.6)
        v = ((1 - 0.55 * np.clip(d, 0, 1) ** 1.2) * 255).astype(np.uint8)
        _VIG[(W, H)] = Image.fromarray(v, 'L').convert('RGB')
    return _VIG[(W, H)]


def _lut(gain):
    return [int(max(0, min(255, (0.5 + (v / 255 * gain - 0.5) * 1.06) * 255))) for v in range(256)]


_WARM = _lut(1.05) + _lut(1.0) + _lut(0.90)
_HI = [int(max(0, min(255, (v / 255 - 0.72) * 2.5 * 255))) for v in range(256)] * 3


_AMBIENT = {'night': 0.48, 'dusk': 0.62, 'dawn': 0.72, 'golden': 0.78}


def _stage_light(img, plate, centers):
    """Practical light: the room sinks to an ambient level set by the plate's time of day, and a warm pool of light
    sits on the puppets, the way a miniature set is lit by a few lamps."""
    W, H = img.size
    amb = next((v for k, v in _AMBIENT.items() if k in plate), 0.86)
    w, h = W // 8, H // 8
    ys, xs = np.ogrid[0:h, 0:w]
    m = np.full((h, w), amb, np.float32)
    for cx, cy in centers or [(0.5, 0.55)]:
        d = ((xs / w - cx) / 0.30) ** 2 + ((ys / h - cy) / 0.45) ** 2
        m = np.maximum(m, amb + (1 - amb) * np.exp(-d))
    tint = np.stack([m, m * (0.96 + 0.04 * m), m * (0.86 + 0.14 * m)], -1)   # the shadows go cool, the pool warm
    L = Image.fromarray((tint * 255).astype(np.uint8), 'RGB').resize((W, H), Image.BILINEAR)
    from PIL import ImageChops
    return ImageChops.multiply(img.convert('RGB'), L)


def _grade(img, look):
    """The miniature look over a finished frame: warm light, a little contrast, a soft glow on highlights, a vignette.
    Lookup tables and half-size blurs, so it adds little to the render time."""
    if look in ('none', 'off', '0'):
        return img
    from PIL import ImageChops
    W, H = img.size
    img = img.convert('RGB').point(_WARM)
    hi = img.resize((W // 4, H // 4), Image.BILINEAR).point(_HI).filter(ImageFilter.GaussianBlur(W * 0.003))
    glow = hi.resize((W, H), Image.BILINEAR).point(lambda v: v * 0.2)
    img = ImageChops.add(img, glow)
    return ImageChops.multiply(img, _vignette(W, H))


def _paste_clipped(dst, im, x, y):
    """alpha_composite that tolerates a picture partly outside the frame."""
    W, H = dst.size
    l, t = max(0, x), max(0, y)
    r, b = min(W, x + im.width), min(H, y + im.height)
    if r <= l or b <= t:
        return
    dst.alpha_composite(im.crop((l - x, t - y, r - x, b - y)), (l, t))


def render_puppet(prog, out, preview=False, no_audio=False, size=None, frames=None):
    """Render the film to out (mp4). frames: a list of seconds -> PNG stills next to out instead."""
    R = Renderer(prog, size=size, preview=preview, no_audio=no_audio)
    if frames:
        os.makedirs(out, exist_ok=True)
        paths = []
        for t in frames:
            p = os.path.join(out, f'{t:06.2f}.png')
            R.frame(min(R.n - 1, int(round(t * R.fps)))).save(p)
            paths.append(p)
        return paths
    wav = out + '.wav'
    R.audio(wav)
    proc = subprocess.Popen([ffmpeg(), '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{R.W}x{R.H}', '-r', str(R.fps), '-i', '-',
                             '-i', wav, '-map', '0:v', '-map', '1:a', '-c:a', 'aac', '-b:a', '160k', '-t', str(prog['length']),
                             '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', '-preset', 'medium', out], stdin=subprocess.PIPE)
    try:
        for i in range(R.n):
            proc.stdin.write(R.frame(i).tobytes())
    finally:
        proc.stdin.close()
        proc.wait()
        os.remove(wav)
    if proc.returncode:
        raise RuntimeError(f'ffmpeg failed with code {proc.returncode}')
    return out


def render_shot(base_p, open_p, blink_p, voice, out, seconds, fps=24, size=(1920, 1080), push=0.06, at=0.3):
    base = _load(base_p, size)
    parts = []
    for p in (open_p, blink_p):
        v = _load(p, size) if p else None
        parts.append((v, diff_mask(base, v) if v else None))
    n = int(seconds * fps)
    lead = int(at * fps)
    mouth = [0] * lead + mouth_track(voice, fps, n - lead) if voice else [0] * n
    proc = subprocess.Popen([ffmpeg(), '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{size[0]}x{size[1]}', '-r', str(fps), '-i', '-']
                            + (['-itsoffset', str(at), '-i', voice, '-map', '0:v', '-map', '1:a', '-c:a', 'aac'] if voice else [])
                            + ['-t', str(seconds), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', out], stdin=subprocess.PIPE)
    W, H = size
    for i in range(n):
        t = i / fps
        img = base
        if mouth[i] and parts[0][0] is not None:
            img = Image.composite(parts[0][0], img, parts[0][1])
        if parts[1][0] is not None and (t % 3.7) < 0.13:
            img = Image.composite(parts[1][0], img, parts[1][1])
        z = 1 + push * (0.5 - 0.5 * math.cos(math.pi * min(1, t / seconds)))
        cw, ch = W / z, H / z
        x0, y0 = (W - cw) * 0.55, (H - ch) * 0.45
        img = img.resize(size, Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))
        proc.stdin.write(img.tobytes())
    proc.stdin.close()
    proc.wait()
