import json, collections
p = 'src/data/wild_encounters.json'
d = json.load(open(p))
fr, lg = {}, {}
rates = {}
for g in d['wild_encounter_groups']:
    for f in g.get('fields', []):
        rates[f['type']] = f['encounter_rates']
    for e in g['encounters']:
        bl = e.get('base_label', '')
        if bl.endswith('_FireRed'): fr[bl[:-8]] = e
        if bl.endswith('_LeafGreen'): lg[bl[:-10]] = e

toggle = 0
log = []
for area, fe in fr.items():
    le = lg.get(area)
    if not le: continue
    for key, fv in fe.items():
        if not (isinstance(fv, dict) and 'mons' in fv) or key not in le: continue
        fm, lm = fv['mons'], le[key]['mons']
        if len(fm) != len(lm): continue
        r = rates.get(key, [1] * len(fm))
        diffs = [i for i in range(len(fm)) if fm[i]['species'] != lm[i]['species']]
        locked = set()
        for i in diffs:
            x, y = fm[i]['species'], lm[i]['species']
            cur = [m['species'] for m in fm]
            if y in cur:
                continue
            if cur.count(x) > 1:
                fm[i] = dict(lm[i]); locked.add(i); log.append((area, key, i, x, '->', y, 'dup')); continue
            counts = collections.Counter(cur)
            fillers = [j for j in range(len(fm)) if counts[fm[j]['species']] > 1 and j not in locked and j not in diffs]
            if fillers:
                j = min(fillers, key=lambda j: abs(r[j] - r[i]))
                old = fm[j]['species']
                fm[j] = dict(fm[j]); fm[j]['species'] = y; locked.add(j)
                log.append((area, key, j, old, '->', y, 'filler'))
            else:
                if toggle % 2:
                    fm[i] = dict(lm[i]); locked.add(i); log.append((area, key, i, x, '->', y, 'alt'))
                toggle += 1
json.dump(d, open(p, 'w'), indent=2, ensure_ascii=False); open(p, 'a').write('\n')

def species(tabs):
    s = set()
    for e in tabs.values():
        for k, v in e.items():
            if isinstance(v, dict) and 'mons' in v: s |= {m['species'] for m in v['mons']}
    return s
allsp = species(lg) | species({a: e for a, e in fr.items()})
d2 = json.load(open(p)); fr2 = {}
for g in d2['wild_encounter_groups']:
    for e in g['encounters']:
        if e.get('base_label', '').endswith('_FireRed'): fr2[e['base_label']] = e
print('changes', len(log))
print('missing from FireRed build:', sorted(allsp - species(fr2)))
