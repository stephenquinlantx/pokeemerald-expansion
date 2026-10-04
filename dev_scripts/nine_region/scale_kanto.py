# Nine-Region: one-off script that rescaled vanilla FireRed levels onto the
# badge curve (applied in the 'Scale Kanto' commit). Do NOT re-run on scaled data.
import re, json, glob, bisect

# Vanilla FireRed level -> Nine-Region level, anchored on the gym leaders
# (Brock 14->10, Misty 21->20, Surge 24->30, Erika 29->40, Koga/Sabrina 43,
# Blaine 47->70, Giovanni 50->80) and the post-game.
ANCHORS = [(1,1),(5,4),(9,8),(14,10),(18,16),(21,20),(24,30),(29,40),(37,52),(41,58),(43,62),(47,70),(50,80),(56,90),(63,96),(75,100),(100,100)]
def scale(L):
    xs=[a for a,_ in ANCHORS]
    if L<=xs[0]: return ANCHORS[0][1]
    if L>=xs[-1]: return 100
    i=bisect.bisect_right(xs,L)-1
    (x0,y0),(x1,y1)=ANCHORS[i],ANCHORS[i+1]
    return max(2,min(100,round(y0+(L-x0)*(y1-y0)/(x1-x0))))
def victory_road(L): return max(70,min(89,round(80+(L-42))))     # after 8 badges, cap 89
def league(L): return max(90,min(100,round(90+(L-51)*10/12)))     # Elite Four + first Champion
def postgame_cave(L): return max(90,min(100,round(90+(L-46)*10/21)))

LEADERS={'TRAINER_LEADER_BROCK':10,'TRAINER_LEADER_MISTY':20,'TRAINER_LEADER_LT_SURGE':30,'TRAINER_LEADER_ERIKA':40,
 'TRAINER_LEADER_KOGA':50,'TRAINER_LEADER_SABRINA':60,'TRAINER_LEADER_BLAINE':70,'TRAINER_LEADER_GIOVANNI':80,'TRAINER_NR_GIOVANNI_REVENGE':90}
GYMS={'PewterCity_Gym':10,'CeruleanCity_Gym':20,'VermilionCity_Gym':30,'CeladonCity_Gym':40,'FuchsiaCity_Gym':50,
 'SaffronCity_Gym':60,'CinnabarIsland_Gym':70,'ViridianCity_Gym':80}

def trainers_in(pattern):
    out=set()
    for f in glob.glob(f'data/maps/{pattern}/scripts.inc'):
        out|=set(re.findall(r'TRAINER_[A-Z0-9_]+',open(f).read()))
    return out

rule={}
for gym,lv in GYMS.items():
    for t in trainers_in(gym+'_Frlg'):
        if t not in LEADERS: rule[t]=('gym',lv)
for t in trainers_in('VictoryRoad_*_Frlg'): rule[t]=('vr',None)
for t in ['TRAINER_RIVAL_ROUTE22_LATE_SQUIRTLE','TRAINER_RIVAL_ROUTE22_LATE_BULBASAUR','TRAINER_RIVAL_ROUTE22_LATE_CHARMANDER']: rule[t]=('vr',None)
for t in trainers_in('PokemonLeague_*_Frlg'):
    rule[t]=('post100',None) if (t.endswith('_2') or 'REMATCH' in t) else ('league',None)

p='src/data/trainers_frlg.party'
s=open(p).read()
parts=re.split(r'(?m)^(?==== )',s)
out=[]; report=[]
for part in parts:
    m=re.match(r'=== (\S+) ===',part)
    if not m or m.group(1) in LEADERS or m.group(1)=='TRAINER_NONE':
        out.append(part); continue
    t=m.group(1); kind,arg=rule.get(t,('scale',None))
    def f(L):
        if kind=='gym': return max(3,arg-3)
        if kind=='vr': return victory_road(L)
        if kind=='league': return league(L)
        if kind=='post100': return 100
        return scale(L)
    old=[int(x) for x in re.findall(r'(?m)^Level: (\d+)',part)]
    part=re.sub(r'(?m)^Level: (\d+)',lambda mm:f'Level: {f(int(mm.group(1)))}',part)
    new=[int(x) for x in re.findall(r'(?m)^Level: (\d+)',part)]
    report.append((t,kind,old,new))
    out.append(part)
open(p,'w').write(''.join(out))

# Wild encounters (FireRed and LeafGreen tables only)
wp='src/data/wild_encounters.json'
d=json.load(open(wp))
nw=0
for g in d['wild_encounter_groups']:
    for e in g['encounters']:
        bl=e.get('base_label','')
        if not (bl.endswith('_FireRed') or bl.endswith('_LeafGreen')): continue
        fn = victory_road if ('VictoryRoad' in bl or 'Route23' in bl) else postgame_cave if 'CeruleanCave' in bl else scale
        for k,v in e.items():
            if isinstance(v,dict) and 'mons' in v:
                for mon in v['mons']:
                    lo,hi=fn(mon['min_level']),fn(mon['max_level'])
                    mon['min_level'],mon['max_level']=min(lo,hi),max(lo,hi); nw+=1
open(wp,'w').write(json.dumps(d,indent=2,ensure_ascii=False)+'\n')

# Static encounters in FRLG map scripts
ns=0
for f in glob.glob('data/maps/*_Frlg/scripts.inc'):
    src=open(f).read()
    def rep(mm):
        global ns; ns+=1
        L=int(mm.group(2))
        return f'{mm.group(1)}{postgame_cave(L) if "CeruleanCave" in f else scale(L)}'
    new=re.sub(r'(setwildbattle\s+SPECIES_[A-Z0-9_]+,\s*)(\d+)',rep,src)
    if new!=src: open(f,'w').write(new)

for r in report:
    if r[1]!='scale' or any(x in r[0] for x in ['RIVAL','BOSS','ROCKET_ADMIN']): print(r)
print('trainers',len(report),'wild slots',nw,'static',ns)
