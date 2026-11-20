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

## D013 - 2026-11-19 - Reconstruction run set up (2014-2018 only)
- Puerto Rico files added; ACSIncome universe now 2014 1,587,856 ... 2018 1,664,500 rows, matching the earlier sandbox
  build exactly (50 states + PR, no DC).
- Figure 13 (EO, arXiv v3 p. 47) digitised with the same method. GBM EO 2014-2018 = .175 .209 .182 .190 .201;
  ExpGrad (EO) .015 .046 .017 .038 .058; Postprocessing (EO) -.008 .030 .001 .007 .019.
  The digitiser now reads tick labels and legend order from the page itself (axis fits exact at the ticks).
- src/models.py fixes the open implementation choices (see its docstring); scripts/reconstruct.py runs
  56 jobs (core interventions at 100 trees, literal 5-tree settings, GBM over 5 seeds x 4 tree counts, each under
  per-year and common scaling). Smoke test on 20,000-row subsamples passed for every method (results/smoke/).

## D014 - 2026-11-19 - Feature harmonisation (documentation only; distributions checked on 2014-2018)
- Dictionaries: COW, SCHL, MAR, SEX, WKHP, AGEP codes identical in the 2014-2018, 2019 and 2024 dictionaries.
  RELP replaced by RELSHIPP in 2019. POBP: 208 Cyprus (to 2016), 456 Tunisia and 463 South Sudan (absent 2024).
- OCCP: every OCCP code in the 2014-2017 data is in the 2017 dictionary (478 codes; 2010-based); 2018 data use
  529 codes, 151 not in the 2017 dictionary and 100 2017 codes gone (matches the brief).
  The official crosswalk sheets list full Census codes, several of which PUMS aggregates, so a fine-grained
  one-to-one PUMS crosswalk is not available from documentation alone.
- Decision: harmonised occupation = major group from the label prefix of each year's own dictionary (25 groups),
  with (a) prefixes supplied for 1555 and 8000 (missing in the 2018 dictionary only; 2019 gives ENG/PRD) and
  9920 (unemployed, own group), and (b) the 8 one-to-one cross-group moves in the crosswalk assigned their 2018
  group in 2010-coded years. Residual 2018 jump against the 2014-2017 trend: at most 0.5 pp of rows per group
  (MGR -0.51, BUS +0.47 from the split of 2010 code 0430). Reported as a known residual artefact.
- RELP_H: roomer/boarder (11), housemate/roommate (12) and other nonrelative (15) merged in every year
  (2.3-2.4% of rows in 2014-2018); RELSHIPP mapped to RELP categories (spouse and partner codes merged across sex).
- POBP_H: 208 -> 169, 456 -> 464, 463 -> 469 in every year (58-187 rows per year).
- Open: confirm POBP collapses against the Census "variable changes" notes before archiving.

## D015 - 2026-11-19 - Reconstruction results (56 runs, 2014-2018 only; results/reconstruction/comparison.csv)
- Literal App. C GBM (5 trees) is far from the paper: accuracy about 0.11 below Figure 4 in every year, DP about 0.13 below.
  It was not what produced the figures.
- GBM, exponential loss, depth 5, 100 trees, each year standardised with its own scaler ("per_year"):
  accuracy within 0.0024 of Figure 4 in every year (mean abs. dev. 0.0012, SD over 5 seeds 0.0003);
  2014-2018 decline 0.0240 vs published 0.0254. With one common (frozen) scaler the decline is 0.0165 (5-seed mean),
  i.e. about a third of the published decline is reproduced only under per-year standardisation.
  DP 0.152-0.158 vs published 0.163-0.165 (about 0.01 lower), flat in both: the DP-stability pattern reproduces.
- EO (Figure 13): ours 0.156-0.167, flat; published 0.175-0.209 with a year-to-year zig-zag (2015 and 2018 high) that
  also appears in the published ExpGrad (EO) and Postprocessing (EO) series. Not reproduced by any variant; seed SD of
  the 2014-2018 change is about 0.007. Reported as an unexplained discrepancy.
