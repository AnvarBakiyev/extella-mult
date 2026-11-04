"""A stand-in set library so PUPPET programs can be checked without the real pictures.

Sets are named after the writers-room codes: every cast code (ch_...) is a talking set with a mouth,
every place code (pl_...) is a silent set. The 63 sets of the device (tools/device_sets.json) are added too.
Each cast code gets one fixed voice from the handler's list (VOICE below); accents are never chosen by a
character's ethnicity, so 'gogi' and 'odessa' are not used for people (odessa only as the salmon's own voice).
"""
import json
import os
import re
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACK = HERE.parent
ROOM = PACK.parent / 'puppet-writers-room'

# one voice per character; female hosts get 'lady', older or softer women 'calm', children and gadgets 'fairy',
# men 'narrator', big slow animals 'deep', the salmon keeps its own voice
FEMALE = set('dina gulnara zuhra olga svetlana madina alina natalya aigerim karina tamara liza leyla raisa kamila zhanna '
             'sveta aidana yulia asel inna sabina turtle cow hen crow seagull vacuum speaker cloud fox snail goat'.split())
VOICE = {
    'ch_narrator': 'deep', 'ch_salmon': 'salmon', 'ch_dina': 'lady', 'ch_inna': 'lady', 'ch_alina': 'lady', 'ch_karina': 'lady',
    'ch_svetlana': 'lady', 'ch_madina': 'lady', 'ch_liza': 'fairy', 'ch_aigerim': 'fairy', 'ch_sasha': 'fairy',
    'ch_chatbot': 'calm', 'ch_speaker': 'calm', 'ch_robot': 'calm', 'ch_vacuum': 'fairy', 'ch_atm': 'calm',
    'ch_moose': 'deep', 'ch_bear': 'deep', 'ch_camel': 'deep', 'ch_barrel': 'deep', 'ch_fridge': 'deep',
    'ch_zucchini': 'deep', 'ch_mosquito': 'fairy', 'ch_hamster': 'fairy', 'ch_phone': 'fairy', 'ch_bulb': 'fairy',
}


def cast_codes():
    return sorted(set(re.findall(r'\|\s*(ch_\w+)\s*\|', (ROOM / 'cast.md').read_text())))


def place_codes():
    return sorted(set(re.findall(r'\|\s*(pl_\w+)\s*\|', (ROOM / 'places.md').read_text())))


def voice_of(code):
    if code in VOICE:
        return VOICE[code]
    return 'calm' if code[3:] in FEMALE else 'narrator'


def device_sets():
    p = HERE / 'device_sets.json'
    return json.loads(p.read_text()) if p.exists() else {}


_PNG = bytes.fromhex('89504e470d0a1a0a0000000d4948445200000001000000010806000000'
                     '1f15c4890000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082')


def build(root=None):
    """Create the stand-in library and return its path."""
    root = Path(root or tempfile.mkdtemp(prefix='puppet_stub_'))
    sets = {c: {'talks': True, 'voice': voice_of(c)} for c in cast_codes()}
    sets.update({p: {'talks': False} for p in place_codes()})
    for k, v in device_sets().items():
        sets.setdefault(k, {'talks': v['talks'], **({'voice': v['voice']} if v.get('voice') else {})})
    for name, info in sets.items():
        d = root / name
        d.mkdir(parents=True, exist_ok=True)
        (d / 'base.png').write_bytes(_PNG)
        if info['talks']:
            (d / 'open.png').write_bytes(_PNG)
        (d / 'set.json').write_text(json.dumps(info))
    return str(root)


if __name__ == '__main__':
    print(build())
