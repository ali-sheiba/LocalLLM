# Docker — Local LLM Inference for Agentic Coding

**Goal**: Find the best local LLM configuration for **agentic coding and workflows**. Each stack targets **2+ parallel sessions** with the **maximum context window** that fits on dual RTX 3090 (24 GB each, PCIe, no NVLink).

This project stores and experiments with different model configurations across **vLLM** and **llama.cpp** backends. Every stack is a hypothesis — we tune, benchmark, and iterate.

## Hardware & Setup

| Item | Detail |
|---|---|
| GPUs | 2× RTX 3090 (24 GB each), PCIe-only (no NVLink) |
| Tensor parallel | TP=2 for vLLM stacks; layer-split via `-ts` or `-np` for llama.cpp |
| Model storage | `/models/` (host), mounted read-only into containers |
| Cache dirs | `/home/app/cache/vllm/torch_compile`, `/home/app/cache/vllm/triton` |
| Chat templates | `/models/chat_template.jinja`, `/models/froggeric/...` |

**Only one stack should run at a time** — they share port `8080` and the two GPUs. Stop the current stack (`docker compose down`) before starting another.

## Project Structure

```
docker/
├── AGENTS.md
├── .gitignore
│
├── models/                            # All runnable stacks, organized by model family
│   │
│   ├── laguna-xs/
│   │   └── default.yml                # llama.cpp — Laguna XS 2.1 (GGUF)
│   │
│   ├── llama-embed/
│   │   └── default.yml                # llama.cpp CPU — Nomic embed (3 replicas)
│   │
│   ├── ornith-1.0-35b/
│   │   ├── llama.yml                  # ik-llama — Ornith 1.0 35B (Q8, agentic-coding RL)
│   │   └── vllm.yml                   # vLLM — Ornith 1.0 35B (FP8)
│   │
│   ├── qwen3.6-27b/
│   │   ├── fp8/default.yml            # vLLM — FP8 (official Qwen quant)
│   │   ├── awq-int4/default.yml       # vLLM — AWQ-INT4 (cyankiwi)
│   │   ├── autoround-int4/default.yml # vLLM — AutoRound-INT4 (Lorbus)
│   │   └── mtp/default.yml            # llama.cpp — MTP speculative (Q4_K_M)
│   │
│   ├── qwen3.6-35b/
│   │   ├── fp8/default.yml            # vLLM — MoE + vision (FP8)
│   │   └── uncensored/default.yml     # llama.cpp — Uncensored (Q6_K_P)
│   │
│   └── qwopus3.6-27b/
│       ├── coder/default.yml          # llama.cpp — Coder fine-tune (Q8)
│       └── coder-mtp/default.yml      # llama.cpp — Coder + MTP speculative
│
├── experiments/                       # Experimental / A-B variants
│   ├── README.md                      # Naming convention and how to run
│   └── <model-name>/
│       └── <description>.yml          # e.g. "v2-nccl-tuning.yml"
│
├── benchmarks/                        # Benchmark results & scoring
│   ├── README.md                      # How we benchmark and scoring rubric
│   ├── scoring.md                     # Current best scores per category
│   └── results/                       # Per-stack benchmark logs
│
└── helpers/                           # Operational scripts
    ├── switch-stack.sh                # Stop current, start new in one shot
    └── check-gpu.sh                   # Quick nvidia-smi wrapper

### Naming conventions

| Pattern | Meaning |
|---|---|
| `models/<model>/<variant>/default.yml` | Canonical config for a stack |
| `models/<model>/<model>.yml` | Single-variant stacks use the model name (e.g. `llama.yml`) |
| `experiments/<model-name>/<name>.yml` | Experimental variant of an existing stack |
| `.env` | Private env vars; placed alongside the compose file, never committed |
| `.env.example` | Public template with no secrets |
```

### Adding a new variant

1. Create a sub-directory under `models/<model>/`
2. Add a `default.yml` with the base configuration
3. Add a `.env.example` with documented env vars
4. If tuning, copy from `default.yml` to `experiments/<model-name>/` and iterate

### Adding a new model

1. Create a new top-level directory under `models/` using the model name
2. Add variants as sub-directories, following the existing patterns

## Stack Quick Reference

| Stack | Engine | Model | Quant | Context | Notes |
|---|---|---|---|---|---|
| `laguna-xs/` | llama.cpp | Laguna XS 2.1 | Q4_K_M | 524K | GGUF, layer-split 2× 3090 |
| `llama-embed/` | llama.cpp (CPU) | Nomic Embed v1.5 | Q8_0 | 8K | Embedding service, 3 replicas |
| `ornith-1.0-35b/llama.yml` | ik-llama | Ornith 1.0 35B | Q8_0 | 262K | Agentic-coding RL, MoE |
| `ornith-1.0-35b/vllm.yml` | vLLM | Ornith 1.0 35B | FP8 | 131K | vLLM variant of Ornith |
| `qwen3.6-27b/fp8/` | vLLM | Qwen3.6-27B | FP8 | 262K | Official Qwen quant, MTP k=3 |
| `qwen3.6-27b/awq-int4/` | vLLM | Qwen3.6-27B | AWQ-INT4 | 262K | cyankiwi quant |
| `qwen3.6-27b/autoround-int4/` | vLLM | Qwen3.6-27B | AutoRound-INT4 | 262K | Lorbus quant |
| `qwen3.6-27b/mtp/` | llama.cpp | Qwen3.6-27B-MTP | Q4_K_M | 32K | Speculative MTP decoding |
| `qwen3.6-35b/fp8/` | vLLM | Qwen3.6-35B-A3B | FP8 | 131K | MoE hybrid (Mamba + full-attn), multimodal |
| `qwen3.6-35b/uncensored/` | llama.cpp | Qwen3.6-35B-A3B-Uncensored | Q6_K_P | 524K | HauhauCS aggressive |
| `qwopus3.6-27b/coder/` | llama.cpp | Qwopus3.6-27B-Coder | Q8_0 | 262K | Coder fine-tune |
| `qwopus3.6-27b/coder-mtp/` | llama.cpp | Qwopus3.6-27B-Coder-MTP | Q8_0 | 262K | Coder + speculative MTP |

