# Benchmark Run — Qwen/Qwen3.6-27B-FP8

- **Run ID:** `20260819T081437Z-qwen-qwen3-6-27b-fp8-dc1824cf`
- **Status:** `completed`
- **Started:** `2026-08-19T08:14:37.346200+00:00`
- **Finished:** `2026-08-19T08:32:17.363419+00:00`
- **Protocol:** `tool-eval-69-perf-v1`
- **Comparison key:** `Qwen/Qwen3.6-27B-FP8\|tool-eval-69-perf-v1\|NVIDIA GeForce RTX 3090,NVIDIA GeForce RTX 3090`

## Model and Stack

| Field | Value |
|---|---|
| Hugging Face source | `Qwen/Qwen3.6-27B-FP8` |
| Host model path | `/home/app/models/Qwen/Qwen3.6-27B-FP8` |
| Served model name | `qwen3.8-27b` |
| Engine | `auto-detected` |
| Compose file | `models/qwen3.6-27b/fp8/docker-compose.yml` |
| Compose SHA-256 | `77288721a0f592d8ae93b997f7395dc3d4151d6760cbb18572f0570771b957b7` |
| Container image | `vllm/vllm-openai:latest` |
| Image digest | `vllm/vllm-openai@sha256:0a51ea5b4ae2dc5d81890e5173f54203d2a3ae0cfffe51b8fd2afd4391bfd967` |

## GPU Power Policy

- No power limit was changed for this run.

## Hardware

| GPU | Name | Power limit | Memory | PCIe |
|---:|---|---:|---:|---|
| 0 | NVIDIA GeForce RTX 3090 | 230.00 W | 24576 MiB | Gen 1 ×16 |
| 1 | NVIDIA GeForce RTX 3090 | 230.00 W | 24576 MiB | Gen 1 ×16 |

## Tool-Calling Quality

- **Final score:** 88
- **Rating:** ★★★★ Good
- **Completion rate:** —
- **Safety warnings:** 1
- **Excluded scenarios:** 0

| Category | Score | Earned | Max | Pass / Partial / Fail |
|---|---:|---:|---:|---|
| Tool Selection | 100 | 6 | 6 | 3 / 0 / 0 |
| Parameter Precision | 100 | 6 | 6 | 3 / 0 / 0 |
| Multi-Step Chains | 75 | 6 | 8 | 3 / 0 / 1 |
| Restraint & Refusal | 100 | 6 | 6 | 3 / 0 / 0 |
| Error Recovery | 83 | 5 | 6 | 2 / 1 / 0 |
| Localization | 100 | 6 | 6 | 3 / 0 / 0 |
| Structured Reasoning | 67 | 4 | 6 | 2 / 0 / 1 |
| Instruction Following | 100 | 10 | 10 | 5 / 0 / 0 |
| Context & State | 85 | 17 | 20 | 7 / 3 / 0 |
| Code Patterns | 100 | 6 | 6 | 3 / 0 / 0 |
| Safety & Boundaries | 81 | 21 | 26 | 9 / 3 / 1 |
| Toolset Scale | 100 | 8 | 8 | 4 / 0 / 0 |
| Autonomous Planning | 67 | 4 | 6 | 1 / 2 / 0 |
| Creative Composition | 100 | 6 | 6 | 3 / 0 / 0 |
| Structured Output | 92 | 11 | 12 | 5 / 1 / 0 |

## Performance — Coding-Agent Workload

| Context depth | Concurrency | Aggregate tg t/s | Per-agent tg t/s | TTFT (ms) | pp t/s |
|---:|---:|---:|---:|---:|---:|
| 0 | 1 | 64.79 | 64.79 | 1140.85 | 1768.87 |
| 0 | 2 | 73.66 | 36.83 | 1785.40 | 1609.78 |
| 8,192 | 1 | 58.77 | 58.77 | 6432.48 | 1476.06 |
| 8,192 | 2 | 28.29 | 14.15 | 9773.11 | 1437.19 |
| 32,768 | 1 | 47.14 | 47.14 | 28414.86 | 1113.58 |
| 32,768 | 2 | 8.29 | 4.14 | 42898.94 | 1110.33 |

At concurrency 2, aggregate throughput is server-wide; per-agent tg t/s is the responsiveness metric for each coding agent.

## Invocation

### llama-benchy

```sh
uv run --extra perf llama-benchy --base-url http://localhost:8080/v1 --model qwen3.8-27b --pp 2048 --tg 128 --depth 0 8192 32768 --concurrency 1 2 --runs 3 --latency-mode generation --no-cache --skip-coherence --no-adapt-prompt --format json --save-result /tmp/localllm-bench-tgpl_fv4/performance.json
```

Exit status: `0`

### tool-eval-bench

```sh
uv run --extra perf tool-eval-bench run --seed 42 --base-url http://localhost:8080 --model qwen3.8-27b --json-file /tmp/localllm-bench-tgpl_fv4/quality.json --output-dir /tmp/localllm-bench-tgpl_fv4/upstream-reports --no-live
```

Exit status: `0`

## Reproducibility Notes

`run.json` is the canonical immutable record. It includes sanitized effective container configuration, tool versions, command outcomes, GPU snapshots, and raw benchmark results.
