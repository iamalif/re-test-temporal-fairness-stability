# Decision log (append-only)

Rules: never edit or delete an entry. Corrections are new entries that reference the old one.
Format: ID, date (Europe/Stockholm), decision or event, reason, who.

---

## D001 - 2026-11-18 - Project set up
- Brief (prepared 18 Nov 2026) adopted as the starting point; copied to `docs/BRIEF_2026-11-18.md`.
- Roles: researcher directs and reviews; Claude (Opus) is the lead AI collaborator; a second AI assists.
- `research_collaboration_rules.md` not yet in the repository; requested from the researcher.

## D002 - 2026-11-18 - Step 0 novelty check: proceed
- Dated search run 18 Nov 2026 (automated deep-research task). Record: `docs/prior_work_search_2026-11-18.md`.
- Result: no work found that re-runs Ding et al. Section 4.1 (US-wide GBM, trained 2014, DP/EO, LFR/ExpGrad/post-processing)
  on 2019+ ACS, and none that puts temporal and cross-state fairness shift on one scale with a decomposition.
- Decision: proceed, with narrowed claims:
  - headline = confirmatory re-test + temporal-vs-geographic explanation/decomposition;
  - "certificate expiry" = secondary, cite arXiv 2611.20901 and 2611.11783; claim only a tabular, frozen-model estimate;
  - harmonised loader = enabling artefact, not a claimed contribution (informal 2019+ patches exist).
- Open search gaps to close before archiving the plan: Semantic Scholar citing list (Sep-Nov 2026), OpenReview
  (TMLR under review, ICLR 2027), folktables GitHub issues/PRs since 2023, Butnaru & Crisan paper text,
  repos Hnhy1806/fairness-over-time and PartowMoradiK/stable-rankings-shifting-fairness, Wicker et al. arXiv 2311.11911 in full.

## D003 - 2026-11-18 - Exposure record update
- The novelty-check report was written under a rule not to report post-2018 ACS outcome numbers. It reports none.
- It does report 2014-2018 results: Chen et al. 2022 shift attribution (label vs covariate) and
  Butnaru & Crisan's 2018 California sex-DP and equalized-odds gaps under threshold recalibration (LR). Both are original-cohort years.
- It notes that Ceross (2609.09788), Tomar (2506.23033), Wicker et al. (2311.11911), arXiv 2412.10575 and Quy et al. (2110.00530)
  contain post-2018 ACS results; these were not read. Wicker et al. contains post-2018 data-shift distances: do not read
  those numbers before archiving; read only design sections.

## D004 - 2026-11-18 - Working rules and venue constraint
- Researcher waived the separate `research_collaboration_rules.md`; the working style in brief section 1 governs.
- Commits use the researcher's GitHub noreply address (set per repository).
- TMLR per-author annual quota (from 1 Jul 2026; secondary source says 2 papers/year for a single-author-only submitter,
  doubled for active reviewers) - to verify on the official TMLR page. The researcher's Kaggle re-test paper is under
  review at TMLR, so a resubmission of it and this paper could compete for the same quota. Plan submission timing accordingly.
- Remaining prior-work checks split: researcher checks Google Scholar, OpenReview, IEEE Xplore/AICCSA, GitHub repos (checklist given 18 Nov 2026).

## D005 - 2026-11-18 - Second search pass (Gemini, run by researcher)
- Automated pass, search-engine-indexed sources only. New hits (all tangential, none tests fairness over time on 2019+ ACS):
  arXiv 2610.15015 (taxonomy), 2610.30472 / ICLR 2027 DiffLTM, ICLR 2027 Delta-Audits (openreview 5ftq4e6alF),
  ICLR 2027 CAFE (XWuLGI5zio), ICLR 2027 SPBM, WiML@NeurIPS 2026 "Fairness After the Fact" (MWTt0Pg5gE), TMLR 2026 QFJuVreJDC.
  Specifics not verified by us.
