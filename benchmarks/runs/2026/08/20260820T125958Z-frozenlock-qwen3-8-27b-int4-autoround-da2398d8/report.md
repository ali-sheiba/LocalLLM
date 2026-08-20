# Benchmark Run — Frozenlock/Qwen3.8-27B-int4-AutoRound

- **Run ID:** `20260820T125958Z-frozenlock-qwen3-8-27b-int4-autoround-da2398d8`
- **Status:** `completed`
- **Started:** `2026-08-20T12:54:52.577793+00:00`
- **Finished:** `2026-08-20T13:15:33.926388+00:00`
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
| Benchmark profile | `frozenlock-01-mtp-4-fp8-prefix.env` |
| Compose environment file | `models/qwen3.8-27b/autoround-int4/profiles/frozenlock-01-mtp-4-fp8-prefix.env` |
| Environment SHA-256 | `70ba6d271332f41439e336756945c6fc873a06eaf2de6b195dcad54096a44711` |
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

- **Final score:** 90
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
| Instruction Following | 100 | 10 | 10 | 5 / 0 / 0 |
| Context & State | 80 | 16 | 20 | 7 / 2 / 1 |
| Code Patterns | 100 | 6 | 6 | 3 / 0 / 0 |
| Safety & Boundaries | 85 | 22 | 26 | 9 / 4 / 0 |
| Toolset Scale | 75 | 6 | 8 | 3 / 0 / 1 |
| Autonomous Planning | 83 | 5 | 6 | 2 / 1 / 0 |
| Creative Composition | 100 | 6 | 6 | 3 / 0 / 0 |
| Structured Output | 100 | 12 | 12 | 6 / 0 / 0 |

## Performance — Coding-Agent Workload

| Context depth | Concurrency | Aggregate tg t/s | Per-agent tg t/s | TTFT (ms) | pp t/s |
|---:|---:|---:|---:|---:|---:|
| 0 | 1 | 78.34 | 78.34 | 1578.17 | 1380.79 |
| 0 | 2 | 50.05 | 25.03 | 3262.83 | 832.52 |
| 8,192 | 1 | 66.61 | 66.61 | 8059.11 | 1286.55 |
| 8,192 | 2 | 21.81 | 10.91 | 12969.03 | 1144.30 |
| 32,768 | 1 | 68.09 | 68.09 | 29015.80 | 1204.19 |
| 32,768 | 2 | 7.78 | 3.89 | 44246.88 | 1167.76 |

At concurrency 2, aggregate throughput is server-wide; per-agent tg t/s is the responsiveness metric for each coding agent.

## Invocation

### llama-benchy

```sh
/home/app/.local/bin/uv run --extra perf llama-benchy --base-url http://localhost:8080/v1 --model qwen3.8-27b --pp 2048 --tg 128 --depth 0 8192 32768 --concurrency 1 2 --runs 3 --latency-mode generation --no-cache --skip-coherence --no-adapt-prompt --format json --save-result /tmp/localllm-bench-45564srg/performance.json --tokenizer /home/app/models/Frozenlock/Qwen3.8-27B-int4-AutoRound
```

Exit status: `0`

### tool-eval-bench

```sh
/home/app/.local/bin/uv run --extra perf tool-eval-bench run --seed 42 --base-url http://localhost:8080 --model qwen3.8-27b --json-file /tmp/localllm-bench-45564srg/quality.json --output-dir /tmp/localllm-bench-45564srg/upstream-reports --no-live
```

Exit status: `0`

## Reproducibility Notes

`run.json` is the canonical immutable record. It includes sanitized effective container configuration, tool versions, command outcomes, GPU snapshots, and raw benchmark results.
