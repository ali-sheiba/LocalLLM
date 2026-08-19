# Qwen3.8-27B benchmark stacks

The compose files in this directory are parameterized baselines for repeatable
benchmark sweeps. Put local overrides in the variant’s untracked `.env` file;
copy its committed `.env.example` first. `helpers/run-benchmark.py` records the
resolved Docker command, environment, and model bind mount in each run report.

Only one GPU stack may run at once because both variants use port `8080` and
both RTX 3090s.

## FP8 — official Qwen checkpoint

```sh
cd models/qwen3.8-27b/fp8
cp .env.example .env
# Adjust one test variable in .env, then:
docker compose up -d
```

The baseline uses the model’s bundled template:

```env
CHAT_TEMPLATE=/models/model/chat_template.jinja
```

To test the mounted froggeric template instead:

```env
CHAT_TEMPLATE=/etc/qwen-custom-chat-template.jinja
```

`MTP_K`, `KV_CACHE_DTYPE`, `MAX_MODEL_LEN`, `MAX_NUM_SEQS`,
`MAX_NUM_BATCHED_TOKENS`, and `GPU_MEMORY_UTILIZATION` are intended sweep
variables. Prefix caching is disabled by default because it may interact badly
with MTP and the model’s recurrent state.

## AutoRound — author baselines and tuning profiles

The committed profiles under `autoround-int4/profiles/` are ordinary Compose
`--env-file` inputs, not ignored local `.env` files. Each fixes one checkpoint,
template, and conservative two-agent baseline:

| Profile | Checkpoint | Initial purpose |
|---|---|---|
| `mkrww.env` | [`MKRWW/Qwen3.8-27B-int4-AutoRound`](https://huggingface.co/MKRWW/Qwen3.8-27B-int4-AutoRound) | W4A16, group-128 INT4 reference |
| `avuja.env` | [`Avuja/Qwen3.8-27B-int4-AutoRound`](https://huggingface.co/Avuja/Qwen3.8-27B-int4-AutoRound) | W4A16 candidate with a preserved BF16 MTP head |
| `goldhub.env` | [`goldhub/Qwen3.8-27B-INT4-W4A16-AutoRound`](https://huggingface.co/goldhub/Qwen3.8-27B-INT4-W4A16-AutoRound) | W4A16, group-32 candidate with more preserved BF16 layers |
| `minachist.env` | [`Minachist/Qwen3.8-27B-INT8-AutoRound`](https://huggingface.co/Minachist/Qwen3.8-27B-INT8-AutoRound) | W8A16 quality/capacity reference for the installed `main` branch |

All profiles start with native model templates, non-thinking tool use, dynamic
INT8 KV, prefix caching off, and `MAX_NUM_SEQS=2`. This is a stability-first
c1/c2 baseline: first establish long-context tool-call behavior, then isolate
MTP, prefix cache, a custom template, or another performance setting in a copied
profile.

The MTP/W4A8 configuration in
[Club-3090](https://github.com/noonghunna/club-3090/blob/master/models/qwen3.8-27b/vllm/compose/dual/autoround-int4/mtp.yml)
is useful evidence but is not this baseline. It uses runtime patches and documents
an OOM with `MTP n=4` plus two sequences on dual 3090s. Do not treat its
single-stream fast path as a safe two-agent configuration.

### Run a named profile

From the repository root:

```sh
docker compose \
  --env-file models/qwen3.8-27b/autoround-int4/profiles/avuja.env \
  -f models/qwen3.8-27b/autoround-int4/docker-compose.yml \
  config

./helpers/run-benchmark.py \
  --stack models/qwen3.8-27b/autoround-int4/docker-compose.yml \
  --env-file models/qwen3.8-27b/autoround-int4/profiles/avuja.env \
  --service vllm-qwen38-27b-autoround-int4 \
  --tokenizer /home/app/models/Avuja/Qwen3.8-27B-int4-AutoRound \
  --start \
  --power-limit 350
```

The run's `run.json` records the profile path and its SHA-256 at launch; the
rendered `report.md` displays both. It also records the effective container
command and environment, which remain the canonical record if profile comments
are later updated.

### Record the short result and manual soak notes

After a completed run, update only the profile's dedicated comment block:

```sh
./helpers/update-benchmark-profile.py \
  --profile models/qwen3.8-27b/autoround-int4/profiles/avuja.env \
  --run benchmarks/runs/YYYY/MM/<run-id> \
  --manual-note "No loops or stalled tool calls during a two-hour coding session."
```

The helper copies the `tool-eval-bench` score and the llama-benchy c1/c2
throughput at 0, 8K, and 32K into comments. The immutable report under
`benchmarks/runs/` remains the detailed evidence.

For every new tuning hypothesis, copy the source profile to a new descriptive
filename, such as `profiles/avuja-mtp-3.env`; change only the experiment's
variables. Do not overwrite an already-benchmarked profile's assignments.

### Avuja tuning matrix

The initial Avuja control is `profiles/avuja.env` and completed run
`20260819T180403Z-avuja-qwen3-8-27b-int4-autoround-c9f9fb98`: tool-eval `88`,
c2 per-agent decode throughput `38.61` t/s at 0 context, `14.61` at 8K, and
`4.60` at 32K. The following profiles each retain the same model, power policy,
benchmark protocol, and base settings while changing one hypothesis:

| Profile | Change | Primary measurement | Gate / risk |
|---|---|---|---|
| `avuja-01-gpu-util-0.94.env` | `GPU_MEMORY_UTILIZATION=0.94` | c2 8K/32K capacity | prefill OOM or reduced transient headroom |
| `avuja-02-prefill-16384.env` | `MAX_NUM_BATCHED_TOKENS=16384` | 8K/32K TTFT and pp t/s | c2 prefill spike or instability |
| `avuja-03-flashinfer-sampler.env` | FlashInfer sampler on | c1/c2 decode t/s | tool-call or output regression |
| `avuja-04-fp8-kv.env` | FP8 E4M3 KV | cache-path speed | quality degradation or loops on Ampere |
| `avuja-05-prefix-cache-align.env` | prefix cache plus Mamba `align` | repeated-agent TTFT | manual chain stability; llama-benchy uses `--no-cache` |
| `avuja-06-tool-parser-xml.env` | `qwen3_xml` tool parser | tool-eval quality | parser/template compatibility |
| `avuja-07-froggeric-template.env` | froggeric template | tool-eval and manual chains | template behavior divergence |
| `avuja-08-tool-sampling-temp-0.6.env` | temperature `0.6` | wrong-argument/tool consistency | quality or completion regression |

Run one profile at a time using the same command above with its profile filename.
After every completed run, update its comment summary and compare it with the
control before advancing. MTP is deliberately absent from this first matrix: the
unpatched stack cannot safely toggle it, and the available two-3090 MTP evidence
uses additional Club-3090 patches and documents a c2 OOM risk.

## Preflight and benchmark

Inspect the fully resolved configuration before each run:

```sh
docker compose config
```

Then, from the repository root, run the benchmark against the service defined by
that variant:

```sh
./helpers/run-benchmark.py \
  --stack models/qwen3.8-27b/fp8/docker-compose.yml \
  --env-file models/qwen3.8-27b/fp8/.env \
  --service vllm-qwen38-27b \
  --tokenizer /home/app/models/Qwen/Qwen3.8-27B-FP8 \
  --start \
  --power-limit 350
```

For AutoRound, change `--stack`, `--service`, and `--tokenizer` to match the
selected `MODEL_HOST_PATH`. Commit the generated run directory and rebuilt
benchmark index together after reviewing the report.
