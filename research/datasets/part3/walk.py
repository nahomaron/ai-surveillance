"""Walk the tar headers of SDG artifacts shards by HTTP range reads (metadata only; D-24 a).

Usage: python -I walk.py <shard_map.json> <out.json> <n_shards>     (or: --one <shard name> <out.json>)
Walks the first n_shards of the declared permutation (seed 2026111203, Part 3 section 3.1) and records, for every member,
the header offset, data offset, size, mode, mtime, typeflag and whether the header checksum verifies. Supports ustar
prefixes, GNU long names ('L') and pax headers ('x')."""
import concurrent.futures as cf
import json
import sys
import urllib.request

import numpy as np

URL = ("https://huggingface.co/datasets/nvidia/PhysicalAI-WorldModel-Synthetic-Warehouse-Operations-Scenes/resolve/"
       "d5b88d3abcf659f304a107f4336b71b4e2159133/artifacts/forklift_human_nearmiss/")


def get(name, start, length):
    for _ in range(4):
        try:
            req = urllib.request.Request(URL + name, headers={"Range": f"bytes={start}-{start + length - 1}", "User-Agent": "rq1-qualification"})
            return urllib.request.urlopen(req, timeout=60).read()
        except Exception as e:  # noqa: BLE001 - retried, then re-raised
            err = e
    raise err


def num(field):
    if field[0] & 0x80:  # base-256
        return int.from_bytes(bytes([field[0] & 0x7F]) + field[1:], "big")
    s = field.split(b"\0")[0].strip()
    return int(s, 8) if s else 0


def walk(name, size):
    off, members, long_name, pax_path = 0, [], None, None
    while off + 512 <= size:
        h = get(name, off, 512)
        if h == b"\0" * 512:
            break
        chk = num(h[148:156])
        ok = chk == sum(h[:148]) + 8 * 32 + sum(h[156:])
        msize, typeflag = num(h[124:136]), h[156:157].decode()
        data_off = off + 512
        nxt = data_off + (msize + 511) // 512 * 512
        if typeflag == "L":
            long_name = get(name, data_off, msize).split(b"\0")[0].decode()
        elif typeflag == "x":
            for rec in get(name, data_off, msize).decode().split("\n"):
                if " path=" in rec:
                    pax_path = rec.split(" path=", 1)[1]
        else:
            base = h[0:100].split(b"\0")[0].decode()
            prefix = h[345:500].split(b"\0")[0].decode() if h[257:262] == b"ustar" else ""
            path = pax_path or long_name or (prefix + "/" + base if prefix else base)
            members.append({"name": path, "header_offset": off, "data_offset": data_off, "size": msize, "typeflag": typeflag,
                            "mode": num(h[100:108]), "mtime": num(h[136:148]), "header_checksum_ok": ok})
            long_name = pax_path = None
        off = nxt
    return name, members


SEED = 2026111203
HELD = "nearmiss-artifacts-00538.tar"


def eligible_shards(rows):
    """Part 3 section 3.1: every run a 10-camera multi_camera_run, size <= 6 GiB, the held shard excluded, sorted by name."""
    return sorted(r["shard"] for r in rows if r["shard"] != HELD and r["size"] <= 6 * 2**30
                  and all(k == "multi_camera_run" for k in r["kinds"]) and all(c == 10 for c in r["n_cameras"]))


def main():
    if sys.argv[1] == "--one":
        name, out = sys.argv[2], sys.argv[3]
        size = int(urllib.request.urlopen(urllib.request.Request(URL + name, method="HEAD", headers={"User-Agent": "rq1-qualification"})).headers["Content-Length"])
        json.dump(dict([walk(name, size)]), open(out, "w"), indent=1)
        return
    smap, out, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
    rows = json.load(open(smap))["shards"]
    shards = {r["shard"]: r for r in rows}
    eligible = eligible_shards(rows)
    assert len(eligible) == 475
    perm = np.random.Generator(np.random.PCG64(SEED)).permutation(len(eligible))
    order = [eligible[i] for i in perm[:n]]
    with cf.ThreadPoolExecutor(4) as ex:
        res = dict(ex.map(lambda sh: walk(sh, shards[sh]["size"]), order))
    json.dump({"order": order, "members": res}, open(out, "w"), indent=1, sort_keys=True)
    print(len(res), sum(len(v) for v in res.values()), sum(not m["header_checksum_ok"] for v in res.values() for m in v))


if __name__ == "__main__":
    main()