## Common Patterns

### Starting a stack

```bash
cd docker/models/<model>/<variant>
docker compose up -d
```

For stacks with a named compose file (not `default.yml`):

```bash
# ik-llama Ornith
cd docker/models/ornith-1.0-35b
MODEL_DIR=/models/deepreinforce-ai/Ornith-1.0-35B-GGUF PORT=8071 \
  docker compose -f llama.yml up -d
```

### Stopping a stack

```bash
cd docker/models/<model>/<variant>
docker compose down
```

### Switching stacks

```bash
# Use the helper to stop current and start new in one shot
./docker/helpers/switch-stack.sh <model>/<variant>
```

### Running an experiment

```bash
# Run an experimental variant (A-B test)
cd docker/experiments/<model-name>
docker compose -f <description>.yml up -d
```

### Common environment overrides

Most stacks support these overrides via `.env` or inline:

| Variable | Default | Description |
|---|---|---|
| `CTX_SIZE` | varies | Context window size |
| `BATCH_SIZE` | 4096 | Prefill batch size |
| `UBATCH_SIZE` | 512 | UV batch size |
| `KV_TYPE` | q4_0 / q8_0 | KV cache quantization |
| `NP` | 1-2 | Number of batch sequences |
| `TEMP` / `TEMPERATURE` | 0.6 | Sampling temperature |
| `TOP_P` | 0.95 | Nucleus sampling threshold |
| `TOP_K` | 20 | Top-k sampling |
| `REASONING` | off | Enable reasoning mode |
| `REASONING_FORMAT` | deepseek | Reasoning output format |

### vLLM-specific

| Variable | Purpose |
|---|---|
| `CUDA_VISIBLE_DEVICES` | Restrict which GPUs the stack uses |
| `PREFIX_CACHE_ARG` | Toggle prefix caching (off by default on AWQ to avoid MTP + prefix-cache corruption) |

## Shared Constraints

- **Port 8080**: All GPU stacks bind to `8080:8000` (vLLM) or `8080:8080` (llama.cpp). Only one can run at a time.
- **GPU conflict**: Running two GPU stacks simultaneously will OOM. Always `docker compose down` the current one first.
- **35B A3B on vLLM** requires a vLLM build with `qwen3_5_moe` support — the pinned v0.22.0 image used for 27B may not support it.
- **Chat templates**: The `froggeric` chat template is mounted from `/models/froggeric/Qwen-Fixed-Chat-Templates/chat_template.jinja` on vLLM stacks. The 35B A3B uses its own built-in template.
- **Speculative decoding (MTP)**: Enabled on most stacks via `--spec-type draft-mtp` (llama.cpp) or `speculative-config` (vLLM). Note: prefix-caching is disabled on AWQ-INT4 because MTP × prefix-cache corrupts recurrent-state KV.

## Models Directory

Models are stored under `/models/` on the host, following **HuggingFace-style** `author/model-name` paths. This convention mirrors HF repository URLs (`huggingface.co/author/model-name`) for easy traceability.

**Convention**: `<hf-username-or-org>/<model-name>`

```
/models/
├── Qwen/Qwen3.6-27B-FP8
├── Qwen/Qwen3.6-35B-A3B-FP8
├── cyankiwi/Qwen3.6-27B-AWQ-INT4
├── Lorbus/Qwen3.6-27B-int4-AutoRound
├── unsloth/Qwen3.6-27B-MTP-GGUF
├── HauhauCS/Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive
├── deepreinforce-ai/Ornith-1.0-35B-GGUF
├── deepreinforce-ai/Ornith-1.0-35B-FP8
├── Jackrong/Qwopus3.6-27B-Coder-GGUF
├── Jackrong/Qwopus3.6-27B-Coder-MTP-GGUF
├── poolside/Laguna-XS-2.1-GGUF
├── nomic-ai/nomic-embed-text-v1.5-GGUF
└── froggeric/Qwen-Fixed-Chat-Templates/
```

**When adding a new model**: Create its directory as `/models/<hf-author>/<model-name>/` to maintain consistency with the source repository.

## Useful Commands

```bash
# Check running containers
docker ps --format "table {{.Names}}	{{.Status}}	{{.Ports}}"

# View logs of a running stack
docker compose -f docker/models/<model>/<variant>/default.yml logs -f

# Check GPU memory
./docker/helpers/check-gpu.sh

# Switch from current stack to another
./docker/helpers/switch-stack.sh qwen3.6-27b/fp8

# Clean up unused images
docker image prune -a
```