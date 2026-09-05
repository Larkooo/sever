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
