# Independent freeze review

**Date:** 20 November 2026  
**Reviewed commit:** `28a6156f760b98df795d529fd9f636d589901ebb`  
**Baseline:** `e61295201422ffa8ac953c2f43feb8e8909e8665`  
**Brief:** `docs/review_brief_freeze.md`

## Conclusion first

**Do not publish the current package. Archive after the blocking fixes below.**

The earlier statistical wording correction is resolved, and the current Stage A output gate passes independently. However, inspecting the actual serialized model contents revealed a material issue missed by the earlier archive reviews: **the ExpGrad file contains 1,270,284 rows of training features, labels and associated constraint data.** Excluding person-data filenames did not exclude person-level data embedded inside a model object.

A second blocker concerns the new archive guarantees: the verifier does not establish that the receipt's commit is the commit represented by the package, and it accepts unexpected ZIP members. Both problems were reproduced with isolated fixtures.

There is a promising fix without retraining: removing the ExpGrad training-only constraint cache in a temporary copy preserved predictions exactly on 4,096 checked inputs. This needs a controlled export/migration and fuller equivalence verification, not an automatic repeat of the long fit.

## Scope and safeguards

I reviewed the complete change set since `e612952`, the current archive code and tests, the previous disposition, the plan changes, the D032 redactions and the deposit inventory. I built a package only in a separate local clone under the review workspace. Only the 98 manifest-listed model files and the four named non-person reference directories were copied into that clone.

The local project was clean and at the commit above. The configured origin matches the repository supplied by the user. A remote-HEAD query failed because the command environment could not resolve GitHub, and the web API request was unavailable. Accordingly, this report is explicitly about the locally available commit, not an independently verified claim about the current remote branch tip.

No project files were modified. No actual deposit was published, no real remote deposit was verified, and no `prereg/ARCHIVED` flag was created. No ACS person records for 2019 or later, later-year empirical results, or external sources reporting such results were accessed. The cached model data inspected below belong to the allowed 2014 training year; only attribute names and shapes were printed, not individual records.

## Findings

### FZ-1 — major; blocking before archive: the ExpGrad model embeds person-level training data

**Locations:**

- `data/derived/models/expgrad_dp_race_s0.joblib`
- `src/pipeline.py::_fit_expgrad`, `_save`, `Frozen.predict`
- Installed Fairlearn `exponentiated_gradient.py::fit`, `_pmf_predict`, and `moment.py::load_data`
- Plan Section 10 and `LICENSE`, which state that Census person records are not included.

**Evidence:** loading the actual frozen artifact exposes these members:

| Attribute | Type / shape |
|---|---|
| `Frozen.model.constraints_.X` | ndarray, **1,270,284 × 10** |
| `Frozen.model.constraints_._y` | Series, **1,270,284** |
| `Frozen.model.constraints_.tags` | DataFrame, **1,270,284 × 3** |
| `Frozen.model.constraints_.utilities` | ndarray, **1,270,284 × 2** |
| `Frozen.model.constraints_.utility_diff` | ndarray, **1,270,284** |
| `Frozen.model.constraints_.U` | DataFrame, **1,270,284 × 18** |

Fairlearn's fitted `constraints_` retains the training matrix and aligned labels/group information. These are transformed person-level observations, not merely learned tree parameters or aggregate training diagnostics. The saved scaler also accompanies the model; standardizing features does not make this cache cease to be row-level training data.

The model file is **101,220,929 bytes** and is included in the built ZIP under its manifest-listed path. Its archive hash matches the manifest, so all current byte-integrity checks correctly accept this unintended payload. The model is trained on 2014, so this is not evidence of later-year exposure. It is nevertheless contrary to the project's explicit no-person-record deposit scope.

**Why blocking:** the package would permanently distribute a substantial training-data cache under a statement that no such records are included. Public availability of the original PUMS data does not resolve the mismatch with the chosen deposit contents. Earlier archive reviews checked paths, inventories and hashes rather than inspecting model-object payloads; that was a material blind spot.

**Suggested fix and validation:**

