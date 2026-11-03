# SCENE — a small language for animated shorts

One statement per line. `#` starts a comment (at line start or after a space). Times are seconds: `2-6s` is a range, `at 12s` a moment. Positions are `x,y` fractions of the frame (0,0 = top-left) or names: `offleft left center right offright`. Parameters are `key=value` (`0.5`, `0.3,0.7`, `#ffd890`, `1920x804`, words).

Run: `python -m handler.main film.scene` (renders `film.mp4`), `--check` only validates, `--preview` renders a small silent preview, `--frames 3,10 --dir stills` dumps stills.

## Statements

| line | meaning |
|---|---|
| `film title="Fable" fps=24 size=1920x804` | optional header |
| `music mood=wonder key=D tempo=72 [from 31s]` | score section; moods: `wonder dark bright tense cozy calm`; keys `C D E F G A B Bb Eb Ab` |
| `scene 0-7s: night_sky moon(x=0.13,y=0.2) cloud_sea(palette=night) island tower` | a shot: background elements in back-to-front order, each with optional `(k=v,...)`. Scenes must touch (no gaps, no overlaps) and start at 0s |
| `fox walk from offleft to center 7.5-12s size=0.12 y=0.86` | actor action inside one scene. `from .. to ..` moves (facing follows direction), `at pos` holds. `facing=-1` flips |
| `camera pan down 0-7s [amount=0.1 zoom=1.15]` | slow pan (`up down left right`) |
| `camera zoom 1.0-1.12 20-26s [center=x,y]` | push-in or pull-out |
| `camera shake 36-37s amount=0.01` | decaying shake |
| `effect paper_vortex 33.5-36.5s center=0.5,0.5 count=700` | animated effect; `hold=1` keeps its end state until the scene ends |
| `text "Fable" handwritten at 0.49,0.63 size=0.13 54-57.5s [pen=tail anchor=x,y color=#.. hold=1]` | writes the text stroke by stroke; `pen=tail` draws the fox tail to the pen tip |
| `fade in 0-1.5s` / `fade out 58-60s` | to/from black |
| `sfx chime at 22s [gain=1 pan=0]` | sound effect |

Actors, effects and text are drawn after the scene's elements, in program order (later lines on top). Each must lie inside one scene; split a motion at a cut.

## Vocabulary

Elements: `night_sky dawn_sky morning_sky nebula stars moon sun cloud_sea(palette=night|dawn|gold,top,seed) mist island tower grass library(bright,grey,pillar,floor,rows) moonbeam floor_light pedestal_book shelf_closeup lantern parchment rooftop(view=wide|close,horizon)`

Actors: `fox` — `walk run stand sit closeup` (params `size y facing lookup`)

Effects: `paper_bird(start,end,size) dust(count,color) paper_storm(count) paper_vortex(center,count) light_burst(center) flash paper_crane(count,size) sheet_fall(land,w,h) confetti(count) quill`

Sounds: `page_rustle wind whoosh chime sparkle thud paper_burst splash clink purr meow`

Lettering glyphs: `a b c d e f g h i l m n o r s t u y A C F M S T` and space.

## Errors

The handler validates the whole program before rendering and stops with a sentence, e.g. `line 12: unknown element 'moom' (did you mean moon, moonbeam?)`, `line 20: scene 20-26s overlaps scene 18-22s (line 19)`, `line 31: fox cannot 'fly'; it can: walk, run, sit, closeup, stand`, `line 40: sfx at 70s is outside the film (0-60s)`.

## Text in any language

`text "С днём рождения, Мира!" font at 0.5,0.25 size=0.14 color=#fff4d8 9-12s hold=1` writes any text (Latin, Cyrillic, digits, punctuation) in the open Caveat font (OFL), revealed left to right. `handwritten` draws letters stroke by stroke but knows only `a b c d e f g h i l m n o r s t u y A C F M S T`.

## Styles

The first line picks one style for the whole film: `film title="..." style=2d` (default), `style=3d` or `style=toon`. The checker rejects a film that mixes them.

- **2d**: the drawn vocabulary above, rendered with numpy and Pillow. No GPU, no Blender.
- **3d**: Blender (EEVEE) renders every shot from a catalog of 582 CC0 models by Quaternius, 99 of them animated. Text, fades, music and sound are added on top by the same code as in 2d.
- **toon**: the 3d library drawn flat with outlines (experimental).

### 3d scenes

`scene 0-6s: day meadow common_tree_1(x=0.2,z=6) pine_2(x=0.7,z=14,s=1.2)`

- skies: `day dawn sunset night`; grounds: `meadow road sand snow`
- props from the catalog: `x` = 0..1 across the frame, `z` = metres away from the stage line, `s` = scale, `rot` = degrees

### 3d actors

`knight_male walk from offleft to 0.4 0-4s`, `panda dance at 0.3 4-8s facing=front`, `eagle fly from offleft to offright 8-13s lift=4`

- 51 people with 17 actions each (`walk run idle jump victory sit pickup punch swordslash roll hit death ...`), farm animals, dog, cat, wolf, eagle, cute creatures (panda, penguin, chicken, deer, bee, dragon, ghost, yeti ...), monsters, robots, sea creatures
- params: `size` (height in metres), `z` (depth), `lift` (metres above the ground), `facing` (`1` right, `-1` left, `front` towards the camera), `speed`, `turn`
- one actor name is one character within a shot, and it does one action at a time
- a position can be one number (`to 0.4`): the actor keeps its line
- the full list is `assets/lib3d/catalog.json` in the 3d bundle; rebuild it with `tools/build_catalog.py`

Not allowed in 3d: the 2d effects (`paper_bird`, `steam`, `confetti` ...) and the drawn elements and actors.

## Films as Extella experts

In Extella a film is an expert with `cspl=scene`: its code is a SCENE program, `{{name}}` places are filled from the run parameters, and the handler on the device runs `check`, `render` or `status`:

```
run_expert film_tpl_park_3d  {"mode": "render", "person": "cowboy_male", "animal": "wolf", "sky2": "night", "title": "Moon"}
```

A template that fits the request gives a new film with no new lines. `extella/templates/` holds ten of them.
