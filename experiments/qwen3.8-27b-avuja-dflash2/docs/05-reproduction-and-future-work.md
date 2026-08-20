# Reproduction and future work

All commands below assume the repository root is `/home/app/LocalLLM`. Only one GPU stack
may run at a time because stacks share port 8080 and both RTX 3090s.

## Prerequisites

- Docker Engine and NVIDIA Container Toolkit;
- `vllm/vllm-openai:v0.27.1` available locally or pullable;
- Avuja target at
  `/home/app/models/Avuja/Qwen3.8-27B-int4-AutoRound`;
- Froggeric template at
  `/home/app/models/froggeric/Qwen-Fixed-Chat-Templates/chat_template.jinja`;
- both GPUs free;
- benchmark `uv` at `/home/app/.local/bin/uv`.

The host did not have `hf` on `PATH` during this experiment. The vLLM image contains the
CLI, but its default entrypoint is `vllm`; override the entrypoint explicitly.

## Download the pinned drafter

From any directory:

```bash
docker run --rm \
  --entrypoint hf \
  -v /home/app/models:/models \
  vllm/vllm-openai:v0.27.1 \
  download incoai/Qwen3.8-27B-DFlash2 \
  --revision dedf8df68adfb1afeaf7b7480c0a0243108177b4 \
  --local-dir /models/incoai/Qwen3.8-27B-DFlash2
```

If a compatible host `hf` CLI is installed, the equivalent is:

```bash
hf download incoai/Qwen3.8-27B-DFlash2 \
  --revision dedf8df68adfb1afeaf7b7480c0a0243108177b4 \
  --local-dir /home/app/models/incoai/Qwen3.8-27B-DFlash2
```

Do not omit the revision. A moving checkpoint changes the experiment.

## Render the stack without starting it

```bash
cd /home/app/LocalLLM

docker compose \
  --env-file experiments/qwen3.8-27b-avuja-dflash2/profiles/avuja-11-dflash2-fp8-kv.env \
  -f experiments/qwen3.8-27b-avuja-dflash2/docker-compose.yml \
  config --quiet
```

Render the control independently:

```bash
docker compose \
  --env-file experiments/qwen3.8-27b-avuja-dflash2/profiles/avuja-11-control-no-draft-prefix.env \
  -f experiments/qwen3.8-27b-avuja-dflash2/docker-compose.yml \
  config --quiet
```

## Start P11

First confirm no other GPU stack is running:

```bash
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

Then:

```bash
docker compose \
  --env-file experiments/qwen3.8-27b-avuja-dflash2/profiles/avuja-11-dflash2-fp8-kv.env \
  -f experiments/qwen3.8-27b-avuja-dflash2/docker-compose.yml \
  up -d
```

Boot can take several minutes because of patching, compilation, graph capture, and
multimodal warmup. Follow logs with:

```bash
docker compose \
  --env-file experiments/qwen3.8-27b-avuja-dflash2/profiles/avuja-11-dflash2-fp8-kv.env \
  -f experiments/qwen3.8-27b-avuja-dflash2/docker-compose.yml \
  logs -f --no-log-prefix
```

Expected evidence:

- `[dflash2] applied vLLM PR#52816 backport` or an idempotent already-present message;
- `[dflash2-local] candidate-selector compile namespace applied`;
- speculative config resolves to `method='dflash'`, `/models/drafter`, n=7;
- V2 model runner selected;
- AutoRound resolves to `inc`;
- CUDA graph mode resolves/downgrades to `PIECEWISE`;
- GPU KV cache size near 221,379 tokens for this exact profile;
- server becomes ready on `http://localhost:8080/v1/models`.

Treat any anchor failure, V1 runner selection, zero acceptance, repeated restart, or CUDA
fault as a failed boot—not as a tuning opportunity.

## Short validation sequence

### Health and model identity

```bash
curl -s http://localhost:8080/v1/models
```

The served ID should be `qwen3.8-27b`. The drafter path must not appear as the served
target identity.

### True c1 and c2 smoke

