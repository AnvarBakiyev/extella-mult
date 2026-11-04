# Войлочные эффекты из кода

99 анимированных эффектов в войлочном стиле. Всё нарисовано кодом: numpy + Pillow + scipy, без ИИ-картинок, без платных сервисов и без готовых ассетов. Каждый кусочек проходит войлочный фильтр с тем же рецептом, что `handler/felt.py::felt_composite` из extella-mult: мягкий скос со светом сверху слева, тёмный край, ворс, пушистая кромка, мягкая тень.

Смотреть сначала: `contact_sheet.jpg` (по кадру на эффект) и `showcase.mp4` (30 секунд, все эффекты сеткой 3×3).

## Что где

| файл | что |
|---|---|
| `effects_lib.py` | библиотека: 99 функций `fx(t, params) -> RGBA`, реестр `EFFECTS` |
| `feltcore.py` | войлочный движок: фигуры, строчка, войлочный спрайт с кэшем, холст, фон для превью |
| `render.py` | рендер последовательностей, превью, `effects.json`, контактного листа и витрины |
| `seq/<name>/0000.png…` | прозрачные PNG-кадры, 24 к/с (у тумана и облаков 12 к/с), тень уже внутри альфы |
| `preview/<name>.mp4` | превью 960×540 на нейтральном войлочном фоне (петли проиграны 2–3 раза) |
| `effects.json` | имя, категория, описание, параметры, петля или нет, длительность, кадры, размер |
| `contact_sheet.jpg`, `showcase.mp4` | обзор |
| `peek.py` | быстрый просмотр кадров при разработке |

Размер: кадры 589 МБ, превью 45 МБ. PNG сжаты pngquant (палитра 256 цветов с альфой, на глаз без потерь, в 3–4 раза меньше). Полноэкранные эффекты (занавес, ирис, разрыв, туман, глитч, волны, линии скорости) хранятся в 960×540; функция при этом рисует любой размер.

## Как пользоваться

```python
import effects_lib as E

img = E.snow_light(1.25)                       # кадр в момент 1.25 с, RGBA 1920x1080
img = E.hearts_float(0.5, {"at": (0.3, 0.5), "seed": 7})   # из точки, другой случайный рисунок
img = E.render("fireworks", 2.0, {"W": 960, "H": 540})     # любой размер, всё масштабируется по высоте
scene.alpha_composite(img)                      # наложить на кадр мультика
```

Общие параметры: `seed` (детерминированно), `W`, `H`, `dur` (длина петли или разового эффекта), `at=(x, y)` в долях кадра для эффектов из точки, `size` (масштаб значков у головы), `density`/`count`, `floor` (уровень пола). У петель кадр в `t` и в `t + dur` совпадает, стык незаметен: частицы идут потоком, где каждая частица рождается на сетке времени, кратной длине петли.

Как устроено: эффект описывает кусочки векторно (многоугольники, полосы, строчка). Кусочек растеризуется с двойным сглаживанием, превращается в войлок один раз и кэшируется (по форме, размеру, квантованному углу), дальше только вклеивается. Поэтому 100–400 войлочных кусочков в кадре 1920×1080 рисуются за 0,05–0,5 с на одном ядре.

Перерендер: `python3 render.py` (всё, 4 процесса, ~25 минут) или `python3 render.py snow_light hail` (отдельные).

## Эффекты

### Погода (16)

| эффект | что | петля | с | параметры |
|---|---|---|---|---|
| `rain_light` | Light felt rain: thin blue drops falling straight down. | да | 2.0 | density=70 |
| `rain_heavy` | Heavy felt rain: dense slanted drops with little splash crowns on the floor. | да | 2.0 | density=340, floor=0.92 |
| `rain_wind` | Wind-driven rain: long drops at a steep angle, gusting. | да | 2.0 | density=150 |
| `snow_light` | Gentle snowfall: soft round felt flakes swaying as they fall. | да | 4.0 | density=70 |
| `snow_heavy` | Heavy snow: large six-arm felt crystals turning slowly among many small flakes. | да | 4.0 | density=110 |
| `blizzard` | Blizzard: dense fast snow driven sideways, wind haze bands and a white veil. | да | 2.0 | density=320 |
| `fog_drift` | Fog: layers of sheer felt mist drifting sideways at different speeds (parallax). | да | 6.0 |  |
| `wind_leaves` | Wind with leaves: autumn leaves tumbling across the frame with curly wind strokes. | да | 3.0 | density=42 |
| `wind_gusts` | Cartoon wind gusts: curly white felt strokes sweeping across. | да | 2.0 |  |
| `lightning_flash` | Thunderstorm: dark felt cloud, a stitched yellow bolt strikes twice with white flashes. | да | 3.0 | at=[0.5, 0.18] |
| `hail` | Hail: pale felt pellets falling hard and bouncing on the floor. | да | 2.0 | density=60, floor=0.9 |
| `sandstorm` | Sandstorm: ochre grains and dusty felt bands streaming sideways under a sandy veil. | да | 2.0 | density=260 |
| `rain_cloud` | A single felt rain cloud bobbing at the top with rain falling from it. | да | 2.0 | at=[0.5, 0.2] |
| `sun_rays` | Felt sun: a stitched disc with alternating rays slowly turning and breathing. | да | 4.0 | at=[0.5, 0.45] |
| `rainbow_grow` | A felt rainbow sweeps across from left to right, puffy clouds pop at its ends. | нет | 3.0 | at=[0.5, 0.82] |
| `clouds_drift` | Puffy white felt clouds drifting across the sky, looping seamlessly. | да | 6.0 |  |

