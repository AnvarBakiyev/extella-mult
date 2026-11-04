"""The plate library: which biome x variant x time x weather x season x palette combinations are rendered.
Deterministic, so `python plates.py --all` always rebuilds the same set."""
import numpy as np

OUTDOOR = ['steppe', 'mountains', 'almaty', 'courtyard', 'bazaar', 'desert', 'birch_forest', 'pine_forest', 'lake',
           'sea_coast', 'village', 'farm', 'downtown', 'suburb', 'highway', 'railway', 'port', 'park', 'school_yard',
           'construction', 'jungle', 'arctic']
FAR = ['space', 'moon', 'mars', 'underwater', 'cave']
INTERIORS = ['tv_studio', 'office', 'boss_office', 'kitchen', 'living_room', 'bedroom', 'classroom', 'hospital',
             'courtroom', 'cafe', 'metro', 'bus_interior', 'airplane', 'lab', 'server_room', 'gov_counter', 'shop']
VARIANTS = {'steppe': 4, 'mountains': 4}  # others have 3

# nine looks per outdoor biome: (time, weather, season, palette)
OUT_LOOKS = [('day', 'clear', 'summer', 'felt'), ('golden', 'clear', 'summer', 'felt'), ('night', 'clear', 'summer', 'felt'),
             ('dawn', 'clouds', 'spring', 'pastel'), ('dusk', 'clear', 'autumn', 'warm'), ('day', 'clouds', 'autumn', 'felt'),
             ('day', 'rain', 'summer', 'muted'), ('day', 'snow', 'winter', 'cool'), ('dawn', 'fog', 'summer', 'felt')]
NO_SNOW = {'desert': ('night', 'clear', 'summer', 'cool'), 'jungle': ('dusk', 'rain', 'summer', 'felt'),
           'bazaar': ('day', 'clear', 'autumn', 'vivid')}
DOWNTOWN = [('night', 'clear', 'summer', 'felt'), ('dusk', 'clear', 'summer', 'felt'), ('night', 'rain', 'summer', 'felt'),
            ('golden', 'clear', 'summer', 'warm'), ('day', 'clear', 'summer', 'felt'), ('night', 'snow', 'winter', 'cool'),
            ('dusk', 'clouds', 'autumn', 'felt'), ('night', 'fog', 'summer', 'muted'), ('dawn', 'clear', 'spring', 'pastel')]
ARCTIC = [('day', 'clear', 'winter', 'felt'), ('night', 'clear', 'winter', 'felt'), ('dusk', 'clear', 'winter', 'felt'),
          ('golden', 'clear', 'winter', 'warm'), ('day', 'snow', 'winter', 'cool'), ('night', 'clouds', 'winter', 'felt'),
          ('dawn', 'clear', 'winter', 'pastel'), ('day', 'fog', 'winter', 'felt'), ('night', 'snow', 'winter', 'felt')]
FAR_LOOKS = {
    'space': [('night', 'clear', 'summer', p) for p in ('felt', 'vivid', 'pastel', 'cool', 'warm', 'felt')],
    'moon': [('night', 'clear', 'summer', p) for p in ('felt', 'cool', 'felt', 'muted', 'felt', 'vivid')],
    'mars': [('day', 'clear', 'summer', 'felt'), ('dusk', 'clear', 'summer', 'felt'), ('night', 'clear', 'summer', 'felt'),
             ('golden', 'clear', 'summer', 'warm'), ('day', 'fog', 'summer', 'felt'), ('day', 'clear', 'summer', 'vivid')],
    'underwater': [('day', 'clear', 'summer', 'felt'), ('night', 'clear', 'summer', 'felt'), ('day', 'clear', 'summer', 'vivid'),
                   ('dusk', 'clear', 'summer', 'felt'), ('day', 'clear', 'summer', 'pastel'), ('golden', 'clear', 'summer', 'felt')],
    'cave': [('day', 'clear', 'summer', 'felt'), ('night', 'clear', 'summer', 'felt'), ('golden', 'clear', 'summer', 'warm'),
             ('day', 'clear', 'summer', 'cool'), ('dusk', 'clear', 'summer', 'felt'), ('day', 'clear', 'summer', 'vivid')],
}
IN_LOOKS = [('day', 'clear', 'summer', 'felt'), ('night', 'clear', 'summer', 'felt'), ('golden', 'clear', 'autumn', 'warm'),
            ('day', 'rain', 'autumn', 'felt'), ('dusk', 'clear', 'winter', 'felt'), ('dawn', 'clouds', 'spring', 'pastel')]


def _name(b, v, t, w, s, p):
    n = f'{b}-v{v}-{t}-{w}'
    if s not in ('summer',):
        n += f'-{s}'
    if p != 'felt':
        n += f'-{p}'
    return n


def catalog():
    specs = []
    seed = 11
    for b in OUTDOOR + FAR + INTERIORS:
        if b in OUTDOOR:
            looks = DOWNTOWN if b == 'downtown' else ARCTIC if b == 'arctic' else list(OUT_LOOKS)
            if b in NO_SNOW:
                looks = [NO_SNOW[b] if l[1] == 'snow' else l for l in looks]
        elif b in FAR:
            looks = FAR_LOOKS[b]
        else:
            looks = IN_LOOKS
        nv = VARIANTS.get(b, 3)
        for i, (t, w, s, p) in enumerate(looks):
            v = i % nv
            seed += 7
            specs.append(dict(name=_name(b, v, t, w, s, p), biome=b, variant=v, time=t, weather=w, season=s, palette=p, seed=seed))
    # the expansion modules (puppet-plates-more): each lists its own looks
    import zlib
    import scenes  # noqa: F401  registers every biome
    for mod in ('studios', 'rooms2', 'kz', 'outdoors2'):
        m = __import__(mod)
        for b, (nv, looks) in m.LOOKS.items():
            for i, (t, w, s_, p) in enumerate(looks):
                v = i % nv
                sd = 5000 + zlib.crc32(f'{b}-{i}'.encode()) % 90000
                specs.append(dict(name=_name(b, v, t, w, s_, p), biome=b, variant=v, time=t, weather=w, season=s_, palette=p, seed=sd))
    names = [s['name'] for s in specs]
    from collections import Counter
    dup = [n for n, k in Counter(names).items() if k > 1]
    assert not dup, dup
    return specs


if __name__ == '__main__':
    c = catalog()
    print(len(c))
    from collections import Counter
    print(Counter(s['biome'] for s in c))
