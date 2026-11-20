"""Verify the archive receipt before the guard flag is created (pre-registration 10; QA 2, A9).

prereg/ARCHIVE_RECEIPT.json (written by hand after depositing) has the form
  {"zenodo_record": "1234567", "doi": "10.5281/zenodo.1234567", "swh_id": "swh:1:dir:...",
   "files": [{"name": "models.tar", "local_path": "archive/models.tar", "sha256": "...", "md5": "...", "size": 123}]}
This script (1) recomputes SHA-256, MD5 and size of every listed local file; (2) fetches the public Zenodo record
(https://zenodo.org/api/records/<id>) and checks that it lists exactly these files with the same MD5 checksums
and sizes; (3) checks that the deposited package contains the pre-registration, the model manifest and the Stage A
result files, by comparing their SHA-256 with the receipt; (4) only then, with --create-flag, writes
prereg/ARCHIVED containing the DOI and the receipt's SHA-256. Exits non-zero on any mismatch.
"""
import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "prereg" / "ARCHIVE_RECEIPT.json"
REQUIRED_IN_PACKAGE = ("prereg/PREREGISTRATION.md", "results/models_manifest.json", "results/stage_a/margins.json",
                       "results/stage_a/estimates_2014_2018.json", "results/validation/split_variance.json",
                       "results/validation/inference_validation.json", "uv.lock")


def digest(path: Path, algo: str) -> str:
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--create-flag", action="store_true")
    a = ap.parse_args()
    rec = json.loads(RECEIPT.read_text())
    problems = []
    for f in rec["files"]:
        p = ROOT / f["local_path"]
        if not p.exists():
            problems.append(f"local file missing: {f['local_path']}")
            continue
        for algo in ("sha256", "md5"):
            if digest(p, algo) != f[algo]:
                problems.append(f"{f['name']}: local {algo} differs from receipt")
        if p.stat().st_size != f["size"]:
            problems.append(f"{f['name']}: local size differs from receipt")
    url = f"https://zenodo.org/api/records/{rec['zenodo_record']}"
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            z = json.load(r)
        remote = {x["key"]: x for x in z.get("files", [])}
        if set(remote) != {f["name"] for f in rec["files"]}:
            problems.append(f"Zenodo file list differs: {sorted(remote)}")
        for f in rec["files"]:
            x = remote.get(f["name"])
            if x and (x.get("checksum", "").removeprefix("md5:") != f["md5"] or x.get("size") != f["size"]):
                problems.append(f"{f['name']}: Zenodo checksum or size differs")
        if z.get("doi") and z["doi"] != rec["doi"]:
            problems.append(f"DOI differs: {z['doi']}")
    except OSError as e:
        problems.append(f"could not read the Zenodo record: {e}")
    inside = rec.get("package_contents_sha256", {})
    for rel in REQUIRED_IN_PACKAGE:
        if rel not in inside:
            problems.append(f"receipt does not list {rel} in the package")
        elif (ROOT / rel).exists() and digest(ROOT / rel, "sha256") != inside[rel]:
            problems.append(f"{rel}: current file differs from the archived one")
    if problems:
        print("ARCHIVE NOT VERIFIED:\n  " + "\n  ".join(problems))
        sys.exit(1)
    print("archive verified:", rec["doi"])
    if a.create_flag:
        (ROOT / "prereg" / "ARCHIVED").write_text(json.dumps(
            {"doi": rec["doi"], "swh_id": rec.get("swh_id"), "receipt_sha256": digest(RECEIPT, "sha256")}, indent=1))
        print("prereg/ARCHIVED created")


if __name__ == "__main__":
    main()
