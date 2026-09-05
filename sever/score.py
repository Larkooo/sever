"""Calibration across studies. Predicted probability of a pass, under the study's own stated
beliefs, is prior * P(pass|true) + (1 - prior) * P(pass|false). Scored against what happened."""
from __future__ import annotations

from pathlib import Path

from .study import load_yaml, studies_dir


def collect(root: Path) -> list[dict]:
    rows = []
    for d in sorted(studies_dir(root).glob("*/")):
        sf, vf = d / "study.yaml", d / "verdict.yaml"
        if not sf.exists() or not vf.exists():
            continue
        study, verdict = load_yaml(sf), load_yaml(vf)
        if verdict.get("exploratory"):
            continue
        prior = float(study["theory"]["prior_credence"])
        for p in study.get("predictions") or []:
            o = p.get("outcome")
            if o not in ("pass", "fail"):
                continue
            a, b = float(p["p_pass_if_true"]), float(p["p_pass_if_false"])
            rows.append({"study": d.name, "id": p["id"], "predicted": prior * a + (1 - prior) * b,
                         "observed": 1.0 if o == "pass" else 0.0})
    return rows


def brier(rows: list[dict]) -> dict:
    if not rows:
        return {"n": 0}
    n = len(rows)
    bs = sum((r["predicted"] - r["observed"]) ** 2 for r in rows) / n
    mean_pred = sum(r["predicted"] for r in rows) / n
    mean_obs = sum(r["observed"] for r in rows) / n
    return {"n": n, "brier": round(bs, 4), "baseline_always_half": 0.25,
            "mean_predicted_pass": round(mean_pred, 3), "observed_pass_rate": round(mean_obs, 3),
            "overconfidence": round(mean_pred - mean_obs, 3)}


def report(root: Path) -> str:
    rows = collect(root)
    s = brier(rows)
    if s["n"] == 0:
        return "no scored predictions yet (a prediction is scored once its study has a non-exploratory verdict)"
    lines = [f"{s['n']} scored predictions across concluded studies",
             f"Brier score {s['brier']}  (0 is perfect, 0.25 is coin-flipping, lower is better)",
             f"mean predicted pass probability {s['mean_predicted_pass']}, observed pass rate {s['observed_pass_rate']}",
             f"overconfidence {s['overconfidence']:+.3f}  (positive: you expected more passes than you got)"]
    return "\n".join(lines)
