from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Refresh GREdit latest results and summary from the server184 logs."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    return parser.parse_args()


def run_step(command: list[str], cwd: Path) -> None:
    completed = subprocess.run(command, cwd=str(cwd), check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    python_exe = sys.executable

    run_step([python_exe, str(repo_root / "util" / "sync_server184_results.py")], repo_root)
    run_step([python_exe, str(repo_root / "util" / "build_experiment_summary.py")], repo_root)


if __name__ == "__main__":
    main()
