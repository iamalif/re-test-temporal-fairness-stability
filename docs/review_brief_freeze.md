# Brief for the freeze check (20 November 2026)

Your final pre-archive review (`docs/qa_final_pre_archive_review_2026-11-20.md`, reviewed HEAD `e612952`) has been
answered (`docs/qa_final_pre_archive_disposition.md`, decision log D031). A further self-check before the freeze
led to more changes (D032). The next steps cannot be undone: the package will be built from the commit you are
reviewing, published on Zenodo (immutable) and saved by Software Heritage; then the later-year data will be opened.
Please check the state that will be frozen.

## Rules (unchanged)

- No ACS person records for 2019 or later, and nothing that could reveal later-year results.
- 2014–2018 data, result files, code, documentation and synthetic data are allowed.
- Do not modify project files. Do not build the real package inside the project, publish anything, or create
  `prereg/ARCHIVED`. Write your report as a separate file.

## Scope

All changes since `e612952` (`git diff e612952 HEAD`), and the archive as a whole:

1. **Your earlier findings.** Whether each disposition actually resolves the finding, and whether any new wording
   (plan Sections 2, 7.6 and 10; status line) is accurate.
2. **Archive tooling.** `scripts/verify_archive.py` and `scripts/test_archive.py` as changed. Whether build, the
   receipt and verify do what plan Section 10 says, and whether any realistic sequence of user actions could produce
   a deposit that differs from what is intended, or an `ARCHIVED` flag without a correct deposit.
3. **Deposit contents.** Whether the package (you may build one in a copy of the project, outside it) contains
   everything that must be frozen and nothing that must not be deposited (person records, third-party copyrighted
   papers, secrets, files outside the archived commit other than models and reference inputs). Whether the licence
   terms in `LICENSE` fit the contents.
4. **Redactions.** Whether the D032 redactions are complete for their stated purpose and change no design content.
5. **Anything else** that should be fixed before an irreversible deposit.

## Report format

Same as before. For each finding give its severity, location, evidence and suggested fix, and mark it **blocking
before archive** or **non-blocking**. End with an archive recommendation: archive / archive after the listed fixes /
do not archive.
