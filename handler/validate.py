"""Validates a parsed program against the vocabulary; raises SceneError with messages in words."""
from .parser import SceneError
from .elements import ELEMENTS
from .actors import ACTORS, POSITIONS
from .effects import EFFECTS
from .lettering import GLYPHS
from .audio import MOODS, SFX, KEYS
from .lib3d import ELEMENTS3D, ACTORS3D


def _vocab(style):
    """(elements, {actor: actions}) of one visual style; a film never mixes styles."""
    if style in ('3d', 'toon'):
        return ELEMENTS3D, ACTORS3D
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
        self.length = 0.0
        self.style = '2d'


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
        if prog.style not in ('2d', '3d', 'toon'):
            raise SceneError(f"line {f.line}: style must be 2d, 3d or toon")
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
                shown = ', '.join(sorted(acts)) if len(acts) <= 12 else f"{len(acts)} actors, search the concepts for the list"
                raise SceneError(f"line {st.line}: '{name}' is not a known statement or actor in style={prog.style}; actors: {shown}; statements: film, scene, camera, effect, text, fade, sfx, music")
            actions = acts[name]
            if str(st.params.get('facing', 1)) == 'front' and prog.style == '2d':
                raise SceneError(f"line {st.line}: facing=front works only in 3d films; in 2d use facing=1 or facing=-1")
            if len(st.words) < 2:
                raise SceneError(f"line {st.line}: {name} needs an action: {', '.join(actions)}")
            if st.words[1] not in actions:
                raise SceneError(f"line {st.line}: {name} cannot '{st.words[1]}'; it can: {', '.join(actions)}")
            _need_time(st, f"{name} {st.words[1]}")
            _check_pos(st, st.frm); _check_pos(st, st.to); _check_pos(st, st.pos)
            if (st.frm is None) != (st.to is None):
                raise SceneError(f"line {st.line}: 'from' and 'to' go together (from left to center)")
            st.scene = _scene_for(prog, st, f"{name} {st.words[1]}")
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
            if not st.words or st.words[0] not in EFFECTS:
                raise SceneError(f"line {st.line}: unknown effect '{st.words[0] if st.words else ''}'; known effects: {', '.join(sorted(k for k in EFFECTS if k != 'handwrite'))}")
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
    prog.music.sort(key=lambda s: s.at)
    return prog
