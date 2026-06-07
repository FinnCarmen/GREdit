from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PUBLISH_FILES = [
    REPO_ROOT / "docs" / "experiment_results_latest.md",
    REPO_ROOT / "docs" / "experiment_results_latest.json",
    REPO_ROOT / "docs" / "experiment_summary_latest.md",
    REPO_ROOT / "docs" / "experiment_summary_latest.json",
    REPO_ROOT / "docs" / "experiment_runtime_latest.md",
    REPO_ROOT / "docs" / "experiment_runtime_latest.json",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Refresh GREdit latest reporting files and publish them through git when they change."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
    )
    parser.add_argument(
        "--commit-message",
        default="docs: refresh latest experiment reporting",
    )
    parser.add_argument(
        "--push-remote",
        action="append",
        default=[],
        metavar="REMOTE",
        help="Optional git remote to push after committing. Can be repeated.",
    )
    parser.add_argument(
        "--skip-push",
        action="store_true",
        help="Refresh and commit locally without pushing.",
    )
    return parser.parse_args()


def run(command: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=False,
    )
    if check and completed.returncode != 0:
        if completed.stdout:
            print(completed.stdout, end="")
        if completed.stderr:
            print(completed.stderr, end="", file=sys.stderr)
        raise SystemExit(completed.returncode)
    return completed


def file_args(repo_root: Path) -> list[str]:
    return [str(path.relative_to(repo_root)) for path in PUBLISH_FILES]


def refresh_latest(repo_root: Path) -> None:
    run([sys.executable, str(repo_root / "util" / "refresh_latest_reporting.py")], repo_root)


def has_changes(repo_root: Path) -> bool:
    for command in (
        ["git", "diff", "--quiet", "--", *file_args(repo_root)],
        ["git", "diff", "--cached", "--quiet", "--", *file_args(repo_root)],
    ):
        result = run(command, repo_root, check=False)
        if result.returncode == 1:
            return True
        if result.returncode not in (0, 1):
            raise SystemExit(result.returncode)
    return False


def commit_changes(repo_root: Path, commit_message: str) -> None:
    run(["git", "add", "--", *file_args(repo_root)], repo_root)
    run(["git", "commit", "-m", commit_message], repo_root)


def current_branch(repo_root: Path) -> str:
    result = run(["git", "branch", "--show-current"], repo_root)
    branch = result.stdout.strip()
    if not branch:
        raise SystemExit("Unable to determine current git branch.")
    return branch


def push_changes(repo_root: Path, remotes: list[str]) -> None:
    branch = current_branch(repo_root)
    for remote in remotes:
        run(["git", "push", remote, f"HEAD:{branch}"], repo_root)


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()

    refresh_latest(repo_root)
    if not has_changes(repo_root):
        print("No latest reporting changes to publish.")
        return

    commit_changes(repo_root, args.commit_message)
    if not args.skip_push and args.push_remote:
        push_changes(repo_root, args.push_remote)

    print("Published latest reporting updates.")


if __name__ == "__main__":
    main()
