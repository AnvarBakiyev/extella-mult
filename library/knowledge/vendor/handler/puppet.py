"""style=puppet: a felt puppet shot built from a few still pictures of the same frame (generated once):
base (mouth closed), mouth open, eyes closed. Only the region where a variant differs from the base is pasted in,
with a soft mask, so the rest of the picture never flickers. The mouth follows the loudness of the voice,
the eyes blink every few seconds, the camera pushes in slowly."""
import math
import subprocess

import numpy as np
from PIL import Image, ImageFilter

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



def mouth_track(wav, fps, n):
    """Per frame: 0 closed, 1 open, from the voice loudness with a little hysteresis."""
    raw = subprocess.run([ffmpeg(), '-v', 'error', '-i', wav, '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'], capture_output=True, check=True).stdout
    s = np.frombuffer(raw, np.float32)
    hop = SR // fps
    rms = np.array([np.sqrt(np.mean(s[i * hop:(i + 1) * hop] ** 2)) if i * hop < len(s) else 0 for i in range(n)])
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
# style=puppet: the language
# film title="Лосось" style=puppet fps=24 size=1920x1080
# music mood=tense key=D tempo=80
# shot 0-6s: salmon_studio push=0.05 pan=right
# say salmon_studio "[tired] Чтобы оставить потомство." at 0.4s who=odessa
# voice "Тысячи километров." at 12s who=deep
# text "РЕКЛАМА" at 0.5,0.15 size=0.1 color=#ffffff 30-33s
# fade in 0-0.6s / fade out 50-51s
import json
import os
import re
import shlex

SETS = os.path.expanduser('~/extella-mult/assets/puppet')
PROPS = os.path.expanduser('~/extella-mult/assets/props')


def props_list():
    out = {}
    for root, _, files in os.walk(PROPS) if os.path.isdir(PROPS) else []:
        for f in files:
            if f.endswith('.png'):
                out[f[:-4]] = os.path.join(root, f)
    return out
PANS = {'left': (-1, 0), 'right': (1, 0), 'up': (0, -1), 'down': (0, 1), 'none': (0, 0)}


_PROP_CACHE = {}


class PuppetError(Exception):
    pass


def sets_list():
    return sorted(d for d in os.listdir(SETS) if os.path.isfile(os.path.join(SETS, d, 'base.png'))) if os.path.isdir(SETS) else []


def set_info(name):
    p = os.path.join(SETS, name, 'set.json')
    return json.load(open(p)) if os.path.isfile(p) else {}


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


