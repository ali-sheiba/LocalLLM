# Avuja Qwen3.8-27B DFlash2 experiment

Isolated DFlash2 serving experiment for dual PCIe RTX 3090s. It does not modify
the canonical Avuja Compose stack and must not be started while another GPU
stack is active.

## Detailed experiment record

See [`docs/README.md`](docs/README.md) for the complete research provenance, port
architecture, immutable benchmark analysis, prefix-cache root cause, reproduction
procedure, failed approaches, and gated future-work plan.

## Why this lane

- Official vLLM `v0.27.1` does not contain DFlash2.
- The native `incoai/Qwen3.8-27B-DFlash2` checkpoint requires the complete V2
  model/speculator integration, not only `qwen3_dflash2.py`.
- This experiment pins Club-3090's hardened v0.27.1 backport and adds upstream's
  candidate-selector compile-cache namespace fix.
- The target remains Avuja; speculative tokens are verified by the target, so
  DFlash2 should not change accepted output. Tool/template/sampling settings are
  kept aligned with the Avuja tuning series.

## Initial profile

`profiles/avuja-11-dflash2-fp8-kv.env` is the two-session lane:

- DFlash2 `n=7`
- FP8 E4M3 KV
- 131,072 max model length
- `MAX_NUM_SEQS=2`
- prefix cache on with Mamba `align`
- async scheduling off for the first correctness soak
- Froggeric template and existing Avuja tool/sampling settings

The 131K window is a capacity trade, not a model limit. Avuja's measured pool
with the native BF16 drafter was 221,379 logical tokens: 1.69× at 131K, or about
110K per session if two sessions grow evenly. The matched no-draft control
provided 508,268 tokens (3.88× at 131K).

## Measured result

P11 is **rejected**, not a promotion candidate. See
`benchmarks/comparisons/avuja-dflash2-evaluation-2026-08-20.md`.

- Canonical run: `benchmarks/runs/2026/08/20260820T174124Z-avuja-qwen3-8-27b-int4-autoround-212a7a5d/`
- Tool quality: 91 with one safety warning
- c1: 92.52 / 86.90 / 64.15 t/s at 0 / 8K / 32K
- c2 per agent: 32.50 / 33.44 / 4.31 t/s
- Full-workload pooled draft acceptance: 48.0%
- Stability: zero restarts and no observed CUDA/index fault across two full runs
- Prefix reuse: zero hits across roughly 1.90M queried tokens

The diagnostic `profiles/avuja-11-control-no-draft-prefix.env` restored 4,704
prefix hits on two identical ~5K prompts and reduced repeated-request latency
from 5.44 s to 1.37 s. DFlash2 stayed near 4.8 s on both requests. This isolates
the follow-up regression to speculative/hybrid cache handling.

## Prepare the drafter

Download the pinned public checkpoint revision outside any running-container
cutover:

```bash
docker run --rm \
  --entrypoint hf \
  -v /home/app/models:/models \
  vllm/vllm-openai:v0.27.1 \
  download incoai/Qwen3.8-27B-DFlash2 \
  --revision dedf8df68adfb1afeaf7b7480c0a0243108177b4 \
  --local-dir /models/incoai/Qwen3.8-27B-DFlash2
```

The explicit entrypoint is required on this host: the image otherwise interprets `hf`
as a `vllm` subcommand, and no host `hf` executable was available during the experiment.

## Render without starting

```bash
docker compose \
  --env-file profiles/avuja-11-dflash2-fp8-kv.env \
  -f docker-compose.yml config
```

## Start only after the active GPU session ends

```bash
docker compose \
  --env-file profiles/avuja-11-dflash2-fp8-kv.env \
  -f docker-compose.yml up -d
```

Expected boot evidence:

- `[dflash2] applied vLLM PR#52816 backport`
- `[dflash2-local] candidate-selector compile namespace applied`
- speculative config reports `method='dflash'`, drafter `/models/drafter`, `n=7`
- V2 model runner selected
- non-zero DFlash acceptance metrics after requests

## Validation order

1. Boot with restart disabled and inspect patch/model-runner logs.
2. Run short c1 and true simultaneous c2 requests; verify acceptance remains
   materially above `1.0` and no CUDA/index errors occur.
3. Run the repository benchmark with the Avuja tokenizer explicitly:

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

4. Require c2 depth-0 throughput above Lorbus's measured 71.12 t/s per agent.
5. Repeat tool-eval; require at least 91 and zero safety warnings.
6. Soak two agent sessions past 20K generated tokens, through compression and
   tool-heavy turns. Track acceptance and container restarts.
7. Measure follow-up TTFT and prefix-cache hits to detect full-context
   reprocessing.

Do not promote from a single throughput result. DFlash2 upstream remains open
and has community reports of concurrency faults, bad CUDA-graph acceptance, and
follow-up context reprocessing.

## Follow-up arms

Do not tune for promotion until prefix reuse is correct. The architectural fix
is successor-aware EAGLE/DFlash hashing (vLLM PR #50897), with hybrid boundary
state work from PR #52244; bypassing the safety rewind can reuse stale state.

After A→A and A→B→A cache correctness passes:

1. Replace the BF16 drafter with `syvai/Qwen3.8-27B-DFlash2-W4A16` as the only
   variable to recover VRAM and reduce drafter bandwidth.
2. Raise batched tokens to 16,384 to remove the speculative-slot scheduling
   warning.
3. Test async scheduling only after applying and validating the GDN spec-order
   fix.
4. Keep BF16 KV + `FLASH_ATTN` as a separate single-stream speed study; it is
   not the two-large-session target on two 24 GB cards.
