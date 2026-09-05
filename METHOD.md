# The method

## The one rule

The theory does not get a vote on the evidence. Predictions are written down with numbers before any data exist. Outcomes are read off by applying those numbers literally. The verdict is computed, not argued. If a critical prediction fails, the version is dead, and the only way forward is a new version that risks something new.

Everything else here is scaffolding to make that rule survivable. The failure mode is never "we saw the data and lied". It is "we saw the data and then remembered what we had really meant".

## Principles

Each principle has a source. None of this is new. The contribution is making it mechanical.

**1. Several hypotheses, never one.** (Chamberlin, 1890.) A study lists at least one rival that would produce similar-looking data. Each prediction says which rivals a pass counts against. A theory with no rivals cannot be tested, only illustrated.

**2. A prediction counts only if it can fail.** (Popper, 1934.) "The optimum will be somewhere in the middle" is not a prediction. "The optimum will lie within a factor of 1.4 of the susceptibility peak, for every ruggedness tested" is. Every prediction has a pass criterion and a fail criterion with numbers in them. Anything outside both is inconclusive, and inconclusive is not a soft pass.

**3. A pass is evidence in proportion to how likely it was to fail.** (Mayo, 2018.) Before data, write P(pass | theory) and P(pass | best rival). Their ratio is the weight of a pass. A ratio under 3 is a demonstration, not a test, and the tooling says so. A theory supported only by demonstrations is marked as weakly supported.

**4. Design to exclude, not to confirm.** (Platt, 1964.) The best experiment is the one whose outcomes split the rivals. For each prediction, ask which rival dies if it passes and which dies if it fails. A prediction that every rival makes equally is a test of the code, not of the theory. Mark those honestly in `theory.formal`.

**5. Freeze before you look.** (Nosek et al., 2018.) The theory, rivals, predictions, analysis plan and kill rule are hashed and tied to a git commit before any data exist. After the freeze those sections cannot change. The tooling checks the hash against the working copy and against the named commit. Anything decided after data is exploratory. Exploratory work is where ideas come from and is welcome. It is recorded as hypotheses for the next study, never as results of this one.

**6. The analysis plan is part of the prediction.** (Gelman and Loken, 2014.) Parameters, seeds, sample sizes, horizons, the statistic, the nuisance parameters varied, the effect sizes reported. A choice made while looking at the data is not a choice. It is a fit.

**7. A refuted theory is not patched.** (Lakatos, 1970.) A revision is a new version that names what it supersedes and makes at least one new prediction that the killing data do not already entail. If the only thing the new version predicts is the data that killed the old one, the programme is degenerating and the revision goes to the graveyard with its parent.

**8. Keep the books.** A prior credence before, an updated credence after, computed from forecasts written before the data. These are forecasts, not measured likelihoods, and the update is a heuristic score. Across studies, calibration is scored (Brier, 1950). Persistent overconfidence is a finding about the researcher and is corrected like any other finding: lower the priors, raise the bar.

**9. Effect sizes and robustness, not direction.** A difference that vanishes when the seed, the population size or the horizon changes is not a difference. Finite-size and nuisance-parameter checks come before any sentence that starts with "the system".

**10. Try to kill it before you announce it.** The adversarial review is written by the same people, in the voice of the sharpest critic, before the verdict. It names the strongest objection, the confounds checked and the ones not checked, and what would change your mind. The tooling refuses to compute a verdict without it.

**11. Claims are indexed to scope.** "In this model" until shown in another. A universality claim needs more than one system and a scaling or collapse argument. An analogy is a research direction, not a result.

**12. One command reproduces everything.** Pinned dependencies, fixed seeds, results committed alongside the commit hash that produced them. If it cannot be rerun, it did not happen.

## Lifecycle

0. **Idea.** One sentence in the notebook.
1. **Literature.** Search before building. If it exists, this study is a replication or an extension and says so in the title.
2. **Theory.** One paragraph, falsifiable, with a scope. Formalise where you can. Separate what the math entails from what you are conjecturing.
3. **Rivals.** At least one.
4. **Predictions.** Each with `pass_if`, `fail_if`, `critical`, and the two likelihoods.
5. **Plan and kill rule.** What will be computed, and what would make you stop.
6. **Design pilot, then freeze.** Show on excluded data or simulation that the design can resolve the prediction. Then `sever lint`, commit, `sever freeze`, commit.
7. **Run.** Do not touch the frozen sections. Record each outcome by applying its criteria literally, with a pointer to the evidence.
8. **Review.** Write the case against.
9. **Verdict.** `sever verdict`. Accept the output.
10. **Next.** Supported: a more severe test, or a system outside scope. Refuted: graveyard, and a new version only if it risks something new. Mixed: the anomalies become the next version's predictions. Inconclusive: fix the design, not the theory.

