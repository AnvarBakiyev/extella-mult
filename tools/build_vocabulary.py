"""Builds the agent's vocabulary from library/ (this repository) and, when they are installed, from the built packs in
~/extella-mult/assets/lib/mult: the lists of picture sets, code characters, full bodies, places, props, effects,
sounds and music the agent may use, plus the PUPPET language page. Writes agent/concepts.json.
python3 tools/build_vocabulary.py [--lib ~/extella-mult/assets/lib/mult]"""
import glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
LIB = os.path.join(REPO, 'library')
BUILT = os.path.expanduser(sys.argv[sys.argv.index('--lib') + 1] if '--lib' in sys.argv else '~/extella-mult/assets/lib/mult')
LIMIT = 6000  # a few large concepts: one search brings a whole topic, the agent finishes inside the platform's run limit

LANG = ("PUPPET v2 language. First line: film title=\"...\" style=puppet fps=24 size=1920x1080 (add voices=off for a film with subtitles instead of recorded voices; look=warm is the default lamp light, look=none switches it off). "
        "cast <char> on <plate> at x,y size=0.62 facing=left|right mood=neutral|happy|angry|shocked as=<stage>: puts a code character on a plate; several cast lines on one plate make one stage with several people; as= names a second staging (a close-up: size=0.92 at 0.5,0.47). "
        "shot A-Bs: <set|plate|stage> + camera (push pull pan focus snap handheld dutch whip shake); shots touch. "
        "say <char|set> \"line\" at Xs mood=... [file=recording]: only the speaker's mouth moves, the others blink; a char must be cast on the shot's plate, a set must be the shot. voice \"[deep] ...\" at Xs: off screen. "
        "prop <name> at x,y size= A-Bs; prop <name> in=<char>.hand; act <char> holding <prop> A-Bs; fx <effect> A-Bs at x,y; sfx <name> at Xs gain=0.6; music file=<name> A-Bs gain=0.4; "
        "cut <wipe|iris|dissolve|whip|dip|dip_white|page|slide> at Xs (on a shot boundary); text \"...\" at x,y size=0.05 font=ptsans|oswald|caveat color=#fff halo=0.8 A-Bs; fade in/out A-Bs. "
        "Full body: cast <char> on <plate> at x,y body=full size=0.7 facing=right as=<stage> puts the whole puppet with its feet at x,y (y about 0.95); "
        "act <char> <move> A-Bs [to=x] makes it move: walk/run with to=x cross the stage, wave point shrug facepalm arms_crossed hands_on_hips typing holding_phone thinking sit jump fall bow dance nod head_shake laugh; between acts it breathes. Use full bodies for wide shots with action, busts for close-ups of talk. "
        "Keep full bodies at least 0.12 apart at every moment. One time range per line: fade, act and text go on lines of their own, never on the shot line. "
        "With voices=off write each line also as a subtitle: text \"— line\" at 0.5,0.9 size=0.05 font=ptsans color=#ffffff halo=0.8 over the same seconds. About 6 syllables a second.")

SETS = ("PUPPET picture sets (generated felt pictures, a whole shot each; not code characters, never write cast lines for them). "
        "A set is used directly as the shot: 'shot 0-5s: devil_hr push=0.05'. Talking sets move their mouth and blink with say <set> \"line\" at Xs while that set is the shot; "
        "a recorded line is attached with file=<path>. Silent sets are cutaways and places: show them and put lines over them as voice or text. ")


def chunks(title, items, sep=' | '):
    out, cur = [], ''
    for it in items:
        if len(cur) + len(it) + len(sep) > LIMIT - len(title) - 20:
            out.append(cur); cur = ''
        cur += (sep if cur else '') + it
    if cur:
        out.append(cur)
    return [f'{title} ({k + 1}/{len(out)}): {c}' for k, c in enumerate(out)]


