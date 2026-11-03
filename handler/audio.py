"""Synthesized score and sound effects (numpy only). Output: stereo float32 at SR."""
import math
import numpy as np
from scipy.signal import butter, lfilter

SR = 48000
KEYS = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11, 'Bb': 10, 'Eb': 3, 'Ab': 8}
# mood: scale degrees (semitones), chord progression (root degree, kind), pluck density, bell density, pad brightness
MOODS = {
    'wonder': dict(scale=[0, 2, 4, 7, 9, 11], chords=[(0, 'maj9'), (9, 'min7'), (5, 'maj7'), (7, 'sus')], pluck=0.5, bell=0.15, pad=0.5, octave=0),
    'dark': dict(scale=[0, 2, 3, 5, 7, 8, 10], chords=[(0, 'min'), (8, 'maj'), (5, 'min'), (7, 'min')], pluck=0.2, bell=0.05, pad=0.7, octave=-1),
    'bright': dict(scale=[0, 2, 4, 7, 9], chords=[(0, 'maj'), (5, 'maj7'), (9, 'min7'), (7, 'sus')], pluck=0.9, bell=0.3, pad=0.45, octave=1),
    'tense': dict(scale=[0, 2, 3, 5, 7, 8, 11], chords=[(0, 'min'), (0, 'min'), (3, 'maj'), (11, 'dim')], pluck=0.7, bell=0.0, pad=0.8, octave=0),
    'cozy': dict(scale=[0, 2, 4, 5, 7, 9], chords=[(0, 'maj7'), (2, 'min7'), (5, 'maj7'), (7, 'sus')], pluck=0.8, bell=0.2, pad=0.35, octave=0),
    'calm': dict(scale=[0, 2, 4, 7, 9], chords=[(0, 'maj9'), (5, 'maj7')], pluck=0.3, bell=0.1, pad=0.5, octave=0),
}
CHORD = {'maj': [0, 4, 7], 'min': [0, 3, 7], 'maj7': [0, 4, 7, 11], 'min7': [0, 3, 7, 10], 'maj9': [0, 4, 7, 11, 14], 'sus': [0, 5, 7], 'dim': [0, 3, 6]}


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def env(n, a, d, s, r, hold):
    """ADSR envelope of n samples; hold = samples of sustain."""
    a, d, r = int(a * SR), int(d * SR), int(r * SR)
    e = np.zeros(n, np.float32)
    i = 0
    seg = min(a, n); e[:seg] = np.linspace(0, 1, seg); i += seg
    seg = min(d, n - i); e[i:i + seg] = np.linspace(1, s, seg); i += seg
    seg = min(hold, n - i); e[i:i + seg] = s; i += seg
    seg = min(r, n - i); e[i:i + seg] = np.linspace(s, 0, seg); i += seg
    return e


def pad_note(f, dur, bright):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n, np.float32)
    for det in (-0.4, 0.0, 0.4):
        ff = f * 2 ** (det / 1200)
        for k, amp in ((1, 1.0), (2, 0.35 * bright), (3, 0.15 * bright), (4, 0.08 * bright)):
            out += amp * np.sin(2 * np.pi * ff * k * t + 0.3 * k) * (1 + 0.03 * np.sin(2 * np.pi * 0.2 * t + k))
    return out * env(n, 1.2, 0.5, 0.8, 1.5, n - int(3.2 * SR)) / 9


def pluck(f, dur=1.6):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n, np.float32)
    for k, amp in ((1, 1.0), (2, 0.5), (3, 0.25), (4, 0.12), (5, 0.06)):
        out += amp * np.sin(2 * np.pi * f * k * t) * np.exp(-t * (2.5 + 1.5 * k))
    return out * env(n, 0.004, 0.1, 0.6, 0.8, n - int(0.9 * SR)) * 0.5


def bell(f, dur=3.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n, np.float32)
    for k, amp in ((1.0, 1.0), (2.76, 0.5), (5.4, 0.25), (8.9, 0.1)):
        out += amp * np.sin(2 * np.pi * f * k * t) * np.exp(-t * (1.2 + 0.8 * k))
    return out * 0.35


def lowpass(x, fc, order=2):
    b, a = butter(order, fc / (SR / 2))
    return lfilter(b, a, x).astype(np.float32)


def bandpass(x, lo, hi):
    b, a = butter(2, [lo / (SR / 2), hi / (SR / 2)], btype='band')
    return lfilter(b, a, x).astype(np.float32)


def add(buf, sig, at, gain=1.0, pan=0.0):
    i = int(at * SR)
    if i >= len(buf) or i < 0:
        return
    seg = sig[:len(buf) - i]
    buf[i:i + len(seg), 0] += seg * gain * (1 - max(0, pan))
    buf[i:i + len(seg), 1] += seg * gain * (1 + min(0, pan))