def parse_puppet(src):
    """Parse and check a puppet film; errors say what to fix, with the line number."""
    from .audio import VOICES
    film, shots, says, texts, fades, music, missing = {}, [], [], [], [], [], []
    for n, raw in enumerate(src.splitlines(), 1):
        line = raw.split('#', 1)[0].strip() if not re.search(r'"[^"]*#', raw) else raw.strip()
        if not line:
            continue
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
                L.t0, L.t1 = float(m.group(1)), float(m.group(2))
            elif re.fullmatch(r'\d+(?:\.\d+)?s', t) and L.words and L.words[-1] == 'at':
                L.words.pop()
                L.at = float(t[:-1])
            elif re.fullmatch(r'-?\d*\.?\d+,-?\d*\.?\d+', t) and L.words and L.words[-1] == 'at':
                L.words.pop()
                L.pos = tuple(float(x) for x in t.split(','))
            elif '=' in t and not t.startswith('['):
                k, v = t.split('=', 1)
                L.params[k] = _num(v)
            elif t == ':':
                continue
            elif L.text is None and t != 'at' and ((head == 'say' and L.words) or head in ('voice', 'text')):
                L.text = t  # the words in quotes: after the set name for say, first for voice and text
            else:
                L.words.append(t)
        if head == 'film':
            film = L.params
        elif head == 'shot':
            if L.t0 is None:
                raise PuppetError(f"line {n}: a shot needs its time: shot 0-6s: salmon_studio")
            if not L.words:
                raise PuppetError(f"line {n}: which set does the shot show? sets: {', '.join(sets_list())}")
            name = L.words[0]
            if name not in sets_list():
                raise PuppetError(f"line {n}: no set '{name}' on this device; sets: {', '.join(sets_list())}")
            if str(L.params.get('pan', 'none')) not in PANS:
                raise PuppetError(f"line {n}: pan must be one of {', '.join(PANS)}")
            shots.append(L)
        elif head in ('say', 'voice'):
            if head == 'say':
                if not L.words or L.words[0] not in sets_list():
                    raise PuppetError(f"line {n}: say needs the set whose mouth moves: say salmon_studio \"...\" at 1s who=odessa; sets: {', '.join(sets_list())}")
                if not os.path.isfile(os.path.join(SETS, L.words[0], 'open.png')):
                    raise PuppetError(f"line {n}: set {L.words[0]} has no talking mouth (open.png); use voice for an off-screen line")
            # the voice: who=..., else the set's own voice (say); off screen: a leading [voice] tag, else the deep narrator
            if L.text and 'who' not in L.params and head == 'voice':
                m = re.match(r'\s*\[([a-z_]+)\]\s*', L.text)
                if m and m.group(1) in VOICES:
                    L.params['who'] = m.group(1)
                    L.text = L.text[m.end():]
            if L.text and 'who' not in L.params:
                L.params['who'] = set_info(L.words[0]).get('voice', 'narrator') if head == 'say' else 'deep'
            if L.at is None:
                raise PuppetError(f"line {n}: {head} needs a start time: ... at 2s")
            if 'file' in L.params:
                if not os.path.isfile(os.path.expanduser(str(L.params['file']))):
                    raise PuppetError(f"line {n}: file {L.params['file']} not found")
            elif not L.text:
                raise PuppetError(f'line {n}: the words go in quotes: {head} ... "Привет!" at 2s who=narrator')
            else:
                from .audio import voice_key, voice_cache_path
                who = str(L.params.get('who', 'narrator'))
                if who not in VOICES:
                    raise PuppetError(f"line {n}: unknown voice who={who}; voices: {', '.join(VOICES)}")
                if not os.path.isfile(voice_cache_path(who, L.text)) and not voice_key():
                    missing.append({'line': n, 'who': who, 'text': L.text, 'file': voice_cache_path(who, L.text)})
            says.append(L)
        elif head == 'text':
            if L.t0 is None or not L.text:
                raise PuppetError(f'line {n}: text "..." at 0.5,0.2 size=0.08 color=#ffffff 3-6s')
            texts.append(L)
        elif head == 'prop':  # prop coffee_cup at 0.7,0.8 size=0.15 12-18s: a felt cut-out placed over the shot
            if not L.words or L.words[0] not in props_list():
                raise PuppetError(f"line {n}: no prop '{L.words[0] if L.words else ''}' on this device; search the concepts for PUPPET props")
            if L.t0 is None:
                raise PuppetError(f"line {n}: a prop needs its time: prop {L.words[0]} at 0.7,0.8 size=0.15 12-18s")
            texts.append(L)
        elif head == 'fade':
            if not L.words or L.words[0] not in ('in', 'out') or L.t0 is None:
                raise PuppetError(f"line {n}: fade in 0-1s or fade out 40-41s")
            fades.append(L)
        elif head == 'music':
            music.append(L)
        else:
            raise PuppetError(f"line {n}: '{head}' is not a statement; statements: film, shot, say, voice, text, prop, fade, music")
    if not shots:
        raise PuppetError('no shots: add shot 0-6s: <set>')
    if missing:
        raise PuppetError(f"{len(missing)} spoken line(s) are not recorded yet and this device has no ElevenLabs key. "
                          "Show the person the lines below; they record them with their own ElevenLabs and the film renders after that. "
                          "LINES_TO_RECORD " + json.dumps(missing, ensure_ascii=False))
    shots.sort(key=lambda s: s.t0)
    # recorded lines have a real length: a line must end inside its shot and before the next line starts
    from .audio import voice_cache_path
    timed = []
    for L in says:
        path = os.path.expanduser(str(L.params['file'])) if 'file' in L.params else voice_cache_path(str(L.params.get('who', 'narrator')), L.text)
        if os.path.isfile(path):
            r = subprocess.run([ffmpeg(), '-i', path], capture_output=True, text=True).stderr
            m = re.search(r'Duration: (\d+):(\d+):([\d.]+)', r)
            if m:
                timed.append((L, int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))))
    problems = []
    timed.sort(key=lambda x: x[0].at)
    for i, (L, d) in enumerate(timed):
        end = L.at + d
        sh = next((x for x in shots if x.t0 <= L.at < x.t1), None)
        if L.kind == 'say' and sh is not None and end > sh.t1 + 0.25:
            problems.append(f"line {L.n}: the recording lasts {d:.1f}s, so it ends at {end:.1f}s but its shot ends at {sh.t1:g}s")
        if i + 1 < len(timed) and end > timed[i + 1][0].at + 0.1:
            problems.append(f"line {L.n} ends at {end:.1f}s and overlaps line {timed[i + 1][0].n} that starts at {timed[i + 1][0].at:g}s")
    if problems:
        raise PuppetError('the recorded lines do not fit the timing. Lengths: ' + '; '.join(f"line {L.n} {d:.1f}s" for L, d in timed)
                          + '. Problems: ' + '; '.join(problems) + '. Re-time the shots and the at= times to the real lengths '
                          '(start each line 0.3s after its shot begins, end the shot 0.4s after the line ends, shift everything after); do not change the words.')
    if shots[0].t0 != 0:
        raise PuppetError(f'line {shots[0].n}: the first shot must start at 0s')
    for a, b in zip(shots, shots[1:]):
        if abs(a.t1 - b.t0) > 1e-6:
            raise PuppetError(f'line {b.n}: shots must touch: the previous one ends at {a.t1:g}s, this one starts at {b.t0:g}s')
    length = shots[-1].t1
    for L in says + texts + fades:
        t = L.at if L.at is not None else L.t0
        if t < 0 or t >= length:
            raise PuppetError(f'line {L.n}: {L.kind} at {t:g}s is outside the film (0-{length:g}s)')
    size = tuple(int(x) for x in str(film.get('size', '1920x1080')).split('x'))
    return dict(title=str(film.get('title', '')), fps=int(film.get('fps', 24)), size=size, length=length,
                shots=shots, says=says, texts=texts, fades=fades, music=music)


