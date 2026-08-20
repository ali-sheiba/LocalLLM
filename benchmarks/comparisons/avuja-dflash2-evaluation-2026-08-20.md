# Avuja DFlash2 evaluation — 2026-08-20

## Verdict

**Do not promote Avuja profile 11.** The DFlash2 port boots cleanly and improves
single-stream decode on favorable prompts, but it misses the required two-agent
record by a wide margin under the canonical benchmark, has no prefix-cache reuse,
and still produces one quality warning.

The strongest replicated c2 result is about **33.5 t/s per agent**, not the
required **60+ t/s per agent** and not Lorbus's depth-0 **71.12 t/s per agent**.
DFlash2 also reprocessed repeated prefixes: after the complete evaluation,
`prefix_cache_hits_total=0` for about **1.90M queried tokens**.

## Runs compared

| Label | Run | Role |
|---|---|---|
| DFlash2 canonical | `benchmarks/runs/2026/08/20260820T174124Z-avuja-qwen3-8-27b-int4-autoround-212a7a5d/` | Correctly attributed P11 result; Avuja tokenizer explicitly supplied |
| DFlash2 replication | `benchmarks/runs/2026/08/20260820T172354Z-incoai-qwen3-8-27b-dflash2-46889170/` | Same effective stack and tokenizer; immutable metadata incorrectly attributes the target to the drafter mount |
| Avuja P10 | `benchmarks/runs/2026/08/20260820T160229Z-avuja-qwen3-8-27b-int4-autoround-6be7c157/` | Same target/image without speculation; performance used GPT-2 tokenizer fallback |
| Lorbus reference | `benchmarks/runs/2026/08/20260820T113142Z-lorbus-qwen3-6-27b-int4-autoround-f4faf298/` | User's target reference; different model/image and GPT-2 tokenizer fallback |

The first DFlash2 run remains immutable. Its Compose file, profile SHA, runtime
arguments, target tokenizer, and observed metrics match the canonical run; only
the benchmark helper's inferred model provenance selected `/models/drafter`
instead of `/models/model`. The second invocation supplied
`--model-source Avuja/Qwen3.8-27B-int4-AutoRound` to correct that metadata.

## Comparability

| Check | DFlash2 replicas | DFlash2 vs P10 | DFlash2 vs Lorbus |
|---|---|---|---|
| Protocol/tasks/seed/repetitions | Aligned | Aligned | Aligned |
| Tokenizer | Aligned, correct Avuja tokenizer | **Not aligned:** P10 fell back to GPT-2 | **Not aligned:** Lorbus fell back to GPT-2 |
| Target model | Aligned | Aligned | Different: Qwen3.8 Avuja vs Qwen3.6 Lorbus |
| Engine/image | Aligned: vLLM 0.27.1 | Aligned: vLLM 0.27.1 | Different: vLLM 0.27.1 vs 0.25.1 |
| Speculation | DFlash2 n=7 | DFlash2 n=7 vs none | DFlash2 n=7 vs built-in MTP n=3 |
| Context/cache/scheduler | Aligned | 131K/0.80/prefix-align/sync vs 262K/0.90/no-prefix/async | Materially different |
| Hardware | 2× RTX 3090, PCIe capability aligned | Aligned | Aligned |
| Power | 350 W | 350 W | 350 W |

**Verdict:** the DFlash2 replicas are directly comparable. P10 is only partially
comparable because its tokenizer fallback changed prompt construction and its
runtime configuration differs. Lorbus is a directional product target, not a
controlled A/B: model, image, tokenizer, and speculative method differ.

## Quality

Higher is better. All three reported configurations produced one safety warning;
none passes the requested zero-warning promotion gate.

