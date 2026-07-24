# Docker — Local LLM Inference

This project manages Docker Compose stacks for running various LLMs locally on **dual RTX 3090 (24 GB each, PCIe, no NVLink)** using **vLLM** and **llama.cpp** backends.

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
├── laguna-xs/
│   └── docker-compose.yml              # llama.cpp — Laguna XS 2.1 (GGUF)
├── llama-embed/
│   └── docker-compose.yml              # llama.cpp CPU — Nomic embed (embedding service, 3 replicas)
├── ornith-1.0-35b/
│   └── docker-compose.yml              # ik-llama — Ornith 1.0 35B (GGUF, agentic-coding RL)
├── qwen3.6-27b/
│   ├── vllm/
│   │   ├── fp8/docker-compose.yml       # vLLM — Qwen3.6-27B-FP8 (official Qwen quant)
│   │   ├── awq-int4/docker-compose.yml  # vLLM — Qwen3.6-27B-AWQ-INT4 (cyankiwi)
│   │   └── autoround-int4/
│   │       ├── docker-compose.yml       # vLLM — Qwen3.6-27B-int4-AutoRound (Lorbus)
│   │       └── update.yml               # Experimental update / A-B test variant
│   └── llama.cpp/
│       └── mtp/
│           ├── .env                     # Private env vars
│           └── docker-compose.yml       # llama.cpp — Qwen3.6-27B-MTP (speculative decoding)
├── qwen3.6-35b/
│   ├── fp8/docker-compose.yml           # vLLM — Qwen3.6-35B-A3B-FP8 (MoE + vision)
│   └── a3b/uncensored.yml               # llama.cpp — Qwen3.6-35B-A3B-Uncensored (HauhauCS)
├── qwopus3.6-27B/
│   └── llama/
│       ├── coder/docker-compose.yml     # llama.cpp — Qwopus3.6-27B-Coder (GGUF, Q8)
│       └── coder-mtp/
│           ├── .env                     # Private env vars
│           └── docker-compose.yml       # llama.cpp — Qwopus3.6-27B-Coder-MTP (speculative)
└── vllm-ornith/
    └── docker-compose.yml               # vLLM — Ornith 1.0 35B (FP8)
```

## Stack Quick Reference

| Directory | Engine | Model | Quant | Context | Notes |
|---|---|---|---|---|---|
| `laguna-xs/` | llama.cpp | Laguna XS 2.1 | Q4_K_M | 524K | GGUF, layer-split 2× 3090 |
| `llama-embed/` | llama.cpp (CPU) | Nomic Embed Text v1.5 | Q8_0 | 8K | Embedding service, 3 replicas |
| `ornith-1.0-35b/` | ik-llama | Ornith 1.0 35B | Q8_0 | 262K | Agentic-coding RL, MoE |
| `qwen3.6-27b/vllm/fp8/` | vLLM | Qwen3.6-27B | FP8 | 262K | Official Qwen quant, MTP k=3 |
| `qwen3.6-27b/vllm/awq-int4/` | vLLM | Qwen3.6-27B | AWQ-INT4 | 262K | cyankiwi quant |
| `qwen3.6-27b/vllm/autoround-int4/` | vLLM | Qwen3.6-27B | AutoRound-INT4 | 262K | Lorbus quant |
| `qwen3.6-27b/llama.cpp/mtp/` | llama.cpp | Qwen3.6-27B-MTP | Q4_K_M | 32K | Speculative MTP decoding |
| `qwen3.6-35b/fp8/` | vLLM | Qwen3.6-35B-A3B | FP8 | 131K | MoE hybrid (Mamba + full-attn), multimodal |
| `qwen3.6-35b/a3b/` | llama.cpp | Qwen3.6-35B-A3B-Uncensored | Q6_K_P | 524K | HauhauCS aggressive |
| `qwopus3.6-27B/llama/coder/` | llama.cpp | Qwopus3.6-27B-Coder | Q8_0 | 262K | Coder fine-tune |
| `qwopus3.6-27B/llama/coder-mtp/` | llama.cpp | Qwopus3.6-27B-Coder-MTP | Q8_0 | 262K | Coder + speculative MTP |
| `vllm-ornith/` | vLLM | Ornith 1.0 35B | FP8 | 131K | vLLM variant of Ornith |

## Common Patterns

### Starting a stack

```bash
cd docker/<stack-dir>
docker compose up -d
```

For stacks that use a non-default compose file:

```bash
# llama.cpp 35B uncensored
cd docker/qwen3.6-35b/a3b
docker compose -f uncensored.yml up -d

# ik-llama Ornith
cd docker/ornith-1.0-35b
MODEL_DIR=/models/deepreinforce-ai/Ornith-1.0-35B-GGUF PORT=8071 \
  docker compose -f docker-compose.yml up -d
```

### Stopping a stack

```bash
cd docker/<stack-dir>
docker compose down
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

Models are stored under `/models/` on the host:

```
models/
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
├── froggeric/Qwen-Fixed-Chat-Templates/
└── chat_template.jinja
```

## Useful Commands

```bash
# Check running containers
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# View logs of a running stack
docker compose -f docker/<stack>/docker-compose.yml logs -f

# Check GPU memory
nvidia-smi

# Clean up unused images
docker image prune -a
```