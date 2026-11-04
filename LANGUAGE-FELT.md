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