| Metric/category | DFlash2 P11 | Avuja P10 | Lorbus |
|---|---:|---:|---:|
| **Overall** | **91** | 88 | **91** |
| Safety warnings (lower is better) | 1 | 1 | 1 |
| Tool Selection | 100 | 100 | 100 |
| Parameter Precision | 100 | 100 | 100 |
| Multi-Step Chains | 75 | 75 | 100 |
| Restraint & Refusal | 100 | 100 | 67 |
| Error Recovery | 83 | 83 | 83 |
| Localization | 100 | 100 | 100 |
| Structured Reasoning | 100 | 100 | 100 |
| Instruction Following | 100 | 100 | 100 |
| Context & State | 85 | 85 | 80 |
| Code Patterns | 67 | 67 | 83 |
| Safety & Boundaries | 88 | 81 | 88 |
| Toolset Scale | 100 | 100 | 100 |
| Autonomous Planning | 67 | 50 | 67 |
| Creative Composition | 100 | 100 | 100 |
| Structured Output | 100 | 92 | 100 |

P11 gained three overall points over P10, associated with better Safety &
Boundaries, Autonomous Planning, and Structured Output results. This must not be
attributed causally to DFlash2: speculative verification is intended to preserve
the target distribution, while scheduler/cache differences and evaluator/model
variance were not isolated. Both DFlash2 runs reproduced the same quality result.

## Performance

The DFlash2 columns use the correctly attributed canonical run. The replication
ranges show how much the same P11 configuration varied. `c2/agent` is aggregate
throughput divided by two and is the relevant responsiveness metric.

| Depth | Metric | DFlash2 P11 | P11 replication range | Avuja P10 | Lorbus |
|---:|---|---:|---:|---:|---:|
| 0 | c1 tg t/s | **92.52** | 85.86–92.52 | 69.69 | 74.02 |
| 0 | c2 aggregate t/s | 65.00 | 65.00–65.41 | 70.44 | **142.24** |
| 0 | **c2/agent t/s** | 32.50 | 32.50–32.71 | 35.22 | **71.12** |
| 8K | c1 tg t/s | **86.90** | 60.82–86.90 | 68.52 | 70.37 |
| 8K | c2 aggregate t/s | **66.89** | 66.89–67.95 | 25.94 | 28.83 |
| 8K | **c2/agent t/s** | **33.44** | 33.44–33.97 | 12.97 | 14.41 |
| 32K | c1 tg t/s | 64.15 | 64.15–82.30 | **66.57** | 65.44 |
| 32K | c2 aggregate t/s | 8.61 | 8.61–8.67 | 8.85 | **12.30** |
| 32K | **c2/agent t/s** | 4.31 | 4.31–4.33 | 4.43 | **6.15** |

### Directional deltas from the canonical run

| Depth | DFlash2 vs P10 c1 | DFlash2 vs P10 c2/agent | DFlash2 vs Lorbus c1 | DFlash2 vs Lorbus c2/agent |
|---:|---:|---:|---:|---:|
| 0 | +22.83 | −2.72 | +18.50 | **−38.62** |
| 8K | +18.38 | +20.47 | +16.53 | +19.03 |
| 32K | −2.42 | −0.12 | −1.29 | −1.84 |

These deltas are associations only. The P10/Lorbus tokenizer fallbacks and
configuration/model differences prevent causal interpretation.

## Runtime evidence beyond the benchmark

- The full v0.27.1 overlay applied and registered `DFlash2DraftModel`.
- The V2 model runner was selected.
- The local upstream compile-cache fix produced separate `dflash_head` and
  `dflash2_candidate_selector` compile namespaces.
- FlashInfer downgraded CUDA graphs to `PIECEWISE`, avoiding unsupported full
  graph capture for this spec-decode path.
- Actual logical KV pool with native DFlash2: **221,379 tokens**.
- Maximum reported concurrency at 131,072 tokens: **1.69×**. Two equal deep
  sessions can consume only about 110K tokens each before overhead/margin.
- The matched no-draft control at the same 0.80 memory utilization provided
  **508,268 KV tokens (3.88× at 131K)**. The native drafter therefore removed
  286,889 logical KV tokens, or **56.4%** of the control pool.
