# Qwen3.8-27B Run Comparison

**Date:** 2026-08-20  
**Protocol:** `tool-eval-69-perf-v1`  
**Purpose:** Select a Qwen3.8-27B checkpoint for further tuning toward agentic coding quality, safety, and two-agent responsiveness.

## Executive recommendation

- **Main quality/safety line: Frozenlock INT4 AutoRound.** It ties for the best score at **91**, has **zero safety warnings**, and is almost as fast as Avuja at concurrency 1. It is the best candidate for quality tuning and MTP experiments.
- **Speed line and control: Avuja INT4 AutoRound.** It has the best practical throughput, especially at concurrency 2: **14.61 t/s per agent at 8K** and **4.60 t/s per agent at 32K**, while scoring 88.
- **Quality-only alternative: goldhub INT4 W4A16 AutoRound.** It also scores 91 and has perfect code-pattern and structured-output scores, but gives up substantial short-context responsiveness and has one safety warning.
- **Do not prioritize official FP8 or Minachist INT8** for this hardware/workload. Neither provides a quality advantage over the best INT4 runs; both are slower at useful context lengths. FP8 performance is additionally affected by a tokenizer fallback.

The next step should be a **tokenizer-corrected, repeated rerun of Frozenlock, Avuja, and goldhub**, followed by one-variable-at-a-time tuning. All six workloads ran with the GPUs set to 350 W, so power does not require normalization here. Do not treat the current cross-checkpoint results as isolated causal experiments: checkpoint, quantization, and profile differences are confounded.

## Runs compared

| Label | Model/checkpoint | Run |
|---|---|---|
| Official FP8 | `Qwen/Qwen3.8-27B-FP8` | [`20260820T115256Z-qwen-qwen3-8-27b-fp8-0041b65d`](../runs/2026/08/20260820T115256Z-qwen-qwen3-8-27b-fp8-0041b65d/report.md) |
| Avuja INT4 | `Avuja/Qwen3.8-27B-int4-AutoRound` | [`20260819T180403Z-avuja-qwen3-8-27b-int4-autoround-c9f9fb98`](../runs/2026/08/20260819T180403Z-avuja-qwen3-8-27b-int4-autoround-c9f9fb98/report.md) |
| MKRWW INT4 | `MKRWW/Qwen3.8-27B-int4-AutoRound` | [`20260819T184714Z-mkrww-qwen3-8-27b-int4-autoround-21dd0010`](../runs/2026/08/20260819T184714Z-mkrww-qwen3-8-27b-int4-autoround-21dd0010/report.md) |
| goldhub W4A16 | `goldhub/Qwen3.8-27B-INT4-W4A16-AutoRound` | [`20260819T190857Z-goldhub-qwen3-8-27b-int4-w4a16-autoround-48a57d75`](../runs/2026/08/20260819T190857Z-goldhub-qwen3-8-27b-int4-w4a16-autoround-48a57d75/report.md) |
| Minachist INT8 | `Minachist/Qwen3.8-27B-INT8-AutoRound` | [`20260819T193216Z-minachist-qwen3-8-27b-int8-autoround-16e1df5e`](../runs/2026/08/20260819T193216Z-minachist-qwen3-8-27b-int8-autoround-16e1df5e/report.md) |
| Frozenlock INT4 | `Frozenlock/Qwen3.8-27B-int4-AutoRound` | [`20260820T123115Z-frozenlock-qwen3-8-27b-int4-autoround-00f126a1`](../runs/2026/08/20260820T123115Z-frozenlock-qwen3-8-27b-int4-autoround-00f126a1/report.md) |

## Comparability verdict

**Partially comparable, not a controlled ablation.** The runs align well on the benchmark and serving platform:

- Same 69-scenario `tool-eval-69-perf-v1` protocol, seed 42, quality temperature 0.0, and max turns 8.
- Same performance workload: `pp=2048`, `tg=128`, depths 0/8192/32768, concurrency 1/2, three performance repetitions, generation-throughput mode.
- Same vLLM `v0.27.1` image digest, dual RTX 3090 hardware, and TP=2.
- All six workloads were run with a 350 W GPU power limit. Later runs omitted the power-limit helper because 350 W was already configured.
- AutoRound baseline profiles use the same broad serving settings: BF16 compute, 262K context, two sequences, 0.90 GPU utilization, INT8 per-token-per-head KV cache, prefix caching disabled, Mamba cache mode `none`, chunked prefill, async scheduling, `qwen3_coder` tool parser, Qwen reasoning parser, thinking disabled/low effort, temperature 0.7, top-p 0.80, top-k 20, and presence penalty 1.5.

Important limitations:

