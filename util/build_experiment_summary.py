from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a concise GREdit experiment summary from the latest result JSON."
    )
    parser.add_argument(
        "--input-json",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "docs" / "experiment_results_latest.json",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "docs" / "experiment_summary_latest.json",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "docs" / "experiment_summary_latest.md",
    )
    return parser.parse_args()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def index_results(payload: dict) -> dict[str, dict]:
    return {str(row.get("label")): row for row in payload.get("results") or []}


def metric_delta(baseline: dict | None, candidate: dict | None, key: str) -> float | None:
    if not baseline or not candidate:
        return None
    left = baseline.get(key)
    right = candidate.get(key)
    if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
        return None
    return right - left


def judge_row(baseline: dict | None, candidate: dict | None) -> str:
    if not candidate or candidate.get("status") != "ok":
        return "pending"
    iid_delta = metric_delta(baseline, candidate, "iid_ratio@10")
    ndcg_delta = metric_delta(baseline, candidate, "ndcg@10")
    if iid_delta is None or ndcg_delta is None:
        return "incomplete"
    if iid_delta >= 0 and ndcg_delta >= 0:
        return "improved_or_tied"
    if iid_delta < 0 and ndcg_delta < 0:
        return "both_lower_than_baseline"
    return "mixed"


def build_summary(payload: dict) -> dict:
    rows = index_results(payload)
    baseline = rows.get("baseline")
    micro10 = rows.get("micro10")
    aug10 = rows.get("aug10")

    summary_rows = []
    for label in ("baseline", "micro10", "aug10"):
        row = rows.get(label)
        summary_rows.append(
            {
                "label": label,
                "status": row.get("status") if row else "missing",
                "iid_ratio@10": row.get("iid_ratio@10") if row else None,
                "ndcg@10": row.get("ndcg@10") if row else None,
                "iid_ratio_delta_vs_baseline": metric_delta(baseline, row, "iid_ratio@10"),
                "ndcg_delta_vs_baseline": metric_delta(baseline, row, "ndcg@10"),
                "judgement": "baseline_reference" if label == "baseline" else judge_row(baseline, row),
            }
        )

    micro10_status = judge_row(baseline, micro10)
    aug10_status = judge_row(baseline, aug10)
    if aug10_status == "pending":
        headline = "Formal aug10 evaluation is still pending; current evidence comes from baseline and micro10 only."
    elif aug10_status == "improved_or_tied":
        headline = "Formal aug10 evaluation is available and does not underperform baseline on the tracked metrics."
    elif aug10_status == "both_lower_than_baseline":
        headline = "Formal aug10 evaluation is available and both tracked metrics are lower than baseline."
    else:
        headline = "Formal aug10 evaluation is available, but the tradeoff against baseline is mixed or incomplete."

    if micro10_status == "both_lower_than_baseline":
        headline += " Micro10 remains below baseline on both tracked metrics."

    return {
        "headline": headline,
        "source_results_json": payload.get("source"),
        "summary_rows": summary_rows,
    }


def build_markdown(payload: dict) -> str:
    lines = [
        "# GREdit Experiment Summary",
        "",
        payload["headline"],
        "",
        "| 设置 | 状态 | iid_ratio@10 | ndcg@10 | iid delta vs baseline | ndcg delta vs baseline | 判断 |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in payload.get("summary_rows") or []:
        lines.append(
            f"| {row['label']} | {row['status']} | "
            f"{'' if row['iid_ratio@10'] is None else row['iid_ratio@10']} | "
            f"{'' if row['ndcg@10'] is None else row['ndcg@10']} | "
            f"{'' if row['iid_ratio_delta_vs_baseline'] is None else row['iid_ratio_delta_vs_baseline']} | "
            f"{'' if row['ndcg_delta_vs_baseline'] is None else row['ndcg_delta_vs_baseline']} | "
            f"{row['judgement']} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    source_payload = read_json(args.input_json)
    summary_payload = build_summary(source_payload)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(summary_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.output_md.write_text(build_markdown(summary_payload), encoding="utf-8")
    print(json.dumps(summary_payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
