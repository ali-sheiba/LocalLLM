# Benchmark Run — Qwen/Qwen3.8-27B-FP8

- **Run ID:** `20260820T115256Z-qwen-qwen3-8-27b-fp8-0041b65d`
- **Status:** `completed`
- **Started:** `2026-08-20T11:47:15.334749+00:00`
- **Finished:** `2026-08-20T12:13:01.957541+00:00`
- **Protocol:** `tool-eval-69-perf-v1`
- **Comparison key:** `Qwen/Qwen3.8-27B-FP8\|tool-eval-69-perf-v1\|NVIDIA GeForce RTX 3090,NVIDIA GeForce RTX 3090`

## Model and Stack

| Field | Value |
|---|---|
| Hugging Face source | `Qwen/Qwen3.8-27B-FP8` |
| Host model path | `/home/app/models/Qwen/Qwen3.8-27B-FP8` |
| Served model name | `qwen3.8-27b` |
| Engine | `auto-detected` |
| Compose file | `models/qwen3.8-27b/fp8/docker-compose.yml` |
| Compose SHA-256 | `35fdf96c3fa51372fa1f400c5e38d424ac6f94385bd8fedf3f8d3bc19fa26e2a` |
| Benchmark profile | `—` |
| Compose environment file | `—` |
| Environment SHA-256 | `—` |
| Container image | `vllm/vllm-openai:v0.27.1` |
| Image digest | `vllm/vllm-openai@sha256:0a51ea5b4ae2dc5d81890e5173f54203d2a3ae0cfffe51b8fd2afd4391bfd967` |

## GPU Power Policy

- No power limit was changed for this run.

## Hardware

| GPU | Name | Power limit | Memory | PCIe capability |
|---:|---|---:|---:|---|
| 0 | NVIDIA GeForce RTX 3090 | 350.00 W | 24576 MiB | Gen 4 ×16 |
| 1 | NVIDIA GeForce RTX 3090 | 350.00 W | 24576 MiB | Gen 4 ×16 |

## Tool-Calling Quality

- **Final score:** 87
- **Rating:** ★★★★ Good
- **Completion rate:** —
- **Safety warnings:** 0
- **Excluded scenarios:** 0

| Category | Score | Earned | Max | Pass / Partial / Fail |
|---|---:|---:|---:|---|
| Tool Selection | 67 | 4 | 6 | 2 / 0 / 1 |
| Parameter Precision | 100 | 6 | 6 | 3 / 0 / 0 |
| Multi-Step Chains | 75 | 6 | 8 | 3 / 0 / 1 |
| Restraint & Refusal | 100 | 6 | 6 | 3 / 0 / 0 |
| Error Recovery | 83 | 5 | 6 | 2 / 1 / 0 |
| Localization | 100 | 6 | 6 | 3 / 0 / 0 |
| Structured Reasoning | 100 | 6 | 6 | 3 / 0 / 0 |
| Instruction Following | 100 | 10 | 10 | 5 / 0 / 0 |
| Context & State | 70 | 14 | 20 | 6 / 2 / 2 |
| Code Patterns | 100 | 6 | 6 | 3 / 0 / 0 |
| Safety & Boundaries | 85 | 22 | 26 | 9 / 4 / 0 |
| Toolset Scale | 100 | 8 | 8 | 4 / 0 / 0 |
| Autonomous Planning | 67 | 4 | 6 | 1 / 2 / 0 |
| Creative Composition | 100 | 6 | 6 | 3 / 0 / 0 |
| Structured Output | 92 | 11 | 12 | 5 / 1 / 0 |

## Performance — Coding-Agent Workload

| Context depth | Concurrency | Aggregate tg t/s | Per-agent tg t/s | TTFT (ms) | pp t/s |
|---:|---:|---:|---:|---:|---:|
| 0 | 1 | 60.86 | 60.86 | 1569.94 | 1280.70 |
| 0 | 2 | 77.11 | 38.56 | 2613.65 | 1167.20 |
| 8,192 | 1 | 39.59 | 39.59 | 8284.33 | 1148.30 |
| 8,192 | 2 | 21.66 | 10.83 | 12316.11 | 1138.45 |
| 32,768 | 1 | 20.85 | 20.85 | 33436.18 | 946.04 |
| 32,768 | 2 | 6.43 | 3.21 | 50599.57 | 943.61 |

At concurrency 2, aggregate throughput is server-wide; per-agent tg t/s is the responsiveness metric for each coding agent.

## Invocation

### llama-benchy

```sh
/home/app/.local/bin/uv run --extra perf llama-benchy --base-url http://localhost:8080/v1 --model qwen3.8-27b --pp 2048 --tg 128 --depth 0 8192 32768 --concurrency 1 2 --runs 3 --latency-mode generation --no-cache --skip-coherence --no-adapt-prompt --format json --save-result /tmp/localllm-bench-py2xaf63/performance.json
```

Exit status: `0`

### tool-eval-bench

```sh
/home/app/.local/bin/uv run --extra perf tool-eval-bench run --seed 42 --base-url http://localhost:8080 --model qwen3.8-27b --json-file /tmp/localllm-bench-py2xaf63/quality.json --output-dir /tmp/localllm-bench-py2xaf63/upstream-reports --no-live
```

Exit status: `0`

## Reproducibility Notes

`run.json` is the canonical immutable record. It includes sanitized effective container configuration, tool versions, command outcomes, GPU snapshots, and raw benchmark results.