### Огонь и дым (10)

| эффект | что | петля | с | параметры |
|---|---|---|---|---|
| `campfire` | Campfire: crossed felt logs and stones, flickering three-colour flames, rising embers and glow. | да | 2.0 | at=[0.5, 0.82], size=1.25 |
| `candle` | Candle: stitched cream felt candle with a swaying teardrop flame and soft glow. | да | 2.0 | at=[0.5, 0.62], size=1.25 |
| `explosion_puff` | Cartoon explosion: spiky orange flash, then grey smoke puffs balloon out and fade, debris flies. | нет | 2.5 | at=[0.5, 0.55] |
| `steam` | Steam: soft white puffs curling up from a point (cup, kettle, pot) and dissolving. | да | 3.0 | at=[0.5, 0.75], size=1.6 |
| `chimney_smoke` | Chimney smoke: grey puffs rising and drifting with the wind, growing as they go. | да | 4.0 | at=[0.62, 0.62] |
| `dust_cloud` | Dust cloud: beige felt puffs burst out sideways along the ground (skid, landing, stomp). | нет | 2.0 | at=[0.5, 0.85] |
| `embers` | Embers: tiny glowing orange felt sparks rising and wavering. | да | 3.0 | density=70 |
| `fire_edge` | A wall of felt flames flickering along the bottom edge of the frame. | да | 2.0 |  |
| `smoke_puffs` | Billowing smoke: puffy felt clouds bursting out sideways and up from a point (launch, crash). | да | 3.0 | at=[0.5, 0.85] |
| `poof_vanish` | Cartoon poof: a ring of white felt puffs and little stars pops out and fades (disappearing). | нет | 2.0 | at=[0.5, 0.55], size=1.25 |

### Вода (8)

| эффект | что | петля | с | параметры |
|---|---|---|---|---|
| `splash` | Water splash: a felt crown rises and blue drops shoot up and fall back. | нет | 2.0 | at=[0.5, 0.8] |
| `ripples` | Ripples: concentric felt rings spreading on a water surface and fading. | да | 3.0 | at=[0.5, 0.75] |
| `bubbles` | Bubbles: light blue felt bubbles with a white glint rising and wobbling. | да | 3.0 | density=22, at=[0.5, 0.95] |
| `drip` | Drip: a drop swells under a point, stretches, falls and makes a small splash ring. | да | 3.0 | at=[0.5, 0.2], floor=0.85, size=1.6 |
| `waves_edge` | Sea edge: three layers of felt waves rolling along the bottom with a stitched foam line. | да | 3.0 |  |
| `fountain` | Fountain: a jet of felt water drops arcing up and falling back, endlessly. | да | 2.0 | at=[0.5, 0.85] |
| `puddle_splashes` | Rain on the ground: little splash crowns and rings popping up all over the floor. | да | 2.0 | density=40, floor=0.78 |
| `tears_stream` | Cartoon crying: two arcing streams of felt tear drops spurting from the eyes. | да | 1.5 | at=[0.5, 0.42], gap=0.09, size=1.6 |

### Праздник (8)

| эффект | что | петля | с | параметры |
|---|---|---|---|---|
| `confetti_fall` | Confetti: rectangles, dots, triangles and stars fluttering down in festive colours. | да | 3.0 | density=120 |
| `confetti_burst` | Confetti cannons: two bursts from the bottom corners shoot confetti up, it flutters down. | нет | 3.0 | count=90 |
| `fireworks` | Fireworks: felt rockets climb on a puff trail and burst into rings of stars and dots that droop and fade. | да | 3.0 |  |
| `balloons_rise` | Balloons: shiny felt balloons on strings rising and swaying. | да | 4.0 | density=8 |
| `streamers_fall` | Streamers: wavy felt ribbons twisting as they fall. | да | 3.0 | density=22 |
| `sparkle_burst` | Sparkle burst: four-point felt stars shoot out from a point, twinkle and shrink. | нет | 2.0 | at=[0.5, 0.5], size=1.6 |
| `bunting` | Bunting: a garland of stitched felt flags across the top, swaying in the breeze. | да | 3.0 |  |
| `stars_shower` | Star shower: golden stitched felt stars tumbling down and twinkling. | да | 3.0 | density=34 |

