# AutoRound benchmark profiles

Each `.env` file is a version-controlled Compose environment profile. A profile
is one immutable hypothesis: after benchmarking it, update only its
`BENCHMARK_SUMMARY` comment block with `helpers/update-benchmark-profile.py`.
Copy a profile to a new descriptive filename for another hypothesis rather than
changing its assignments.

## Completed controls

| Control | Tool-eval | c1 tg t/s (0 / 8K / 32K) | c2 per-agent tg t/s (0 / 8K / 32K) | Focus |
|---|---:|---|---|---|
| `avuja.env` | 88 | 68.73 / 62.33 / 49.32 | 38.61 / 14.61 / 4.60 | c2 long-context responsiveness and tool quality |
| `mkrww.env` | 88 | 68.64 / 62.37 / 49.34 | 38.49 / 14.61 / 4.34 | structured reasoning and safety quality |
| `goldhub.env` | 91 | 50.11 / 46.64 / 38.90 | 31.23 / 13.43 / 4.48 | recover decode speed while preserving quality |
| `minachist.env` | 88 | 46.89 / 43.81 / 36.87 | 29.87 / 13.20 / 4.47 | tool selection/context quality and INT8 speed |
| `frozenlock.env` | pending | pending | pending | W4A16 control with a quantized MTP head; benchmark native-template stability first |

All controls used the same benchmark protocol, vLLM image, dual 3090 hardware,
and 350W benchmark power cap. They remain model-specific comparisons because
checkpoint quantization and chat templates differ.

## MKRWW experiments

Run performance profiles first, then quality profiles. The control already has
perfect Code Patterns, so do not trade it away for a small gain elsewhere.

| Profile | One change | Question |
|---|---|---|
| `mkrww-01-gpu-util-0.94.env` | GPU memory utilization `0.94` | Does more KV headroom help c2 8K/32K? |
| `mkrww-02-prefill-16384.env` | prefill batch `16384` | Can long-context TTFT/prefill improve safely? |
| `mkrww-03-flashinfer-sampler.env` | FlashInfer sampler on | Can sampled decode improve without quality loss? |
| `mkrww-04-tool-parser-xml.env` | `qwen3_xml` parser | Does native XML improve Structured Reasoning? |
| `mkrww-05-froggeric-template.env` | froggeric template | Does template formatting improve tools/safety? |
| `mkrww-06-thinking-low.env` | low-effort thinking on | Is the quality cost worth the throughput loss? |

## Goldhub experiments

Goldhub is the current quality leader, but is slower at c1 decode. Preserve its
quality score as the primary gate when testing its author-recommended cache path.

| Profile | One change | Question |
|---|---|---|
| `goldhub-01-gpu-util-0.92.env` | GPU memory utilization `0.92` | Does the author's former value improve c2 headroom safely? |
| `goldhub-02-fp8-kv.env` | FP8 E4M3 KV | Does Goldhub's preferred cache path help without Ampere quality regressions? |
| `goldhub-03-flashinfer-sampler.env` | FlashInfer sampler on | Can sampled decode recover some c1 throughput? |
| `goldhub-04-prefix-cache-align.env` | prefix cache + Mamba `align` | Does repeated-agent TTFT improve without cache corruption? |
| `goldhub-05-tool-parser-xml.env` | `qwen3_xml` parser | Does it improve Multi-Step Chains and Planning? |
| `goldhub-06-thinking-low.env` | low-effort thinking on | Does it improve planning enough to justify latency? |
| `goldhub-07-froggeric-template.env` | mounted froggeric template | Does it differ from Goldhub's native froggeric-v22-derived template? |

## Minachist experiments

Minachist is the heaviest checkpoint and the slowest at c1 decode. Its main
quality gaps are Tool Selection and Context & State, so memory/cache changes are
kept conservative and template/parser trials have clear quality gates.

| Profile | One change | Question |
|---|---|---|
| `minachist-01-gpu-util-0.92.env` | GPU memory utilization `0.92` | Can a modest extra KV pool help c2 safely? |
| `minachist-02-prefill-16384.env` | prefill batch `16384` | Can long-prompt TTFT improve within the INT8 VRAM budget? |
| `minachist-03-flashinfer-sampler.env` | FlashInfer sampler on | Can sampled decode improve without tool regressions? |
| `minachist-04-fp8-kv.env` | FP8 E4M3 KV | Is there a cache-path benefit without SM86 quality loss? |
| `minachist-05-prefix-cache-align.env` | prefix cache + Mamba `align` | Does repeated-agent Context & State improve safely? |
| `minachist-06-tool-parser-xml.env` | `qwen3_xml` parser | Can Tool Selection improve? |
| `minachist-07-froggeric-template.env` | froggeric template | Does tool/context behavior improve across multi-turn chains? |
| `minachist-08-thinking-low.env` | low-effort thinking on | Is the quality cost worth the latency? |

Every author now has an explicit repository-mounted froggeric-template
experiment: `avuja-07`, `mkrww-05`, `goldhub-07`, and `minachist-07`. Goldhub's
native template is already froggeric-v22-derived, so that arm specifically tests
whether the bundled and repository-mounted versions diverge. Compare each only
with its own native-template control.

MTP is intentionally not in this profile set. This includes Frozenlock, whose
checkpoint quantizes its MTP head. The existing unpatched Compose stack does not
expose a safe MTP toggle, and the available dual-3090 MTP evidence uses Club-3090
runtime patches and reports a two-sequence OOM risk. Add it later as a dedicated
compose experiment after the stable profile matrix is complete.

## Run and record

```sh
./helpers/run-benchmark.py \
  --stack models/qwen3.8-27b/autoround-int4/docker-compose.yml \
  --env-file models/qwen3.8-27b/autoround-int4/profiles/goldhub-03-flashinfer-sampler.env \
  --service vllm-qwen38-27b-autoround-int4 \
  --tokenizer /home/app/models/goldhub/Qwen3.8-27B-INT4-W4A16-AutoRound \
  --start \
  --power-limit 350
```

Use the profile's matching `MODEL_HOST_PATH` as `--tokenizer`. After a completed
run, update its summary with the profile-summary helper and record manual
long-session observations about loops, stalled calls, and malformed tool calls.
