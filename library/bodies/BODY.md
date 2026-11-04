# Full-body felt puppets (2D rig)

The 153 bust characters, now with bodies that move. Same parts, palettes and felt filter as the busts
(`charlib.py`, Pillow primitives + `felt`), no image generation, no paid services.

```
python3 body_build.py rigs     # body/<name>/rig.json + part PNGs, body/_props   (~8 min for 153 on 4 cores)
python3 body_build.py base     # body/<name>/full_q34.png + body/body.json
python3 body_build.py sheets   # body_sheets/<name>.jpg   (30 demo characters: every pose and cycle, both views)
python3 body_build.py demo     # body_demo/<name>.mp4     (30 demo characters, 20 s: walk, wave+talk, shrug, dance, jump, run)
python3 body_build.py all      # everything; add names to limit:  python3 body_build.py rigs aigul timur
```

## What is in `body/<name>/`
| file | what |
|---|---|
| `rig.json` | per view (`q34` front three-quarter, `side`): parts with `file`, `pivot` (px in the png), `parent`, `offset` (px from the parent's pivot, rest pose), `z`, `hull` (outline points); `head_states`; `soles`, `ground`, `waist_dx`; plus `anchors`, `dims`, `has` (tail, wings, mic) |
| `head_<view>.png` + `head_<view>_<state>.png` | the bust head, turned for the view; states are cropped overlays (`at` = position in the head png): `mouth_closed/A/E/O/U/MBP`, `blink`, `expr_happy/angry/shocked` |
| `torso_<view>`, `pelvis_<view>`, `neck_<view>`, `hair_back_<view>` | turned body parts (outfit, skirt / robe / coat tails / trousers) |
| `upper_arm_L/R`, `lower_arm_L/R`, `hand_L/R_<shape>`, `thigh_L/R`, `shin_L/R`, `foot_L/R_<view>`, `tail`, `wings` | limbs; hand shapes `relaxed open fist point flat`; animals get paws, owl wing-tip feathers, salmon fins, robot steel limbs |
| `full_q34.png` | the standing puppet, front three-quarter, transparent |

`body/body.json` indexes all characters (kind, about, voice, files, size, tail/wings) and lists views, poses, cycles,
hand shapes, visemes, expressions and props. Parts are stored at 768 px per unit (a standing adult is ~900 px tall).

Rig: `pelvis` (root) → `torso` → `neck`, `head` → `hair_back`; `torso` → `upper_arm` → `lower_arm` → `hand`;
`pelvis` → `thigh` → `shin` → `foot`; `pelvis` → `tail`; `torso` → `wings`. `_L` is the near side, `_R` the far side
(drawn behind the body and a little darker). Every limb segment has round ends centred on both joints, so joints stay
closed at any angle. The puppet faces screen-right; render with `flip` to face left.

## Animating a character in a frame loop
```python
import anim as A

p = A.Puppet('aigul', view='side', scale=0.5)      # scale: output px per rig px
scene = A.Scene(1280, 720)                          # plain felt wall + floor
speed = A.stride(p, 'walk') * p.scale / A.clip('walk').length    # px/s that keeps the planted foot still
for i in range(25 * 4):
    t = i / 25
    pose = A.play('walk', t, p)                     # dict of joint angles at time t (keyframes + easing, looped)
    frame = scene.frame([(p, pose, 100 + speed * t, 650, False,           # puppet, pose, x, ground y, flip
                          dict(expr='happy', mouth='A', blink=False))])   # head states, as in the bust
    # frame: HxWx3 uint8 -> ffmpeg / PIL

img, (ox, oy) = p.image(pose)                       # or just the puppet: transparent RGBA, ground line at oy
```
- `A.POSES` (enter from standing, then hold or loop): `stand sit wave point shrug facepalm arms_crossed hands_on_hips
  typing holding_phone thinking jump fall bow dance`.
- `A.CYCLES` (looping): `walk run nod head_shake laugh idle` (idle = breathing + a blink).
- Blend two poses: `A.blend(pose_a, pose_b, u)`; switch clips smoothly by blending the old clip's last pose into the new one
  over ~0.3 s (see `body_build._demo`).
- A pose can be edited on the fly: `pose['head'] += 5`, `pose['shape'] = {'L': 'open'}`, `pose['props'] = {'phone': 'L'}`.
- Talking: pass `mouth=` per frame (visemes `closed A E O U MBP`), `expr=` (`neutral happy angry shocked`), `blink=`.
- Both views use the same angles, so a puppet can cut from `side` (walking) to `q34` (talking) between frames.

## Adding a pose
Poses are plain dicts in `anim.POSE`; clips (keyframes) in `anim.POSES` / `anim.CYCLES`.
```python
A.POSE['salute'] = {
    'base': 'stand',                                     # start from another pose
    'reach': {'R': ('eyes', 0.04, -0.02, -1)},           # arm IK: wrist to an anchor + (dx, dy) units; elbow side +1/-1
    'wrist_R': 30, 'shape': {'R': 'flat'},               # extra hand angle, hand shape
    'head': 4, 'expr': 'happy',
    'side': {'head': 2},                                 # optional overrides for the side view
}
A.POSES['salute'] = A.Clip([(0, 'stand', 'linear'), (0.5, 'salute', 'back')])   # (time s, pose, easing into it)
```
- Angles are degrees, positive = counter-clockwise on screen; 0 = limb hanging straight down. With the puppet facing right,
  + swings a limb forward; for the near arm (`_L`, screen-left) "outwards" is negative, for the far arm positive.
- Joints: `pelvis` (whole body), `torso`, `head`, `upper_arm_L/R`, `lower_arm_L/R`, `hand_L/R`, `thigh_L/R`, `shin_L/R`,
  `foot_L/R`, `tail`, `wings`.
- IK anchors: `mouth eyes chin head_top chest belly hip_L hip_R shoulder_L/R knee_L/R`.
- Other keys: `root` (dx, dy in units after grounding; dy < 0 lifts), `ground` (`feet` default: lowest sole on the floor;
  `all`: lowest point of the whole body, for lying; `None`), `zset` (draw order, torso = 14, head = 15, near arm 16-18,
  far arm 3-5), `props` (`phone`/`mic` in a hand: `'L'`/`'R'`; `stool`, `laptop`: `True`), `head_sx`, `scale`, `blink`, `mouth`.
- Easing: `linear in out inout sine back step`. `Clip(keys, loop=(t0, t1), hold=t)`: loop a span after the first pass;
  `hold` is the moment shown on contact sheets. Cycles: `mirror_legs(pose)` swaps L/R for the second half step.
- Check it: `python3 body_build.py sheets <name>` and look at `body_sheets/<name>.jpg`.

## Known gaps
- Heads are the frontal bust heads turned by a 2D warp (features shift, the far side is squeezed); there is no true profile
  head, so the `side` view is a strong three-quarter turn rather than a pure profile. No head turn between views within a clip.
- Talking states are baked per view (12 overlays each); expression overlays still replace the mouth (as in the bust).
- Skirts, robes and coat tails are rigid (part of the pelvis); legs swing under them. Long hair is part of the head.
- Hand shapes are drawn hanging down; IK gets the wrist to the target but finger direction is set by hand (`wrist_*`).
- The bust's hand-held mic is not on the body; use the `mic` prop (`'props': {'mic': 'R'}`).
- Feet do not adapt to slopes; the floor is flat (y = 0). Walk/run assume the scene moves the puppet at `stride/length`.
