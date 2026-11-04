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

## Extella Puppet (v4): satirical felt-puppet episodes

A second agent on the same handler, for grown-ups: deadpan TV formats, an absurd situation played straight, an unexpected last line. The language is [PUPPET](LANGUAGE-PUPPET.md). The library comes in three free packs, installed together by the expert `puppet_install` (or pick with `packs=core,premium`):

| pack | what is inside | licence |
|---|---|---|
| **premium** | 67 generated picture sets: 24 talking characters (mouth and blink frames) and 43 places. The best-looking ones | ours, free |
| **core** | 383 felt characters built by code (155 with full bodies that walk and gesture), 683 places, 99 animated effects, 273 props | ours, free |
| **community** | 227 CC0 sounds, 68 music tracks, OFL fonts; see `ATTRIBUTION.md` inside | CC0 / OFL, credited |

The agent works in three calls, each under the platform's 120-second limit: write an episode; `render ep_<name>`; `status ep_<name> <job>`. A 40-second film renders in about a minute on an Apple M-series laptop.

### The library is open to contributions

`library/` in this repository holds the picture sets, the media and the sources of the code packs; the rendered pictures of the code packs live in the release archives. Add a set, a sound or a character by pull request: the format, the licence (CC0 / CC BY / OFL) and the check are in [CONTRIBUTING.md](CONTRIBUTING.md). A merged pull request reaches users with their next install, and `tools/build_vocabulary.py` puts it into the agent's vocabulary.

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

## Installed into your own agent?

The store offers two ways to install: **as a new agent** (recommended) and **into an agent you already have**. The second way copies only the rules, the concepts and the experts; the system prompt, the model and the tools stay those of your agent, so Puppet does not work until you set them by hand:

1. Agent settings, system prompt: paste [agent/instructions.md](agent/instructions.md).
2. Tools: switch on the Extella tools `list_rules`, `search_concepts`, `list_concepts`, `search_experts`, `get_expert`, `run_expert`, `check_task`, `save_expert`.
3. Model: any model with tool calls; we use DeepSeek-V4-Flash.

Or reinstall the listing choosing "new agent": everything comes set up.

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
