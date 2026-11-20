"""One-off migration to inference-only model files (freeze review FZ-1, decision log D033).

The fitted ExponentiatedGradient object kept a training-only cache of 2014 training rows (Fairlearn's loaded
constraint object, `constraints_`). This script removes the training caches listed in pipeline.TRAINING_CACHES from
every frozen model that has them, without refitting:

1. audits every model in the manifest for row-level arrays (pipeline.row_level_arrays) and records the result;
2. for each model holding a listed cache: removes it, refuses if any row-level array remains, keeps the old file in
   data/derived/models_superseded/, writes the new file and updates its manifest entry (new SHA-256; fit
   specification, fit time and training metadata unchanged; old hash and removed attributes recorded); the old
   entry is added to results/models_manifest_superseded.json;
3. recomputes that model's predictions for every year in which it is evaluated (2014-2018) and requires each
   prediction file to be byte-identical to the one made with the original model; any difference stops the script
   with a non-zero exit (the old model file is kept, so the change can be reverted);
4. writes results/validation/inference_only_export.json.

Running it again when no model holds a cache re-audits and keeps the record if it still matches the manifest; if it
does not (models refitted since), it stops with recovery instructions and changes nothing; with no record (a rebuild
from scratch, where models are saved inference-only when fitted) it writes a record with no exports.
  uv run python scripts/export_inference_only.py
"""
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import pipeline as P  # noqa: E402

ORIGINAL = (2014, 2015, 2016, 2017, 2018)
RECORD = ROOT / "results" / "validation" / "inference_only_export.json"


