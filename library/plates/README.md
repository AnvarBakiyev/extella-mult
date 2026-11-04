# Felt background plates, made in code

A library of felt cut-out backgrounds for Extella Mult and Extella Puppet, drawn entirely with Pillow primitives and the
felt pass from `extella-mult/handler/felt.py`. No image models, no paid services, no network. Every plate is a 16:9
scene split into separate parallax layers, so a renderer can move them at different speeds.

## What is in a plate

```
plates/<name>/
  sky.png    opaque back: sky, sun or moon, stars, clouds (indoors: the back wall and floor, windows with the outside)
  far.png    transparent: mountains, skyline, far hills (indoors: things on the wall, window frames)
  mid.png    transparent: the main subject (yurts, houses, stalls, desks...)
  near.png   transparent: the ground in front, cars, benches, furniture in front
  fg.png     transparent: framing props, grass, rain and snow in front
  full.jpg   all layers stacked
  plate.json {name, about, biome, variant, time, weather, season, palette, seed, interior, size, layers:[{file, layer, z, parallax}]}
```

All PNGs are 1920x1080. Layers carry a soft shadow on what is behind them, and lit windows and lamps carry their glow.
`parallax` in `plate.json` is how far a layer moves for a camera move of 1 (sky 0.04, far 0.18, mid 0.42, near 0.72,
fg 1.1). For a pan, scale the layers up by about 1.08 so the edges never show (see `parallax.py`).

The PNGs in `plates/` are 256-colour (about 8x smaller than RGBA, and the felt grain hides the quantisation). For
full-colour RGBA layers run the generator with `PLATES_PNG=full`.

The middle of the near layer is left open on purpose: that is where characters stand.

## Run

```
pip install numpy scipy pillow
python plates.py --one steppe --variant 1 --time golden --weather clear --season summer --palette felt --seed 3 --out out/
python plates.py --all --out plates/ --jobs 4      # the whole catalogue (catalog.py), skips plates already there
python sheets.py plates/ sheets/                   # contact sheets of full.jpg
python parallax.py demo.mp4 plates/<a> plates/<b>  # a parallax pan across plates
```

Parameters:

- `biome`: see the list below
- `time`: dawn, day, golden (golden hour), dusk, night (stars, moon, lit windows, street lamps, car lights)
- `weather`: clear, clouds, rain, snow (forces winter), fog
- `season`: spring, summer, autumn, winter (grass, leaves, bare trees, snow on roofs)
- `palette`: felt, pastel, vivid, warm, cool, muted
- `seed`: placement of clouds, trees, houses, animals, lit windows
- `variant`: composition (3 per place, 4 for steppe and mountains)

## Places

Outdoors: `steppe` (yurts, horses), `mountains` (Tian Shan-like peaks, spruce, a lake, a pasture yurt), `almaty`
(a city at the foot of a snowy range, poplar avenues, no real landmarks), `courtyard` (Soviet panel blocks,
playground, laundry, garages), `bazaar`, `desert` (dunes, camels, an oasis, saxaul), `birch_forest`, `pine_forest`,
`lake`, `sea_coast` (lighthouse), `village`, `farm`, `downtown` (big city, best at night), `suburb`, `highway`,
`railway`, `port`, `park`, `school_yard`, `construction`, `jungle`, `arctic` (aurora at night).

Far places: `space`, `moon`, `mars` (blue sunset at dusk, dust storm in fog), `underwater`, `cave`.

Interiors: `tv_studio`, `office`, `boss_office`, `kitchen`, `living_room`, `bedroom`, `classroom`, `hospital`,
`courtroom` (no state symbols), `cafe`, `metro`, `bus_interior`, `airplane`, `lab`, `server_room`, `gov_counter`
(no symbols), `shop`. Windows in interiors show the time of day outside; lamps light up at dusk and night.

## Expansion (puppet-plates-more): 52 more places, 353 plates

Every place from the writers' room `places.md` that the first library did not cover, Central Asian settings, and studio
sets. Same layers, felt pass and `plate.json`; each place has 3 compositions across 6 (interiors, studios) or 8-9
(outdoors) looks with day and night.

- `studios.py` (12): interview_studio, talkshow, news_desk, game_show, podcast, weather_studio (map with no borders or
  names), press_room (no emblem), cooking_show, pitch_stage, unboxing_desk, wedding_hall (toi hall with a stage),
  aquarium_studio
