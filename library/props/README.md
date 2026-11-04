# puppet-procedural: code-drawn felt props and camera moves

Everything here is drawn by code: Pillow polygons, ellipses, lines and arcs, no image generation and no paid services.
Each prop is drawn in several layers; every layer goes through extella-mult's `felt_composite`
(bevel lit from the top-left, wool grain, soft shadow on the layers beneath), so the props look like stacked felt cut-outs.

## Files

| file | what |
|---|---|
| `props_lib.py` | 273 prop functions in 9 categories, the `Canvas` drawing helper and the felt palette `C` |
| `render_props.py` | renders every prop through `felt_composite` to `png/<category>/<name>.png` and makes `contact-<category>.png` |
| `png/` | the rendered props: transparent PNG, cropped with a 14 px margin |
| `contact-*.png` | one contact sheet per category on a light checkerboard, with names |
| `motion.py` | ease curves, camera moves and transitions for a Pillow frame pipeline |
| `demo_motion.py` | renders `showcase.mp4` (10 s, 960x540, 25 fps) with three felt scenes made from the props |
| `showcase.mp4` | the rendered showcase |

## Run

    pip install pillow numpy scipy          # ffmpeg is needed only for the demo
    # extella-mult must be checked out next to this repo, or set EXTELLA_MULT=/path/to/extella-mult
    python render_props.py                  # all props + contact sheets (~1 min)
    python render_props.py food             # one category
    python render_props.py --only apple_red food
    python demo_motion.py                   # showcase.mp4 (~20 s)

In code:

    from props_lib import Canvas, PROPS
    c = Canvas(); PROPS['food']['teapot'](c)
    layers = c.frame()                      # [(RGBA 512x512, depth), ...] -> felt_composite each over a base

    from render_props import felt_prop      # or get the finished felt RGBA image directly
    img = felt_prop('food', 'teapot')

## Writing a new prop

    @prop('food')
    def my_thing(c):
        c.ell(256, 300, 150, 120, C['coral'])      # first layer: the body
        c.new(0.6)                                  # new layer; 0.6 = shallower bevel and shadow
        c.circ(220, 260, 30, shade(C['coral'], 0.4))
        c.clip()                                    # optional: keep this layer inside the one below

Canvas primitives (512-px coordinates): `poly, ell, circ, rect(r=), line(w), arc, pie, ring, star, rrot, capsule,
blob, leafshape, clip, punch`. Helpers: `shade(col, f)`, `rot(pts, cx, cy, deg)`, `bez(...)`, `arcpts(...)`.
`variant(cat, name, fn, *args)` registers a parametric prop (cars, trees, flowers, grass, ...).

## Props (273)

