#!/usr/bin/env python3
"""Turn a writers-room script (episodes/E###.md) into a PUPPET program.

  python3 tools/convert.py E004 E038 ... --out fewshot --why why.json

Sets are the writers-room codes: a talking character is a set ch_<code>, a wide or empty shot is the place
set pl_<code>. Rules (the same the agent learns from the concepts):
- one row of the script = one shot; shots touch; a line starts 0.3 s after its shot begins;
- a line lasts words/2 s + 0.5 s per [pause]; if it does not fit, the shot grows (end = line end + 0.4 s)
  and everything after shifts; the words are never cut;
- the speaker on screen talks with `say`; someone off screen or the narrator talks with `voice`;
- camera words of the script map to shot parameters; music words map to mood ranges; silence stops music;
- fade in 0-0.6 s, fade out over the last 0.4 s.
"""
import argparse
import json
import re
from pathlib import Path

import stubs

ROOM = stubs.ROOM
NARR = ('диктор', 'голос', 'закадр', 'реклам')


def stem(w):
    w = w.lower().replace('ё', 'е')
    return w[:len(w) - 1] if len(w) <= 4 else w[:min(5, len(w) - 2)]


def names():
    """code -> stems of its names in cast.md ('Нина Аркадьевна, черепаха' -> нина, аркад, череп)."""
    out = {}
    for code, who in re.findall(r'^\|\s*(ch_\w+)\s*\|\s*([^|]+)\|', (ROOM / 'cast.md').read_text(), re.M):
        words = re.findall(r'[А-Яа-яЁёA-Za-z]+', who.split(',')[0])
        words += re.findall(r'[А-Яа-яЁёA-Za-z]{4,}', who.split(',')[1] if ',' in who else '')[:2]
        out[code] = [stem(w) for w in words if len(w) > 2]
    return out


def place_names():
    out = {}
    for code, what in re.findall(r'^\|\s*(pl_\w+)\s*\|\s*([^|]+)\|', (ROOM / 'places.md').read_text(), re.M):
        out[code] = [stem(w) for w in re.findall(r'[А-Яа-яЁё]{4,}', what)]
    return out


NAMES, PLACES = names(), place_names()


def find_char(text, cast, first_only=False):
    """The cast code whose name appears earliest in text."""
    t = text.lower().replace('ё', 'е')
    best = None
    for c in cast:
        for s in NAMES.get(c, []):
            m = re.search(r'(?<![а-яa-z])' + re.escape(s), t)
            if m and (best is None or m.start() < best[0]):
                best = (m.start(), c)
    return best[1] if best else None


def parse(eid):
    text = (ROOM / 'episodes' / f'{eid}.md').read_text()
    meta = dict(re.findall(r'^- \*\*([^:]+):\*\* (.+)$', text, re.M))
    title = re.match(r'# E\d+\. (.+)', text).group(1).strip()
    rows = []
    for line in text.splitlines():
        m = re.match(r'^\|\s*(\d+(?:[.,]\d+)?)\s*[–-]\s*(\d+(?:[.,]\d+)?)\s*\|(.*)\|\s*$', line)
        if m:
            cells = [c.strip() for c in m.group(3).split('|')]
            cells += [''] * (6 - len(cells))
            rows.append(dict(t0=float(m.group(1).replace(',', '.')), t1=float(m.group(2).replace(',', '.')),
                             frame=cells[0], who=cells[1], line=cells[2], cam=cells[3], sfx=cells[4], music=cells[5]))
    cast = meta.get('Персонажи', '').replace(',', ' ').split()
    places = meta.get('Места', '').replace(',', ' ').split()
    return dict(id=eid, title=title, meta=meta, rows=rows, cast=[c for c in cast if c != 'ch_narrator'], places=places)


def words(t):
    return len(re.findall(r'[\wё]+(?:-[\wё]+)?', re.sub(r'\[[^\]]*\]', '', t)))


def est(t):
    return words(t) / 2 + 0.5 * t.count('[pause]')


def clean(line):
    """Script cell -> spoken text: stage directions become delivery tags or go, inner quotes become «»."""
    line = line.strip()
    tags = []
    for d in re.findall(r'\(([^)]*)\)', line):
        dl = d.lower()
        if 'пауз' in dl:
            line = line.replace(f'({d})', '[pause]')
            continue
        if 'шёпот' in dl or 'шепот' in dl:
            tags.append('[whispering]')
        line = line.replace(f'({d})', '')
    line = re.sub(r'"([^"]*)"', r'«\1»', line).replace('"', '')
    line = line.replace('…', '... ')
    line = re.sub(r'\s*\.\.\.\s*', '... ', line)
    line = re.sub(r'\s+', ' ', line).strip()
    return ' '.join(tags + [line]) if line else ''


