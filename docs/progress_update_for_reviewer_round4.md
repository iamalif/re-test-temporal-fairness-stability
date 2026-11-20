# Progress update for the independent reviewer: round 4 (20 November 2026)

Thank you for round 3 (`docs/qa_independent_round_3_report.md`). We accepted all nine findings. The responses are
in `docs/qa_independent_round_3_disposition.md`, and the reasons are in decision log entry D027. Please verify
everything in the code and files themselves.

## State

- The plan is not archived. No ACS person record for 2019 or later has been opened.
- The Stage A rerun has not started.
  - It will first rebuild the 2014–2018 tables, which writes their build records.
  - It then refits all 98 models and regenerates all Stage A and validation outputs.
  - Until then, the Stage A and validation result files are stale. The exceptions are the synthetic test results,
    which are current.

## Changes in response to round 3

**Refit-relevant findings**

- **R3-1 (specification coverage)**
  - The fit and prediction specifications now include every semantic setting by value: feature sets, group
    columns, label threshold and rule, race codes, pooling, GBM, post-processing and LFR settings, the ExpGrad and
    DemographicParity library defaults, and the mapping.
  - The prediction code list now also covers the scaler, the pooling and the data-to-design path.
  - `scripts/test_specs.py` changes 9 settings one at a time. In each case exactly the expected specifications
    change.
- **R3-2 (provenance of the 2014–2018 tables)**
  - Each derived table records the hashes of its raw files and of the build code, including column selection,
    types and library versions. This record is checked on every load, and tables without it are refused.
  - Both raw files are required.
  - The raw-hash log is append-only.
  - A rebuild with the current builder reproduced all five existing tables byte for byte, so the earlier analyses
    and the reconstruction used the same tables.
- **R3-7 (fitting code per family)**
  - Fitting is now one function per model family.
  - A family's fit specification hashes only the shared code and its own family code. This is tested.

**Analysis and archive findings**

- **A3-1 (archive verifier)** The archive verifier now opens the package and hashes every member. It requires the
  full inventory, including every model file checked against the archived manifest. It also checks the local
  copies, the Zenodo record and a manual Software Heritage check. Offline tests use a mocked Zenodo record.
- **A3-2 (input lineage)** Every result file records the hashes of the files it consumed, and the gate flags stale
  inputs. A lineage regression test covers this.
- **A3-3 (error-rate claims)**
  - The plan now claims only unconditional operating characteristics.
  - The simulation now covers both signs of θ, a trend history and the seed-mean SE convention.
  - It reports null-conditioned rates with their denominators, and Monte Carlo SEs.
- **A3-4 (validation runs)** Only a complete validation run is accepted. The gate recomputes the acceptance
  criteria from the detailed results and requires complete case grids.
- **A3-5 (balance gate)** The balance gate adds an ESS support floor, a cap on the tolerance and a total-variation
  check for each categorical feature. On real 2014→2018 data every group fails before reweighting and passes
  after. Synthetic failure cases were added.
- **A3-6 (split calibration)** The split calibration uses the number of valid splits for each bound and requires
  at least 95% valid splits in every configuration, so there is no silent default of 1.

## Rehearsal

The rehearsal used the final code in a sandbox, with real 2014–2018 subsamples, synthetic stand-ins for the later
years and 30 trees per model.

- **Stage A gate.** Everything passes except the split calibration. It fails because the 60,000-row sample is too
  small: some splits of one state contain no Black person above $50,000. This is correct behaviour. In the real
  2018 data every one of the 20 states has at least 130 such persons.
- **Stage B gate.** It passes apart from P1, which was skipped for time.

## Request

Please do a fourth independent, critical review with the same rules and report format, following
`docs/review_brief_independent_qa_2.md`. In Part 1, verify the round-3 dispositions. Put anything refit-relevant at
the top of the report.

Your round-3 report advised against repeatedly changing the scientific specification to satisfy a growing
infrastructure checklist. We agree. Please mark each finding as either:

- **blocking**: it affects validity or must be done before the refit or the archive, or
- **non-blocking**: an improvement that can be recorded as a limitation or done later.
