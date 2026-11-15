"""T21.6: describe the SDG Dodge task fields (truth annotation only; read-only). Output summarised in qualification.md Part 4."""
import json, glob, collections
by_run = {}
for f in sorted(glob.glob("data/raw/sdg/members/*/*.object_detection.jsonl")):
    run = f.split("/")[-1].split(".")[0]
    by_run.setdefault(run, f)
values, fields, onsets, n_dodge_runs, at0, durations = collections.Counter(), collections.Counter(), [], 0, 0, []
for run, f in sorted(by_run.items()):
    seq = []
    for line in open(f):
        d = json.loads(line)
        tasks = [a.get("metro_agent_data", {}) for a in (d.get("agents") or {}).values() if isinstance(a, dict)]
        for md in tasks:
            fields.update(md.keys())
        seq.append([md.get("current_task_name") for md in tasks])
    flat = [t for fr in seq for t in fr]
    values.update(set(flat))
    frames = [k for k, fr in enumerate(seq) if "Dodge" in fr]
    if frames:
        n_dodge_runs += 1; onsets.append(frames[0]); at0 += frames[0] == 0; durations.append(len(frames))
print("runs", len(by_run), "runs with Dodge", n_dodge_runs, "Dodge from frame 0", at0)
print("current_task_name values", dict(values))
print("metro_agent_data fields", dict(fields))
print("onset frames sorted", sorted(onsets)); print("Dodge frame counts sorted", sorted(durations))
