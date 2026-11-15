#!/bin/zsh
# T-21: after the SmartSpaces base + full_camera run exits, build the truth tables, evaluate and aggregate (one camera at a
# time; every step skips finished cameras, so the script can be re-run after an interruption).
cd "$(dirname "$0")/../.."
while pgrep -f "run_m1a.py smartspaces run1" >/dev/null; do sleep 60; done
export PYTHONPATH="$PWD/src"
RECS=$(ls out/m1a/run1/smartspaces | grep '^rec_' | while read r; do [ -f out/m1a/run1/smartspaces/$r/full_camera.json ] && echo $r; done | paste -sd, -)
echo "truth tables: $RECS"
for r in ${(s:,:)RECS}; do .venv/bin/python research/m1a/truth_unit.py smartspaces run1 $r || exit 1; done
.venv/bin/python research/m1a/evaluate_m1a.py smartspaces run1 cameras 1 || exit 1
.venv/bin/python research/m1a/evaluate_m1a.py smartspaces run1 aggregate || exit 1
echo "finished $(date)"
