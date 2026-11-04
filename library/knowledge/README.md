# Puppet agent knowledge pack

Knowledge for a **small** model (DeepSeek-V4-Flash class) that writes PUPPET programs for Extella Puppet: short concept texts to retrieve, 40 worked few-shot programs, and an evaluation with an automatic scorer. Built from `puppet-handler-base` (the language, `handler/puppet.py`) and `puppet-writers-room` (25 formats, 150 scripts, cast, places). Nothing here calls a paid service.

```
concepts/           24 concept texts, English, imperative, each under 1200 characters
concepts.jsonl      the same, one JSON record per concept (built by tools/build_concepts.py)
fewshot/            40 PUPPET programs converted from the best writers-room scripts
eval/requests.jsonl 30 user requests in Russian with expected formats
eval/rubric.md      the rubric (5 criteria × 2 points)
eval/score.py       automatic scorer
eval/run.py         optional: ask an agent for each request and save the programs
tools/puppet_check.py  syntax check with the handler's own parser (stand-in sets when the device has none)
tools/convert.py    writers-room script → PUPPET program (how fewshot/ was made)
tools/stubs.py      stand-in set library: ch_/pl_ codes + the 63 device sets, one voice per character
vendor/handler/     puppet.py, audio.py, config.py copied unchanged from puppet-handler-base (d9f52dd)
```

Setup: Python 3.9+. `pip install numpy pillow scipy` is recommended; without them the checker substitutes empty modules, since parsing needs none of them.

## Sets: an assumption

The few-shot programs and concepts name sets after the writers-room codes: `ch_dina`, `ch_salmon` … are talking character sets (with a mouth), `pl_tv_studio`, `pl_court` … are silent place sets, and `ad_cream` is the existing commercial pack shot. Most of these sets do not exist on the device yet. Until they do, check programs with the stand-in library (`--stub-sets`, which is the default when `~/extella-mult/assets/puppet` is missing). When the real sets arrive, either keep these names or rename them in one pass (`sed -i 's/\bch_dina\b/news_anchor/g' fewshot/*.scene`) and add the new names to the catalog concept your agent retrieves.

## 1. Loading the concepts into the agent

The agent's dictionary is built by `puppet_concepts.py` (see ARCHITECTURE §3.1). Two ways:

**A. As files.** Copy `concepts/*.md` next to the concepts that `puppet_concepts.py` already reads, and let it add each file as one concept. Use the file's first line (`# PUPPET: ...`) as the title and the `tags:` line as keywords. Keep one file per concept; do not merge them. Each is short so that a retrieval of 3–5 concepts fits easily in a small context.

**B. From JSONL.**
```
python3 tools/build_concepts.py        # rebuilds concepts.jsonl, fails if any concept is 1200+ characters
```
Each line is `{"id": "puppet-05-dialogue-timing", "title": ..., "tags": [...], "text": ...}`. Load the records into the concept store with whatever upsert the platform offers, keyed by `id`, so that a rebuild replaces old versions.

**What to retrieve when.** Put `01-workflow`, `02-language` and `05-dialogue-timing` in the system prompt or always-on rules (≈3 KB together). Retrieve the rest on demand. The titles are written to match the queries the workflow tells the model to make:

| the agent needs | query | concept |
|---|---|---|
| beats of a format | `PUPPET format F07` | `16`–`23` (three or four formats each) |
| camera | `PUPPET camera grammar`, `camera per format` | `03`, `07`, `08` |
| the joke | `PUPPET joke structure`, `last line` | `09`, `10` |
| an ad block | `PUPPET commercial break` | `11` |
| forbidden content | `PUPPET safety` | `12` |
| a check error | `PUPPET fixing check errors` | `13` |
| recordings missing | `LINES_TO_RECORD` | `14` |
| a full example | `PUPPET minimal complete program` | `15` |
| self-review before check | `PUPPET common mistakes` | `24` |

**Few-shot.** Give the model 1–2 programs from `fewshot/` **of the same format** as the request (the format is in the first header line, `# format: F07 ...`). Same format matters more than a high score. The lines `# format`, `# logline` and `# why it works` are comments: the handler ignores them, the model learns from them, and the scorer reads `# format`. Good defaults, one per format:

```
F01 E004  F02 E007  F03 E015  F04 E019  F05 E026  F06 E031  F07 E038  F08 E048  F09 E049
F10 E056  F11 E066  F12 E068  F13 E075  F14 E082  F15 E087  F16 E093  F17 E098  F18 E106
F19 E109  F20 E115  F21 E124  F22 E127  F23 E134  F24 E142  F25 E148
```

Check every program yourself at any time:
```
python3 tools/puppet_check.py fewshot/*.scene          # 40/40 passed (stand-in sets)
python3 tools/puppet_check.py --device my.scene        # against the real sets on this device
```

## 2. Running the eval

1. Get one program per request into a folder, named by request id (`outputs/R01.scene` … `outputs/R30.scene`). Either run the agent by hand (`python3 eval/run.py --print` lists the requests), or wrap it in a command that reads the request on stdin and prints the program:
   ```
   python3 eval/run.py --cmd "python3 run_agent.py --stdin" --out outputs
   ```
   `run.py` cuts the program out of the agent's reply (prose and ``` fences are dropped).
2. Score:
   ```
   python3 eval/score.py --dir outputs          # table: format, timing, last line, safety, camera, total /10
   python3 eval/score.py --dir outputs -v       # plus every finding, with line numbers
   python3 eval/score.py --dir outputs --json report.json
   python3 eval/score.py outputs/R07.scene --request R07
   ```
3. Read `eval/rubric.md` for what each point means and for the human-only checks: is it funny, does the last line flip the meaning.

Reference: `python3 eval/score.py --fewshot` scores the 40 few-shot programs at 9.72/10 on average. A deliberately broken program (wrong length, long lines, a politician and a brand, flat camera) scores 0–2.

The scorer is a heuristic. It estimates speech at 2 words per second, as the handler's concepts do. Real recordings are slower (ARCHITECTURE §9.5), so the handler's real-length check after recording stays the final word on timing.

## How the few-shot programs were made

`tools/convert.py` reads a script's table. Each row becomes one shot, played by the speaker's set, or by the place set for wide shots with nobody talking. Lines start 0.3 s after the cut. A shot grows when its line needs more than words/2 s plus the 0.4 s tail. The script's camera words map to shot parameters (наезд→push, отъезд→pull, снап-зум→snap, ручная→handheld, голландский→dutch, вип→whip, панорама→pan, тряска→shake), and its music words map to the six moods. In F05, the product shots use `ad_cream` with an `[ad]` voice and a slogan `text`. The last line gets `[deadpan]` and, unless a silent shot sets it up, a snap. The 40 scripts are the editors' ten plus 30 more, so every format is covered; the "why it works" lines are in `tools/why.json`. To regenerate:
```
python3 tools/convert.py $(python3 -c "import json;print(' '.join(json.load(open('tools/why.json'))))") --why tools/why.json
```