- `rooms2.py` (15): dining, meeting_room, hr_room, office_kitchen, therapy, clinic, vet, apartment_empty, call_center,
  gym, supermarket, stairwell, bathroom, bank, museum
- `kz.py` (13): aul, yurt_interior (kerege, uyk, shanyrak open to the sky, tus kiiz, syrmak, dastarkhan), gorge,
  city_dusk (a city under a snowy range, no landmarks), business_lobby, dastarkhan_kitchen, service_center (queue
  screens of unreadable dots), auditorium, dacha, bus_stop (mostly winter), station, caspian, taxi (night and day)
- `outdoors2.py` (12): street, crossroads, river, new_building, airport (baggage claim), beaver_dam, burrow, anthill,
  savanna, ice_floe, oil_depot, beach_pier

Each module has a `LOOKS` dict (variants, looks) that `catalog.py` adds to the catalogue. `sheets/more_*.jpg` are the
contact sheets of the new plates (`python sheets.py plates/ sheets/ --only <biomes> --prefix more`), and
`parallax_demo_more.mp4` is a 15-second pan over 8 of them (aul, yurt interior, gorge, city at dusk, dastarkhan
kitchen, toi hall, talk show, night taxi).

Places from `places.md` mapped to existing biomes: pl_forest -> pine_forest, pl_desert -> desert, pl_kitchen_home ->
kitchen, pl_livingroom -> living_room, pl_open_space -> office, pl_court -> courtroom, pl_govt_window -> gov_counter,
pl_school -> classroom, pl_park -> park, pl_yard -> courtyard, pl_farm -> farm, pl_director_office -> boss_office,
pl_server_room -> server_room, pl_construction -> construction. Almaty-like city, Soviet courtyard, bazaar and the
railway line were already there (almaty, courtyard, bazaar, railway); city_dusk and station add the dusk view and the
platform.

Known gaps in the expansion: studios have no windows, so their day/night looks differ only in tint; the three street
variants share one facade style; station canopy columns cut the view into strips; caspian cliffs are blocky and v2 is
sparse; taxi front seats take much of the frame; yurt interior's white tablecloth dominates; dacha beds turn into white
bars in snow; animals (giraffes, zebras, horses) are simple silhouettes; some floors (oil depot, airport, pitch stage,
office kitchen v2) are left bare for puppets.

## Files

- `plates.py`: layers, the felt pass per piece, time/weather/season/palette colour grading, sky, rain, snow, fog, output
- `props.py`: shared props (trees, mountains, houses, panel blocks, towers, yurts, horses, camels, cars, buses...)
- `scenes.py`: the outdoor and far biomes
- `rooms.py`: the interiors
- `catalog.py`: the list of plates that `--all` renders
- `sheets.py`, `parallax.py`: contact sheets and the parallax demo
- `felt.py`: a verbatim copy of `extella-mult/handler/felt.py` (MIT) so the folder runs on its own

## The first library (330 plates)

Outdoors, 9 plates each (every time of day, clear/clouds/rain/snow/fog, four seasons, several palettes): steppe,
mountains, almaty, courtyard, bazaar, desert, birch_forest, pine_forest, lake, sea_coast, village, farm, downtown,
suburb, highway, railway, port, park, school_yard, construction, jungle, arctic (22 x 9 = 198).
Far places, 6 each: space, moon, mars, underwater, cave (30). Interiors, 6 each, 17 rooms (102).

`sheets/` has contact sheets of every `full.jpg`; `parallax_demo.mp4` is a 10-second pan over five plates.

## What to improve next

- Animals and vehicles are simple silhouettes; horses and camels read at mid size but would gain from a second pose
  and nicer heads.
- Fog is a uniform veil; rain has no puddles or wet reflections; snow does not pile on props other than roofs and pines.
- Interiors are flat-on views (no perspective walls); metro, bus and airplane are side views only.
- Some places repeat the same skeleton across variants (school yard, server room, shop); more layout variants per place
  would make 9-12 truly different plates each.
- Big empty floor or yard areas are left for characters on purpose, but some (school yard, port quay) look bare without them.
- 256-colour PNGs show slight blotching on large soft gradients; use `PLATES_PNG=full` when size does not matter.
