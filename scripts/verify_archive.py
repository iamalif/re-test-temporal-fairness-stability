"""Build and verify the pre-registration archive package; create the guard flag only after verification
(pre-registration 10; QA 2 A9, QA 3 A3-1).

  python scripts/verify_archive.py build                 # writes archive/package.zip and a receipt draft
  (upload archive/package.zip to Zenodo, publish, save the repository in Software Heritage, then fill
   zenodo_record, doi, swh_id and swh_checked_by_hand_on in prereg/ARCHIVE_RECEIPT.json)
  python scripts/verify_archive.py verify [--create-flag]

verify (1) recomputes SHA-256, MD5 and size of archive/package.zip and compares them with the receipt;
(2) opens the package itself (no extraction; unsafe member paths rejected) and hashes every member; requires the
complete inventory: the pre-registration, code, lock file, every Stage A and validation result, the harmonisation
report and provenance table, and every frozen model file listed in the package's model manifest with the hash
recorded there; (3) requires each of these reference files to exist locally with the same bytes as in the package;
(4) reads the public Zenodo record and checks that it is published, has the receipt's DOI and lists exactly the
package with the same MD5 and size; (5) requires the Software Heritage identifier and the date it was checked by
hand (Software Heritage is not queried automatically). Only then does --create-flag write prereg/ARCHIVED.
"""
import argparse
import hashlib
import json
import sys
import time
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "archive/package.zip"
REQUIRED = ["prereg/PREREGISTRATION.md", "prereg/OUTPUT_CHECKLIST.md", "uv.lock", "pyproject.toml",
            "results/models_manifest.json", "results/stage_a/margins.json", "results/stage_a/estimates_2014_2018.json",
            "results/stage_a/geographic_pairs_2014.csv", "results/stage_a/recoding_check.json",
            "results/stage_a/decomposition_2018_check.json", "results/validation/split_variance.json",
            "results/validation/inference_validation.json", "results/validation/integrity_tests.json",
            "results/validation/analysis_tests.json", "results/validation/fetch_tests.json",
            "results/validation/spec_tests.json", "results/harmonisation/report_2014_2018.json",
            "docs/harmonisation_provenance.md", "logs/decision_log.md", "logs/raw_sha256.txt",
            "results/validation/archive_tests.json"] + [f"results/data_provenance/acsincome_{y}.json"
                                                         for y in (2014, 2015, 2016, 2017, 2018)]
CODE_DIRS = ("src", "scripts", "prereg", "results", "docs", "logs", "paper")
REFERENCE_INPUTS = ("data/raw/dictionaries", "data/raw/crosswalk", "data/raw/variable_changes", "data/raw/cpi")
# non-person reference inputs (public-domain US government documents); Census person files are never packaged
EXCLUDE = ("docs/sources/", "__pycache__", ".DS_Store")


def digest(path: Path, algo: str) -> str:
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def inventory(root: Path = ROOT) -> list:
    """The one inventory policy shared by build and verify (QA 4, A4-1): every file under the code, plan, result,
    documentation, log and manuscript folders (all file types, shell scripts included), the lock and project files,
    and every frozen model file in the model manifest; generated receipt/flag files and third-party papers excluded."""
    manifest = json.loads((root / "results" / "models_manifest.json").read_text())
    members = [p for d in CODE_DIRS for p in sorted((root / d).rglob("*")) if p.is_file()
               and not any(x in p.relative_to(root).as_posix() for x in EXCLUDE)
               and p.name not in ("ARCHIVED", "ARCHIVE_RECEIPT.json")]
    members += [root / "uv.lock", root / "pyproject.toml", root / "README.md", root / "LICENSE"]
    members += [p for d in REFERENCE_INPUTS for p in sorted((root / d).rglob("*")) if p.is_file()]
    members += [root / "data" / "derived" / "models" / e["file"] for e in manifest.values()]
    return [p.relative_to(root).as_posix() for p in members if p.exists()]


def build(root: Path = ROOT) -> None:
    members = [root / rel for rel in inventory(root)]
    out = root / PACKAGE
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in members:
            z.write(p, p.relative_to(root).as_posix())
    rec = {"zenodo_record": "", "doi": "", "swh_id": "", "swh_checked_by_hand_on": "",
           "files": [{"name": "package.zip", "local_path": PACKAGE, "sha256": digest(out, "sha256"),
                      "md5": digest(out, "md5"), "size": out.stat().st_size}],
           "built": time.strftime("%Y-%m-%dT%H:%M:%S"), "n_members": len(members)}
    (root / "prereg" / "ARCHIVE_RECEIPT.json").write_text(json.dumps(rec, indent=1))
    print(f"wrote {PACKAGE} ({len(members)} members, {out.stat().st_size / 1e6:.0f} MB) and the receipt draft")


