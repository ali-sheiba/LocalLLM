# Benchmark Run — goldhub/Qwen3.8-27B-INT4-W4A16-AutoRound

- **Run ID:** `20260819T190857Z-goldhub-qwen3-8-27b-int4-w4a16-autoround-48a57d75`
- **Status:** `completed`
- **Started:** `2026-08-19T19:03:31.635169+00:00`
- **Finished:** `2026-08-19T19:26:48.286539+00:00`
- **Protocol:** `tool-eval-69-perf-v1`
- **Comparison key:** `goldhub/Qwen3.8-27B-INT4-W4A16-AutoRound\|tool-eval-69-perf-v1\|NVIDIA GeForce RTX 3090,NVIDIA GeForce RTX 3090`

## Model and Stack

| Field | Value |
|---|---|
| Hugging Face source | `goldhub/Qwen3.8-27B-INT4-W4A16-AutoRound` |
| Host model path | `/home/app/models/goldhub/Qwen3.8-27B-INT4-W4A16-AutoRound` |
| Served model name | `qwen3.8-27b` |
| Engine | `auto-detected` |
| Compose file | `models/qwen3.8-27b/autoround-int4/docker-compose.yml` |
| Compose SHA-256 | `bcfa28eff60a44d7a487a826bd8c469f42964d691fe38375c8f40f666688ddbc` |
| Compose environment file | `models/qwen3.8-27b/autoround-int4/profiles/goldhub.env` |
| Environment SHA-256 | `27e8d69a902e5e1558b6ab2b13aa8c0be9c5b6ce857c0d9502d2eb9fb6ed693b` |
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

- **Final score:** 91
- **Rating:** ★★★★★ Excellent
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
| Structured Reasoning | 100 | 6 | 6 | 3 / 0 / 0 |
| Instruction Following | 100 | 10 | 10 | 5 / 0 / 0 |
| Context & State | 85 | 17 | 20 | 7 / 3 / 0 |
| Code Patterns | 100 | 6 | 6 | 3 / 0 / 0 |
| Safety & Boundaries | 81 | 21 | 26 | 9 / 3 / 1 |
| Toolset Scale | 100 | 8 | 8 | 4 / 0 / 0 |
| Autonomous Planning | 67 | 4 | 6 | 1 / 2 / 0 |
| Creative Composition | 100 | 6 | 6 | 3 / 0 / 0 |
| Structured Output | 100 | 12 | 12 | 6 / 0 / 0 |

## Performance — Coding-Agent Workload

| Context depth | Concurrency | Aggregate tg t/s | Per-agent tg t/s | TTFT (ms) | pp t/s |
|---:|---:|---:|---:|---:|---:|
| 0 | 1 | 50.11 | 50.11 | 1159.25 | 1912.95 |
| 0 | 2 | 62.47 | 31.23 | 1748.12 | 1765.47 |
| 8,192 | 1 | 46.64 | 46.64 | 6368.43 | 1631.80 |
| 8,192 | 2 | 26.85 | 13.43 | 9540.39 | 1613.65 |
| 32,768 | 1 | 38.90 | 38.90 | 28279.56 | 1235.44 |
| 32,768 | 2 | 8.96 | 4.48 | 44051.42 | 1236.35 |

At concurrency 2, aggregate throughput is server-wide; per-agent tg t/s is the responsiveness metric for each coding agent.

## Invocation

### llama-benchy

```sh
uv run --extra perf llama-benchy --base-url http://localhost:8080/v1 --model qwen3.8-27b --pp 2048 --tg 128 --depth 0 8192 32768 --concurrency 1 2 --runs 3 --latency-mode generation --no-cache --skip-coherence --no-adapt-prompt --format json --save-result /tmp/localllm-bench-uxzs4ypf/performance.json --tokenizer /home/app/models/goldhub/Qwen3.8-27B-INT4-W4A16-AutoRound
```

Exit status: `0`

### tool-eval-bench

```sh
uv run --extra perf tool-eval-bench run --seed 42 --base-url http://localhost:8080 --model qwen3.8-27b --json-file /tmp/localllm-bench-uxzs4ypf/quality.json --output-dir /tmp/localllm-bench-uxzs4ypf/upstream-reports --no-live
```

Exit status: `0`

## Reproducibility Notes

`run.json` is the canonical immutable record. It includes sanitized effective container configuration, tool versions, command outcomes, GPU snapshots, and raw benchmark results.
