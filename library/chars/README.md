# Felt puppet characters, built from code

153 talking felt puppet busts drawn only with Pillow primitives and `felt_composite` (felt.py, "felt v3": needle-felted
wool look, see below). No image generation, no paid services, no external textures.

```
python3 build.py            # render chars/ (about 6 min on 4 cores; `python3 build.py aigul` for one); also checks overlays
python3 sheets.py           # sheets/cast_*.jpg, sheets/frames_*.jpg, demo/demo_*.mp4, demo/talk_15s.mp4
python3 compare.py          # sheets/compare_felt3.jpg: v1 paper cut-out / v2 felt / v3 felt, 12 characters
```

## Files per character: `chars/<name>/`
| file | what |
|---|---|
| `base.png` | full neutral frame, 1024x1024, transparent background |
| `mouth_closed/A/E/O/U/MBP.png` | visemes: full-size, pixel-aligned overlay of the **mouth region** only |
| `blink.png` | overlay of the **eye region** with closed lids |
| `expr_neutral/happy/angry/shocked.png` | overlay of the eye and mouth regions (eyes, lids, brows, mouth) |
| `char.json` | name, kind, about, default_voice, palette, parts, anchors (eyes, mouth), layering note |

A frame is `base`, then optionally `expr_<e>`, then `mouth_<v>`, then optionally `blink`, each alpha-composited
(`charlib.compose(base, *overlays)`). The overlays are exact (checked by build.py on every character: max 4/255 against
a full render; frogs up to 66/255 on <90 pixels, see v3 known gaps), regions do not overlap, so talking, blinking and an expression stack. Overlays hold only the changed region, so they
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
(own volume, wool texture, fibres and shadow per piece; see "Felt v2"). Base pieces render once; per state only the face (sclera, iris, lids,
brows, mouth cavity, lips) and front pieces (nose, moustache, glasses, whiskers, hand/mic, helmet glass) are redrawn.

## Cast
`characters.py`: 90 people (newsroom, office, medicine, science, food, transport, village, family, teachers,
artists, sport; Central Asian, Slavic, Caucasian, African, South and East Asian looks; kids to grandparents) and
63 animals/specials (incl. salmon anchor, HR imp, robots, monsters). Voices from: journalist, salmon, lady, deep, ad,
narrator, odessa, gogi, fairy, calm.

## Known weak spots
- every character faces front; no head turn or 3/4 view, no arm gestures besides the fixed hand poses
- visemes are one mouth per shape; no in-between (co-articulation) frames
- beards partly cover open mouths; hats over frog/hare eyes and ears need per-kit placement
- expression overlays replace the mouth too, so "angry while talking" uses the neutral viseme mouth with angry eyes

## Felt v2 (branch `puppet-characters-felt2`): what changed
The first version read as flat paper cut-outs (clean edges, flat fill, fine noise). `felt.py` was rewritten; the drawing
code (charlib.py) only got a `kind` per piece (`felt`, `skin`, `hair`, `fur`, `fine`, `hard`) and per-piece seeds.
Per piece:
1. **Rounder silhouette**: sharp corners smoothed (blur + re-threshold of the alpha); thin lines are left alone.
2. **Fibrous edge**: the piece (colour and alpha) is domain-warped by an anisotropic noise field (0.7-2 px), so outlines
   and inner colour borders (stripes, lapels, muzzles) break up like wool instead of a clean cut, plus a soft fuzzy
   halo of the piece colour around it.
3. **Stray fibres**: short thin curved hairs (2-12 px at 1024, 0.5-1 px wide, 2x supersampled) start just inside the
   outline and stick out, lighter/darker than the piece and semi-transparent: ~30 per 100 px of outline on clothes,
   ~22 on skin, 60-80 on fur and hair. Hair and fur also get strands *inside* the piece that follow the outline.
4. **Wool texture**: a cached 1024 tile of ~190k layered micro-fibres (random direction, length, bend, a tint per
   stroke) plus soft clumps modulates the colour; it is offset per piece. Stronger on dark wool, weaker on white.
5. **Felt colour**: 12 % desaturated, heathered with a warmer-lighter and a cooler-darker tone mixed by low-frequency
   noise (2-3 nearby tones per piece).
6. **Volume**: height = blurred, saturating distance transform (a pillow); lit from the top-left with normals from
   it, edge ambient occlusion, warm (subsurface-like) shadows on skin, a soft sheen on the crown; underneath, a soft
   cast shadow plus a wide ambient-occlusion shadow.
7. **Studio light** on the whole frame: key light falloff from the top-left, a warm rim on the right-hand outline and
   a soft drop shadow behind the bust (semi-transparent black, so base.png still composites on any background).

Kept from the experiments: all of the above. Dropped: a strong high-contrast stroke texture (looked like crumpled
paper), whitish fibre tips on dark wool (read as dust), strong outline warp (looked torn rather than fuzzy).

Overlays: every random stream is seeded from the piece's place in the part list, so a piece drawn in two frames is
bit-identical and `base + overlay` still matches a full render (max 5/255 on fuzzy fur edges, 3/255 otherwise; checked on every character by
`python3 check_overlays.py`). Overlays are regenerated with the same look.

Render time: 5 min 10 s for all 153 characters on 4 cores (was about 7 min), i.e. ~8 s per character
(13 frames) on one core. PNGs are bigger (texture): 297 MB (was 228 MB) for chars/.

