"""Paper outputs for the reconstruction (2014-2018 only): figure and LaTeX number macros.

Inputs: results/reconstruction/runs.jsonl, figure4_digitised.json, figure13_digitised.json.
Outputs: paper/figures/reconstruction.pdf, paper/numbers_reconstruction.tex
Every reconstruction number quoted in the paper comes from the macros written here.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REC = ROOT / "results" / "reconstruction"
YEARS = [2014, 2015, 2016, 2017, 2018]
INK, MUTED, GRID = "#1f1f1e", "#6b6a64", "#e4e3de"
PUBLISHED = "#4a4a46"
COL = {"per_year": "#2a78d6", "common": "#eb6834"}            # categorical slots 1 and 2
LAB = {"per_year": "Ours, each year standardised separately", "common": "Ours, frozen 2014 standardisation"}


def runs():
    rs = [json.loads(l) for l in (REC / "runs.jsonl").read_text().splitlines() if l.strip()]
    return [r for r in rs if r["status"] == "ok"]


def series(rs, method, constraint, scaling, trees, metric, seeds=None):
    out = []
    for r in rs:
        j = r["job"]
        if (j["method"], j["constraint"], j["scaling"], j["n_trees"]) == (method, constraint, scaling, trees) \
                and (seeds is None or j["seed"] in seeds):
            out.append([r["eval"][str(y)][metric] for y in YEARS])
    return np.array(out)


def figure(rs, f4):
    plt.rcParams.update({"font.size": 8, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED,
                         "ytick.color": MUTED, "font.family": "serif"})
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.4), constrained_layout=True)
    for ax, metric, title in zip(axes, ("accuracy", "dp"), ("Accuracy", "Demographic-parity gap (White − Black)")):
        pub = f4["GBM"][metric]
        ax.plot(YEARS, pub, color=PUBLISHED, lw=2, marker="o", ms=4, label="Published (Fig. 4, digitised)",
                zorder=3)
        for sc in ("per_year", "common"):
            s = series(rs, "gbm", "none", sc, 100, metric)
            ax.fill_between(YEARS, s.min(0), s.max(0), color=COL[sc], alpha=0.18, lw=0)
            ax.plot(YEARS, s.mean(0), color=COL[sc], lw=2, marker="s", ms=3.5, label=LAB[sc], zorder=2)
        ax.set_title(title, fontsize=8, color=INK, loc="left")
        ax.set_xticks(YEARS)
        ax.grid(axis="y", color=GRID, lw=0.6)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    axes[1].set_ylim(0, 0.2)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.12), fontsize=7)
    out = ROOT / "paper" / "figures"
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / "reconstruction.pdf", bbox_inches="tight")
    fig.savefig(out / "reconstruction.png", dpi=200, bbox_inches="tight")


def macros(rs, f4, f13):
    m = {}
    def put(k, v, fmt="{:.3f}"):
        m[k] = fmt.format(v)
    lit = np.vstack([series(rs, "gbm", "none", sc, 5, "accuracy") for sc in ("common", "per_year")])
    gaps = np.array(f4["GBM"]["accuracy"])[None, :] - lit          # every seed, scaling and year
    put("LiteralAccGapMean", gaps.mean(), "{:.2f}")
    put("LiteralAccGapMin", gaps.min(), "{:.2f}")
    put("LiteralAccGapMax", gaps.max(), "{:.2f}")
    for sc, tag in (("per_year", "PerYear"), ("common", "Common")):
        for n in (50, 100, 200):
            acc = series(rs, "gbm", "none", sc, n, "accuracy").mean(0)
            put(f"AccMeanDevTrees{ {50: 'L', 100: 'C', 200: 'CC'}[n] }{tag}", np.abs(acc - np.array(f4["GBM"]["accuracy"])).mean(), "{:.4f}")
    for sc, tag in (("per_year", "PerYear"), ("common", "Common")):
        acc = series(rs, "gbm", "none", sc, 100, "accuracy")
        dp = series(rs, "gbm", "none", sc, 100, "dp")
        eo = series(rs, "gbm", "none", sc, 100, "eo")
        dev = np.abs(acc.mean(0) - np.array(f4["GBM"]["accuracy"]))
        put(f"AccMaxDev{tag}", dev.max(), "{:.4f}")
        put(f"AccMeanDev{tag}", dev.mean(), "{:.4f}")
        put(f"AccDecline{tag}", acc.mean(0)[0] - acc.mean(0)[-1], "{:.3f}")
        put(f"AccDeclineSD{tag}", np.std(acc[:, 0] - acc[:, -1], ddof=1), "{:.4f}")
        put(f"DPMin{tag}", dp.mean(0).min()); put(f"DPMax{tag}", dp.mean(0).max())
        put(f"EOMin{tag}", eo.mean(0).min()); put(f"EOMax{tag}", eo.mean(0).max())
    pa = np.array(f4["GBM"]["accuracy"])
    put("PubAccDecline", pa[0] - pa[-1]); put("PubAccFirst", pa[0]); put("PubAccLast", pa[-1])
    put("PubDPMin", min(f4["GBM"]["dp"])); put("PubDPMax", max(f4["GBM"]["dp"]))
    put("PubEOMin", min(f13["GBM"]["eo"])); put("PubEOMax", max(f13["GBM"]["eo"]))
    common = series(rs, "gbm", "none", "common", 100, "accuracy").mean(0)
    m["ShareDeclinePerYearOnly"] = "{:.0f}\\%".format(100 * (1 - (common[0] - common[-1]) / (pa[0] - pa[-1])))
    for key, name, method, cons in (("LFR", "GBM w/ LFR", "lfr", "dp"), ("ExpGrad", "GBM w/ ExpGrad (DP)", "expgrad", "dp"),
                                    ("Post", "GBM w/ Postprocessing (DP)", "postprocessing", "dp")):
        for sc, tag in (("per_year", "PerYear"), ("common", "Common")):
            acc = series(rs, method, cons, sc, 100, "accuracy").mean(0)
            dp = series(rs, method, cons, sc, 100, "dp").mean(0)
            put(f"{key}AccMaxDev{tag}", np.abs(acc - np.array(f4[name]["accuracy"])).max(), "{:.3f}")
            put(f"{key}DPMaxDev{tag}", np.abs(dp - np.array(f4[name]["dp"])).max(), "{:.3f}")
    post_eo = series(rs, "postprocessing", "eo", "per_year", 100, "accuracy").mean(0)
    put("PostEOAccGap", (post_eo - np.array(f13["GBM w/ Postprocessing (EO)"]["accuracy"])).mean(), "{:.3f}")
    lines = ["% generated by scripts/make_reconstruction_outputs.py - do not edit"]
    lines += [f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in sorted(m.items())]
    (ROOT / "paper").mkdir(exist_ok=True)
    (ROOT / "paper" / "numbers_reconstruction.tex").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def main():
    rs = runs()
    f4 = json.loads((REC / "figure4_digitised.json").read_text())["series"]
    f13 = json.loads((REC / "figure13_digitised.json").read_text())["series"]
    figure(rs, f4)
    macros(rs, f4, f13)


if __name__ == "__main__":
    main()