def main():
    manifest = json.loads(P.MANIFEST.read_text())
    specs = P.expected_specs()
    not_current = sorted(n for n in specs if n not in manifest or not P.model_current(n, manifest[n], specs))
    if not_current or set(manifest) != set(specs):
        raise SystemExit(f"model inventory incomplete or not current (e.g. {not_current[:5]}); nothing changed")
    audit, todo = {}, []
    for name in sorted(manifest):
        fz = P.load_model(name, manifest)
        found = P.row_level_arrays(fz)
        caches = [a for a in P.TRAINING_CACHES.get(fz.kind, ()) if hasattr(fz.model, a)]
        audit[name] = {"row_level_arrays": found, "training_caches": caches}
        if caches:
            todo.append(name)
        elif found:
            raise SystemExit(f"{name}: row-level arrays outside the known training caches: {found[:5]}; nothing changed")
    print(f"audited {len(audit)} models; {len(todo)} hold training caches: {todo}", flush=True)
    if not todo:
        if RECORD.exists():          # the record must still describe the current model files (second freeze review F2-1)
            rec = json.loads(RECORD.read_text())
            stale = [n for n, e in rec.get("exports", {}).items()
                     if manifest.get(n, {}).get("sha256") != e.get("new_sha256")
                     or manifest.get(n, {}).get("inference_only", {}).get("exported_from_sha256") != e.get("old_sha256")]
            if stale:
                raise SystemExit(
                    f"the export record no longer matches the manifest for {stale} (models refitted since the migration?). "
                    f"Nothing was changed. Keep the old record as history (e.g. move it to "
                    f"results/validation/inference_only_export_<date>.json and log it in the decision log), then rerun "
                    f"this script to write a current audit record.")
            print("nothing to export; existing record matches the manifest and is kept")
        else:                       # e.g. a rebuild from scratch: models were saved inference-only when fitted
            RECORD.write_text(json.dumps({
                "exports": {}, "audit_before": {},
                "audit_after": {"models": len(audit), "with_row_level_arrays": 0, "row_level_min": P.ROW_LEVEL_MIN},
                "models_total_bytes": sum((P.MODELS / e["file"]).stat().st_size for e in manifest.values()),
                "provenance": P.provenance("export_inference_only.py")}, indent=1, default=str))
            print("nothing to export; all models already inference-only; record written")
        return
    exports = {}
    for name in todo:
        entry = dict(manifest[name])
        years = P.prediction_years(name, manifest, ORIGINAL)
        old_pred = {}
        for y in years:
            arr, meta = P._pred_paths(name, y)
            if not P._pred_valid(name, y, manifest):
                raise SystemExit(f"{name}/{y}: stored prediction is not valid for the original model; nothing changed")
            old_pred[y] = json.loads(meta.read_text())["pred_sha256"]
        old_path = P.MODELS / entry["file"]
        keep = ROOT / "data" / "derived" / "models_superseded" / f"{name}.{entry['sha256'][:12]}.joblib"
        keep.parent.mkdir(parents=True, exist_ok=True)
        if not keep.exists():
            shutil.copy2(old_path, keep)
        if P.sha256_file(keep) != entry["sha256"]:
            raise SystemExit(f"{name}: kept copy of the original model differs from its manifest hash")
        fz = P.load_model(name, manifest)
        removed = [a for a in P.TRAINING_CACHES[fz.kind] if hasattr(fz.model, a)]
        new_path = P.dump_model(fz)                          # removes the caches and refuses leftover row-level data
        reloaded = __import__("joblib").load(new_path)
        if P.row_level_arrays(reloaded):
            raise SystemExit(f"{name}: reloaded file still holds row-level arrays")
        new_sha = P.sha256_file(new_path)
        sup = P.MANIFEST.with_name("models_manifest_superseded.json")
        old = json.loads(sup.read_text()) if sup.exists() else {}
        old[f"{name}@{entry['sha256'][:12]}"] = dict(entry, superseded_by="inference-only export (D033)",
                                                    kept_as=keep.relative_to(ROOT).as_posix())
        sup.write_text(json.dumps(dict(sorted(old.items())), indent=1))
        manifest[name] = dict(entry, sha256=new_sha, inference_only={
            "exported_from_sha256": entry["sha256"], "removed_attributes": removed, "decision": "D033"})
        tmp = P.MANIFEST.with_suffix(".tmp.json")
        tmp.write_text(json.dumps(manifest, indent=1))
        tmp.replace(P.MANIFEST)
        P._CACHE.clear()
        new_pred = {}
        for y in years:
            t0 = time.time()
            P.predict_year([name], y)
            new_pred[y] = json.loads(P._pred_paths(name, y)[1].read_text())["pred_sha256"]
            same = new_pred[y] == old_pred[y]
            print(f"{name} {y}: predictions {'identical' if same else 'DIFFER'} ({time.time() - t0:.0f}s)", flush=True)
            if not same:
                raise SystemExit(f"{name}/{y}: predictions of the inference-only model differ from the original; "
                                 f"stop and report (original kept at {keep})")
        exports[name] = {"old_sha256": entry["sha256"], "new_sha256": new_sha, "removed_attributes": removed,
                         "old_bytes": keep.stat().st_size, "new_bytes": new_path.stat().st_size,
                         "kept_as": keep.relative_to(ROOT).as_posix(),
                         "predictions": {str(y): {"old_pred_sha256": old_pred[y], "new_pred_sha256": new_pred[y],
                                                  "identical": new_pred[y] == old_pred[y]} for y in years}}
    after = {n: P.row_level_arrays(P.load_model(n, manifest)) for n in sorted(manifest)}
    if any(after.values()):
        raise SystemExit(f"row-level arrays remain: { {k: v for k, v in after.items() if v} }")
    RECORD.write_text(json.dumps({
        "exports": exports, "audit_before": {k: v for k, v in audit.items() if v["row_level_arrays"]},
        "audit_after": {"models": len(after), "with_row_level_arrays": 0, "row_level_min": P.ROW_LEVEL_MIN},
        "models_total_bytes": sum((P.MODELS / e["file"]).stat().st_size for e in manifest.values()),
        "provenance": P.provenance("export_inference_only.py")}, indent=1, default=str))
    print(f"exported {list(exports)}; all predictions identical; record written to {RECORD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
