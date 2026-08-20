# Avuja Qwen3.8-27B AutoRound Profile Sweep

- **Date:** 2026-08-20
- **Model:** `Avuja/Qwen3.8-27B-int4-AutoRound`
- **Protocol:** `tool-eval-69-perf-v1`
- **Purpose:** Select the next Avuja profile for two parallel agentic-coding sessions and define the next tuning sequence.

## Executive conclusion

- **Best two-agent performance base: P04 (`avuja-04-fp8-kv.env`) as actually executed.** Its recorded container had both **FlashInfer sampling and FP8 E4M3 KV**, not FP8 KV alone. Among profiles with `MAX_NUM_SEQS=2`, it leads c1 at all depths (**70.01 / 68.78 / 66.40 t/s**) and c2 per-agent at 32K (**5.48 t/s**), with score **89** and no safety warning.
- **Best quality candidate: P07 (`avuja-07-froggeric-template.env`).** It scored **91** with no safety warning, but the gain is only 3 raw points out of 138, there was one quality trial, and responsiveness was the lowest of the sweep. Treat Froggeric as a promising hypothesis, not a proven quality win.
- **P09 is a one-stream MTP speed record, not the serving winner.** It sets the absolute c1 records (**82.81 / 84.96 / 68.57 t/s**) but allows only one active sequence, so c2 requests queue and per-agent throughput falls to **25.48 / 10.67 / 3.83 t/s**. The development-session tool loop after context compression and the reported long-run MTP acceptance collapse make it unsuitable for promotion.
- **P05's 8K c2 record is provisional.** Its **18.82 t/s per agent** mean has high run-to-run spread, and `llama-benchy --no-cache` does not validate the intended repeated-prefix benefit. It also scored 88 with one safety warning.
- **Next profile:** `avuja-10-fp8-kv-froggeric.env` combines the strongest two-agent performance path actually measured (FlashInfer + FP8 KV) with the only plausible semantic quality lead (Froggeric). It deliberately keeps MTP and prefix caching off, uses two sequences, and makes async scheduling explicit.

No measured profile dominates every metric. The next target is therefore a **new production Pareto record**: reproduce P07's quality while retaining P04-like two-agent performance. It is not realistic to require a stable two-agent profile to beat P09's one-stream MTP c1 numbers simultaneously.

## Runs compared

| Code | Profile | Run |
|---|---|---|
| P01 | `avuja-01-gpu-util-0.94.env` | [`20260819T195658Z-avuja-qwen3-8-27b-int4-autoround-4f0a879b`](../runs/2026/08/20260819T195658Z-avuja-qwen3-8-27b-int4-autoround-4f0a879b/report.md) |
| P02 | `avuja-02-prefill-16384.env` | [`20260820T084730Z-avuja-qwen3-8-27b-int4-autoround-781666d6`](../runs/2026/08/20260820T084730Z-avuja-qwen3-8-27b-int4-autoround-781666d6/report.md) |
| P03 | `avuja-03-flashinfer-sampler.env` | [`20260820T090652Z-avuja-qwen3-8-27b-int4-autoround-4b90c1c7`](../runs/2026/08/20260820T090652Z-avuja-qwen3-8-27b-int4-autoround-4b90c1c7/report.md) |
| P04 | `avuja-04-fp8-kv.env` | [`20260820T092927Z-avuja-qwen3-8-27b-int4-autoround-53ad978e`](../runs/2026/08/20260820T092927Z-avuja-qwen3-8-27b-int4-autoround-53ad978e/report.md) |
| P05 | `avuja-05-prefix-cache-align.env` | [`20260820T094951Z-avuja-qwen3-8-27b-int4-autoround-aef5842c`](../runs/2026/08/20260820T094951Z-avuja-qwen3-8-27b-int4-autoround-aef5842c/report.md) |
| P06 | `avuja-06-tool-parser-xml.env` | [`20260820T100811Z-avuja-qwen3-8-27b-int4-autoround-fbc853aa`](../runs/2026/08/20260820T100811Z-avuja-qwen3-8-27b-int4-autoround-fbc853aa/report.md) |
| P07 | `avuja-07-froggeric-template.env` | [`20260820T102849Z-avuja-qwen3-8-27b-int4-autoround-84de9b81`](../runs/2026/08/20260820T102849Z-avuja-qwen3-8-27b-int4-autoround-84de9b81/report.md) |
| P08 | `avuja-08-tool-sampling-temp-0.6.env` | [`20260820T105159Z-avuja-qwen3-8-27b-int4-autoround-a874a23f`](../runs/2026/08/20260820T105159Z-avuja-qwen3-8-27b-int4-autoround-a874a23f/report.md) |
| P09 | `avuja-09-mtp-3-fp8-prefix.env` | [`20260820T140014Z-avuja-qwen3-8-27b-int4-autoround-af994635`](../runs/2026/08/20260820T140014Z-avuja-qwen3-8-27b-int4-autoround-af994635/report.md) |

