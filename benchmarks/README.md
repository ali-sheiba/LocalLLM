# LocalLLM Benchmark Records

This directory is the durable experiment ledger for LocalLLM serving stacks. Each benchmark run captures tool-calling quality, throughput for one or two long-running coding agents, the effective container configuration, and relevant GPU/power state.

## Run a benchmark

Start the intended stack first, then run the recorder from the LocalLLM repository:

```sh
./helpers/run-benchmark.py \
  --stack models/qwen3.6-27b/autoround-int4/docker-compose.yml \
  --service vllm-qwen36-27b-dual \
  --power-limit 350
```

The standard protocol is equivalent in scope to the usual tool-eval workload:

- full public `tool-eval-bench` suite with seed `42`;
- performance depths `0,8192,32768`;
- performance concurrency `1,2`;
- `pp=2048`, `tg=128`, three measurements per point;
- generation-latency mode.

The script runs llama-benchy directly so its complete JSON result is retained, then runs tool-eval-bench for the quality result. Both raw results become part of the run's `run.json`.

### Common overrides

```sh
# The benchmark service is already running; model is discovered from /v1/models.
./helpers/run-benchmark.py \
  --stack models/qwen3.6-27b/fp8/docker-compose.yml \
  --service vllm-qwen36-27b \
  --power-limit 350 \
  --depth "0,16384,32768" \
  --tg 1024 \
  --runs 5

# Start only the declared service before testing. This never stops another stack.
./helpers/run-benchmark.py \
  --stack models/qwen3.6-27b/fp8/docker-compose.yml \
  --service vllm-qwen36-27b \
  --start
```

Use `--model`, `--model-source`, or `--tokenizer` when automatic discovery is insufficient. `--model-source` should be the actual host model path or an HF-style `author/model` identifier. An optional API key is read from `TOOL_EVAL_API_KEY` by default and is never written to a run record.

> **Stack safety:** GPU stacks share the same hardware and normally port `8080`. The benchmark runner does not stop a different stack. Ensure the intended stack is the only GPU workload before running a benchmark.

## GPU power policy

Power control is opt-in: omit `--power-limit` to observe hardware state without changing it. When a limit is requested, the runner calls [`helpers/set-gpu-power-limit.sh`](../helpers/set-gpu-power-limit.sh) with only the requested wattage.

The helper is deliberately narrow:

- it connects to the power-management host, `root@192.168.0.10`, over SSH;
- it accepts exactly one positive integer wattage;
- it refuses values above the `350W` safety maximum;
- it changes every GPU on that host.

The benchmark runner itself collects `nvidia-smi` telemetry locally inside the LXC. Before calling the helper, it captures that local GPU state and refuses a capped run unless the benchmark stack owns every detected GPU and their previous limits match. This guarantees that a one-value helper can restore the original cap after normal benchmark failures, `Ctrl+C`, and `SIGTERM`. An LXC crash or `SIGKILL` cannot execute cleanup; the recorded `power_policy.manual_recovery_command` in `run.json` is the recovery command in that case.

## Artifact layout

```text
benchmarks/
├── INDEX.md
├── index.json
├── runs/
│   └── YYYY/MM/<run-id>/
│       ├── report.md
│       └── run.json
└── comparisons/
```

A run directory is immutable after completion and intentionally contains only two files:

| File | Purpose |
|---|---|
| `report.md` | Human- and LLM-readable summary of stack identity, power/hardware, quality, and the c1/c2 performance matrix. |
| `run.json` | Canonical structured evidence: commands, raw benchmark results, sanitized effective container configuration, tool versions, Docker/Git identity, GPU snapshots, and power restoration state. |

`run.json` redacts environment values whose names contain `key`, `token`, `secret`, `password`, `credential`, or `auth`.

## Index and comparisons

`helpers/run-benchmark.py` regenerates `INDEX.md` and `index.json` after recording a run. To rebuild them manually:

```sh
python3 helpers/build-benchmark-index.py --index
```

The index reports quality, completion/safety state, and throughput at the most relevant depth/concurrency points. It deliberately does not create one arbitrary combined score: compare quality and c1/c2 responsiveness separately.

Write intentional analyses under `benchmarks/comparisons/`. The project-local `benchmark-analysis` skill validates protocol, effective stack configuration, hardware, and power equivalence before an LLM claims that a run is faster or better.

## Comparability

Two runs are directly comparable only when they use the same:

- benchmark protocol and tool/evaluator versions;
- model source, quantization, serving engine/image, chat/tool configuration, and sampling settings;
- effective server command and relevant environment settings;
- GPU topology, driver/runtime, and power policy;
- performance depths, token counts, latency mode, and measurement repetitions.

At concurrency 2, report both aggregate generation throughput and **per-agent** generation throughput. Aggregate throughput can rise even when each coding agent becomes less responsive.
