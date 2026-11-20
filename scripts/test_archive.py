"""Offline tests of the archive verifier (QA 3, A3-1) on a synthetic project tree with a mocked Zenodo record.
A complete package must pass; a package that omits a required member must fail even when the receipt matches the
package bytes; a model file that differs from its manifest hash, a wrong Zenodo checksum and a missing Software
Heritage check must fail. Writes results/validation/archive_tests.json; exits non-zero on any failure."""
import hashlib
import json
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import verify_archive as V  # noqa: E402

results = {}


def make_tree(root: Path):
    for rel in V.REQUIRED + ["src/a.py", "scripts/b.py", "scripts/run_all.sh", "README.md"]:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if rel != "results/models_manifest.json":
            p.write_text(f"content of {rel}\n")
    model = root / "data" / "derived" / "models" / "m.joblib"
    model.parent.mkdir(parents=True, exist_ok=True)
    model.write_bytes(b"model bytes")
    (root / "results" / "models_manifest.json").write_text(json.dumps(
        {"m": {"file": "m.joblib", "sha256": hashlib.sha256(b"model bytes").hexdigest()}}))


def finish_receipt(root: Path):
    rec = json.loads((root / "prereg" / "ARCHIVE_RECEIPT.json").read_text())
    rec.update({"zenodo_record": "1", "doi": "10.5281/zenodo.1", "swh_id": "swh:1:dir:abc",
                "swh_checked_by_hand_on": "2026-11-21"})
    (root / "prereg" / "ARCHIVE_RECEIPT.json").write_text(json.dumps(rec))
    return rec


def record_for(rec, md5=None):
    f = rec["files"][0]
    return lambda _id: {"doi": rec["doi"], "status": "published",
                        "files": [{"key": "package.zip", "checksum": "md5:" + (md5 or f["md5"]), "size": f["size"]}]}


def rewrite_receipt_to_package(root: Path):
    pkg = root / V.PACKAGE
    rec = json.loads((root / "prereg" / "ARCHIVE_RECEIPT.json").read_text())
    rec["files"][0].update({"sha256": V.digest(pkg, "sha256"), "md5": V.digest(pkg, "md5"), "size": pkg.stat().st_size})
    (root / "prereg" / "ARCHIVE_RECEIPT.json").write_text(json.dumps(rec))
    return rec


def drop_member(root: Path, member: str, replace: bytes | None = None):
    pkg = root / V.PACKAGE
    tmp = pkg.with_suffix(".tmp")
    with zipfile.ZipFile(pkg) as zin, zipfile.ZipFile(tmp, "w") as zout:
        for info in zin.infolist():
            if info.filename == member:
                if replace is not None:
                    zout.writestr(member, replace)
                continue
            zout.writestr(info, zin.read(info))
    tmp.replace(pkg)


def case(name, expect_pass, setup):
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        make_tree(root)
        V.build(root)
        rec = finish_receipt(root)
        fetch = setup(root, rec) or record_for(rec)
        problems = V.verify(root, fetch)
        ok = (not problems) == expect_pass
        results[name] = {"passed": ok, "problems": problems[:5]}


case("complete package passes", True, lambda root, rec: None)


def omit_prereg(root, rec):
    drop_member(root, "prereg/PREREGISTRATION.md")
    r = rewrite_receipt_to_package(root)              # the receipt matches the (incomplete) package bytes
    return record_for(r)


case("package without the pre-registration fails", False, omit_prereg)


def bad_model(root, rec):
    drop_member(root, "data/derived/models/m.joblib", replace=b"other bytes")
    return record_for(rewrite_receipt_to_package(root))


case("model file differing from its manifest hash fails", False, bad_model)
case("wrong Zenodo checksum fails", False, lambda root, rec: record_for(rec, md5="0" * 32))


def no_swh(root, rec):
    r = json.loads((root / "prereg" / "ARCHIVE_RECEIPT.json").read_text())
    r["swh_checked_by_hand_on"] = ""
    (root / "prereg" / "ARCHIVE_RECEIPT.json").write_text(json.dumps(r))
    return record_for(r)


case("missing Software Heritage check fails", False, no_swh)


def local_changed(root, rec):
    (root / "results" / "stage_a" / "margins.json").write_text("changed after archiving\n")
    return record_for(rec)


case("local reference file changed after archiving fails", False, local_changed)

def python_changed(root, rec):
    (root / "src" / "a.py").write_text("changed code\n")
    return record_for(rec)


case("local Python source changed after archiving fails", False, python_changed)


def shell_changed(root, rec):
    (root / "scripts" / "run_all.sh").write_text("changed shell code\n")
    return record_for(rec)


case("local shell script changed after archiving fails", False, shell_changed)


def omit_shell(root, rec):
    drop_member(root, "scripts/run_all.sh")
    return record_for(rewrite_receipt_to_package(root))     # receipt and remote record match the incomplete package


case("package without a shell script fails", False, omit_shell)

passed = all(v["passed"] for v in results.values())
for k, v in results.items():
    print(f"{k:55s} {'ok' if v['passed'] else 'FAILED'}  {v['problems'][:1]}")
out = ROOT / "results" / "validation"
out.mkdir(parents=True, exist_ok=True)
(out / "archive_tests.json").write_text(json.dumps({"tests": results, "all_passed": passed,
                                                    "script_sha256": V.digest(Path(__file__), "sha256")}, indent=1))
sys.exit(0 if passed else 1)
