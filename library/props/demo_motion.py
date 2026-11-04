"""10-second showcase of motion.py on three felt scenes built from the rendered props (run render_props.py first).

    python demo_motion.py            # writes showcase.mp4 (960x540, 25 fps) next to this file
"""
import math
import os
import subprocess
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import motion as M  # noqa: E402

W, H, FPS, SECONDS = 960, 540, 25, 10


def prop(path, height):
    im = Image.open(os.path.join(HERE, 'png', path + '.png')).convert('RGBA')
    return im.resize((max(1, int(im.width * height / im.height)), height), Image.LANCZOS)


def put(layer, im, x, y):
    """Paste a prop with its bottom-centre at (x, y) and a soft contact shadow."""
    a = im.getchannel('A').filter(ImageFilter.GaussianBlur(6)).point(lambda v: int(v * 0.35))
    sh = Image.new('RGBA', im.size, (40, 30, 30, 0))
    sh.putalpha(a)
    layer.alpha_composite(sh, (int(x - im.width / 2 + 6), int(y - im.height + 8)))
    layer.alpha_composite(im, (int(x - im.width / 2), int(y - im.height)))


def gradient(top, bottom):
    g = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    a = np.array(top, np.float32) * (1 - g) + np.array(bottom, np.float32) * g
    return Image.fromarray(np.broadcast_to(a, (H, W, 3)).astype(np.uint8), 'RGB').convert('RGBA')


def ground(img, y, col, wav=0.0):
    d = ImageDraw.Draw(img)
    pts = [(x, y + wav * math.sin(x / 90)) for x in range(0, W + 10, 10)]
    d.polygon(pts + [(W, H), (0, H)], fill=col)


def town():
    back = gradient((159, 208, 238), (226, 240, 246))
    put(back, prop('nature/sun', 140), 800, 190)
    put(back, prop('nature/cloud_puffy', 70), 220, 120)
    put(back, prop('nature/cloud_long', 50), 560, 90)
    ground(back, 360, (185, 214, 150), 10)
    mid = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ground(mid, 430, (143, 190, 110), 6)
    for x, n, h in ((120, 'plants/tree_round', 230), (300, 'city/apartment_block', 250), (480, 'plants/tree_pine', 220),
                    (640, 'city/kiosk', 170), (820, 'plants/tree_autumn', 220)):
        put(mid, prop(n, h), x, 440)
    front = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ground(front, 505, (210, 196, 170))
    for x, n, h in ((180, 'city/street_lamp', 260), (430, 'city/car_sedan', 120), (700, 'city/bench', 100),
                    (60, 'plants/bush_flowering', 90), (900, 'plants/grass_spiky', 70)):
        put(front, prop(n, h), x, 520)
    return [back, mid, front]


def space():
    back = gradient((18, 15, 46), (52, 38, 100))
    d = ImageDraw.Draw(back)
    r = np.random.default_rng(2)
    for _ in range(160):
        x, y, s = r.random() * W, r.random() * H, 0.6 + r.random() * 1.8
        d.ellipse([x - s, y - s, x + s, y + s], fill=(255, 248, 224))
    put(back, prop('tech/planet_ring', 200), 230, 260)
    put(back, prop('nature/moon_crescent', 80), 820, 120)
    mid = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    put(mid, prop('tech/ufo', 150), 760, 330)
    put(mid, prop('tech/satellite', 70), 470, 120)
    front = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    put(front, prop('tech/rocket_flying', 300), 500, 500)
    put(front, prop('nature/stars_cluster', 90), 120, 520)
    return [back, mid, front]


def kitchen():
    back = gradient((242, 226, 200), (232, 214, 186))
    d = ImageDraw.Draw(back)
    for x in range(0, W, 48):
        d.rectangle([x, 0, x + 23, 300], fill=(236, 218, 190))
    put(back, prop('home/window', 220), 300, 280)
    put(back, prop('home/wall_clock', 100), 680, 160)
    mid = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(mid).rectangle([0, 380, W, H], fill=(160, 112, 72))
    put(mid, prop('home/fridge', 300), 860, 420)
    put(mid, prop('plants/potted_plant', 120), 90, 390)
    front = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(front).rounded_rectangle([150, 430, 770, 470], 10, fill=(192, 138, 90))
    put(front, prop('food/plov_kazan', 140), 300, 440)
    put(front, prop('food/teapot', 120), 500, 440)
    put(front, prop('food/piala', 60), 600, 440)
    put(front, prop('food/baursaki', 80), 690, 440)
    return [back, mid, front]