def music_track(sections, length):
    """sections: list of (start, mood, key, tempo). Returns stereo buffer."""
    buf = np.zeros((int(length * SR) + SR, 2), np.float32)
    rng = np.random.default_rng(1)
    for i, (start, mood, key, tempo) in enumerate(sections):
        end = sections[i + 1][0] if i + 1 < len(sections) else length
        M = MOODS[mood]
        root = 48 + KEYS[key] + 12 * M['octave']
        beat = 60.0 / tempo
        bar = beat * 4
        tt = start
        ci = 0
        while tt < end:
            deg, kind = M['chords'][ci % len(M['chords'])]
            for iv in CHORD[kind]:
                add(buf, pad_note(hz(root + deg + iv), bar + 3.0, M['pad']), tt, 0.22, (iv % 7 - 3) * 0.1)
            add(buf, pad_note(hz(root + deg - 12), bar + 3.0, 0.2), tt, 0.25)
            # plucked melody on scale notes inside the chord's bar
            for b in range(8):
                if rng.random() < M['pluck']:
                    note = root + 12 + deg + M['scale'][int(rng.integers(len(M['scale'])))] + (12 if rng.random() < 0.3 else 0)
                    add(buf, pluck(hz(note)), tt + b * beat / 2, 0.35, rng.random() * 0.8 - 0.4)
            if rng.random() < M['bell']:
                add(buf, bell(hz(root + 24 + deg + CHORD[kind][int(rng.integers(len(CHORD[kind])))])), tt + beat * int(rng.integers(4)), 0.3)
            tt += bar
            ci += 1
        # section fade-in and fade-out over 1.5 s
        a, b = int(start * SR), int(min(end, length) * SR)
        n = min(int(1.5 * SR), (b - a) // 2)
        if i > 0:
            buf[a:a + n] *= np.linspace(0, 1, n)[:, None]
    return buf


def sfx_page_rustle(rng):
    n = int(0.7 * SR)
    x = rng.standard_normal(n).astype(np.float32)
    x = bandpass(x, 1500, 7000)
    e = np.abs(np.sin(np.linspace(0, 9, n))) ** 3 * np.exp(-np.linspace(0, 4, n))
    return x * e * 0.6


def sfx_wind(rng):
    n = int(5.0 * SR)
    x = lowpass(rng.standard_normal(n).astype(np.float32), 600)
    t = np.arange(n) / SR
    e = (0.5 + 0.5 * np.sin(2 * np.pi * 0.25 * t)) * np.sin(np.pi * t / 5.0)
    return x * e * 1.2


def sfx_whoosh(rng):
    n = int(1.4 * SR)
    x = rng.standard_normal(n).astype(np.float32)
    t = np.linspace(0, 1, n)
    out = np.zeros(n, np.float32)
    for k in range(6):
        seg = slice(k * n // 6, (k + 1) * n // 6)
        out[seg] = bandpass(x[seg], 300 + 2500 * (k / 6), 900 + 5000 * (k / 6))
    return out * np.sin(np.pi * t) ** 1.5 * 1.3


def sfx_chime(rng):
    out = np.zeros(int(3 * SR), np.float32)
    for i, m in enumerate((84, 88, 91, 96)):
        s = bell(hz(m), 2.5)
        at = int(i * 0.12 * SR)
        out[at:at + len(s)] += s[:len(out) - at]
    return out * 0.8


def sfx_sparkle(rng):
    out = np.zeros(int(2.5 * SR), np.float32)
    for i in range(18):
        s = bell(hz(int(rng.integers(90, 104))), 0.8) * 0.3
        at = int(rng.random() * 1.8 * SR)
        out[at:at + len(s)] += s[:len(out) - at]
    return out


def sfx_thud(rng):
    n = int(0.5 * SR)
    t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 70 * t * np.exp(-t * 3)) * np.exp(-t * 12) + lowpass(rng.standard_normal(n).astype(np.float32), 300) * np.exp(-t * 25) * 0.5) * 1.2


def sfx_paper_burst(rng):
    n = int(2.5 * SR)
    x = bandpass(rng.standard_normal(n).astype(np.float32), 800, 6000)
    t = np.linspace(0, 1, n)
    flutter = 0.6 + 0.4 * np.sin(2 * np.pi * 14 * t * (1 + t)) * np.sin(2 * np.pi * 3 * t)
    return x * flutter * np.sin(np.pi * t) ** 0.7 * 0.9


def sfx_splash(rng):
    n = int(1.2 * SR)
    t = np.arange(n) / SR
    x = bandpass(rng.standard_normal(n).astype(np.float32), 400, 5000) * np.exp(-t * 4)
    for i in range(10):
        f = 600 + rng.random() * 1500
        at = int(rng.random() * 0.5 * SR)
        drip = np.sin(2 * np.pi * f * (t[:int(0.1 * SR)]) * (1 + 3 * t[:int(0.1 * SR)])) * np.exp(-t[:int(0.1 * SR)] * 40)
        x[at:at + len(drip)] += drip * 0.4
    return x * 1.3


