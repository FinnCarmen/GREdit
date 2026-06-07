from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_JSON = REPO_ROOT / "docs" / "experiment_runtime_latest.json"
DEFAULT_OUTPUT_MD = REPO_ROOT / "docs" / "experiment_runtime_latest.md"
DEFAULT_SSH_TARGET = "grf@172.31.233.184"
DEFAULT_SSH_PORT = 50805


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync the latest server184 runtime status for the formal aug10 GREdit run."
    )
    parser.add_argument("--ssh-target", default=DEFAULT_SSH_TARGET)
    parser.add_argument("--ssh-port", type=int, default=DEFAULT_SSH_PORT)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    return parser.parse_args()


def run_ssh(ssh_target: str, ssh_port: int, command: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["ssh", "-p", str(ssh_port), ssh_target, command],
        check=False,
        text=True,
        encoding="utf-8",
        errors="ignore",
        capture_output=True,
    )


def parse_runtime_output(text: str) -> dict:
    data = {
        "edit_pid": None,
        "watcher_pid": None,
        "deltaw_exists": False,
        "solve_progress": None,
        "position_batch_progress": None,
        "tail_excerpt": [],
    }
    for line in text.splitlines():
        if line.startswith("EDIT_PID="):
            value = line.split("=", 1)[1].strip()
            data["edit_pid"] = int(value) if value.isdigit() else None
        elif line.startswith("WATCHER_PID="):
            value = line.split("=", 1)[1].strip()
            data["watcher_pid"] = int(value) if value.isdigit() else None
        elif line.startswith("DELTAW_EXISTS="):
            data["deltaw_exists"] = line.split("=", 1)[1].strip() == "1"
        elif line.startswith("TAIL="):
            data["tail_excerpt"].append(line.split("=", 1)[1])

    solve_match = None
    batch_match = None
    for entry in data["tail_excerpt"]:
        solve_match = solve_match or re.search(r"solve edits by position:\s+(\d+)%\|", entry)
        batch_match = batch_match or re.search(r"z batches position\s+(\d+):\s+(\d+)%\|", entry)
    if solve_match:
        data["solve_progress"] = int(solve_match.group(1))
    if batch_match:
        data["position_batch_progress"] = {
            "position": int(batch_match.group(1)),
            "percent": int(batch_match.group(2)),
        }
    return data


def build_markdown(payload: dict) -> str:
    lines = [
        "# GREdit Runtime Status",
        "",
        f"- edit_pid: `{payload.get('edit_pid')}`",
        f"- watcher_pid: `{payload.get('watcher_pid')}`",
        f"- deltaW_exists: `{payload.get('deltaw_exists')}`",
        f"- solve_progress: `{payload.get('solve_progress')}`",
    ]
    batch = payload.get("position_batch_progress") or {}
    lines.append(
        f"- current_position_batch_progress: `position={batch.get('position')}` `percent={batch.get('percent')}`"
        if batch
        else "- current_position_batch_progress: `unknown`"
    )
    lines.extend(["", "## Tail Excerpt"])
    for entry in payload.get("tail_excerpt") or []:
        lines.append(f"- {entry}")
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    remote_command = r"""
EDIT_PID=$(pgrep -f "edit_main.py --category=Cell_Phones_and_Accessories --pretrained_model_path=data/ckpt/TIGER_Cell_Phones_and_Accessories/genrec_default_ori.pth --cov_lambda=1000 --number_knowledge=5" | head -n 1 || true)
WATCHER_PID=$(pgrep -f "/tmp/gredit_aug10_eval_watcher.sh" | head -n 1 || true)
if [ -f /home/grf/GenRecEdit-main/results/Cell_Phones_and_Accessories/deltaW_edit_requests_cold_test_augmented_10_1000_5.pt ]; then
  DELTAW_EXISTS=1
else
  DELTAW_EXISTS=0
fi
echo "EDIT_PID=${EDIT_PID}"
echo "WATCHER_PID=${WATCHER_PID}"
echo "DELTAW_EXISTS=${DELTAW_EXISTS}"
python3 - <<'PY'
import re
from pathlib import Path
path = Path('/home/grf/GenRecEdit-main/outputs/logs/genrecedit_aug10_gpu0_20260607.log')
if path.exists():
    text = path.read_text(encoding='utf-8', errors='ignore')
    ansi = re.compile(r'\x1b\[[0-9;?]*[ -/]*[@-~]')
    cleaned = ansi.sub('', text).replace('\r', '\n')
    lines = [line for line in cleaned.splitlines() if line.strip()]
    for line in lines[-40:]:
        print(f'TAIL={line}')
PY
"""
    result = run_ssh(args.ssh_target, args.ssh_port, remote_command)
    payload = parse_runtime_output(result.stdout)
    payload["source"] = {
        "ssh_target": args.ssh_target,
        "ssh_port": args.ssh_port,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.output_md.write_text(build_markdown(payload), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
