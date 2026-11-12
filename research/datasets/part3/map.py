import json, sys, collections
import pyarrow.parquet as pq
tree, heads, man, runsp, out = sys.argv[1:6]
size={x['path']:x['size'] for x in json.load(open(tree))}
sha={x['path']:x['lfs']['oid'] for x in json.load(open(tree))}
H=json.load(open(heads))
m=json.load(open(man)); ks=sorted(k.rstrip('/') for k in m['runs'])
idx={k:i for i,k in enumerate(ks)}
rp={r['run_id']:r for r in pq.read_table(runsp).to_pylist()}
paths=sorted(H)
first=[]
for p in paths:
    run=H[p].split('.')[0].split('_',1)[1]
    first.append(idx[run])
mono=all(a<b for a,b in zip(first,first[1:]))
print('monotonic',mono,'first starts at',first[0])
rows=[]
for i,p in enumerate(paths):
    end=first[i+1] if i+1<len(paths) else len(ks)
    runs=ks[first[i]:end]
    nc=[rp[r]['n_cameras'] if r in rp else None for r in runs]
    kinds=[rp[r]['source_kind'] if r in rp else None for r in runs]
    rows.append(dict(shard=p.rsplit('/',1)[1], size=size[p], sha256=sha[p], runs=runs, n_cameras=nc, kinds=kinds))
json.dump(rows, open(out,'w'), indent=1)
c=collections.Counter(len(r['runs']) for r in rows); print('runs per shard',sorted(c.items()))
print('kinds',collections.Counter(k for r in rows for k in r['kinds']))
print('ncam',sorted(collections.Counter(n for r in rows for n in r['n_cameras']).items()))
allten=[r for r in rows if all(n==10 for n in r['n_cameras'])]
print('shards all 10-cam',len(allten))
r538=[r for r in rows if '00538' in r['shard']][0]; print(r538['runs'],r538['size'])
big=sorted(rows,key=lambda r:-r['size'])[:3]; print([(b['shard'],b['size'],len(b['runs']),b['n_cameras']) for b in big])
import statistics as st
s=[r['size'] for r in rows]; print('size GB min/med/max',min(s)/1e9,st.median(s)/1e9,max(s)/1e9)
mc=[r for r in rows if len(r['runs'])>0]; print(sum(len(r['runs']) for r in rows))
# multi-camera duplicates check in runs.parquet
mcr=[r for r in rp.values() if r['source_kind']=='multi_camera_run']; print('mc in parquet',len(mcr), 'ncam!=10', sum(r['n_cameras']!=10 for r in mcr), collections.Counter(r['n_cameras'] for r in mcr if r['n_cameras']!=10))
print('manifest runs not in parquet', sum(k not in rp for k in ks))
