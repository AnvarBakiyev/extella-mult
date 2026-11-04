#!/usr/bin/env python3
"""Pack concepts/*.md into concepts.jsonl for the agent's concept store and check the size limit.

  python3 tools/build_concepts.py            # writes concepts.jsonl, fails if a concept is 1200+ characters
Each record: {"id": "puppet-05-dialogue-timing", "title": ..., "tags": [...], "text": <the whole file>}.
"""
import json
import sys
from pathlib import Path

PACK = Path(__file__).resolve().parent.parent
LIMIT = 1200


def records():
    for p in sorted((PACK / 'concepts').glob('*.md')):
        text = p.read_text().strip()
        lines = text.splitlines()
        title = lines[0].lstrip('# ').strip()
        tags = [t.strip() for t in lines[1].split(':', 1)[1].split(',')] if lines[1].startswith('tags:') else []
        yield p, dict(id='puppet-' + p.stem, title=title, tags=tags, text=text)


def main():
    bad = 0
    out = []
    for p, r in records():
        n = len(r['text'])
        flag = 'OK ' if n < LIMIT else 'TOO LONG'
        bad += n >= LIMIT
        print(f'{flag} {n:5d} {p.name}')
        out.append(json.dumps(r, ensure_ascii=False))
    (PACK / 'concepts.jsonl').write_text('\n'.join(out) + '\n')
    print(f'{len(out)} concepts -> concepts.jsonl')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
