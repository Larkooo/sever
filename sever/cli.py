"""sever command line."""
from __future__ import annotations

import argparse
import datetime as dt
import shutil
import sys
from importlib import resources
from pathlib import Path

from . import freeze as fz
from . import score as sc
from . import verdict as vd
from .study import StudyError, find_root, lint, load_yaml, save_yaml, studies_dir, study_dir


def cmd_new(args, root):
    d = studies_dir(root) / args.slug
    if d.exists():
        raise StudyError(f"{d} already exists")
    d.mkdir(parents=True)
    tpl = resources.files("sever") / "templates"
    text = (tpl / "study.yaml").read_text().replace("{slug}", args.slug).replace("{date}", dt.date.today().isoformat())
    (d / "study.yaml").write_text(text)
    (d / "notes.md").write_text((tpl / "notes.md").read_text().replace("{slug}", args.slug))
    print(f"created {d.relative_to(root)}/study.yaml and notes.md")
    print("fill in theory, alternatives, predictions with numeric criteria, analysis_plan, kill_rule; then `sever lint` and `sever freeze`")


def cmd_lint(args, root):
    slugs = [args.slug] if args.slug else [p.name for p in sorted(studies_dir(root).glob("*/")) if (p / "study.yaml").exists()]
    bad = 0
    for slug in slugs:
        d = study_dir(slug, root)
        frozen = (d / "freeze.yaml").exists()
        E, W = lint(load_yaml(d / "study.yaml"), slug, frozen=frozen)
        if frozen:
            E += fz.check(slug, root)
        print(f"{slug}: {len(E)} errors, {len(W)} warnings")
        for e in E:
            print(f"  error   {e}")
        for w in W:
            print(f"  warning {w}")
        bad += bool(E)
    return 1 if bad else 0


def cmd_freeze(args, root):
    rec = fz.freeze(args.slug, root)
    print(f"frozen {args.slug} at commit {rec['commit'][:10]}  sha256 {rec['sha256'][:12]}")
    print("commit freeze.yaml now. From here on the theory, alternatives, predictions, analysis plan and kill rule are fixed.")


def cmd_check(args, root):
    problems = fz.check(args.slug, root)
    if problems:
        print(f"{args.slug}: preregistration NOT intact")
        for p in problems:
            print(f"  {p}")
        return 1
    print(f"{args.slug}: preregistration intact")
    return 0


def cmd_verdict(args, root):
    d = study_dir(args.slug, root)
    study = load_yaml(d / "study.yaml")
    problems = fz.check(args.slug, root)
    if study.get("exploratory"):
        args.exploratory = True
    if problems and not args.exploratory:
        print(f"refusing to compute a verdict: {'; '.join(problems)}")
        print("either restore the frozen sections, or re-run with --exploratory to record a verdict that will not count")
        return 1
    review = study.get("review") or {}
    if not (review.get("strongest_objection") or "").strip() and not args.exploratory:
        print("refusing to compute a verdict: review.strongest_objection is empty. Try to kill the result first.")
        return 1
    v = vd.compute(study)
    v["exploratory"] = bool(problems) or bool(args.exploratory) or bool(study.get("exploratory"))
    save_yaml(d / "verdict.yaml", v)
    print(vd.report(study, v, exploratory=v["exploratory"]))
    print(f"\nwritten {d.relative_to(root)}/verdict.yaml")
    return 0


def cmd_status(args, root):
    rows = []
    for d in sorted(studies_dir(root).glob("*/")):
        if not (d / "study.yaml").exists():
            continue
        s = load_yaml(d / "study.yaml")
        th = s.get("theory") or {}
        state = "draft"
        if (d / "freeze.yaml").exists():
            state = "frozen" if not fz.check(d.name, root) else "frozen (BROKEN)"
        if (d / "verdict.yaml").exists():
            v = load_yaml(d / "verdict.yaml")
            state = v.get("status", "?") + (" (exploratory)" if v.get("exploratory") else "")
        n = len(s.get("predictions") or [])
        done = sum(1 for p in s.get("predictions") or [] if p.get("outcome") is not None)
        rows.append((d.name, f"{th.get('name')}@{th.get('version', 1)}", state, f"{done}/{n}", th.get("prior_credence")))
    if not rows:
        print("no studies. `sever new <slug>` to start one.")
        return 0
    w = max(5, *(len(r[0]) for r in rows))
    print(f"{'study':<{w}}  {'theory':<28} {'state':<24} {'outcomes':<9} prior")
    for r in rows:
        print(f"{r[0]:<{w}}  {r[1]:<28} {r[2]:<24} {r[3]:<9} {r[4]}")


def cmd_score(args, root):
    print(sc.report(root))


def cmd_graveyard(args, root):
    dead = []
    successors = {}
    for d in sorted(studies_dir(root).glob("*/")):
        if not (d / "study.yaml").exists():
            continue
        s = load_yaml(d / "study.yaml")
        th = s.get("theory") or {}
        if th.get("supersedes"):
            successors[th["supersedes"]] = f"{th.get('name')}@{th.get('version', 1)} ({d.name})"
        v = load_yaml(d / "verdict.yaml") if (d / "verdict.yaml").exists() else {}
        if v.get("status") == "refuted" or s.get("status") == "abandoned":
            failed = [r["id"] for r in v.get("predictions", []) if r["critical"] and r["outcome"] == "fail"]
            tag = " (exploratory)" if v.get("exploratory") else ""
            dead.append((f"{th.get('name')}@{th.get('version', 1)}{tag}", d.name, failed, v.get("computed_at", "")))
    if not dead:
        print("the graveyard is empty. Either nothing has been tested severely, or you are very good.")
        return 0
    for key, slug, failed, when in dead:
        succ = successors.get(key)
        print(f"{key}  ({slug})  died {when[:10]}  killed by: {', '.join(failed) or 'abandoned'}"
              + (f"  ->  {succ}" if succ else "  (no successor)"))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sever", description="severe testing for research programmes")
    ap.add_argument("--root", default=None, help="repository root (default: found from cwd)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("new", help="scaffold a study"); p.add_argument("slug"); p.set_defaults(fn=cmd_new)
    p = sub.add_parser("lint", help="check a study (or all) for missing criteria and weak tests"); p.add_argument("slug", nargs="?"); p.set_defaults(fn=cmd_lint)
    p = sub.add_parser("freeze", help="preregister: tie the theory and predictions to the current commit"); p.add_argument("slug"); p.set_defaults(fn=cmd_freeze)
    p = sub.add_parser("check", help="verify the preregistration has not changed"); p.add_argument("slug"); p.set_defaults(fn=cmd_check)
    p = sub.add_parser("verdict", help="compute the verdict from recorded outcomes"); p.add_argument("slug"); p.add_argument("--exploratory", action="store_true"); p.set_defaults(fn=cmd_verdict)
    p = sub.add_parser("status", help="all studies at a glance"); p.set_defaults(fn=cmd_status)
    p = sub.add_parser("score", help="calibration of your stated credences across studies"); p.set_defaults(fn=cmd_score)
    p = sub.add_parser("graveyard", help="refuted theories, what killed them, and their successors"); p.set_defaults(fn=cmd_graveyard)
    args = ap.parse_args(argv)
    root = Path(args.root).resolve() if args.root else find_root()
    try:
        rc = args.fn(args, root)
    except StudyError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return rc or 0


if __name__ == "__main__":
    sys.exit(main())