def camera(row, film_at, k, shot_len):
    c = row['cam'].lower()
    f = row['frame'].split(',')[0].upper()
    P = {}
    if 'снап' in c:
        P['push'] = 0.02
        P['snap'] = round(film_at, 2)
    if 'очень медленный наезд' in c:
        P['push'] = 0.03
    elif 'медленный наезд' in c or 'медленно' in c and 'наезд' in c:
        P['push'] = 0.05
    elif 'лёгкий наезд' in c or 'легкий наезд' in c:
        P['push'] = 0.04
    elif 'наезд на паузе' in c:
        P['push'] = 0.08
    elif 'наезд' in c:
        P['push'] = 0.1
    if 'отъезд' in c:
        P.pop('push', None)
        P['pull'] = 0.15 if ('плавн' in c or 'медлен' in c) else 0.25
    if 'ручн' in c or 'селфи' in c:
        P['handheld'] = 1
    if 'голланд' in c:
        P['dutch'] = 10 if k % 2 else -10
    if 'вип' in c:
        P['whip'] = 'left' if k % 2 else 'right'
    if 'панорам' in c or 'вращ' in c or 'проводк' in c:
        P['pan'] = 'left' if 'влево' in c else 'right'
    if 'подъ' in c:
        P['pan'] = 'up'
    if 'опуск' in c or 'опуска' in c:
        P['pan'] = 'down'
    if 'тряск' in c or 'ветер' in c or 'удар' in c:
        P['shake'] = 0.003
    if not P or set(P) <= {'handheld'}:
        P.setdefault('push', 0.02)  # 'статика' or nothing: an almost still camera, never fully dead
    if f.startswith('ДКР'):
        P['push'] = round(P.get('push', 0) + 0.08, 2) if 'pull' not in P else P.get('push')
        P['focus'] = '0.5,0.5'
    elif f.startswith('КР'):
        if 'pull' not in P:
            P['push'] = round(P.get('push', 0) + 0.04, 2)
        P['focus'] = '0.5,0.4'
    if P.get('push') is None:
        P.pop('push', None)
    return P


MUSIC = [  # first match wins; None stops the music
    (('тишин', 'обрыв', 'стихает', 'замолк', 'пауза'), None),
    (('джингл', 'заставк', 'бодр', 'фанфар', 'торжеств', 'весёл', 'весел', 'диско', 'поп'), 'bright'),
    (('струнн', 'эпич', 'величеств', 'гимн'), 'wonder'),
    (('тревож', 'напряж', 'бас', 'барабан', 'саспенс', 'тикан'), 'tense'),
    (('мрачн', 'тёмн', 'темн', 'нуар'), 'dark'),
    (('гитар', 'тёпл', 'тепл', 'уют', 'семейн', 'вальс', 'аккордеон'), 'cozy'),
    (('тих', 'пианино', 'эмбиент', 'фон', 'лаунж', 'ожидани', 'мелоди', 'музык', 'нежн', 'спокой', 'флейт'), 'calm'),
]


def mood_of(cell):
    c = cell.lower()
    if not c or c in ('—', '-'):
        return 'same'
    if 'нараст' in c or 'пик' in c:
        return 'same'
    for keys, mood in MUSIC:
        if any(k in c for k in keys):
            return mood
    return 'same'


def fmt(x):
    return f'{x:.1f}'.rstrip('0').rstrip('.') if abs(x - round(x)) > 1e-9 else str(int(round(x)))


