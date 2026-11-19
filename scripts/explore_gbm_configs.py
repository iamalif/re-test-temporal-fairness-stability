"""EXPLORATORY (2014-2018 data only): which GBM configuration reproduces the published numbers?

Target: Ding et al. Table 2, US-level unconstrained GBM on 2018 data: accuracy 81.7%, DP 17.7%.
Results are appended to results/exploratory/gbm_configs.jsonl. Not part of the confirmatory pipeline.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier

from common import RESULTS, evaluate, folktables_matrix, label, load_year, state_split

CONFIGS = {
    "literal_exp_5x5": dict(loss="exponential", n_estimators=5, max_depth=5),
    "exp_50x5": dict(loss="exponential", n_estimators=50, max_depth=5),
    "exp_100x5": dict(loss="exponential", n_estimators=100, max_depth=5),
    "sk_default": dict(),
}

def main(year: int, names: list[str], seed: int = 0):
    df = load_year(year)
    X, y, race = folktables_matrix(df), label(df), df["RAC1P"].to_numpy()
    test = state_split(df, seed)
    out = RESULTS / "exploratory"
    out.mkdir(parents=True, exist_ok=True)
    for name in names:
        t = time.time()
        m = GradientBoostingClassifier(random_state=seed, **CONFIGS[name]).fit(X[~test], y[~test])
        r = evaluate(m.predict(X[test]), y[test], race[test])
        r.update(config=name, params=CONFIGS[name], train_year=year, test_year=year, seed=seed,
                 n_train=int((~test).sum()), fit_seconds=round(time.time() - t, 1))
        print(json.dumps({k: r[k] for k in ("config", "accuracy", "dp", "eo", "fit_seconds", "n_train")}))
        with open(out / "gbm_configs.jsonl", "a") as f:
            f.write(json.dumps(r) + "\n")

if __name__ == "__main__":
    main(int(sys.argv[1]), sys.argv[2:])
