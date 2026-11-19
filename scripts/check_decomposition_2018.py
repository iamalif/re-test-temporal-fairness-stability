"""Pre-archiving validation of the decomposition (pre-registration 8.4) on the original cohort: 2014 -> 2018.

A frozen model's DP depends only on the features, so after reweighting 2014 rows to the 2018 feature
distribution the reweighted DP must match the 2018 DP (conditional component near 0, tolerance 0.005).
Writes results/stage_a/decomposition_2018_check.json.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from stage_b_secondary import STAGE_A, decompose, frame, p3_prior_shift, thresholds


def main():
    frames = {y: frame(y) for y in (2014, 2018)}
    thr = thresholds(frames)
    out = []
    for lk in ("nominal", "inflation", "base_rate"):
        d = decompose("gbm_s0", 0, 2018, frames, thr, lk)
        d["P3"] = {g: p3_prior_shift(d["m2014"], d["m_year"], g) for g in ("race", "sex")}
        out.append(d)
        print(lk, "AUC 2014 vs 2018:", round(d["auc_2014_vs_year"], 4), "| DP check:", d["dp_check"],
              "| composition acc %.4f, conditional acc %.4f" % (d["composition"]["accuracy"],
                                                               d["conditional"]["accuracy"]))
    STAGE_A.mkdir(parents=True, exist_ok=True)
    (STAGE_A / "decomposition_2018_check.json").write_text(
        json.dumps({"thresholds": thr, "results": out}, indent=1, default=float))


if __name__ == "__main__":
    main()
