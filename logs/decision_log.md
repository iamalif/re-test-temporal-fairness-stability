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

## D008 - 2026-11-19 - Admin checks
- dap-alif copy deleted (researcher). uv 0.13.9 installed (Homebrew).
- folktables issue #51 (open, Feb 2025): POBP value "456" appears in data but not in the data dictionary consulted;
  maintainer: schemas differ between years, check the matching dictionary year. -> Harmonisation tables are built
  per survey year from that year's dictionary; unknown codes are counted and reported, never silently mapped.
- TMLR editorial policies (fetched 19 Nov 2026): yearly per-author quota, generalized harmonic rule, N_1 = 2 (sole author),
  doubled for reviewers/AEs (N_1 = 4); desk rejects spend budget; a rejected paper resubmits as a new submission.
  Reproducibility studies are in scope; a Reproducibility Certification exists for papers whose primary purpose is reproduction.
  -> Kaggle paper plus a possible resubmission plus this paper can exceed 2 in one year. Mitigation: researcher volunteers
  as a TMLR reviewer; avoid any desk-reject risk (template, anonymisation, claims statement).
- Ethics: independent research, no university involvement. Secondary analysis of public, de-identified, CC0 microdata;
  no interaction with people. The paper states this; it does not claim any institutional endorsement.

## D009 - 2026-11-19 - Google Scholar citing-article check (researcher's screenshots, first 2-3 pages per term)
- Anchor "Cited by", Since 2026, search within citing articles: temporal (~58 results), drift (~62), 2021 (~245), 2024 (~232),
  geographic (~40). First 2-3 pages per term inspected.
- None re-runs Ding et al. Section 4.1 on 2019+ ACS, and none compares temporal and geographic fairness stability on one scale.
- Read in full before archiving (design only; flag any 2019+ ACS results):
  - Lammers, Defrance et al., "Fairness in the Flow: An Overview and Drift-Aware Evaluation of Fair Classifiers for Drifting
    Data Streams" (EWAF 2026).
  - Wang, Chen, Shen, "DriftFair: Anytime-Valid Temporal Fairness Monitoring and Shift Attribution..." (World Scientific
    Research Journal 2026) - claims an additive decomposition of observed fairness drift (talent-promotion data). Relevant to
    our decomposition novelty claim.
  - Ismael, "Measuring Model Durability under Progressive Tabular Distribution Shift" (Research Square 2026) - how long a
    classifier stays useful; relevant to the certificate-expiry framing.
  - Taturyan, Laclau, Clemencon, "A Comprehensive View of Fairness through Distributional Stability" (arXiv 2609.37081).
  - Sikder, Johnson, Heintz, "StreamFair: Online Fair Adaptation Under Temporal Intersectional Drift" (AI Transparency Journal 2026).
  - Huby, Byun, "Label-Noise Decay Confounds Loss-Based Drift Attribution" (TMLR) - caveat for loss-based shift attribution.
- Citation update: Cai, Namkoong, Yadlowsky, "Diagnosing model performance under distribution shift", Operations Research 2026
  (the DISDE decomposition planned in brief section 8.5).
- Side note: an LLM fairness paper (ACL 2026) samples ACSIncome (2024), so 2024 ACS loaders are in informal use.
- Scholar alert on the anchor's citations: to be created by the researcher.

## D010 - 2026-11-19 - Schedule revised
- The brief's 4-5 months assumed 8-10 researcher-hours a week of hands-on work. With Claude doing implementation and the
  researcher reviewing, the binding constraints are: (1) the pre-registration must be complete and independently reviewed
  before any 2019+ file is opened; (2) compute (estimated 40-80 CPU-hours); (3) TMLR accepts no submissions from
  30 Nov 2026 to 3 Jan 2027.
- Target: pre-registration archived in about 1-2 weeks; confirmatory runs, decomposition and paper drafted by late December;
  submission on or after 4 Jan 2027 when TMLR reopens.

## D011 - 2026-11-19 - Target: submit before the TMLR pause (30 Nov 2026, 23:59 AoE)
- Researcher's goal. Feasible only with a tightly scoped confirmatory core; quality gates are not relaxed.
- Scope kept (confirmatory): re-test of Section 4.1 / App. D.3 on 2019 and 2021-2024 (DP, EO, accuracy; unconstrained,
  post-processed, ExpGrad, LFR if runtime allows); persistence of the 2014-certified constraint; fairness vs accuracy stability
  on a common scale; temporal vs geographic shift on one axis (large states).
- Scope kept (pre-specified secondary): decomposition into recoding, label definition, composition (reweighting) and
  conditional label change; survey-weighted vs unweighted.
- Deferred (not in this paper): certificate-expiry/time-to-violation framing beyond a descriptive remark; other folktables tasks;
  other model classes; harmonised loader released only as code with the paper, not as a contribution.
- Go/no-go checkpoint 27 Nov 2026: if the confirmatory results, checks and draft are not at standard, submission moves to
  4 Jan 2027 or later. A quota note: a 2026 submission uses the 2026 budget if TMLR's year is the calendar year.

## D012 - 2026-11-19 - Reconstruction findings so far (EXPLORATORY; 2014-2018 data only)
- Environment: pyproject.toml + uv.lock (Python 3.12; numpy 2.5.5, pandas 3.1.1, scikit-learn 1.9.1, scipy 1.17.1,
  fairlearn 0.15.0, aif360 0.6.1, statsmodels 0.15.0, folktables @ ebace19, pdfplumber).
- Loader (src/data.py): reads raw Census zips, ACSIncome filters in folktables' order, DC excluded (not in folktables'
  state list). Rows without Puerto Rico: 2014 1,577,844; 2015 1,594,081; 2016 1,608,420; 2017 1,636,312; 2018 1,655,429.
  The brief's sandbox counts (2014 1,587,856; 2018 1,664,500) equal these plus Puerto Rico (10,012 and 9,071 implied),
  i.e. folktables' 50 states + PR. PR files (csv_ppr.zip) added to the stage-1 download script.
- Figure 4 of arXiv v3 is vector graphics. scripts/digitise_figure4.py recovers its plotted values (~1e-4 precision):
  GBM accuracy 2014-2018 = .8231 .8127 .8094 .8023 .7977; DP = .1634 .1652 .1639 .1629 .1636.
  Legend colours: GBM blue, ExpGrad purple, Postprocessing green, LFR orange. ExpGrad DP .013-.022; LFR DP .106-.108;
  Postprocessing DP about 0. (Correction to brief: LFR barely reduces DP; ExpGrad does.)
- Literal App. C GBM (exponential loss, 5 trees, depth 5) does not reproduce: 2018 in-year accuracy .723, DP .058
  (Table 2: 81.7%, 17.7%). Exponential loss, depth 5, 100 trees: 2018 in-year .811 / .178.
- Trained on 2014 (100 trees), common feature scale: accuracy 2014-2018 = .8232 .8172 .8148 .8117 .8068 - 2014 matches
  Figure 4 but the decline is shallower. With features standardised by a scaler fitted separately on each year,
  accuracy = .8232 .8148 .8093 .8042 .7987, within 0.002 of Figure 4 in every year. DP under either variant is
  about .153-.161, about 0.008 below Figure 4.
- Interpretation (tentative): the published accuracy decline is reproduced when each year is standardised separately,
  which shifts a 2014 tree model's inputs in later years. If confirmed, part of the published accuracy decline is a
  preprocessing effect, which bears directly on "fairness is more stable than accuracy". To be checked: seeds, Puerto
  Rico, other tree counts, the three interventions, and Figure 13 (EO). Report neutrally as a reproduction finding.
