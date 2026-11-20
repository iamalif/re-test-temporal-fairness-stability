"""Offline tests of the archive verifier (QA 3 A3-1, QA 4 A4-1, freeze review FZ-2) on synthetic git repositories
with a mocked Zenodo record. A correct package must pass; every listed tampering, omission, extra member, wrong
commit or wrong identifier must fail, and build must refuse a dirty tree or a reference/model file that differs from
its frozen hash. Writes results/validation/archive_tests.json; exits non-zero on any failure."""
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import verify_archive as V  # noqa: E402

results = {}


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t", *args],
                          capture_output=True, text=True, check=True).stdout.strip()


def make_repo(root: Path):
    for rel in V.REQUIRED + ["src/a.py", "scripts/b.py", "scripts/run_all.sh", "README.md"]:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if rel not in (V.MANIFEST, V.REFERENCE_LIST):
            p.write_text(f"content of {rel}\n")
    (root / ".gitignore").write_text("data/\narchive/\nprereg/ARCHIVE_RECEIPT.json\nprereg/ARCHIVED\n")
    model = root / "data" / "derived" / "models" / "m.joblib"
    model.parent.mkdir(parents=True, exist_ok=True)
    model.write_bytes(b"model bytes")
    (root / V.MANIFEST).write_text(json.dumps({"m": {"file": "m.joblib", "sha256": hashlib.sha256(b"model bytes").hexdigest()}}))
    ref = root / "data" / "raw" / "cpi" / "cpi.xlsx"
    ref.parent.mkdir(parents=True, exist_ok=True)
    ref.write_bytes(b"cpi bytes")
    V.freeze_references(root)
    git(root, "init", "-q")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "t")


def receipt(root):
    return json.loads((root / V.RECEIPT).read_text())


def save_receipt(root, rec):
    (root / V.RECEIPT).write_text(json.dumps(rec))


def finish(root, swh=None):
    rec = receipt(root)
    rec.update({"zenodo_record": "1", "doi": "10.5281/zenodo.1", "swh_checked_by_hand_on": "2026-11-21",
                "swh_id": swh if swh is not None else f"swh:1:rev:{rec['git_commit']};origin=x"})
    save_receipt(root, rec)
    return rec


def record_for(rec, md5=None, extra_file=False):
    f = rec["files"][0]
    files = [{"key": "package.zip", "checksum": "md5:" + (md5 or f["md5"]), "size": f["size"]}]
    if extra_file:
        files.append({"key": "other.txt", "checksum": "md5:0", "size": 1})
    return lambda _id: {"doi": rec["doi"], "status": "published", "files": files}


def resync(root):
    """Make the receipt and the mocked record match the (tampered) package bytes."""
    pkg = root / V.PACKAGE
    rec = receipt(root)
    rec["files"][0].update({"sha256": V.digest(pkg), "md5": V.digest(pkg, "md5"), "size": pkg.stat().st_size})
    save_receipt(root, rec)
    return record_for(rec)


def rewrite(root, member, replace=None, add=None, dup=False):
    pkg = root / V.PACKAGE
    tmp = pkg.with_suffix(".tmp")
    with zipfile.ZipFile(pkg) as zin, zipfile.ZipFile(tmp, "w") as zout:
        for info in zin.infolist():
            if info.filename == member:
                if replace is not None:
                    zout.writestr(member, replace)
                continue
            zout.writestr(info, zin.read(info))
        if add:
            zout.writestr(add[0], add[1])
        if dup:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                zout.writestr("src/a.py", b"content of src/a.py\n")
    tmp.replace(pkg)


def case(name, expect_pass, setup=lambda root: None, before_build=lambda root: None):
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        make_repo(root)
        try:
            before_build(root)
            V.build(root)
            finish(root)
            fetch = setup(root) or record_for(receipt(root))
            problems = V.verify(root, fetch)
        except SystemExit as e:
            problems = [f"build refused: {str(e).splitlines()[0]}"]
        ok = (not problems) == expect_pass
        results[name] = {"passed": ok, "problems": problems[:5]}


case("complete package passes", True)
case("package without the pre-registration fails", False,
     lambda r: (rewrite(r, "prereg/PREREGISTRATION.md"), resync(r))[1])
