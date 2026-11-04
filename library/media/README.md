# puppet-oss/media: free media for the felt-puppet renderer

This folder holds free, openly licensed media for the Python/Pillow/numpy/ffmpeg felt-puppet cartoon renderer.
Everything was collected without accounts, API keys or paid services.

- **Licences:** everything is CC0 or public domain. The only exception is `fonts/`, which uses SIL OFL 1.1 and is the normal licence for fonts. Nothing here is NC, ND, SA or "personal use only".
- **Per-file source and licence:** see `INDEX.md`.
- **Credits:** see `ATTRIBUTION.md`. CC0 does not require credit, but we give it anyway.

| folder | count | format | source |
|---|---|---|---|
| `textures/` | 80 | 2K colour-map JPG | ambientCG and Poly Haven (CC0) |
| `sfx/` | 227 | OGG Vorbis 44.1 kHz | OpenGameArt items marked CC0, including Kenney packs |
| `music/` | 68 | OGG Vorbis 44.1 kHz stereo | OpenGameArt items marked CC0, including Kenney jingles |
| `fonts/` | 13 families / 22 files | TTF + OFL.txt | google/fonts on GitHub (OFL) |
| `overlays/` | 41 | 1920x1080 RGBA PNG | generated procedurally (CC0, own work) |

## textures/

File names follow the pattern `<material>_<acg|ph>_<assetId>_2K.jpg`, for example `felt_acg_Fabric034_2K.jpg` or `knit_ph_knitted_fleece_2k.jpg`.

- Only the colour (albedo) map was kept from each PBR set. Normal, roughness and other maps were discarded.
- The source sets are published as tileable, so the textures are seamless.

Material groups:

- felt
- wool
- knit
- fleece
- burlap (hessian)
- linen
- denim
- corduroy
- velvet
- fabric (tartan, gingham, woven cloth and so on)
- carpet
- cork
- cardboard
- paper
- wood
- plywood
- plaster
- stone

How to use them:

- **Fill a puppet or set shape.** Tile the texture, then mask it with the shape's alpha:
  ```python
  tex = Image.open("textures/felt_acg_Fabric034_2K.jpg").convert("RGB")
  tile = Image.new("RGB", (W, H))
  for y in range(0, H, tex.height):
      for x in range(0, W, tex.width):
          tile.paste(tex, (x, y))
  ```
- **Recolour.** Convert to greyscale, then use `ImageOps.colorize(gray, dark, light)` to get any felt colour from one neutral swatch. Grey or white sources such as Fabric034, Fabric019 and Fabric032 work best.
- **Backgrounds.** Use cork, cardboard, kraft-like paper, plywood or plaster for sets and tables.

## sfx/

Files are named `<category>_NN.ogg`. The categories are:

- **Comedy:** whoosh, pop, boing, slip, cartoon, laugh, applause
- **Objects and devices:** cash, typewriter, keyboard, click, phone, notification, door, footsteps, camera
- **Water and weather:** splash, water, wind, rain, thunder
- **Ambience:** birds, forest, crickets, city, office (room tone and hum)
- **Signals and effects:** static, glitch, bell, gong, horn, siren, explosion, fire, rocket, magic

Processing applied to every file:

- Leading and trailing silence trimmed (threshold -55 dB).
- Long ambiences cut to at most 30 s, with a 0.3 s fade-out.
- Resampled to 44.1 kHz.
- Peak-normalised to -1 dBFS. Vorbis encoding can shift a peak by about ±0.5 dB.

How to use them:

- **Mix with ffmpeg.** Place each effect on the timeline with `adelay`, then combine with `amix`:
  ```
  ffmpeg -i video.mp4 -i sfx/boing_01.ogg -filter_complex "[1]adelay=2500|2500[a];[0:a][a]amix=inputs=2:normalize=0" ...
  ```
- **Loop an ambience.** Use `-stream_loop -1` together with `-t`. The rain, wind, water, office and city loops are made for this.
- **Add variety.** For repeated actions such as footsteps, typing or clicks, pick a random file from the category each time.

## music/

Names describe the use: `news_intro_*`, `commercial_jingle_*`, `gameshow_*`, `suspense_*`, `doc_drone_*`, `comedy_*`, `ukulele_*`, `whistling_*`, `lounge_*`, `lofi_*`, `epic_*`, `stinger_*`, `sad_piano_*`, `happy_ending_*`, `jingle_*`, `intro_*`.