## Comparability verdict

**Partially comparable and suitable for descriptive profile selection, but not for a causal ranking of every declared profile change.**

### Aligned conditions

- Same `tool-eval-69-perf-v1` protocol and all 69 quality scenarios.
- Quality: seed 42, request temperature 0.0, one trial, concurrency 1, max 8 turns, 120-second timeout, evaluator fingerprint `713e814ba311`.
- Performance: `llama-benchy 0.4.0`, `pp=2048`, `tg=128`, depths 0/8192/32768, concurrency 1/2, three repetitions, generation mode, correct Avuja tokenizer path, `--no-cache`, and `--skip-coherence`.
- Same checkpoint, model path, served name, native quantized weights, dual RTX 3090 GPUs, TP=2, NVIDIA driver `595.91.07`, and vLLM `0.27.1` image digest `sha256:0a51ea5b…`.
- Both GPUs were operated at a 350 W benchmark power limit. P01 raised them from 230 W to 350 W; its top-level run status is `failed` only because restoring 230 W failed after the complete performance and quality commands. P02–P09 began at 350 W.

### Limitations

1. **One quality trial per profile:** quality variance is unknown. The integer 88–91 spread is only 122–125 raw points out of 138.
2. **Recorded runtime differs from profile comments:** P04 and P05 both had `VLLM_USE_FLASHINFER_SAMPLER=1` in their canonical container snapshots. Therefore P04 is FlashInfer + FP8 KV, and P05 is FlashInfer + prefix cache/aligned Mamba state. The report uses the runtime snapshots as authoritative.
3. **P09 changes several dimensions:** MTP k=3, FP8 KV, prefix caching, aligned Mamba state, one sequence, async scheduling off, and a newer compose SHA. It is not an isolated MTP ablation.
4. **Concurrency mismatch in P09:** the benchmark sends two requests, but `MAX_NUM_SEQS=1` prevents two simultaneously active sequences. Its c2 aggregate divided by two is reported as required, but it does not represent two concurrent active agents.
5. **Prefix cache is not directly tested:** the performance command uses `--no-cache`; P05 requires a repeated-prefix/manual test before its intended benefit can be accepted.
6. CPU/RAM details, locked GPU clocks, and a continuous thermal trace are not recorded. End snapshots show the same GPU/driver/power family and active clocks around 1905–1935 MHz, but full thermal normalization is unavailable.
7. P09 is the only profile with a development-session observation. P01–P08 manual long-session notes remain pending.

## Configuration matrix (recorded runtime)

