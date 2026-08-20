# Avuja Qwen3.8-27B DFlash2 experiment record

This directory is the durable technical record for the DFlash2 serving experiment in
`experiments/qwen3.8-27b-avuja-dflash2/`. It records the implementation and the
negative result as of **2026-08-20**. Benchmark runs are immutable; this documentation
interprets them but does not replace their `run.json` records.

## Executive conclusion

The native DFlash2 port was technically successful but is **not suitable for the
project's production target** in its tested form.

What worked:

- Stock `vllm/vllm-openai:v0.27.1` was extended at container startup without building
  a custom image.
- The native BF16 `incoai/Qwen3.8-27B-DFlash2` drafter ran through vLLM's V2 model
  runner against the Avuja AutoRound INT4 target.
- Two complete benchmark runs finished with no restart, OOM, CUDA index fault, or
  observed acceptance collapse.
- A favorable 768-token coding smoke reached 124.15 t/s at c1 and 118.60 t/s mean
  streamed decode per agent at c2.

What failed:

- The canonical result was only **32.50 t/s per agent at c2 depth 0**, versus the
  required 60+ and Lorbus's directional 71.12 t/s reference.
- c2 performance collapsed to **4.31 t/s per agent at 32K depth**.
- Tool quality scored 91 but produced one safety warning, failing the zero-warning
  promotion gate.
- DFlash2 reduced the logical KV pool from 508,268 to 221,379 tokens under the matched
  control envelope, leaving only 1.69× 131K concurrency.
- Prefix caching recorded **zero hits across about 1.90 million queried tokens**. A
  matched no-draft control immediately restored 4,704 hits and cut repeated-request
  latency from 5.44 s to 1.37 s.

**Decision:** reject P11, do not create a speed-tuned P12 on top of the unresolved
cache behavior, and do not present community single-stream headlines as evidence for
two-agent performance. If this lane is resumed, the first milestone is safe, nonzero
follow-up prefix reuse under DFlash2—not another throughput toggle.

## Documents

1. [Research and provenance](01-research-and-provenance.md) — discovery trail,
   upstream claims, source pins, checkpoint choice, and alternatives considered.
2. [Port architecture](02-port-architecture.md) — runtime overlay, required DFlash2
   components, local patches, profile, and boot behavior.
3. [Results and analysis](03-results-and-analysis.md) — immutable runs, comparability,
   quality, performance, acceptance, capacity, and stability.
4. [Prefix-cache root cause](04-prefix-cache-root-cause.md) — controlled A/B,
   EAGLE/hybrid cache interaction, unsafe shortcuts, and correct fix direction.
5. [Reproduction and future work](05-reproduction-and-future-work.md) — download,
   start/stop, validation, benchmark commands, probes, and staged resume plan.

## Artifact map

| Artifact | Purpose |
|---|---|
| [`../docker-compose.yml`](../docker-compose.yml) | Isolated vLLM v0.27.1 runtime-overlay stack |
| [`../profiles/avuja-11-dflash2-fp8-kv.env`](../profiles/avuja-11-dflash2-fp8-kv.env) | Rejected DFlash2 P11 profile |
| [`../profiles/avuja-11-control-no-draft-prefix.env`](../profiles/avuja-11-control-no-draft-prefix.env) | Matched no-draft prefix-cache control |
| [`../smoke_concurrency.py`](../smoke_concurrency.py) | True simultaneous streamed c1/c2 micro-smoke |
| [`../local-patches/patch_candidate_selector_namespace.py`](../local-patches/patch_candidate_selector_namespace.py) | Compile-cache namespace hardening |
| [`../vendor/UPSTREAM.md`](../vendor/UPSTREAM.md) | Vendored source pins and licensing |
| [`../../../benchmarks/comparisons/avuja-dflash2-evaluation-2026-08-20.md`](../../../benchmarks/comparisons/avuja-dflash2-evaluation-2026-08-20.md) | Formal benchmark comparison and recommendation |
| [`../../../benchmarks/runs/2026/08/20260820T174124Z-avuja-qwen3-8-27b-int4-autoround-212a7a5d/`](../../../benchmarks/runs/2026/08/20260820T174124Z-avuja-qwen3-8-27b-int4-autoround-212a7a5d/) | Canonical, correctly attributed run |
| [`../../../benchmarks/runs/2026/08/20260820T172354Z-incoai-qwen3-8-27b-dflash2-46889170/`](../../../benchmarks/runs/2026/08/20260820T172354Z-incoai-qwen3-8-27b-dflash2-46889170/) | Replication with incorrect model provenance metadata |

## Evidence labels used here

- **Measured:** observed locally and preserved in a run artifact, profile note, or
  comparison report.
- **Calculated:** arithmetic derived from measured values.
- **Upstream/community claim:** useful for hypothesis generation, but not evidence that
  the result generalizes to this project.
- **Interpretation:** technically supported explanation that still requires an isolated
  implementation test before being called a proven causal fix.
