# Second independent freeze review

**Date:** 20 November 2026  
**Reviewed commit:** `e816bfdcdd9bf2b1a79798a8aef83c98f7b3f0a4`  
**Baseline:** `28a6156f760b98df795d529fd9f636d589901ebb`  
**Brief:** `docs/review_brief_freeze_2.md`

## Decision

**No blocking finding remains for the reviewed commit. Recommendation: archive.**

The two previous blockers are resolved in the actual artifacts, not just in the dispositions:

- The ExpGrad training cache has been removed. An independent scan of all 98 current model files found no comparable retained row-level arrays. The original cache-bearing model is outside the package.
- Archive verification now binds the package to a real, specific Git commit, compares committed bytes against Git blobs, freezes reference-input hashes, and checks exact ZIP membership. The earlier acceptance paths are covered by the rewritten checks and tests.

I independently recomputed predictions from both the original and exported ExpGrad files on **all 8,116,931 allowed-year rows**. Their stored-precision predictions were exactly equal to each other and to the current saved predictions. Scientific content in the ten compared Stage A/validation artifacts is unchanged. The current Stage A gate passed independently.

There is one **non-blocking** maintenance issue affecting a future fresh rebuild, described below. It does not affect the current artifacts or require postponing this deposit, changing the scientific specification, or refitting models.

This recommendation concerns the exact reviewed commit and frozen inputs. It is not permission to substitute later unreviewed changes or skip verification of the actual published deposit.

## Scope and safeguards

I inspected all changes since `28a6156`, including D033/D034, the migration script and records, output-gate changes, archive rewrite/tests, plan, reference manifest and licensing changes. I built a package only in an isolated clone under the review workspace. That clone received only the 98 current manifest-listed models and 40 explicitly listed non-person reference files.

No project files were edited. No package was built inside the project, no actual publication occurred, and no `prereg/ARCHIVED` flag was created. Remote verification was exercised with a mock record only. No ACS person records for 2019 or later, or later-year empirical results, were accessed. Allowed 2014–2018 data were read for the independent prediction comparison and output gate.

The original working tree remained clean and at the reviewed commit at the final check.

## Dispositions of the previous findings

| Previous finding | Verdict | Evidence |
|---|---|---|
| **FZ-1: person-level cache inside ExpGrad** | **Resolved for the deposited artifacts.** | Actual exported file lacks `constraints_`; an independent model traversal found no large row-level cache in any of the 98 current models. Full allowed-year prediction comparison passed. The old cached model is not a package member. |
| **FZ-2: incomplete commit and exact-membership guarantees** | **Resolved for the reviewed release.** | Expected content is derived from the receipt commit's tree, frozen reference list and model manifest. Commit existence, checkout identity, tracked cleanliness, Git-blob equality, local equality, exact member sets and duplicate-member rejection are implemented. All 24 archive tests passed independently; the actual isolated package also passed verification with a matching mock remote record. |
| **FZ-3: licensing scope** | **Resolved as a scope/documentation issue.** | Original project material is distinguished from third-party template files; frozen model artifacts have an explicit CC BY 4.0 grant. The four template files and their upstream revision are identified, an Apache 2.0 license copy is included, and the embedded LPPL notices are retained. I did not independently re-establish the claimed byte identity against the upstream template repository. |
| **FZ-4: status/DOI wording** | **Resolved.** | The plan now describes a version prepared for deposit and identifiers recorded outside the package, rather than asserting that a DOI technically cannot appear inside it. |
| **FZ-5: targeted redactions versus anonymity** | **Appropriately recorded.** | No broader anonymity claim or history rewrite was introduced. The public archive remains distinct from any future anonymous-review supplement. |

## Independent migration verification

### Model identity and retained fitted state

The only changed model-manifest entry is `expgrad_dp_race_s0`. The other 97 entries are unchanged from `28a6156`.

