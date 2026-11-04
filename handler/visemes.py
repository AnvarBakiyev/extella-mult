"""Russian text -> visemes for the code-built puppets (puppet-characters-code).

The busts have six mouths: closed (rest), A, E, O, U, MBP. A spoken line becomes a per-frame list of these names:

1. g2p(): rule-based Russian grapheme -> phoneme. Handles iotated vowels (е ё ю я at a word start or after a vowel,
   ь, ъ give й + vowel), akanye (unstressed о sounds like а; stress is not marked, so in a word with several о only
   the last one keeps its O shape, and ё is always stressed), silent ь and ъ, the тс/тьс -> ц and сч/зч -> щ clusters.
2. Each phoneme maps to a viseme (VISEME): а я -> A, о ё -> O, у ю -> U, э е и ы -> E, п б м -> MBP (lips pressed),
   ф в -> E (upper teeth on the lower lip: a narrow mouth with the teeth showing), ш ж щ ч -> U (rounded, pushed
   forward), с з ц -> E (teeth together), the rest (т д н л р к г х й ...) -> closed, the rest shape between vowels.
3. viseme_track() lays the phonemes over the voiced part of the recording by loudness: cumulative phoneme weight
   (vowels heavy, consonants light) is matched to cumulative loudness of the voiced frames, so vowels land on the
   loud parts. Quiet frames narrow the mouth (A -> E, O -> U), silence closes it, single-frame flickers are removed.
   No text: loudness only (loud peaks A, softer E, dips closed).
4. synthetic_envelope() makes a loudness curve from the text alone (about 6 syllables a second, pauses at
   punctuation), so a film without recorded voices still has moving mouths.
"""
import hashlib
import re

import numpy as np

VISEMES = ('closed', 'A', 'E', 'O', 'U', 'MBP')
VOWELS = 'аеёиоуыэюя'
IOTATED = {'е': 'э', 'ё': 'о', 'ю': 'у', 'я': 'а'}
VISEME = {
    'а': 'A', 'о': 'O', 'у': 'U', 'ы': 'E', 'э': 'E', 'и': 'E',
    'п': 'MBP', 'б': 'MBP', 'м': 'MBP',
    'ф': 'E', 'в': 'E',
    'ш': 'U', 'ж': 'U', 'щ': 'U', 'ч': 'U',
    'с': 'E', 'з': 'E', 'ц': 'E',
}
# a little Latin, so names and brands in a line do not leave the mouth shut
LATIN = str.maketrans({'a': 'а', 'b': 'б', 'c': 'к', 'd': 'д', 'e': 'е', 'f': 'ф', 'g': 'г', 'h': 'х', 'i': 'и', 'j': 'ж',
                       'k': 'к', 'l': 'л', 'm': 'м', 'n': 'н', 'o': 'о', 'p': 'п', 'q': 'к', 'r': 'р', 's': 'с', 't': 'т',
                       'u': 'у', 'v': 'в', 'w': 'в', 'x': 'к', 'y': 'и', 'z': 'з'})
PAUSE = {',': 0.22, ';': 0.3, ':': 0.3, '—': 0.3, '-': 0.0, '.': 0.42, '!': 0.42, '?': 0.42, '…': 0.55}


class Phone:
    __slots__ = ('ph', 'vis', 'vowel', 'w')

    def __init__(self, ph, vowel):
        self.ph, self.vowel = ph, vowel
        self.vis = VISEME.get(ph, 'closed')
        self.w = 1.0 if vowel else (0.55 if self.vis != 'closed' else 0.4)

    def __repr__(self):
        return f'{self.ph}:{self.vis}'


def _word_g2p(w):
    out = []
    n_o = w.count('о')
    seen_o = 0
    stressed_yo = 'ё' in w
    i = 0
    while i < len(w):
        c = w[i]
        prev = w[i - 1] if i else ''
        nxt = w[i + 1] if i + 1 < len(w) else ''
        if c in 'ьъ':
            i += 1
            continue
        if c == 'т' and (w[i + 1:i + 3] == 'ьс' or nxt == 'с') and w[i + 1:].lstrip('ь').startswith('ся'):
            out.append(Phone('ц', False))  # -тся / -ться
            i += 3 if nxt == 'ь' else 2
            continue
        if c in 'сз' and nxt == 'ч':
            out.append(Phone('щ', False))
            i += 2
            continue
        if c in IOTATED:
            if not prev or prev in VOWELS or prev in 'ьъ':
                out.append(Phone('й', False))
            v = IOTATED[c]
            if c == 'ё' or v != 'о':
                out.append(Phone(v, True))
            i += 1
            continue
        if c == 'о':
            seen_o += 1
            # akanye: only the stressed о is round; guess it is the last о, unless ё carries the stress
            keep = (not stressed_yo) and (n_o == 1 or seen_o == n_o)
            out.append(Phone('о' if keep else 'а', True))
            i += 1
            continue
        if c in VOWELS:
            out.append(Phone(c, True))
        elif c.isalpha():
            out.append(Phone(c, False))
        i += 1
    return out


