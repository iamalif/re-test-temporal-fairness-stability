"""Build and verify the pre-registration archive package; create the guard flag only after verification
(pre-registration 10; QA 2 A9, QA 3 A3-1, QA 4 A4-1, freeze review FZ-2).

  python scripts/verify_archive.py freeze-references     # writes results/reference_inputs.json (commit it)
  python scripts/verify_archive.py build                 # writes archive/package.zip and a receipt draft
  (upload archive/package.zip to Zenodo, publish, save the repository in Software Heritage, then fill
   zenodo_record, doi, swh_id and swh_checked_by_hand_on in prereg/ARCHIVE_RECEIPT.json)
  python scripts/verify_archive.py verify [--create-flag]

The package holds exactly: every file of the archived git commit (taken from the commit itself), the non-person
reference inputs listed with their SHA-256 in that commit's results/reference_inputs.json, and the frozen model files
listed in that commit's results/models_manifest.json. build requires a clean tracked working tree and records HEAD.

verify requires, and only then does --create-flag write prereg/ARCHIVED:
 (1) the receipt names an existing commit, the checkout is at that commit and its tracked files are unchanged;
 (2) the package's SHA-256, MD5 and size equal the receipt's; no unsafe or duplicate member names;
 (3) the package's member set equals the expected set exactly (nothing missing, nothing extra);
 (4) every committed member equals its git blob in that commit and the local file; every reference input equals
     its frozen hash and the local file; every model file equals its manifest hash and the local file;
 (5) the public Zenodo record is published, has the receipt's DOI and lists exactly package.zip with the same MD5
     and size;
 (6) the Software Heritage identifier is the revision of the archived commit (swh:1:rev:<commit>) and the date of
     its manual check is recorded (Software Heritage is not queried automatically).
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "archive/package.zip"
RECEIPT = "prereg/ARCHIVE_RECEIPT.json"
FLAG = "prereg/ARCHIVED"
REFERENCE_LIST = "results/reference_inputs.json"
MANIFEST = "results/models_manifest.json"
REFERENCE_INPUTS = ("data/raw/dictionaries", "data/raw/crosswalk", "data/raw/variable_changes", "data/raw/cpi")
# non-person reference inputs (public US government documents); Census person files are never packaged
REQUIRED = ["prereg/PREREGISTRATION.md", "prereg/OUTPUT_CHECKLIST.md", "uv.lock", "pyproject.toml", "LICENSE",
            MANIFEST, REFERENCE_LIST, "results/stage_a/margins.json", "results/stage_a/estimates_2014_2018.json",
            "results/stage_a/geographic_pairs_2014.csv", "results/stage_a/recoding_check.json",
            "results/stage_a/decomposition_2018_check.json", "results/validation/split_variance.json",
            "results/validation/inference_validation.json", "results/validation/integrity_tests.json",
            "results/validation/analysis_tests.json", "results/validation/fetch_tests.json",
            "results/validation/spec_tests.json", "results/validation/archive_tests.json",
            "results/validation/inference_only_export.json", "results/harmonisation/report_2014_2018.json",
            "docs/harmonisation_provenance.md", "logs/decision_log.md", "logs/raw_sha256.txt"] + [
    f"results/data_provenance/acsincome_{y}.json" for y in (2014, 2015, 2016, 2017, 2018)]
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


def digest(path: Path, algo: str = "sha256") -> str:
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def git(root: Path, *args, binary: bool = False):
    out = subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=True).stdout
    return out if binary else out.decode()


def commit_files(root: Path, commit: str) -> list:
    return sorted(x for x in git(root, "ls-tree", "-r", "--name-only", "-z", commit).split("\0") if x)


def blob(root: Path, commit: str, rel: str) -> bytes:
    return git(root, "cat-file", "blob", f"{commit}:{rel}", binary=True)


def freeze_references(root: Path = ROOT) -> dict:
    """List every file now under REFERENCE_INPUTS with its SHA-256 and size (to be committed before build)."""
    files = {p.relative_to(root).as_posix(): {"sha256": digest(p), "size": p.stat().st_size}
             for d in REFERENCE_INPUTS for p in sorted((root / d).rglob("*")) if p.is_file()}
    (root / REFERENCE_LIST).write_text(json.dumps({"directories": list(REFERENCE_INPUTS), "files": files}, indent=1))
    return files


def expected(root: Path, commit: str) -> dict:
    """{member: ('commit'|'reference'|'model', frozen sha256 or None)} for the archive of a commit."""
    out = {rel: ("commit", None) for rel in commit_files(root, commit)}
    refs = json.loads(blob(root, commit, REFERENCE_LIST))["files"]
    for rel, e in refs.items():
        if rel in out or not any(rel.startswith(d + "/") for d in REFERENCE_INPUTS):
            raise ValueError(f"reference list entry not allowed: {rel}")
        out[rel] = ("reference", e["sha256"])
    for name, e in json.loads(blob(root, commit, MANIFEST)).items():
        rel = f"data/derived/models/{e['file']}"
        if rel in out:
            raise ValueError(f"model file listed twice: {rel}")
        out[rel] = ("model", e["sha256"])
    return out


def clean_checkout(root: Path) -> str:
    return git(root, "status", "--porcelain", "--untracked-files=no").strip()


def build(root: Path = ROOT) -> None:
    if not (root / ".git").exists():
        raise SystemExit("build needs the git repository")
    if clean_checkout(root):
        raise SystemExit("refusing to build: tracked files have uncommitted changes:\n" + clean_checkout(root))
    commit = git(root, "rev-parse", "HEAD").strip()
    exp = expected(root, commit)
    for rel, (kind, sha) in exp.items():         # frozen local inputs must match before anything is written
        if kind != "commit" and (not (root / rel).exists() or digest(root / rel) != sha):
            raise SystemExit(f"refusing to build: {rel} is missing or differs from its frozen hash")
    out = root / PACKAGE
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for rel, (kind, _) in sorted(exp.items()):
            if kind == "commit":
                info = zipfile.ZipInfo(rel, date_time=(1980, 1, 1, 0, 0, 0))
                info.external_attr = 0o644 << 16
                z.writestr(info, blob(root, commit, rel), compress_type=zipfile.ZIP_DEFLATED)
            else:
                z.write(root / rel, rel)
    rec = {"zenodo_record": "", "doi": "", "swh_id": "", "swh_checked_by_hand_on": "", "git_commit": commit,
           "files": [{"name": "package.zip", "local_path": PACKAGE, "sha256": digest(out),
                      "md5": digest(out, "md5"), "size": out.stat().st_size}],
           "built": time.strftime("%Y-%m-%dT%H:%M:%S"), "n_members": len(exp)}
    (root / RECEIPT).write_text(json.dumps(rec, indent=1))
    print(f"wrote {PACKAGE} ({len(exp)} members, {out.stat().st_size / 1e6:.0f} MB) from commit {commit}; "
          f"receipt draft written to {RECEIPT}")


def package_hashes(path: Path) -> dict:
    out = {}
    with zipfile.ZipFile(path) as z:
        for info in z.infolist():
            name = PurePosixPath(info.filename)
            if name.is_absolute() or ".." in name.parts or info.filename.endswith("/"):
                raise ValueError(f"unsafe member path in package: {info.filename}")
            if info.filename in out:
                raise ValueError(f"duplicate member in package: {info.filename}")
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
    rec = json.loads((root / RECEIPT).read_text())
    commit = str(rec.get("git_commit", ""))
    if not COMMIT_RE.match(commit):
        return ["the receipt must name the archived commit (40-character git_commit)"]
    try:
        git(root, "cat-file", "-e", f"{commit}^{{commit}}")
    except subprocess.CalledProcessError:
        return [f"commit {commit} does not exist in this repository"]
    problems = []
    if git(root, "rev-parse", "HEAD").strip() != commit:
        problems.append(f"checkout is not at the archived commit {commit}")
    if clean_checkout(root):
        problems.append("tracked files differ from the archived commit")
    files = rec.get("files", [])
    if len(files) != 1 or files[0].get("local_path") != PACKAGE:
        return problems + [f"the receipt must list exactly {PACKAGE}"]
    f = files[0]
    pkg = root / PACKAGE
    if not pkg.exists():
        return problems + [f"{PACKAGE} missing locally"]
    for algo in ("sha256", "md5"):
        if digest(pkg, algo) != f.get(algo):
            problems.append(f"package {algo} differs from the receipt")
    if pkg.stat().st_size != f.get("size"):
        problems.append("package size differs from the receipt")
    try:
        inside = package_hashes(pkg)
        exp = expected(root, commit)
    except (ValueError, zipfile.BadZipFile, subprocess.CalledProcessError, KeyError, json.JSONDecodeError) as e:
        return problems + [f"cannot read package or archived commit: {e}"]
    missing, extra = sorted(set(exp) - set(inside)), sorted(set(inside) - set(exp))
    problems += [f"package lacks {m}" for m in missing[:20]] + [f"unexpected package member {x}" for x in extra[:20]]
    problems += [f"package lacks required {r}" for r in REQUIRED if r not in exp]
    for rel, (kind, sha) in sorted(exp.items()):
        if rel not in inside:
            continue
        frozen = hashlib.sha256(blob(root, commit, rel)).hexdigest() if kind == "commit" else sha
        if inside[rel] != frozen:
            problems.append(f"{rel}: packaged bytes differ from the archived {kind}")
        local = root / rel
        if not local.exists() or digest(local) != frozen:
            problems.append(f"{rel}: local file missing or differs from the archived {kind}")
    try:
        z = fetch(rec.get("zenodo_record", ""))
        files_ = z.get("files", [])
        if isinstance(files_, dict):            # InvenioRDM layout: {"entries": {key: {...}}}
            files_ = list(files_.get("entries", {}).values())
        remote = {x["key"]: x for x in files_}
        if set(remote) != {"package.zip"} or len(files_) != 1:
            problems.append(f"Zenodo record lists {sorted(remote)}, expected exactly package.zip")
        x = remote.get("package.zip")
        if x and (str(x.get("checksum", "")).removeprefix("md5:") != f.get("md5") or x.get("size") != f.get("size")):
            problems.append("Zenodo checksum or size differs from the receipt")
        doi = z.get("doi") or (z.get("pids", {}).get("doi", {}) or {}).get("identifier")
        if not rec.get("doi") or doi != rec.get("doi"):
            problems.append(f"DOI differs or missing: record {doi}, receipt {rec.get('doi')}")
        if not (z.get("status") == "published" or z.get("submitted") is True or z.get("is_published") is True):
            problems.append("Zenodo record is not published")
    except Exception as e:                                     # noqa: BLE001 - any failure to verify is a failure
        problems.append(f"could not verify the Zenodo record: {e}")
    if str(rec.get("swh_id", "")).split(";")[0] != f"swh:1:rev:{commit}":
        problems.append(f"Software Heritage identifier must be the revision of the archived commit "
                        f"(swh:1:rev:{commit})")
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(rec.get("swh_checked_by_hand_on", ""))):
        problems.append("date of the manual Software Heritage check missing (YYYY-MM-DD)")
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["freeze-references", "build", "verify"])
    ap.add_argument("--create-flag", action="store_true")
    a = ap.parse_args()
    if a.step == "freeze-references":
        files = freeze_references()
        print(f"wrote {REFERENCE_LIST} ({len(files)} files); commit it before building")
        return
    if a.step == "build":
        build()
        return
    problems = verify()
    if problems:
        print("ARCHIVE NOT VERIFIED:\n  " + "\n  ".join(problems))
        sys.exit(1)
    rec = json.loads((ROOT / RECEIPT).read_text())
    print("archive verified:", rec["doi"], "commit", rec["git_commit"])
    if a.create_flag:
        (ROOT / FLAG).write_text(json.dumps(
            {"doi": rec["doi"], "git_commit": rec["git_commit"], "swh_id": rec["swh_id"],
             "swh_checked_by_hand_on": rec["swh_checked_by_hand_on"], "receipt_sha256": digest(ROOT / RECEIPT),
             "verified": time.strftime("%Y-%m-%dT%H:%M:%S")}, indent=1))
        print(f"{FLAG} created")


if __name__ == "__main__":
    main()
