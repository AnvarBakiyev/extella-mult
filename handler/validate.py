import os
import re
"""Validates a parsed program against the vocabulary; raises SceneError with messages in words."""
from .parser import SceneError
from .elements import ELEMENTS
from .actors import ACTORS, POSITIONS
from .effects import EFFECTS
from .lettering import GLYPHS
from .audio import MOODS, SFX, KEYS
from .lib3d import ELEMENTS3D, ACTORS3D
from .felt_actors import PEOPLE, SKINS, HAIRSTYLES

PEOPLE_LOOKS = (PEOPLE, list(SKINS), HAIRSTYLES)


def _vocab(style):
    """(elements, {actor: actions}) of one visual style; a film never mixes styles."""
    if style in ('3d', 'toon'):
        return ELEMENTS3D, ACTORS3D
    if style == 'felt':
        from .felt_elements import FE
        from .felt_actors import FA
        return set(FE), {n: a for n, (_, a) in FA.items()}
    return set(ELEMENTS), {n: a for n, (_, a) in ACTORS.items()}


def _other(style):
    return '2d' if style in ('3d', 'toon') else '3d'

CAMERA_MOVES = {'pan': ('up', 'down', 'left', 'right'), 'zoom': (), 'shake': (), 'static': ()}


class Program:
    def __init__(self, stmts):
        self.stmts = stmts
        self.title = 'untitled'
        self.fps = 24
        self.size = (1920, 804)
        self.scenes = []
        self.music = []
        self.sfx = []
        self.voices = []
        self.length = 0.0
        self.style = '2d'
        self.look = ''
        self.warnings = []


def _need_time(st, what):
    if st.t0 is None:
        raise SceneError(f"line {st.line}: {what} needs a time range like 2-6s")
    if st.t1 <= st.t0:
        raise SceneError(f"line {st.line}: time range {st.t0:g}-{st.t1:g}s ends before it starts")


def _scene_for(prog, st, what):
    for sc in prog.scenes:
        if sc.t0 <= st.t0 < sc.t1:
            if st.t1 > sc.t1 + 1e-6:
                raise SceneError(f"line {st.line}: {what} {st.t0:g}-{st.t1:g}s runs past the end of its scene ({sc.t0:g}-{sc.t1:g}s); split it per scene")
            return sc
    raise SceneError(f"line {st.line}: {what} at {st.t0:g}s is outside every scene")


def _check_pos(st, pos):
    if pos is None or isinstance(pos, tuple):
        return
    if pos not in POSITIONS:
        raise SceneError(f"line {st.line}: unknown position '{pos}'; use one of {', '.join(POSITIONS)} or x,y")


def _home(st, others, what):
    """Where a character is before a line that names no place: where its last line ended, else where its next line starts."""
    from .actors import _lerp_pos
    if st.pos is not None:
        return _lerp_pos(st, 0.0, st.params.get('y', 0.86))
    before = [a for a in others if a.t1 <= st.t0 + 1e-6]
    after = [a for a in others if a.t0 >= st.t1 - 1e-6]
    if before:
        a = before[-1]
        return getattr(a, 'home', None) or _lerp_pos(a, 1.0, a.params.get('y', 0.86))
    if after:
        return _lerp_pos(after[0], 0.0, after[0].params.get('y', 0.86))
    raise SceneError(f"line {st.line}: {st.words[0]} is not in the frame before {what}; add a line like '{st.words[0]} stand at 0.4 {max(0.0, st.t0 - 1):g}-{st.t0:g}s' or give a place with at 0.4")