- LFR: accuracy within 0.004 and DP within 0.006 of Figure 4 in every year (both scalings).
- ExpGrad (DP): accuracy within 0.004 (common) / 0.004 (per_year) of Figure 4; DP 0.004-0.015 vs 0.013-0.022.
- Postprocessing (fairlearn ThresholdOptimizer, all race groups): DP about 0 as published, but accuracy 0.015 (DP) and
  0.04 (EO) higher than published. The published postprocessing costs more accuracy; the EO version may have enforced
  equalized odds (AIF360's Hardt et al. implementation is equalized odds). Underspecified in the paper.
- Run cost: ExpGrad at 100 trees took about 7.5 h per fit with 6 jobs sharing the CPU; LFR about 34 min.
  Fitted models were not saved; the confirmatory runner must persist fitted models.
- Decisions for the pre-registration (to be finalised there):
  (1) base model: exponential loss, depth 5, 100 trees (reconstruction rule: tree count in {5,50,100,200} with the
      smallest mean absolute accuracy deviation from Figure 4 under the variant that best reproduces it);
  (2) primary pipeline: a frozen preprocessing (common scaler fitted on the 2014 training split), because a deployed
      model applies its training-time preprocessing; the per-year variant is reported as the reconstruction of the
      original pipeline;
  (3) the postprocessing and EO discrepancies are reported neutrally as reproduction findings.

## D016 - 2026-11-19 - Pre-registration draft v0.1 and the two-stage design
- Design: Stage A (before archiving) fits every final model once on 2014, saves it with a SHA-256 hash
  (results/models_manifest.json), predicts 2014-2018 and computes the margins (results/stage_a/margins.json).
  Stage B (after archiving) only evaluates the same frozen models on 2019 and 2021-2024. src/data.py refuses any
  year after 2018 until prereg/ARCHIVED exists (checked: guard raises).
- Confirmatory family C1-C8 (prereg Section 5), Bonferroni alpha 0.05/8, three-way decisions; margins defined by
  rules on 2014-2018 data (delta: largest 2014-2018 drift; epsilon: largest post-processed DP; floor 0.01;
  G: median noise-corrected cross-state change over the 20 largest states).
- Small sensitive-feature categories are pooled for the interventions (>= 100 training rows and >= 20 of each label
  to stay separate; pooled group assigned to the largest category if itself too small). Found necessary in the smoke
  test (degenerate labels in a tiny race group).
- Correction to the brief: incomes of $50,000 or more are not all multiples of $1,000 (2014-2018: about 80% are),
  because PINCP sums separately rounded components. Inflation- and base-rate-anchored thresholds are therefore put
  on the $1,000 grid with the nominal label's strict inequality, rather than "off the grid".
- ADJINC is a single value per year file (checked 2014-2018).
- Code written and smoke-tested end to end on 20,000-row subsamples of 2014-2018 (2017/2018 standing in for
  2019/2024): src/pipeline.py, src/analysis.py (unit-tested against analytic binomial SEs), scripts/stage_a.py,
  scripts/stage_a_analysis.py, scripts/stage_b_confirmatory.py. Secondary-analysis code (Section 8) still to write.
- Independent review brief for the second AI: docs/review_brief_prereg_v0.1.md.

## D017 - 2026-11-19 - Documentation checks, CPI, secondary-analysis code
- Census PUMS variable-change notes (data/raw/variable_changes/) read. Confirmed: Tunisia (456) collapsed into
  464 "Northern Africa, not specified" (from the 2022 1-year file; harmonise.py docstring says 2024, to correct after
  Stage A); South Sudan (463) deleted in 2024; Cyprus (208) refers to 2016 and earlier, destination not stated
  (kept as 208 -> 169 "Other Europe, n.s."; about 60 rows a year in 2014-2016; Census codes Cyprus in its Asia range,
  so 254 would have been equally defensible; not changed because Stage A was already running and the effect on a
  tree model is negligible). COW, PINCP, OCCP (2019-2024): label/cosmetic changes only. No change notes found for
  AGEP, SCHL, MAR, WKHP, SEX, RAC1P, PWGTP.
- BLS blocked the scripted CPI download (403); the researcher downloaded r-cpi-u-rs-allitems.xlsx manually.
  R-CPI-U-RS annual averages: 2014 347.7, 2018 369.1, 2019 375.8, 2024 462.5 (retroactive series; replaces the
  older CPI-U-RS PDF, whose 2014 value was 348.3).
- Inflation-anchored thresholds (2014-2018): 50,000; 50,000; 51,000; 52,000; 53,000. (Base-rate-anchored values are
  computed on the full data in Stage B.)
- Secondary-analysis code written and smoke-tested: scripts/stage_b_secondary.py (8.2-8.6),
  src/analysis.point (weighted point estimates), scripts/check_decomposition_2018.py (pre-archiving validation of
  the DFL decomposition on 2014 -> 2018, added to prereg 8.4).

## D018 - 2026-11-19 - QA round (no outcome data involved)
- Bug found and fixed before it could bite: the state column is named STATE from 2023 (2023 and 2024 dictionaries;
  ST in 2019-2022). src/data.py now reads STATE, renames it to ST, and checks that every required column is present
  (verified on 2014 and 2018 headers). scripts/download_stage2.sh added; it refuses to run before archiving (tested).
- Statistical fix: unweighted standard errors now cluster by household (state + SERIALNO), because the ACS samples
  households. Monte Carlo check with household-clustered outcomes: clustered SE 0.0171 vs empirical SD 0.0176;
  the unclustered SE (0.0112) was too small. Applied in stage_a_analysis, stage_b_confirmatory, stage_b_secondary
  before Stage A analysis ran; prereg 7.1 updated. Smoke tests re-run.
- Sync check: a device_commit_files call earlier reported success but left scripts/reconstruct.py at the older
  version (resume-robustness patch missing; the run itself used the old version, which is unaffected). All files
  now verified by checksum against the working copies.
- Paper and plan wording made exact: the literal 5-tree model is 0.10-0.15 below the published accuracy in every
  year and seed; the 100-tree choice minimises deviation under per-year standardisation (50 trees is closer under
  the frozen standardisation, whose curve shape does not match the published one).

## D019 - 2026-11-19 - Power fix: stability tests measured against the 2014-2018 baseline
- Problem (found in QA, from group sizes only, before any outcome was examined): the 2014 evaluation set is the
  20% test split (about 30,000 Black and 250,000 White rows), so a change measured from 2014 has an SE of about
  0.003 for the race DP gap; with the Bonferroni interval (z = 2.73) a "holds" decision would need |change| below
  about 0.002 for a 0.01 margin. C1, C2, C5 and C6 could almost never conclude stability.
- Fix: C1, C2, C5, C6 now test the deviation of m(t) from the model's 2014-2018 baseline mean (equal weight per year;
  Var(B) = sum Var(m_t)/25), SE about 0.0015 for the race DP gap. delta is redefined consistently as the largest
  deviation of a 2014-2018 year from that baseline (floor 0.01); the largest change from 2014 is still reported.
  C7 keeps change from 2014 (accuracy trends within the window; C7 compares two changes, no margin).
