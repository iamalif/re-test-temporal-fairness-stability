"""Stage A (before the pre-registration is archived): fit and freeze all models on 2014, predict 2014-2018.

  uv run python scripts/stage_a.py fit --jobs 6       # fits every model once (ExpGrad is the long one)
  uv run python scripts/stage_a.py predict --jobs 5   # predictions for 2014-2018 (original cohort only)

Both steps are resumable: models already in results/models_manifest.json and prediction files already on disk
are skipped. Stage B (after archiving) runs `predict` for 2019 and 2021-2024 with the same frozen models.
"""
import argparse
import sys
import time
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import json

from pipeline import MANIFEST, MODELS, fit_job, manifest_update, model_prefix, predict_year, stage_a_jobs

ORIGINAL = (2014, 2015, 2016, 2017, 2018)
NEW = (2019, 2021, 2022, 2023, 2024)


def _names_of(job):
    p = model_prefix(job)
    if job["kind"] in ("gbm", "rawgbm"):
        names = [f"{p}{job['kind']}_s{job['seed']}"]
        names += [f"{p}post_{c}_{g}_s{job['seed']}" for g, c in job.get("post", [])]
        return names
    return [{"expgrad": f"expgrad_dp_race_s{job['seed']}", "lfr": f"lfr_race_s{job['seed']}"}[job["kind"]]]


def _safe_fit(job):
    t = time.time()
    try:
        return job, fit_job(job), None, time.time() - t
    except Exception:
        return job, [], traceback.format_exc()[-2500:], time.time() - t


def _safe_predict(names, year):
    t = time.time()
    try:
        predict_year(names, year)
        return year, None, time.time() - t
    except Exception:
        return year, traceback.format_exc()[-2500:], time.time() - t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["fit", "predict"])
    ap.add_argument("--jobs", type=int, default=5)
    ap.add_argument("--years", type=int, nargs="*", default=list(ORIGINAL))
    a = ap.parse_args()
    done = set(json.loads(MANIFEST.read_text())) if MANIFEST.exists() else set()
    if a.step == "fit":
        todo = [j for j in stage_a_jobs() if not all(n in done for n in _names_of(j))]
        order = {"expgrad": 0, "lfr": 1, "gbm": 2, "rawgbm": 3}
        todo.sort(key=lambda j: (order[j["kind"]], j.get("state") is not None))
        print(f"{len(todo)} fit jobs to run", flush=True)
        with ProcessPoolExecutor(max_workers=a.jobs) as ex:
            for f in as_completed([ex.submit(_safe_fit, j) for j in todo]):
                job, entries, err, secs = f.result()
                if err:
                    print(f"ERROR {job} after {secs:.0f}s\n{err}", flush=True)
                    continue
                manifest_update(entries)
                print(f"ok  {', '.join(e['name'] for e in entries)}  {secs:.0f}s", flush=True)
    else:
        names = sorted(json.loads(MANIFEST.read_text()))
        missing = [n for n in names if not (MODELS / f"{n}.joblib").exists()]
        if missing:
            raise SystemExit(f"model files missing: {missing[:5]}")
        raw = [n for n in names if "rawgbm" in n]
        with ProcessPoolExecutor(max_workers=a.jobs) as ex:
            futs = [ex.submit(_safe_predict, [n for n in names if (y <= 2018 or n not in raw)], y)
                    for y in a.years]
            for f in as_completed(futs):
                year, err, secs = f.result()
                print(("ERROR " + err) if err else f"ok  predictions {year}  {secs:.0f}s", flush=True)


if __name__ == "__main__":
    main()