| category | count | props |
|---|---|---|
| food | 54 | apple_red, apple_green, orange, lemon, pear, banana, cherries, strawberry, grapes, watermelon_slice, pineapple, peach, carrot, tomato, cucumber, eggplant, bell_pepper, onion, potato, broccoli, corn, cabbage, pumpkin, garlic, bread_loaf, baguette, lepyoshka, croissant, layer_cake, cupcake, donut, cake_slice, berry_pie, plov_kazan, baursaki, teapot, piala, teacup, samovar, sushi_nigiri, sushi_maki, pizza, pizza_slice, burger, hot_dog, ice_cream, candy, lollipop, fried_egg, cheese, milk_carton, honey_jar, watermelon, sandwich |
| plants | 44 | grass_spiky, grass_round, grass_curly, grass_tall, grass_seeds, grass_low, flower_daisy, flower_tulip, flower_sunflower, flower_rose, flower_poppy, flower_bluebell, flower_lavender, flower_dandelion, flower_lily, flower_pansy, bush_round, bush_berry, bush_flowering, bush_hedge, tree_round, tree_pine, tree_birch, tree_palm, tree_oak, tree_apple, tree_willow, tree_autumn, tree_poplar, tree_snowy_fir, cactus, cactus_round, succulent_pot, potted_plant, mushroom_fly_agaric, mushroom_porcini, mushroom_cluster, leaf_green, leaf_maple, leaf_autumn, leaf_monstera, cattail, reeds, clover |
| home | 29 | chair, armchair, stool, dining_table, coffee_table, sofa, floor_lamp, table_lamp, bed, tv, retro_tv, fridge, stove, carpet, round_rug, wall_clock, alarm_clock, picture_landscape, picture_abstract, mirror, vase_flowers, vase, books, bookshelf, wardrobe, window, door, kettle, houseplant_hanging |
| office | 25 | laptop, monitor, smartphone, desk_phone, document, documents_stack, folder, stapler, mug, whiteboard, chart_arrow_up, chart_arrow_down, bar_chart, pie_chart, pen, pencil, calculator, briefcase, paper_clip, scissors, desk_lamp, printer, calendar, keyboard, computer_mouse |
| city | 22 | bench, street_lamp, traffic_light, bus, car_sedan, car_hatchback, car_van, car_sport, taxi, bicycle, scooter, kiosk, fountain, fire_hydrant, trash_bin, road_sign, direction_sign, mailbox, tram, apartment_block, shop_front, parking_meter |
| nature | 25 | rock_big, rock_flat, rock_pile, cloud_puffy, cloud_long, cloud_rain, cloud_storm, sun, sun_simple, moon_crescent, moon_full, star, stars_cluster, rainbow, snowman, campfire, waves, mountain, snowflake, raindrop, island, puddle, log, hill, iceberg |
| tech | 18 | rocket, rocket_flying, satellite, ufo, robot, robot_round, drone, planet_ring, planet_earth, planet_plain, comet, astronaut_helmet, lightbulb, battery, gear, magnet, space_station, game_controller |
| clothes | 21 | top_hat, cap, beanie, sun_hat, cowboy_hat, tubeteika, scarf, glasses, sunglasses, tie, bow_tie, crown, backpack, umbrella_open, umbrella_closed, boot, sneaker, tshirt, dress, mitten, sock |
| symbols | 35 | heart, star_symbol, question_mark, exclamation_mark, arrow_right, arrow_left, arrow_up, arrow_down, arrow_curved, arrow_cycle, speech_bubble, thought_bubble, shout_bubble, money_bill, money_stack, coin, coin_stack, lightning, fire, smoke_puff, sparkle, music_note, music_notes, check_mark, cross_mark, plus_sign, key, padlock, magnifier, target, location_pin, hourglass, zzz, bell, gift_box |

## motion.py

`t` is progress 0..1. Camera moves are `fn(frame, t, params)`, transitions `fn(img_a, img_b, t, params)`; every
function returns an RGB frame of the same size. `params` is an optional dict; `ease` takes a name from `EASES` or a function.

### Ease curves

- `linear(t)` : constant speed
- `ease_in(t)` : cubic, starts slow
- `ease_out(t)` : cubic, ends slow
- `ease_in_out(t)` : cubic, slow at both ends
- `ease_out_expo(t)` : exponential stop, for crash moves
- `ease_back(t)` : Overshoots past 1 and settles (out-back).
- `ease_in_back(t)` : Pulls back below 0 before going (in-back).
- `ease_elastic(t)` : Springs past the target a few times (out-elastic).
- `ease_bounce(t)` : Drops and bounces on the target (out-bounce).

Names in `EASES`: `linear`, `in_`, `out`, `in_out`, `expo`, `back`, `in_back`, `elastic`, `bounce`.

### Camera moves and helpers

