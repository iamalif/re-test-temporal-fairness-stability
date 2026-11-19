"""Pre-archiving falsification check of the decomposition (pre-registration 8.4) on the original cohort: 2014 -> 2018.

A frozen model's DP depends only on the features, so after reweighting 2014 rows to the 2018 feature distribution
the reweighted DP must match the 2018 DP (residual near 0, tolerance 0.005). Passing is necessary, not sufficient:
the same run reports the balance, overlap, effective-sample-size and clipping diagnostics and the pre-specified
reliability rule (DP check, max group-wise SMD <= 0.05, clipping sensitivity <= 0.005).
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
        dg = d["diagnostics"]
        print(f"{lk}: AUC {d['auc_2014_vs_year']:.4f} | DP residual race {d['dp_check']['race']['residual']:+.4f} "
              f"sex {d['dp_check']['sex']['residual']:+.4f} | acc composition {d['composition']['accuracy']:+.4f} "
              f"residual {d['residual']['accuracy']:+.4f} | ESS {dg['ess_fraction']:.3f} | max SMD by group "
              f"{max(dg['max_smd_by_group'].values()):.3f} | clip shift {d['clip_sensitivity_accuracy']:.4f} "
              f"| reliable {d['reliable']}")
    STAGE_A.mkdir(parents=True, exist_ok=True)
    (STAGE_A / "decomposition_2018_check.json").write_text(
        json.dumps({"thresholds": thr, "results": out}, indent=1, default=float))


if __name__ == "__main__":
    main()