| Item | Verified value |
|---|---|
| Original ExpGrad SHA-256 | `3e1c0f7efc00eae97fd12cc5e7992da99cdbc612b2e953b9f2676380d45f8008` |
| Exported ExpGrad SHA-256 | `15988935949067c9e2ad0bf424317d6fa74bbbcfd5bd81a7fbc26e0e4e3a8076` |
| Original / exported file size | 101,220,929 / 81,523,108 bytes |
| Removed fitted-object attribute | `constraints_` |
| Total size of current 98 models | **107,051,279 bytes** |
| Current manifest SHA-256 | `5232aad3a7386c77d1e9aef080cfa4a77d4dcd52f85ecdcf0c42c543d6369ca7` |

I used the original artifact retained in the previous review's isolated copy, checked its hash against the migration record, and compared it with the new artifact. Every retained top-level fitted-model attribute and every retained `Frozen` preprocessing/metadata attribute had an identical `joblib.hash`. The sole removed fitted-model attribute was the known training cache. This independently supports the claim that the operation was an export change, not a refit or alteration of learned predictors.

The new save path strips known training-only state before serialization and rejects detected large arrays. Both the project's check and an independent traversal were applied to the actual current models. The independent traversal also follows function closure contents and object-valued estimator containers. No large cached training arrays were found.

These scans are bounded inspections of the known model types, not a general proof that any arbitrary pickle is free of data. For the specific artifacts reviewed, the previously identified cache is absent and no replacement cache was found.

### Full allowed-year prediction comparison

I independently loaded the original and exported model files and called their prediction methods on the full eligible population for each allowed year. I compared their float32 predictions—the precision actually stored by this pipeline—with the current `.npy` predictions, checked each file hash against the export record, and checked that prediction metadata names the new model hash.

| Year | Rows checked | Original = exported | Exported = stored | Hash and new-model metadata checks |
|---|---:|---|---|---|
| 2014 | 1,587,856 | Exact | Exact | Pass |
| 2015 | 1,603,542 | Exact | Exact | Pass |
| 2016 | 1,618,060 | Exact | Exact | Pass |
| 2017 | 1,642,973 | Exact | Exact | Pass |
| 2018 | 1,664,500 | Exact | Exact | Pass |
| **Total** | **8,116,931** | **Exact** | **Exact** | **All pass** |

This verifies the submitted migration evidence independently rather than relying only on the log's “identical” messages. It does not require testing on unopened later-year records: retained fitted state is unchanged, and the removed cache is outside the inference path.

### Results, provenance and historical references

I independently compared the current versions of these files with `28a6156`:

- Stage A margins, stored estimates, recoding check and decomposition check.
- Geographic-pair CSV and US-metric CSV.
- Split-variance validation, inference validation, integrity tests and inventory check.

All ten comparisons passed: CSV bytes were identical; JSON scientific content was identical after removing provenance/timing/code-identity fields expected to change during the migration. This agrees with the committed `migration_equivalence.json`. Its recorded baseline `ebf359f` is the pre-migration code commit; the additional comparison against `28a6156` confirms continuity with the previously reviewed scientific results.

The migration log records all five prediction-identity checks, downstream reruns, successful equivalence checks, the final successful output gate and `=== MIGRATION DONE ===`.

The plan's manifest hash and total model size match the current files. All five current ExpGrad prediction metadata files name the new model hash. The old ExpGrad hash is absent from current Stage A results and inventory records; its appearance in the export record and superseded manifest is clearly historical. The original artifact's `kept_as` path is outside the archive inventory. Historical reviews and logs retain old hashes as audit history, not current artifact declarations.

The independent Stage A command, run in a separate code/result copy with explicitly selected allowed-year artifact links, returned:

`stage_a: all promised outputs present, current and passing their acceptance criteria`

The current model scanner is part of this gate. Passing the gate now therefore includes a check addressing the earlier cached-data issue, in addition to model/prediction identity and analysis freshness.

## Archive verification and actual package inspection

The isolated build from the reviewed commit produced **264 members**, totaling **114,301,711 bytes** in that build:

| Content class | Members |
|---|---:|
| Files from the exact Git commit | 126 |
| Frozen non-person reference inputs | 40 |
| Current inference-only model files | 98 |

