"""Equivalence check for the inference-only migration (D033): compare every Stage A result file now on disk with its
version in a git commit (default HEAD, i.e. before the reruns were committed), ignoring provenance blocks (which
record hashes, commit and time and are expected to change). JSON files are compared value by value, CSV files byte
by byte. Writes results/validation/migration_equivalence.json; exits non-zero if any scientific content differs.
  uv run python scripts/compare_results_to_commit.py [commit]
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ["results/stage_a/margins.json", "results/stage_a/estimates_2014_2018.json",
         "results/stage_a/recoding_check.json", "results/stage_a/decomposition_2018_check.json",
         "results/stage_a/geographic_pairs_2014.csv", "results/stage_a/metrics_us_2014_2018.csv",
         "results/validation/split_variance.json", "results/validation/inference_validation.json",
         "results/validation/integrity_tests.json", "results/inventory_check.json"]
SKIP_KEYS = {"provenance", "_provenance", "time", "_script_sha256", "code_sha256"}


def strip(o):
    if isinstance(o, dict):
        return {k: strip(v) for k, v in o.items() if k not in SKIP_KEYS}
    if isinstance(o, list):
        return [strip(v) for v in o]
    return o


def diff(a, b, path="", out=None):
    out = [] if out is None else out
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b), key=str):
            if k not in a or k not in b:
                out.append(f"{path}/{k}: only in {'new' if k in b else 'old'}")
            else:
                diff(a[k], b[k], f"{path}/{k}", out)
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            diff(x, y, f"{path}[{i}]", out)
    elif a != b and not (isinstance(a, float) and isinstance(b, float) and a != a and b != b):
        out.append(f"{path}: {str(a)[:60]} -> {str(b)[:60]}")
    return out


def main():
    commit = sys.argv[1] if len(sys.argv) > 1 else "HEAD"
    commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", commit], capture_output=True, text=True,
                            check=True).stdout.strip()
    report, bad = {}, False
    for rel in FILES:
        old_b = subprocess.run(["git", "-C", str(ROOT), "show", f"{commit}:{rel}"], capture_output=True).stdout
        new_b = (ROOT / rel).read_bytes()
        if rel.endswith(".csv"):
            d = [] if old_b == new_b else ["bytes differ"]
        else:
            d = diff(strip(json.loads(old_b)), strip(json.loads(new_b)))
        report[rel] = {"identical_scientific_content": not d, "differences": d[:20]}
        bad |= bool(d)
        print(f"{'same   ' if not d else 'DIFFERS'} {rel}" + (f"  e.g. {d[0]}" if d else ""))
    (ROOT / "results/validation/migration_equivalence.json").write_text(json.dumps(
        {"baseline_commit": commit, "ignored_keys": sorted(SKIP_KEYS),
         "files": report, "all_identical": not bad}, indent=1))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
