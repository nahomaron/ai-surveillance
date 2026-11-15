"""D-38 A.3 feasibility: how many pair-frames the T21.1 reference construction needs on SmartSpaces Warehouse_000.

T21.1 uses every eligible frame on which both objects exist in the truth, whatever their visibility. The SmartSpaces truth
is scene-wide (`t17_oracle.smartspaces_frames` gives every camera every object of the scene on every frame), so the count
is the same for each of the 19 cameras: sum over frames of persons x forklifts with a pose (pair class forklift only;
all 9,000 frames are eligible). Validation recordings only."""
import json, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT / "research/datasets/part3"))
import t17_oracle as drv
index = [e for e in json.load(open(ROOT / "out/s0_smartspaces/index.json")) if e["run"] == "Warehouse_000"]
entry = sorted(index, key=lambda e: e["camera"])[0]
t0 = time.time()
frames, classes = drv.smartspaces_frames(entry, drv.Annotations(str(ROOT / "data")), 9000, {})
per_frame = [(sum(1 for k in objs if classes[k] == "person"), sum(1 for k in objs if classes[k] == "forklift")) for objs in frames]
pf = sum(p * f for p, f in per_frame)
pairs = len({k for objs in frames for k in objs if classes[k] == "person"}) * len({k for objs in frames for k in objs if classes[k] == "forklift"})
out = {"camera_used": entry["camera"], "frames": len(frames), "persons": len({k for o in frames for k in o if classes[k] == "person"}),
       "forklifts": len({k for o in frames for k in o if classes[k] == "forklift"}), "pairs_upper_bound": pairs,
       "reference_pair_frames_per_camera": pf, "reference_pair_frames_all_19_cameras": pf * 19,
       "max_persons_on_a_frame": max(p for p, _ in per_frame), "max_forklifts_on_a_frame": max(f for _, f in per_frame), "seconds": round(time.time() - t0)}
print(json.dumps(out, indent=1))
(ROOT / "research/m1a/smartspaces_reference_pair_frames.json").write_text(json.dumps(out, indent=1))
