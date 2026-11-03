"""Device paths written by the installer into ~/extella-mult/config.json (python, ffmpeg, blender)."""
import json, os, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_C = {}
try:
    _C = json.load(open(os.path.join(ROOT, 'config.json')))
except Exception:
    pass


def ffmpeg():
    p = os.environ.get('FFMPEG') or _C.get('ffmpeg')
    if p and os.path.exists(p):
        return p
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return shutil.which('ffmpeg') or os.path.expanduser('~/.local/bin/ffmpeg')


def blender():
    return os.environ.get('BLENDER') or _C.get('blender') or '/Applications/Blender.app/Contents/MacOS/Blender'