Known gaps: fibres are 2D (no real self-shadowing of hair), the light is baked in (always from the top-left), the felt
tile is the same pattern for every piece (offset, so seams are not visible), hard outlines of tiny details (pupils,
eye highlights, earrings) stay crisp on purpose so faces read at small sizes.

## Felt v3 (branch `puppet-characters-felt3`): what changed
Goal: push v2 further towards the needle-felted reference puppets (more volume, fuzzier, real wool surfaces) while
keeping faces readable. All in `felt.py` plus a few `kind`s in charlib.py; no image generation, no external textures.

New piece kinds: `knit`, `fleece`, `suit` (garment weaves), `ball` (noses, buttons, the owl's upper beak), `eye`
(sclera), `bead` (iris/pupil, bead eyes), `glint` (glossy eye highlight), `brow`.

1. **Deeper volume**: larger pillow radius (0.36 x piece size, up to 165 px), normals scaled 1.45x (v2 1.1x),
   light response 1.75x (v2 1.25x), wrap-around rim occlusion 0.30 (v2 0.22), silhouette rounding 2.8 px (v2 2.2) so
   edges read thicker and rounder.
2. **Ambient occlusion where pieces meet**: every piece now leaves three things on what lies beneath: a tight contact
   crease (2.2 px blur), a soft cast shadow offset down-right (7 px x depth) and a wide occlusion (16 px). This gives the
   dark band under the chin on the neck, under the fringe on the forehead and under collars / lapels / scarves.
   Face pieces (eyes, lids, brows, mouth) use a short 7 px occlusion so overlays stay compact.
3. **Specular-free sheen**: a broad, desaturated warm-white lift on top-lit areas, modulated by the fibre texture (the
   light sits on the fibres, no hot spot).
4. **Needle-felt surface (bump map)**: cached periodic fields add height detail to the normals: small needle pits
   (sparse 1.5 px dimples, also slightly darker), uneven density (26 px and 8 px lumps); weaker on skin, off on the
   fuzzy rim.
5. **Fibre direction follows the form**: four oriented fibre fields (0/45/90/135 degrees, white noise filtered in the
   Fourier domain, 7 px along x 0.75 px across) are blended per pixel by the tangent of the piece's outline, so fibres
   run around the form; weaker on light colours (it read as brushed metal on white).
6. **Fuzzier silhouettes**: stray fibres denser and longer (clothes 44 per 100 px up to 11 px, hair 130 up to 19 px, fur
   110 up to 17 px; v2 30/80/60, max 8-12 px), hair strands inside the piece 1.5x denser and longer, bigger fuzzy halo.
   **Fibres crossing borders**: along each new piece's outline a few fibres of the layer beneath (colour sampled
   there) lie over the new piece's edge.
7. **Eyes as glossy beads**: sclera and iris are domes (ball shading, little texture); the highlight is its own
   `glint` piece (no wool, softened 0.6 px) with a small second reflection; drawn under the lids, so blinking covers it.
8. **Noses and buttons as felted balls**: smooth dome height from a blurred mask (no distance-field creases), felt
   texture, own shadow and crease. Buttons were split out of the garments into `ball` pieces (shirt, suit, vest,
   overalls, uniform incl. pockets and epaulettes, chef, spacesuit lights).
9. **Garment weaves**: `knit` (sweater, scarf, beanie): V-stitch columns (80 per 1024 px, 124 rows) as a height + tone
   map, per-stitch tone jitter, jittered by the warp field; `fleece` (hoodie, hood, spacesuit): soft pills, more fuzz,
   lighter micro texture; `suit` (suit, uniform, vest, robe, overalls, fedora/bowler/kalpak/cap): finer, flatter
   pressed felt. Shirts, coats, dresses stay plain felt.

Overlay fixes made on the way (both were already wrong in v2, the old check only looked at every 13th character):
- regions are no longer a pure horizontal split: blink changes seed the eye region, viseme changes the mouth region,
  expression changes join by `split_y`, and every pixel goes to the nearer seed. The owl's beak is now two pieces (fixed
  upper beak, moving lower beak that starts clear of the eyes): owl overlays went from 220/255 to exact.
- raised brows are kept on the head (`_head_top`, incl. the frogs' eye bumps), so "shocked" never paints over the
  transparent edge: frogs went from 255/255 on ~26k pixels to <=66/255 on <90 silhouette pixels.
- build.py now checks `base + overlay == full render` for every character and prints the worst difference.

Render time: 6 min 3 s for all 153 characters on 4 cores (v2: 5 min 10 s), ~9.5 s per character (13 frames) on one
core; the per-process field warm-up (felt tile, oriented fibres, bump maps) takes ~6 s. `sheets.py` (contact sheets,
16 demos, 15 s talk) takes 3 min 45 s. PNGs: 288 MB for chars/.

Known gaps (v3):
- big plain suit/coat pieces can look a little lumpy (leathery) at 100 %; at video size it reads as felt
- the oriented fibres are four blended directions, not true flow lines; on grey fur (owl) they read slightly metallic
- fibres are still 2D strokes: no self-shadowing inside hair, stray fibres are not lit by the bump map
- knit columns are always vertical in screen space (sleeves, scarf ends and beanie do not follow their own axis)
- frog expression overlays differ by up to 66/255 on <90 pixels where the eye bumps touch the transparent edge
- light is baked in (top-left), the same as v2