1. Export an inference-only version of the already fitted ExpGrad model. Remove training-only caches, preserving every learned predictor, mixture weight, sensitive-category specification and preprocessing parameter. Do not refit just to remove a cache.
2. Audit the serialized object graph across all model families, including callable closures and nested estimators. Add an export test for known training-cache attributes; a filename exclusion test is insufficient.
3. Compare the original and exported model's expected predictions across the allowed-year evaluation data, including serialization/reload. Preserve evidence of exact equality or investigate any discrepancy before proceeding.
4. Update the model artifact hash, manifest hash and plan references through a documented migration. Refresh or explicitly revalidate dependent prediction provenance and result provenance; do not leave the old model hash in records that claim to identify the new bytes. Run the final output gate on the resulting consistent state.
5. Rebuild the archive from the final corrected commit and scan that actual package again.

**Independent feasibility check:** in a temporary copy only, deleting `model.constraints_`, serializing and reloading produced exactly equal probability predictions on **4,096 inputs**: 2,048 cached allowed-year training vectors plus 2,048 synthetic vectors. Maximum absolute difference was **0.0**. The candidate file was **81,522,690 bytes**. The pinned `_pmf_predict` path uses the predictor callables, mixture weights and the original constraint type; it does not read `constraints_`.

A traversal of all 98 current model objects found the above large caches only in ExpGrad. The same scan found none in the temporary sanitized candidate. The scan is evidence, not a general proof of absence of every possible record representation; retain the targeted export check and broader inspection.

### FZ-2 — major; blocking before archive: verify does not bind the deposit to its declared commit or enforce exact membership

**Locations:** `scripts/verify_archive.py::_tracked`, `inventory`, `build`, `verify`, `package_hashes`; plan Section 10; `scripts/test_archive.py`.

**What improved:** build rejects an ordinarily dirty tracked working tree, excludes untracked files from the selected project directories, records HEAD, and checks that the SWHID string agrees with the receipt's commit string. All **13 existing tests passed** independently.

**Remaining evidence:** additional synthetic probes all returned `[]` from `verify()`, meaning acceptance:

| Probe | Incorrectly accepted behavior |
|---|---|
| Replace `git_commit` with an unrelated identifier and set `swh_id` to match it | Neither commit existence nor the package's relationship to that commit is checked. |
| Delete `git_commit` from a git-built receipt and supply a directory SWHID | The newly promised revision binding is silently bypassed. |
| Build, then delete a tracked source file and commit that deletion locally | The old package still passes: the missing local file disappears from the newly computed inventory, while the archive's extra copy is ignored. |
| Add an unintended ZIP member, update the receipt checksums and supply the matching mocked remote record | The extra member is ignored; checksum agreement does not establish intended membership. |
| Put an unrelated synthetic note in a reference-input directory before build | It is packaged by the unrestricted directory wildcard. Deleting it locally afterward still leaves verification passing. |

No real secret or person file was used in these probes. The unexpected member and reference note were clearly marked synthetic strings. No flag was actually created; the probes demonstrate that the verifier returns the success result on which flag creation relies.

**Why blocking:** Section 10 promises correspondence among the package, archived commit, local files and SWH revision. Current verification only compares two editable receipt strings and checks that a changing subset of local paths is present. It does not establish those stronger properties. A manual receipt edit, checkout/cleanup between build and verify, or accidental extra reference download can escape the intended checks. Manual SWH existence checking remains useful, but does not independently establish ZIP-to-commit equality.

**Suggested fix:**

- Require a valid commit identifier for the production CLI and resolve it to an actual commit. Keep non-git synthetic fixtures explicit rather than letting production silently fall back to the fixture mode.
- Derive the committed portion of the expected inventory from that commit's tree, and compare packaged bytes against its Git blobs. Also require the executing checkout to match the intended frozen state, or explicitly reject a changed checkout.
- Require exact member-set equality, with explicit documented exclusions; reject unexpected and duplicate ZIP names as well as missing members.
- Freeze an explicit list and hashes for allowed reference inputs. The raw-hash log already identifies 38 of the 40 current files; the two `_files.txt` listings need an explicit inclusion/hash policy. Do not treat every future file placed in those directories as approved deposit content.
- Check model bytes against the frozen manifest and reference bytes against their frozen identifiers, not just against whatever local copies currently exist.
- Add regression cases for the demonstrated acceptance paths, while preserving the existing passing-package case.