The ZIP's member set equaled the expected set exactly. Every committed member matched its Git blob. Every model and reference member matched its frozen hash. The previous omissions of `.gitignore` and the tracked `.gitkeep` files are resolved by taking the committed portion directly from the commit tree.

Inspection found no standalone person-data ZIP, parquet file, prediction array, superseded-model file, third-party research-paper directory, private-key file or Git-internals directory in the package. Common credential/private-key patterns produced no matches in the scanned text members. The model-object audit supplies the additional check that filename inspection alone could not provide in the previous review.

The current verifier was exercised on this real isolated package with a synthetic, matching InvenioRDM-style remote record. It returned no problems. This checks the archive/local/commit logic and the mocked response layout; it does not claim that a real Zenodo record or Software Heritage visit has already been verified.

### Regression tests and implementation review

All **24 current archive tests passed** in a separate test tree. The rewritten implementation addresses the previous failure mechanisms:

- Missing/malformed/nonexistent receipt commits are rejected.
- A checkout at another commit or with tracked changes is rejected.
- Committed content is verified against Git blobs, not merely the current filesystem.
- ZIP membership must equal the frozen expected set; extra and duplicate members fail.
- Deleting or changing a local committed file cannot make it disappear from the expected inventory.
- References come from a committed list of hashes; an unrelated file subsequently placed in a reference directory is not packaged.
- Model and reference mismatches fail before build or during verification.
- Remote file count, name, checksum, size, DOI and publication evidence are checked.
- The recorded SWH revision must match the archived commit, with the manual-check date present.

I found no remaining blocker in these changes for the current snapshot. This is not a promise that all conceivable repository manipulation or malicious pickle is handled; the release recommendation is based on the inspected commit, inputs, package and tested failure cases.

## Finding F2-1 — minor; non-blocking: a future fresh rebuild can retain a stale export record

**Location:** `scripts/export_inference_only.py::main`, the `if not todo` branch; `scripts/check_outputs.py::check_models_inference_only`.

**Evidence:** when no model has a training cache and `inference_only_export.json` already exists, the export script leaves that record unchanged without checking whether its exported-model hashes still match the manifest. After a future genuine refit, models are saved inference-only immediately, so there may be nothing to migrate even though the old committed export record refers to different model bytes. The final output gate then correctly rejects that stale record.

An isolated fixture reproduced the behavior: a current inference-only model with a new manifest hash, alongside an existing export record with an old hash, produced “nothing to export; existing record kept”; the saved record remained mismatched.

**Why non-blocking:** the current reviewed export record matches the current manifest, and the complete migration and gate passed. Stage B uses these frozen models and does not refit them. This issue concerns maintenance of a future from-scratch reproduction, not current predictions, inference or deposit contents. The existing gate fails safely rather than accepting mismatched provenance.

**Suggested later fix:** on the no-cache path, validate any existing export record against the current manifest. If a genuine new fit has occurred, preserve the historical migration evidence separately and write an appropriate current audit record, or stop early with explicit recovery instructions. Do not erase a valid current migration record merely to make an audit pass.

**Do not postpone the present deposit or refit models to address this maintenance improvement.**

## Remaining release actions

No additional scientific or archive-code fix is required by this review. Build the production package from exactly the reviewed commit and frozen inputs, publish it, verify the actual record/checksum/DOI with the existing verifier, perform and record the manual Software Heritage revision check, and only then create `prereg/ARCHIVED` and open later-year person data.

The actual package's checksum must be recorded from that build: ZIP metadata for external inputs can differ between builds or machines even when all member contents match. The byte count above identifies my isolated build, not a checksum substitute for the eventual deposit.

No real publication, real receipt verification or archive-flag creation was performed in this review. Those remain the authorized release workflow's next steps.

## Archive recommendation

**ARCHIVE — for commit `e816bfdcdd9bf2b1a79798a8aef83c98f7b3f0a4` and the reviewed frozen inputs. No blocking findings remain.** Complete the normal verification of the actual deposit before creating the flag or accessing later-year data. F2-1 is non-blocking and does not require moving the deposit to another commit.
