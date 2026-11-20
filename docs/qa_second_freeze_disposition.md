# Disposition of the second freeze review (20 Nov 2026)

Report: `docs/qa_second_freeze_review_2026-11-20.md` (reviewed commit e816bfd). Recommendation of the reviewer:
archive; no blocking finding; F2-1 non-blocking. Decision log: D035.

| Finding | Severity | Disposition |
|---|---|---|
| F2-1 a future rebuild can keep a stale export record | minor | **Fixed (fail-safe).** On the no-cache path, `export_inference_only.py` now checks that every exported model in an existing record still has the recorded new and original hashes in the manifest; if not (models refitted since), it stops with recovery instructions and changes nothing (the record is history and is never overwritten automatically). Tested on the smoke models: matching record kept; simulated refit stops with the record unchanged; restored state passes. The output gate already rejects a mismatched record. No result depends on this script's code. |

Further pre-deposit corrections from the author's own review of the plan (D035): the status line now lists D021–D035
(D034 had updated Section 4 values) and two freeze reviews; the exposure record includes the second freeze review's
recomputation of ExpGrad predictions on 2014–2018; Section 3 states precisely that the 2025 1-year PUMS files (not the
1-year summary tables) were unreleased when archiving.
