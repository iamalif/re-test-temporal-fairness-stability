"""EXPLORATORY (2014-2018 only): accuracy and DP of an exponential-loss, depth-5 GBM as trees are added.

Grows the model in chunks with warm_start so each call stays short, then records staged metrics
(n_estimators = 1..N) for the test split. Usage: explore_gbm_trees.py TRAIN_YEAR TARGET_TREES [SEED] [EVAL_YEARS...]
(evaluation years default to the training year; each year uses its own within-state 80/20 split)
Writes results/exploratory/gbm_trees_<year>_seed<seed>.csv and keeps the model in data/derived/tmp/.
"""
import pickle
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier

from common import DERIVED, FEATURES, RESULTS, dp_gap, eo_gap, folktables_matrix, label, load_year, state_split

CHUNK = 100


def main(year: int, target: int, seed: int = 0, eval_years=None):
    eval_years = eval_years or [year]
    tmp = DERIVED / "tmp"; tmp.mkdir(parents=True, exist_ok=True)
    mpath = tmp / f"gbm_exp_d5_{year}_seed{seed}.pkl"
    df = load_year(year, columns=FEATURES + ["PINCP", "ST"])
    X, y, race = folktables_matrix(df), label(df), df["RAC1P"].to_numpy()
    test = state_split(df, seed)
    if mpath.exists():
        m = pickle.loads(mpath.read_bytes())
    else:
        m = GradientBoostingClassifier(loss="exponential", max_depth=5, n_estimators=0,
                                       warm_start=True, random_state=seed)
    t0 = time.time()
    while m.n_estimators < target and time.time() - t0 < 100:
        m.n_estimators = min(target, m.n_estimators + CHUNK)
        m.fit(X[~test], y[~test])
        mpath.write_bytes(pickle.dumps(m))
        print("trees", m.n_estimators, round(time.time() - t0, 1), flush=True)
    if m.n_estimators >= target:
        rows = []
        for ey in eval_years:
            if ey == year:
                Xt, yt, rt = X[test], y[test], race[test]
            else:
                de = load_year(ey, columns=FEATURES + ["PINCP", "ST"])
                te = state_split(de, seed)
                Xt, yt, rt = folktables_matrix(de)[te], label(de)[te], de["RAC1P"].to_numpy()[te]
            for k, p in enumerate(m.staged_predict(Xt), start=1):
                if k in (1, 2, 5, 10, 20, 50) or k % 25 == 0:
                    rows.append(dict(train_year=year, eval_year=ey, n_estimators=k,
                                     accuracy=float((p == yt).mean()), dp=dp_gap(p, rt),
                                     eo=eo_gap(p, yt, rt), pos_rate=float(p.mean())))
        out = RESULTS / "exploratory"; out.mkdir(parents=True, exist_ok=True)
        res = pd.DataFrame(rows)
        res.to_csv(out / f"gbm_trees_train{year}_seed{seed}.csv", index=False)
        print(res.pivot(index="n_estimators", columns="eval_year", values=["accuracy", "dp"]).round(4).to_string())


if __name__ == "__main__":
    a = sys.argv[1:]
    main(int(a[0]), int(a[1]), int(a[2]) if len(a) > 2 else 0, [int(v) for v in a[3:]] or None)
