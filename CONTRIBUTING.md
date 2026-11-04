# Contributing to Extella Puppet

Extella Puppet grows with what people add to `library/`. Every merged pull request reaches users on their next install: the picture sets and media are taken straight from this repository, the agent's vocabulary is rebuilt from it.

## What you can add

| folder | what | how the agent uses it |
|---|---|---|
| `library/sets/<name>/` | a generated or photographed felt picture: one character or one place, a whole 16:9 shot | `shot 0-5s: <name>`; a talking set gets `say <name> "..."` |
| `library/media/sfx/`, `library/media/music/` | short sounds and music tracks (`.ogg`, `.mp3`, `.wav`) | `sfx <file>`, `music file=<file>` |
| `library/media/fonts/` | fonts (`.ttf`, `.otf`) | `text ... font=<name>` |
| `library/chars/chars/<name>/char.json` | a code-built felt character: palette and parts, drawn by `charlib.py` | `cast <name> on <plate>` |
| `library/plates/*.py`, `library/props/*.py`, `library/effects/*.py` | generators of places, props and effects | `shot ...: <plate>`, `prop <name>`, `fx <name>` |

The built pictures of the code packs (characters, plates, props, effects) are not stored in git: they are rendered from these sources and published as release archives.

## A picture set

```
library/sets/<name>/
  base.png     the frame, mouth closed, eyes open   (required, 1280x720 or 1920x1080)
  open.png     same frame, mouth open               (makes the set talk)
  mid.png      same frame, mouth half open          (smoother speech)
  blink.png    same frame, both eyes closed         (blinking)
  set.json     {"talks": true, "about": "one line: who or what, where, for which scenes", "author": "...", "license": "CC0"}
```

The variants must be the same frame pixel for pixel except the mouth or the eyes: the handler pastes only the region that differs. Names are lowercase `a-z0-9_`, English, and say what the picture is: `owl_professor`, `night_kitchen`. Look at `library/sets/fox_lawyer/` for an example.

A good set for the house style: needle-felted wool, miniature set, macro lens, shallow depth of field, warm key light, the character in the middle at a slight three-quarter angle, a microphone from the side for interview scenes, no text in the picture.

## Media

Put the file in the folder and add a line to `library/media/ATTRIBUTION.md`: source, link, licence, file name. Only CC0, CC BY, CC BY-SA or OFL (fonts). CC BY needs the author's name in that line.

## Licence of your contribution

By opening a pull request you agree that your files are published under **CC0 1.0** (or the licence you state in `set.json` / `ATTRIBUTION.md`, from the list above), and that the code is under the repository licence. Do not add pictures or sounds you do not have the right to publish; a file taken from the internet without a licence will be removed.

## Check before you push

```
python3 tools/check_library.py
```

It checks names, picture sizes, that every variant matches its base, `set.json` fields and that every media file is listed in `ATTRIBUTION.md`. The same check runs on every pull request.

## How the agent learns about your files

`python3 tools/build_vocabulary.py` reads `library/` (and the built packs when they are installed) and writes `agent/concepts.json`: the lists of sets, characters, places, props, effects, sounds and music the agent may use. The maintainers push it to the agent with `tools/push_agent.py`; a merged pull request is in the agent's vocabulary with the next push.
