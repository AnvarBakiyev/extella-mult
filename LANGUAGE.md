# SCENE, felt style
A film is a text program, one statement per line. The first line picks the look: `film title="..." style=felt fps=24 size=1920x804`. Every element, character part and effect is drawn as a felt cut-out: a soft rounded edge, a fibre texture and a shadow on what lies beneath.
```
film title="Дома лучше всего" style=felt fps=24 size=1920x804
music mood=cozy key=G tempo=100
scene 0-6s: sky(time=night) hills(top=0.62) forest(base=0.66)
grandpa walk from offleft to 0.4 0-4s y=0.95 holds=lantern
fox jump at 0.55 4-6s y=0.96 facing=-1
text "Дома лучше всего" font at 0.5,0.2 size=0.11 color=#f5d742 4-6s hold=1
```
Scenes touch (`0-6s`, `6-12s` ...). Elements go back to front on the scene line or on their own lines under it; the renderer puts them in depth order (sky, far, ground, props). Positions are 0..1 of the frame, (0,0) is the top-left. A night sky dims the whole scene.
## Characters
People: `girl`, `boy`, `mom`, `dad`, `granny`, `grandpa`. Actions: stand, walk, run, wave, jump, sit, dance, look_up.
Animals: `cat`, `fox`, `dog`, `bunny`, `bear`. Actions: stand, walk, run, jump, sit, look_up. `bird`: fly, stand.
`girl walk from offleft to 0.45 0-5s y=0.95`, `dog sit at 0.3 2-8s y=0.96 facing=-1`. Params: `y` (feet line), `size`, `facing` (1 or -1), `color`, `hair`, `holds=lantern|balloon|flower|book|gift|umbrella`. One end of a move is enough: `walk to 0.4` comes in from the nearer side. A character does one action at a time.
## Elements
| name | what it is |
|---|---|
| `hills` | Two rolling hills; top = horizon height. |
| `puff_cloud` | A puffy cloud: x, y, s; drifts slowly with speed. |
| `round_tree` | A lollipop tree that sways a little: x, y (base), s. |
| `house_row` | A street of tall colourful houses with windows: base = street line, grey=1 drains the colour. |
| `felt_sun` | Sun or moon: x, y, r, kind=sun|moon. |
| `felt_sea` | Sea with gentle waves from top down; a sandy shore if shore=1. |
| `sky` | Gradient sky: time=day|dawn|sunset|night|space; night and space get stars. |
| `mountains` | Soft rounded mountains with snowy tops along the horizon: top = highest peak. |
| `pine_tree` | A felt fir tree: x, y (base), s; snow=1 adds white tips. |
| `forest` | A row of round and pine trees along base. |
| `bush` | A round bush, flowers=1 adds blossoms. |
| `flowers` | A strip of small flowers along y between x0 and x1. |
| `river` | A winding river from the horizon to the bottom of the frame. |
| `bridge` | A little arched wooden bridge: x, y (deck), s. |
| `house` | One house with a door and windows: x (centre), y (ground), s, color, lit=1 for warm night windows. |
| `school` | A school with a clock and a flag: x, y (ground), s. |
| `rainbow` | A felt rainbow arc: x, y (centre of the arc's foot), r. |
| `planet` | A planet with continents and an optional ring: x, y, r, ring=1. |
| `rocket` | A rocket: x, y (base), s; flying=1 shakes it and adds a flame. |
| `moon_ground` | Grey cratered ground of the moon from top down. |
| `snow_ground` | Snowy rolling ground. |
| `snowman` | A snowman: x, y (ground), s. |
| `fence` | A wooden fence along y from x0 to x1. |
| `boat` | A sailing boat rocking on the water: x, y (waterline), s. |
| `lighthouse` | A striped lighthouse with a turning beam at night: x, y (base), s. |
| `room` | Inside a home: a wall (color), a wooden floor from floor= down, a window with the sky (time). |
| `table` | A round-cornered table: x, y (floor), s. |
| `cake` | A birthday cake with flickering candles: x, y (bottom), s, candles. |
| `gift` | A wrapped present: x, y (bottom), s, color. |
| `lamp` | A floor lamp: x, y (floor), s, on=1 glows. |
| `bed` | A bed with a blanket: x, y (floor), s, color. |
| `ground` | Flat ground from top down: kind=meadow|sand|road|path. |

## Effects
| name | what it is |
|---|---|
| `snow` | Felt snowflakes falling over the whole frame. |
| `rain` | Felt rain drops. |
| `hearts` | Hearts float up from at=x,y. |
| `sparkles` | Twinkling four-point stars around at=x,y (radius r). |
| `leaves` | Autumn leaves drifting down. |
| `bubbles` | Bubbles rise from at=x,y. |
| `balloons` | Balloons rise from the bottom over the effect's time. |
| `butterflies` | Butterflies flutter around at=x,y. |
| `notes` | Music notes float up from at=x,y. |

## Text, sound, camera
`text "Привет!" font at 0.5,0.2 size=0.11 color=#c5583e 9-12s hold=1` writes any text. `music mood=bright key=C tempo=110` (moods wonder dark bright tense cozy calm), `sfx chime at 6s`, `fade in 0-1s`, `fade out 15-16s`, `camera zoom 1.0-1.1 0-6s`, `camera pan right 0-6s`.

## Films as Extella experts
In Extella a film is an expert with `cspl=scene`; `{{name}}` places are filled from the run parameters, and the handler runs `check`, `render` or `status`. `extella/templates/` holds eight felt stories.

## Other styles
The handler also has a drawn `style=2d` and an experimental Blender-based `style=3d`; the agent uses felt only.
