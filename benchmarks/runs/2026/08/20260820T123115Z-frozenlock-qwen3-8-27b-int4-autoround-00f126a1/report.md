# Benchmark Run — Frozenlock/Qwen3.8-27B-int4-AutoRound

- **Run ID:** `20260820T123115Z-frozenlock-qwen3-8-27b-int4-autoround-00f126a1`
- **Status:** `completed`
- **Started:** `2026-08-20T12:26:04.951115+00:00`
- **Finished:** `2026-08-20T12:50:29.844458+00:00`
- **Protocol:** `tool-eval-69-perf-v1`
- **Comparison key:** `Frozenlock/Qwen3.8-27B-int4-AutoRound\|tool-eval-69-perf-v1\|NVIDIA GeForce RTX 3090,NVIDIA GeForce RTX 3090`

## Model and Stack

| Field | Value |
|---|---|
| Hugging Face source | `Frozenlock/Qwen3.8-27B-int4-AutoRound` |
| Host model path | `/home/app/models/Frozenlock/Qwen3.8-27B-int4-AutoRound` |
| Served model name | `qwen3.8-27b` |
| Engine | `auto-detected` |
| Compose file | `models/qwen3.8-27b/autoround-int4/docker-compose.yml` |
| Compose SHA-256 | `4443f62246704a186e5e8c42ccc675a5a4b8e81d32dfc0254b083f08b6dce93c` |
| Benchmark profile | `frozenlock.env` |
| Compose environment file | `models/qwen3.8-27b/autoround-int4/profiles/frozenlock.env` |
| Environment SHA-256 | `262ca569f4c0fe7dce7da25ee0c905cbbc0fda9b998048ce1c0b2e5d31f24371` |
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

- **Final score:** 91
- **Rating:** ★★★★★ Excellent
- **Completion rate:** —
- **Safety warnings:** 0
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
| Instruction Following | 90 | 9 | 10 | 4 / 1 / 0 |
| Context & State | 80 | 16 | 20 | 7 / 2 / 1 |
| Code Patterns | 100 | 6 | 6 | 3 / 0 / 0 |
| Safety & Boundaries | 85 | 22 | 26 | 9 / 4 / 0 |
| Toolset Scale | 100 | 8 | 8 | 4 / 0 / 0 |
| Autonomous Planning | 83 | 5 | 6 | 2 / 1 / 0 |
| Creative Composition | 100 | 6 | 6 | 3 / 0 / 0 |
| Structured Output | 100 | 12 | 12 | 6 / 0 / 0 |

## Performance — Coding-Agent Workload

| Context depth | Concurrency | Aggregate tg t/s | Per-agent tg t/s | TTFT (ms) | pp t/s |
|---:|---:|---:|---:|---:|---:|
| 0 | 1 | 68.39 | 68.39 | 1634.29 | 1329.66 |
| 0 | 2 | 66.23 | 33.12 | 2452.51 | 1259.98 |
| 8,192 | 1 | 62.19 | 62.19 | 8783.49 | 1179.17 |
| 8,192 | 2 | 22.75 | 11.37 | 13149.71 | 1170.45 |
| 32,768 | 1 | 49.25 | 49.25 | 36427.21 | 958.55 |
| 32,768 | 2 | 7.39 | 3.70 | 57047.43 | 958.26 |

At concurrency 2, aggregate throughput is server-wide; per-agent tg t/s is the responsiveness metric for each coding agent.

## Invocation

### llama-benchy

```sh
/home/app/.local/bin/uv run --extra perf llama-benchy --base-url http://localhost:8080/v1 --model qwen3.8-27b --pp 2048 --tg 128 --depth 0 8192 32768 --concurrency 1 2 --runs 3 --latency-mode generation --no-cache --skip-coherence --no-adapt-prompt --format json --save-result /tmp/localllm-bench-qg4ixkri/performance.json --tokenizer /home/app/models/Frozenlock/Qwen3.8-27B-int4-AutoRound
```

Exit status: `0`

### tool-eval-bench

```sh
/home/app/.local/bin/uv run --extra perf tool-eval-bench run --seed 42 --base-url http://localhost:8080 --model qwen3.8-27b --json-file /tmp/localllm-bench-qg4ixkri/quality.json --output-dir /tmp/localllm-bench-qg4ixkri/upstream-reports --no-live
```

Exit status: `0`

## Reproducibility Notes

`run.json` is the canonical immutable record. It includes sanitized effective container configuration, tool versions, command outcomes, GPU snapshots, and raw benchmark results.