The current build also omits `.gitignore`, `data/raw/.gitkeep` and `data/derived/.gitkeep`, despite the unqualified statement that it holds “exactly the files” of the commit. These omissions are not themselves a scientific blocker, but include them or qualify the wording consistently with the explicit inventory policy.

### FZ-3 — minor; non-blocking: make third-party and model licensing scopes explicit

**Locations:** `LICENSE`, `README.md`, `paper/fancyhdr.sty`, `paper/tmlr.bst`, `paper/tmlr.sty`, `paper/math_commands.tex`.

The license file correctly says third-party material retains its own terms. However, its broad MIT grant for “any other source code files” and CC BY listing for `paper/` can obscure that carve-out. Two vendored files explicitly carry different terms: `fancyhdr.sty` identifies LPPL 1.3-or-later, and `tmlr.bst` identifies LPPL 1-or-later. TMLR style/template provenance should also be listed. These files are not US-government reference works.

The frozen models are described as derived from public ACS data, but that description does not explicitly assign a reuse license to the model artifacts themselves, which live outside the listed code/text directory scopes.

**Suggested improvement:** limit MIT/CC BY grants explicitly to original project material; list the vendored template files and retain their upstream notices/terms; state the intended model-artifact license. Include enough upstream provenance to identify the distributed versions. The LPPL distinguishes complete works, generated works and modified distributions, so use the actual upstream distribution terms rather than inferring permission from the project's MIT notice. [Official LPPL 1.3c](https://www.latex-project.org/lppl/lppl-1-3c/).

This finding identifies scope ambiguity, not a conclusion that the current inclusion is unlawful: the relevant file notices are retained and the root license already contains a third-party carve-out. It does not require a model or analysis change.

### FZ-4 — minor; non-blocking: status wording should distinguish a publication choice from a technical restriction

**Location:** first paragraph of `prereg/PREREGISTRATION.md`; README status.

