# Disposition of independent QA round 3 (report: `docs/qa_independent_round_3_report.md`)

Date: 20 Nov 2026, before the Stage A rerun. Decision log: D027. All findings accepted. No real 2019+ data used.

| # | Disposition | Change | Refit impact | Validation |
|---|---|---|---|---|
| R3-1 | Accepted | Semantic configuration serialised by value into the fit and prediction specifications; settings moved to named constants used by the code; prediction code list includes the scaler, pooling and the full data-to-design path. | None beyond the planned refit. | `scripts/test_specs.py`: 9 one-setting changes, each changes exactly the expected specifications. |
| R3-2 | Accepted | Derived tables used only with build provenance (raw-file hashes, build-code hash including column selection/types and library versions), checked on every load; legacy tables refused; both raw files required; append-only raw-hash log. Mac run rebuilds 2014–2018 first. | None: a rebuild with the current builder reproduced all five tables byte for byte (checked in the VM). | SHA-256 identical and pyarrow content equal for 2014–2018. |
| A3-1 | Accepted | `verify_archive.py build/verify`: package members hashed, full inventory incl. every model file against the archived manifest, identical local copies, Zenodo record (published, DOI, MD5, size), manual Software Heritage check recorded. | None. | `scripts/test_archive.py`: 6 cases (incomplete package fails although the receipt matches it, etc.). |
| A3-2 | Accepted | Provenance records the hash of every consumed input; stale inputs reported by the gate; test results record their script hash. | None. | Lineage regression test in `test_specs.py`. |
| A3-3 | Accepted | Plan and code describe unconditional operating characteristics, no conditional guarantee; simulation adds negative θ, a trend history, null-conditioned rates with denominators, MC SEs, the seed-mean SE convention. | None. | Rehearsal: acceptance passes. |
| A3-4 | Accepted | Only a complete validation run writes the registered file; the gate recomputes acceptance from the detailed rows and requires complete grids. | None. | Rehearsal. |
| A3-5 | Accepted | Support criterion (ESS ≥ 50%), tolerance cap 0.05, total-variation gate with noise allowance. | None. | Real 2014→2018 fails before / passes after; synthetic concentrated-weight and rare-category failures. |
| A3-6 | Accepted | Valid-split degrees of freedom; ≥ 95% valid splits required in every configuration (else failure); "approximate" wording. | None. | Rehearsal (correctly fails on the tiny sandbox sample). |
| A3-7 | Accepted | One fitting function per model family; family-specific fit specifications. | None. | Family-isolation tests. |