def convert(ep, why=''):
    cast, places = ep['cast'], ep['places'] or ['pl_tv_studio']
    fid = re.match(r'(F\d\d)\s*(.*)', ep['meta'].get('Формат', 'F00'))
    out, t, music_runs = [], 0.0, []
    lines, ad_set, recent, prev_silent = [], None, [], False
    last_speaker_idx = max((i for i, r in enumerate(ep['rows']) if r['line'] not in ('', '—', '-')), default=-1)
    for k, r in enumerate(ep['rows']):
        txt = clean(r['line']) if r['line'] not in ('', '—', '-') else ''
        who_l = r['who'].lower()
        narrator = any(n in who_l for n in NARR) and not find_char(r['who'], cast)
        speaker = None if (not txt or narrator) else (find_char(r['who'], cast) or None)
        fr = r['frame']
        wide = re.match(r'\s*(ОБЩ|2Ш|СПЛИТ|ВСТ)', fr.upper()) is not None
        subject = None if wide else find_char(fr, cast)
        if speaker and (wide or subject is None):
            subject = speaker
        if subject is None:  # a wide or empty shot without a speaker on screen: the place
            subject = next((p for p in places if any(re.search(s, fr.lower()) for s in PLACES.get(p, []))), places[-1])
        ad = bool(fid) and fid.group(1) == 'F05'
        product = ad and subject in places and re.search(r'крем|баноч|тюбик|продукт|упаков|на белом|флакон|шрифт', fr.lower())
        if product and (re.search(r'крем|баноч|тюбик|флакон', fr.lower()) or ad_set):
            subject = ad_set = 'ad_cream'  # the device's beauty-commercial set
        if txt and k == last_speaker_idx and '[' not in txt:
            txt = '[deadpan] ' + txt
        dur = r['t1'] - r['t0']
        at = t + 0.3
        need = 0.3 + est(txt) + 0.4 if txt else 0
        dur = max(dur, round(need + 0.049, 1))
        P = camera(r, at, k, dur)
        if fid and fid.group(1) == 'F22':
            P['handheld'] = 1  # taxi: the camera is always in the moving car
        if txt and k == last_speaker_idx and 'snap' not in P and not prev_silent:
            P['snap'] = round(at, 2)  # the turn gets a crash zoom unless a silent beat already sets it up
        key = tuple(sorted((a, b) for a, b in P.items() if a != 'snap'))
        if len(recent) >= 2 and recent[-1] == recent[-2] == key and set(P) <= {'push', 'focus', 'handheld'}:
            P['push'] = 0.05 if P.get('push', 0.04) <= 0.03 else 0.02  # shot/reverse-shot: never 3 identical in a row
            key = tuple(sorted((a, b) for a, b in P.items() if a != 'snap'))
        recent.append(key)
        prev_silent = not txt
        cam = ' '.join(f'{a}={b}' if not isinstance(b, float) else f'{a}={fmt(b) if a == "snap" else b:}' for a, b in P.items())
        out.append(f'shot {fmt(t)}-{fmt(t + dur)}s: {subject} {cam}'.rstrip())
        if txt:
            if speaker and speaker == subject:
                out.append(f'say {speaker} "{txt}" at {fmt(at)}s')
            elif speaker:
                out.append(f'voice "{txt}" at {fmt(at)}s who={stubs.voice_of(speaker)}')
            else:
                tag = '[ad] ' if ('реклам' in who_l or product or (ad and mood_of(r['music']) == 'bright')) else '[deep] '
                out.append(f'voice "{tag}{txt}" at {fmt(at)}s')
            lines.append(txt)
        if product:
            for q in re.findall(r'«([^»]{2,30})»', r['line'])[:1]:
                out.append(f'text "{q.upper()}" at 0.2,0.25 size=0.08 color=#c4426a glow=#ffffff {fmt(t)}-{fmt(t + dur)}s')
        for q in re.findall(r'(?:надпис|титр|табло|слайд|плашк|экран)[^«]*«([^»]{2,40})»', fr, re.I):
            out.append(f'text "{q.upper()}" at 0.5,0.18 size=0.07 color=#ffffff glow=#000000 {fmt(t)}-{fmt(t + dur)}s')
        music_runs.append((t, t + dur, mood_of(r['music'])))
        t += dur
    # music: runs of one mood; 'same' continues the previous mood, None is silence
    mus, cur, start = [], None, 0.0
    for a, b, m in music_runs:
        if m == 'same':
            continue
        if m != cur:
            if cur:
                mus.append((start, a, cur))
            cur, start = m, a
    if cur:
        mus.append((start, t, cur))
    total = t
    head = [
        f'# format: {fid.group(1)} {fid.group(2)}' if fid else '# format: ?',
        f'# logline: {ep["meta"].get("Логлайн", "")}',
        f'# why it works: {why}',
        f'film title="{ep["title"]}" style=puppet fps=24 size=1920x1080',
    ]
    body = []
    for i, s in enumerate(out):
        body.append(s)
        if i == 0:
            body.append('fade in 0-0.6s')
    for a, b, m in mus:
        if b - a >= 1.5:
            tempo = {'bright': 118, 'tense': 92, 'wonder': 70, 'dark': 66, 'cozy': 84, 'calm': 72}[m]
            body.append(f'music mood={m} tempo={tempo} {fmt(a)}-{fmt(b)}s')
    body.append(f'fade out {fmt(total - 0.4)}-{fmt(total)}s')
    return '\n'.join(head + body) + '\n'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('ids', nargs='+')
    ap.add_argument('--out', default=str(stubs.PACK / 'fewshot'))
    ap.add_argument('--why', help='json {E004: "why it works"}')
    a = ap.parse_args()
    why = json.loads(Path(a.why).read_text()) if a.why else {}
    Path(a.out).mkdir(exist_ok=True)
    for eid in a.ids:
        ep = parse(eid)
        Path(a.out, f'{eid}.scene').write_text(convert(ep, why.get(eid, '')))
        print(eid, ep['title'])


if __name__ == '__main__':
    main()
