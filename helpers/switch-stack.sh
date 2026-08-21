#!/usr/bin/env bash
set -euo pipefail

# Switch from a currently running model stack to another.
# Usage: switch-stack.sh <model>/<variant>
#   e.g. switch-stack.sh qwen3.8-27b/fp8
#   e.g. switch-stack.sh ornith-1.0-35b/llama.yml

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODELS_DIR="${ROOT_DIR}/models"
STACK="${1:?Usage: switch-stack.sh <model>/<variant> or <model>/<compose-file>.yml}"
TARGET="${MODELS_DIR}/${STACK}"

if [ -f "${TARGET}" ]; then
  COMPOSE_PATH="${TARGET}"
elif [ -f "${TARGET}/default.yml" ]; then
  COMPOSE_PATH="${TARGET}/default.yml"
elif [ -f "${TARGET}/docker-compose.yml" ]; then
  COMPOSE_PATH="${TARGET}/docker-compose.yml"
else
  echo "ERROR: No Compose file found for ${STACK}" >&2
  echo "  Expected a model directory with default.yml or docker-compose.yml," >&2
  echo "  or a path such as ornith-1.0-35b/llama.yml." >&2
  exit 1
fi

# GPU stacks intentionally share both cards and port 8080. Bring down every
# canonical model configuration before starting the requested one.
echo "Stopping model stacks..."
while IFS= read -r -d '' compose_file; do
  compose_dir="$(dirname "${compose_file}")"
  (
    cd "${compose_dir}"
    docker compose -f "$(basename "${compose_file}")" down 2>/dev/null
  ) || true
done < <(find "${MODELS_DIR}" -type f \( -name 'default.yml' -o -name 'docker-compose.yml' -o -name 'llama.yml' -o -name 'vllm.yml' \) -print0)

echo "Starting ${STACK}..."
(
  cd "$(dirname "${COMPOSE_PATH}")"
  docker compose -f "$(basename "${COMPOSE_PATH}")" up -d
)

echo "Done. Stack '${STACK}' is running (normally on port 8080)."