- Full-workload pooled draft acceptance: `36,031 / 75,122 = 48.0%`.
- Favorable 768-token coding micro-smoke: 124.15 t/s c1 and 118.60 t/s mean
  streamed decode at c2. This demonstrates prompt/output-length sensitivity; it
  is not a substitute for the canonical workload, whose c2 result was ~32.5.
- Repeated identical ~5K-token prompts: approximately 4.8 s end-to-end both
  times, with zero prefix hits.
- End-of-evaluation prefix metrics: roughly **1.90M queries / 0 hits**.
- Container stability: zero restarts, no OOM, and no observed CUDA/index fault
  during two full runs.
- vLLM warned that speculative slots reduced scheduled tokens from 8192 to
  8178; a later performance arm may test 16384, but this cannot solve prefix
  correctness or the 2× c2 gap by itself.

## Root-cause assessment for zero prefix reuse

vLLM classifies `dflash` as EAGLE-style speculation. On Qwen hybrid models, the
fallback marks all KV groups as EAGLE groups and reconciles prefix reuse to the
minimum resumable hit across full-attention and Mamba groups. The PR #48375
safety rewind drops the final recurrent-state block; where no earlier resumable
Mamba boundary is available, the Mamba hit becomes zero and therefore the global
hit becomes zero.

This behavior is independently reported on vLLM PR #52816. Removing the rewind
or removing DFlash from `use_eagle()` could make counters nonzero while reusing
stale recurrent/draft state, so those are not acceptable production fixes.

The correct architectural direction is successor-aware EAGLE hashing from
vLLM PR #50897, with the related hybrid boundary-state work in PR #52244. Both
are open/large changes and are not safely represented by a profile flag.

### Local no-draft control

`profiles/avuja-11-control-no-draft-prefix.env` kept the target, image,
Froggeric template, FP8 KV, 131K limit, prefix cache, Mamba align mode,
synchronous scheduler, and 0.80 memory utilization unchanged while setting
`DRAFT_SPEC_N=0`.

Two sequential identical ~5K-token prompts produced:

| Arm/request | End-to-end | Prefix metrics after two requests |
|---|---:|---:|
| DFlash2 first | 4.87 s | 0 hits |
| DFlash2 repeat | 4.82 s | 0 hits |
| No-draft first | 5.44 s | — |
| No-draft repeat | **1.37 s** | **4,704 hits / 10,102 queries** |

The repeat's end-to-end latency dropped 74.8% only when speculation was absent.
This isolates the zero-hit behavior to DFlash/spec-decode hybrid cache handling,
not tokenizer, chat template, request identity, or the underlying Avuja target.

## Recommendation and next plan

1. **Reject P11 for production and record chasing.** It fails c2 depth 0, the
   zero-warning quality gate, deep c2 responsiveness, two-full-131K capacity,
   and follow-up prefix reuse.
2. **Treat the no-draft APC control as confirmation:** repeated-prefix hits and
   TTFT recovery returned immediately when `DRAFT_SPEC_N=0`.
3. **Do not combine more speed toggles yet.** First instrument per-group hit
   lengths or backport successor-aware hashing. Validate A→A and A→B→A replay,
   byte-identical greedy output against APC-off, and repeated tool turns.
4. **After cache correctness is solved**, test a staged performance ladder:
   - P12: quantized `syvai/Qwen3.8-27B-DFlash2-W4A16` drafter only;
   - P13: raise batched tokens to 16384;
   - P14: async scheduling only after applying/validating the GDN spec-order fix.
5. Keep a separate BF16-KV/FlashAttention lane as a single-stream speed study,
   not as the two-large-session target.

The present evidence does not support promising that the next profile will beat
Lorbus. The next defensible milestone is **correct nonzero follow-up reuse with
DFlash2**; only then should throughput tuning resume.
