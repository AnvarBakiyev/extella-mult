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
People: `girl`, `boy`, `mom`, `dad`, `granny`, `grandpa`, `doctor`. Actions: stand, walk, run, wave, jump, sit, dance, look_up, sleep, hug, give, hold_hands.
Animals: `cat`, `fox`, `dog`, `bunny`, `bear`, `hedgehog`, `mouse`, `frog`, `hen`, `elephant`. Actions: stand, walk, run, jump, sit, look_up, sleep, hug, give, hold_hands. `bird`: fly, stand.
`girl walk from offleft to 0.45 0-5s y=0.95`, `dog sit at 0.3 2-8s y=0.96 facing=-1`. Params: `y` (feet line), `size`, `facing` (1 or -1), `color`, `hair`, `holds=lantern|balloon|flower|book|gift|umbrella|ball|medicine`. One end of a move is enough: `walk to 0.4` comes in from the nearer side. A character does one action at a time.
Any person can look different: `skin=light|tan|brown|dark` or `#rrggbb`, `hair=#rrggbb`, `hairstyle=bob|bun|short|bald|braids|ponytail|curly|afro`. Write the same look on each line of that character: `girl stand at 0.3 0-3s y=0.95 skin=brown hairstyle=braids hair=#2a1a14 color=#f2a541`, `boy wave at 0.6 0-3s y=0.95 skin=dark hairstyle=afro hair=#1e1512`. `hug`, `give`, `hold_hands` and `sleep` take the look from the character's other lines.
`wave` raises one hand beside the head, `dance` raises both hands, one higher in turn, `jump` raises both hands and tucks the legs in the air.

`mood=happy|sad|surprised|sleepy` sets the face of a person, an animal or a bird: `fox sit at 0.5 0-4s y=0.96 mood=sad`. `happy` is the usual smile and the default; `sad` gives brows like a little roof, a mouth turned down and a tear; `surprised` gives round eyes and an "o" mouth (a hen opens its beak); `sleepy` gives closed eyes, arcs. A bird changes only its eye and brow. To change the mood, write a new line with the next seconds: `fox sit at 0.5 4-8s y=0.96 mood=happy`. This `mood` is about the face; `music mood=` is a different word for the sound.
## Two characters together
`girl hug cat 3-5s`, `girl hold_hands boy 3-6s`, `girl give cat ball 2-3s` work for any two people or animals (not `bird`). The first one starts the action, the second is the partner.
- Both must be in the frame: the first one needs a place from its line before or after, or `at x`, and takes its `y`, `size`, `color` and `hair` from those lines. The partner needs its own line for the whole time, such as `cat stand at 0.5 0-6s`. The partner keeps doing that line; `cat sit` stays sitting.
- They must stand at most 0.3 of the frame apart. The first one walks up by itself, and walks to its next line at the end. Both turn to each other. An animal is hugged from behind, so it turns away and its muzzle stays in view.
- `give` takes one thing: `lantern`, `balloon`, `flower`, `book`, `gift`, `umbrella`, `ball`, `medicine`. The thing changes hands halfway; the partner keeps it in its next lines of that scene and the first one no longer has it.
- With `hold_hands`, if the partner walks or runs, the first one goes along: `boy walk from 0.3 to 0.8 0-6s`, `girl hold_hands boy 0-6s`.
- A partner cannot be busy with its own `hug`, `give`, `hold_hands` or `sleep`. `mood=` works on these lines too.

`boy sleep 8-14s` lies down under a blanket in the bed of the scene, head on a pillow, eyes closed, breathing. `cat sleep at 0.6 8-14s y=0.97` lies anywhere, with a small pillow and blanket of its own; `blanket=#rrggbb` picks the colour. A scene needs a `bed` for a sleeper with no place, and one bed holds one sleeper. A sleeper's mood is `sleepy` unless you set it. Animals can hold things too: `dog stand at 0.5 0-3s holds=ball` shows a paw with the ball.

## Elements
| name | what it is |
|---|---|
| `hills` | Two rolling hills; top = horizon height. |
| `puff_cloud` | A puffy cloud: x, y, s; drifts slowly with speed. |
| `round_tree` | A lollipop tree that sways a little: x, y (base), s. |
| `house_row` | A street of tall colourful houses with windows: base = street line, grey=1 drains the colour. |
| `felt_sun` | Sun or moon: x, y, r, kind=sun\|moon. |
| `felt_sea` | Sea with gentle waves from top down; a sandy shore if shore=1. |
| `sky` | Gradient sky: time=day\|dawn\|sunset\|night\|space; night and space get stars. |
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
| `planet` | A planet with continents and an optional ring: x, y, r, ring=1, color. The ring passes behind and in front of the ball. |
| `rocket` | A felt rocket: x, y (base), s (size); flying=1 adds a flickering flame and a shake; rise=0.2 lifts it 0.2 of the frame per second; drift=0.1 moves it right per second; tilt=15 leans it (degrees, + to the right), spin=90 turns it (degrees per second); pilot=cat\|boy\|girl\|dog\|bunny\|fox\|bear shows who looks out of the window; color=#e05a5a for stripes and fins; pad=1 adds a launch tower; sputter=1 makes the flame cough. |
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
| `ground` | Flat ground from top down: kind=meadow\|sand\|road\|path. |
| `garland` | A string of felt light bulbs across the wall: y (top), x0, x1, sag, bulbs. |
| `balloon_bunch` | Three felt balloons tied together, swaying: x, y (where the strings are tied), s. |
| `toys` | Small things on the floor so a room is not empty: blocks, a ball, a party hat, confetti: x0, x1, y. |
| `kitchen` | A whole kitchen: tiled wall, fridge, cupboards, a stove with a pot, a sink, a window: color (wall), cupboard, pot, window, time, floor. |
| `classroom` | A classroom from inside: a green blackboard, a clock, a window, books, a teacher's table, small desks: color, board, window, time, floor, desks=0. |
| `shop` | A small grocery from inside: shelves of boxes, jars and fruit, a striped awning, a counter with scales and a till: color, awning, floor, seed. |
| `underwater` | The sea from inside: bands of blue water, faint rays, a sandy bottom, corals and stones: color, floor, seed. |
| `city_night` | A city at night: stars, a moon, lit windows that change slowly, street lamps, a street: base, moon, seed. |
| `ferris_wheel` | A big wheel that turns, with hanging cabins: x, y (ground), r, speed, cabins. |
| `carousel` | A merry-go-round with a striped roof and horses going round: x, y (ground), s, speed. |
| `stall` | A fair stall with a striped canopy: x, y (ground), s, color. |
| `bunting` | A string of triangle flags: y (top), x0, x1, sag, flags. |
| `barn` | A red barn with crossed doors and a hay loft: x, y (ground), s, color. |
| `haystack` | A round haystack: x, y (ground), s. |
| `tractor` | A little tractor: x, y (ground), s, color; drive=0.05 moves it right per second. |
| `seaweed` | Seaweed swaying under water: x, y (bottom), s, color. |
| `fish` | Bright fish swimming across: count, y0, y1, seed. |