- Long tracks were cut to 30–45 s excerpts with a 2.5 s fade-out. `INDEX.md` marks which files are excerpts.
- Short jingles and stingers are kept whole.
- All files are peak-normalised to -1 dBFS.

How to use them:

- **Background bed.** Play at about -18 dB under dialogue: `volume=0.12`.
- **Ducking.** Use `sidechaincompress` with the voice track as the sidechain.
- **Scene transitions and punchlines.** Use stingers and `jingle_*`.
- **Seamless loop.** `ukulele_loop` loops cleanly. Most other excerpts do not, so crossfade them with `acrossfade` if you need to loop them.

## fonts/

There is one folder per family, and each keeps its `OFL.txt`. Every font was checked to render Cyrillic (Ж щ Ё ы Я) with Pillow.

| use | fonts |
|---|---|
| Titles | Rubik, Montserrat, Unbounded, Russo One, Comfortaa, Pacifico |
| TV lower-thirds and tickers | Oswald, PT Sans, Montserrat |
| Documentary captions and newspaper props | PT Serif |
| Handwritten notes and signs | Caveat, Marck Script, Neucha, Amatic SC |

Variable fonts (`[wght]`) load in Pillow with `ImageFont.truetype(path, size)`. To pick a weight, call `font.set_variation_by_name("Bold")` or `set_variation_by_axes([700])`.

## overlays/

All overlays are 1920x1080 RGBA PNG, composited on top of each rendered frame. They were generated by this collection's script with numpy and Pillow, because no CC0 grain, leak or bokeh plates could be fetched without an account. They are our own work and released under CC0.

| file | what it is | how to apply |
|---|---|---|
| `grain_fine_loop_f00..07`, `grain_coarse_loop_f00..07` | 8-frame film-grain loops: mid-grey luminance noise, alpha 0.35 | Cycle `frame % 8`. Composite normally, or use the luminance in an overlay/soft-light blend. |
| `dust_scratches_f00..05` | Dust specks, hairs and vertical scratches | Pick a random frame every 1–3 frames for an old-film look. |
| `light_leak_01..06` | Warm or colourful edge leaks | Screen or add blend at 40–90 % opacity. Animate opacity slowly. |
| `bokeh_01..04` | Out-of-focus light discs | Screen blend for night and festive scenes. |
| `vignette_soft`, `vignette_strong`, `vignette_oval_iris` | Black alpha vignettes, including an iris-out | Normal `alpha_composite`. |
| `paper_fibre_01..03` | Paper grain and fibres, mid-grey | Overlay or soft-light blend for a paper or cut-out look. |
| `fabric_fibre_01..03` | Stray felt fibres and lint, light to heavy | Normal blend over puppets for a tactile felt look. |

Example of a soft-light blend with numpy, where `a` is the frame and `b` is the overlay luminance, both scaled 0..1:

```python
out = np.where(b < .5, 2*a*b + a*a*(1 - 2*b), 2*a*(1 - b) + np.sqrt(a)*(2*b - 1))
```

## What is not included, and why

**Sources not used**

- **Wikimedia Commons:** the API answered with rate-limit and error pages from this environment.
- **Freesound:** returns 403 without login.
- **kenney.nl:** returns 403 to scripted requests. The same Kenney packs were taken from their CC0 mirrors on OpenGameArt instead.
- **Free Music Archive:** downloads need an account.

**Licences rejected.** Many OpenGameArt items were skipped because they are CC-BY-SA, GPL, CC-BY 3.0 or OGA-BY. No CC-BY 4.0 item was needed.

**Categories missing from sfx**

- Real record scratch: only UI "scratch" clicks were found.
- Gasp.
- Phone vibration.
- Drum roll.
- Cymbal crash.
- A real cash-register "ka-ching": coin and money handling sounds are included instead.
- A dedicated office ambience: room-tone, hum and machine loops are included instead.

**Other gaps**

- **Music:** there is no CC0 piece explicitly titled "news intro". Dramatic opening themes are included instead.
- **Textures:** there is no crochet texture, and no dedicated watercolour paper or kraft paper. Paper and cardboard maps cover those uses. Poly Haven `book_pattern` has no diffuse map, so it was skipped.