1. **Checkpoint and quantization differ by design.** Quality and performance differences cannot be attributed to a single setting.
2. **Early telemetry is partly misdocumented.** The initial benchmark script could record the configured/restored power value and PCIe lane state rather than the effective benchmark-time values. The script was subsequently fixed. Treat the execution procedure as authoritative: all six workloads ran at 350 W; do not infer benchmark-time PCIe lanes from the early `run.json` snapshots.
3. **Official FP8 performance tokenizer was wrong.** `llama-benchy` could not load `qwen3.8-27b` and fell back to GPT-2. Its throughput, especially prefill-related values, should not be used as a precise absolute comparison.
4. **Quality variance is not measured.** Each quality result is one trial. Scenario-level repeats should be added before treating one- or two-point differences as stable.
5. The profile comments associate goldhub with group size 32 and more BF16-preserved layers, but this is not isolated against an otherwise identical export; the causal explanation remains a hypothesis.

## Quality results

Scores are higher-is-better. Safety warnings are lower-is-better.

### Overall and category scores

| Category | Official FP8 | Avuja INT4 | MKRWW INT4 | goldhub W4A16 | Minachist INT8 | Frozenlock INT4 |
|---|---:|---:|---:|---:|---:|---:|
| **Overall** | **87** | **88** | **88** | **91** | **88** | **91** |
| Safety warnings | 0 | 1 | 2 | 1 | 1 | **0** |
| Tool Selection | 67 | 100 | 100 | 100 | 67 | 100 |
| Parameter Precision | 100 | 100 | 100 | 100 | 100 | 100 |
| Multi-Step Chains | 75 | 75 | 75 | 75 | 75 | 75 |
| Restraint & Refusal | 100 | 100 | 100 | 100 | 100 | 100 |
| Error Recovery | 83 | 100 | 83 | 83 | 83 | 83 |
| Localization | 100 | 100 | 100 | 100 | 100 | 100 |
| Structured Reasoning | 100 | 100 | 67 | 100 | 100 | 100 |
| Instruction Following | 100 | 100 | 100 | 100 | 90 | 90 |
| Context & State | 70 | 80 | 85 | 85 | 70 | 80 |
| Code Patterns | 100 | 67 | 100 | 100 | 100 | 100 |
| Safety & Boundaries | 85 | 81 | 73 | 81 | 85 | 85 |
| Toolset Scale | 100 | 100 | 100 | 100 | 100 | 100 |
| Autonomous Planning | 67 | 83 | 83 | 67 | 83 | 83 |
| Creative Composition | 100 | 100 | 100 | 100 | 100 | 100 |
| Structured Output | 92 | 83 | 92 | 100 | 100 | 100 |

### Quality deltas versus Official FP8

| Variant | Overall delta | Safety-warning delta | Interpretation |
|---|---:|---:|---|
| Avuja INT4 | +1 | +1 | Higher aggregate score, but one warning. |
| MKRWW INT4 | +1 | +2 | Higher aggregate score, but two warnings and weak safety-boundary score. |
| goldhub W4A16 | **+4** | +1 | Best score, but one warning. |
| Minachist INT8 | +1 | +1 | No measured quality advantage over INT4. |
| Frozenlock INT4 | **+4** | **0** | Best score tied with goldhub and no reported safety warnings. |

The strongest quality profile is therefore **Frozenlock/goldhub at 91**, with Frozenlock preferred for the safety line. Goldhub's notable strengths are perfect `Code Patterns` and `Structured Output`; its weak areas are `Autonomous Planning` (67) and `Safety & Boundaries` (81). Frozenlock's main remaining gaps are `Context & State` (80), `Instruction Following` (90), and `Autonomous Planning` (83). Both runs have a TC-35/Kelvin-related caveat; goldhub reports it as a safety warning, while Frozenlock reports a related partial without a safety warning.

## Performance results

All values are generation throughput in tokens/second. For `c2`, aggregate is server-wide and **per-agent is the relevant responsiveness metric**.

| Variant | c1 @ 0K / 8K / 32K | c2 aggregate @ 0K / 8K / 32K | c2 per-agent @ 0K / 8K / 32K |
|---|---|---|---|
| Official FP8 | 60.86 / 39.59 / 20.85 | 77.11 / 21.66 / 6.43 | 38.56 / 10.83 / 3.21 |
| **Avuja INT4** | **68.73 / 62.33 / 49.32** | **77.21 / 29.23 / 9.20** | **38.61 / 14.61 / 4.60** |
| MKRWW INT4 | 68.64 / 62.37 / 49.34 | 76.99 / 29.22 / 8.68 | 38.49 / 14.61 / 4.34 |
| goldhub W4A16 | 50.11 / 46.64 / 38.90 | 62.47 / 26.85 / 8.96 | 31.23 / 13.43 / 4.48 |
| Minachist INT8 | 46.89 / 43.81 / 36.87 | 59.74 / 26.40 / 8.94 | 29.87 / 13.20 / 4.47 |
| Frozenlock INT4 | 68.39 / 62.19 / 49.25 | 66.23 / 22.75 / 7.39 | 33.12 / 11.37 / 3.70 |

### Speed deltas versus Avuja

The following deltas are calculated as `variant - Avuja`; negative values are slower. They are descriptive rather than causal because checkpoint, quantization, and serving-profile differences are confounded.

