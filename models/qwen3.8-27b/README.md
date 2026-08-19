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

## AutoRound INT4 — multiple authors

```sh
cd models/qwen3.8-27b/autoround-int4
cp .env.example .env
# Set MODEL_HOST_PATH to the specific author/model directory under /home/app/models.
docker compose up -d
```

For example:

```env
MODEL_HOST_PATH=/home/app/models/goldhub/Qwen3.8-27B-INT4-W4A16-AutoRound
CHAT_TEMPLATE=/models/model/chat_template.jinja
```

Use the same `CHAT_TEMPLATE` switch above for a model-template versus froggeric
template A/B test. The AutoRound stack relies on each checkpoint's
`config.json` to select its own packing format, which keeps the same compose
file compatible with differently packaged AutoRound releases. The baseline
enables prefix caching and uses `MAMBA_CACHE_MODE=align`; change those together.

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