def flat(layers):
    out = layers[0].copy()
    for l in layers[1:]:
        out.alpha_composite(l)
    return out.convert('RGB')


def label(img, text):
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 20) if os.path.exists(
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf') else ImageFont.load_default()
    w = d.textlength(text, font=f)
    d.rounded_rectangle([16, H - 46, 16 + w + 20, H - 16], 8, fill=(30, 30, 34))
    d.text((26, H - 43), text, fill=(250, 248, 240), font=f)
    return img


def main():
    T, S, K = town(), space(), kitchen()
    A, B, Cc = flat(T), flat(S), flat(K)
    # (start, end, label, fn(local_t) -> frame)
    shots = [
        (0.0, 1.5, 'parallax (3 layers)', lambda u: M.parallax(T, u, {'swing': 0.05, 'turns': 0.5})),
        (1.5, 2.5, 'push + handheld', lambda u: M.handheld(M.push(A, u, {'zoom': 1.3, 'cx': 0.45, 'cy': 0.7}), u, {'time': 1.5 + u})),
        (2.5, 3.1, 'whip_pan', lambda u: M.whip_pan(M.push(A, 1, {'zoom': 1.3, 'cx': 0.45, 'cy': 0.7}), B, u)),
        (3.1, 3.9, 'crash_zoom (ease: expo)', lambda u: M.crash_zoom(B, u, {'zoom': 1.9, 'cx': 0.52, 'cy': 0.68})),
        (3.9, 4.5, 'shake with decay', lambda u: M.shake(M.crash_zoom(B, 1, {'zoom': 1.9, 'cx': 0.52, 'cy': 0.68}), u)),
        (4.5, 5.3, 'iris out / in', lambda u: M.iris(M.crash_zoom(B, 1, {'zoom': 1.9, 'cx': 0.52, 'cy': 0.68}), Cc, u,
                                                      {'cx': 0.5, 'cy': 0.5, 'cx2': 0.35, 'cy2': 0.75})),
        (5.3, 6.1, 'dutch_tilt (ease: back)', lambda u: M.dutch_tilt(Cc, u, {'angle': 10, 'ease': 'back'})),
        (6.1, 6.9, 'rack_focus', lambda u: M.rack_focus(M.dutch_tilt(Cc, 1, {'angle': 10}), u, {'blur': 7})),
        (6.9, 7.5, 'wipe_right', lambda u: M.wipe_right(M.dutch_tilt(Cc, 1, {'angle': 10}), A, u)),
        (7.5, 8.2, 'pan (ease: elastic)', lambda u: M.pan(A, u, {'zoom': 1.4, 'x0': 0.36, 'x1': 0.64, 'y0': 0.6, 'y1': 0.6, 'ease': 'elastic'})),
        (8.2, 8.8, 'page_turn', lambda u: M.page_turn(M.pan(A, 1, {'zoom': 1.4, 'x0': 0.36, 'x1': 0.64, 'y0': 0.6, 'y1': 0.6}), B, u)),
        (8.8, 9.4, 'slowmo_hold + cross_dissolve', lambda u: M.cross_dissolve(
            M.slowmo_hold(lambda st: M.parallax(S, st, {'swing': 0.08, 'turns': 0.25}), u, {'start': 0.2, 'length': 0.5}), Cc, max(0, u - 0.6) / 0.4)),
        (9.4, 10.0, 'dip_to_black', lambda u: M.dip_to_black(Cc, Image.new('RGB', (W, H)), u)),
    ]
    out = os.path.join(HERE, 'showcase.mp4')
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H),
                           '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', out], stdin=subprocess.PIPE)
    for f in range(FPS * SECONDS):
        tt = f / FPS
        for a, b, name, fn in shots:
            if a <= tt < b or (b == SECONDS and tt >= a):
                img = label(fn((tt - a) / (b - a)).convert('RGB'), name)
                break
        ff.stdin.write(img.tobytes())
    ff.stdin.close()
    ff.wait()
    print('wrote', out)


if __name__ == '__main__':
    main()