def g2p(text):
    """Russian text -> list of Phone and float pauses (seconds) at punctuation and between words."""
    t = re.sub(r'\[[^\]]*\]', ' ', text or '').lower().replace('ё', 'ё').translate(LATIN)
    t = t.replace('...', '…')
    seq = []
    for tok in re.findall(r'[а-яё]+|[,;:—.!?…]', t):
        if tok in PAUSE:
            if PAUSE[tok]:
                seq.append(PAUSE[tok])
            continue
        if seq and isinstance(seq[-1], Phone):
            seq.append(0.03)  # a tiny gap between words
        seq.extend(_word_g2p(tok))
    while seq and not isinstance(seq[-1], Phone):
        seq.pop()
    return seq


def phonemes(text):
    return [p for p in g2p(text) if isinstance(p, Phone)]


def visemes_of(text):
    """The viseme names of a text, one per phoneme (for tests and for the check)."""
    return [p.vis for p in phonemes(text)]


def estimate_seconds(text):
    """How long the line takes when spoken at an even pace (about 6 syllables a second)."""
    s = 0.0
    for p in g2p(text):
        s += p if isinstance(p, float) else (0.12 if p.vowel else 0.05)
    return max(0.4, s + 0.15)


def synthetic_envelope(text, fps, seed=None):
    """A loudness curve (one value per frame, 0..1) made from the text alone: a bump per syllable, silence at pauses."""
    seq = g2p(text)
    n = int(round(estimate_seconds(text) * fps)) + 1
    env = np.zeros(n, np.float32)
    h = int(hashlib.sha1((text or '').encode()).hexdigest()[:8], 16) if seed is None else seed
    rng = np.random.default_rng(h)
    t = 0.05
    for p in seq:
        if isinstance(p, float):
            t += p
            continue
        d = 0.12 if p.vowel else 0.05
        a = (0.65 + 0.35 * rng.random()) if p.vowel else 0.32
        c = (t + d / 2) * fps
        r = max(1.0, d * fps * 0.9)
        k = np.arange(n)
        bump = np.clip(1 - ((k - c) / r) ** 2, 0, None) * a
        env = np.maximum(env, bump.astype(np.float32))
        t += d
    return env


def loudness(samples, sr, fps, n=None):
    hop = sr // fps
    n = n if n is not None else int(np.ceil(len(samples) / hop))
    out = np.zeros(n, np.float32)
    for i in range(n):
        seg = samples[i * hop:(i + 1) * hop]
        if len(seg):
            out[i] = float(np.sqrt(np.mean(seg.astype(np.float64) ** 2)))
    return out


def _voiced(r, thr=0.12):
    v = r > thr
    # close gaps of one frame inside a word, drop single-frame blips
    for i in range(1, len(v) - 1):
        if not v[i] and v[i - 1] and v[i + 1]:
            v[i] = True
    for i in range(len(v)):
        if v[i] and (i == 0 or not v[i - 1]) and (i + 1 >= len(v) or not v[i + 1]):
            v[i] = False
    return v


def _despeckle(track):
    out = list(track)
    for i in range(1, len(out) - 1):
        if out[i] != out[i - 1] and out[i] != out[i + 1]:
            out[i] = out[i - 1] if out[i] != 'MBP' else out[i]  # keep a labial closure even when it is short
    return out


def viseme_track(text, env):
    """Per frame viseme names for one line. env: loudness per frame (any scale). text may be empty."""
    env = np.asarray(env, np.float64)
    if len(env) == 0:
        return []
    top = np.percentile(env[env > 0], 90) if (env > 0).any() else 1.0
    r = env / (top + 1e-9)
    voiced = _voiced(r)
    phones = phonemes(text)
    out = ['closed'] * len(r)
    if not phones:  # loudness only
        for i in range(len(r)):
            if not voiced[i]:
                continue
            lo, hi = max(0, i - 2), min(len(r), i + 3)
            peak = r[lo:hi].max()
            out[i] = 'A' if (r[i] >= 0.85 * peak and r[i] > 0.45) else ('E' if r[i] >= 0.4 * peak else 'closed')
        return _despeckle(out)
    idx = np.nonzero(voiced)[0]
    if len(idx) == 0:
        return out
    energy = r[idx] + 0.15  # a floor so quiet consonants still get a little time
    cum = np.concatenate([[0], np.cumsum(energy)])
    cum = cum / cum[-1]
    w = np.array([p.w * (1.6 if p.vowel else 1.0) for p in phones])
    edges = np.concatenate([[0], np.cumsum(w)]) / w.sum()
    for j, i in enumerate(idx):
        mid = (cum[j] + cum[j + 1]) / 2
        k = min(len(phones) - 1, int(np.searchsorted(edges, mid, side='right') - 1))
        v = phones[k].vis
        if r[i] < 0.3:  # quiet: the mouth only half opens
            v = {'A': 'E', 'O': 'U'}.get(v, v)
        out[i] = v
    return _despeckle(out)
