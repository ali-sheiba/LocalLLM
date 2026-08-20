# Benchmark Run — Lorbus/Qwen3.6-27B-int4-AutoRound

- **Run ID:** `20260820T113142Z-lorbus-qwen3-6-27b-int4-autoround-f4faf298`
- **Status:** `completed`
- **Started:** `2026-08-20T11:27:36.408422+00:00`
- **Finished:** `2026-08-20T11:45:33.640091+00:00`
- **Protocol:** `tool-eval-69-perf-v1`
- **Comparison key:** `Lorbus/Qwen3.6-27B-int4-AutoRound\|tool-eval-69-perf-v1\|NVIDIA GeForce RTX 3090,NVIDIA GeForce RTX 3090`

## Model and Stack

| Field | Value |
|---|---|
| Hugging Face source | `Lorbus/Qwen3.6-27B-int4-AutoRound` |
| Host model path | `/home/app/models/Lorbus/Qwen3.6-27B-int4-AutoRound` |
| Served model name | `qwen3.6-27b` |
| Engine | `auto-detected` |
| Compose file | `models/qwen3.6-27b/autoround-int4/docker-compose.yml` |
| Compose SHA-256 | `ad724c9e128f00c9f0dd23af3da839feffddd1a35fb3d81770cadcff757c1721` |
| Benchmark profile | `—` |
| Compose environment file | `—` |
| Environment SHA-256 | `—` |
| Container image | `vllm/vllm-openai:v0.25.1` |
| Image digest | `vllm/vllm-openai@sha256:e4f88a835143cd22aee2397a26ec6bb80b3a4a6fe0c882bcbc63822904766089` |

## GPU Power Policy

- No power limit was changed for this run.

## Hardware

| GPU | Name | Power limit | Memory | PCIe capability |
|---:|---|---:|---:|---|
| 0 | NVIDIA GeForce RTX 3090 | 350.00 W | 24576 MiB | Gen 4 ×16 |
| 1 | NVIDIA GeForce RTX 3090 | 350.00 W | 24576 MiB | Gen 4 ×16 |

## Tool-Calling Quality

- **Final score:** 91
- **Rating:** ★★★★★ Excellent
- **Completion rate:** —
- **Safety warnings:** 1
- **Excluded scenarios:** 0

| Category | Score | Earned | Max | Pass / Partial / Fail |
|---|---:|---:|---:|---|
| Tool Selection | 100 | 6 | 6 | 3 / 0 / 0 |
| Parameter Precision | 100 | 6 | 6 | 3 / 0 / 0 |
| Multi-Step Chains | 100 | 8 | 8 | 4 / 0 / 0 |
| Restraint & Refusal | 67 | 4 | 6 | 2 / 0 / 1 |
| Error Recovery | 83 | 5 | 6 | 2 / 1 / 0 |
| Localization | 100 | 6 | 6 | 3 / 0 / 0 |
| Structured Reasoning | 100 | 6 | 6 | 3 / 0 / 0 |
| Instruction Following | 100 | 10 | 10 | 5 / 0 / 0 |
| Context & State | 80 | 16 | 20 | 7 / 2 / 1 |
| Code Patterns | 83 | 5 | 6 | 2 / 1 / 0 |
| Safety & Boundaries | 88 | 23 | 26 | 11 / 1 / 1 |
| Toolset Scale | 100 | 8 | 8 | 4 / 0 / 0 |
| Autonomous Planning | 67 | 4 | 6 | 1 / 2 / 0 |
| Creative Composition | 100 | 6 | 6 | 3 / 0 / 0 |
| Structured Output | 100 | 12 | 12 | 6 / 0 / 0 |

## Performance — Coding-Agent Workload

| Context depth | Concurrency | Aggregate tg t/s | Per-agent tg t/s | TTFT (ms) | pp t/s |
|---:|---:|---:|---:|---:|---:|
| 0 | 1 | 74.02 | 74.02 | 1389.78 | 1432.68 |
| 0 | 2 | 142.24 | 71.12 | 2732.72 | 1379.68 |
| 8,192 | 1 | 70.37 | 70.37 | 6818.65 | 1376.84 |
| 8,192 | 2 | 28.83 | 14.41 | 10210.58 | 1365.40 |
| 32,768 | 1 | 65.44 | 65.44 | 24397.71 | 1294.80 |
| 32,768 | 2 | 12.30 | 6.15 | 39423.97 | 1291.78 |

At concurrency 2, aggregate throughput is server-wide; per-agent tg t/s is the responsiveness metric for each coding agent.

## Invocation

### llama-benchy

```sh
/home/app/.local/bin/uv run --extra perf llama-benchy --base-url http://localhost:8080/v1 --model qwen3.6-27b --pp 2048 --tg 128 --depth 0 8192 32768 --concurrency 1 2 --runs 3 --latency-mode generation --no-cache --skip-coherence --no-adapt-prompt --format json --save-result /tmp/localllm-bench-p6jhso35/performance.json
```

Exit status: `0`

### tool-eval-bench

```sh
/home/app/.local/bin/uv run --extra perf tool-eval-bench run --seed 42 --base-url http://localhost:8080 --model qwen3.6-27b --json-file /tmp/localllm-bench-p6jhso35/quality.json --output-dir /tmp/localllm-bench-p6jhso35/upstream-reports --no-live
```

Exit status: `0`

## Reproducibility Notes

`run.json` is the canonical immutable record. It includes sanitized effective container configuration, tool versions, command outcomes, GPU snapshots, and raw benchmark results.
