# Final freeze diff review

**Date:** 20 November 2026

**Reviewed commit:** `ff45b43304ad4e14e5c4a9de8ad75b3e847ef5b4`

**Baseline:** `e816bfdcdd9bf2b1a79798a8aef83c98f7b3f0a4`

**Brief:** `docs/review_brief_freeze_3.md`

## Decision

**No blocking findings. No new non-blocking defects identified. Archive the reviewed commit.**

The previous recommendation for `e816bfd` carries forward to `ff45b43`: the intervening changes correctly add a fail-safe check and correct documentation without changing fitted models, predictions, scientific results or registered analysis rules. No refit or additional project edit is required by this review.

I reviewed all six changed files, not just the plan wording. The diff contains 234 insertions and 10 deletions, including the copied review, disposition and brief. Checks extended beyond the diff where necessary to validate the new claims and release identity.

## Findings and dispositions

| Item | Conclusion | Blocking status |
|---|---|---|
| F2-1: stale migration record after a future refit | Correctly addressed by stopping early with recovery instructions; existing valid migration evidence is preserved. | Resolved; not blocking |
| Plan status and exposure record | Accurately incorporate D034/D035 and the second freeze review's full allowed-year prediction comparison. | No defect identified |
| 2025 release wording | Correctly distinguishes the released summary products from unreleased PUMS files. | No defect identified |
| D035 pre-deposit claims | Supported by the independent checks below; historical author-run claims are distinguished from my own reruns. | No blocking discrepancy |
| New commit's package | Isolated build and verification passed for the actual new commit. | No defect identified |

## Export safeguard: implementation and execution

The changed branch runs after inventory validation, model-file hash checks and model-object audits. If no cache needs removal, it now compares each recorded export's new hash with the current manifest and its original hash with the manifest's `exported_from_sha256`. Either mismatch stops execution before writing. The suggested recovery preserves the historical record and permits a new current audit. This implements the fail-safe alternative proposed in F2-1.

I exercised the actual changed `main()` with controlled fixtures for:

1. A matching existing record: succeeds and preserves bytes.
2. A changed current-model hash: rejects and changes no fixture files.
3. A changed original-model hash: rejects and changes no fixture files.
4. A recorded export whose model is absent from the manifest: rejects and changes no fixture files.
5. An existing empty-export audit: succeeds and preserves bytes.
6. No existing record: writes an empty-export current audit.

All six passed. These branch tests use controlled pipeline dependencies; they are not represented as real-model tests. Separately, I ran the changed script in an isolated analysis copy against all **98 current models**, with the allowed 2014 inputs needed to establish the expected model inventory. It reported zero training caches and that the existing record matches the manifest and is kept.

The output gate already makes the same two export-identity comparisons. The change therefore moves failure earlier for a future refit; it does not relax acceptance or require regenerating historical migration evidence. The training, prediction and analysis implementations and their current result files are unchanged in this diff.

## Plan and review record

The committed second-freeze report is byte-identical to my delivered report. Its recommendation is explicitly historical and identifies `e816bfd`; it does not misleadingly claim that the new commit had already been reviewed.

The plan's exposure statement now includes the full 2014–2018 ExpGrad prediction recomputation, consistent with that report. The updated decision range includes the model-manifest values changed by D034. The count of two completed freeze reviews is correct for the history preceding this final diff check; it does not require another plan-edit cycle merely to count this check.

The 2025 wording is supported by the official [2025 ACS release schedule](https://www.census.gov/programs-surveys/acs/news/data-releases/2025/release-schedule.html), updated 29 October 2026: the summary-product release is dated 29 October, while the 1-year PUMS release remains TBD. This check used release metadata only, not demographic outcomes. The wording is supported as of this review; a substantially delayed deposit would need its date-sensitive status checked again.

## Independent checks of D035

I independently checked the frozen dictionary CSVs and the relevant code:

- Required input variables are present for 2019 and 2021–2024, accounting for `STATE` from 2023 and `RELSHIPP` replacing `RELP`.
- COW, SCHL, MAR, SEX and RAC1P code sets agree across the listed 2017–2024 dictionaries.
- OCCP code sets agree from 2018 onward; the effective occupation-group mappings also agree, including the already-documented prefix corrections.
- Relative to 2018, POBP loses 456 from 2022 and additionally 463 in 2024, with no added codes in these comparisons. Those deletions are covered by the existing merges.
- All numeric RELSHIPP codes in the later dictionaries are mapped.
- The frozen CPI workbook contains annual averages for every year 2014–2025.

The official [2019 directory listing](https://www2.census.gov/programs-surveys/acs/data/pums/2019/1-Year/) and [2024 directory listing](https://www2.census.gov/programs-surveys/acs/data/pums/2024/1-Year/) contain both `csv_pus.zip` and `csv_ppr.zip` at the download script's locations. I inspected listings only and did not open or download those archives.

I also independently constructed synthetic raw ZIP fixtures for 2019, 2023 and 2024, using `psam_` CSV members, separate Puerto Rico files, string serial numbers and the appropriate ST/STATE layout. Each fixture contained 57 input rows: 52 expected survivors across all 51 registered geographies and five deliberate exclusions. The real builder produced the expected sequential counts **57 → 56 → 55 → 54 → 53 → 52**, retained Puerto Rico and preserved string identifiers. An accepted row exercised AGEP=17, PINCP=101, WKHP=1 and PWGTP=1.

For each fixture year, the real year-frame/harmonisation and prediction-writing code evaluated all **97 applicable frozen models**. Every saved vector had the expected length and finite values in [0,1]. The raw-code model was excluded by the existing prediction-year rule. Thus **291 model/year checks passed**. The fixture harness redirected all raw, derived, provenance and prediction outputs to a separate scratch directory; its access guard accepted only those synthetic paths. No archive flag was created.

These reruns corroborate the substance of D035. They do not establish the execution history of the author's uncommitted scratch tests or prove compatibility with every possible future empirical record. D035 labels those tests as the author's checks; I found no reason to change that attribution or block the deposit.

## New-commit archive verification

I cloned the new commit into a separate review directory and supplied only the previously frozen 40 non-person reference files and 98 current models. The actual archive builder produced **267 members**: 129 commit-tree files, 40 references and 98 models. The increase from the previous 264 is exactly the three newly committed documentation files.

I independently compared the member set and every member hash against the commit blobs or frozen manifest hashes. All matched. The verifier then returned no problems using a synthetic matching remote publication record and the new commit's Software Heritage revision identity. No real publication or remote receipt verification is implied by this test.

D035's 264-member dry-run statement explicitly refers to `e816bfd`, so it remains accurate historical evidence; it is not a mistaken size claim for the new package.

## Scope, safeguards and release recommendation

The original working tree remained clean at `ff45b43304ad4e14e5c4a9de8ad75b3e847ef5b4`. No project files were edited. No real package was built inside the project, nothing was published, and no `prereg/ARCHIVED` flag was created. No ACS person records for 2019 or later, or later-year empirical results, were accessed.

This is a verified diff review building on the previous full review, not a claim that software or a scientific study can be proven universally error-free. The new code paths, documentation claims and new-commit packaging passed the checks described above. I found no substantive reason for another fix-and-review cycle before deposition.

Build and deposit the reviewed commit, record that same revision in Software Heritage, and verify the actual published package and receipt before creating the archive flag or opening later-year data. The earlier commit's package and receipt must not be substituted for the new one.

**Final recommendation: archive.**
