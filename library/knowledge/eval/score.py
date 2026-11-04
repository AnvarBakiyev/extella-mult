#!/usr/bin/env python3
"""Score PUPPET programs against the rubric (eval/rubric.md). Everything here is automatic.

  python3 eval/score.py outputs/R07.scene --request R07     # one program for one request
  python3 eval/score.py --dir outputs                        # outputs/R01.scene ... R30.scene
  python3 eval/score.py --fewshot                            # self-test on fewshot/ (format from the header)
  add --json report.json for a machine-readable report, -v for every finding

Five criteria, 0-2 points each, 10 total: format fit, timing, last line, safety, camera variety.
A program the handler's parser rejects gets 0 for timing and is marked INVALID (the rest is still scored
from a lenient parse so the agent can see what else is wrong).
"""
import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

EVAL = Path(__file__).resolve().parent
PACK = EVAL.parent
sys.path.insert(0, str(PACK / 'tools'))
import puppet_check  # noqa: E402

# the writers room's own banned list: countries, cities, politics, religion, brands
_spec = importlib.util.spec_from_file_location('wr_check', PACK.parent / 'puppet-writers-room' / 'tools' / 'check.py')
_wr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_wr)
BANNED_RE = _wr.BANNED_RE
EXTRA_BANNED = re.compile(r'\b(?:выбор(?:ах|ам|ами)\b|кока|спрайт|фант[аы]\b|кол[уаы]\b|пепси|путин|трамп|байден|навальн|зеленск|лукашенк|токаев|илон\b|маск\b)', re.I)

# what a format looks like in a program: typical sets (any one) and a signature check
FORMAT_SETS = {
    'F01': {'ch_dina', 'pl_tv_studio'}, 'F02': {'ch_arsen', 'pl_talkshow'}, 'F03': {'ch_timur', 'pl_newsroom'},
    'F04': set(), 'F05': {'ad_cream'}, 'F06': {'ch_alina', 'pl_hr_room'}, 'F07': {'ch_mark', 'pl_therapy'},
    'F08': {'ch_svetlana', 'pl_court', 'ch_igor'}, 'F09': {'ch_madina', 'pl_cooking_set'}, 'F10': {'ch_kirill', 'pl_weather_studio'},
    'F11': {'ch_inna', 'pl_game_show'}, 'F12': {'ch_pavel', 'pl_press_room'}, 'F13': {'ch_aidana'},
    'F14': {'ch_liza', 'pl_unboxing_desk'}, 'F15': {'ch_nurlan', 'pl_podcast'}, 'F16': set(),
    'F17': {'ch_sveta', 'pl_support_desk'}, 'F18': {'ch_danya', 'ch_viktor', 'pl_pitch_stage'}, 'F19': {'pl_dining'},
    'F20': {'ch_natalya', 'pl_school'}, 'F21': {'ch_olga', 'pl_clinic'}, 'F22': {'ch_rustam', 'pl_taxi'},
    'F23': {'ch_lev', 'pl_museum'}, 'F24': {'ch_karina', 'pl_apartment_empty', 'pl_new_building'},
    'F25': {'pl_wedding_hall', 'ch_zhanna', 'ch_artyom', 'ch_kamila'},
}
WORD = re.compile(r'[\wё]+(?:-[\wё]+)?', re.I)


def words(t):
    return len(WORD.findall(re.sub(r'\[[^\]]*\]', '', t or '')))


def est(t):
    return words(t) / 2 + 0.5 * (t or '').count('[pause]')


# ---------------------------------------------------------------- lenient parse (works on broken programs too)
class S:
    def __init__(self, **k):
        self.__dict__.update(k)