def sfx_clink(rng):
    n = int(0.8 * SR)
    t = np.arange(n) / SR
    out = np.zeros(n, np.float32)
    for f, a in ((2300, 1.0), (3100, 0.6), (5200, 0.3)):
        out += a * np.sin(2 * np.pi * f * t) * np.exp(-t * 18)
    return out * 0.6


def sfx_purr(rng):
    n = int(2.0 * SR)
    t = np.arange(n) / SR
    x = lowpass(rng.standard_normal(n).astype(np.float32), 250)
    return x * (0.5 + 0.5 * np.sin(2 * np.pi * 25 * t)) * np.sin(np.pi * t / 2.0) * 1.5


def sfx_meow(rng):
    n = int(0.6 * SR)
    t = np.arange(n) / SR
    f = 500 + 300 * np.sin(np.pi * t / 0.6) - 150 * t
    ph = np.cumsum(2 * np.pi * f / SR)
    out = sum(np.sin(ph * k) * a for k, a in ((1, 1.0), (2, 0.6), (3, 0.35), (4, 0.2)))
    return out * np.sin(np.pi * t / 0.6) ** 0.5 * 0.5


SFX = {'page_rustle': sfx_page_rustle, 'wind': sfx_wind, 'whoosh': sfx_whoosh, 'chime': sfx_chime, 'sparkle': sfx_sparkle,
       'thud': sfx_thud, 'paper_burst': sfx_paper_burst, 'splash': sfx_splash, 'clink': sfx_clink, 'purr': sfx_purr, 'meow': sfx_meow}


# who=... -> an ElevenLabs voice; lines may carry tags like [excited], [whispering], [laughs]
VOICES = {'narrator': 'VlXLedwkU4YDM3HBGpiI',   # Miron, lively storyteller
          'deep': 'pM78bgjPVk0JXtaEnFoj',       # Nester, deep and serious: mock-epic lines
          'odessa': 'RLRdvNFwJJct2XZOgfzy',     # Mishka, Odessa accent, dry irony
          'gogi': 'XNrB7jz2HCkpU5yK08kP',       # Gogi, Georgian accent, comedy
          'fairy': 'RxivyypsDodFBfmDDOZF',      # Mila, high and sweet
          'calm': 'RD1wW20GjG2W8Fc8vVvm'}       # El, calm and friendly


def voice_key():
    import json
    import os
    try:
        return json.load(open(os.path.expanduser('~/extella-mult/config.json'))).get('elevenlabs_key')
    except Exception:
        return None


def _voice_file(st):
    """The recording for one voice line: a given file, or ElevenLabs speech cached by text and voice."""
    import hashlib
    import json
    import os
    import urllib.request
    if 'file' in st.params:
        return os.path.expanduser(str(st.params['file']))
    vid = VOICES[st.params.get('who', 'narrator')]
    cache = os.path.expanduser('~/extella-mult/assets/voice_cache')
    os.makedirs(cache, exist_ok=True)
    path = os.path.join(cache, hashlib.sha1(f'{vid}|{st.text}'.encode()).hexdigest()[:16] + '.mp3')
    if not os.path.isfile(path):
        req = urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{vid}?output_format=mp3_44100_128',
                                     data=json.dumps({'text': st.text, 'model_id': 'eleven_v3'}).encode(),
                                     headers={'xi-api-key': voice_key(), 'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=120) as r:
            open(path, 'wb').write(r.read())
    return path


def _decode(path):
    import subprocess
    from .config import ffmpeg
    raw = subprocess.run([ffmpeg(), '-v', 'error', '-i', path, '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def render_audio(prog, path):
    length = prog.length
    sections = [(m.at, m.params['mood'], str(m.params.get('key', 'C')), float(m.params.get('tempo', 72))) for m in prog.music]
    buf = music_track(sections, length) if sections else np.zeros((int(length * SR) + SR, 2), np.float32)
    rng = np.random.default_rng(7)
    for s in prog.sfx:
        sig = SFX[s.words[0]](rng)
        add(buf, sig, s.at, float(s.params.get('gain', 1.0)), float(s.params.get('pan', 0.0)))
    voices = getattr(prog, 'voices', [])
    if voices:
        vbuf = np.zeros_like(buf)
        for v in voices:
            add(vbuf, _decode(_voice_file(v)) * 1.4, v.at, float(v.params.get('gain', 1.0)), float(v.params.get('pan', 0.0)))
        env = np.abs(vbuf).max(axis=1)
        k = int(0.25 * SR)  # duck the music under speech, with a soft attack and release
        env = np.convolve((env > 0.02).astype(np.float32), np.ones(k, np.float32) / k, mode='same')
        buf = buf * (1 - 0.65 * np.clip(env * 2, 0, 1))[:, None] + vbuf
    buf = buf[:int(length * SR)]
    # master: soft limiter + end fade
    buf = np.tanh(buf * 1.2) * 0.85
    n = min(int(2.0 * SR), len(buf))
    buf[-n:] *= np.linspace(1, 0, n)[:, None]
    from scipy.io import wavfile
    wavfile.write(path, SR, (buf * 32767).astype(np.int16))
