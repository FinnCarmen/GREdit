from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

RESULT_PATTERN = re.compile(
    r"Test Results: OrderedDict\(\[\('iid_ratio@10', ([^\)]+)\), \('ndcg@10', ([^\)]+)\)\]\)"
)


def describe_status(status: str) -> str:
    mapping = {
        "ok": "已完成",
        "missing_log": "缺少日志",
        "missing_test_results": "缺少评测结果",
        "missing": "缺失",
    }
    return mapping.get(status, status)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Parse GREdit evaluation logs and build a compact result table."
    )
    parser.add_argument(
        "--result",
        action="append",
        default=[],
        metavar="LABEL=LOG_PATH",
        help="Evaluation result label and log path, for example baseline=outputs/logs/baseline.log",
    )
    parser.add_argument("--output-json", type=Path, help="Optional path to write a JSON summary.")
    parser.add_argument("--output-md", type=Path, help="Optional path to write a Markdown table.")
    return parser.parse_args()


def parse_result_arg(raw: str) -> tuple[str, Path]:
    if "=" not in raw:
        raise ValueError(f"Invalid --result value: {raw!r}")
    label, path = raw.split("=", 1)
    label = label.strip()
    if not label:
        raise ValueError(f"Missing label in --result value: {raw!r}")
    return label, Path(path.strip())


def extract_metrics(log_path: Path) -> dict:
    if not log_path.exists():
        return {
            "status": "missing_log",
            "log_path": str(log_path),
            "iid_ratio@10": None,
            "ndcg@10": None,
        }
    text = log_path.read_text(encoding="utf-8", errors="ignore")
    matches = RESULT_PATTERN.findall(text)
    if not matches:
        return {
            "status": "missing_test_results",
            "log_path": str(log_path),
            "iid_ratio@10": None,
            "ndcg@10": None,
        }
    iid_ratio, ndcg = matches[-1]
    return {
        "status": "ok",
        "log_path": str(log_path),
        "iid_ratio@10": float(iid_ratio),
        "ndcg@10": float(ndcg),
    }


def build_payload(result_specs: list[tuple[str, Path]]) -> dict:
    rows = []
    for label, log_path in result_specs:
        row = {"label": label}
        row.update(extract_metrics(log_path))
        rows.append(row)
    return {"result_count": len(rows), "results": rows}


def build_markdown(payload: dict) -> str:
    lines = [
        "# GREdit 实验结果",
        "",
        "| 设置 | 状态 | iid_ratio@10 | ndcg@10 | 日志 |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    rows = payload.get("results") or []
    if not rows:
        lines.append("| none | 缺失 |  |  |  |")
    else:
        for row in rows:
            iid_ratio = "" if row["iid_ratio@10"] is None else row["iid_ratio@10"]
            ndcg = "" if row["ndcg@10"] is None else row["ndcg@10"]
            lines.append(
                f"| {row['label']} | {describe_status(row['status'])} | {iid_ratio} | {ndcg} | `{row['log_path']}` |"
            )
    return "\n".join(lines) + "\n"


def write_outputs(payload: dict, output_json: Path | None, output_md: Path | None) -> None:
    if output_json is not None:
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if output_md is not None:
        output_md.parent.mkdir(parents=True, exist_ok=True)
        output_md.write_text(build_markdown(payload), encoding="utf-8")


def main() -> None:
    args = parse_args()
    result_specs = [parse_result_arg(raw) for raw in args.result]
    payload = build_payload(result_specs)
    write_outputs(payload, args.output_json, args.output_md)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