def lenient(src):
    shots, lines, music, texts, fades, header = [], [], [], [], [], {}
    for n, raw in enumerate(src.splitlines(), 1):
        s = raw.strip()
        m = re.match(r'#\s*(format|logline|why it works)\s*:\s*(.*)', s, re.I)
        if m:
            header[m.group(1).lower()] = m.group(2)
            continue
        if not s or s.startswith('#'):
            continue
        rng = re.search(r'(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)s', s)
        at = re.search(r'\bat (\d+(?:\.\d+)?)s', s)
        q = re.search(r'"([^"]*)"', s)
        params = dict(re.findall(r'(\w+)=("[^"]*"|\S+)', s))
        if s.startswith('film'):
            header['title'] = q.group(1) if q else ''
        elif s.startswith('shot') and rng:
            m = re.match(r'shot\s+\S+\s*:?\s*(\S+)', s)
            shots.append(S(n=n, t0=float(rng.group(1)), t1=float(rng.group(2)), set=m.group(1) if m else '', P=params))
        elif s.startswith(('say', 'voice')):
            kind = s.split()[0]
            who_set = s.split()[1] if kind == 'say' and len(s.split()) > 1 else None
            lines.append(S(n=n, kind=kind, set=who_set, text=q.group(1) if q else '', at=float(at.group(1)) if at else None, P=params))
        elif s.startswith('music'):
            music.append(S(n=n, t0=float(rng.group(1)) if rng else 0, t1=float(rng.group(2)) if rng else 1e9, P=params))
        elif s.startswith(('text', 'prop')):
            texts.append(S(n=n, text=q.group(1) if q else '', P=params))
        elif s.startswith('fade'):
            fades.append(S(n=n, kind=s.split()[1] if len(s.split()) > 1 else ''))
    shots.sort(key=lambda x: x.t0)
    lines = [L for L in lines if L.at is not None]
    lines.sort(key=lambda x: x.at)
    return dict(shots=shots, lines=lines, music=music, texts=texts, fades=fades, header=header,
                length=shots[-1].t1 if shots else 0)


def shot_at(p, t):
    return next((s for s in p['shots'] if s.t0 <= t < s.t1), None)