- Implementation: stage_a_analysis saves every US model-year estimate (values and covariance) to
  results/stage_a/estimates_2014_2018.json; stage_b_confirmatory computes the baseline from it. Smoke-tested.
  Prereg sections 5 and 6 updated. Done before Stage A analysis has run, so no margin value was seen first.

## D020 - 2026-11-19 - Full QA pass of plan, code and harmonisation (plan v0.2)
- Read every pipeline file against the plan. Fixed: occupation has 25 major groups plus a code for the long-term
  unemployed (26 codes), not 25; harmonise.py docstring (Tunisia collapsed from 2022, not 2024); broken indentation
  in plan section 3; plan section 10 now lists the exact Stage A/B commands.
- Checked: RELSHIPP -> RELP mapping against the 2017, 2019 and 2024 dictionaries (correct); the 2019-2024 occupation
  code lists and prefixes are identical to 2018 (no further break); every OCCP code 2019-2024 maps to a group.
- Gap closed: the 20 per-state DP-post-processed models were fitted but no analysis used them. Added secondary
  analysis 8.8 (constraint transfer: own state later vs other states in 2014) to the plan and to
  stage_b_secondary.py (smoke-tested).
- 8.2 wording made exact (band around 0 with epsilon = largest |DP| in 2014-2018; for LFR this is its own range).
- scripts/run_all.sh added (single command per stage); README updated. Plan bumped to v0.2.
- Sync: a commit of src/harmonise.py again reported success without updating the file; re-committed and verified
  by checksum. Every edited file is now verified by checksum after transfer.

