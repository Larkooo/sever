"""Tie the preregistered sections of a study to a git commit, and verify later that
they have not changed. The freeze record names a commit; the study file at that commit
must hash to the recorded value, and so must the working copy."""
from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

from .study import (
    StudyError, frozen_hash, lint, load_study, load_yaml, now_iso, save_yaml,
    study_dir, structure_errors,
)


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)


def head(root: Path) -> str:
    r = _git(root, "rev-parse", "HEAD")
    if r.returncode:
        raise StudyError("not a git repository, or no commits yet")
    return r.stdout.strip()


def is_clean(root: Path, path: Path) -> bool:
    return _git(root, "status", "--porcelain", "--", str(path)).stdout.strip() == ""


def file_at_commit(root: Path, commit: str, relpath: str) -> str:
    r = _git(root, "show", f"{commit}:{relpath}")
    if r.returncode:
        raise StudyError(f"cannot read {relpath} at commit {commit[:10]}")
    return r.stdout


def study_at_commit(root: Path, commit: str, relpath: str) -> dict:
    try:
        study = yaml.safe_load(file_at_commit(root, commit, relpath))
    except yaml.YAMLError as exc:
        raise StudyError("committed study is not valid YAML") from exc
    if not isinstance(study, dict) or structure_errors(study):
        raise StudyError("committed study has an invalid structure")
    return study


def freeze(slug: str, root: Path) -> dict:
    d = study_dir(slug, root)
    if (d / "freeze.yaml").exists():
        raise StudyError("already frozen. A changed theory is a new version: run `sever new` for it")
    study = load_study(d / "study.yaml")
    if any(p.get("outcome") is not None for p in study.get("predictions") or []):
        raise StudyError("outcomes are already recorded; a freeze must come before data")
    errors, _ = lint(study, slug)
    if errors:
        raise StudyError("lint errors:\n  " + "\n  ".join(errors))
    if not is_clean(root, d):
        raise StudyError("commit the study files first; the freeze records the commit they live in")
    commit = head(root)
    rel = str((d / "study.yaml").relative_to(root))
    committed = study_at_commit(root, commit, rel)
    h = frozen_hash(study)
    if frozen_hash(committed) != h:
        raise StudyError("working copy differs from HEAD; commit first")
    rec = {"commit": commit, "sha256": h, "frozen_at": now_iso(), "file": rel}
    save_yaml(d / "freeze.yaml", rec)
    return rec


def check(slug: str, root: Path) -> list[str]:
    """Empty list means the preregistration is intact."""
    d = study_dir(slug, root)
    if not (d / "freeze.yaml").exists():
        return ["not frozen"]
    fz = load_yaml(d / "freeze.yaml")
    study = load_study(d / "study.yaml")
    problems = []
    if frozen_hash(study) != fz.get("sha256"):
        problems.append("preregistered sections changed since the freeze "
                        "(theory, alternatives, predictions, analysis_plan, or kill_rule)")
    try:
        committed = study_at_commit(root, fz["commit"], fz["file"])
        if frozen_hash(committed) != fz.get("sha256"):
            problems.append("freeze record does not match the commit it names; freeze.yaml was edited")
    except (StudyError, KeyError):
        problems.append(f"freeze commit {str(fz.get('commit', ''))[:10]} is not in this repository's history")
    return problems
