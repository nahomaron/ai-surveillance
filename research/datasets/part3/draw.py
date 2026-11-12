import json, sys, glob, numpy as np
rows=json.load(open(sys.argv[1])); S=sys.argv[2]
GB=1e9; CAP=30*GB; GiB6=6*2**30
# exact held bytes
import os
held=sum(os.path.getsize(p) for p in glob.glob('data/raw/**/*',recursive=True) if os.path.isfile(p) and not p.endswith('.DS_Store'))
ss=sum(x['size'] for w in ['Warehouse_026','Warehouse_027'] for x in json.load(open(f'{S}/ss_{w}.json')) if x['type']=='file')
fold={f['id']:f for f in json.load(open(f'{S}/mendeley/datasets_xjmtb22pff_folders_1.json'))}
want={'0_safe_walkway_violation','3_carrying_overload_with_forklift','4_safe_walkway','7_safe_carrying'}
md=[];
for p in glob.glob(f'{S}/mendeley/files_*.json'):
    fid=p.split('files_')[1][:-5]
    if fold[fid]['name'] in want: md+=json.load(open(p))
mds=sum(x['size'] for x in md)
RESERVE=int(0.5*GB)
sdg_budget=CAP-held-ss-mds-RESERVE
print('held',held,'ss',ss,len([1]),'mendeley',mds,len(md),'sdg_budget',sdg_budget)
elig=sorted([r for r in rows if r['shard']!='nearmiss-artifacts-00538.tar' and r['size']<=GiB6 and all(n==10 for n in r['n_cameras'])], key=lambda r:r['shard'])
elig2=[r for r in rows if r['shard']!='nearmiss-artifacts-00538.tar' and r['size']<=GiB6 and all(n>=2 for n in r['n_cameras'])]
print('eligible (all 10 cam, <=6GiB, not held)',len(elig),' alt >=2 cam',len(elig2))
SEED=2026111203
perm=np.random.Generator(np.random.PCG64(SEED)).permutation(len(elig))
take=[];tot=0
for i in perm:
    r=elig[i]
    if tot+r['size']>sdg_budget: break
    take.append(r); tot+=r['size']
print('take',len(take),'bytes',tot, 'runs',sum(len(r['runs']) for r in take))
for r in take: print(r['shard'],r['size'],r['sha256'],r['runs'])
print('next (first misfit)', elig[perm[len(take)]]['shard'], elig[perm[len(take)]]['size'])
print('grand total', held+ss+mds+tot)
json.dump(dict(seed=SEED,held=held,ss=ss,mendeley=mds,mendeley_files=len(md),reserve=RESERVE,budget=sdg_budget,eligible=[r['shard'] for r in elig],take=take),open(f'{S}/draw.json','w'),indent=1)
