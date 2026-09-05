# Working in a repository that uses sever

This repository runs research under the method in METHOD.md. When you work on a study here, these rules apply to you.

## Before touching a study

- Run `sever status`. Know whether the study is draft, frozen, or concluded.
- If it is frozen, run `sever check <slug>` before writing anything. If the check fails, stop and say so.

## Writing a study

- Every prediction gets `pass_if` and `fail_if` with numbers, a `critical` flag, and both likelihoods. If you cannot write a number, the prediction is not ready.
- List at least one rival that would produce similar data. Say which rivals each prediction discriminates.
- Separate in `theory.formal` what the math entails from what is conjecture. Predictions the math entails are tests of the code, not the theory. Do not count them as evidence.
- The analysis plan names parameters, seeds, sample sizes, horizons, and the statistic. Do not leave any of these to be chosen later.
- Write the kill rule before the data. It states what refutes this version and what a revision must add.
- Give P(fail | .) as well as P(pass | .). Treat all of them as forecasts, not measured likelihoods, and never present the updated credence as odds to bet at.
- Run a design pilot on excluded data or simulation before the freeze. If the estimator cannot resolve the predicted effect, fix the design, not the numbers.

## After the freeze

- Never edit `theory`, `alternatives`, `predictions` (other than `outcome` and `evidence`), `analysis_plan`, or `kill_rule`. If the user asks to change one, explain that this creates a new version and scaffold it with `sever new`.
- Fill each `outcome` by applying `pass_if` and `fail_if` literally. If the criterion does not settle the case, the outcome is `inconclusive`, and the ambiguity is a lint finding for the next version. Do not resolve ambiguity in the theory's favour.
- Findings that were not predicted go under `results.exploratory` with a proposed next test. They are hypotheses, not results, and are not evidence for the theory.
- Report effect sizes with the numbers. Direction alone is not a result. Report the robustness checks the plan named.
- Write `review` as the sharpest critic. Name the confounds you did not check.
- Run `sever verdict` and accept its output. Do not argue with a refutation in the summary.

## Reporting to the user

- Lead with the verdict-relevant fact, especially when it goes against the theory. Say "the critical prediction failed" in the first sentence, not the fourth.
- Never reframe a failure as partial support. Never raise a prior after the fact, never change a likelihood after an outcome is known.
- Use the vocabulary: supported, refuted, mixed, inconclusive. Not proven, confirmed, validated, or "shows".
- Reproduce before you report. If the one command does not rerun cleanly, say that first.
