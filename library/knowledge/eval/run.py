#!/usr/bin/env python3
"""Ask an agent for a program per request and save it as outputs/R01.scene ... (no service is called by default).

  python3 eval/run.py --cmd "python3 my_agent.py" --out outputs      # the command reads the request on stdin
  python3 eval/run.py --print                                         # just print the 30 requests
The command's stdout may contain prose or ``` fences; the program is cut out from the line that starts
with `film` to the last PUPPET statement. Then: python3 eval/score.py --dir outputs
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

EVAL = Path(__file__).resolve().parent
STATEMENT = re.compile(r'^\s*(film|shot|say|voice|text|prop|music|fade|#)')


def extract(out):
    lines = out.replace('```puppet', '```').splitlines()
    start = next((i for i, l in enumerate(lines) if l.strip().startswith('film')), None)
    if start is None:
        return out
    while start > 0 and lines[start - 1].strip().startswith('#'):
        start -= 1  # keep the header comments
    body = [l for l in lines[start:] if STATEMENT.match(l) or not l.strip()]
    return '\n'.join(body).strip() + '\n'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cmd')
    ap.add_argument('--out', default='outputs')
    ap.add_argument('--only', nargs='*')
    ap.add_argument('--print', action='store_true')
    a = ap.parse_args()
    reqs = [json.loads(l) for l in (EVAL / 'requests.jsonl').read_text().splitlines()]
    if a.print or not a.cmd:
        for r in reqs:
            print(f"{r['id']}  {r['request']}")
        return
    Path(a.out).mkdir(exist_ok=True)
    for r in reqs:
        if a.only and r['id'] not in a.only:
            continue
        res = subprocess.run(a.cmd, shell=True, input=r['request'], capture_output=True, text=True, timeout=600)
        Path(a.out, r['id'] + '.scene').write_text(extract(res.stdout))
        print(r['id'], 'saved' if res.returncode == 0 else f'exit {res.returncode}')


if __name__ == '__main__':
    main()
