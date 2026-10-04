import re, glob

# --- Parse species evolution data -------------------------------------------
evos = {}
for f in sorted(glob.glob('src/data/pokemon/species_info/gen_*_families.h')):
    src = open(f).read()
    for m in re.finditer(r'\[(SPECIES_[A-Z0-9_]+)\]\s*=\s*\{(.*?)(?=\n    \[SPECIES_|\Z)', src, re.S):
        sp, body = m.group(1), m.group(2)
        e = re.search(r'\.evolutions\s*=\s*EVOLUTION\((.*?)\),\s*\n', body, re.S)
        if sp in evos or not e:
            evos.setdefault(sp, evos.get(sp, []))
            continue
        evos[sp] = re.findall(r'\{\s*(EVO_[A-Z_]+)\s*,\s*([A-Z0-9_]+)\s*,\s*(SPECIES_[A-Z0-9_]+)', e.group(1))

FORM_SUFFIXES = ('_ALOLA', '_GALAR', '_HISUI', '_PALDEA', '_MEGA', '_GMAX', '_TOTEM')

def threshold(method, param):
    if method in ('EVO_LEVEL', 'EVO_LEVEL_BATTLE_ONLY'):
        return int(param) if param.isdigit() and int(param) > 0 else 36   # friendship/location-style
    if method == 'EVO_ITEM':
        return 36
    if method == 'EVO_TRADE':
        return 38
    return None   # EVO_NONE, split, script, spin, battle-end: never auto-evolve

def evolve(sp, level):
    for _ in range(3):
        nxt = None
        for method, param, target in evos.get(sp, []):
            if target.endswith(FORM_SUFFIXES) or target not in evos:
                continue
            t = threshold(method, param)
            if t is not None and level >= t:
                nxt = target
                break
        if not nxt:
            break
        sp = nxt
    return sp

def name_to_const(name):
    return 'SPECIES_' + re.sub(r"[.'’]", '', name).upper().replace(' ', '_').replace('-', '_')

def const_to_name(c):
    return ' '.join(w.capitalize() for w in c[len('SPECIES_'):].split('_'))

LEADERS = {'TRAINER_LEADER_BROCK','TRAINER_LEADER_MISTY','TRAINER_LEADER_LT_SURGE','TRAINER_LEADER_ERIKA',
           'TRAINER_LEADER_KOGA','TRAINER_LEADER_SABRINA','TRAINER_LEADER_BLAINE','TRAINER_LEADER_GIOVANNI'}

p = 'src/data/trainers_frlg.party'
text = open(p).read()
parts = re.split(r'(?m)^(?==== )', text)
changes = []
out = []
for part in parts:
    m = re.match(r'=== (\S+) ===', part)
    if not m:
        out.append(part); continue
    tname = m.group(1)
    chunks = part.split('\n\n')
    newchunks = [chunks[0]]
    for ch in chunks[1:]:
        lines = ch.split('\n')
        head = lines[0]
        lvm = re.search(r'(?m)^Level: (\d+)', ch)
        hm = re.match(r"^([A-Z][A-Za-z.' -]*?)( \([MF]\))?( @ .*)?$", head)
        if not lvm or not hm:
            newchunks.append(ch); continue
        name = hm.group(1)
        const = name_to_const(name)
        if const not in evos:
            newchunks.append(ch); continue
        level = int(lvm.group(1))
        new = evolve(const, level)
        if new != const:
            lines[0] = const_to_name(new) + (hm.group(2) or '') + (hm.group(3) or '')
            changes.append((tname, name, level, const_to_name(new)))
        if tname in LEADERS:
            lines = [l for l in lines if not l.startswith('- ')]   # let leaders use level-up moves
        newchunks.append('\n'.join(lines))
    out.append('\n\n'.join(newchunks))
open(p, 'w').write(''.join(out))
for c in changes:
    if c[0] in LEADERS or 'RIVAL' in c[0] or 'GIOVANNI' in c[0] or 'ELITE' in c[0] or 'CHAMPION' in c[0]:
        print(c)
print('evolved', len(changes))