def _link_pair(prog, st, acts):
    """Checks a hug, give or hold_hands line in words and ties it to the partner's lines."""
    from .felt_actors import PAIR_ACTIONS, HELD, _plain, _line_at
    name, act = st.words[0], st.words[1]
    example = f"{name} {act} cat ball 2-3s" if act == 'give' else f"{name} {act} cat 3-5s"
    if len(st.words) < 3:
        raise SceneError(f"line {st.line}: {act} needs a partner: {example}")
    mate = st.words[2]
    known = _vocab(prog.style)[1]
    if mate not in known:
        raise SceneError(f"line {st.line}: '{mate}' is not a known actor, so {name} cannot {act} with it")
    if mate == name:
        raise SceneError(f"line {st.line}: {name} needs someone else for {act}")
    if act not in known[mate]:
        raise SceneError(f"line {st.line}: {mate} cannot take part in {act}; it can: {', '.join(known[mate])}")
    if act == 'give' and (len(st.words) < 4 or st.words[3] not in HELD):
        raise SceneError(f"line {st.line}: give needs a thing, one of {', '.join(HELD)}: {example}")
    lines = sorted((a for a in acts if a.words[0] == mate and a.scene is st.scene and a.t0 < st.t1 and st.t0 < a.t1), key=lambda a: a.t0)
    until = st.t0
    for a in lines:
        if a.t0 > until + 1e-6:
            break
        until = max(until, a.t1)
    if until < st.t1 - 1e-6:
        raise SceneError(f"line {st.line}: {mate} is not in the frame at {until:g}s, while {name} wants to {act}; add a line like '{mate} stand at 0.5 {st.t0:g}-{st.t1:g}s'")
    for a in lines:
        if a.words[1] in PAIR_ACTIONS or a.words[1] == 'sleep':
            raise SceneError(f"line {st.line}: {mate} is busy at that time ({a.words[1]}, line {a.line}), so {name} cannot {act} with it")
    others = sorted((a for a in acts if a.words[0] == name and a.scene is st.scene and a is not st), key=lambda a: a.t0)
    st.home = _home(st, others, act)
    for k in ('y', 'size', 'color', 'hair', 'skin', 'hairstyle'):
        for a in others:
            if k in a.params:
                st.params.setdefault(k, a.params[k])
    st.ar = prog.size[1] / prog.size[0]
    st.mates = lines
    far = abs(st.home[0] - _plain(_line_at(lines, st.t0), st.t0)[0])
    if far > 0.3 + 1e-6:
        raise SceneError(f"line {st.line}: {name} and {mate} are {far:.2f} of the frame apart at {st.t0:g}s, too far for {act} (at most 0.3); move them closer or let one of them walk up first")
    nxt = next((a for a in others if a.t0 >= st.t1 - 1e-6), None)
    st.after = None
    if nxt is not None and abs(nxt.t0 - st.t1) < 1e-6:
        st.after = _plain(nxt, nxt.t0)[0] if nxt.words[1] not in PAIR_ACTIONS else None
    for a in lines:
        a.pairs.append(st)
    if act == 'give':  # the thing changes hands for the rest of the scene
        for a in acts:
            if a.scene is st.scene and a.t0 >= st.t1 - 1e-6:
                if a.words[0] == mate:
                    a.params.setdefault('holds', st.words[3])
                elif a.words[0] == name and a.params.get('holds') == st.words[3]:
                    del a.params['holds']
    i = max(prog.stmts.index(a) for a in lines)  # the arms of the one who starts go over the partner
    if prog.stmts.index(st) < i:
        prog.stmts.remove(st)
        prog.stmts.insert(i, st)


def _link_sleep(prog, st, acts):
    """A sleeper with no place of its own lies in the bed of its scene; a bed holds one sleeper at a time."""
    name = st.words[0]
    others = sorted((a for a in acts if a.words[0] == name and a.scene is st.scene and a is not st), key=lambda a: a.t0)
    for k in ('y', 'size', 'color', 'hair', 'skin', 'hairstyle'):
        for a in others:
            if k in a.params and not (k == 'y' and st.pos is None):
                st.params.setdefault(k, a.params[k])
    beds = [p for n, p in st.scene.elements if n == 'bed']
    if st.pos is None:
        if not beds:
            raise SceneError(f"line {st.line}: there is no bed in this scene for {name} to sleep in; add bed(x=0.3,y=0.95) to the scene line or give a place: {name} sleep at 0.4 {st.t0:g}-{st.t1:g}s y=0.95")
        b = beds[0]
        bx, by, bs = b.get('x', 0.3), b.get('y', 0.88), b.get('s', 1.0)
        st.pos = (bx - 0.115 * bs, by - 0.13 * bs)
        st.params.setdefault('blanket', b.get('color', '#9fc8e8'))
        st.in_bed = True
        for a in acts:
            if a is not st and getattr(a, 'in_bed', False) and a.scene is st.scene and a.t0 < st.t1 and st.t0 < a.t1:
                raise SceneError(f"line {st.line}: {a.words[0]} already sleeps in this bed at that time (line {a.line}); give {name} its own place: {name} sleep at 0.6 {st.t0:g}-{st.t1:g}s y=0.97")


