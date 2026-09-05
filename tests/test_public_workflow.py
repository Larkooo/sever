import copy
from pathlib import Path

import pytest

from sever.cli import main
from sever.freeze import freeze
from sever.score import collect
from sever.study import StudyError, find_root, load_yaml, save_yaml
from test_freeze import GOOD, repo


@pytest.mark.parametrize("slug", ["../outside", "/tmp/outside", "nested/study", "."])
def test_new_rejects_paths_outside_studies(tmp_path, slug, capsys):
    assert main(["--root", str(tmp_path), "new", slug]) == 1
    assert "single name" in capsys.readouterr().err
    assert not (tmp_path / "studies").exists()


def test_find_root_recognizes_git_worktree(tmp_path):
    (tmp_path / ".git").write_text("gitdir: /example/worktree")
    nested = tmp_path / "nested"
    nested.mkdir()
    assert find_root(nested) == tmp_path


@pytest.mark.parametrize("content", ["- not a mapping", "theory: [invalid]", "predictions: [1]"])
def test_malformed_yaml_is_reported_without_traceback(tmp_path, capsys, content):
    folder = tmp_path / "studies" / "bad"
    folder.mkdir(parents=True)
    (folder / "study.yaml").write_text(content)
    assert main(["--root", str(tmp_path), "lint", "bad"]) == 1
    assert "error:" in capsys.readouterr().err


def conclude(root: Path, outcome="pass"):
    freeze("s1", root)
    study = load_yaml(root / "studies/s1/study.yaml")
    study["predictions"][0]["outcome"] = outcome
    study["review"]["strongest_objection"] = "Synthetic demonstration only."
    save_yaml(root / "studies/s1/study.yaml", study)
    assert main(["--root", str(root), "verdict", "s1"]) == 0


def test_inconclusive_counts_as_not_pass_in_calibration(repo):
    conclude(repo, "inconclusive")
    rows = collect(repo)
    assert len(rows) == 1 and rows[0]["observed"] == 0


def test_calibration_rejects_changed_outcomes(repo):
    conclude(repo)
    path = repo / "studies/s1/study.yaml"
    study = load_yaml(path)
    study["predictions"][0]["outcome"] = "fail"
    save_yaml(path, study)
    with pytest.raises(StudyError, match="recompute"):
        collect(repo)


def test_calibration_rejects_changed_forecasts(repo):
    conclude(repo)
    path = repo / "studies/s1/study.yaml"
    study = load_yaml(path)
    study["theory"]["prior_credence"] = .9
    save_yaml(path, study)
    with pytest.raises(StudyError, match="broken freeze"):
        collect(repo)


def test_invalid_exploratory_verdict_is_rejected(repo, capsys):
    study = copy.deepcopy(GOOD)
    study["theory"]["prior_credence"] = 1
    save_yaml(repo / "studies/s1/study.yaml", study)
    assert main(["--root", str(repo), "verdict", "s1", "--exploratory"]) == 1
    assert "invalid study" in capsys.readouterr().err


def test_review_objection_must_be_text(repo, capsys):
    study = load_yaml(repo / "studies/s1/study.yaml")
    study["review"]["strongest_objection"] = ["not a string"]
    save_yaml(repo / "studies/s1/study.yaml", study)
    assert main(["--root", str(repo), "verdict", "s1", "--exploratory"]) == 1
    assert "must be a string" in capsys.readouterr().err