### Комикс-знаки (20)

| эффект | что | петля | с | параметры |
|---|---|---|---|---|
| `speed_lines_radial` | Focus speed lines: felt wedges flicking in from the frame edges toward the centre. | да | 1.0 | at=[0.5, 0.5] |
| `motion_lines` | Whoosh lines: horizontal felt strips streaking past (something moving fast). | да | 1.0 | density=16 |
| `impact_star` | Impact: a spiky red-yellow felt burst pops with overshoot and shakes, small stars fly off. | нет | 1.5 | at=[0.5, 0.5], size=1.25 |
| `sweat_drops` | Nervous sweat: light-blue felt drops pop off the side of a head and fall. | да | 2.0 | at=[0.56, 0.36], size=1.6 |
| `anger_vein` | Anger mark: a red four-part felt "vein" cross pulsing next to a head. | да | 1.0 | at=[0.6, 0.3], size=1.6 |
| `question_marks` | Confusion: felt question marks pop up one by one over a head and bob. | да | 3.0 | at=[0.5, 0.25], size=1.6 |
| `exclamation` | Surprise: a big felt exclamation mark pops up with overshoot and quivers, with small burst lines. | нет | 2.0 | at=[0.5, 0.25], size=1.6 |
| `zzz` | Sleeping: felt Z letters drift up and to the side, growing and fading. | да | 3.0 | at=[0.55, 0.35], size=1.6 |
| `hearts_float` | Love: stitched pink felt hearts float up and sway. | да | 3.0 | density=8, at=[0.5, 0.6], size=1.6 |
| `heart_beat` | Heartbeat: one big stitched felt heart thumping lub-dub. | да | 2.0 | at=[0.5, 0.5], size=1.25 |
| `dizzy_stars` | Dizzy: little felt stars circling around a head on a tilted orbit. | да | 1.5 | at=[0.5, 0.3], size=1.6 |
| `dizzy_swirl` | Dizzy swirl: felt spirals spinning (over a head or as eyes). | да | 1.0 | at=[0.5, 0.35], gap=0.07, size=1.6 |
| `idea_bulb` | Idea: a felt light bulb pops up over a head, lights up yellow with flashing rays and a glow. | нет | 2.0 | at=[0.5, 0.25], size=1.6 |
| `music_notes` | Music: felt notes and beamed pairs float up along a wavy path. | да | 3.0 | at=[0.5, 0.55], size=1.6 |
| `shock_lines` | Shock: short felt strokes radiating around a head and vibrating. | да | 1.0 | at=[0.5, 0.4], size=1.6 |
| `anger_steam` | Fuming: white steam puffs blasting out of both sides of a head in bursts. | да | 1.5 | at=[0.5, 0.4], gap=0.11, size=1.6 |
| `grawlix_cloud` | Cursing: a jittering cluster of felt symbols (spiral, bolt, star, cross) over a head. | да | 1.0 | at=[0.5, 0.25], size=1.6 |
| `shine_glint` | Shine: twinkling four-point glints popping on a shiny object (clean, new, sparkling). | да | 2.0 | at=[0.5, 0.5], size=2.6 |
| `thought_bubble` | Thinking: three small felt circles pop in a trail, then an empty cloud bubble puffs up. | нет | 2.0 | at=[0.62, 0.3], size=1.25 |
| `speech_bubble_pop` | Speech bubble: an empty stitched felt speech bubble with a tail pops in and breathes. | нет | 2.0 | at=[0.55, 0.3], size=1.25 |

### Деньги (5)

| эффект | что | петля | с | параметры |
|---|---|---|---|---|
| `bills_fall` | Money rain: blank green felt banknotes fluttering and flipping down. | да | 3.0 | density=30 |
| `coins_rain` | Coin rain: stitched gold felt coins spinning as they fall. | да | 2.0 | density=40 |
| `coin_burst` | Jackpot: a fountain of spinning gold felt coins bursts up and falls back. | нет | 2.5 | at=[0.5, 0.9], count=60 |
| `coin_stack_grow` | Savings: gold felt coins drop one by one onto three growing stacks. | нет | 3.0 | at=[0.5, 0.85] |
| `gems_rain` | Treasure: faceted felt gems falling, turning and twinkling. | да | 3.0 | density=22 |

### Магия (7)

