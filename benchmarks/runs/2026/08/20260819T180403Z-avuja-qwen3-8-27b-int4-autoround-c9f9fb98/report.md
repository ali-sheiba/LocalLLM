# Benchmark Run — Avuja/Qwen3.8-27B-int4-AutoRound

- **Run ID:** `20260819T180403Z-avuja-qwen3-8-27b-int4-autoround-c9f9fb98`
- **Status:** `completed`
- **Started:** `2026-08-19T18:04:03.191593+00:00`
- **Finished:** `2026-08-19T18:19:53.620777+00:00`
- **Protocol:** `tool-eval-69-perf-v1`
- **Comparison key:** `Avuja/Qwen3.8-27B-int4-AutoRound\|tool-eval-69-perf-v1\|NVIDIA GeForce RTX 3090,NVIDIA GeForce RTX 3090`

## Model and Stack

| Field | Value |
|---|---|
| Hugging Face source | `Avuja/Qwen3.8-27B-int4-AutoRound` |
| Host model path | `/home/app/models/Avuja/Qwen3.8-27B-int4-AutoRound` |
| Served model name | `qwen3.8-27b` |
| Engine | `auto-detected` |
| Compose file | `models/qwen3.8-27b/autoround-int4/docker-compose.yml` |
| Compose SHA-256 | `bcfa28eff60a44d7a487a826bd8c469f42964d691fe38375c8f40f666688ddbc` |
| Compose environment file | `models/qwen3.8-27b/autoround-int4/profiles/avuja.env` |
| Environment SHA-256 | `d2569b7b94bee82a7e327291c49cef22b7741cd72850387fa33c39f760cc0559` |
| Container image | `vllm/vllm-openai:v0.27.1` |
| Image digest | `vllm/vllm-openai@sha256:0a51ea5b4ae2dc5d81890e5173f54203d2a3ae0cfffe51b8fd2afd4391bfd967` |

## GPU Power Policy

- **Management:** `local`
- **Requested limit:** `350 W`
- **Restore status:** `succeeded`

| GPU | Original limit | Applied limit | Restored limit |
|---|---:|---:|---:|
| 0 | 230.00 W | 350 W | 230.00 W |
| 1 | 230.00 W | 350 W | 230.00 W |

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
| Error Recovery | 100 | 6 | 6 | 3 / 0 / 0 |
| Localization | 100 | 6 | 6 | 3 / 0 / 0 |
| Structured Reasoning | 100 | 6 | 6 | 3 / 0 / 0 |
| Instruction Following | 100 | 10 | 10 | 5 / 0 / 0 |
| Context & State | 80 | 16 | 20 | 7 / 2 / 1 |
| Code Patterns | 67 | 4 | 6 | 2 / 0 / 1 |
| Safety & Boundaries | 81 | 21 | 26 | 9 / 3 / 1 |
| Toolset Scale | 100 | 8 | 8 | 4 / 0 / 0 |
| Autonomous Planning | 83 | 5 | 6 | 2 / 1 / 0 |
| Creative Composition | 100 | 6 | 6 | 3 / 0 / 0 |
| Structured Output | 83 | 10 | 12 | 5 / 0 / 1 |

## Performance — Coding-Agent Workload

| Context depth | Concurrency | Aggregate tg t/s | Per-agent tg t/s | TTFT (ms) | pp t/s |
|---:|---:|---:|---:|---:|---:|
| 0 | 1 | 68.73 | 68.73 | 1137.03 | 1949.99 |
| 0 | 2 | 77.21 | 38.61 | 1715.22 | 1801.24 |
| 8,192 | 1 | 62.33 | 62.33 | 6338.96 | 1638.98 |
| 8,192 | 2 | 29.23 | 14.61 | 9521.61 | 1617.09 |
| 32,768 | 1 | 49.32 | 49.32 | 28254.85 | 1236.43 |
| 32,768 | 2 | 9.20 | 4.60 | 44084.65 | 1235.52 |

At concurrency 2, aggregate throughput is server-wide; per-agent tg t/s is the responsiveness metric for each coding agent.

## Invocation

### llama-benchy

```sh
uv run --extra perf llama-benchy --base-url http://localhost:8080/v1 --model qwen3.8-27b --pp 2048 --tg 128 --depth 0 8192 32768 --concurrency 1 2 --runs 3 --latency-mode generation --no-cache --skip-coherence --no-adapt-prompt --format json --save-result /tmp/localllm-bench-xmu4_8xh/performance.json --tokenizer /home/app/models/Avuja/Qwen3.8-27B-int4-AutoRound
```

Exit status: `0`

### tool-eval-bench

```sh
uv run --extra perf tool-eval-bench run --seed 42 --base-url http://localhost:8080 --model qwen3.8-27b --json-file /tmp/localllm-bench-xmu4_8xh/quality.json --output-dir /tmp/localllm-bench-xmu4_8xh/upstream-reports --no-live
```

Exit status: `0`

## Reproducibility Notes

`run.json` is the canonical immutable record. It includes sanitized effective container configuration, tool versions, command outcomes, GPU snapshots, and raw benchmark results.