```bash
python3 experiments/qwen3.8-27b-avuja-dflash2/smoke_concurrency.py \
  --concurrency 1 \
  --max-tokens 768

python3 experiments/qwen3.8-27b-avuja-dflash2/smoke_concurrency.py \
  --concurrency 2 \
  --max-tokens 768
```

The c2 script launches both requests in one thread pool. Do not substitute two serial
calls. Inspect acceptance metrics after requests:

```bash
curl -s http://localhost:8080/metrics | \
  grep -E 'spec_decoding|draft|accepted|prefix_cache'
```

The historical favorable smoke reached 124.15 t/s c1, 118.60 t/s mean c2 streamed
decode, and 65.6% draft acceptance. These are diagnostic expectations, not promotion
gates.

### Repeated-prefix probe

Record metrics, then run the same long prompt twice sequentially:

```bash
curl -s http://localhost:8080/metrics | \
  grep -E 'prefix_cache_(queries|hits)_total'

python3 experiments/qwen3.8-27b-avuja-dflash2/smoke_concurrency.py \
  --concurrency 1 \
  --prefix-words 1000 \
  --max-tokens 1

python3 experiments/qwen3.8-27b-avuja-dflash2/smoke_concurrency.py \
  --concurrency 1 \
  --prefix-words 1000 \
  --max-tokens 1

curl -s http://localhost:8080/metrics | \
  grep -E 'prefix_cache_(queries|hits)_total'
```

The script's `--prefix-words` value is a repeat count for the shared phrase, not an exact
token count. Use the target tokenizer if exact boundary-length probes are needed.

Historical P11 behavior was about 4.8 s for both requests and zero hits. That result is a
known blocker, not an expected pass condition for future work.

## Canonical benchmark

Use the repository helper so power, metadata, commands, and artifacts are captured:

```bash
./helpers/run-benchmark.py \
  --stack experiments/qwen3.8-27b-avuja-dflash2/docker-compose.yml \
  --env-file experiments/qwen3.8-27b-avuja-dflash2/profiles/avuja-11-dflash2-fp8-kv.env \
  --service vllm-qwen38-27b-avuja-dflash2 \
  --model-source Avuja/Qwen3.8-27B-int4-AutoRound \
  --tokenizer /home/app/models/Avuja/Qwen3.8-27B-int4-AutoRound \
  --uv /home/app/.local/bin/uv \
  --start \
  --power-limit 350
```

Three arguments are easy to miss and are required:

- `--model-source Avuja/Qwen3.8-27B-int4-AutoRound` prevents the helper from recording
  `/models/drafter` as the target;
- `--tokenizer /home/app/models/Avuja/Qwen3.8-27B-int4-AutoRound` prevents GPT-2
  fallback and keeps prompt depths meaningful;
- `--uv /home/app/.local/bin/uv` is required because `uv` is not on shell `PATH`.

Never modify a generated run directory to fix attribution. Preserve it and create a new
correctly invoked run, as was done here.

## Matched no-draft control

Stop P11 before changing profiles:

```bash
docker compose \
  --env-file experiments/qwen3.8-27b-avuja-dflash2/profiles/avuja-11-dflash2-fp8-kv.env \
  -f experiments/qwen3.8-27b-avuja-dflash2/docker-compose.yml \
  down
```

Start the control:

```bash
docker compose \
  --env-file experiments/qwen3.8-27b-avuja-dflash2/profiles/avuja-11-control-no-draft-prefix.env \
  -f experiments/qwen3.8-27b-avuja-dflash2/docker-compose.yml \
  up -d
```

Repeat the prefix probe. Historical control evidence was 5.44 s cold, 1.37 s replay,
4,704 hits / 10,102 queries, and a 508,268-token KV pool.

## Stop and verify cleanup

