"""Study files: loading, hashing the preregistered sections, and lint."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from pathlib import Path

import yaml

FROZEN_KEYS = ["theory", "alternatives", "predictions", "analysis_plan", "kill_rule"]
POST_DATA_PREDICTION_KEYS = {"outcome", "evidence"}
OUTCOMES = {"pass", "fail", "inconclusive"}
WEAK_LR = 3.0


class StudyError(Exception):
    pass


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def find_root(start: Path | None = None) -> Path:
    p = (start or Path.cwd()).resolve()
    for q in [p, *p.parents]:
        if (q / "studies").is_dir() or (q / ".git").is_dir():
            return q
    return p


def studies_dir(root: Path) -> Path:
    return root / "studies"


def study_dir(slug: str, root: Path) -> Path:
    d = studies_dir(root) / slug
    if not (d / "study.yaml").exists():
        raise StudyError(f"no study at {d}")
    return d


def load_yaml(path: Path) -> dict:
    with open(path) as fh:
        return yaml.safe_load(fh) or {}


def save_yaml(path: Path, data: dict) -> None:
    with open(path, "w") as fh:
        yaml.safe_dump(data, fh, sort_keys=False, allow_unicode=True)


def frozen_payload(study: dict) -> dict:
    out = {}
    for k in FROZEN_KEYS:
        v = study.get(k)
        if k == "predictions" and v:
            v = [{kk: vv for kk, vv in p.items() if kk not in POST_DATA_PREDICTION_KEYS} for p in v]
        out[k] = v
    return out


def frozen_hash(study: dict) -> str:
    blob = json.dumps(frozen_payload(study), sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()


def _ratio(num: float, den: float) -> float:
    num, den = max(num, 0.0), max(den, 0.0)
    if den <= 1e-12:
        return 1.0 if num <= 1e-12 else float("inf")
    return num / den


def likelihood_ratios(pred: dict) -> tuple[float, float, float, str]:
    """(LR if pass, LR if fail, LR if inconclusive, mode).

    mode is 'three-outcome' when P(fail | .) is given for both hypotheses, so that
    inconclusive is the remainder and gets its own ratio. Otherwise mode is 'legacy':
    a failure is scored by the binary complement (1 - P(pass | .)) and inconclusive is
    left neutral at LR 1. That is not a coherent three-outcome likelihood and not a
    literal pooling of fail and inconclusive; it is kept for old study files only."""
    a, b = float(pred["p_pass_if_true"]), float(pred["p_pass_if_false"])
    lr_pass = _ratio(a, b)
    if pred.get("p_fail_if_true") is None or pred.get("p_fail_if_false") is None:
        return lr_pass, _ratio(1 - a, 1 - b), 1.0, "legacy"
    ft, fr = float(pred["p_fail_if_true"]), float(pred["p_fail_if_false"])
    return lr_pass, _ratio(ft, fr), _ratio(1 - a - ft, 1 - b - fr), "three-outcome"


def _text(x) -> str:
    return (x or "").strip() if isinstance(x, str) else ""


def _has_number(s: str) -> bool:
    return bool(re.search(r"\d", s))


def lint(study: dict, slug: str | None = None, frozen: bool = False) -> tuple[list[str], list[str]]:
    """Returns (errors, warnings). Errors block freezing."""
    E, W = [], []
    if slug and study.get("slug") != slug:
        E.append(f"slug in file ({study.get('slug')!r}) does not match directory ({slug!r})")
    th = study.get("theory") or {}
    if not _text(th.get("statement")):
        E.append("theory.statement is empty")
    if not _text(th.get("scope")):
        E.append("theory.scope is empty: say which systems the claim is about")
    try:
        pc = float(th.get("prior_credence"))
        if not 0 < pc < 1:
            E.append("theory.prior_credence must be strictly between 0 and 1")
        elif pc > 0.9 or pc < 0.05:
            W.append(f"theory.prior_credence {pc} is extreme; is a test even needed?")
    except (TypeError, ValueError):
        E.append("theory.prior_credence missing or not a number")
    version = th.get("version", 1)
    if isinstance(version, int) and version > 1 and not th.get("supersedes"):
        E.append("theory.version > 1 requires theory.supersedes (name@version of the refuted parent)")

    alts = study.get("alternatives") or []
    if not alts or not any(_text(a.get("statement")) for a in alts):
        E.append("at least one alternative hypothesis with a statement is required")
    alt_ids = {a.get("id") for a in alts}

    preds = study.get("predictions") or []
    if not preds:
        E.append("no predictions")
    ids, n_critical = set(), 0
    for p in preds:
        pid = p.get("id", "?")
        if pid in ids:
            E.append(f"duplicate prediction id {pid}")
        ids.add(pid)
        if not _text(p.get("statement")):
            E.append(f"{pid}: statement is empty")
        for k in ("pass_if", "fail_if"):
            t = _text(p.get(k))
            if not t:
                E.append(f"{pid}: {k} is empty; a prediction without a criterion is not a prediction")
            elif not _has_number(t):
                W.append(f"{pid}: {k} has no number in it; is it operational?")
        try:
            a, b = float(p.get("p_pass_if_true")), float(p.get("p_pass_if_false"))
            if not (0 <= a <= 1 and 0 <= b <= 1):
                E.append(f"{pid}: likelihoods must be in [0, 1]")
            elif a <= b:
                E.append(f"{pid}: p_pass_if_true ({a}) must exceed p_pass_if_false ({b}); otherwise a pass is not evidence")
            elif a / max(b, 1e-9) < WEAK_LR - 1e-9:
                W.append(f"{pid}: likelihood ratio {a / max(b, 1e-9):.1f} is below {WEAK_LR}; this is a weak test")
            if a in (0.0, 1.0) or b in (0.0, 1.0):
                E.append(f"{pid}: a forecast of exactly 0 or 1 is not a forecast and makes the score degenerate; use 0.01 or 0.99")
            ft, fr = p.get("p_fail_if_true"), p.get("p_fail_if_false")
            if ft is None or fr is None:
                W.append(f"{pid}: no P(fail | .) given; legacy mode scores a failure by the binary complement and "
                         f"leaves inconclusive neutral. Not a coherent three-outcome likelihood; give P(fail | .) for new studies")
            else:
                ft, fr = float(ft), float(fr)
                if not (0 <= ft <= 1 and 0 <= fr <= 1):
                    E.append(f"{pid}: P(fail | .) must be in [0, 1]")
                elif ft in (0.0, 1.0) or fr in (0.0, 1.0):
                    E.append(f"{pid}: a forecast of exactly 0 or 1 is not a forecast and makes the score degenerate; use 0.01 or 0.99")
                elif a + ft > 1 - 1e-9 or b + fr > 1 - 1e-9:
                    E.append(f"{pid}: P(pass) + P(fail) leaves no probability for inconclusive under one hypothesis; "
                             f"if an outcome is impossible, say so in pass_if / fail_if and keep the forecasts interior")
        except (TypeError, ValueError):
            E.append(f"{pid}: p_pass_if_true and p_pass_if_false are required")
        if p.get("critical"):
            n_critical += 1
        for d in p.get("discriminates") or []:
            if d not in alt_ids:
                W.append(f"{pid}: discriminates {d!r} which is not a listed alternative")
        o = p.get("outcome")
        if o is not None and o not in OUTCOMES:
            E.append(f"{pid}: outcome must be one of {sorted(OUTCOMES)}")
        if o is not None and not frozen:
            msg = f"{pid}: outcome recorded but the study was never frozen; this is exploratory, not a result"
            (W if study.get("exploratory") else E).append(msg)
    if preds and n_critical == 0:
        E.append("no prediction is marked critical; nothing could refute this theory")
    if not _text(study.get("analysis_plan")):
        E.append("analysis_plan is empty")
    elif "seed" not in _text(study.get("analysis_plan")).lower():
        W.append("analysis_plan does not mention seeds")
    if not _text(study.get("kill_rule")):
        E.append("kill_rule is empty: decide now what would make you abandon this")
    return E, W
