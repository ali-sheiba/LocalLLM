# Experiments

This directory contains isolated serving changes under evaluation. Canonical runnable configurations remain under [`models/`](../models/); do not overwrite them with an unverified tuning attempt.

## Layout and naming

```text
experiments/<model>-<variant>/<descriptive-name>.yml
```

Use a descriptive name for the hypothesis, such as `dflash2`, `gpu-mem-0.90`, or `no-prefix-cache`. Keep source patches, a short provenance note, and any experiment-specific profiles adjacent to the Compose file.

## Run an experiment

From the repository root, render it first and then launch it:

```sh
MODEL_ROOT="$HOME/models" docker compose \
  -f experiments/<model>-<variant>/<descriptive-name>.yml config

MODEL_ROOT="$HOME/models" docker compose \
  -f experiments/<model>-<variant>/<descriptive-name>.yml up -d
```

When an experiment provides a committed profile, pass it explicitly:

```sh
MODEL_ROOT="$HOME/models" docker compose \
  --env-file experiments/<model>-<variant>/profiles/<profile>.env \
  -f experiments/<model>-<variant>/<descriptive-name>.yml up -d
```

Stop the same configuration with `docker compose ... down` before launching another GPU stack. Most experiments use both RTX 3090s and host port `8080`.

## Workflow

1. Copy the closest canonical Compose file into a clearly named experiment directory.
2. Change one hypothesis at a time where possible.
3. Use `${MODEL_ROOT:-${HOME}/models}` for all model/template mounts and the repository container-name convention.
4. Record upstream source, patch origin, image version, expected benefit, and known risk.
5. Validate with `docker compose ... config`.
6. Benchmark the result and commit the generated immutable benchmark artifacts when publishing a conclusion.