## D021 - 2026-11-19 - Added secondary analysis 8.9: deployment in 2018
- Rationale: the confirmatory tests concern a model deployed in 2014, as in the original. A reviewer can ask whether
  the result is specific to that deployment year. Five base models and their DP post-processing (race, sex) are now
  also trained on the 2018 training split, frozen before archiving, and evaluated forward (2018 test split, then
  2019 and 2021-2024). Descriptive only; the 2014-2018 margins do not apply to them.
- Code: pipeline.model_prefix / train_year in the manifest (older entries default to 2014); stage_a_analysis and
  stage_b_confirmatory evaluate each model on its own training year's test split and only forward in time;
  stage_b_secondary 8.9. Full chain smoke-tested (fit, predict, stage A analysis, confirmatory, secondary incl. P1).
- Cost: 5 GBM fits plus 10 post-processing fits (minutes). Run after the current Stage A finishes:
  stage_a.py fit (fits only the new jobs), stage_a.py predict (skips existing files), stage_a_analysis.py.

## D022 - 2026-11-19 - EO interventions covered (secondary 8.2)
- Gap: the original Appendix D.3 also covers EO interventions; the plan tested only the unconstrained EO gap
  (C5, C6). The fitted EO-post-processed models (race, sex; 5 seeds) are now assessed like 8.2: |EO| at 2019 (race)
  and 2024 (sex) within epsilon_EO, the largest |EO| of that model in 2014-2018 (floor 0.01). Secondary, so the
  confirmatory family and alpha are unchanged. stage_a_analysis computes epsilon_eo; smoke-tested.

## D023 - 2026-11-19 - Independent QA 1: dispositions and changes (all before archiving; no 2019+ data opened)
Report: docs/qa_independent_1_report.md; point-by-point disposition: docs/qa_independent_1_disposition.md.
- Confirmatory family reduced to C1, C2, C3, C4, C6, C7 (Bonferroni alpha = 0.05/6).
  C8 (20-state sign test) is descriptive: the state comparisons share observations and estimated references, so the
  exact binomial test lacks a valid null (QA #1). C5 (EO race) is secondary: at the anticipated SE (0.0033
  unweighted, 0.0043 weighted) "holds" has probability 0.31 / 0.00 even with zero true change
  (results/validation/inference_validation.json), so it would spend alpha on a test that cannot conclude stability.
- C7 interval replaced. The Monte Carlo percentile interval under-covered in simulation (minimum coverage 0.93
  against a 0.992 target near zero changes). New: simultaneous Bonferroni box for the two changes, exact range of
  D over the box; G treated as fixed calibration constants with floor 0.005. Simulated coverage >= 0.995 at the
  anticipated covariance and under stress settings (SE x3, rho = +/-0.9); max P(wrong direction) 0.004.
- C3/C4 renamed "retention of the historical disparity envelope"; estimand: seed-average signed gap of the five
  frozen post-processed models; per-seed values reported as diagnostics.