| Profile | Seqs | Batch tokens | GPU util | KV | Prefix / Mamba | Async | FlashInfer | Tool/template | MTP |
|---|---:|---:|---:|---|---|---|---|---|---:|
| P01 | 2 | 8192 | 0.94 | INT8 per-token/head | off / none | on | off | coder / native | off |
| P02 | 2 | 16384 | 0.90 | INT8 per-token/head | off / none | on | off | coder / native | off |
| P03 | 2 | 8192 | 0.90 | INT8 per-token/head | off / none | on | **on** | coder / native | off |
| P04 | 2 | 8192 | 0.90 | **FP8 E4M3** | off / none | on | **on** | coder / native | off |
| P05 | 2 | 8192 | 0.90 | INT8 per-token/head | **on / align** | on | **on** | coder / native | off |
| P06 | 2 | 8192 | 0.90 | INT8 per-token/head | off / none | on | off | **XML** / native | off |
| P07 | 2 | 8192 | 0.90 | INT8 per-token/head | off / none | on | off | coder / **Froggeric** | off |
| P08 | 2 | 8192 | 0.90 | INT8 per-token/head | off / none | on | off | coder / native; server default temp 0.6 | off |
| P09 | **1** | 8192 | 0.90 | FP8 E4M3 | **on / align** | **off** | off | coder / native | **3** |

P08's server-default temperature did not control the quality requests because the evaluator explicitly sent temperature 0.0.

## Quality metrics

Higher is better except safety warnings, where lower is better. Completion rate is unavailable in every canonical report.

| Profile | Raw points | Overall | Delta vs P01 | Completion | Safety warnings | Deployability | Responsiveness |
|---|---:|---:|---:|---:|---:|---:|---:|
| P01 | 122/138 | 88 | — | — | 1 | 80 | 61 |
| P02 | 124/138 | 90 | +2 | — | **0** | 80 | 58 |
| P03 | 122/138 | 88 | 0 | — | 1 | 78 | 56 |
| P04 | 123/138 | 89 | +1 | — | **0** | 80 | 58 |
| P05 | 122/138 | 88 | 0 | — | 1 | **84** | **74** |
| P06 | 122/138 | 88 | 0 | — | 1 | 78 | 55 |
| P07 | **125/138** | **91** | **+3** | — | **0** | 80 | 54 |
| P08 | 122/138 | 88 | 0 | — | 1 | 78 | 56 |
| P09 | 123/138 | 89 | +1 | — | **0** | 80 | 60 |

### Category scores

| Category | P01 | P02 | P03 | P04 | P05 | P06 | P07 | P08 | P09 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Tool Selection | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 100 |
| Parameter Precision | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 100 |
| Multi-Step Chains | 75 | 75 | 75 | 75 | 75 | 75 | 75 | 75 | 75 |
| Restraint & Refusal | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 100 |
| Error Recovery | 100 | 100 | 100 | 100 | 100 | 100 | **83** | 100 | 100 |
| Localization | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 100 |
| Structured Reasoning | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 100 |
| Instruction Following | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 100 |
| Context & State | 80 | 80 | 80 | 80 | 80 | 80 | **85** | 80 | **85** |
| Code Patterns | 67 | 67 | 67 | 67 | 67 | 67 | 67 | 67 | 67 |
| Safety & Boundaries | 81 | **88** | 81 | 85 | 81 | 81 | **88** | 81 | 85 |
| Toolset Scale | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 100 | **88** |
| Autonomous Planning | 83 | 83 | 83 | 83 | 83 | 83 | **100** | 83 | 83 |
| Creative Composition | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 100 |
| Structured Output | 83 | 83 | 83 | 83 | 83 | 83 | 83 | 83 | 83 |

### Quality stability

- **63 of 69 scenario statuses are invariant** across all nine runs.
- Seven scenarios are non-pass in every profile: `TC-30`, `TC-34`, `TC-46`, `TC-50`, `TC-57`, `TC-61`, and `TC-68`.
- Only `TC-14`, `TC-35`, `TC-39`, `TC-51`, `TC-60`, and `TC-62` vary.
- `TC-35` alone accounts for all of P02's gain, all of P04's gain, and part of P07/P09's gains. It moves between fail, partial, and pass under unrelated serving changes.
- P07's net +3 raw points is broader than P02/P04: gains on `TC-35`, `TC-51`, `TC-60`, and `TC-62`, offset by a regression on `TC-14`. Its `TC-68` remains failed and changes failure mode to invalid JSON.
- P01, P03, P05, P06, and P08 have the same category vector and 122/138 raw score.

