from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
from pathlib import Path


def load_summarize_module():
    module_path = Path(__file__).with_name("summarize_experiment_results.py")
    spec = importlib.util.spec_from_file_location("summarize_experiment_results", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load summarize module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SUMMARY_MODULE = load_summarize_module()
build_markdown = SUMMARY_MODULE.build_markdown
build_payload = SUMMARY_MODULE.build_payload
REPO_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_SSH_TARGET = "grf@172.31.233.184"
DEFAULT_SSH_PORT = 50805
DEFAULT_REMOTE_BASE = "/home/grf/GenRecEdit-main/outputs/logs"
DEFAULT_LOCAL_CACHE = REPO_ROOT / "tmp" / "server184_eval_logs"
DEFAULT_OUTPUT_JSON = REPO_ROOT / "docs" / "experiment_results_latest.json"
DEFAULT_OUTPUT_MD = REPO_ROOT / "docs" / "experiment_results_latest.md"

DEFAULT_LOGS = {
    "baseline": "genrecedit_eval_baseline_test_20260607_small.log",
    "micro10": "genrecedit_eval_micro10_test_20260607_small.log",
    "aug10": "genrecedit_eval_aug10_test_20260607_small.log",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync GREdit evaluation logs from server184 and rebuild the latest result table."
    )
    parser.add_argument("--ssh-target", default=DEFAULT_SSH_TARGET)
    parser.add_argument("--ssh-port", type=int, default=DEFAULT_SSH_PORT)
    parser.add_argument("--remote-base", default=DEFAULT_REMOTE_BASE)
    parser.add_argument("--local-cache", type=Path, default=DEFAULT_LOCAL_CACHE)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    return parser.parse_args()


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=False, text=True, capture_output=True)


def sync_log(ssh_target: str, ssh_port: int, remote_base: str, local_cache: Path, filename: str) -> Path:
    local_cache.mkdir(parents=True, exist_ok=True)
    local_path = local_cache / filename
    remote_path = f"{ssh_target}:{remote_base}/{filename}"
    result = run_command(["scp", "-P", str(ssh_port), remote_path, str(local_path)])
    if result.returncode != 0 and local_path.exists():
        # Keep the last successful local copy if the remote file is not ready yet.
        return local_path
    if result.returncode != 0:
        return local_path
    return local_path


def build_sync_summary(payload: dict, output_json: Path, output_md: Path) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_md.write_text(build_markdown(payload), encoding="utf-8")


def main() -> None:
    args = parse_args()
    result_specs = []
    for label, filename in DEFAULT_LOGS.items():
        local_path = sync_log(args.ssh_target, args.ssh_port, args.remote_base, args.local_cache, filename)
        result_specs.append((label, local_path))

    payload = build_payload(result_specs)
    payload["source"] = {
        "ssh_target": args.ssh_target,
        "ssh_port": args.ssh_port,
        "remote_base": args.remote_base,
    }
    build_sync_summary(payload, args.output_json, args.output_md)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
