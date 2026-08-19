#!/usr/bin/env python3
"""Render LocalLLM benchmark run reports and the repository benchmark index.

The canonical data source is a run's immutable ``run.json``. This script has
no third-party dependencies so it can run on the Docker control host.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
BENCHMARKS = ROOT / "benchmarks"


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError(f"Expected object in {path}")
    return data


def write_text(path: Path, content: str) -> None:
    temp = path.with_suffix(f"{path.suffix}.tmp")
    temp.write_text(content, encoding="utf-8")
    temp.replace(path)


def value_at(data: dict[str, Any], *keys: str, default: Any = "—") -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return default if current is None else current


def markdown_cell(value: Any) -> str:
    if value is None or value == "":
        return "—"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value).replace("|", "\\|").replace("\n", " ")


def command_text(command: Any) -> str:
    if isinstance(command, list):
        return " ".join(str(part) for part in command)
    return str(command or "")


def stat_mean(value: Any) -> float | None:
    candidate: object = value.get("mean") if isinstance(value, dict) else value
    if candidate is None:
        return None
    try:
        return float(str(candidate))
    except ValueError:
        return None


def performance_rows(run: dict[str, Any]) -> list[dict[str, Any]]:
    raw = value_at(run, "results", "performance", default={})
    if not isinstance(raw, dict):
        return []
    rows: list[dict[str, Any]] = []
    for entry in raw.get("benchmarks", []):
        if not isinstance(entry, dict):
            continue
        concurrency = int(entry.get("concurrency", 1) or 1)
        aggregate_tg = stat_mean(entry.get("tg_throughput"))
        rows.append(
            {
                "depth": int(entry.get("context_size", 0) or 0),
                "concurrency": concurrency,
                "pp_tps": stat_mean(entry.get("pp_throughput")),
                "tg_tps": aggregate_tg,
                "per_agent_tg_tps": (
                    aggregate_tg / concurrency if aggregate_tg is not None and concurrency else None
                ),
                "ttft_ms": stat_mean(entry.get("e2e_ttft")),
                "pp": entry.get("prompt_size"),
                "tg": entry.get("response_size"),
            }
        )
    return sorted(rows, key=lambda row: (row["depth"], row["concurrency"]))


def quality_summary(run: dict[str, Any]) -> dict[str, Any]:
    quality = value_at(run, "results", "quality", default={})
    if not isinstance(quality, dict):
        return {}
    scores: dict[str, Any] = {}
    raw_scores = quality.get("scores")
    if isinstance(raw_scores, dict):
        scores = raw_scores
    return {
        "score": quality.get("final_score", scores.get("final_score")),
        "rating": quality.get("rating", scores.get("rating")),
        "completion_rate": quality.get("completion_rate", scores.get("completion_rate")),
        "safety_warnings": quality.get("safety_warnings", scores.get("safety_warnings", [])),
        "categories": scores.get("category_scores", quality.get("category_scores", [])),
        "excluded": scores.get("excluded_scenarios", quality.get("excluded_scenarios", [])),
    }


def run_title(run: dict[str, Any]) -> str:
    model = value_at(run, "model", "hf_repository", default=None)
    if model:
        return str(model)
    return str(value_at(run, "model", "served_name", default="Unknown model"))


def render_report(run: dict[str, Any], run_path: Path) -> str:
    quality = quality_summary(run)
    rows = performance_rows(run)
    stack = value_at(run, "stack", default={})
    model = value_at(run, "model", default={})
    hardware = value_at(run, "hardware", default={})
    power = value_at(run, "power_policy", default={})
    commands = value_at(run, "commands", default=[])

    lines = [
        f"# Benchmark Run — {run_title(run)}",
        "",
        f"- **Run ID:** `{markdown_cell(run.get('run_id'))}`",
        f"- **Status:** `{markdown_cell(run.get('status'))}`",
        f"- **Started:** `{markdown_cell(run.get('started_at'))}`",
        f"- **Finished:** `{markdown_cell(run.get('finished_at'))}`",
        f"- **Protocol:** `{markdown_cell(run.get('protocol'))}`",
        f"- **Comparison key:** `{markdown_cell(run.get('comparison_key'))}`",
        "",
        "## Model and Stack",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Hugging Face source | `{markdown_cell(model.get('hf_repository'))}` |",
        f"| Host model path | `{markdown_cell(model.get('host_path'))}` |",
        f"| Served model name | `{markdown_cell(model.get('served_name'))}` |",
        f"| Engine | `{markdown_cell(stack.get('engine'))}` |",
        f"| Compose file | `{markdown_cell(stack.get('compose_file'))}` |",
        f"| Compose SHA-256 | `{markdown_cell(stack.get('compose_sha256'))}` |",
        f"| Compose environment file | `{markdown_cell(value_at(stack, 'environment_file', 'path'))}` |",
        f"| Environment SHA-256 | `{markdown_cell(value_at(stack, 'environment_file', 'sha256'))}` |",
        f"| Container image | `{markdown_cell(value_at(stack, 'container', 'image'))}` |",
        f"| Image digest | `{markdown_cell(value_at(stack, 'container', 'image_digest'))}` |",
        "",
        "## GPU Power Policy",
        "",
    ]

    if isinstance(power, dict) and power.get("enabled"):
        lines.extend(
            [
                f"- **Management:** `{markdown_cell(power.get('target'))}`",
                f"- **Requested limit:** `{markdown_cell(power.get('requested_watts'))} W`",
                f"- **Restore status:** `{markdown_cell(power.get('restore_status'))}`",
                "",
                "| GPU | Original limit | Applied limit | Restored limit |",
                "|---|---:|---:|---:|",
            ]
        )
        before = power.get("before_watts", {}) if isinstance(power.get("before_watts"), dict) else {}
        restored = power.get("restored_watts", {}) if isinstance(power.get("restored_watts"), dict) else {}
        for gpu in sorted(before, key=lambda value: int(value) if str(value).isdigit() else str(value)):
            lines.append(
                f"| {markdown_cell(gpu)} | {markdown_cell(before[gpu])} W | "
                f"{markdown_cell(power.get('requested_watts'))} W | {markdown_cell(restored.get(gpu))} W |"
            )
    else:
        lines.append("- No power limit was changed for this run.")

    lines.extend(["", "## Hardware", ""])
    before_snapshot = hardware.get("before", {}) if isinstance(hardware, dict) else {}
    gpus = before_snapshot.get("gpus", []) if isinstance(before_snapshot, dict) else []
    if gpus:
        lines.extend(
            [
                "| GPU | Name | Power limit | Memory | PCIe |",
                "|---:|---|---:|---:|---|",
            ]
        )
        for gpu in gpus:
            lines.append(
                "| {index} | {name} | {power} W | {memory} MiB | Gen {pcie_gen} ×{pcie_width} |".format(
                    index=markdown_cell(gpu.get("index")),
                    name=markdown_cell(gpu.get("name")),
                    power=markdown_cell(gpu.get("power.limit")),
                    memory=markdown_cell(gpu.get("memory.total")),
                    pcie_gen=markdown_cell(gpu.get("pcie.link.gen.current")),
                    pcie_width=markdown_cell(gpu.get("pcie.link.width.current")),
                )
            )
    else:
        lines.append("- GPU snapshot unavailable; see `run.json` for the collection error.")

    lines.extend(["", "## Tool-Calling Quality", ""])
    if quality:
        safety = quality.get("safety_warnings") or []
        lines.extend(
            [
                f"- **Final score:** {markdown_cell(quality.get('score'))}",
                f"- **Rating:** {markdown_cell(quality.get('rating'))}",
                f"- **Completion rate:** {markdown_cell(quality.get('completion_rate'))}",
                f"- **Safety warnings:** {len(safety)}",
                f"- **Excluded scenarios:** {len(quality.get('excluded') or [])}",
                "",
            ]
        )
        categories = quality.get("categories")
        if isinstance(categories, list) and categories:
            lines.extend(["| Category | Score | Earned | Max | Pass / Partial / Fail |", "|---|---:|---:|---:|---|"])
            for category in categories:
                if not isinstance(category, dict):
                    continue
                lines.append(
                    "| {label} | {percent} | {earned} | {maximum} | {passed} / {partial} / {failed} |".format(
                        label=markdown_cell(category.get("label", category.get("category"))),
                        percent=markdown_cell(category.get("percent")),
                        earned=markdown_cell(category.get("earned")),
                        maximum=markdown_cell(category.get("max")),
                        passed=markdown_cell(category.get("passed", category.get("pass_count"))),
                        partial=markdown_cell(category.get("partial", category.get("partial_count"))),
                        failed=markdown_cell(category.get("failed", category.get("fail_count"))),
                    )
                )
    else:
        lines.append("- Quality benchmark did not complete.")

    lines.extend(["", "## Performance — Coding-Agent Workload", ""])
    if rows:
        lines.extend(
            [
                "| Context depth | Concurrency | Aggregate tg t/s | Per-agent tg t/s | TTFT (ms) | pp t/s |",
                "|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for row in rows:
            lines.append(
                "| {depth:,} | {concurrency} | {tg} | {per_agent} | {ttft} | {pp} |".format(
                    depth=row["depth"],
                    concurrency=row["concurrency"],
                    tg=markdown_cell(row["tg_tps"]),
                    per_agent=markdown_cell(row["per_agent_tg_tps"]),
                    ttft=markdown_cell(row["ttft_ms"]),
                    pp=markdown_cell(row["pp_tps"]),
                )
            )
        lines.append("")
        lines.append("At concurrency 2, aggregate throughput is server-wide; per-agent tg t/s is the responsiveness metric for each coding agent.")
    else:
        lines.append("- Performance benchmark did not complete.")

    lines.extend(["", "## Invocation", ""])
    for command in commands if isinstance(commands, list) else []:
        if not isinstance(command, dict):
            continue
        lines.extend(
            [
                f"### {markdown_cell(command.get('name'))}",
                "",
                "```sh",
                command_text(command.get("argv")),
                "```",
                "",
                f"Exit status: `{markdown_cell(command.get('returncode'))}`",
                "",
            ]
        )

    lines.extend(
        [
            "## Reproducibility Notes",
            "",
            "`run.json` is the canonical immutable record. It includes sanitized effective container configuration, tool versions, command outcomes, GPU snapshots, and raw benchmark results.",
            "",
        ]
    )
    return "\n".join(lines)


def summary_row(run: dict[str, Any], path: Path) -> dict[str, Any]:
    quality = quality_summary(run)
    rows = performance_rows(run)
    metrics: dict[str, Any] = {}
    for row in rows:
        if row["depth"] in (0, 8192, 32768) and row["concurrency"] in (1, 2):
            metrics[f"d{row['depth']}_c{row['concurrency']}_tg_tps"] = row["tg_tps"]
            metrics[f"d{row['depth']}_c{row['concurrency']}_per_agent_tg_tps"] = row["per_agent_tg_tps"]
    return {
        "run_id": run.get("run_id"),
        "status": run.get("status"),
        "started_at": run.get("started_at"),
        "protocol": run.get("protocol"),
        "comparison_key": run.get("comparison_key"),
        "model": value_at(run, "model", "hf_repository", default="unknown"),
        "served_model": value_at(run, "model", "served_name", default="unknown"),
        "engine": value_at(run, "stack", "engine", default="unknown"),
        "quality_score": quality.get("score"),
        "completion_rate": quality.get("completion_rate"),
        "safety_warnings": len(quality.get("safety_warnings") or []),
        "report": str(path.parent.relative_to(BENCHMARKS) / "report.md"),
        **metrics,
    }


def render_index(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Benchmark Run Index",
        "",
        "Generated from immutable `benchmarks/runs/**/run.json` records. Scores are only directly comparable when their protocol and comparison key match.",
        "",
        "| Date | Model | Engine | Quality | Completion | Safety warnings | d0 c1 | d0 c2 / agent | d8K c1 | d8K c2 / agent | d32K c1 | d32K c2 / agent | Report |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    if not rows:
        lines.append("| — | _No benchmark runs recorded yet_ | — | — | — | — | — | — | — | — | — | — | — |")
    for row in rows:
        date = markdown_cell(row.get("started_at"))
        c2_0 = " / ".join(
            markdown_cell(row.get(key))
            for key in ("d0_c2_tg_tps", "d0_c2_per_agent_tg_tps")
        )
        c2_8 = " / ".join(
            markdown_cell(row.get(key))
            for key in ("d8192_c2_tg_tps", "d8192_c2_per_agent_tg_tps")
        )
        c2_32 = " / ".join(
            markdown_cell(row.get(key))
            for key in ("d32768_c2_tg_tps", "d32768_c2_per_agent_tg_tps")
        )
        lines.append(
            "| {date} | `{model}` | `{engine}` | {quality} | {completion} | {safety} | {d0c1} | {d0c2} | {d8c1} | {d8c2} | {d32c1} | {d32c2} | [{run_id}]({report}) |".format(
                date=date,
                model=markdown_cell(row.get("model")),
                engine=markdown_cell(row.get("engine")),
                quality=markdown_cell(row.get("quality_score")),
                completion=markdown_cell(row.get("completion_rate")),
                safety=markdown_cell(row.get("safety_warnings")),
                d0c1=markdown_cell(row.get("d0_c1_tg_tps")),
                d0c2=c2_0,
                d8c1=markdown_cell(row.get("d8192_c1_tg_tps")),
                d8c2=c2_8,
                d32c1=markdown_cell(row.get("d32768_c1_tg_tps")),
                d32c2=c2_32,
                run_id=markdown_cell(row.get("run_id")),
                report=markdown_cell(row.get("report")),
            )
        )
    lines.append("")
    return "\n".join(lines)


def build_index() -> None:
    run_paths = sorted((BENCHMARKS / "runs").glob("**/run.json"))
    rows: list[dict[str, Any]] = []
    for path in run_paths:
        try:
            rows.append(summary_row(read_json(path), path))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"warning: skipping {path}: {exc}")
    rows.sort(key=lambda row: str(row.get("started_at") or ""), reverse=True)
    write_text(BENCHMARKS / "INDEX.md", render_index(rows))
    write_text(
        BENCHMARKS / "index.json",
        json.dumps({"schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(), "runs": rows}, indent=2) + "\n",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, help="render report.md for this run.json")
    parser.add_argument("--index", action="store_true", help="rebuild benchmarks/INDEX.md and index.json")
    args = parser.parse_args()
    if not args.report and not args.index:
        parser.error("choose --report and/or --index")
    if args.report:
        run = read_json(args.report)
        write_text(args.report.with_name("report.md"), render_report(run, args.report))
    if args.index:
        build_index()


if __name__ == "__main__":
    main()