def package_hashes(path: Path) -> dict:
    out = {}
    with zipfile.ZipFile(path) as z:
        for info in z.infolist():
            name = PurePosixPath(info.filename)
            if name.is_absolute() or ".." in name.parts:
                raise ValueError(f"unsafe member path in package: {info.filename}")
            h = hashlib.sha256()
            with z.open(info) as f:
                for chunk in iter(lambda: f.read(1 << 22), b""):
                    h.update(chunk)
            out[info.filename] = h.hexdigest()
    return out


def fetch_zenodo(record: str) -> dict:
    with urllib.request.urlopen(f"https://zenodo.org/api/records/{record}", timeout=60) as r:
        return json.load(r)


def verify(root: Path = ROOT, fetch=fetch_zenodo) -> list:
    rec = json.loads((root / "prereg" / "ARCHIVE_RECEIPT.json").read_text())
    problems = []
    files = rec.get("files", [])
    if len(files) != 1 or files[0].get("local_path") != PACKAGE:
        return [f"the receipt must list exactly {PACKAGE}"]
    f = files[0]
    pkg = root / PACKAGE
    if not pkg.exists():
        return [f"{PACKAGE} missing locally"]
    for algo in ("sha256", "md5"):
        if digest(pkg, algo) != f.get(algo):
            problems.append(f"package {algo} differs from the receipt")
    if pkg.stat().st_size != f.get("size"):
        problems.append("package size differs from the receipt")
    try:
        inside = package_hashes(pkg)
    except (ValueError, zipfile.BadZipFile) as e:
        return problems + [str(e)]
    for rel in REQUIRED:
        if rel not in inside:
            problems.append(f"package lacks {rel}")
        elif not (root / rel).exists():
            problems.append(f"{rel} missing locally")
        elif digest(root / rel, "sha256") != inside[rel]:
            problems.append(f"{rel}: local file differs from the archived one")
    for rel in inventory(root):        # complete inventory, every member byte-identical to the local file
        if rel not in inside:
            problems.append(f"package lacks {rel}")
        elif digest(root / rel, "sha256") != inside[rel]:
            problems.append(f"{rel}: local file differs from the archived one")
    if "results/models_manifest.json" in inside:
        with zipfile.ZipFile(pkg) as z:
            manifest = json.loads(z.read("results/models_manifest.json"))
        for name, e in manifest.items():
            m = f"data/derived/models/{e['file']}"
            if m not in inside:
                problems.append(f"package lacks model file {m}")
            elif inside[m] != e["sha256"]:
                problems.append(f"model file {m} in the package differs from its manifest hash")
    try:
        z = fetch(rec.get("zenodo_record", ""))
        files_ = z.get("files", [])
        if isinstance(files_, dict):            # InvenioRDM layout: {"entries": {key: {...}}}
            files_ = list(files_.get("entries", {}).values())
        remote = {x["key"]: x for x in files_}
        if set(remote) != {"package.zip"}:
            problems.append(f"Zenodo record lists {sorted(remote)}, expected exactly package.zip")
        x = remote.get("package.zip")
        if x and (str(x.get("checksum", "")).removeprefix("md5:") != f.get("md5") or x.get("size") != f.get("size")):
            problems.append("Zenodo checksum or size differs from the receipt")
        if not rec.get("doi") or z.get("doi") != rec.get("doi"):
            problems.append(f"DOI differs or missing: record {z.get('doi')}, receipt {rec.get('doi')}")
        if z.get("status", "published") != "published" and not z.get("submitted", False):
            problems.append("Zenodo record is not published")
    except Exception as e:                                     # noqa: BLE001 - any failure to verify is a failure
        problems.append(f"could not verify the Zenodo record: {e}")
    if not str(rec.get("swh_id", "")).startswith("swh:1:") or not rec.get("swh_checked_by_hand_on"):
        problems.append("Software Heritage identifier or the date of its manual check is missing")
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["build", "verify"])
    ap.add_argument("--create-flag", action="store_true")
    a = ap.parse_args()
    if a.step == "build":
        build()
        return
    problems = verify()
    if problems:
        print("ARCHIVE NOT VERIFIED:\n  " + "\n  ".join(problems))
        sys.exit(1)
    rec = json.loads((ROOT / "prereg" / "ARCHIVE_RECEIPT.json").read_text())
    print("archive verified:", rec["doi"])
    if a.create_flag:
        (ROOT / "prereg" / "ARCHIVED").write_text(json.dumps(
            {"doi": rec["doi"], "swh_id": rec["swh_id"], "swh_checked_by_hand_on": rec["swh_checked_by_hand_on"],
             "receipt_sha256": digest(ROOT / "prereg" / "ARCHIVE_RECEIPT.json", "sha256"),
             "verified": time.strftime("%Y-%m-%dT%H:%M:%S")}, indent=1))
        print("prereg/ARCHIVED created")


if __name__ == "__main__":
    main()