**Interpretation:** most of the apparent 88–91 ranking is likely path-level/single-trial variation. Froggeric is the only change with a direct semantic mechanism and multi-scenario movement, so it deserves replication; it has not yet earned promotion.

## Performance metrics

All values are generation tokens/second. c2 per-agent is aggregate throughput divided by two and is the relevant responsiveness metric. Higher is better.

| Profile | c1 0 / 8K / 32K | c2 aggregate 0 / 8K / 32K | c2 per-agent 0 / 8K / 32K |
|---|---|---|---|
| P01 | 68.68 / 62.41 / 49.38 | **77.25** / 29.28 / 9.21 | **38.62** / 14.64 / 4.60 |
| P02 | 68.56 / 62.36 / 49.35 | 73.05 / 26.75 / 10.78 | 36.52 / 13.37 / 5.39 |
| P03 | 69.31 / 62.88 / 49.73 | 71.90 / 25.45 / 8.13 | 35.95 / 12.72 / 4.06 |
| **P04** | **70.01 / 68.78 / 66.40** | 74.05 / 28.15 / **10.96** | 37.03 / 14.07 / **5.48** |
| P05 | 68.75 / 62.60 / 49.45 | 70.98 / **37.63** / 9.06 | 35.49 / **18.82** / 4.53 |
| P06 | 68.30 / 62.05 / 49.18 | 69.86 / 24.67 / 7.94 | 34.93 / 12.34 / 3.97 |
| P07 | 68.24 / 62.04 / 50.01 | 70.07 / 22.14 / 7.96 | 35.03 / 11.07 / 3.98 |
| P08 | 68.33 / 62.16 / 49.22 | 69.98 / 24.73 / 7.95 | 34.99 / 12.37 / 3.97 |
| P09 | **82.81 / 84.96 / 68.57** | 50.96 / 21.35 / 7.66 | 25.48 / 10.67 / 3.83 |

Bold P09 c1 values are absolute one-stream records. Bold P04 values are records among profiles capable of two active sequences.

### Deltas versus P01

| Profile | Overall | c1 delta 0 / 8K / 32K | c2 per-agent delta 0 / 8K / 32K |
|---|---:|---|---|
| P02 | +2 | -0.13 / -0.05 / -0.03 | -2.10 / -1.27 / **+0.79** |
| P03 | 0 | +0.62 / +0.47 / +0.35 | -2.67 / -1.92 / -0.54 |
| P04 | +1 | +1.32 / **+6.37 / +17.02** | -1.60 / -0.57 / **+0.88** |
| P05 | 0 | +0.07 / +0.19 / +0.07 | -3.13 / **+4.18** / -0.08 |
| P06 | 0 | -0.39 / -0.36 / -0.20 | -3.69 / -2.30 / -0.63 |
| P07 | +3 | -0.45 / -0.37 / +0.63 | -3.59 / -3.57 / -0.62 |
| P08 | 0 | -0.35 / -0.25 / -0.15 | -3.63 / -2.27 / -0.63 |
| P09 | +1 | **+14.13 / +22.55 / +19.19** | **-13.14 / -3.96 / -0.78** |

### Controlled associations available inside the sweep

Because the recorded runtime is authoritative:

- **P03 → P04** keeps FlashInfer on and changes INT8 KV to FP8 KV. Associated deltas are c1 **+0.70 / +5.90 / +16.67 t/s** and c2 per-agent **+1.08 / +1.35 / +1.42 t/s**. This is the strongest and most consistent serving result.
- **P03 → P05** keeps FlashInfer and INT8 KV, adding prefix cache + aligned Mamba state. It is associated with c2 8K **+6.09 t/s per agent**, but little c1 change and high c2 8K spread. A cached-prefix workload is needed before attributing that gain to cache reuse.
- P06's XML parser and P08's lower server default do not show a quality gain. P08 did not actually vary evaluator sampling temperature.
- P09 is not a controlled MTP comparison because sequence capacity, async scheduling, KV/cache settings, and compose revision also differ.

