"""EXPLORATORY (2014-2018 only): does standardising each year with its own scaler reproduce the
steeper accuracy decline in Ding et al. Figure 4?

Hypothesis: features standardised with a StandardScaler fitted separately on each year's data. Trees are
invariant to a common affine map, but not to year-specific ones, so a 2014 model sees shifted inputs later.
Uses the warm-started 2014 model from explore_gbm_trees.py. Prints staged metrics at selected tree counts.
"""
import pickle
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd

from common import DERIVED, FEATURES, RESULTS, dp_gap, folktables_matrix, label, load_year, state_split

KEEP = (50, 100, 150, 200, 300)


def stats_of(X):
    return X.mean(0), X.std(0)


def main(seed=0):
    m = pickle.loads((DERIVED / "tmp" / f"gbm_exp_d5_2014_seed{seed}.pkl").read_bytes())
    d14 = load_year(2014, columns=FEATURES + ["PINCP", "ST"])
    X14 = folktables_matrix(d14)
    tr14 = ~state_split(d14, seed)
    mu14, sd14 = stats_of(X14[tr14])       # scaler fitted on the 2014 training split
    del d14, X14
    rows = []
    for ey in (2014, 2015, 2016, 2017, 2018):
        de = load_year(ey, columns=FEATURES + ["PINCP", "ST"])
        te = state_split(de, seed)
        X = folktables_matrix(de)
        y, r = label(de)[te], de["RAC1P"].to_numpy()[te]
        variants = {}
        for name, (mu, sd) in {"scaler_per_year_all": stats_of(X),
                               "scaler_per_year_train": stats_of(X[~te])}.items():
            Z = (X[te] - mu) / sd                     # what a per-year scaler would feed the model
            variants[name] = Z * sd14 + mu14          # same thing expressed on the model's raw scale
        variants["common_scaler"] = X[te]
        for name, Xt in variants.items():
            for k, p in enumerate(m.staged_predict(Xt), start=1):
                if k in KEEP:
                    rows.append(dict(variant=name, eval_year=ey, n_estimators=k,
                                     accuracy=float((p == y).mean()), dp=dp_gap(p, r)))
        del de, X
    res = pd.DataFrame(rows)
    out = RESULTS / "exploratory"; out.mkdir(parents=True, exist_ok=True)
    res.to_csv(out / "scaling_hypothesis.csv", index=False)
    print(res[res.n_estimators == 100].pivot(index="variant", columns="eval_year",
                                              values=["accuracy", "dp"]).round(4).to_string())


if __name__ == "__main__":
    main()
