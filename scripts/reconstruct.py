"""Reconstruction of Ding et al. (2021) Figure 4 / Figure 13 on 2014-2018 data (original cohort only).

Each job trains one method on the 2014 training split and evaluates it on the test split of every year
2014-2018. Jobs run in parallel processes; each result is appended as one JSON line to
results/reconstruction/runs.jsonl together with the job's settings, timing and package versions.

Usage:
  uv run python scripts/reconstruct.py --plan core --jobs 5
  uv run python scripts/reconstruct.py --plan all --jobs 6     (core + literal + gbm_seeds)
Plans are defined in PLANS below. Re-running skips jobs whose key already appears in runs.jsonl.
"""
from __future__ import annotations

import argparse
import itertools
import json
import platform
import subprocess
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

TRAIN_YEAR = 2014
EVAL_YEARS = (2014, 2015, 2016, 2017, 2018)
OUT = ROOT / "results" / "reconstruction" / "runs.jsonl"
if __import__("os").environ.get("RT_SMOKE_ROWS"):
    OUT = ROOT / "results" / "smoke" / "runs_smoke.jsonl"


def job_key(j: dict) -> str:
    return "|".join(f"{k}={j[k]}" for k in sorted(j))


def plans() -> dict[str, list[dict]]:
    P = {}
    P["core"] = [dict(method=m, constraint=c, scaling=s, n_trees=100, seed=0)
                 for s in ("per_year", "common")
                 for m, c in [("gbm", "none"), ("postprocessing", "dp"), ("postprocessing", "eo"),
                              ("expgrad", "dp"), ("expgrad", "eo"), ("lfr", "dp")]]
    P["gbm_seeds"] = [dict(method="gbm", constraint="none", scaling=s, n_trees=n, seed=sd)
                      for s, n, sd in itertools.product(("per_year", "common"), (5, 50, 100, 200), range(5))]
    P["literal"] = [dict(method=m, constraint=c, scaling=s, n_trees=5, seed=0)
                    for s in ("per_year", "common")
                    for m, c in [("gbm", "none"), ("postprocessing", "dp"), ("expgrad", "dp"), ("lfr", "dp")]]
    seen, P["all"] = set(), []
    for j in P["core"] + P["literal"] + P["gbm_seeds"]:
        if job_key(j) not in seen:
            seen.add(job_key(j)); P["all"].append(j)
    P["smoke"] = [dict(method=m, constraint=c, scaling=s, n_trees=5, seed=0)
                  for s in ("per_year", "common")
                  for m, c in [("gbm", "none"), ("postprocessing", "dp"), ("postprocessing", "eo"),
                               ("expgrad", "dp"), ("expgrad", "eo"), ("lfr", "dp")]]
    return P


def versions() -> dict:
    import aif360, fairlearn, numpy, pandas, scipy, sklearn
    try:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                                capture_output=True, text=True).stdout.strip()
    except Exception:
        commit = ""
    return {"python": platform.python_version(), "machine": platform.machine(), "git": commit,
            **{m.__name__: m.__version__ for m in (numpy, pandas, scipy, sklearn, fairlearn, aif360)}}


def run_job(job: dict) -> dict:
    import numpy as np
    from common import evaluate
    from models import METHODS, Scaling, year_arrays
    t0 = time.time()
    try:
        X, y, race, test = year_arrays(TRAIN_YEAR, job["seed"])
        scaler = Scaling(job["scaling"], X[~test])
        Xs = scaler.apply(X)
        m = METHODS[job["method"]](job["n_trees"], job["seed"], job["constraint"])
        m.fit(Xs[~test], y[~test], race[~test])
        fit_s = time.time() - t0
        evals = {}
        for ey in EVAL_YEARS:
            if ey == TRAIN_YEAR:
                Xe, ye, re_ = Xs[test], y[test], race[test]
            else:
                Xa, ya, ra, te = year_arrays(ey, job["seed"])
                Xe, ye, re_ = scaler.apply(Xa)[te], ya[te], ra[te]
            evals[str(ey)] = evaluate(m.predict(Xe, re_), ye, re_)
        return {"job": job, "key": job_key(job), "status": "ok", "fit_seconds": round(fit_s, 1),
                "total_seconds": round(time.time() - t0, 1), "eval": evals, "versions": versions(),
                "finished": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    except Exception as e:
        return {"job": job, "key": job_key(job), "status": "error", "error": repr(e),
                "traceback": traceback.format_exc()[-3000:], "total_seconds": round(time.time() - t0, 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True, choices=sorted(plans()))
    ap.add_argument("--jobs", type=int, default=5)
    a = ap.parse_args()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if OUT.exists():
        for line in OUT.read_text().splitlines():
            r = json.loads(line)
            if r.get("status") == "ok":
                done.add(r["key"])
    todo = [j for j in plans()[a.plan] if job_key(j) not in done]
    # longest jobs first so the pool stays busy
    cost = {"lfr": 4, "expgrad": 3, "postprocessing": 1, "gbm": 1}
    todo.sort(key=lambda j: -cost[j["method"]] * j["n_trees"])
    print(f"{len(todo)} jobs to run ({len(done)} already done)", flush=True)
    from concurrent.futures import ProcessPoolExecutor, as_completed
    with ProcessPoolExecutor(max_workers=a.jobs) as ex:
        futs = {ex.submit(run_job, j): j for j in todo}
        for f in as_completed(futs):
            r = f.result()
            with open(OUT, "a") as fh:
                fh.write(json.dumps(r) + "\n")
            j = r["job"]
            msg = f'{r["status"]:5s} {j["method"]:14s} {j["constraint"]:4s} {j["scaling"]:8s} ' \
                  f'trees={j["n_trees"]:3d} seed={j["seed"]} {r["total_seconds"]:7.1f}s'
            if r["status"] == "ok":
                e = r["eval"]
                msg += "  acc " + " ".join(f'{e[str(y)]["accuracy"]:.4f}' for y in EVAL_YEARS)
            else:
                msg += "  " + r["error"][:200]
            print(msg, flush=True)


if __name__ == "__main__":
    main()