- `view(img, cx=0.5, cy=0.5, zoom=1.0, angle=0.0, dx=0.0, dy=0.0, fill=(0, 0, 0))` : Look at img through a virtual camera: centre (cx, cy) in 0..1, zoom > 1 goes closer, angle in degrees (camera roll), dx/dy shift the picture by a fraction of its size.
- `cover_zoom(angle, w, h)` : The zoom that keeps a rotated frame free of empty corners.
- `push(frame, t, p=None)` : Push in: zoom from 1 to params zoom (1.35) towards cx, cy.
- `pull(frame, t, p=None)` : Pull out: start at params zoom (1.35) on cx, cy and open to the full frame.
- `pan(frame, t, p=None)` : Pan across the frame: the camera, zoomed by params zoom (1.3), travels from (x0, y0) to (x1, y1) in 0..1.
- `parallax(layers, t, p=None)` : Orbit-like parallax for 3 RGBA layers [back, middle, front]: the camera swings sideways (and a little in depth), nearer layers move more.
- `crash_zoom(frame, t, p=None)` : Crash zoom: a violent zoom into (cx, cy) that lands in the first third, with a zoom blur while moving.
- `handheld(frame, t, p=None)` : Handheld wander: slow organic drift in x, y and roll.
- `dutch_tilt(frame, t, p=None)` : Dutch tilt: roll the camera to params angle (12 degrees) with a cover zoom so no corner is empty.
- `rack_focus(frame, t, p=None)` : Fake rack focus: focus moves from the background to the foreground (or back with reverse=1).
- `shake(frame, t, p=None)` : Shake with decay: a hit at t=0 that dies away.
- `slowmo_time(t, start=0.4, length=0.2, factor=0.2)` : Time remap for a slow-motion hold: playback speed drops to factor between start and start+length (both in output time 0..1) and recovers smoothly.
- `slowmo_hold(frame_at, t, p=None)` : Slow-motion hold: frame_at(src_t) renders the scene at source time; output time t is remapped by slowmo_time and, while slow, the camera creeps in and the frame gets a soft vignette.
- `vignette(frame, strength=0.4)` : Darken the corners (helper used by slowmo_hold, also handy on its own).
- `iris_in(frame, t, p=None)` : Iris in from black on one frame (opens as t goes 0 -> 1).
- `iris_out(frame, t, p=None)` : Iris out to black on one frame (closes as t goes 0 -> 1).

### Transitions

- `whip_pan(img_a, img_b, t, p=None)` : Whip pan from a to b: a fast slide with heavy horizontal motion blur peaking in the middle.
- `iris(img_a, img_b, t, p=None)` : Iris: a circle closes on a to black (first half) and opens on b (second half).
- `wipe(img_a, img_b, t, p=None)` : Wipe from a to b with a soft edge.
- `wipe_left(img_a, img_b, t, p=None)` : wipe with direction=left.
- `wipe_right(img_a, img_b, t, p=None)` : wipe with direction=right.
- `cross_dissolve(img_a, img_b, t, p=None)` : Cross-dissolve a into b.
- `dip(img_a, img_b, t, p=None)` : Dip to a colour: a fades to params color (black) by the middle, then b fades up.
- `dip_to_black(img_a, img_b, t, p=None)` : dip through black.
- `dip_to_white(img_a, img_b, t, p=None)` : dip through warm white.
- `page_turn(img_a, img_b, t, p=None)` : Page-turn-like slide: a folds away towards the left edge like a page (narrows, darkens towards the fold, with a bright curl strip and a shadow cast on b).
- `slide(img_a, img_b, t, p=None)` : Plain slide (push transition): b pushes a out.

`CAMERA` and `TRANSITIONS` map names to the functions, for driving them from a script or a scene language.

## Showcase timeline (demo_motion.py)

0-1.5 s parallax on the town (3 layers) · 1.5-2.5 push + handheld · 2.5-3.1 whip pan to space · 3.1-3.9 crash zoom
on the rocket (expo) · 3.9-4.5 shake with decay · 4.5-5.3 iris out/in to the kitchen · 5.3-6.1 dutch tilt (back
ease) · 6.1-6.9 rack focus · 6.9-7.5 wipe right to the town · 7.5-8.2 pan (elastic) · 8.2-8.8 page turn to space ·
8.8-9.4 slow-motion hold on a parallax drift + cross-dissolve · 9.4-10 dip to black.
