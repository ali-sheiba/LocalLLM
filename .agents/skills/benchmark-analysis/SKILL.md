---
name: benchmark-analysis
description: Compare immutable LocalLLM benchmark runs by validating experimental equivalence, analyzing quality and depth-specific performance metrics, and writing evidence-based comparison reports.
---

# Benchmark Analysis

Use this skill when asked to compare or summarize LocalLLM benchmark results.

## Run layout and outputs

- Treat each run as immutable input at `benchmarks/runs/<year>/<month>/<run-id>/`.
- A valid run directory contains exactly these canonical artifacts:
  - `report.md`
  - `run.json`
- Use `run.json` as the canonical structured record and `report.md` for its human-readable results and context.
- Write newly requested comparison artifacts under `benchmarks/comparisons/`; do not place comparison files in a run directory.
- Never modify, rename, delete, or regenerate artifacts in `benchmarks/runs/`.

## Establish comparability first

Before drawing a conclusion, inspect each candidate run and explicitly validate whether these are aligned:

1. Benchmark protocol: task set/version, evaluator and scoring rules, prompts, repetitions, and concurrency.
2. Model: model identity, revision, quantization, chat template, reasoning/tool settings, and inference engine version.
3. Configuration: context limits, sampling parameters, batching, speculative decoding, cache settings, and other inference flags.
4. Hardware: GPU model/count, topology, CPU/RAM where relevant, drivers, CUDA/runtime, and container/image version.
5. Power conditions: power limits, clocks/performance mode, thermal state, and any other recorded power-management settings.

If any required setting is missing or differs, label the comparison as partially comparable or non-comparable. State the limitation prominently and restrict conclusions to the evidence available.

## Metrics to analyze

For comparable runs, report both absolute values and deltas for:

- Overall tool-eval score.
- Completion score, safety score, and each reported category score.
- Performance at both `c1` and `c2` depths `0`, `8192`, and `32768`.
- At every `c2` depth, per-agent tokens per second (t/s), alongside aggregate performance where available.

Use consistent units and identify whether a higher or lower value is better. Do not substitute aggregate throughput for per-agent `c2` t/s.

## Interpret results responsibly

- Identify material configuration differences between runs, including settings that could plausibly affect quality, latency, or throughput.
- Describe differences as associations or hypotheses, not proven causes, unless the benchmark design isolates the changed variable under otherwise equivalent conditions.
- Separate measured facts, calculated deltas, and interpretation in the comparison report.
- Call out tradeoffs: for example, a quality gain accompanied by a safety, latency, or per-agent throughput regression.
- If data is absent, say so rather than estimating or silently omitting the metric.

## Comparison report structure

Create a concise report under `benchmarks/comparisons/` that includes:

1. Runs compared, with their paths and identifiers.
2. Comparability verdict and the protocol/model/config/hardware/power checks.
3. A metric table covering quality scores and the required `c1`/`c2` depths.
4. Configuration differences.
5. Evidence-based findings, caveats, and a recommendation only when supported by comparable results.