The plan says the DOI and SWH identifier “cannot appear in the deposited file.” That is too broad for a DOI: Zenodo explicitly permits reserving one and inserting it into files before upload. Keeping identifiers outside this package is a reasonable workflow choice, not a DOI restriction. [Zenodo's DOI reservation instructions](https://help.zenodo.org/docs/deposit/describe-records/reserve-doi/).

Use wording such as “Identifiers are recorded outside the package in the verified receipt.” Before publication, “version prepared for deposit” is more accurate than the present-tense implication that the record is already archived. The final deposited plan may naturally describe its status as frozen. No new DOI reservation workflow is necessary to resolve this wording.

### FZ-5 — minor; non-blocking: targeted redactions are complete in current text, but this is not an anonymous deposit

**Locations:** D032; `docs/BRIEF_2026-11-18.md`; earlier decision-log entries; packaged review reports; `LICENSE`.

The D032 changes remove the named affiliation and the specific reference to the other paper from the targeted current documents. Searches of tracked text found no remaining occurrences of the removed institution or the distinctive prior-paper terms. Diff inspection shows edits to personal context, not design rules, estimands, thresholds, numerical results or execution code.

The package still contains the public GitHub account, a historical account reference in the log and local usernames in earlier review-report paths. D032 also correctly acknowledges that earlier versions remain in public Git history, which Software Heritage can preserve. These facts mean the redactions reduce personal detail in the current snapshot; they do not anonymize the public project or remove historical disclosure.

**Suggested action:** preserve that narrow, accurate description. If the deposited package is later offered as an anonymous-review supplement, prepare an appropriately separate anonymous artifact. No public-history rewrite or broader redaction is required by the stated D032 purpose, and none was performed in this review.

## Previous findings and dispositions

| Earlier item | Freeze-review conclusion |
|---|---|
| PA-1: combined-error interpretation | **Resolved.** Section 7.6 now distinguishes 0.0055 false holds, 0.0050 false violated, and 0.0094 combined error with the appropriate MC qualification. The boundary mean is descriptive; criteria and result files are unchanged. D031 explicitly withdraws the old D030 interpretation. |
| PA-2: missing non-person reference inputs | **Resolved for the current inventory.** All four named reference directories are now included, totaling 40 files. FZ-2 addresses how that list is frozen and verified, not a request for more reference documents. |
| PA-3: P1 runtime | **Appropriately recorded.** The commitment to run both variants with fixed settings remains; no scientific choice was changed. |
| PA-4: exposure history/model size | **Resolved relative to the then-current artifacts.** The exposure account is more precise and the original total 126,749,100 bytes is accurate. FZ-1's export will change the total and manifest hash, so update those values again after the controlled migration. |
| D032: ignored files/dirty-tree handling | **Improved, but incomplete.** The current dry-run correctly excludes ignored drafts and test leftovers. Exact commit/membership guarantees still need FZ-2. |
| D032: privacy redactions | **Supported for their stated current-text purpose**, with the public-history and anonymity limitations in FZ-5. |

## Actual package and checks performed

The isolated build at the reviewed commit produced **251 members**, **130,898,302 bytes**. Its components were:

- 113 selected tracked files.
- 98 manifest-listed model files.
- 40 non-person reference inputs: 28 dictionary files/listings, 10 variable-change files/listings, one occupation crosswalk and one CPI workbook.

The difference from D032's earlier count of 250 is not evidence of missing content: the final reviewed tree includes the freeze brief. Every included tracked file matched its HEAD blob. All 98 model members matched their manifest hashes. All 38 reference files represented in the raw-hash log matched their recorded hashes; the two unlogged files were directory listings.

No standalone parquet, prediction-array, raw Census person ZIP, third-party research-paper directory, private-key file or Git-internals directory appeared in the inventory. Common private-key/API-token patterns found no matches in the scanned text members. This was a bounded content scan, not a guarantee that every conceivable secret representation is absent.

**The model-object inspection overrides a filename-only “no person records” conclusion:** FZ-1 proves that the current ZIP nevertheless contains person-level data inside ExpGrad. The current package must not be treated as cleared for publication.

Additional independent checks:

- Existing archive suite: **13/13 passed** in a separate test tree.
- Adversarial archive/receipt probes: reproduced the incorrect acceptance paths in FZ-2.
- Serialized model inspection: all 98 model files traversed for large array caches; only ExpGrad exposed the identified training-row caches.
- Temporary inference-only candidate: exact prediction equality on 4,096 inputs after serialization/reload; no detected large cache arrays in the candidate.
- Current Stage A gate, run in the isolated allowed-year copy: **passed**. This verifies scientific artifact freshness; it does not inspect serialized model payloads for deposit exclusions.
- All changes since `e612952`: inspected; no fitting, prediction or statistical-analysis implementation changes in the reviewed diff.

The new report and temporary artifacts remain outside the project. A final Git status check of the original project was clean.

## Required sequence before publication

1. Resolve **FZ-1** with an audited inference-only export, allowed-year prediction-equivalence evidence, updated identities and consistent provenance. Avoid an unnecessary refit.
2. Resolve **FZ-2** with commit-derived verification, exact archive membership and a frozen reference-input list; add the failing regression fixtures.
3. Commit the resulting final state, rerun the relevant gates, build a new package in the intended release workflow, and inspect that package rather than relying on this superseded dry run.
4. Only after those checks publish and verify the actual deposit, record the manual SWH revision check, and create the archive flag. Keep later-year person data unopened until then.

## Archive recommendation

**ARCHIVE AFTER THE LISTED FIXES. Do not publish the current package:** FZ-1 and FZ-2 are blocking before archive. FZ-3 through FZ-5 are non-blocking. No new scientific model fit is presently indicated, but the inference-only export and its updated provenance must be validated before freezing.
