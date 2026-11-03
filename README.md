# Extella Mult

Extella is an extensible software environment that connects AI models, software tools and devices into working systems. Its core lets you configure and change how each module runs, from document processing to controlling sensors and robots.

Extella Mult is an Extella agent that makes short felt cartoons from a request in plain words: "a birthday cartoon for my daughter Aliya, she loves cats", "a fox cub gets lost in the forest and grandpa finds it with a lantern". The agent does not write drawing code. It writes a short program in SCENE, a small language for cartoons, and a handler on your computer checks it and renders an mp4 with music.

The look is felt and plasticine: every tree, house and character part is a cut-out with a soft rounded edge, a fibre texture and a shadow. It runs on any computer with Python, no GPU.

| | |
|---|---|
| characters | girl, boy, mom, dad, granny, grandpa, cat, fox, dog, bunny, bear, bird; walk, run, wave, jump, sit, dance, look up; things in hand |
| places and things | 32: skies (day, dawn, sunset, night, space), hills, mountains, forest, river and bridge, houses, a school, a rainbow, the sea with a boat and a lighthouse, snow and a snowman, a planet and a rocket, a room with a bed, a lamp, a table, a cake and gifts |
| effects | snow, rain, hearts, sparkles, falling leaves, bubbles, balloons, butterflies, music notes, smoke |
| voice | spoken lines through ElevenLabs with your own key, six voices, music ducks under speech; or your own recordings |
| ready stories | eight templates: birthday, park, school, space, winter, sea, bedtime, friends |
| download | 0.3 MB |
| speed | about 35 seconds for a 16-second film on an Apple M-series laptop (v3; v2 took about 5 minutes) |

## In numbers

From our tests on 3 November 2026, agent on DeepSeek-V4-Flash:

- a request that fits a template gives a film with **no new lines**: the agent fills the hero, the pet and the title;
- a new story ("a fox cub lost in the forest, grandpa with a lantern, granny at home") took **27 lines** of SCENE and passed the check on the first try;
- the checker answers in words, so the agent can fix its own mistakes: `line 18: 'from' and 'to' go together`.

## Install

In Extella, run the expert `mult_install` on your device. It downloads `extella-mult-2d.tar.gz` from this repository's release, installs numpy, scipy, Pillow and an ffmpeg binary, registers the `cspl=scene` handler and renders a self-test scene.

Without Extella:

```
pip install numpy scipy pillow imageio-ffmpeg
python -m handler.main film.scene --check
python -m handler.main film.scene --out film.mp4
```

## Files

- `LANGUAGE.md`: the SCENE language in felt style, generated from the handler's own descriptions
- `handler/`: parser, checker, the felt pass (`felt.py`), felt elements, characters and effects, audio, ffmpeg muxing
- `extella/scene_handler.py`: the `cspl=scene` handler; `extella/mult_install.fython`: the installer expert
- `extella/templates/`: eight felt stories with their parameters
- `extella/prompts/system_prompt.md`: the agent's instructions
- `tools/`: building the release bundle

## Limits

- Characters move along the ground line; there is no speech or lip sync.
- The agent's sense of composition is still uneven: it sometimes makes props too small or puts them in odd places. A composition guide in its concepts and the automatic depth order help.
- The vocabulary is what is listed in `LANGUAGE.md`; anything else the agent should offer to replace and ask.

## Licences

- Code: MIT, see `LICENSE`.
- Font: Caveat, SIL Open Font License 1.1 (`assets/fonts/OFL.txt` in the bundle).