def validate(stmts):
    prog = Program(stmts)
    films = [s for s in stmts if s.kind == 'film']
    if len(films) > 1:
        raise SceneError(f"line {films[1].line}: only one 'film' line is allowed")
    if films:
        f = films[0]
        prog.title = f.params.get('title', prog.title)
        prog.fps = int(f.params.get('fps', prog.fps))
        prog.size = tuple(f.params.get('size', prog.size))
        prog.style = str(f.params.get('style', '2d'))
        prog.look = str(f.params.get('look', ''))
        if prog.look not in ('', 'flat', 'felt'):
            raise SceneError(f"line {f.line}: look must be flat or felt")
        if prog.style not in ('2d', '3d', 'toon', 'felt'):
            raise SceneError(f"line {f.line}: style must be felt, 2d, 3d or toon")
        if not (8 <= prog.fps <= 60):
            raise SceneError(f"line {f.line}: fps must be between 8 and 60")
    scenes = sorted([s for s in stmts if s.kind == 'scene'], key=lambda s: s.t0)
    if not scenes:
        raise SceneError("the program has no 'scene' lines; nothing to render")
    for sc in scenes:
        if sc.t1 <= sc.t0:
            raise SceneError(f"line {sc.line}: scene {sc.t0:g}-{sc.t1:g}s ends before it starts")
        if not sc.elements:
            raise SceneError(f"line {sc.line}: scene {sc.t0:g}-{sc.t1:g}s lists no elements; a scene needs at least a background")
        elems, _ = _vocab(prog.style)
        for name, params in sc.elements:
            if name not in elems:
                if name in _vocab(_other(prog.style))[0]:
                    raise SceneError(f"line {sc.line}: element '{name}' belongs to style={_other(prog.style)}, the film is style={prog.style}; do not mix styles")
                close = sorted(e for e in elems if e.startswith(name[:3]))[:8]
                hint = f" (did you mean {', '.join(close)}?)" if close else ''
                raise SceneError(f"line {sc.line}: unknown element '{name}'{hint}; there are {len(elems)} elements in style={prog.style}, search the concepts for the list")
    for a, b in zip(scenes, scenes[1:]):
        if b.t0 < a.t1 - 1e-6:
            raise SceneError(f"line {b.line}: scene {b.t0:g}-{b.t1:g}s overlaps scene {a.t0:g}-{a.t1:g}s (line {a.line})")
        if b.t0 > a.t1 + 1e-6:
            raise SceneError(f"line {b.line}: gap between scene ending at {a.t1:g}s (line {a.line}) and scene starting at {b.t0:g}s; scenes must touch")
    if scenes[0].t0 != 0:
        raise SceneError(f"line {scenes[0].line}: the first scene must start at 0s, it starts at {scenes[0].t0:g}s")
    prog.scenes = scenes
    prog.length = scenes[-1].t1

    for st in stmts:
        if st.kind in ('film', 'scene'):
            continue
        if st.kind == 'actor':
            name = st.words[0]
            _, acts = _vocab(prog.style)
            if name not in acts:
                if name in _vocab(_other(prog.style))[1]:
                    raise SceneError(f"line {st.line}: {name} is a {_other(prog.style)} actor, the film is style={prog.style}; do not mix styles")
                base = name.split('(')[0]
                if base in _vocab(prog.style)[0]:
                    raise SceneError(f"line {st.line}: {base} is an element, not an actor: elements have no seconds and no actions. "
                                     f"Put '{base}(x=..,y=..)' on the scene line or on its own line under it, without a time; "
                                     f"to move it use its parameters (rocket: flying=1 rise=.. drift=.. tilt=..)")
                shown = ', '.join(sorted(acts)) if len(acts) <= 12 else f"{len(acts)} actors, search the concepts for the list"
                raise SceneError(f"line {st.line}: '{name}' is not a known statement or actor in style={prog.style}; actors: {shown}; statements: film, scene, camera, effect, text, fade, sfx, voice, music")
            actions = acts[name]
            if str(st.params.get('facing', 1)) == 'front' and prog.style == '2d':
                raise SceneError(f"line {st.line}: facing=front works only in 3d films; in 2d use facing=1 or facing=-1")
            if len(st.words) < 2:
                raise SceneError(f"line {st.line}: {name} needs an action: {', '.join(actions)}")
            if st.words[1] not in actions:
                raise SceneError(f"line {st.line}: {name} cannot '{st.words[1]}'; it can: {', '.join(actions)}")
            if prog.style == 'felt' and name in PEOPLE_LOOKS[0]:
                skins, styles = PEOPLE_LOOKS[1:]
                skin = st.params.get('skin')
                if skin is not None and skin not in skins and not re.fullmatch(r'#[0-9a-fA-F]{6}', str(skin)):
                    raise SceneError(f"line {st.line}: skin '{skin}' unknown; use one of {', '.join(skins)} or #rrggbb")
                if st.params.get('hairstyle', styles[0]) not in styles:
                    raise SceneError(f"line {st.line}: hairstyle '{st.params['hairstyle']}' unknown; hairstyles: {', '.join(styles)}")
            if 'holds' in st.params and prog.style == 'felt':
                from .felt_actors import HELD
                if st.params['holds'] not in HELD:
                    raise SceneError(f"line {st.line}: {name} cannot hold '{st.params['holds']}'; things to hold: {', '.join(HELD)}")
            if 'mood' in st.params:
                if prog.style != 'felt':
                    raise SceneError(f"line {st.line}: mood= works only in style=felt films")
                from .felt_actors import FACE_MOODS
                if st.params['mood'] not in FACE_MOODS:
                    raise SceneError(f"line {st.line}: mood '{st.params['mood']}' unknown; moods: {', '.join(FACE_MOODS)}")
            _need_time(st, f"{name} {st.words[1]}")
            _check_pos(st, st.frm); _check_pos(st, st.to); _check_pos(st, st.pos)
            if (st.frm is None) != (st.to is None):  # one end given: come in from, or go out to, the nearer side
                from .lib3d import _x
                if st.frm is None:
                    st.frm = 'offleft' if _x(st.to) >= 0.5 else 'offright'
                else:
                    st.to = 'offright' if _x(st.frm) <= 0.5 else 'offleft'
            st.scene = _scene_for(prog, st, f"{name} {st.words[1]}")
        elif st.kind == 'say':
            name = st.words[0]
            if prog.style != 'felt':
                raise SceneError(f"line {st.line}: say works only in style=felt films")
            if name not in _vocab(prog.style)[1]:
                raise SceneError(f"line {st.line}: '{name}' is not a known actor, so it cannot say anything")
            if not st.text or not st.text.strip():
                raise SceneError(f"line {st.line}: say needs the words in quotes: {name} say \"Привет!\" 3-5s")
            if len(st.text) > 90 or st.text.count('\n') > 3:
                raise SceneError(f"line {st.line}: this line is too long for one bubble (at most 90 letters and 4 lines); split it into two say lines one after the other")
            _need_time(st, f"{name} say")
            _check_pos(st, st.pos)
            st.scene = _scene_for(prog, st, f"{name} say")
        elif st.kind == 'camera':
            if not st.words or st.words[0] not in CAMERA_MOVES:
                raise SceneError(f"line {st.line}: camera move must be one of {', '.join(CAMERA_MOVES)}")
            mv = st.words[0]
            if mv == 'pan':
                if len(st.words) < 2 or st.words[1] not in CAMERA_MOVES['pan']:
                    raise SceneError(f"line {st.line}: camera pan needs a direction: up, down, left or right")
            if mv == 'zoom' and 'range' not in st.params:
                raise SceneError(f"line {st.line}: camera zoom needs a range like 1.0-1.3")
            _need_time(st, f"camera {mv}")
            st.scene = _scene_for(prog, st, f"camera {mv}")
        elif st.kind == 'effect':
            if prog.style in ('3d', 'toon'):
                raise SceneError(f"line {st.line}: effects are drawn 2d and cannot be used in a style=3d or style=toon film; use actors, text, fade, camera, sfx and music")
            effs = EFFECTS
            if prog.style == 'felt':
                from .felt_effects import FX as effs
            if not st.words or st.words[0] not in effs:
                raise SceneError(f"line {st.line}: unknown effect '{st.words[0] if st.words else ''}'; known effects: {', '.join(sorted(k for k in effs if k not in ('handwrite', 'font_text')))}")
            _need_time(st, f"effect {st.words[0]}")
            st.scene = _scene_for(prog, st, f"effect {st.words[0]}")
        elif st.kind == 'text':
            if not st.text:
                raise SceneError(f"line {st.line}: text needs a quoted string, e.g. text \"Fable\" handwritten")
            if 'handwritten' not in st.words and 'font' not in st.words:
                raise SceneError(f"line {st.line}: text needs a style word: handwritten (drawn letters, limited set) or font (any letters, Cyrillic too)")
            bad = [ch for ch in st.text if ch not in GLYPHS] if 'handwritten' in st.words else []
            if bad:
                raise SceneError(f"line {st.line}: the handwritten lettering has no glyph for {', '.join(repr(c) for c in bad)}; available: {''.join(sorted(k for k in GLYPHS if k != ' '))}. Write 'text \"...\" font' instead to use any letters")
            if not isinstance(st.pos, tuple):
                raise SceneError(f"line {st.line}: text needs a position 'at x,y'")
            _need_time(st, 'text')
            st.scene = _scene_for(prog, st, 'text')
        elif st.kind == 'fade':
            if not st.words or st.words[0] not in ('in', 'out'):
                raise SceneError(f"line {st.line}: fade must be 'fade in' or 'fade out'")
            _need_time(st, 'fade')
            if st.t1 > prog.length + 1e-6:
                raise SceneError(f"line {st.line}: fade ends at {st.t1:g}s but the film ends at {prog.length:g}s")
        elif st.kind == 'sfx':
            if not st.words or st.words[0] not in SFX:
                raise SceneError(f"line {st.line}: unknown sound '{st.words[0] if st.words else ''}'; known sounds: {', '.join(sorted(SFX))}")
            if st.at is None:
                raise SceneError(f"line {st.line}: sfx needs a time: sfx {st.words[0]} at 12s")
            if not (0 <= st.at <= prog.length):
                raise SceneError(f"line {st.line}: sfx at {st.at:g}s is outside the film (0-{prog.length:g}s)")
            prog.sfx.append(st)
        elif st.kind == 'voice':
            from .audio import VOICES, voice_key
            if st.at is None:
                raise SceneError(f"line {st.line}: voice needs a start time: voice \"Привет!\" at 2s who=narrator")
            if not (0 <= st.at < prog.length):
                raise SceneError(f"line {st.line}: voice at {st.at:g}s is outside the film (0-{prog.length:g}s)")
            if 'file' in st.params:
                if not os.path.isfile(os.path.expanduser(str(st.params['file']))):
                    raise SceneError(f"line {st.line}: voice file {st.params['file']} not found on this device")
            elif not st.text:
                raise SceneError(f"line {st.line}: voice needs the words in quotes or a ready file: voice \"Поехали!\" at 2s who=narrator, or voice file=~/a.mp3 at 2s")
            else:
                who = st.params.get('who', 'narrator')
                if who not in VOICES:
                    raise SceneError(f"line {st.line}: unknown voice who={who}; voices: {', '.join(VOICES)}")
                if not voice_key():
                    raise SceneError(f"line {st.line}: spoken lines need an ElevenLabs key on this device (\"elevenlabs_key\" in ~/extella-mult/config.json); "
                                     "without it use a ready recording: voice file=~/line.mp3 at 2s, or tell the person and leave the line out")
            prog.voices.append(st)
        elif st.kind == 'music':
            mood = st.params.get('mood')
            if mood not in MOODS:
                raise SceneError(f"line {st.line}: music mood '{mood}' unknown; moods: {', '.join(MOODS)}")
            key = str(st.params.get('key', 'C'))
            if key not in KEYS:
                raise SceneError(f"line {st.line}: music key '{key}' unknown; keys: {', '.join(KEYS)}")
            tempo = st.params.get('tempo', 72)
            if not (40 <= tempo <= 200):
                raise SceneError(f"line {st.line}: tempo {tempo} is outside 40-200")
            st.at = st.at or 0.0
            if st.at > prog.length:
                raise SceneError(f"line {st.line}: music starts at {st.at:g}s, after the film ends ({prog.length:g}s)")
            prog.music.append(st)
    acts = [s for s in stmts if s.kind == 'actor']
    for i, a in enumerate(acts):
        for b in acts[i + 1:]:
            if a.words[0] == b.words[0] and a.t0 < b.t1 - 1e-6 and b.t0 < a.t1 - 1e-6:
                raise SceneError(f"line {b.line}: {b.words[0]} {b.words[1]} {b.t0:g}-{b.t1:g}s overlaps {a.words[0]} {a.words[1]} {a.t0:g}-{a.t1:g}s (line {a.line}); one {a.words[0]} does one action at a time, end the first action where the second starts")
    if prog.style == 'felt':
        from .felt_actors import PAIR_ACTIONS
        for st in sorted(acts, key=lambda a: a.t0):
            if st.words[1] == 'sleep':
                _link_sleep(prog, st, acts)
            elif st.words[1] in PAIR_ACTIONS:
                _link_pair(prog, st, acts)
    for st in stmts:  # a bubble hangs over its speaker, so the speaker must be in the frame while it talks
        if st.kind == 'say' and st.pos is None and not any(a.words[0] == st.words[0] and a.t0 < st.t1 and st.t0 < a.t1 for a in acts):
            raise SceneError(f"line {st.line}: {st.words[0]} says something at {st.t0:g}-{st.t1:g}s but is not in the frame then; add a line like '{st.words[0]} stand at 0.5 {st.t0:g}-{st.t1:g}s' or give the bubble a place with at x,y")
    if any(s.kind == 'say' for s in stmts):
        from .felt_effects import say_warnings
        prog.warnings += say_warnings(prog)
    prog.music.sort(key=lambda s: s.at)
    return prog