- Randomised predictors (ThresholdOptimizer, ExpGrad) evaluated through expected predictions (positive-class
  probability), i.e. the expected metrics of the randomised policy; removes the dependence on row order and on
  reusing one random stream across years (QA #15). Metrics are linear in the prediction, so estimators carry over.
- BUG FOUND IN OUR HARMONISATION (while answering QA #13): DESTINATION_GROUP moved eight 2010 occupation codes to
  their crosswalk destination group, but five of them (2160, 2900, 3540, 4320, 9520) are SPLIT codes whose own group
  is among their destinations; the stated rule (whole moves only) gives just 4610 HLS, 5620 TRN, 5800 CMM.
  0.33% of 2014 rows were affected. The corrected mapping reduces the 2018 discontinuities of the affected groups
  (e.g. LGL +0.0011 -> 0.0000, MED +0.0012 -> +0.0001, OFF -0.0015 -> -0.0008). harmonisation_report.py now
  re-derives the set from the crosswalk and fails if harmonise.py differs.
  Consequence: every model trained on harmonised 2014 features is refitted (incl. ExpGrad); 2018-trained models and
  rawgbm are unaffected but refitted where the mapping fingerprint differs (deterministic). Models now record a
  fingerprint of the mapping content; stale models are refitted automatically and old entries are kept in
  results/models_manifest_superseded.json.
- New frozen family peryear_gbm_s0-4 (QA #12): each year standardised with its own full-population scaler, the
  training scaler fitted on all 2014 rows as in the reconstruction. Replaces the ad hoc 8.6 variant.
- Split variance (QA #14): scripts/check_split_variance.py estimates, on 2018 with 200 random 20% splits, whether
  variance estimates on a test split include the split's own randomness. Pre-specified: variances of every
  training-year test-split estimate are multiplied by max(1, 1/R) per metric and weighting.
- Reconstruction attribution corrected (QA #4): the paired preprocessing contrast within the reconstruction is
  0.0075 accuracy, 29.5% of the published decline; the earlier "35%" was the share NOT recovered by the
  common-scaler reconstruction and includes unexplained mismatch.
- Provenance and failure handling (QA #5-#8): model hashes verified on load; predictions carry a provenance record
  (model hash, data-file hash, row identity, convention) checked before use; atomic writes; exact model inventory
  (88 models) and 20 states / 380 pairs asserted; failed workers exit non-zero; reconstruction runs carry a code
  fingerprint and downstream scripts require the full 56-run inventory; Puerto Rico and the 51-geography set are
  mandatory; downloads go to .part files and are integrity-checked before use; CPI failure separated (exit 3).
  Tests: scripts/test_integrity.py (all tampering cases detected in smoke mode).
- Decomposition (QA #11): household-grouped cross-fitting folds; ESS, weight tails, overlap and group-wise balance
  diagnostics; clipping sensitivity (99.9%, 99%, none); residual named "conditional change plus approximation
  error"; reliability rule (DP check, max group SMD <= 0.10, clipping shift <= 0.005) gates P2.
- Outputs (QA #16): margin-sensitivity curves 0.005-0.03 for C1-C6; 8.9 reports changes with SEs; checklist
  prereg/OUTPUT_CHECKLIST.md enforced by scripts/check_outputs.py.
- Pending at the time of writing: Stage A rerun on the Mac (refit, predictions, split variance, Stage A analysis,
  decomposition check, inference validation, integrity tests), then prereg and paper text, then QA round 2.

## D024 - 2026-11-20 - End-to-end rehearsal before the Stage A rerun (no real 2019+ data)
- Rehearsal of the whole chain with the production (non-smoke) code paths in a throw-away sandbox: real 2014-2018
  person records subsampled to 60,000 rows a year; SYNTHETIC stand-ins for 2019 and 2021-2024 built from 2018 rows
  (incomes scaled, RELP recoded to RELSHIPP, new SERIALNOs); 30 trees instead of 100 to fit the time limit;
  everything else as registered (88 models, 5 seeds, 20 states, ExpGrad, LFR). Steps run: fit, predict 2014-2018,
  split-variance check, Stage A analysis, decomposition check, inference validation, integrity tests,
  check_outputs stage_a, predict for the stand-in later years, confirmatory, secondary (P1 on 3 states), all passing.
  No real later-year record was created or read; the sandbox is outside the repository.
- Fixes from the rehearsal: check_split_variance divides by zero for a constant metric (now no adjustment);
  validate_inference used unfloored yardsticks (now floored as in C7); geographic yardsticks, C8 and 8.8 aborted on a
  state with an empty group (now recorded as not computable, per prereg 7.5; does not occur in the real 2014 data,
  where the smallest relevant count is 20); the inventory record kept only the last check (now one record per set
  of years, so Stage A and Stage B both remain visible).
- Decomposition balance threshold changed from 0.10 to 0.05 before any real use: on the real 2014 -> 2018 data
  (domain classifier only; no model predictions involved) the largest group-wise standardised mean difference is
  0.046-0.051 BEFORE reweighting, so a 0.10 rule could not fail. After reweighting it is 0.004-0.019, ESS 0.98.
  The output now also reports the before-reweighting values.
- P1 additionally reported without place of birth in the domain classifier: place of birth separates states almost
  by construction (rehearsal: geographic AUC about 0.9 with it, 0.65-0.71 without), which would make P1 nearly
  automatic.

## D025 - 2026-11-20 - Second pre-run audit (no changes to fitting or prediction code)
- Dictionaries 2017-2024: code sets and labels of COW, SCHL, MAR, SEX, RAC1P identical in every year (labels compared
  case-insensitively); POBP differs only by the three registered deletions (456 from 2022, 463 in 2024; 208 is
  absent from all CSV dictionaries); OCCP code lists identical 2018-2024, label prefixes identical apart from 1555 and
  8000 (missing in 2018 only, already handled); RELSHIPP present from 2019, RELP up to 2018; ST named STATE in
  2023-2024.
- Data 2014-2018 after harmonisation: no missing values in any harmonised feature; every COW, SCHL, MAR and POBP code
  is in the dictionary except POBP 208 (handled); RELP_H categories in 2014-2018 equal the RELSHIPP mapping's targets.
- Manuscript compiles without undefined references or citations (latexmk, TMLR style).
- Plan: secondary analyses stated as unweighted; exposure record lists the decomposition balance diagnostics and the
  synthetic-stand-in rehearsal. README status updated.

## D026 - 2026-11-20 - Independent QA round 2: dispositions and changes (before the Stage A rerun)
Report: docs/qa_independent_round_2_report.md; disposition: docs/qa_independent_round_2_disposition.md.
- R1 provenance: fit-specification hash per model (job, features, mapping, estimator hyperparameters, training-data
  hash, split and fitting code as AST hash, library versions), compared on resume together with the model-file hash;
  prediction-specification hash enforced on every prediction; load_pred checks the sidecar's model hash against the
  current manifest; preflight inventory checks in every prediction consumer; derived data bound to raw-file hashes
  and build code (2014-2018 files checked against logs/raw_sha256.txt).
- R2 person-level row identity (ST, SERIALNO, SPORDER); unique in 2014 and 2018; convention expected-v2.
- R3 decision: race stays an input of the primary models (fidelity to the original). The plan now states that the
  sex endpoints include any effect of the 2020 race-measurement change; new frozen no-race models (base and sex DP
  post-processing, seeds 0-4) and secondary analysis 8.10. Inventory: 98 models.
- R4 crosswalk derivation: codes with an unresolved destination are never moved (430, 3060, 3730, 9520 listed);
  the derived set is unchanged.
- A1 target (b) stated; joint simulation of calibration + baseline + later year with registered acceptance criteria.
- A2 split-variance calibration over 15 configurations, K = 400, upper 95% bound, maximum multiplier.
- A3 one estimate builder everywhere (8.3 and 8.6 now get the split multiplier); cross-table agreement checked.
- A4 balance with category indicators and a noise allowance (0.02 + 3 sqrt(1/ESS + 1/n)); clipping gate for
  accuracy and both EO gaps. Real 2014 -> 2018 (domain classifier on the 2014 seed-0 test split; clipping effects
  computed with the previous gbm_s0 predictions, which is allowed historical data): before reweighting the largest
  values are 0.039-0.046 against limits 0.027-0.039 (all four groups fail); after, 0.010-0.023 (all pass);
  clipping changes of the accuracy, EO and DP residuals are below 0.0003.
- A5 download checks take the format from the destination name; XLS by signature; synthetic fixtures.
- A6 metric-local failure handling; C7 input validation; tests (scripts/test_analysis.py, 12/12 pass).
- A7 provenance block in every result file; check_outputs re-runs the inventory check and rejects stale files.
- A8 P(false violated) <= alpha, not alpha/2 (docstring, plan, tests).
- A9 wording: disposition override, provenance table, manuscript (no certification claim), exposure record,
  C5 rationale; scripts/verify_archive.py.
- Rehearsal of the full chain with the final code in the sandbox: Stage A gate passes; Stage B gate passes apart
  from P1 (skipped for time; P1 run separately on 3 states).

## D027 - 2026-11-20 - Independent QA round 3: dispositions and changes (before the Stage A rerun)
Report: docs/qa_independent_round_3_report.md; disposition: docs/qa_independent_round_3_disposition.md.
- R3-1: semantic configuration serialised by value in both specifications (feature sets, group columns, label
  threshold and rule, race codes, pooling, GBM / post-processing / LFR settings, ExpGrad and DemographicParity
  library defaults, mapping); prediction code list extended (Scaler, pooling, data-to-design path). Settings moved to
  named module constants used by the code (GBM_PARAMS, POST_*, LFR_*). scripts/test_specs.py changes one setting at
  a time (9 settings) and checks that exactly the expected specifications change (all pass).
- R3-7: fitting split into a shared preparation and one function per model family; a family's fit specification
  hashes only the shared code and its own family code (test: replacing one family's function changes only that
  family's specification; gbm and no-race share _fit_gbm).
- R3-2: derived tables are used only with build provenance (raw-file hashes, build-code hash incl. column selection
  and types and pandas/pyarrow versions), checked on every load; legacy tables are refused. Both raw files required.
  Raw-hash log append-only (scripts/log_raw_hashes.sh). Rebuilding 2014-2018 with the current builder in the VM
  reproduced every table byte for byte (SHA-256 identical, pyarrow content equal), so the reconstruction and all
  earlier 2014-2018 analyses used the same tables. The Mac run rebuilds them first to write the provenance records;
  copies of the build records are committed in results/data_provenance/.
- A3-1: archive package built by scripts/verify_archive.py build (code, plan, results, logs, all model files);
  verify opens the package, hashes every member, requires the full inventory incl. every model file against the
  archived manifest, requires identical local copies, checks the Zenodo record and a manual Software Heritage check.
  scripts/test_archive.py (mocked record): incomplete package, altered model, wrong checksum, missing SWH check and
  changed local file all fail; complete package passes.
- A3-2: provenance records the SHA-256 of every consumed input (upstream results, split calibration, data tables,
  CPI); check_outputs reports a result stale when any input changed; test scripts record their own hash. Lineage
  regression test in test_specs.py.
- A3-3: the plan no longer claims error control conditional on the realised constants; the joint simulation is
  described as unconditional operating characteristics, now with negative and positive theta, a trend history,
  null-conditioned rates with denominators, Monte Carlo SEs, and the runner's seed-mean SE convention.
- A3-4: only a complete validation run writes the registered file; check_outputs recomputes every acceptance
  criterion from the detailed rows and requires complete case grids.
- A3-5: balance gate adds a support criterion (group ESS >= 50% of rows), caps the balance tolerance at 0.05 and
  gates each categorical feature's total-variation distance (0.05 + its expected value under sampling noise). Real
  2014 -> 2018: all groups fail before reweighting, pass after (ESS 97-98%, largest TVD 0.028 vs limit 0.070).
  Synthetic tests: concentrated weights and rare-category mass shift fail; balanced case passes.
- A3-6: split calibration uses the number of valid splits for each bound, requires >= 95% valid splits in every
  configuration and metric (else the step fails), and is described as approximate.
- Full rehearsal with the final code (sandbox; synthetic later years; 30 trees): Stage A gate passes except the
  split calibration, which correctly fails in the sandbox because a 60,000-row sample leaves some 20% splits of a
  middle state with no Black person above $50,000 (in the real 2018 data the smallest of the 20 states has 130 such
  persons, about 26 per split). Stage B gate passes apart from P1 (skipped for time).

## D028 - 2026-11-20 - Independent QA round 4 (report: docs/qa_independent_round_4_report.md)
- Verdict: no blocking defect in the fitted models or predictions; proceed with the rebuild and refit. Blocking
  before archive: A4-1 (archive verifier) and G4-1 (the full Stage A run must pass its gates).
- A4-1 fixed: build and verify share one inventory (all files under src, scripts, prereg, results, docs, logs,
  paper, incl. shell scripts; lock and project files; every model file); verify requires every inventory member in
  the package with bytes identical to the local file. test_archive.py: 9 cases, incl. changed Python source,
  changed shell script and a package without a shell script (receipt and record matching it), all fail as required.
- A4-3 fixed: the gate checks the exact registered coordinates of every validation grid (each once), not counts.
- A4-2 recorded: the joint simulation's SE is an annual-SE proxy for the runner's seed aggregation; wording in the
  plan and the script changed; no claim of conservatism.
- R4-1 recorded as a limitation: semantic settings are global, so a family-local setting change would also mark
  other families for refitting (safe over-invalidation).
- validate_inference.py changed in a docstring only, before the run.
