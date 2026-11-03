# Extella Mult

Extella is an extensible software environment that connects AI models, software tools and devices into working systems. Its core lets you configure and change how each module runs, from document processing to controlling sensors and robots.

Extella Mult is a pair of Extella agents that make short animated films from a request in plain words. The agent does not write drawing code. It writes a short program in SCENE, a small language for cartoons, and a handler on your computer checks it and renders an mp4 with music and sound.

| | Extella Mult 2D | Extella Mult 3D |
|---|---|---|
| look | flat drawn | low-poly 3D, rendered in Blender |
| characters | a fox and a cat, about 20 drawn backgrounds, paper effects | 582 CC0 models by Quaternius: 51 people, animals, cute creatures, monsters, robots, sea life, trees, buildings, space |
| needs | Python 3.10+ | Python 3.10+ and Blender 4.x (the installer downloads it) |
| download | 0.3 MB | 134 MB |
| speed (Apple M-series) | about 1 min for 15 s of film | 1 to 3 min for 15 s of film |

## What it looks like in numbers

From our tests on 3 November 2026, agent on DeepSeek-V4-Flash:

- a request that fits one of the ten templates ("a cowboy walks a wolf in the park, then night falls, title Moon") gives a film with **no new lines**: the agent fills four parameters;
- a new request takes **12 to 44 lines** of SCENE and one or two checks; the checker answers in words, e.g. `line 6: fox is a 2d actor, the film is style=3d; do not mix styles`;
- for comparison, a large model asked to make a similar one-minute film in plain Python wrote about 1,000 lines.

## Install

In Extella, run the expert `mult_install` on your device:

```
run_expert mult_install {"kind": "2d"}
run_expert mult_install {"kind": "3d"}
```

It downloads the bundle from this repository's release, checks its SHA-256 when given, installs numpy, scipy, Pillow and an ffmpeg binary, finds or downloads Blender for `3d`, registers the `cspl=scene` handler and runs a self-test.

Without Extella:

```
pip install numpy scipy pillow imageio-ffmpeg
python -m handler.main film.scene --check
python -m handler.main film.scene --out film.mp4
```

## Files

- `handler/`: the SCENE language: parser, checker, 2d drawing, 3d shots in Blender (`blender_scene.py`), audio, ffmpeg muxing
- `LANGUAGE.md`: the language reference
- `extella/scene_handler.py`: the `cspl=scene` handler; `extella/mult_install.fython`: the installer expert
- `extella/templates/`: ten template films with their parameters
- `extella/prompts/`: the instructions of the two agents
- `tools/`: building the 3d catalog and the release bundles

## Limits

- The 2d vocabulary is small. People, animals and cities are 3d only.
- Characters move along one stage line; there is no lip sync or speech.
- On a server without a GPU, 3d rendering is slow.
- The agent sometimes replaces what it cannot draw instead of asking. The checker catches unknown words, but not every change of meaning.

## Licences

- Code: MIT, see `LICENSE`.
- 3d models: CC0 1.0 by Quaternius (quaternius.com), taken from OpenGameArt. Each pack's licence file is inside the 3d bundle.
- Font: Caveat, SIL Open Font License 1.1.
