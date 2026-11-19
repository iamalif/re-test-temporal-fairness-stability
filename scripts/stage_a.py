"""Stage A (before the pre-registration is archived): fit and freeze all models, predict 2014-2018.

  uv run python scripts/stage_a.py fit --jobs 6       # fits every model once (ExpGrad is the long one)
  uv run python scripts/stage_a.py predict --jobs 5   # expected predictions for 2014-2018 (original cohort only)
  uv run python scripts/stage_a.py verify             # exact inventory check (models, hashes, predictions)

Both steps are resumable: models already in results/models_manifest.json are skipped if they were fitted with the
current harmonisation mappings (otherwise refitted; superseded entries go to models_manifest_superseded.json); predictions are recomputed
unless their provenance record matches the current model hash, data file and rows. Any failed job makes the
command exit non-zero. Stage B (after archiving) runs `predict --years 2019 2021 2022 2023 2024`.
"""
import argparse
import json
import sys
import time
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pipeline import (MANIFEST, MODELS, expected_models, fit_job, job_names, manifest_update, model_current,
                      prediction_years, predict_year, stage_a_jobs, verify_inventory)

ORIGINAL = (2014, 2015, 2016, 2017, 2018)
NEW = (2019, 2021, 2022, 2023, 2024)


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
    ap.add_argument("step", choices=["fit", "predict", "verify"])
    ap.add_argument("--jobs", type=int, default=5)
    ap.add_argument("--years", type=int, nargs="*", default=list(ORIGINAL))
    a = ap.parse_args()
    errors = []
    if a.step == "fit":
        manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
        done = {n for n, e in manifest.items() if model_current(e)}
        stale = sorted(set(manifest) - done)
        if stale:                       # keep a record of the superseded entries before they are overwritten
            sup = MANIFEST.with_name("models_manifest_superseded.json")
            old = json.loads(sup.read_text()) if sup.exists() else {}
            old.update({n: manifest[n] for n in stale})
            sup.write_text(json.dumps(dict(sorted(old.items())), indent=1))
            print(f"{len(stale)} models fitted with other harmonisation mappings will be refitted", flush=True)
        todo = [j for j in stage_a_jobs() if not all(n in done for n in job_names(j))]
        order = {"expgrad": 0, "lfr": 1, "gbm": 2, "rawgbm": 3, "peryear": 4}
        todo.sort(key=lambda j: (order[j["kind"]], j.get("state") is not None))
        print(f"{len(todo)} fit jobs to run", flush=True)
        with ProcessPoolExecutor(max_workers=a.jobs) as ex:
            for f in as_completed([ex.submit(_safe_fit, j) for j in todo]):
                job, entries, err, secs = f.result()
                if err:
                    errors.append(f"fit {job}: {err.strip().splitlines()[-1]}")
                    print(f"ERROR {job} after {secs:.0f}s\n{err}", flush=True)
                    continue
                manifest_update(entries)
                print(f"ok  {', '.join(e['name'] for e in entries)}  {secs:.0f}s", flush=True)
        missing = sorted(set(expected_models()) - set(json.loads(MANIFEST.read_text())))
        if missing:
            errors.append(f"models still missing: {missing}")
    elif a.step == "predict":
        manifest = json.loads(MANIFEST.read_text())
        missing = sorted(set(expected_models()) - set(manifest))
        if missing or any(not (MODELS / f"{n}.joblib").exists() for n in manifest):
            raise SystemExit(f"model inventory incomplete (missing: {missing[:5]}); run `fit` first")
        with ProcessPoolExecutor(max_workers=a.jobs) as ex:
            futs = [ex.submit(_safe_predict, [n for n in sorted(manifest) if y in prediction_years(n, manifest, [y])], y)
                    for y in a.years]
            for f in as_completed(futs):
                year, err, secs = f.result()
                if err:
                    errors.append(f"predict {year}: {err.strip().splitlines()[-1]}")
                print(("ERROR " + err) if err else f"ok  predictions {year}  {secs:.0f}s", flush=True)
        if not errors:
            verify_inventory(a.years)
            print("inventory check passed for", a.years)
    else:
        verify_inventory(a.years)
        print("inventory check passed for", a.years)
    if errors:
        print("\nFAILED:\n  " + "\n  ".join(errors), flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
