"""Mechanical verdict from recorded outcomes. The theory does not get a vote."""
from __future__ import annotations

import math

from .study import OUTCOMES, WEAK_LR, likelihood_ratios, now_iso

STATUS_TEXT = {
    "refuted": "REFUTED. A critical prediction failed. This version is abandoned. The kill rule applies.",
    "supported": "SUPPORTED, not proven. Every prediction passed. Next: a more severe test, or a system outside the current scope.",
    "supported-weakly": "SUPPORTED WEAKLY. Every critical prediction passed, but no passing test had a likelihood ratio of 3 or more. This is a demonstration, not evidence. Design a test that could have failed.",
    "mixed": "MIXED. Critical predictions passed; at least one non-critical prediction failed or is unresolved. The theory survives; the failures are anomalies and the unresolved ones stay open, and both carry into the next version.",
    "inconclusive": "INCONCLUSIVE. A critical prediction was neither passed nor failed. Fix the design, not the theory.",
    "incomplete": "INCOMPLETE. Some predictions have no outcome. Fill them in by applying pass_if / fail_if literally.",
}


def compute(study: dict) -> dict:
    preds = study.get("predictions") or []
    prior = float(study["theory"]["prior_credence"])
    odds = prior / (1 - prior)
    log10_evidence = 0.0
    rows, missing = [], []
    crit_fail = crit_incl = noncrit_fail = noncrit_incl = 0
    modes = set()
    for p in preds:
        o = p.get("outcome")
        if o is None:
            missing.append(p["id"])
            continue
        if o not in OUTCOMES:
            raise ValueError(f"{p['id']}: bad outcome {o!r}")
        lr_pass, lr_fail, lr_inc, mode = likelihood_ratios(p)
        modes.add(mode)
        lr = {"pass": lr_pass, "fail": lr_fail, "inconclusive": lr_inc}[o]
        if math.isfinite(lr) and lr > 0:
            odds *= lr
            log10_evidence += math.log10(lr)
        elif lr == 0:
            odds = 0.0
        critical = bool(p.get("critical"))
        rows.append({"id": p["id"], "critical": critical, "outcome": o,
                     "likelihood_ratio": round(lr, 3) if math.isfinite(lr) else "inf",
                     "mode": mode, "weak_test": lr_pass < WEAK_LR - 1e-9})
        if critical and o == "fail":
            crit_fail += 1
        elif critical and o == "inconclusive":
            crit_incl += 1
        elif not critical and o == "fail":
            noncrit_fail += 1
        elif not critical and o == "inconclusive":
            noncrit_incl += 1
    if missing:
        status = "incomplete"
    elif crit_fail:
        status = "refuted"
    elif crit_incl:
        status = "inconclusive"
    elif noncrit_fail or noncrit_incl:
        status = "mixed"
    else:
        status = "supported"
        passes = [r for r in rows if r["outcome"] == "pass"]
        if passes and all(r["weak_test"] for r in passes):
            status = "supported-weakly"
    posterior = odds / (1 + odds) if math.isfinite(odds) else 1.0
    return {
        "status": status,
        "prior_credence": prior,
        "posterior_credence": round(posterior, 4),
        "log10_evidence": round(log10_evidence, 3),
        "likelihood_mode": "binary" if "binary" in modes else "three-outcome",
        "predictions": rows,
        "missing": missing,
        "computed_at": now_iso(),
    }


def report(study: dict, v: dict, exploratory: bool = False) -> str:
    th = study["theory"]
    lines = [f"{th.get('name')} v{th.get('version', 1)}: {v['status'].upper()}"
             + ("  [EXPLORATORY: preregistration not intact; excluded from calibration]" if exploratory else "")]
    lines.append(STATUS_TEXT[v["status"]])
    lines.append(f"forecast bookkeeping, heuristic and not a calibrated posterior: credence "
                 f"{v['prior_credence']:.2f} -> {v['posterior_credence']:.2f}   "
                 f"(log10 score {v['log10_evidence']:+.2f}; ratios multiplied as if independent"
                 + ("; binary mode on some predictions, fail and inconclusive pooled as not-pass)"
                    if v.get("likelihood_mode") == "binary" else ")"))
    for r in v["predictions"]:
        flag = " critical" if r["critical"] else ""
        weak = "  weak test" if r["weak_test"] else ""
        lines.append(f"  {r['id']:<6} {r['outcome']:<13} LR {r['likelihood_ratio']}{flag}{weak}")
    if v["missing"]:
        lines.append("  missing outcomes: " + ", ".join(v["missing"]))
    if v["status"] == "refuted":
        lines.append("kill rule:\n  " + (study.get("kill_rule") or "").strip().replace("\n", "\n  "))
        lines.append("A revision is a new study with theory.version + 1 and theory.supersedes set. "
                     "It must contain at least one prediction that the data which killed this version do not already entail.")
    if v["status"] == "mixed":
        failed = [r["id"] for r in v["predictions"] if r["outcome"] == "fail"]
        open_ = [r["id"] for r in v["predictions"] if r["outcome"] == "inconclusive"]
        if failed:
            lines.append("anomalies (failed) to carry forward: " + ", ".join(failed))
        if open_:
            lines.append("open (inconclusive) to carry forward: " + ", ".join(open_))
    return "\n".join(lines)