| эффект | что | петля | с | параметры |
|---|---|---|---|---|
| `glitter_trail` | Glitter trail: a bright felt star flies a figure-eight leaving twinkling sparkles that drift down. | да | 3.0 | at=[0.5, 0.45] |
| `stars_swirl` | Star vortex: felt stars spiralling around a centre, those near the middle shrink in. | да | 3.0 | at=[0.5, 0.5] |
| `portal` | Magic portal: rotating felt rings in purple and teal with spiral arms, pulsing, sparkles drawn in. | да | 3.0 | at=[0.5, 0.5] |
| `magic_dust` | Magic dust: tiny glowing felt motes rising and twinkling in a column. | да | 3.0 | at=[0.5, 0.85], width=0.35 |
| `orbiting_orbs` | Orbiting orbs: glowing felt balls circling a centre on a tilted orbit, with fading trails. | да | 3.0 | at=[0.5, 0.5], size=1.6 |
| `shooting_star` | Shooting star: a felt star streaks diagonally across the sky with a tapering dotted tail. | да | 2.0 |  |
| `twinkle_field` | Night twinkle: felt stars across the top of the frame twinkling at different rhythms. | да | 3.0 | density=40 |

### Техника (8)

| эффект | что | петля | с | параметры |
|---|---|---|---|---|
| `glitch_blocks` | Glitch: felt blocks in cyan, magenta and off-white flicker and jump in horizontal bands. | да | 2.0 |  |
| `scanlines` | Old screen: dark felt scanlines with a lighter band rolling down the frame. | да | 2.0 |  |
| `loading_spinner` | Loading spinner: a ring of felt dots with a bright dot chasing around (no text). | да | 1.0 | at=[0.5, 0.5], size=1.6 |
| `notification_dots` | Notifications: red felt badge dots pop in with a bounce at several spots and pulse. | да | 3.0 |  |
| `signal_waves` | Signal: felt arcs pulsing outward one after another from a dot (wireless, broadcast). | да | 1.5 | at=[0.5, 0.6], size=1.6 |
| `typing_dots` | Typing indicator: three felt dots bouncing in turn inside a soft bubble (no text). | да | 1.2 | at=[0.5, 0.5], size=1.6 |
| `data_blocks` | Data rain: columns of small green felt squares streaming down and fading. | да | 2.0 | density=60 |
| `radar_sweep` | Radar: a stitched felt radar disc with a rotating sweep wedge and blips lighting up. | да | 3.0 | at=[0.5, 0.5] |

### Природа (10)

| эффект | что | петля | с | параметры |
|---|---|---|---|---|
| `butterflies` | Butterflies: felt butterflies with spotted wings flutter along looping paths. | да | 4.0 | count=5, size=1.25 |
| `fireflies` | Fireflies: little felt bugs with blinking warm glows wandering in the dusk. | да | 4.0 | count=26 |
| `birds_flock` | Bird flock: small felt birds flapping across the sky in a loose V. | да | 4.0 |  |
| `petals_fall` | Petals: pink cherry petals tumbling and drifting down. | да | 3.0 | density=40 |
| `apples_fall` | Falling apples: shiny felt apples drop, bounce on the ground and roll away. | да | 3.0 | floor=0.86 |
| `dandelion_seeds` | Dandelion seeds: fluffy felt-and-thread parachutes floating up and across on the breeze. | да | 4.0 | density=16 |
| `bees` | Bees: striped felt bees buzzing around in loops with blurry flapping wings. | да | 3.0 | count=4, at=[0.5, 0.45], size=1.6 |
| `autumn_leaves` | Autumn leaves: veined felt leaves drifting down, swaying and flipping. | да | 4.0 | density=22 |
| `grass_edge` | Grass: a fringe of felt grass blades along the bottom, swaying in a breeze wave. | да | 3.0 |  |
| `flowers_pop` | Flowers: stems grow up from the ground and felt blossoms pop open one after another. | нет | 3.0 | floor=0.95 |

### Переходы как эффекты (7)

| эффект | что | петля | с | параметры |
|---|---|---|---|---|
| `curtain_close` | Theatre curtain closes: red velvet felt drapes with gold stitched hems slide in from both sides. | нет | 2.0 |  |
| `curtain_open` | Theatre curtain opens: red felt drapes part to reveal the scene. | нет | 2.0 |  |
| `iris_close` | Iris out: a dark felt mask with a hand-stitched edge closes in a circle (focus at at=). | нет | 2.0 | at=[0.5, 0.5] |
| `iris_open` | Iris in: the stitched felt mask opens from a point to reveal the scene. | нет | 2.0 | at=[0.5, 0.5] |
| `page_tear` | Page tear: a felt sheet covering the frame rips along a jagged line and both halves fall away. | нет | 2.5 |  |
| `wipe_stitched` | Felt wipe: a felt panel with a zig-zag stitched leading edge slides across and covers the frame. | нет | 1.5 |  |
| `patches_cover` | Patchwork cover: stitched felt squares drop in tile by tile until the frame is covered. | нет | 2.5 |  |

