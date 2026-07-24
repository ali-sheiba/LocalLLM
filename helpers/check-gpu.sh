#!/usr/bin/env bash
set -euo pipefail

nvidia-smi --query-gpu=index,name,memory.total,memory.used,memory.free,temperature.gpu,power.draw,power.limit,utilization.gpu,utilization.memory --format=csv,noheader