def fnum(v, d=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def moves(s):
    """The camera moves one shot uses."""
    P, out = s.P, set()
    push = fnum(P.get('push'), 0.04 if 'pull' not in P else 0)
    if 'pull' in P:
        out.add('pull')
    elif push >= 0.08:
        out.add('push')
    elif push <= 0.03:
        out.add('still')
    else:
        out.add('slow')
    for k in ('snap', 'handheld', 'dutch', 'whip', 'shake'):
        if k in P:
            out.add(k)
    if P.get('pan', 'none') != 'none':
        out.add('pan')
    return frozenset(out)


# ---------------------------------------------------------------- criteria
def detect_format(p):
    m = re.match(r'(F\d\d)', p['header'].get('format', '').strip())
    if m:
        return m.group(1)
    used = {s.set for s in p['shots']} | {L.set for L in p['lines'] if L.set}
    best = max(FORMAT_SETS, key=lambda f: len(FORMAT_SETS[f] & used))
    return best if FORMAT_SETS[best] & used else None


def signature(fid, p):
    """Format-specific evidence, True when the program looks like that format."""
    lines, shots = p['lines'], p['shots']
    used = {s.set for s in shots}
    allm = [m for s in shots for m in moves(s)]
    deep = [L for L in lines if L.kind == 'voice' and (L.P.get('who') in (None, 'deep', 'narrator')) and not L.text.startswith('[ad]')]
    if fid == 'F04':
        return len(deep) >= max(2, 0.4 * len(lines))
    if fid == 'F05':
        return 'ad_cream' in used or any(L.text.startswith('[ad]') or L.P.get('who') == 'ad' for L in lines)
    if fid == 'F13':
        return any('[whispering]' in L.text for L in lines)
    if fid == 'F22':
        return allm.count('handheld') >= len(shots) / 2
    if fid in ('F02', 'F11', 'F19'):
        return 'whip' in allm or bool(FORMAT_SETS[fid] & used)
    if fid == 'F03':
        return 'handheld' in allm
    if fid == 'F16':
        return any(re.search(r'шаг', L.text, re.I) for L in lines)
    return bool(FORMAT_SETS[fid] & used)


def c_format(p, req):
    notes = []
    fid = detect_format(p)
    ok_dur = 30 <= p['length'] <= 65
    if not ok_dur:
        notes.append(f"length {p['length']:g}s outside 30-65s")
    if len(p['shots']) < 5:
        notes.append(f"only {len(p['shots'])} shots; a format has at least 5 beats")
    want = (req or {}).get('formats') or []
    if want and fid not in want:
        notes.append(f"format {fid} but the request fits {'/'.join(want)}")
        return 0, notes
    if not fid:
        notes.append('format not declared (# format: Fxx) and not recognisable')
        return 0, notes
    sig = signature(fid, p)
    if not sig:
        notes.append(f'{fid} signature missing (typical sets/voice/camera of the format)')
    for s in (req or {}).get('must_sets', []):
        if s not in {x.set for x in p['shots']} | {L.set for L in p['lines'] if L.set}:
            notes.append(f'requested character {s} not on screen')
            sig = False
    if (req or {}).get('kind') == 'break' and not re.search(r'реклам', ' '.join(L.text for L in p['lines']), re.I):
        notes.append('request asks for a commercial break; no "реклама" line')
        sig = False
    score = 2 if (sig and ok_dur and len(p['shots']) >= 5) else 1
    return score, notes


def c_timing(p, valid):
    notes = []
    if not valid:
        notes.append('handler check failed')
    lines = p['lines']
    for i, L in enumerate(lines):
        s = shot_at(p, L.at)
        d = est(L.text)
        if s is None:
            notes.append(f'line {L.n}: at {L.at:g}s is outside every shot')
            continue
        if L.at < s.t0 + 0.2:
            notes.append(f'line {L.n}: starts {L.at - s.t0:.1f}s into its shot; start 0.3s after the cut')
        if L.kind == 'say' and L.at + d > s.t1 + 0.25:
            notes.append(f'line {L.n}: {words(L.text)} words need {d:.1f}s, so it ends at {L.at + d:.1f}s but its shot ends at {s.t1:g}s')
        if i + 1 < len(lines) and L.at + d > lines[i + 1].at + 0.1:
            notes.append(f'line {L.n}: overlaps line {lines[i + 1].n}')
        if L.kind == 'say' and words(L.text) / max(0.1, s.t1 - s.t0) > 2.0:
            notes.append(f'line {L.n}: {words(L.text) / (s.t1 - s.t0):.1f} words/s in its shot; keep 2 or less')
    for a, b in zip(p['shots'], p['shots'][1:]):
        if abs(a.t1 - b.t0) > 1e-6:
            notes.append(f'line {b.n}: shot does not touch the previous one')
    if not any(f.kind == 'in' for f in p['fades']) or not any(f.kind == 'out' for f in p['fades']):
        notes.append('missing fade in or fade out')
    if not valid:
        return 0, notes
    return (2 if not notes else 1 if len(notes) <= 2 else 0), notes


EXPLAIN = re.compile(r'потому что|то есть|мораль|вот почему|понимаете|в общем|иными словами', re.I)


def c_last(p):
    notes = []
    if not p['lines']:
        return 0, ['no spoken lines']
    L = p['lines'][-1]
    end = L.at + est(L.text)
    core = 0
    if words(L.text) > 10:
        notes.append(f'last line has {words(L.text)} words; keep 2-8, never over 10')
    else:
        core += 1
        if words(L.text) > 8:
            notes.append(f'last line has {words(L.text)} words; 2-8 is better')
    if p['length'] - L.at > 7:
        notes.append(f"last line starts {p['length'] - L.at:.1f}s before the end; put it in the last 3-6s")
    else:
        core += 1
    ad_turn = L.kind == 'voice' and (L.text.startswith('[ad]') or L.P.get('who') == 'ad')  # F05: the jingle carries the slogan
    if not ad_turn and any(m.t0 < end and m.t1 > L.at + 0.3 for m in p['music']):
        notes.append('music plays under the last line; stop it 3-6s earlier')
    else:
        core += 1
    if EXPLAIN.search(L.text):
        notes.append('last line explains the joke')
        core -= 1
    s = shot_at(p, L.at)
    others = [x for x in p['lines'][:-1] if s and s.t0 <= x.at < s.t1]
    if others:
        notes.append('last line shares its shot with another line; give it its own shot')
    prev = [x for x in p['shots'] if s and x.t1 <= s.t0]
    silent_before = bool(prev) and not any(prev[-1].t0 <= x.at < prev[-1].t1 for x in p['lines'])
    if not (s and 'snap' in s.P) and not silent_before:
        notes.append('no snap on the last line and no silent beat before it')
    return (2 if core >= 3 and not others else 1 if core >= 2 else 0), notes


def c_safety(p, src):
    notes = []
    text = ' '.join([p['header'].get('title', '')] + [L.text for L in p['lines']] + [t.text for t in p['texts']])
    for m in list(BANNED_RE.finditer(text)) + list(EXTRA_BANNED.finditer(text)):
        notes.append(f'banned word: «{m.group(0)}»')
    for L in p['lines']:
        if L.P.get('who') in ('gogi', 'odessa'):
            notes.append(f'line {L.n}: accent voice who={L.P["who"]} chosen by hand; avoid accent voices for characters')
    return (0 if any(n.startswith('banned') for n in notes) else 1 if notes else 2), notes


def c_camera(p):
    notes = []
    sig = [moves(s) for s in p['shots']]
    distinct = set().union(*sig) if sig else set()
    distinct.discard('slow')
    n_snap = sum('snap' in s for s in sig)
    score = 2 if len(distinct) >= 4 else 1 if len(distinct) == 3 else 0
    if len(distinct) < 4:
        notes.append(f"only {len(distinct)} kinds of camera move ({', '.join(sorted(distinct)) or 'none'}); use 4+")
    doc_end = bool(p['shots']) and 'pull' in p['shots'][-1].P  # a documentary may end on a pull-out instead
    if (n_snap == 0 and not doc_end) or n_snap > 3:
        notes.append(f'{n_snap} snaps; use 1-3, on the turn')
        score = max(0, score - 1)
    run = best = 1
    for a, b in zip(sig, sig[1:]):
        run = run + 1 if a == b else 1
        best = max(best, run)
    if best >= 4:
        notes.append(f'{best} identical camera shots in a row')
        score = max(0, score - 1)
    return score, notes


# ---------------------------------------------------------------- driver
_PUPPET = None


def score(src, req=None):
    global _PUPPET
    if _PUPPET is None:
        _PUPPET = puppet_check.load(PACK / 'vendor', stub=True)
    valid, msg, _ = puppet_check.check_text(_PUPPET, src)
    p = lenient(src)
    res = dict(valid=valid, check=msg)
    for name, (pts, notes) in dict(format=c_format(p, req), timing=c_timing(p, valid), last_line=c_last(p),
                                   safety=c_safety(p, src), camera=c_camera(p)).items():
        res[name] = dict(points=pts, notes=notes)
    res['total'] = sum(res[k]['points'] for k in ('format', 'timing', 'last_line', 'safety', 'camera'))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('files', nargs='*')
    ap.add_argument('--request', help='request id for a single file (R01..R30)')
    ap.add_argument('--dir', help='folder with R01.scene ... R30.scene')
    ap.add_argument('--fewshot', action='store_true', help='score fewshot/*.scene (self-test)')
    ap.add_argument('--json')
    ap.add_argument('-v', action='store_true')
    a = ap.parse_args()
    reqs = {r['id']: r for r in map(json.loads, (EVAL / 'requests.jsonl').read_text().splitlines())}
    jobs = []
    if a.fewshot:
        jobs = [(f, None) for f in sorted((PACK / 'fewshot').glob('*.scene'))]
    elif a.dir:
        for rid in reqs:
            jobs.append((Path(a.dir) / f'{rid}.scene', reqs[rid]))
    else:
        jobs = [(Path(f), reqs.get(a.request or Path(f).stem)) for f in a.files]
    report, tot, n = {}, 0, 0
    print(f"{'id':6} {'valid':5} fmt tim last safe cam  total")
    for f, req in jobs:
        key = req['id'] if req else f.stem
        if not f.exists():
            print(f'{key:6} missing')
            report[key] = dict(missing=True, total=0)
            n += 1
            continue
        r = score(f.read_text(), req)
        report[key] = r
        tot += r['total']
        n += 1
        print(f"{key:6} {'yes' if r['valid'] else 'NO':5} {r['format']['points']:3} {r['timing']['points']:3} {r['last_line']['points']:4} "
              f"{r['safety']['points']:4} {r['camera']['points']:3}  {r['total']:2}/10")
        if a.v or not r['valid']:
            if not r['valid']:
                print('       check: ' + r['check'][:300])
            for k in ('format', 'timing', 'last_line', 'safety', 'camera'):
                for note in r[k]['notes'] if a.v else []:
                    print(f'       {k}: {note}')
    if n:
        print(f'mean {tot / n:.2f}/10 over {n}')
    if a.json:
        Path(a.json).write_text(json.dumps(report, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
