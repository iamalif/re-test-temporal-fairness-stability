# Brief for the second freeze check (20 November 2026)

Your freeze review (`docs/qa_freeze_review_2026-11-20.md`, reviewed commit 28a6156) has been answered
(`docs/qa_freeze_disposition.md`, decision log D033) and the model migration has been run (D034, log
`logs/migration_D034.txt`). The commit you are reviewing is the one intended for deposit. The next steps cannot be
undone: build the package from this commit, publish on Zenodo, save in Software Heritage, then open later-year data.

## Rules (unchanged)

- No ACS person records for 2019 or later, and nothing that could reveal later-year results.
- 2014–2018 data, result files, code, documentation and synthetic data are allowed.
- Do not modify project files. Do not build the real package inside the project, publish anything, or create
  `prereg/ARCHIVED`. Write your report as a separate file.

## Scope

All changes since `28a6156`, and the deposit as a whole:

1. Whether the dispositions of FZ-1 to FZ-5 resolve the findings.
2. The model migration: whether the deposited model files now hold no row-level data, whether the migration and its
   evidence (export record, prediction identity, result equivalence, provenance) are complete and correct, and
   whether anything in the frozen record still refers to the old model bytes as current.
3. The archive tooling as rewritten (`scripts/verify_archive.py`, `scripts/test_archive.py`): whether any realistic
   sequence of actions can still yield a deposit other than the intended one, or an `ARCHIVED` flag without a
   correct deposit.
4. Deposit contents and licence terms (you may build a package in a separate copy).
5. Anything else that should be fixed before an irreversible deposit.

## Report format

Same as before. For each finding give its severity, location, evidence and suggested fix, and mark it **blocking
before archive** or **non-blocking**. End with an archive recommendation: archive / archive after the listed fixes /
do not archive.
