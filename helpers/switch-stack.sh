#!/usr/bin/env bash
set -euo pipefail

# Switch from a currently running stack to a new one.
# Usage: switch-stack.sh <model>/<variant>
#   e.g. switch-stack.sh qwen3.6-27b/fp8
#   e.g. switch-stack.sh ornith-1.0-35b/llama

STACK="${1:?Usage: switch-stack.sh <model>/<variant>}"
STACK_DIR="docker/models/${STACK}"

# Figure out the compose file
if [ -f "${STACK_DIR}/default.yml" ]; then
  COMPOSE_FILE="default.yml"
elif [ -f "${STACK_DIR}/docker-compose.yml" ]; then
  COMPOSE_FILE="docker-compose.yml"
else
  echo "ERROR: No compose file found in ${STACK_DIR}"
  echo "  Looked for: default.yml or docker-compose.yml"
  exit 1
fi

# Stop any running GPU stacks
echo "Stopping any running stacks..."
for f in $(find docker/models -name "default.yml" -o -name "docker-compose.yml"); do
  dir="$(dirname "$f")"
  cd "$dir" && docker compose -f "$(basename "$f")" down 2>/dev/null || true
done

# Start the new stack
echo "Starting ${STACK}..."
cd "${STACK_DIR}"
docker compose -f "${COMPOSE_FILE}" up -d

echo "Done. Stack '${STACK}' is running on port 8080."