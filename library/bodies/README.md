# Felt puppet characters, built from code

153 talking felt puppet busts drawn only with Pillow primitives and `felt_composite` (copied unchanged from
`extella-mult/handler/felt.py`). No image generation, no paid services.

```
python3 build.py            # render chars/ (about 7 min on 4 cores; `python3 build.py aigul` for one)
python3 sheets.py           # sheets/cast_*.jpg, sheets/frames_*.jpg, demo/demo_*.mp4
```

## Full bodies
Every character also has a full-body rig (torso, arms, hands, legs, feet, tails, wings as pivoted parts) with poses,
walk/run cycles and the same talking head: see [BODY.md](BODY.md) (`anim.py`, `body_build.py`, `body/`, `body_sheets/`,
`body_demo/`).

## Files per character: `chars/<name>/`
| file | what |
|---|---|
| `base.png` | full neutral frame, 1024x1024, transparent background |
| `mouth_closed/A/E/O/U/MBP.png` | visemes: full-size, pixel-aligned overlay of the **mouth region** only |
| `blink.png` | overlay of the **eye region** with closed lids |
| `expr_neutral/happy/angry/shocked.png` | overlay of the eye and mouth regions (eyes, lids, brows, mouth) |
| `char.json` | name, kind, about, default_voice, palette, parts, anchors (eyes, mouth), layering note |

A frame is `base`, then optionally `expr_<e>`, then `mouth_<v>`, then optionally `blink`, each alpha-composited
(`charlib.compose(base, *overlays)`). The overlays are exact (checked: max 2/255 difference against a full render),
regions do not overlap, so talking, blinking and an expression stack. Overlays hold only the changed region, so they
are 50-110 KB instead of a full 560 KB frame each.

## Parts (charlib.py)
- heads: 12 (`round oval egg pear square long wide heart diamond jaw potato moon`)
- hair: 17 (`bald horseshoe buzz short sidepart quiff spiky curly bob long ponytail bun braids wavy mohawk kerchief topknot`) + `tuft` for animals; facial hair: mustache, walrus, beard, goatee, stubble
- kits: 10 animals (`fox bear cat dog owl salmon frog mouse hare pig`) + `robot imp monster sheep`; each kit brings ears/fins/horns, muzzle, nose, eye type, fur colours
- eyes: 5 (`round sleepy wide narrow bead`) with lids (top/bottom/tilt), iris colours; brows: 4 (`neutral angry worried raised`)
- noses: 8 (`ball button long hooked wide snout pig beak`) + kit noses (cat, mouse, hare, sheep, frog dots)
- skin tones: 6 (`porcelain light olive tan brown deep`)
- outfits: 13 (`sweater suit labcoat hoodie overalls dress uniform chef robe vest tshirt shirt spacesuit`), uniforms carry no insignia
- hats: 10 (`cap beanie tubeteika kalpak toque fedora bowler beret straw hardhat`); accessories: glasses (round/square/cat-eye), headphones, headset, scarf, earrings, mic with hand, stethoscope, bowtie, necklace, pencil, lanyard, helmet, flower; hands: mic, wave, clasp
- visemes: closed, A, E, O, U, MBP; expressions: neutral, happy, angry, shocked; owl has a beak that opens per viseme

Rendering: each piece is drawn at 2048 px, reduced to 1024 with premultiplied alpha, then laid with felt_composite
(own bevel, grain and shadow per piece). Base pieces render once; per state only the face (sclera, iris, lids,
brows, mouth cavity, lips) and front pieces (nose, moustache, glasses, whiskers, hand/mic, helmet glass) are redrawn.

## Cast
`characters.py`: 90 people (newsroom, office, medicine, science, food, transport, village, family, teachers,
artists, sport; Central Asian, Slavic, Caucasian, African, South and East Asian looks; kids to grandparents) and
63 animals/specials (incl. salmon anchor, HR imp, robots, monsters). Voices from: journalist, salmon, lady, deep, ad,
narrator, odessa, gogi, fairy, calm.

## Known weak spots
- busts face front; the full-body rig (BODY.md) adds a turned three-quarter and side view and arm gestures
- visemes are one mouth per shape; no in-between (co-articulation) frames
- beards partly cover open mouths; hats over frog/hare eyes and ears need per-kit placement
- expression overlays replace the mouth too, so "angry while talking" uses the neutral viseme mouth with angry eyes