- AICCSA 2026 programme lists Butnaru & Crisan paper (#3189, Track 4); full text not public; not on IEEE Xplore yet.
- OSF and AsPredicted: 0 hits for "folktables" and "American Community Survey" + "fairness".
- Exposure: CAFE abstract (ICLR 2027) states an OOD accuracy result on folktables; data years unknown; not fairness over time. Logged as seen.
- Still open (pass relied on search indexes, so these were not actually checked): Google Scholar citing list (Since 2026);
  READMEs of ClaudiuBu/benchmark-fairness-folktables, Hnhy1806/fairness-over-time, PartowMoradiK/stable-rankings-shifting-fairness;
  folktables issues/PRs created after 2023-01-01.
- Decision: remaining checks are not a blocker for work on 2014-2018 data, reading, and harmonisation tables.
  They are a hard blocker for archiving the pre-registration, and are repeated just before archiving.

## D006 - 2026-11-19 - Manual GitHub checks (researcher's browser screenshots)
- folktables: last commit ebace19, 15 May 2024. Issues/PRs created after 2023-01-01: 19. None adds 2019+ survey years,
  RELSHIPP, OCCP crosswalk or inflation adjustment. Relevant to us: #49 "Data download fails w/ 403 Forbidden" (Feb 2025) and
  #50 archive.org mirror flag (download risk; we download files directly); #51 "Wrong matching between data and schema"
  (Feb 2025; to read); #39/#52 NaN-to-0 postprocessing; #37 "Why restricted to 2014 onwards?"; #38 "support for years >= 2000".
- folktables source (downloaded by researcher to folktables-main/, not committed): library and tests only.
  No experiment code for the NeurIPS paper. Original experiment code: not found in this repository.
- ClaudiuBu/benchmark-fairness-folktables: README read. Confirms CA only, LR, 2014 -> 2015-2018, ACSIncome + ACSEmployment,
  sex and race (White vs non-White), 20 seeds, unweighted. Authors: Butnaru and Crisan. Cites folktables (Ding et al.) as data source.
- Hnhy1806/fairness-over-time (single contributor, very active: last commit about 1 hour before the check, 22 commits, Streamlit app):
  Texas, 2014 -> 2015-2017, LR and XGBoost, frozen, ExpGrad with equalized odds; DPD and EOD over 10 race/ethnicity x sex groups;
  diagnoses label drift (share over $50k rising; split into real growth vs CPI-U inflation) vs feature drift (PSI/KS) and SHAP.
  Its README states a mechanism matching our planned explanation (labels move, features barely move, fixed cutoff).
  "Future work" lists: more years and states, with an occupation-code mapping to include 2018 onwards.
  -> Closest substantive overlap so far for the explanation component, but one state, 2014-2017, not a paper (no paper linked).
  -> Raises scoop risk: its stated next step is our extension. Cite as prior evidence; keep its result as a prediction to test US-wide.
- PartowMoradiK/stable-rankings-shifting-fairness (FH Joanneum; paper "Stable Rankings, Shifting Fairness", arXiv link pending):
  ACSPublicCoverage, train on one state-year, evaluate on 49 other state-years, XGBoost/RF, SHAP-based label-free monitoring.
  Different question. Years not stated in README.
- Exposure: the Hnhy1806 README shows 2014-2017 Texas results (original-cohort years, permitted). The PartowMoradiK README states
  an outcome ("false positive rate gap changed by up to 13.4 points" across shifts; survey years not stated; PublicCoverage task).
  Logged as seen. Not used to set any margin.
- Still open: Google Scholar citing list (Since 2026); folktables issue #51 text.

## D007 - 2026-11-19 - Repository home
- Repository moved to github.com/iamalif/re-test-temporal-fairness-stability (public, researcher's choice).
  The dap-alif copy is to be deleted. Pushes use a dedicated SSH key for iamalif, so the gh login (dap-alif) is unchanged.
- Consequence noted: plan, decision log and prior-work notes are visible before the pre-registration is archived.
  For double-blind review, the submission will link an anonymised mirror, and the repository name and title must not
  appear in the manuscript.
