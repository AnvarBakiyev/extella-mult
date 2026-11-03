"""Parser for the .scene language. Produces a list of Stmt; raises SceneError with a worded message."""
import re
import shlex


class SceneError(Exception):
    pass


class Stmt:
    def __init__(self, kind, line, raw):
        self.kind = kind          # film, music, scene, camera, effect, text, fade, sfx, actor
        self.line = line          # 1-based line number
        self.raw = raw
        self.words = []           # bare words in order (after the keyword)
        self.params = {}          # key=value
        self.t0 = self.t1 = None  # seconds
        self.at = None            # 'at' time for sfx
        self.frm = self.to = None  # positions for from/to
        self.pos = None           # 'at' position
        self.elements = []        # for scene: [(name, params)]
        self.text = None

    def __repr__(self):
        return f"<{self.kind} L{self.line} {self.words} {self.params} {self.t0}-{self.t1}>"


TIME_RANGE = re.compile(r'^(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)s$')
TIME_ONE = re.compile(r'^(\d+(?:\.\d+)?)s$')
NUM_RANGE = re.compile(r'^(-?\d+(?:\.\d+)?)-(-?\d+(?:\.\d+)?)$')
ELEMENT = re.compile(r'^([a-z_][a-z0-9_]*)(?:\((.*)\))?$')


def _value(v):
    if re.fullmatch(r'-?\d+', v):
        return int(v)
    if re.fullmatch(r'-?\d+\.\d*', v):
        return float(v)
    if re.fullmatch(r'-?\d+(\.\d+)?,-?\d+(\.\d+)?', v):
        return tuple(float(x) for x in v.split(','))
    if re.fullmatch(r'\d+x\d+', v):
        return tuple(int(x) for x in v.split('x'))
    return v


def _pos(tok, line):
    if re.fullmatch(r'-?\d+(\.\d+)?,-?\d+(\.\d+)?', tok):
        return tuple(float(x) for x in tok.split(','))
    if re.fullmatch(r'-?\d+(\.\d+)?', tok):  # x alone: the actor keeps its y= line
        return (float(tok), None)
    if re.fullmatch(r'[a-z_]+', tok):
        return tok
    raise SceneError(f"line {line}: '{tok}' is not a position (use a name like left/center/right or x,y)")


def _elements(joined, n):
    """Elements may contain spaces inside parentheses: split on top-level spaces."""
    out = []
    for el in _split_top(joined):
        m2 = ELEMENT.match(el)
        if not m2:
            raise SceneError(f"line {n}: '{el}' is not an element name (letters, digits, underscore, optional (k=v,...))")
        params = {}
        if m2.group(2):
            for kv in m2.group(2).split(','):
                if '=' not in kv:
                    raise SceneError(f"line {n}: element parameter '{kv}' must be key=value")
                k, v = kv.split('=', 1)
                params[k.strip()] = _value(v.strip())
        out.append((m2.group(1), params))
    return out


def parse(text):
    stmts = []
    for n, raw in enumerate(text.splitlines(), 1):
        line = _strip_comment(raw).strip()
        if not line:
            continue
        try:
            toks = shlex.split(line, posix=True)
        except ValueError as e:
            raise SceneError(f"line {n}: cannot read the line ({e})")
        head = toks[0]
        if head == 'scene':
            st = Stmt('scene', n, raw)
            if len(toks) < 2:
                raise SceneError(f"line {n}: scene needs a time range like 'scene 0-8s: sky moon'")
            m = TIME_RANGE.match(toks[1].rstrip(':'))
            if not m:
                raise SceneError(f"line {n}: scene time must look like 0-8s, got '{toks[1]}'")
            st.t0, st.t1 = float(m.group(1)), float(m.group(2))
            rest = toks[2:]
            if rest and rest[0] == ':':
                rest = rest[1:]
            st.elements.extend(_elements(' '.join(rest), n))
            stmts.append(st)
            continue
        # a line with no time on it, right under a scene, adds elements to that scene: 'lamp(x=0.2,y=0.97)'
        if not re.search(r'\d(\.\d+)?s\b', line) and head not in ('film', 'music') and stmts and any(x.kind == 'scene' for x in stmts):
            last = [x for x in stmts if x.kind == 'scene'][-1]
            last.elements.extend(_elements(line, n))
            continue
        kind = head if head in ('film', 'music', 'camera', 'effect', 'text', 'fade', 'sfx') else 'actor'
        st = Stmt(kind, n, raw)
        if kind == 'actor':
            st.words.append(head)
        i = 1
        while i < len(toks):
            t = toks[i]
            if kind == 'text' and st.text is None and i == 1:
                st.text = t
            elif TIME_RANGE.match(t):
                m = TIME_RANGE.match(t)
                st.t0, st.t1 = float(m.group(1)), float(m.group(2))
            elif t == 'at' and i + 1 < len(toks):
                nxt = toks[i + 1]
                if TIME_ONE.match(nxt):
                    st.at = float(TIME_ONE.match(nxt).group(1))
                else:
                    st.pos = _pos(nxt, n)
                i += 1
            elif t == 'from' and i + 1 < len(toks):
                nxt = toks[i + 1]
                if TIME_ONE.match(nxt):
                    st.at = float(TIME_ONE.match(nxt).group(1))
                else:
                    st.frm = _pos(nxt, n)
                i += 1
            elif t == 'to' and i + 1 < len(toks):
                st.to = _pos(toks[i + 1], n)
                i += 1
            elif '=' in t:
                k, v = t.split('=', 1)
                st.params[k] = _value(v)
            elif NUM_RANGE.match(t) and kind == 'camera':
                m = NUM_RANGE.match(t)
                st.params['range'] = (float(m.group(1)), float(m.group(2)))
            else:
                st.words.append(t)
            i += 1
        stmts.append(st)
    return stmts


def _strip_comment(raw):
    """A '#' starts a comment only at line start or after a space, and not inside quotes (so color=#ffd890 survives)."""
    inq = False
    for i, ch in enumerate(raw):
        if ch == '"':
            inq = not inq
        elif ch == '#' and not inq and (i == 0 or raw[i - 1].isspace()):
            return raw[:i]
    return raw


def _split_top(s):
    out, depth, cur = [], 0, ''
    for ch in s:
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
        if ch == ' ' and depth == 0:
            if cur:
                out.append(cur)
            cur = ''
        else:
            cur += ch
    if cur:
        out.append(cur)
    return out