## Vocabulary

Supported, refuted, mixed, inconclusive. Never proven, confirmed, validated, or "shows". "Consistent with" is allowed only with the likelihood ratio next to it.

## How the verdict is computed

Each prediction carries forecasts written before data: P(pass | theory), P(pass | best rival), P(fail | theory), and P(fail | best rival). Inconclusive is the remainder under each hypothesis. Each recorded outcome multiplies the odds on the theory by the ratio of its probabilities under the two hypotheses. This is the three-outcome mode, and new confirmatory studies use it or omit numerical evidence accumulation altogether. If only the pass probabilities are given, the tool runs in legacy mode: a failure is scored by the binary complement and inconclusive is left neutral. That is not a coherent three-outcome likelihood and not a literal pooling of fail and inconclusive; it exists for old study files and the report labels it. Forecasts of exactly 0 or 1 are rejected by lint, because they are not forecasts and they make the score degenerate.

The resulting number is bookkeeping, not a calibrated posterior. The forecasts are subjective, the rivals are usually narrative rather than predictive distributions, and the ratios are multiplied as if the predictions were independent. Record the forecasts, score them for calibration across studies, and do not present them as measured evidential likelihoods or as odds to bet at. The status is decided by rules, not by the number:

| status | rule |
|---|---|
| refuted | any critical prediction failed |
| inconclusive | no critical failure, but a critical prediction was inconclusive |
| mixed | every critical prediction passed, and at least one non-critical prediction failed or was inconclusive; both are listed and carry forward |
| supported | every prediction passed |
| supported-weakly | every prediction passed, but every passing test had a likelihood ratio under 3 |
| incomplete | some outcome is not recorded |

A critical failure refutes the specified bundle of theory, model, and analysis assumptions. It does not refute a mathematical identity the theory used; identities are proved, not tested.

## Design before freeze

A frozen prediction is only as good as the design behind it. Before freezing, run a design pilot on excluded data or on simulation under the theory and under the main rival: check that the estimator can resolve the predicted effect, that the intervals have the coverage you claim, and that the pass and fail criteria are reachable under each hypothesis. A useful target is a high chance of a decisive outcome under the theory and a low chance under a meaningfully different rival. Record the pilot in the notebook. A study that skips this can pass or fail for reasons that have nothing to do with the theory, and the second study in the worked example did exactly that.

## Worked example

The first study run under this method asked whether, in a population of innovating agents, collective performance peaks at the phase transition of the population's diversity. The theory made one critical prediction: the performance optimum and the susceptibility peak coincide within a factor of 1.4. They did not. The optimum sat at about twice the transition for every ruggedness tested, and the gap did not shrink with population size. That version was refuted and is in the graveyard. Because its criteria were written after the data, it is marked exploratory and its verdict does not count toward calibration.

The successor said the optimum sits inside the connected phase at a location set by the ratio of information spread rate to local search rate, and earned its place by predicting something the first study's data did not contain: that the optimum moves when local search speed changes. That prediction was frozen, then run. The interior optimum replicated in a new topology, and the critical prediction came back inconclusive, because performance sits on a plateau two decades wide and the estimator could not locate the optimum within an order of magnitude. The verdict is inconclusive, the theory is untested on its central claim, and the next version is a design fix, not a theory change. The adversarial review says which fix: more resolution, an estimator that fits a curve instead of taking an argmax, and a spread rate measured before convergence. One exploratory finding runs against the formal model and becomes a preregistered prediction next time.

Three things the method did there that a notebook would not have: it refused to let a pass on the weakest prediction count as support, it made the design failure visible as a failure rather than as a soft result, and it put the theory's own prediction on record before the data could suggest a friendlier one.

## Sources

- Chamberlin, T. C. (1890). The method of multiple working hypotheses. Science.
- Popper, K. (1934). Logik der Forschung. English: The Logic of Scientific Discovery (1959).
- Platt, J. R. (1964). Strong inference. Science.
- Lakatos, I. (1970). Falsification and the methodology of scientific research programmes.
- Brier, G. W. (1950). Verification of forecasts expressed in terms of probability. Monthly Weather Review.
- Gelman, A. and Loken, E. (2014). The statistical crisis in science. American Scientist.
- Nosek, B. A. et al. (2018). The preregistration revolution. PNAS.
- Mayo, D. G. (2018). Statistical Inference as Severe Testing. Cambridge University Press.
