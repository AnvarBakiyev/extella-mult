"""Quick look: a grid of frames of one or more effects over the felt background (for development)."""
import sys, time
from PIL import Image
import effects_lib as E
from feltcore import felt_background

def peek(names, ts=(0.2, 0.45, 0.7), out='peek.jpg', W=960, H=540):
    bg = felt_background(W, H).convert('RGBA')
    sheet = Image.new('RGB', (W * len(ts), H * len(names)))
    for j, n in enumerate(names):
        D = E.EFFECTS[n]['dur']
        t0 = time.time()
        for i, f in enumerate(ts):
            im = bg.copy()
            im.alpha_composite(E.render(n, f * D, {'W': W, 'H': H}))
            sheet.paste(im.convert('RGB'), (i * W, j * H))
        print(n, '%.2fs/frame' % ((time.time() - t0) / len(ts)))
    sheet.save(out, quality=85)

if __name__ == '__main__':
    peek(sys.argv[2:], out=sys.argv[1])