## Development-session evidence for P09

The only manual observation is from the same development session used for Frozenlock:

- At roughly 128K configured agent context, the model entered a tool-call loop after context compression.
- It eventually completed after a steer.
- Community testing already warned that Avuja MTP draft acceptance may collapse to 0% after roughly 14.5K generated tokens.

This does not prove MTP caused the loop, because P09 also uses FP8 KV and prefix/aligned recurrent caching. It is sufficient to reject P09 as a stable baseline until those factors are isolated and long-run acceptance is instrumented.

## Recommendation and next profile

Create and test [`avuja-10-fp8-kv-froggeric.env`](../../models/qwen3.8-27b/autoround-int4/profiles/avuja-10-fp8-kv-froggeric.env):

- FlashInfer sampler explicitly on, matching P04's recorded runtime.
- FP8 E4M3 KV, the strongest measured two-agent performance change.
- Froggeric chat template, the only plausible semantic quality lead.
- Two sequences and async scheduling enabled.
- MTP off, prefix cache off, Mamba cache mode `none`.
- Batch tokens remain 8192 so the first synthesis changes only the template relative to a reproducible P04-like serving base.

### Promotion gates

The profile should be promoted only if it establishes a reproducible Pareto improvement:

1. **Quality replication:** run at least 3 quality trials. Target median **≥125/138 (91)**, every trial with zero safety warnings, and persistent gains in `TC-51`, `TC-60`, and `TC-62` without recurring `TC-14` or invalid-JSON regressions.
2. **Performance retention:** c1 at 32K **≥64.4 t/s** (within 3% of P04), c2 per-agent at 32K **≥5.30 t/s**, c1 at 0 **≥68 t/s**, and c2 per-agent at 0 **≥36 t/s**.
3. **Two-agent manual soak:** two concurrent development sessions, including context compression and at least one long tool chain per session. Reject on tool loops, malformed calls, stalled requests, recurrent-state corruption, or OOM.
4. **Runtime verification:** confirm the canonical container snapshot shows `MAX_NUM_SEQS=2`, FP8 KV, FlashInfer on, Froggeric template, async on, prefix off, and MTP disabled. Do not trust profile comments alone.

## Subsequent tuning plan

Proceed only after P10 passes its gate:

1. **P11: add `MAX_NUM_BATCHED_TOKENS=16384` to P10.** Target c2 32K while preserving P10 quality and c1. This is the next clean performance ablation.
2. **P12: add prefix cache + Mamba `align` to the winning non-MTP profile.** Evaluate with a dedicated repeated-system/tool-schema benchmark plus manual multi-turn sessions; `llama-benchy --no-cache` is insufficient.
3. **Keep MTP on a separate experimental branch.** Start with a reproducible two-sequence control and MTP k=1, record draft acceptance over more than 20K generated tokens, then test k=2/3 only if acceptance and tool behavior remain stable. Never combine an unvalidated MTP step with a production promotion.
4. **Quality work should target the invariant failure core:** incomplete tool phases (`TC-46`, `TC-50`, `TC-57`), failure to execute (`TC-61`), unnecessary tools/invalid structured output (`TC-68`), ungrounded branches (`TC-30`), and injection-payload repetition (`TC-34`). Serving knobs alone did not move these failures.

## Bottom line

**Promote neither P07 nor P09 directly. Build P10 from P04's actual two-agent performance path plus P07's template, replicate quality, and require a two-agent soak.** P04 gives the strongest measurable base; P07 gives the only credible quality hypothesis; P09 demonstrates that MTP can accelerate one stream but currently conflicts with the project's two-session stability objective.