def _say_file(L):
    from .audio import _voice_file

    class S:
        pass
    s = S()
    s.params, s.text = L.params, L.text
    return _voice_file(s)


def render_puppet(prog, out, preview=False):
    from .audio import _decode, music_track, SR as ASR
    W, H = prog['size']
    if preview:
        W, H = W // 2 // 2 * 2, H // 2 // 2 * 2
    fps = prog['fps']
    n = int(round(prog['length'] * fps))
    sets = {}
    for sh in prog['shots']:
        name = sh.words[0]
        if name not in sets:
            d = os.path.join(SETS, name)
            base = _load(os.path.join(d, 'base.png'), (W, H))
            parts = {}
            for k in ('open', 'mid', 'blink'):
                p = os.path.join(d, k + '.png')
                if os.path.isfile(p):
                    v = _load(p, (W, H))
                    parts[k] = (v, diff_mask(base, v))
            sets[name] = (base, parts)
    # mouths and the sound track
    mouth = {name: np.zeros(n, np.int8) for name in sets}
    buf = np.zeros((int(prog['length'] * ASR) + ASR, 2), np.float32)
    for m in prog['music']:  # music plays over its own range: music mood=bright 35-43s (or from at= to the end)
        a = m.t0 if m.t0 is not None else (m.at or 0)
        b = m.t1 if m.t1 is not None else prog['length']
        tr = music_track([(0, m.params.get('mood', 'calm'), str(m.params.get('key', 'C')), float(m.params.get('tempo', 72)))], b - a)
        tr = tr[:int((b - a) * ASR)] * float(m.params.get('gain', 0.6))
        f = min(len(tr), int(0.3 * ASR))
        tr[:f] *= np.linspace(0, 1, f)[:, None]
        tr[-f:] *= np.linspace(1, 0, f)[:, None]
        i = int(a * ASR)
        buf[i:i + len(tr)] += tr[:len(buf) - i]
    vbuf = np.zeros_like(buf)
    for L in prog['says']:
        path = _say_file(L)
        sig = _decode(path) * float(L.params.get('gain', 1.0)) * 1.4
        i = int(L.at * ASR)
        seg = sig[:max(0, len(vbuf) - i)]
        vbuf[i:i + len(seg)] += seg[:, None]
        if L.kind == 'say':
            f0 = int(L.at * fps)
            tr = mouth_track(path, fps, int(len(sig) / ASR * fps) + 1)
            for k, o in enumerate(tr):
                if f0 + k < n:
                    mouth[L.words[0]][f0 + k] = max(mouth[L.words[0]][f0 + k], o)
    env = np.abs(vbuf).max(axis=1)
    k = int(0.25 * ASR)
    env = np.convolve((env > 0.02).astype(np.float32), np.ones(k, np.float32) / k, mode='same')
    buf = buf * (1 - 0.7 * np.clip(env * 2, 0, 1))[:, None] + vbuf
    buf = np.tanh(buf[:int(prog['length'] * ASR)] * 1.1) * 0.9
    from scipy.io import wavfile
    wav = out + '.wav'
    wavfile.write(wav, ASR, (buf * 32767).astype(np.int16))
    from PIL import ImageDraw, ImageFont
    font_p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'fonts', 'Caveat.ttf')
    proc = subprocess.Popen([ffmpeg(), '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(fps), '-i', '-',
                             '-i', wav, '-map', '0:v', '-map', '1:a', '-c:a', 'aac', '-b:a', '160k', '-t', str(prog['length']),
                             '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '19', out], stdin=subprocess.PIPE)
    for i in range(n):
        t = i / fps
        sh = next((s for s in prog['shots'] if s.t0 <= t < s.t1), prog['shots'][-1])
        name = sh.words[0]
        base, parts = sets[name]
        img = base
        m = mouth[name][i]
        if m:
            k = 'mid' if (m == 1 and 'mid' in parts) else 'open'
            if k in parts:
                img = Image.composite(parts[k][0], img, parts[k][1])
        tl = t - sh.t0
        if 'blink' in parts and not mouth[name][i] and ((tl + 1.1) % 3.7) < 0.13:
            img = Image.composite(parts['blink'][0], img, parts['blink'][1])
        # camera: push in / pull out, pan, snap zoom, handheld wander, dutch tilt, whip in, shake; all eased
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
        cw, ch = W / z, H / z
        fx, fy = (float(v) for v in str(P.get('focus', '0.5,0.45')).split(','))
        if P.get('handheld'):  # slow uneven wander, like a camera held by hand
            fx += 0.006 * (math.sin(t * 1.3) + 0.6 * math.sin(t * 2.9 + 1))
            fy += 0.005 * (math.sin(t * 1.7 + 2) + 0.5 * math.sin(t * 3.7))
            z = max(z, 1.04)
            cw, ch = W / z, H / z
        x0 = min(max(fx * W - cw / 2 + dx * (W - cw) * (e - 0.5), 0), W - cw)
        y0 = min(max(fy * H - ch / 2 + dy * (H - ch) * (e - 0.5), 0), H - ch)
        img = img.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))
        if 'dutch' in P:  # a tilted horizon for unease; zoomed a little so the corners stay filled
            a = float(P['dutch'])
            img = img.rotate(a, Image.BICUBIC, expand=False).resize((int(W * 1.12), int(H * 1.12)), Image.BICUBIC)
            img = img.crop(((img.width - W) // 2, (img.height - H) // 2, (img.width - W) // 2 + W, (img.height - H) // 2 + H))
        if 'whip' in P and tl < 0.35:  # the shot slides in fast from one side with motion blur
            k = 1 - tl / 0.35
            off = int((1 if str(P['whip']) == 'left' else -1) * W * 0.6 * k * k)
            bl = img.filter(ImageFilter.BoxBlur(int(30 * k) + 1))
            moved = bl.transform((W, H), Image.AFFINE, (1, 0, off, 0, 1, 0), Image.BICUBIC, fillcolor=None)
            back = bl.transform((W, H), Image.AFFINE, (1, 0, off - (W if off > 0 else -W), 0, 1, 0), Image.BICUBIC)
            img = Image.composite(moved, back, moved.convert('L').point(lambda v: 255 if v > 0 else 0))
        if 'shake' in P:
            a = float(P['shake']) * W
            img = img.transform((W, H), Image.AFFINE, (1, 0, a * math.sin(t * 37), 0, 1, a * math.cos(t * 29)), Image.BICUBIC)
        for L in prog['texts']:
            if L.kind == 'prop' and L.t0 <= t < L.t1:
                key = (L.words[0], float(L.params.get('size', 0.15)))
                if key not in _PROP_CACHE:
                    im = Image.open(props_list()[L.words[0]]).convert('RGBA')
                    hgt = int(key[1] * H)
                    im = im.crop(im.getbbox() or (0, 0, im.width, im.height))
                    im = im.resize((max(1, int(im.width * hgt / im.height)), hgt), Image.LANCZOS)
                    sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
                    sh.putalpha(im.getchannel('A').point(lambda v: int(v * 0.35)).filter(ImageFilter.GaussianBlur(hgt * 0.03)))
                    _PROP_CACHE[key] = (im, sh)
                im, shd = _PROP_CACHE[key]
                x, y = L.pos or (0.5, 0.8)
                bob = float(L.params.get('bob', 0)) * H * math.sin(t * 3)  # bob=0.01 makes it float gently
                px, py = int(x * W - im.width / 2), int(y * H - im.height + bob)
                img = img.convert('RGBA')
                img.alpha_composite(shd, (px + int(im.height * 0.03), py + int(im.height * 0.04)))
                img.alpha_composite(im, (px, py))
                img = img.convert('RGB')
                continue
            if L.t0 <= t < L.t1:
                d = ImageDraw.Draw(img)
                px = int(float(L.params.get('size', 0.08)) * H * 1.25)
                fnt = ImageFont.truetype(font_p, px)
                x, y = L.pos or (0.5, 0.2)
                bb = d.textbbox((0, 0), L.text, font=fnt)
                tx, ty = x * W - (bb[2] - bb[0]) / 2, y * H - (bb[3] - bb[1]) / 2
                glow = Image.new('L', (W, H), 0)
                ImageDraw.Draw(glow).text((tx, ty + px * 0.04), L.text, font=fnt, fill=255)
                glow = glow.filter(ImageFilter.GaussianBlur(px * 0.12))
                halo = str(L.params.get('glow', '#000000'))  # a soft halo instead of a hard shadow: glow=#ffffff on dark text
                img = Image.composite(Image.new('RGB', (W, H), halo), img, glow.point(lambda v: int(v * float(L.params.get('halo', 0.55)))))
                d = ImageDraw.Draw(img)
                d.text((tx, ty), L.text, font=fnt, fill=str(L.params.get('color', '#ffffff')))
        dark = 0.0
        for L in prog['fades']:
            if L.t0 <= t <= L.t1:
                f = (t - L.t0) / max(1e-6, L.t1 - L.t0)
                dark = max(dark, 1 - f if L.words[0] == 'in' else f)
            elif L.words[0] == 'out' and t > L.t1:
                dark = 1.0
        if dark > 0:
            img = Image.fromarray((np.asarray(img, np.float32) * (1 - dark)).astype(np.uint8))
        proc.stdin.write(img.tobytes())
    proc.stdin.close()
    proc.wait()
    os.remove(wav)


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
