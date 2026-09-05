from sever.verdict import compute


def base(**over):
    s = {"theory": {"name": "t", "version": 1, "prior_credence": 0.4},
         "predictions": [
             {"id": "P1", "critical": True, "p_pass_if_true": 0.8, "p_pass_if_false": 0.2, "outcome": "pass"},
             {"id": "P2", "critical": False, "p_pass_if_true": 0.7, "p_pass_if_false": 0.5, "outcome": "pass"},
         ]}
    s.update(over)
    return s


def test_supported_updates_credence():
    v = compute(base())
    assert v["status"] == "supported"
    odds = (0.4 / 0.6) * 4 * 1.4
    assert abs(v["posterior_credence"] - odds / (1 + odds)) < 1e-3


def test_critical_fail_refutes_regardless_of_other_passes():
    s = base()
    s["predictions"][0]["outcome"] = "fail"
    v = compute(s)
    assert v["status"] == "refuted"
    assert v["posterior_credence"] < 0.4


def test_noncritical_fail_is_mixed():
    s = base()
    s["predictions"][1]["outcome"] = "fail"
    assert compute(s)["status"] == "mixed"


def test_noncritical_inconclusive_is_mixed_not_supported():
    s = base()
    s["predictions"][1]["outcome"] = "inconclusive"
    assert compute(s)["status"] == "mixed"


def test_three_outcome_likelihoods_do_not_reverse_evidence():
    # Codex's example: (pass, fail, inc) = (0.80, 0.15, 0.05) under H and (0.20, 0.05, 0.75) under R.
    from sever.study import likelihood_ratios
    pred = {"p_pass_if_true": 0.8, "p_pass_if_false": 0.2, "p_fail_if_true": 0.15, "p_fail_if_false": 0.05}
    lr_pass, lr_fail, lr_inc, mode = likelihood_ratios(pred)
    assert mode == "three-outcome"
    assert abs(lr_pass - 4.0) < 1e-9
    assert abs(lr_fail - 3.0) < 1e-9          # binary mode would have given 0.25
    assert abs(lr_inc - 0.05 / 0.75) < 1e-9
    binary = likelihood_ratios({"p_pass_if_true": 0.8, "p_pass_if_false": 0.2})
    assert binary[3] == "legacy" and abs(binary[1] - 0.25) < 1e-9 and binary[2] == 1.0


def test_critical_inconclusive():
    s = base()
    s["predictions"][0]["outcome"] = "inconclusive"
    assert compute(s)["status"] == "inconclusive"


def test_missing_outcome_is_incomplete():
    s = base()
    s["predictions"][1]["outcome"] = None
    v = compute(s)
    assert v["status"] == "incomplete" and v["missing"] == ["P2"]


def test_only_weak_passes_is_weak_support():
    s = base()
    s["predictions"][0]["p_pass_if_true"], s["predictions"][0]["p_pass_if_false"] = 0.6, 0.4
    assert compute(s)["status"] == "supported-weakly"


def test_infinite_ratio_is_not_skipped():
    s = base()
    s["predictions"][0]["p_pass_if_false"] = 0.0  # bypasses lint on purpose
    v = compute(s)
    assert v["posterior_credence"] == 1.0
    assert v["boundary_inputs"] == ["P1"]


def test_boundary_forecasts_are_lint_errors():
    from sever.study import lint
    study = {"slug": "s", "theory": {"statement": "x", "scope": "y", "prior_credence": 0.4},
             "alternatives": [{"id": "H0", "statement": "z"}],
             "predictions": [{"id": "P1", "statement": "s", "critical": True, "pass_if": "r < 1", "fail_if": "r > 2",
                              "p_pass_if_true": 1.0, "p_pass_if_false": 0.2, "p_fail_if_true": 0.0, "p_fail_if_false": 0.5}],
             "analysis_plan": "seeds fixed", "kill_rule": "k"}
    errors, _ = lint(study, "s")
    assert any("exactly 0 or 1" in e for e in errors)
