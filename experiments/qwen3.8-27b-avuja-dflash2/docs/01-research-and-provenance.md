# Research and provenance

## Why DFlash2 was investigated

The Avuja Qwen3.8 AutoRound sweep had not reached the project's target of two genuinely
concurrent coding agents at at least 60 generation t/s each while preserving large
context and tool quality. Community reports published on 2026-08-19 and 2026-08-20
showed unusually high Qwen3.8-27B decode rates on dual RTX 3090 systems using DFlash2.
Those reports were treated as leads, not directly comparable benchmark evidence.

DFlash2 is an external block-diffusion drafter. It proposes a block in parallel, adds
short dynamic convolutions to reduce suffix decay, and uses a lightweight candidate
selector to choose a coherent path through each position's top candidates. The target
model verifies the proposals. Correct speculative verification is intended to preserve
greedy output and the target sampling distribution; it does **not** make every runtime,
cache, or scheduler integration automatically correct.

## Source map

Status and claims in this table are recorded as observed on **2026-08-20**.

| Source | Role in the investigation | What was taken from it |
|---|---|---|
| [Reddit: “218 tok/s single”](https://www.reddit.com/r/LocalLLaMA/comments/1vsccit/qwen3827b_on_2x_3090_vllm_dflash2_218_toks_single/) | Discovery | Headline dual-3090 single-stream result; not used as a promotion metric |
| [Reddit: “124 tps single request”](https://www.reddit.com/r/LocalLLaMA/comments/1vrw4sz/i_pushed_qwen3827b_to_124_tps_on_a_single_request/) | Discovery | A second prompt-dependent single-request data point |
| [Club-3090 PR #1056](https://github.com/noonghunna/club-3090/pull/1056) | Detailed community benchmark | 120.08 narrative / 218.33 code decode t/s, n=7, acceptance 47.8%, 131K context, custom bare-metal vLLM; also made the context and VRAM costs explicit |
| [oceanplexian/vllm PR #1](https://github.com/oceanplexian/vllm/pull/1) | Startup-fix trail | INC/AutoRound unquantized LM-head guard issue and temporary FlashInfer top-k fallback investigation |
| [vLLM PR #52883](https://github.com/vllm-project/vllm/pull/52883) | Upstream compatibility fix | Accept `UnquantizedLinearMethod` for quantized-body targets whose LM head remains unquantized |
| [DFlash2 upstream PR #52816](https://github.com/vllm-project/vllm/pull/52816) | Primary architecture source | Native `DFlash2DraftModel`, local convolution, candidate selector, V2 speculator, registry and runtime hooks |
| [Inco DFlash2 blog](https://inco.ai/blog/dflash2/) | Design and vendor evaluation | Architecture rationale and H200/SGLang claims; not a dual-3090 workload comparison |
| [Native drafter model card](https://huggingface.co/incoai/Qwen3.8-27B-DFlash2) | Checkpoint contract | BF16 2B-parameter draft model, block size 8, vLLM invocation with seven speculative tokens |
| [z-lab mirror](https://huggingface.co/z-lab/Qwen3.8-27B-DFlash2) | Checkpoint provenance | Mirror of the same native DFlash2 format |
| [DFlash code](https://github.com/z-lab/dflash) | Research implementation | Training/evaluation context for the DFlash family |
| [Tony dual-3090 recipe](https://github.com/tonyd2wild/Qwen3.8-27B-DFLASH2-AutoRound-W4A16-2x3090) | Deployment reference | Runtime-overlay approach, dual-tier framing, and measured drafter/KV tradeoff |
| Tony commit `bfa25155b9704b0496ecec783f5aa49f949bec43` | Historical recipe pin | State examined during the port investigation |
| [Club-3090 PR #1060](https://github.com/noonghunna/club-3090/pull/1060) | Earlier deployment integration | Intermediate DFlash2 backport/recipe lineage |
| [Club-3090 PR #1072](https://github.com/noonghunna/club-3090/pull/1072) | Selected runtime overlay | Hardened v0.27.1 backport and cache-safety patch set |
| [Speculators plugin commit `b9ee1f9`](https://github.com/thyways/speculators/commit/b9ee1f9) | Alternative integration | Released-vLLM plugin route for **Speculators-format** DFlash2 checkpoints |
| [syvai quantized drafter](https://huggingface.co/syvai/Qwen3.8-27B-DFlash2-W4A16) | Deferred follow-up | Potential VRAM/bandwidth recovery arm; not tested in P11 |

## Exact pins used locally

### Upstream implementation lineage

The initial DFlash2 implementation examined in vLLM PR #52816 was commit:

```text
19c9351904df4c63042671bc67a866ca48dc7d6f
```

The upstream branch continued evolving during the experiment. In particular, commit
`64c5b80cbf66b405cd000223fc4705fcf3bb2b50` added the selector compile namespace
hardening described below. This is why “PR #52816” alone is not a reproducible pin.

### Runtime overlay

The checked-in overlay was copied from Club-3090 PR #1072 at:

```text
b664aacf301c4195693e0be509cdb581bd099d96
```

It is vendored under:

- `vendor/vllm-dflash2-backport/`
- `vendor/vllm-pr48375-mamba-drop-eagle-block/`

The overlay targets `vllm/vllm-openai:v0.27.1`. Its Apache-2.0 provenance and drop
conditions are recorded in [`../vendor/UPSTREAM.md`](../vendor/UPSTREAM.md).

### Local compile-cache hardening

The Club pin predated part of the evolving upstream DFlash2 branch. The local patch
backports vLLM PR #52816 commit:

```text
64c5b80cbf66b405cd000223fc4705fcf3bb2b50
```

It creates a separate `dflash2_candidate_selector` compile namespace. Without it, the
selector can share the `dflash_head` namespace and load a compiled graph with an
incompatible input signature. Clearing persistent caches is not sufficient because the
collision can happen within one startup.

### Prefix/Mamba correctness patch

The experiment also applies vLLM PR #48375 commit:

```text
4532e8a9d85ea69e8770a7ee2b8085010a56ea64
```

This makes `MambaManager` honor the EAGLE final-block rewind. It is a correctness patch,
not a prefix-hit optimization. Removing it can expose stale recurrent state.

### Drafter checkpoint

The native drafter was downloaded to:

```text
/home/app/models/incoai/Qwen3.8-27B-DFlash2
```

Pinned Hugging Face revision:

```text
dedf8df68adfb1afeaf7b7480c0a0243108177b4
```

Observed download size was approximately 3.6 GB. The target remained:

```text
/home/app/models/Avuja/Qwen3.8-27B-int4-AutoRound
```

The drafter is not the served model and must not be recorded as target provenance.

## Integration alternatives considered

### 1. Build vLLM PR #52816 from source

Rejected for the first experiment. It would maximize fidelity to the moving upstream
branch but introduce a long build, toolchain variability, and a large rollback surface.
The project already had a stable v0.27.1 image and a community-tested backport.

### 2. Copy only `qwen3_dflash2.py`

Rejected as incomplete. The model file alone does not provide:

- model registry wiring;
- forced V2 model-runner selection;
- DFlash2 speculator initialization;
- proposal/sampling state plumbing;
- DFlash input and slot-allocation hardening;
- candidate path-walk kernels and rejection-sampling compatibility.

A partial port could boot incorrectly, silently run as DFlash1, corrupt proposal state,
or fail only under concurrency.

### 3. Use the Speculators plugin

Initially rejected because `thyways/speculators@b9ee1f9` translates and serves a
**Speculators-format** DFlash2 checkpoint. The downloaded `incoai`/`z-lab` checkpoint
is the native `DFlash2DraftModel` format expected by vLLM PR #52816. Converting formats
would add a second unvalidated variable and undermine provenance.

### 4. Use Tony's repository directly

Used as a reference, not copied wholesale. Its target checkpoint, topology assumptions,
benchmark protocol, and deployment scripts differ from this repository. The useful
pattern was the runtime overlay on a released vLLM image.

### 5. Use Club-3090's vendored v0.27.1 overlay

Selected because it offered the smallest reversible change:

- no custom image build;
- exact vendored files under the experiment directory;
- idempotent, anchor-checked installers that refuse boot on drift;
- native checkpoint compatibility;
- known dual-3090 lineage;
- easy matched no-draft control by setting `DRAFT_SPEC_N=0`.

The local compile namespace patch was added because the selected Club commit did not yet
contain upstream commit `64c5b80`.

## How to interpret community speed claims

The 218 t/s report was a code prompt in a single-stream benchmark on a custom bare-metal
vLLM build, with different power limits, target weights, sampling, backend, and KV dtype.
Club-3090 later reported 135–139 code t/s for an FP8-KV “superfast” tier and over 230 t/s
for a BF16-KV/FlashAttention “ultrafast” tier. Tony's recipe also showed large gains on
structured/code prompts but saturated aggregate throughput near 180 t/s.

These reports established that DFlash2 was worth testing. They did **not** establish:

- 60+ t/s for each of two simultaneous agent sessions;
- performance at 8K and 32K depth;
- large-prefix follow-up reuse;
- equivalent tool/safety behavior;
- two full 131K resident sessions on 48 GB total VRAM.

The local canonical benchmark and controlled prefix probe therefore remain the decision
evidence for this project.
