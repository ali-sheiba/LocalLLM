# Experiments

Experimental configurations that deviate from the canonical `default.yml` in `stacks/`.

## Naming Convention

```
experiments/<stack-name>/<name>.yml
```

- `<stack-name>` matches the variant name under `stacks/<model>/<variant>/`
- `<name>` describes the change — e.g. `v2-gpu-mem-0.90.yml`, `no-prefix-cache.yml`

## How to Run

```bash
cd docker/experiments/<stack-name>
docker compose -f <name>.yml up -d
```

## Workflow

1. Copy `stacks/<model>/<variant>/default.yml` as a starting point
2. Make your change(s)
3. Name the file descriptively
4. Add a comment at the top documenting what changed and why