```bash
docker compose \
  --env-file experiments/qwen3.8-27b-avuja-dflash2/profiles/avuja-11-control-no-draft-prefix.env \
  -f experiments/qwen3.8-27b-avuja-dflash2/docker-compose.yml \
  down

docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

At the end of the original experiment the diagnostic stack was stopped, only the CPU
embedding service remained, and both GPUs were idle.

## Known operational pitfalls

- Official vLLM v0.27.1 does not contain DFlash2.
- `qwen3_dflash2.py` alone is insufficient.
- The original Tony overlay state examined during discovery lacked the later selector
  compile-cache namespace fix.
- The first Docker checkpoint download failed because the default `vllm` entrypoint
  parsed `hf` as a vLLM command; use `--entrypoint hf`.
- `MAX_NUM_BATCHED_TOKENS=8192` warns that speculative slots reduce schedulable tokens
  to 8,178.
- Overlay-specific `VLLM_DFLASH2_*` variables may trigger “unknown vLLM environment
  variable” warnings while still being read by the patched code.
- A high micro-smoke result can coexist with poor canonical c2 performance.
- The native BF16 drafter consumed enough memory to remove 56.4% of the matched
  no-draft logical KV pool.
- Prefix hit counters can be made nonzero unsafely; output correctness must be tested.

## Resume plan

Do not promise that the next profile will beat Lorbus. Use staged gates and stop at the
first failure.

### Stage 0 — refresh upstream status

Before changing code:

1. Check whether vLLM PRs #52816, #48375, #50897, and #52244 have merged or been
   superseded.
2. Pin exact commits and image digest.
3. Re-read open concurrency/graph issues on #52816.
4. Decide whether native upstream support now makes the runtime overlay obsolete.

### Stage 1 — instrument, do not optimize

Build an instrumented lane that records per-request/per-group:

- full-attention hit length;
- Mamba/GDN resumable hit length;
- DFlash/EAGLE hit length;
- global reconciled hit;
- boundary/hash unit;
- whether successor-aware publication is active.

Reproduce P11's zero and the no-draft control's hit before attempting a fix.

### Stage 2 — cache correctness milestone

Prefer a maintained successor-aware implementation based on PR #50897. If that is not
available, evaluate the boundary-state approach from PR #52244 as an explicitly temporary
lane. Run the complete matrix in
[the root-cause document](04-prefix-cache-root-cause.md), including A→A, A→B→A, greedy
parity, tool turns, boundary lengths, c2, and preemption.

**Gate:** nonzero safe replay hits, lower repeat TTFT, byte-identical greedy output, no
malformed tools, and no acceptance regression. No throughput tuning before this passes.

### Stage 3 — recover drafter memory

Test `syvai/Qwen3.8-27B-DFlash2-W4A16` as the **only** changed variable. Re-measure:

- boot and quantization compatibility;
- acceptance by workload and depth;
- logical KV pool;
- c1/c2 canonical performance;
- tool quality and safety;
- prefix correctness.

The purpose is to recover VRAM/bandwidth, not assume speed. Reject if quantization changes
acceptance enough to erase the memory benefit.

### Stage 4 — scheduler budget

Only after Stage 3 passes, raise `MAX_NUM_BATCHED_TOKENS` from 8,192 to 16,384 as a
single-variable arm. Confirm the 8,178 warning disappears and measure c2, TTFT, OOM
headroom, and deep-context behavior.

### Stage 5 — async scheduling

Async scheduling is last because speculative/hybrid state publication order is a
correctness concern. Apply and validate the relevant GDN/spec-order fix before enabling
it. Repeat A→B→A and tool-call soak tests, not only throughput.

### Separate single-stream lane

BF16 KV plus `FLASH_ATTN` may be useful for a single-stream speed study and is the path
behind some 200+ t/s community reports. On two 24 GB cards it further reduces context
capacity and does not satisfy the two-large-session objective. Keep it labeled as a
separate product hypothesis rather than P12 for the primary lane.

## Promotion gates for any future profile

A future profile may be promoted only if all are met in repeat runs:

- c2 depth 0 > 60 t/s per agent; target > 71.12 directional Lorbus record;
- c2 8K and 32K do not regress materially versus the best safe baseline;
- tool-eval ≥91 and **zero** safety warnings;
- correct Avuja tokenizer and model provenance recorded;
- nonzero, safe follow-up prefix reuse with lower TTFT;
- two-session KV capacity is stated honestly at the configured max context;
- no OOM, restart, CUDA/index error, or acceptance collapse;
- >20K generated-token dual-agent soak through tool-heavy turns and context
  compression;
- results replicate in at least two immutable canonical runs.

The next defensible milestone is cache correctness. Performance records come after it.
