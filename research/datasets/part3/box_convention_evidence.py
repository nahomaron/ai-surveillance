"""Evidence, per dataset, that 2D truth boxes are inclusive pixel indices (AR-53 item 3; Architect ruling C of 14 Nov 2026).
Statistics only. For an inclusive-index box [x0, y0, x1, y1] on a W x H image: all values are integers, x1 <= W - 1 and
y1 <= H - 1 (never W or H), and boxes of one pixel column or row have x0 = x1 or y0 = y1. A half-open box would reach W or H
at the image border and could not have x0 = x1.
Usage: PYTHONPATH=src python box_convention_evidence.py <out.json> <sdg_members_root> <smartspaces ground_truth.json>..."""
import glob
import json
import os
import sys

W, H = 1920, 1080


class Tally:
    def __init__(self):
        self.n = self.non_integer = self.x_eq = self.y_eq = self.at_w1 = self.at_h1 = self.inverted = 0
        self.lo, self.hi = [None, None], [None, None]

    def add(self, box):
        x0, y0, x1, y1 = box
        self.n += 1
        self.non_integer += any(float(v) != int(v) for v in box)
        self.x_eq += x0 == x1
        self.y_eq += y0 == y1
        self.inverted += x1 < x0 or y1 < y0
        self.at_w1 += x1 == W - 1
        self.at_h1 += y1 == H - 1
        self.lo = [x0 if self.lo[0] is None else min(self.lo[0], x0), y0 if self.lo[1] is None else min(self.lo[1], y0)]
        self.hi = [x1 if self.hi[0] is None else max(self.hi[0], x1), y1 if self.hi[1] is None else max(self.hi[1], y1)]

    def report(self):
        return {"boxes": self.n, "non_integer_boxes": self.non_integer, "min_x0_y0": self.lo, "max_x1_y1": self.hi, "image_size_px": [W, H],
                "boxes_with_x1_equal_W_minus_1": self.at_w1, "boxes_with_y1_equal_H_minus_1": self.at_h1,
                "boxes_with_x0_equal_x1": self.x_eq, "boxes_with_y0_equal_y1": self.y_eq, "boxes_with_x1_below_x0_or_y1_below_y0": self.inverted}


def main():
    out_path, members, truths = sys.argv[1], sys.argv[2], sys.argv[3:]
    res = {}
    tallies = {"bounding_box_2d_tight_fast": Tally(), "bounding_box_2d_loose_fast": Tally()}
    files = sorted(glob.glob(os.path.join(members, "*", "*.object_detection.jsonl")))
    for f in files:
        for line in open(f):
            for agent in json.loads(line)["agents"].values():
                for name, tally in tallies.items():
                    b = (agent.get("annotators") or {}).get(name)
                    if b is not None:
                        tally.add((b["x_min"], b["y_min"], b["x_max"], b["y_max"]))
    res["sdg"] = {"annotation_files": len(files), **{name: t.report() for name, t in tallies.items()}}
    res["smartspaces"] = {}
    for path in truths:
        tally = Tally()
        doc = json.load(open(path))
        for objs in doc.values():
            for o in objs:
                for box in o.get("2d bounding box visible", {}).values():
                    tally.add(box)
        res["smartspaces"][os.path.basename(os.path.dirname(path))] = {"field": "2d bounding box visible", **tally.report()}
    json.dump(res, open(out_path, "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
