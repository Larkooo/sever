"""Exercise the CLI in a temporary Git repository with explicitly synthetic outcomes."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import yaml


def main() -> None:
    example = Path(__file__).with_name("latency-study.yaml")
    with tempfile.TemporaryDirectory(prefix="sever-demo-") as directory:
        root = Path(directory)

        def git(*arguments: str) -> None:
            subprocess.run(["git", *arguments], cwd=root, check=True, capture_output=True)

        def sever(*arguments: str) -> None:
            subprocess.run(
                [sys.executable, "-m", "sever.cli", "--root", str(root), *arguments],
                cwd=root, check=True,
            )

        git("init", "-q")
        git("config", "user.name", "Example")
        git("config", "user.email", "example@example.invalid")
        sever("new", "latency-cache")
        study_path = root / "studies/latency-cache/study.yaml"
        shutil.copyfile(example, study_path)
        sever("lint", "latency-cache")
        git("add", "studies")
        git("commit", "-qm", "Register example criteria")
        sever("freeze", "latency-cache")
        git("add", "studies")
        git("commit", "-qm", "Record example freeze")

        study = yaml.safe_load(study_path.read_text())
        for prediction in study["predictions"]:
            prediction["outcome"] = "pass"
            prediction["evidence"] = "Synthetic outcome for the CLI demonstration; no benchmark was run."
        study["results"]["summary"] = "Synthetic demonstration only."
        study["review"]["strongest_objection"] = "No real measurements were collected."
        study_path.write_text(yaml.safe_dump(study, sort_keys=False))
        sever("check", "latency-cache")
        sever("verdict", "latency-cache")
        sever("score")
        print("\nDemo complete. All outcomes were synthetic; the temporary repository is removed.")


if __name__ == "__main__":
    main()
