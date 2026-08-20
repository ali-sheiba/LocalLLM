# Benchmark Run — Avuja/Qwen3.8-27B-int4-AutoRound

- **Run ID:** `20260820T102849Z-avuja-qwen3-8-27b-int4-autoround-84de9b81`
- **Status:** `completed`
- **Started:** `2026-08-20T10:26:28.765207+00:00`
- **Finished:** `2026-08-20T10:47:11.104193+00:00`
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
| Benchmark profile | `avuja-07-froggeric-template.env` |
| Compose environment file | `models/qwen3.8-27b/autoround-int4/profiles/avuja-07-froggeric-template.env` |
| Environment SHA-256 | `59c3d5ebafa90549e15c6515c568b9ce968dff3df2a3b738f52483d80c11e8a8` |
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
| Instruction Following | 100 | 10 | 10 | 5 / 0 / 0 |
| Context & State | 85 | 17 | 20 | 7 / 3 / 0 |
| Code Patterns | 67 | 4 | 6 | 2 / 0 / 1 |
| Safety & Boundaries | 88 | 23 | 26 | 10 / 3 / 0 |
| Toolset Scale | 100 | 8 | 8 | 4 / 0 / 0 |
| Autonomous Planning | 100 | 6 | 6 | 3 / 0 / 0 |
| Creative Composition | 100 | 6 | 6 | 3 / 0 / 0 |
| Structured Output | 83 | 10 | 12 | 5 / 0 / 1 |

## Performance — Coding-Agent Workload

| Context depth | Concurrency | Aggregate tg t/s | Per-agent tg t/s | TTFT (ms) | pp t/s |
|---:|---:|---:|---:|---:|---:|
| 0 | 1 | 68.24 | 68.24 | 1451.48 | 1505.76 |
| 0 | 2 | 70.07 | 35.03 | 2176.02 | 1421.03 |
| 8,192 | 1 | 62.04 | 62.04 | 7893.16 | 1313.40 |
| 8,192 | 2 | 22.14 | 11.07 | 11808.76 | 1303.52 |
| 32,768 | 1 | 50.01 | 50.01 | 33408.23 | 1045.29 |
| 32,768 | 2 | 7.96 | 3.98 | 52318.89 | 1043.64 |

At concurrency 2, aggregate throughput is server-wide; per-agent tg t/s is the responsiveness metric for each coding agent.

## Invocation

### llama-benchy

```sh
/home/app/.local/bin/uv run --extra perf llama-benchy --base-url http://localhost:8080/v1 --model qwen3.8-27b --pp 2048 --tg 128 --depth 0 8192 32768 --concurrency 1 2 --runs 3 --latency-mode generation --no-cache --skip-coherence --no-adapt-prompt --format json --save-result /tmp/localllm-bench-x5zldxbt/performance.json --tokenizer /home/app/models/Avuja/Qwen3.8-27B-int4-AutoRound
```

Exit status: `0`

### tool-eval-bench

```sh
/home/app/.local/bin/uv run --extra perf tool-eval-bench run --seed 42 --base-url http://localhost:8080 --model qwen3.8-27b --json-file /tmp/localllm-bench-x5zldxbt/quality.json --output-dir /tmp/localllm-bench-x5zldxbt/upstream-reports --no-live
```

Exit status: `0`

## Reproducibility Notes

`run.json` is the canonical immutable record. It includes sanitized effective container configuration, tool versions, command outcomes, GPU snapshots, and raw benchmark results.
