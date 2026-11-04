"""Pushes agent/concepts.json (from build_vocabulary.py) and agent/instructions.md to an Extella agent: deletes the
agent's own PUPPET concepts and adds the new ones. Needs an Extella API token in ~/.extella/api_token.txt.
python3 tools/push_agent.py <agent_id> [--concepts-only]"""
import json, os, sys, urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = 'https://api.extella.ai'
TOKEN = open(os.path.expanduser('~/.extella/api_token.txt')).read().strip()
AGENT = sys.argv[1]
H = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + TOKEN, 'X-Agent-Id': AGENT}


def call(path, body):
    r = urllib.request.Request(API + path, data=json.dumps(body).encode(), headers=H)
    try:
        return json.loads(urllib.request.urlopen(r, timeout=300).read().decode())
    except urllib.error.HTTPError as e:
        return {'http': e.code, 'body': e.read().decode()[:400]}


C = json.load(open(os.path.join(REPO, 'agent', 'concepts.json'), encoding='utf-8'))
gone = 0
for q in ('PUPPET', 'PUPPET code characters', 'PUPPET plates', 'PUPPET formats', 'PUPPET props', 'PUPPET sounds', 'PUPPET picture sets'):
    for c in call('/api/concept/search', {'query': q, 'limit': 100}).get('results', []):
        if c.get('group_name') is None and c['concept_text'].startswith('PUPPET'):
            call('/api/concept/delete', {'concept_id': c['concept_id']}); gone += 1
ok = sum(call('/api/concept/add', {'text': t}).get('status') == 'success' for t in C)
print('concepts: removed', gone, 'added', ok, 'of', len(C))
if '--concepts-only' not in sys.argv:
    text = open(os.path.join(REPO, 'agent', 'instructions.md'), encoding='utf-8').read()
    print('instructions:', call('/api/agent/update', {'agent_id': AGENT, 'instructions': text}).get('status'))