def sets():
    talk, silent = [], []
    for d in sorted(glob.glob(os.path.join(LIB, 'sets', '*', 'set.json'))):
        n = os.path.basename(os.path.dirname(d))
        j = json.load(open(d, encoding='utf-8'))
        talks = j.get('talks') or os.path.isfile(os.path.join(os.path.dirname(d), 'open.png'))
        blink = os.path.isfile(os.path.join(os.path.dirname(d), 'blink.png'))
        (talk if talks else silent).append(f"{n}{'' if blink else ' (no blink)'}: {j.get('about', '')[:70]}")
    return [SETS + 'Talking sets: ' + ' | '.join(talk) + ' || Silent sets: ' + ' | '.join(silent)]


def pages(nums):
    d = os.path.join(LIB, 'knowledge', 'concepts')
    out = []
    for f in sorted(glob.glob(os.path.join(d, '*.md'))):
        if os.path.basename(f)[:2] in nums:
            out.append(open(f, encoding='utf-8').read().strip().lstrip('# ').replace('\n', ' '))
    return ' || '.join(out)


def main():
    C = [f'PUPPET language and camera: {LANG} || ' + pages(['03', '07', '08']),
         'PUPPET workflow, check errors, safety: ' + pages(['01', '13', '14', '12', '24']),
         'PUPPET dialogue timing, music, skeleton, voices: ' + pages(['05', '06', '15', '04']),
         'PUPPET jokes: ' + pages(['09', '10', '11']),
         'PUPPET formats F01-F12: ' + pages(['16', '17', '18', '19']),
         'PUPPET formats F13-F25: ' + pages(['20', '21', '22', '23'])]
    C += sets()
    chars = []
    for d in sorted(glob.glob(os.path.join(LIB, 'chars', 'chars', '*', 'char.json'))):
        j = json.load(open(d, encoding='utf-8'))
        chars.append(f"{j['name']}: {j.get('about', '')[:40]}")
    C += chunks('PUPPET code characters (use with cast)', chars)
    bodies = sorted(os.path.basename(os.path.dirname(p)) for p in glob.glob(os.path.join(BUILT, 'puppet-characters-body-felt3', 'body', '*', 'rig.json')))
    if bodies:
        C += chunks('PUPPET full-body characters (cast ... body=full; other characters are busts only)', bodies, ', ')
    places = sorted({os.path.basename(p).split('-v')[0] for p in glob.glob(os.path.join(BUILT, 'puppet-plates-code', 'plates', '*'))})
    if places:
        C += chunks('PUPPET plates (use the place name, e.g. tv_studio, or a full variant like tv_studio-v1-night-clear)', places, ', ')
    props = sorted(os.path.basename(p)[:-4] for p in glob.glob(os.path.join(BUILT, 'puppet-procedural', 'png', '*', '*.png')))
    if props:
        C += chunks('PUPPET props (prop <name>)', props, ', ')
    fx = sorted(os.path.basename(p) for p in glob.glob(os.path.join(BUILT, 'puppet-effects-code', 'seq', '*')))
    if fx:
        C += chunks('PUPPET effects (fx <name>)', fx, ', ')
    sfx = sorted({os.path.basename(p).rsplit('.', 1)[0] for p in glob.glob(os.path.join(LIB, 'media', 'sfx', '*'))})
    C += chunks('PUPPET sounds (sfx <name>)', sfx, ', ')
    mus = sorted({os.path.basename(p).rsplit('.', 1)[0] for p in glob.glob(os.path.join(LIB, 'media', 'music', '*'))})
    C += chunks('PUPPET music (music file=<name>)', mus, ', ')
    os.makedirs(os.path.join(REPO, 'agent'), exist_ok=True)
    json.dump(C, open(os.path.join(REPO, 'agent', 'concepts.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print(len(C), 'concepts', sum(map(len, C)), 'chars ->', 'agent/concepts.json',
          '' if bodies else '(built packs not installed: bodies, plates, props, effects are left out)')


if __name__ == '__main__':
    main()
