# Benchmark Run — incoai/Qwen3.8-27B-DFlash2

- **Run ID:** `20260820T172354Z-incoai-qwen3-8-27b-dflash2-46889170`
- **Status:** `completed`
- **Started:** `2026-08-20T17:23:54.639679+00:00`
- **Finished:** `2026-08-20T17:40:47.060414+00:00`
- **Protocol:** `tool-eval-69-perf-v1`
- **Comparison key:** `incoai/Qwen3.8-27B-DFlash2\|tool-eval-69-perf-v1\|NVIDIA GeForce RTX 3090,NVIDIA GeForce RTX 3090`

## Model and Stack

| Field | Value |
|---|---|
| Hugging Face source | `incoai/Qwen3.8-27B-DFlash2` |
| Host model path | `/home/app/models/incoai/Qwen3.8-27B-DFlash2` |
| Served model name | `qwen3.8-27b` |
| Engine | `auto-detected` |
| Compose file | `experiments/qwen3.8-27b-avuja-dflash2/docker-compose.yml` |
| Compose SHA-256 | `5103c111ea75f6cb887004d3bc166662ae514ffb0c8a6dc7a60e3cda504dd036` |
| Benchmark profile | `avuja-11-dflash2-fp8-kv.env` |
| Compose environment file | `experiments/qwen3.8-27b-avuja-dflash2/profiles/avuja-11-dflash2-fp8-kv.env` |
| Environment SHA-256 | `ec41ba75b1d1469641428f5dc1f344fda2d6f0bcbb9cd7b1a7a7d5bcf7ca2703` |
| Container image | `vllm/vllm-openai:v0.27.1` |
| Image digest | `vllm/vllm-openai@sha256:0a51ea5b4ae2dc5d81890e5173f54203d2a3ae0cfffe51b8fd2afd4391bfd967` |

## GPU Power Policy

- **Management:** `local`
- **Requested limit:** `350 W`
- **Restore status:** `succeeded`

| GPU | Original limit | Applied limit | Restored limit |
|---|---:|---:|---:|
| 0 | 350.00 W | 350 W | 350.00 W |
| 1 | 350.00 W | 350 W | 350.00 W |

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
| Multi-Step Chains | 75 | 6 | 8 | 3 / 0 / 1 |
| Restraint & Refusal | 100 | 6 | 6 | 3 / 0 / 0 |
| Error Recovery | 83 | 5 | 6 | 2 / 1 / 0 |
| Localization | 100 | 6 | 6 | 3 / 0 / 0 |
| Structured Reasoning | 100 | 6 | 6 | 3 / 0 / 0 |
| Instruction Following | 100 | 10 | 10 | 5 / 0 / 0 |
| Context & State | 85 | 17 | 20 | 7 / 3 / 0 |
| Code Patterns | 67 | 4 | 6 | 2 / 0 / 1 |
| Safety & Boundaries | 88 | 23 | 26 | 11 / 1 / 1 |
| Toolset Scale | 100 | 8 | 8 | 4 / 0 / 0 |
| Autonomous Planning | 67 | 4 | 6 | 2 / 0 / 1 |
| Creative Composition | 100 | 6 | 6 | 3 / 0 / 0 |
| Structured Output | 100 | 12 | 12 | 6 / 0 / 0 |

## Performance — Coding-Agent Workload

| Context depth | Concurrency | Aggregate tg t/s | Per-agent tg t/s | TTFT (ms) | pp t/s |
|---:|---:|---:|---:|---:|---:|
| 0 | 1 | 85.86 | 85.86 | 1726.75 | 1241.08 |
| 0 | 2 | 65.41 | 32.71 | 2597.70 | 1188.13 |
| 8,192 | 1 | 60.82 | 60.82 | 8760.80 | 1179.76 |
| 8,192 | 2 | 67.95 | 33.97 | 16665.33 | 1169.26 |
| 32,768 | 1 | 82.30 | 82.30 | 31440.25 | 1110.34 |
| 32,768 | 2 | 8.67 | 4.33 | 49272.99 | 1106.63 |

At concurrency 2, aggregate throughput is server-wide; per-agent tg t/s is the responsiveness metric for each coding agent.

## Invocation

### llama-benchy

```sh
/home/app/.local/bin/uv run --extra perf llama-benchy --base-url http://localhost:8080/v1 --model qwen3.8-27b --pp 2048 --tg 128 --depth 0 8192 32768 --concurrency 1 2 --runs 3 --latency-mode generation --no-cache --skip-coherence --no-adapt-prompt --format json --save-result /tmp/localllm-bench-dem3cv6c/performance.json --tokenizer /home/app/models/Avuja/Qwen3.8-27B-int4-AutoRound
```

Exit status: `0`

### tool-eval-bench

```sh
/home/app/.local/bin/uv run --extra perf tool-eval-bench run --seed 42 --base-url http://localhost:8080 --model qwen3.8-27b --json-file /tmp/localllm-bench-dem3cv6c/quality.json --output-dir /tmp/localllm-bench-dem3cv6c/upstream-reports --no-live
```

Exit status: `0`

## Reproducibility Notes

`run.json` is the canonical immutable record. It includes sanitized effective container configuration, tool versions, command outcomes, GPU snapshots, and raw benchmark results.
