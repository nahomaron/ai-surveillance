import json, sys, urllib.request, concurrent.futures as cf
tree, out = sys.argv[1], sys.argv[2]
U="https://huggingface.co/datasets/nvidia/PhysicalAI-WorldModel-Synthetic-Warehouse-Operations-Scenes/resolve/d5b88d3abcf659f304a107f4336b71b4e2159133/"
paths=sorted(x['path'] for x in json.load(open(tree)))
def get(p):
    for _ in range(3):
        try:
            r=urllib.request.Request(U+p, headers={'Range':'bytes=0-511','User-Agent':'rq1-qualification'})
            b=urllib.request.urlopen(r, timeout=60).read(512)
            return p, b[:100].split(b'\0')[0].decode()
        except Exception as e: err=str(e)
    return p, 'ERR '+err
with cf.ThreadPoolExecutor(4) as ex: res=dict(ex.map(get, paths))
json.dump(res, open(out,'w'), indent=0, sort_keys=True)
print(sum(v.startswith('ERR') for v in res.values()), len(res))
