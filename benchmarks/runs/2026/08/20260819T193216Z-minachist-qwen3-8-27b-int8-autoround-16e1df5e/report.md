# Benchmark Run — Minachist/Qwen3.8-27B-INT8-AutoRound

- **Run ID:** `20260819T193216Z-minachist-qwen3-8-27b-int8-autoround-16e1df5e`
- **Status:** `completed`
- **Started:** `2026-08-19T19:26:50.729639+00:00`
- **Finished:** `2026-08-19T19:51:07.522942+00:00`
- **Protocol:** `tool-eval-69-perf-v1`
- **Comparison key:** `Minachist/Qwen3.8-27B-INT8-AutoRound\|tool-eval-69-perf-v1\|NVIDIA GeForce RTX 3090,NVIDIA GeForce RTX 3090`

## Model and Stack

| Field | Value |
|---|---|
| Hugging Face source | `Minachist/Qwen3.8-27B-INT8-AutoRound` |
| Host model path | `/home/app/models/Minachist/Qwen3.8-27B-INT8-AutoRound` |
| Served model name | `qwen3.8-27b` |
| Engine | `auto-detected` |
| Compose file | `models/qwen3.8-27b/autoround-int4/docker-compose.yml` |
| Compose SHA-256 | `bcfa28eff60a44d7a487a826bd8c469f42964d691fe38375c8f40f666688ddbc` |
| Compose environment file | `models/qwen3.8-27b/autoround-int4/profiles/minachist.env` |
| Environment SHA-256 | `b396ba9cfdc8a6fec2d48fd04f649547ee99e5246992893e259a718e946464b6` |
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
| Tool Selection | 67 | 4 | 6 | 2 / 0 / 1 |
| Parameter Precision | 100 | 6 | 6 | 3 / 0 / 0 |
| Multi-Step Chains | 75 | 6 | 8 | 3 / 0 / 1 |
| Restraint & Refusal | 100 | 6 | 6 | 3 / 0 / 0 |
| Error Recovery | 83 | 5 | 6 | 2 / 1 / 0 |
| Localization | 100 | 6 | 6 | 3 / 0 / 0 |
| Structured Reasoning | 100 | 6 | 6 | 3 / 0 / 0 |
| Instruction Following | 90 | 9 | 10 | 4 / 1 / 0 |
| Context & State | 70 | 14 | 20 | 5 / 4 / 1 |
| Code Patterns | 100 | 6 | 6 | 3 / 0 / 0 |
| Safety & Boundaries | 85 | 22 | 26 | 10 / 2 / 1 |
| Toolset Scale | 100 | 8 | 8 | 4 / 0 / 0 |
| Autonomous Planning | 83 | 5 | 6 | 2 / 1 / 0 |
| Creative Composition | 100 | 6 | 6 | 3 / 0 / 0 |
| Structured Output | 100 | 12 | 12 | 6 / 0 / 0 |

## Performance — Coding-Agent Workload

| Context depth | Concurrency | Aggregate tg t/s | Per-agent tg t/s | TTFT (ms) | pp t/s |
|---:|---:|---:|---:|---:|---:|
| 0 | 1 | 46.89 | 46.89 | 1227.10 | 1792.55 |
| 0 | 2 | 59.74 | 29.87 | 1855.74 | 1663.62 |
| 8,192 | 1 | 43.81 | 43.81 | 6416.45 | 1618.19 |
| 8,192 | 2 | 26.40 | 13.20 | 9619.75 | 1600.71 |
| 32,768 | 1 | 36.87 | 36.87 | 28211.37 | 1238.21 |
| 32,768 | 2 | 8.94 | 4.47 | 43886.82 | 1240.57 |

At concurrency 2, aggregate throughput is server-wide; per-agent tg t/s is the responsiveness metric for each coding agent.

## Invocation

### llama-benchy

```sh
uv run --extra perf llama-benchy --base-url http://localhost:8080/v1 --model qwen3.8-27b --pp 2048 --tg 128 --depth 0 8192 32768 --concurrency 1 2 --runs 3 --latency-mode generation --no-cache --skip-coherence --no-adapt-prompt --format json --save-result /tmp/localllm-bench-2srxb2ij/performance.json --tokenizer /home/app/models/Minachist/Qwen3.8-27B-INT8-AutoRound
```

Exit status: `0`

### tool-eval-bench

```sh
uv run --extra perf tool-eval-bench run --seed 42 --base-url http://localhost:8080 --model qwen3.8-27b --json-file /tmp/localllm-bench-2srxb2ij/quality.json --output-dir /tmp/localllm-bench-2srxb2ij/upstream-reports --no-live
```

Exit status: `0`

## Reproducibility Notes

`run.json` is the canonical immutable record. It includes sanitized effective container configuration, tool versions, command outcomes, GPU snapshots, and raw benchmark results.
