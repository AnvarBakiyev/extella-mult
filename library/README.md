# The Extella Puppet library

Everything the agent can show or play. Three packs, all free:

| pack | here in git | built, in the release archives |
|---|---|---|
| **premium** | `sets/`: 67 generated felt pictures, 24 of them talk (mouth and blink frames) | installed as `~/extella-mult/assets/puppet/` |
| **core** | `chars/`, `bodies/`, `plates/`, `props/`, `effects/`: the sources, `char.json` per character and the generators | the rendered PNGs, `puppet-core-*.tar.gz` |
| **community** | `media/`: CC0 sounds and music, OFL fonts, textures, `ATTRIBUTION.md` | installed as `~/extella-mult/assets/lib/mult/puppet-oss/media/` |

`knowledge/` and `writers-room/` are the agent's pages: the language, formats, joke structure, workflow.

To add something, read [CONTRIBUTING.md](../CONTRIBUTING.md). `python3 tools/check_library.py` checks the folder; `python3 tools/build_vocabulary.py` turns it into the agent's vocabulary.
