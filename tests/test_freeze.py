import subprocess
from pathlib import Path

import pytest
import yaml

from sever.cli import main
from sever.freeze import check, freeze
from sever.study import StudyError, load_yaml, save_yaml

GOOD = {
    "slug": "s1", "title": "t", "created": "2026-01-01",
    "theory": {"name": "s1", "version": 1, "supersedes": None, "statement": "x is y", "formal": "",
               "scope": "toy", "prior_credence": 0.4},
    "alternatives": [{"id": "H0", "statement": "nothing"}],
    "predictions": [{"id": "P1", "statement": "z", "critical": True, "pass_if": "ratio < 1.5",
                     "fail_if": "ratio > 2", "p_pass_if_true": 0.8, "p_pass_if_false": 0.2,
                     "discriminates": ["H0"], "outcome": None, "evidence": None}],
    "analysis_plan": "run 10 seeds", "kill_rule": "if P1 fails, abandon",
    "results": {"summary": None, "exploratory": []},
    "review": {"strongest_objection": None, "confounds_checked": [], "what_would_change_my_mind": None},
}


def git(root, *a):
    return subprocess.run(["git", *a], cwd=root, capture_output=True, text=True, check=True)


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "t@t")
    git(tmp_path, "config", "user.name", "t")
    d = tmp_path / "studies" / "s1"
    d.mkdir(parents=True)
    save_yaml(d / "study.yaml", GOOD)
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-qm", "prereg")
    return tmp_path


def test_freeze_then_check_ok(repo):
    freeze("s1", repo)
    assert check("s1", repo) == []


def test_freeze_refuses_uncommitted(repo):
    s = load_yaml(repo / "studies/s1/study.yaml")
    s["theory"]["statement"] = "changed"
    save_yaml(repo / "studies/s1/study.yaml", s)
    with pytest.raises(StudyError, match="commit"):
        freeze("s1", repo)


def test_freeze_refuses_recorded_outcomes(repo):
    s = load_yaml(repo / "studies/s1/study.yaml")
    s["predictions"][0]["outcome"] = "pass"
    save_yaml(repo / "studies/s1/study.yaml", s)
    git(repo, "commit", "-qam", "peeked")
    with pytest.raises(StudyError, match="before data"):
        freeze("s1", repo)


def test_editing_prediction_after_freeze_is_detected(repo):
    freeze("s1", repo)
    s = load_yaml(repo / "studies/s1/study.yaml")
    s["predictions"][0]["pass_if"] = "ratio < 3"
    save_yaml(repo / "studies/s1/study.yaml", s)
    assert any("changed since the freeze" in p for p in check("s1", repo))


def test_recording_outcome_after_freeze_is_fine(repo):
    freeze("s1", repo)
    s = load_yaml(repo / "studies/s1/study.yaml")
    s["predictions"][0]["outcome"] = "fail"
    s["predictions"][0]["evidence"] = "fig1"
    save_yaml(repo / "studies/s1/study.yaml", s)
    assert check("s1", repo) == []


def test_tampered_freeze_record_is_detected(repo):
    freeze("s1", repo)
    s = load_yaml(repo / "studies/s1/study.yaml")
    s["predictions"][0]["pass_if"] = "ratio < 3"
    save_yaml(repo / "studies/s1/study.yaml", s)
    from sever.study import frozen_hash
    fz = load_yaml(repo / "studies/s1/freeze.yaml")
    fz["sha256"] = frozen_hash(s)
    save_yaml(repo / "studies/s1/freeze.yaml", fz)
    assert any("edited" in p for p in check("s1", repo))


def test_verdict_requires_review_and_intact_freeze(repo, capsys):
    freeze("s1", repo)
    s = load_yaml(repo / "studies/s1/study.yaml")
    s["predictions"][0]["outcome"] = "fail"
    save_yaml(repo / "studies/s1/study.yaml", s)
    assert main(["--root", str(repo), "verdict", "s1"]) == 1
    assert "strongest_objection" in capsys.readouterr().out
    s["review"]["strongest_objection"] = "the toy is too small"
    save_yaml(repo / "studies/s1/study.yaml", s)
    assert main(["--root", str(repo), "verdict", "s1"]) == 0
    v = load_yaml(repo / "studies/s1/verdict.yaml")
    assert v["status"] == "refuted" and not v["exploratory"]
    assert "REFUTED" in capsys.readouterr().out


def test_exploratory_study_allows_outcomes_without_freeze(repo, capsys):
    s = load_yaml(repo / "studies/s1/study.yaml")
    s["exploratory"] = True
    s["predictions"][0]["outcome"] = "fail"
    save_yaml(repo / "studies/s1/study.yaml", s)
    assert main(["--root", str(repo), "lint", "s1"]) == 0
    assert main(["--root", str(repo), "verdict", "s1"]) == 0
    v = load_yaml(repo / "studies/s1/verdict.yaml")
    assert v["status"] == "refuted" and v["exploratory"]
    from sever.score import collect
    assert collect(repo) == []
