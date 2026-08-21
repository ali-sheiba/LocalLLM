# LocalLLM contributor guide

## Purpose

LocalLLM is a personal set of reproducible local-LLM serving and benchmark experiments for agentic coding. It targets a Proxmox LXC with a Threadripper Pro 3955WX, 128 GB ECC RAM, and two PCIe RTX 3090 GPUs (24 GB each, no NVLink). Configurations are hypotheses to measure, not universal recommendations.

The project is inspired by [club-3090](https://github.com/noonghunna/club-3090) and community research. Preserve provenance when porting or adapting an upstream configuration.

## Repository layout

```text
LocalLLM/
├── README.md
├── AGENTS.md
├── models/                         # Canonical runnable stacks
│   ├── laguna-xs/
│   ├── llama-embed/
│   ├── muse-glimmer-30b/
│   ├── ornith-1.0-35b/
│   ├── qwen3.6-27b/
│   ├── qwen3.6-35b/
│   └── qwen3.8-27b/
├── experiments/                    # Isolated changes under evaluation
├── benchmarks/                     # Immutable run evidence and comparisons
└── helpers/                        # Operational and benchmark scripts
```

## Runtime conventions

- Run only **one GPU stack at a time**. Most GPU stacks consume both cards and bind host port `8080`; the CPU embedding service uses `8082`.
- Compose bind mounts must use `${MODEL_ROOT:-${HOME}/models}` for all host-side model and template paths. Never add `/home/app/models` or a machine-specific model root.
- vLLM cache mounts use `${VLLM_CACHE_ROOT:-${HOME}/.cache/LocalLLM/vllm}`. Do not introduce machine-specific cache paths.
- Keep model files in a Hugging Face-style layout: `$MODEL_ROOT/<author-or-org>/<model-name>/`.
- Mount weights and templates read-only unless a stack has a documented reason not to.
- Explicit container names use `local-llm-<model>-<variant>-<engine>` and must be globally unique. Do not reuse a name from a canonical stack in an experiment.
- Check the resolved file with `docker compose -f <compose-file> config` before launching a changed stack.

## Current stack inventory

| Path | Engine | Notes |
|---|---|---|
| `models/laguna-xs/default.yml` | llama.cpp | Laguna XS 2.1 GGUF |
| `models/llama-embed/default.yml` | llama.cpp CPU | Nomic embedding service |
| `models/muse-glimmer-30b/docker-compose.yml` | llama.cpp | Muse Glimmer 30B GGUF |
| `models/ornith-1.0-35b/llama.yml` | ik-llama | Ornith 1.0 35B GGUF |
| `models/ornith-1.0-35b/vllm.yml` | vLLM | Ornith 1.0 35B FP8 |
| `models/qwen3.6-27b/*` | vLLM / llama.cpp | FP8, AWQ, AutoRound, MTP, and Fable Fusion variants |
| `models/qwen3.6-35b/*` | vLLM / llama.cpp | Qwen 3.6 35B A3B variants |
| `models/qwen3.8-27b/*` | vLLM / llama.cpp | FP8, AutoRound profile sweeps, and Unsloth GGUF |

Compose files may be named `default.yml`, `docker-compose.yml`, or a model-specific file such as `llama.yml`; use the actual filename.

## Adding or changing stacks

1. Add a model family under `models/<model>/`; use a variant directory where more than one configuration exists.
2. Use `default.yml` for a canonical variant when practical. Provide `.env.example` for stacks with meaningful user-tunable values.
3. Put a tuning hypothesis under `experiments/<model>-<variant>/` rather than overwriting a canonical configuration.
4. Use a distinct explicit container name for every Compose configuration.
5. Preserve source URLs, image tags/digests, model identifiers, and any local patch provenance in comments or adjacent documentation.
6. Do not add weights, generated caches, `.env` files, credentials, or private host/network details to Git.
7. Validate Compose syntax and mount interpolation with `MODEL_ROOT=/tmp/models docker compose -f <file> config`.

## Benchmarking

- `helpers/run-benchmark.py` writes immutable `report.md` and `run.json` artifacts under `benchmarks/runs/` and rebuilds the index.
- Install `uv` before running benchmark helpers. See `benchmarks/README.md` for the protocol.
- Compare runs only when model source/quantization, engine/image, effective command/environment, GPU topology, power policy, and measurement protocol are equivalent.
- At concurrency two, report per-agent responsiveness as well as aggregate throughput.
- Historical benchmark records must not be edited merely to reflect a newer local path or Compose file.

## Useful commands

```sh
# Inspect GPU state
./helpers/check-gpu.sh

# Render a stack before launch
MODEL_ROOT="$HOME/models" docker compose -f models/qwen3.8-27b/fp8/docker-compose.yml config

# Start a stack
MODEL_ROOT="$HOME/models" docker compose -f models/qwen3.8-27b/fp8/docker-compose.yml up -d

# Stop it
docker compose -f models/qwen3.8-27b/fp8/docker-compose.yml down

# Switch canonical model stacks
./helpers/switch-stack.sh qwen3.8-27b/fp8
```
