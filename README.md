# LocalLLM

Personal local-LLM serving and benchmark experiments for agentic coding. This is a reproducible reference for rebuilding the author's inference LXC and for sharing the results, not a polished distribution or a claim that these settings are generally optimal.

The work is inspired by [club-3090](https://github.com/noonghunna/club-3090) and community research, including Reddit discussions. Credit for the upstream ideas and configurations belongs to their authors.

## Test system

| Component | Configuration |
|---|---|
| Host platform | Gigabyte MC62-G40 |
| CPU | AMD Threadripper Pro 3955WX |
| Memory | 128 GB ECC DDR4-2133 |
| GPUs | 2 × RTX 3090, 24 GB each, PCIe only (no NVLink) |
| Virtualization | Proxmox VE 9.2.10 LXC |

The GPU configurations assume that both GPUs are available to the container. Most GPU stacks use tensor parallelism across both cards and publish port `8080`; run **one GPU stack at a time**.

## What is here

- `models/` — runnable vLLM, llama.cpp, and ik-llama stacks.
- `experiments/` — isolated configuration changes and patches under evaluation.
- `benchmarks/` — immutable run records, indexes, and comparison notes.
- `helpers/` — stack switching, GPU inspection, benchmark recording, and index tools.

The current model families include Laguna XS, Nomic embedding, Muse Glimmer, Ornith 1.0, Qwen 3.6, and Qwen 3.8. See [`AGENTS.md`](AGENTS.md) for the complete stack inventory and contributor conventions.

## Prerequisites

### 1. Prepare the LXC and GPU access

This project was developed in a privileged Proxmox LXC with NVIDIA device access. The exact LXC configuration is host- and security-policy-specific; before using this repository, ensure the container can run `nvidia-smi` and see both RTX 3090s.

You need:

- NVIDIA drivers on the Proxmox host compatible with the cards and userspace libraries exposed to the LXC;
- `/dev/nvidia*` device access and required cgroup permissions in the LXC;
- Docker-compatible LXC settings, commonly including `nesting=1` and `keyctl=1` where permitted by your Proxmox policy;
- sufficient disk space for checkpoints, images, and caches.

Validate GPU access inside the LXC before installing a model stack:

```sh
nvidia-smi
```

For hardware passthrough and Docker-in-LXC details, use the Proxmox and NVIDIA documentation for your host version. Do not blindly copy another system's LXC privilege or device ACL settings.

### 2. Install Docker, Compose, and NVIDIA Container Toolkit

Install Docker Engine and the Compose plugin from the [official Docker instructions](https://docs.docker.com/engine/install/), then install and configure the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) for Docker.

To run Docker without `sudo`, add your normal LXC user to Docker's group, then start a new login session:

```sh
sudo usermod -aG docker "$USER"
newgrp docker
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
```

> Membership in the `docker` group grants root-equivalent access to the host/container. Use it only for a trusted local user.

Also install the general command-line prerequisites used by the helpers:

```sh
sudo apt update
sudo apt install -y git curl python3 python3-venv
```

Benchmarking additionally requires [`uv`](https://docs.astral.sh/uv/) and a local checkout of [SeraphimSerapis/tool-eval-bench](https://github.com/SeraphimSerapis/tool-eval-bench). Install `uv` with its official installer, clone the benchmark repository, and configure its location:

```sh
uv --version
mkdir -p "$HOME/bench"
git clone https://github.com/SeraphimSerapis/tool-eval-bench.git "$HOME/bench/tool-eval-bench"
export TOOL_EVAL_DIR="$HOME/bench/tool-eval-bench"
```

The benchmark helper runs `uv` from this checkout to invoke both `tool-eval-bench` and `llama-benchy`. For reproducible comparisons, record and keep the same upstream checkout revision; the helper stores its Git commit in each run record. Set `TOOL_EVAL_DIR` in your shell profile when using a non-default location. The CLI option `--tool-eval-dir /path/to/tool-eval-bench` overrides the environment variable for one invocation.

### 3. Clone and configure storage

```sh
git clone <your-fork-or-repository-url> LocalLLM
cd LocalLLM

# Optional: the Compose default is "$HOME/models" when this is unset.
export MODEL_ROOT="$HOME/models"
export VLLM_CACHE_ROOT="$HOME/.cache/LocalLLM/vllm"
mkdir -p "$MODEL_ROOT" "$VLLM_CACHE_ROOT"
```

`MODEL_ROOT` is the single host root used by all Compose model and chat-template mounts. If it is not set, Compose falls back to `${HOME}/models`. Export it in your shell profile (for example, `~/.profile`) if your models live elsewhere.

`VLLM_CACHE_ROOT` controls vLLM compile and Triton caches and defaults to `${HOME}/.cache/LocalLLM/vllm` for the stacks that use it.

Download each required Hugging Face checkpoint yourself, retaining the source's `author/model-name` layout beneath `MODEL_ROOT`. For example, the Qwen 3.8 FP8 stack expects:

```text
$MODEL_ROOT/
├── Qwen/Qwen3.8-27B-FP8/
└── froggeric/Qwen-Fixed-Chat-Templates/chat_template.jinja
```

Model weights are intentionally not included in this repository. Check each model's license, gating requirements, and disk-space needs before downloading it.

## Run a stack

Inspect the resolved configuration before launching. This catches missing paths and shows the final environment values:

```sh
MODEL_ROOT="$MODEL_ROOT" docker compose \
  -f models/qwen3.8-27b/fp8/docker-compose.yml config
```

For parameterized stacks, copy the local template first when one is supplied:

```sh
cd models/qwen3.8-27b/fp8
cp .env.example .env
# Edit .env for your model path, port, capacity, or sampling choices.
docker compose up -d
```

For a named benchmark profile, run from the repository root:

```sh
docker compose \
  --env-file models/qwen3.8-27b/autoround-int4/profiles/avuja.env \
  -f models/qwen3.8-27b/autoround-int4/docker-compose.yml up -d
```

The OpenAI-compatible GPU API is normally available at `http://localhost:8080/v1`. Check it and view logs with:

```sh
curl http://localhost:8080/v1/models
docker compose -f models/qwen3.8-27b/fp8/docker-compose.yml logs -f
```

Stop the same configuration with `docker compose ... down` before launching another GPU stack. `helpers/switch-stack.sh` can stop discovered model stacks and start a selected one:

```sh
./helpers/switch-stack.sh qwen3.8-27b/fp8
```

## Configuration conventions

- **Host paths:** `MODEL_ROOT` and `VLLM_CACHE_ROOT` are portable host-root variables; container paths remain fixed under `/models` where required by the server command.
- **Local overrides:** `.env` and `.env.local` are ignored by Git. Copy a committed `.env.example` when available; never commit credentials.
- **Containers:** explicit names follow `local-llm-<model>-<variant>-<engine>`. They are globally unique, but this does not make dual-GPU/port-8080 stacks safe to run together.
- **Ports:** GPU stacks normally use `8080`; the CPU embedding stack uses `8082`. Set `PORT` only for configurations that expose it as an interpolation variable.
- **Capacity:** context length, parallel sequences, batch sizes, KV cache type, and GPU memory utilization are hardware-sensitive. Treat defaults as recorded hypotheses, not safe universal settings.

## Benchmarks

The benchmark recorder captures the resolved Compose configuration, sanitized environment, GPU state, tool-calling quality, and one- and two-agent throughput. It requires the local `tool-eval-bench` checkout configured through `TOOL_EVAL_DIR` (or the default `~/bench/tool-eval-bench`). Start the target stack first, then run:

```sh
TOOL_EVAL_DIR="$HOME/bench/tool-eval-bench" \
./helpers/run-benchmark.py \
  --stack models/qwen3.8-27b/fp8/docker-compose.yml \
  --service vllm-qwen38-27b-fp8 \
  --power-limit 350
```

Read [`benchmarks/README.md`](benchmarks/README.md) before comparing results. Benchmark records are historical evidence: their stored host paths and Compose hashes describe the original run and are not rewritten when configurations evolve.

## Safety and limitations

- GPU stack defaults target this specific dual-3090, PCIe-only system; OOMs and instability are expected when changing context, concurrency, MTP, caching, or quantization.
- Some experiments mount local patches and intentionally pin (or do not pin) images; review the resolved config before running them.
- Docker images and model downloads execute third-party code. Review sources and use a trusted environment.
- The optional power-limit helper connects to a configured management host; inspect [`benchmarks/README.md`](benchmarks/README.md) and `helpers/set-gpu-power-limit.sh` before enabling it.

## Contributing / reproducing

Keep model weights, caches, `.env` files, API keys, and private network details out of commits. Add a new stack or experiment using the conventions in [`AGENTS.md`](AGENTS.md), run `docker compose ... config`, and retain benchmark artifacts when publishing a result.