case("model file differing from its manifest hash fails", False,
     lambda r: (rewrite(r, "data/derived/models/m.joblib", replace=b"other"), resync(r))[1])
case("wrong Zenodo checksum fails", False, lambda r: record_for(receipt(r), md5="0" * 32))
case("Zenodo record with an extra file fails", False, lambda r: record_for(receipt(r), extra_file=True))


def no_swh_date(r):
    rec = receipt(r)
    rec["swh_checked_by_hand_on"] = ""
    save_receipt(r, rec)


case("missing Software Heritage check date fails", False, no_swh_date)
case("local committed file changed after build fails", False,
     lambda r: (r / "results" / "stage_a" / "margins.json").write_text("changed\n"))
case("local shell script changed after build fails", False,
     lambda r: (r / "scripts" / "run_all.sh").write_text("changed\n"))
case("package without a shell script fails", False, lambda r: (rewrite(r, "scripts/run_all.sh"), resync(r))[1])
case("untracked file is left out and the package passes", True,
     before_build=lambda r: (r / "paper").mkdir(exist_ok=True) or (r / "paper" / "draft.pdf").write_bytes(b"d"))


def dirty(r):
    (r / "src" / "a.py").write_text("uncommitted\n")


case("build with an uncommitted tracked change is refused", False, before_build=dirty)
case("identifier of another commit fails", False, lambda r: finish(r, "swh:1:rev:" + "0" * 40) and None)
case("directory identifier instead of revision fails", False, lambda r: finish(r, "swh:1:dir:" + "0" * 40) and None)


def unrelated_commit(r):
    rec = receipt(r)
    rec["git_commit"] = "1" * 40
    rec["swh_id"] = "swh:1:rev:" + "1" * 40
    save_receipt(r, rec)


case("receipt naming a non-existent commit with a matching identifier fails", False, unrelated_commit)


def no_commit(r):
    rec = receipt(r)
    rec.pop("git_commit")
    rec["swh_id"] = "swh:1:dir:" + "0" * 40
    save_receipt(r, rec)


case("receipt without the commit fails", False, no_commit)


def delete_and_commit(r):
    git(r, "rm", "-q", "scripts/b.py")
    git(r, "commit", "-q", "-m", "delete")


case("tracked file deleted and committed after build fails", False, delete_and_commit)
case("unexpected extra package member fails (receipt and record matching)", False,
     lambda r: (rewrite(r, None, add=("notes/extra.txt", b"synthetic extra")), resync(r))[1])
case("duplicate package member fails", False, lambda r: (rewrite(r, None, dup=True), resync(r))[1])
case("unlisted file in a reference folder is left out and the package passes", True,
     before_build=lambda r: (r / "data" / "raw" / "cpi" / "note.txt").write_text("synthetic note"))
case("reference input changed locally after build fails", False,
     lambda r: (r / "data" / "raw" / "cpi" / "cpi.xlsx").write_bytes(b"changed"))
case("model file changed locally after build fails", False,
     lambda r: (r / "data" / "derived" / "models" / "m.joblib").write_bytes(b"changed"))
case("build with a reference input differing from its frozen hash is refused", False,
     before_build=lambda r: (r / "data" / "raw" / "cpi" / "cpi.xlsx").write_bytes(b"changed"))
case("build with a model differing from its manifest hash is refused", False,
     before_build=lambda r: (r / "data" / "derived" / "models" / "m.joblib").write_bytes(b"changed"))


def unpublished(r):
    rec = receipt(r)
    f = rec["files"][0]
    return lambda _id: {"doi": rec["doi"], "status": "draft",
                        "files": [{"key": "package.zip", "checksum": "md5:" + f["md5"], "size": f["size"]}]}


case("unpublished Zenodo record fails", False, unpublished)

passed = all(v["passed"] for v in results.values())
for k, v in results.items():
    print(f"{k:72s} {'ok' if v['passed'] else 'FAILED'}  {v['problems'][:1]}")
out = ROOT / "results" / "validation"
out.mkdir(parents=True, exist_ok=True)
(out / "archive_tests.json").write_text(json.dumps({"tests": {k: {"passed": v["passed"]} for k, v in results.items()},
                                                    "all_passed": passed,
                                                    "script_sha256": V.digest(Path(__file__))}, indent=1))
sys.exit(0 if passed else 1)
