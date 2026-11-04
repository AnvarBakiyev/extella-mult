"""Re-render characters and check that base + overlay equals the full frame for every overlay.

    python3 check_overlays.py [names...]   (default: 12 spread over the cast)
"""
import sys

import numpy as np

import charlib as L
from characters import CAST

if __name__ == '__main__':
    spec = {s['name']: s for s in CAST}
    names = sys.argv[1:] or [s['name'] for s in CAST][::13]
    worst = 0
    for n in names:
        c, out, full = L.render_all(spec[n])
        d = max(int(np.abs(np.asarray(L.compose(out['base'], out[k]), np.int16) - np.asarray(full[k], np.int16)).max())
                for k in out if k != 'base')
        worst = max(worst, d)
        print(n, 'max diff', d, flush=True)
    print('worst', worst)
