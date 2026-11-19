"""Integrity tests (QA 1, #5 and #6) on a smoke-mode inventory: tampering, stale or truncated artifacts and failing
workers must be detected. Run after a smoke fit and predict:

  RT_SMOKE_ROWS=20000 RT_SMOKE_TAG=it python scripts/stage_a.py fit --jobs 4
  RT_SMOKE_ROWS=20000 RT_SMOKE_TAG=it python scripts/stage_a.py predict --jobs 3
  RT_SMOKE_ROWS=20000 RT_SMOKE_TAG=it python scripts/test_integrity.py

Every test restores what it changed. Uses 2014-2018 only.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

assert os.environ.get("RT_SMOKE_ROWS"), "run in smoke mode only (RT_SMOKE_ROWS, RT_SMOKE_TAG)"
import numpy as np

import pipeline as P
from common import load_year

YEARS = [2014, 2015, 2016, 2017, 2018]
results = {}


def expect_fail(label, fn):
    try:
        fn()
    except Exception as e:                                     # noqa: BLE001 - any refusal counts
        results[label] = f"detected ({type(e).__name__}: {str(e)[:80]})"
        return
    results[label] = "NOT DETECTED"


def frame(year):
    df = load_year(year, columns=["ST", "SERIALNO", "PINCP"])
    return df.sample(n=int(P.SMOKE), random_state=0).reset_index(drop=True)


def backup(path):
    b = path.with_name(path.name + ".bak")
    shutil.copy2(path, b)
    return b


def restore(path, b):
    shutil.copy2(b, path)
    b.unlink()


def main():
    P.verify_inventory(YEARS, write_record=False)
    results["baseline inventory"] = "passes"
    manifest = json.loads(P.MANIFEST.read_text())
    name = "post_dp_race_s0"

    # 1. altered model bytes
    mp = P.MODELS / f"{name}.joblib"
    b = backup(mp)
    with open(mp, "ab") as f:
        f.write(b"\0")
    expect_fail("altered model bytes: load_model", lambda: P.load_model(name, manifest))
    expect_fail("altered model bytes: inventory", lambda: P.verify_inventory(YEARS, write_record=False))
    restore(mp, b)

    # 2. reordered / different rows
    df = frame(2015)
    P.load_pred(name, 2015, df)
    expect_fail("reordered rows", lambda: P.load_pred(name, 2015, df.iloc[::-1].reset_index(drop=True)))
    expect_fail("fewer rows", lambda: P.load_pred(name, 2015, df.iloc[:-1]))

    # 3. truncated prediction file
    arr, meta = P._pred_paths(name, 2016)
    b = backup(arr)
    np.save(arr, np.load(arr)[:-5])
    expect_fail("truncated predictions: load_pred", lambda: P.load_pred(name, 2016, frame(2016)))
    expect_fail("truncated predictions: inventory", lambda: P.verify_inventory(YEARS, write_record=False))
    restore(arr, b)

    # 4. prediction made by a different model version (stale provenance record)
    mb = backup(meta)
    m = json.loads(meta.read_text()); m["model_sha256"] = "0" * 64; meta.write_text(json.dumps(m))
    expect_fail("stale model hash in prediction record", lambda: P.verify_inventory(YEARS, write_record=False))
    restore(meta, mb)

    # 5. interrupted write: a leftover temporary file must not be taken for a prediction
    tmp = arr.with_suffix(".tmp.npy"); np.save(tmp, np.zeros(3, np.float32))
    P.verify_inventory(YEARS, write_record=False)
    tmp.unlink()
    results["leftover temporary file"] = "ignored (inventory still passes)"

    # 6. missing model in the manifest
    man_b = backup(P.MANIFEST)
    cur = json.loads(P.MANIFEST.read_text()); cur.pop("state6_gbm_s0", None) or cur.pop(sorted(cur)[0])
    P.MANIFEST.write_text(json.dumps(cur))
    expect_fail("model missing from manifest", lambda: P.verify_inventory(YEARS, write_record=False))
    restore(P.MANIFEST, man_b)

    # 7. failing worker -> non-zero exit (a year without data)
    r = subprocess.run([sys.executable, "-W", "ignore", str(ROOT / "scripts" / "stage_a.py"), "predict",
                        "--jobs", "1", "--years", "2013"], capture_output=True, text=True, env=os.environ)
    results["failing worker exit code"] = f"{r.returncode} ({'detected' if r.returncode != 0 else 'NOT DETECTED'})"

    P.verify_inventory(YEARS, write_record=False)
    results["inventory after restore"] = "passes"
    for k, v in results.items():
        print(f"{k:45s} {v}")
    bad = [k for k, v in results.items() if "NOT DETECTED" in v]
    out = ROOT / "results" / "validation"; out.mkdir(parents=True, exist_ok=True)
    (out / "integrity_tests.json").write_text(json.dumps(results, indent=1))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