| Variant | c1 delta @ 0K / 8K / 32K | c2 per-agent delta @ 0K / 8K / 32K |
|---|---|---|
| Official FP8 | -7.87 / -22.74 / -28.47 | -0.05 / -3.78 / -1.39 |
| MKRWW INT4 | -0.09 / +0.04 / +0.02 | -0.12 / 0.00 / -0.26 |
| goldhub W4A16 | -18.62 / -15.69 / -10.42 | -7.38 / -1.18 / -0.12 |
| Minachist INT8 | -21.84 / -18.52 / -12.45 | -8.74 / -1.41 / -0.13 |
| Frozenlock INT4 | -0.34 / -0.14 / -0.07 | -5.49 / -3.24 / -0.90 |

Avuja is the best speed control on the measured profile. MKRWW is effectively tied in c1 and at 8K c2, but its two safety warnings make it a poor primary tuning target. Frozenlock's c1 performance is nearly tied with Avuja, but its c2 per-agent result is lower, especially at 0K/8K; repeat the measurement to determine whether that is a checkpoint/profile effect or ordinary run variance. Power is not the explanation, since all workloads ran at 350 W.

## Configuration differences that matter

### Shared AutoRound profile

The comparable AutoRound profiles broadly use BF16 compute, long context (262K), two sequences, INT8 KV, no prefix cache, no Mamba cache, chunked prefill, async scheduling, Qwen coder/tool parsers, and low/no thinking. This makes the Avuja/MKRWW/goldhub/Minachist results useful as a family comparison, but not a clean quantization-only test because the checkpoints and exports differ.

### Official FP8

The official profile differs materially: FP8 quantization, 0.92 GPU utilization, no explicit `mamba-cache-mode=none`, no async scheduling, and one-token MTP speculative decoding. It also lacks an explicit low reasoning-effort setting. These differences, plus the GPT-2 tokenizer fallback, make its performance a weak baseline for tuning decisions.

### Frozenlock

Frozenlock uses the AutoRound INT4 serving family but was run with a profile/compose revision distinct from the earlier AutoRound profiles. Its checkpoint documentation states that the MTP head is quantized, making it the most promising candidate for a controlled MTP test.

### goldhub

goldhub's profile documentation claims group size 32 and more BF16-preserved layers. The observed association is higher quality (91) with lower throughput (50.11 c1 t/s at 0K versus Avuja's 68.73), but this should be confirmed with a standardized serving profile and repeated measurement.

## Recommended next experiments

### 0. Re-establish a clean baseline first

Rerun **Frozenlock, Avuja, and goldhub** with:

- an explicit, correct tokenizer path for every performance run;
- the same compose/profile fingerprint and serving flags where the experiment is intended to compare checkpoints;
- the existing depths, concurrency levels, `pp`, `tg`, and three performance repetitions;
- at least repeated quality trials or scenario-level variance reporting.

All six current workloads ran at 350 W, so this rerun is for tokenizer correctness, repeatability, and configuration control—not power normalization. The early PCIe/power telemetry should also be treated as a recorder bug, not evidence that those workloads used different power limits or PCIe states.

### 1. Primary quality/safety track: Frozenlock

Keep Frozenlock as the quality control and change one variable at a time:

1. Native versus Froggeric chat template.
2. Sampling temperature around 0.5, 0.6, and 0.7.
3. Reduce or remove the presence penalty of 1.5.
4. Low versus default reasoning effort.
5. Tool parser/template combinations.

Quality gates: retain **91+**, retain **zero safety warnings**, improve `Context & State`/`Autonomous Planning`, and eliminate or clarify the TC-35 Kelvin behavior. Re-run performance after any serving change that could affect tool formatting or scheduling.

### 2. MTP track: Frozenlock first

Use MTP-disabled Frozenlock as the control. Test `MTP_K=1` first, then higher values only if stable. Measure quality/safety and c1 plus especially c2 per-agent throughput at 0K, 8K, and 32K. Watch for OOM, malformed tool calls, recurrent-state corruption, and long-context degradation. The quantized MTP head makes Frozenlock a better starting point than the other INT4 exports, but the current runs do not prove an MTP benefit.

### 3. Primary speed track: Avuja

Use Avuja as the throughput baseline and test serving-only changes:

- GPU utilization 0.90 → 0.92/0.94 if memory permits;
- prefill batch/max-num-batched-tokens;
- FlashInfer sampler;
- KV cache type;
- confirmed async scheduling;
- prefix caching only if it is safe with the chosen recurrent/MTP configuration.

After each meaningful serving change, run the quality suite because parser, sampler, and template changes can regress tool behavior.

### 4. Goldhub only if quality is the priority

Continue with goldhub only if the project accepts its responsiveness cost. First verify that the 91 score survives normalization. Then target its `Autonomous Planning` and TC-35 safety weakness without disturbing its perfect code-pattern and structured-output results.

## Bottom line

**Tune Frozenlock for the main agentic-coding quality/safety line; keep Avuja as the speed control; use goldhub as a quality-focused fallback.** The highest-value immediate experiment is not another checkpoint sweep—it is a tokenizer-corrected, repeatable baseline rerun, followed by Frozenlock MTP and one-variable serving/quality experiments. FP8 and INT8 are currently dominated for this dual-3090, two-agent workload.