`kitchen`, `classroom`, `shop`, `underwater` and `city_night` each fill the whole frame, so a scene needs no `sky` with them; `time=night` dims the indoor places. Heroes stand on them with `y=0.95` to `y=0.97`. A fair and a farm are built from parts:
```
scene 0-8s: sky ground(top=0.72,kind=meadow) ferris_wheel(x=0.74,y=0.74) carousel(x=0.24,y=0.8) stall(x=0.5,y=0.78) bunting(y=0.04)
scene 8-16s: sky hills(top=0.56) ground(top=0.72,kind=meadow) barn(x=0.22,y=0.76) haystack(x=0.46,y=0.78) tractor(x=0.8,y=0.92) fence(y=0.8,x0=0.55,x1=1)
scene 16-24s: underwater seaweed(x=0.2,y=0.85) seaweed(x=0.74,y=0.85,s=1.2) fish
```

Elements have no seconds and no actions. To move one, use its parameters: `rocket(flying=1,rise=0.3,tilt=20,spin=40)`; a falling rocket is `rise=-0.1` with `spin`, a crashed one `tilt=84`.

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
| `smoke` | Puffy felt smoke clouds that billow out sideways and up from at=x,y (a rocket launch, a crash, a cough); r = how far they spread; color=#efebe4. |

`room(cozy=1)` adds striped wallpaper, a panelled lower wall, a rug, curtains and a picture (params `panel`, `curtain`, `picture`).

## Speech bubbles
`girl say "Привет, котик!" 3-5s` puts a felt speech bubble over the speaker, with a tail pointing at its head. The bubble fades in and out, follows the speaker while it walks and stays above everything else in the frame. Any letters work, Cyrillic too. Long lines wrap by themselves; `\n` inside the quotes always starts a new line: `bunny say "Первая строка\nвторая" 1-3s`.

Params: `size` (letter height, 0.05), `width` (widest line as a fraction of the frame, 0.26), `side=left|right` (which way the bubble leans; by default towards the middle of the frame), `color` (the felt, #rrggbb), `at x,y` (a bubble with no speaker in the frame). A bubble holds up to 90 letters and 4 lines; longer speech goes in two `say` lines one after the other. The speaker must be in the frame at that time and the line must stay inside one scene. Give each line about a second per three words, and say lines one after the other when you can: two bubbles that would touch slide apart by themselves (sideways, or the later one up when there is no room), and `--check` prints a warning. `say` works only in `style=felt`; it draws words, it does not speak them.

## Text, sound, camera
`text "Привет!" font at 0.5,0.2 size=0.11 color=#c5583e 9-12s hold=1` writes any text. `music mood=bright key=C tempo=110` (moods wonder dark bright tense cozy calm) plays that mood's own short melody; `music tune=birthday key=G` picks one by name, with its own mood and tempo: `hop`, `home`, `breeze`, `stars`, `shadow`, `chase`, `birthday`, `twinkle`, `jingle`, `lullaby`; `tune=none` plays free notes. A second `music ... at 8s` changes the music from that second. `sfx chime at 6s`, `fade in 0-1s`, `fade out 15-16s`, `camera zoom 1.0-1.1 0-6s`, `camera pan right 0-6s`.

## Voice
`voice "Две тысячи двадцать шестой год. [pause] Человечество готово." at 0.3s who=deep` speaks the words from that second; the music gets quieter under speech. Voices (ElevenLabs): `narrator`, `deep`, `odessa`, `gogi`, `fairy`, `calm`. Tags in square brackets set the delivery: `[excited]`, `[whispering]`, `[sighs]`, `[pause]`, `[deadpan]`. Each line is generated once and cached. It needs your own ElevenLabs key as `"elevenlabs_key"` in `~/extella-mult/config.json`; without a key use a ready recording: `voice file=~/line.mp3 at 2s`.

## Films as Extella experts
In Extella a film is an expert with `cspl=scene`; `{{name}}` places are filled from the run parameters, `{{a|b|5}}` takes the first of a and b that was given, else the last word (`{{candles|age|5}}`), and the handler runs `check`, `render` or `status`. `extella/templates/` holds sixteen felt stories.

## Other styles
The handler also has a drawn `style=2d` and an experimental Blender-based `style=3d`; the agent uses felt only.
