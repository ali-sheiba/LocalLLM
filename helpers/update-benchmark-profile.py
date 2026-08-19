#!/usr/bin/env python3
"""Update a benchmark profile's comment-only summary from an immutable run.json.

Profiles under models/**/profiles/*.env contain ordinary Compose environment
assignments plus a BENCHMARK_SUMMARY block. This helper replaces only that
comment block; the benchmark run remains the canonical source of evidence.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
START = "# BENCHMARK_SUMMARY_BEGIN"
END = "# BENCHMARK_SUMMARY_END"
DEPTHS = (0, 8192, 32768)


def resolve_path(value: Path) -> Path:
    path = value.expanduser()
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve()


def read_run(path: Path) -> dict[str, Any]:
    run_path = path / "run.json" if path.is_dir() else path
    if not run_path.is_file():
        raise ValueError(f"Run JSON does not exist: {run_path}")
    with run_path.open(encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object in {run_path}")
    return data


def number(value: Any) -> float | None:
    candidate = value.get("mean") if isinstance(value, dict) else value
    try:
        return float(candidate) if candidate is not None else None
    except (TypeError, ValueError):
        return None


def display(value: Any) -> str:
    if value is None or value == "":
        return "—"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def quality_summary(run: dict[str, Any]) -> tuple[Any, Any, int]:
    raw = run.get("results", {}).get("quality", {})
    if not isinstance(raw, dict):
        return None, None, 0
    scores = raw.get("scores", {})
    if not isinstance(scores, dict):
        scores = {}
    warnings = raw.get("safety_warnings", scores.get("safety_warnings", []))
    warning_count = len(warnings) if isinstance(warnings, list) else int(warnings or 0)
    return (
        raw.get("final_score", scores.get("final_score")),
        raw.get("completion_rate", scores.get("completion_rate")),
        warning_count,
    )


def performance_summary(run: dict[str, Any], concurrency: int) -> str:
    raw = run.get("results", {}).get("performance", {})
    benchmarks = raw.get("benchmarks", []) if isinstance(raw, dict) else []
    points: dict[int, tuple[float | None, float | None]] = {}
    for entry in benchmarks:
        if not isinstance(entry, dict):
            continue
        if int(entry.get("concurrency", 0) or 0) != concurrency:
            continue
        depth = int(entry.get("context_size", 0) or 0)
        throughput = number(entry.get("tg_throughput"))
        per_agent = throughput / concurrency if throughput is not None else None
        points[depth] = (throughput, per_agent)

    rendered: list[str] = []
    for depth in DEPTHS:
        aggregate, per_agent = points.get(depth, (None, None))
        label = "0" if depth == 0 else f"{depth // 1024}K"
        if concurrency == 1:
            rendered.append(f"{label}={display(aggregate)}")
        else:
            rendered.append(f"{label}={display(aggregate)} aggregate / {display(per_agent)} per-agent")
    return ", ".join(rendered) + " tg tok/s"


def stored_manual_notes(block: str) -> list[str]:
    notes = []
    for line in block.splitlines():
        match = re.fullmatch(r"# Manual notes:\s*(.*)", line)
        if match and match.group(1).strip() and not match.group(1).strip().startswith("pending"):
            notes.append(match.group(1).strip())
    return notes


def comment(value: str) -> str:
    return " ".join(value.replace("\n", " ").split()).replace("#", "[hash]")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, type=Path, help="Version-controlled profile .env file")
    parser.add_argument("--run", required=True, type=Path, help="Benchmark run.json or its containing run directory")
    parser.add_argument("--manual-note", action="append", default=[], help="Manual long-session observation; may be repeated")
    parser.add_argument(
        "--allow-profile-mismatch",
        action="store_true",
        help="Allow updating a profile other than the --env-file recorded by the run",
    )
    args = parser.parse_args()

    profile = resolve_path(args.profile)
    if not profile.is_file():
        parser.error(f"Profile does not exist: {profile}")
    run = read_run(resolve_path(args.run))
    if run.get("status") != "completed":
        parser.error("Only a completed benchmark run may update a profile summary")

    stack = run.get("stack", {})
    environment = stack.get("environment_file") if isinstance(stack, dict) else None
    recorded_path: Path | None = None
    recorded_sha: Any = None
    if isinstance(environment, dict) and environment.get("path"):
        recorded_path = resolve_path(Path(str(environment["path"])))
        recorded_sha = environment.get("sha256")
    if recorded_path != profile and not args.allow_profile_mismatch:
        expected = str(recorded_path) if recorded_path else "no --env-file"
        parser.error(
            f"Run is attributed to {expected}, not {profile}. "
            "Use the matching profile or pass --allow-profile-mismatch deliberately."
        )

    content = profile.read_text(encoding="utf-8")
    start = content.find(START)
    end = content.find(END)
    if start < 0 or end < start:
        parser.error(f"Profile needs a {START} ... {END} comment block")
    end += len(END)
    previous = content[content.find("\n", start) + 1 : content.rfind("\n", start, end)]
    notes = [comment(note) for note in args.manual_note if comment(note)] or stored_manual_notes(previous)

    score, completion_rate, warning_count = quality_summary(run)
    run_id = display(run.get("run_id"))
    run_path = resolve_path(args.run)
    if run_path.is_file():
        run_path = run_path.parent
    relative_run = str(run_path.relative_to(ROOT)) if run_path.is_relative_to(ROOT) else str(run_path)
    launched_sha = display(recorded_sha)
    summary = [
        START,
        f"# Latest benchmark: {relative_run}/report.md (run {run_id})",
        f"# Profile SHA-256 at benchmark launch: {launched_sha}",
        f"# tool-eval-bench: score={display(score)}, completion={display(completion_rate)}, safety_warnings={warning_count}",
        f"# llama-benchy c1: {performance_summary(run, 1)}",
        f"# llama-benchy c2: {performance_summary(run, 2)}",
    ]
    if notes:
        summary.extend(f"# Manual notes: {note}" for note in notes)
    else:
        summary.append("# Manual notes: pending — test long coding sessions for loops, stalled calls, and malformed tool calls.")
    summary.append(END)
    updated = content[:start] + "\n".join(summary) + content[end:]
    profile.write_text(updated, encoding="utf-8")
    print(f"Updated {profile.relative_to(ROOT) if profile.is_relative_to(ROOT) else profile}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
