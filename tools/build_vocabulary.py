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
        "prop <name> at x,y size= A-Bs (lies or hangs in the shot); prop <name> in=<char>.hand size=0.12 A-Bs (a full-body puppet holds it); fx <effect> A-Bs at x,y; sfx <name> at Xs gain=0.6; music file=<name> A-Bs gain=0.4; "
        "cut <wipe|iris|dissolve|whip|dip|dip_white|page|slide> at Xs (on a shot boundary); text \"...\" at x,y size=0.05 font=ptsans|oswald|caveat color=#fff halo=0.8 A-Bs; fade in/out A-Bs. "
        "Full body: cast <char> on <plate> at x,y body=full size=0.62 facing=right as=<stage> puts the whole puppet with its feet at x,y (y 0.88); "
        "act <char> <move> A-Bs [to=x] makes it move (search \"PUPPET full-body characters and moves\"). "
        "One time range per line: fade, act and text go on lines of their own, never on the shot line. "
        "With voices=off write each line also as a subtitle: text \"— line\" at 0.5,0.95 size=0.045 font=ptsans color=#ffffff halo=0.8 over the same seconds, without the [tags] ([deadpan] goes on say, never into text). About 6 syllables a second.")

SETS = ("PUPPET picture sets (generated felt pictures, a whole shot each; not code characters, never write cast lines for them). "
        "A set is used directly as the shot: 'shot 0-5s: devil_hr push=0.05'. Talking sets move their mouth and blink with say <set> \"line\" at Xs while that set is the shot; "
        "a recorded line is attached with file=<path>. Silent sets are cutaways and places: show them and put lines over them as voice or text. ")

BODY = ("PUPPET full-body characters and moves. This is how an episode looks like a cartoon and not a slide show: "
        "whole felt puppets that walk in, gesture while they talk and react. Default for every episode unless the person asks for picture sets. "
        "Cast: cast <char> on <plate> at x,y body=full size=0.62 facing=right|left as=<stage>; x,y is where the feet stand, y=0.88; x from 0.1 to 0.9; "
        "size 0.55-0.65 for one or two puppets in a wide shot. A stage (as=) is one plate with its puppets; everyone cast on a stage is on screen in every shot of it, "
        "so make a second stage (as=<name>2, cast the same characters again) for the part where someone has not arrived yet. "
        "Close-ups: the same stage with push=0.1-0.14 focus=<speaker x>,0.5; no separate bust needed. "
        "Moves: act <char> <move> A-Bs. Travel: walk or run with to=x (to= is where it ends; facing turns by itself; 1.5-2.5 s per 0.3 of the frame). "
        "Gestures (hold for the range): wave point shrug facepalm arms_crossed hands_on_hips thinking typing holding_phone sit bow. "
        "One-off: jump fall dance. Loops: nod head_shake laugh idle. Between acts the puppet breathes (idle). "
        "Objects: whatever a character brings, gives, shows or eats is held, never floating: prop pizza in=sasha_courier.hand 0-6s; to hand it over, end the giver's range at the second the taker's starts (prop pizza in=oleg_petrovich.hand 6-12s); size 0.08-0.14. "
        "Rules: at least one act in EVERY shot; the speaker gestures on their line (point to explain, shrug to admit, facepalm for disbelief, arms_crossed or hands_on_hips to judge, "
        "thinking for a pause), the listener reacts (nod, head_shake, laugh) a beat later; an entrance is a walk or run from x=1.0 or 0.0; the turn line gets one strong move (fall, jump, facepalm). "
        "Keep full bodies at least 0.12 apart at every moment, also at the end of a walk (to= of one and x of the other). "
        "Subtitles over bodies at 0.5,0.95 size=0.045 so they do not cover the legs. "
        "Example: cast farmer_bear on river at 0.15,0.88 body=full size=0.62 facing=right as=bank || "
        "cast farmer_bear on river at 0.4,0.88 body=full size=0.62 facing=right as=bank2 || cast sasha_courier on river at 1.0,0.88 body=full size=0.58 facing=left as=bank2 || "
        "shot 0-5s: bank push=0.03 || act farmer_bear walk 0.5-4.5s to=0.4 || shot 5-9s: bank push=0.08 focus=0.4,0.55 || act farmer_bear thinking 5.3-8.7s || "
        "shot 9-13s: bank push=0.12 focus=0.4,0.5 || say farmer_bear \"Раньше лосось сам шёл в руки.\" at 9.3s || act farmer_bear point 9.3-12s || "
        "shot 24-28s: bank2 push=0.02 || act sasha_courier run 24-26.5s to=0.68 || act farmer_bear wave 25.5-27.5s || "
        "shot 28-33s: bank2 push=0.1 focus=0.5,0.5 snap=28.3 || say farmer_bear \"[deadpan] Перешёл на доставку.\" at 28.3s || act farmer_bear nod 28.5-31s || act sasha_courier bow 29-31.5s. ")


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
            out.append(open(f, encoding='utf-8').read().strip().lstrip('# '))
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
        about = {c.split(':')[0]: c for c in chars}
        C += chunks(BODY + 'Characters with a full body (others are busts only)', [about.get(b, b) for b in bodies])
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
