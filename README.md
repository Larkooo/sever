# sever

Severe testing for research programmes. A theory earns belief only by surviving tests that could have killed it. `sever` makes the bookkeeping mechanical: predictions with numeric criteria are frozen to a git commit before any data exist, outcomes are recorded against those criteria, the verdict is computed rather than argued, refuted theories go to a graveyard, and your stated credences are scored for calibration over time.

[METHOD.md](METHOD.md) is the method. This file is how to use the tool. [CLAUDE.md](CLAUDE.md) is the instruction set for an AI assistant working in a repository that uses it.

## Install

```
uv tool install git+https://github.com/Larkooo/sever
```

or, inside a project:

```
uv add --dev git+https://github.com/Larkooo/sever
```

## Quick start

```
sever new my-theory                  # studies/my-theory/study.yaml and notes.md
#   fill in: theory, at least one rival, predictions with numbers, analysis plan, kill rule
sever lint my-theory                 # missing criteria, weak tests, extreme priors
git add -A && git commit -m "prereg: my-theory"
sever freeze my-theory               # ties the frozen sections to that commit
git add -A && git commit -m "freeze: my-theory"
#   run the experiment. Fill outcome and evidence on each prediction. Write results and the review.
sever check my-theory                # is the preregistration intact?
sever verdict my-theory              # supported, refuted, mixed, inconclusive
sever status                         # every study at a glance
sever score                          # calibration of your stated credences
sever graveyard                      # what died, what killed it, what replaced it
```

## Commands

| command | what it does |
|---|---|
| `new <slug>` | scaffold `studies/<slug>/` from the template |
| `lint [slug]` | errors block freezing: empty criteria, no rival, no critical prediction, likelihoods that make a pass uninformative. Warnings: criteria without numbers, weak tests, extreme priors |
| `freeze <slug>` | record the commit and the hash of the frozen sections. Refuses uncommitted changes, recorded outcomes, or lint errors |
| `check <slug>` | verify the working copy and the named commit both hash to the frozen value |
| `verdict <slug>` | compute status and a heuristic credence update from recorded outcomes. Refuses a broken freeze (unless `--exploratory`) and refuses an empty adversarial review |
| `status` | table of studies, state, outcomes recorded |
| `score` | Brier score of predicted pass probabilities against observed outcomes across concluded studies |
| `graveyard` | refuted theories, the predictions that killed them, and their successors |

## Layout

```
studies/<slug>/study.yaml     written by you. Frozen sections, then outcomes, results, review
studies/<slug>/freeze.yaml    written by `sever freeze`
studies/<slug>/verdict.yaml   written by `sever verdict`
studies/<slug>/notes.md       lab notebook, dated entries
```

Only `outcome` and `evidence` on each prediction, plus everything under `results:` and `review:`, may change after the freeze.

Give both P(pass | .) and P(fail | .) on every prediction. Without P(fail | .) the tool runs in a labelled legacy mode that is not a coherent three-outcome likelihood.

A study can declare `exploratory: true` at the top. Use it for a post-hoc registration, when the criteria were written after the data existed. Lint then allows outcomes without a freeze, `verdict` records the result, and `score` ignores it. The graveyard still lists it, tagged.

## What the tool refuses to do

- freeze a study with uncommitted changes, recorded outcomes, or lint errors
- compute a verdict when a frozen section changed, unless you pass `--exploratory`, which excludes the study from calibration
- compute a verdict without an adversarial review
- treat a critical failure as anything other than refutation

## Development

```
uv sync
uv run pytest
```
