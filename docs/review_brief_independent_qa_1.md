# Independent QA brief (first review) — 19 November 2026

You are reviewing a research project you have not seen before. Another AI did the work so far, with a single human
researcher directing and checking it. Your job is an **independent, critical quality review of everything in the
project**. Form your own view from the materials and the primary sources. Do not assume that anything in the
project is correct because it is written down, logged or tested.

## The project in one paragraph
A planned, pre-registered study re-testing one published claim: Ding, Hardt, Miller and Schmidt, *Retiring Adult:
New Datasets for Fair Machine Learning* (NeurIPS 2021; arXiv:2108.04884), Section 4.1 and Appendix D.3, about how
stable fairness measures of a classifier are over time on US Census (ACS) data. The intended venue is TMLR. The goal
is a paper that is correct, defensible and as strong as possible.

## Where things are
The project folder (also public at https://github.com/iamalif/re-test-temporal-fairness-stability). Start with
`README.md`. Everything else is reachable from there: the plan in `prereg/`, the decision log in `logs/`, code in
`src/` and `scripts/`, results in `results/`, the paper draft in `paper/`, the original brief and earlier review
material in `docs/`. Third-party papers are in `docs/sources/` (local only). Read the anchor paper itself, not only
the project's description of it.

## Rules
1. **Do not open, compute on, or report any ACS person-level data, or any published result, for survey years 2019 or
   later.** The study's plan depends on nobody having seen them. If you encounter such a result by accident, say so
   and do not repeat it.
2. **Do not change anything in the project folder.** If you want to run code, work on a copy. A model-fitting job may
   be running in the folder; do not start heavy computations there and do not touch `data/derived/`.
3. Verify claims against primary sources (the anchor paper and its supplement, Census documentation, library source
   code, cited papers) wherever you can, and say when you could not.
4. You may disagree with any decision, including ones the log presents as settled.

## What to review
Cover the whole project. At a minimum, form an independent judgement on each of these areas; how you approach them
is up to you.
- **Research question and novelty**: is the study worth doing as framed, and is the prior-work assessment sound?
- **Fidelity to the claim**: does the study test what the anchor paper actually claims?
- **Reconstruction of the original results** (2014–2018): methods, evidence, and whether the conclusions drawn from
  it are justified.
- **Data handling**: sources, filters, harmonisation across years, anything that changes between survey years.
- **Models and interventions**: specification and implementation.
- **Pre-registration**: hypotheses, estimands, margins, decision rules, multiplicity, weighting, secondary analyses,
  exposure record, deviations policy. Would it withstand a sceptical reviewer?
- **Statistics**: estimators, standard errors, intervals, tests, power.
- **Code**: correctness, and whether the code does exactly what the plan and paper say.
- **Reproducibility and research hygiene**: environment, hashes, logs, guards, ability to rebuild from raw data.
- **Paper draft**: accuracy of every statement, framing, citations, anything a TMLR reviewer would object to.
- **Anything else** you think matters, including problems nobody has thought of.

## Output
1. A numbered list of findings, most severe first. For each: where (file and line, or section), what is wrong or
   doubtful, why it matters, the evidence (with sources), and a concrete fix. Classify each as **critical** (would
   invalidate results or the plan), **major** (a strong reviewer would demand it), **minor**, or **question**
   (you could not decide; say what would settle it).
2. A list of things you checked and found correct, briefly, so the coverage of your review is visible.
3. A short overall judgement: is the plan ready to be archived, and what must happen first?

Be specific and blunt. Do not soften findings, and do not pad the list.
