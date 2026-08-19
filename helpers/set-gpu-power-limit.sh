#!/usr/bin/env bash
# Set the power cap for every GPU on the benchmark host.
# The benchmark runner records and restores the previous cap after a run.

set -euo pipefail

readonly GPU_HOST="192.168.0.10"
readonly GPU_USER="root"
readonly MAX_POWER_WATTS=350

usage() {
    echo "Usage: $(basename "$0") <watts>" >&2
    echo "Sets every GPU on ${GPU_USER}@${GPU_HOST}; maximum is ${MAX_POWER_WATTS}W." >&2
}

if [[ $# -ne 1 ]]; then
    usage
    exit 2
fi

watts="$1"
if ! [[ "$watts" =~ ^[0-9]+$ ]] || (( watts < 1 )); then
    echo "ERROR: watts must be a positive integer, got: ${watts}" >&2
    exit 2
fi

if (( watts > MAX_POWER_WATTS )); then
    echo "ERROR: refusing ${watts}W; the benchmark safety maximum is ${MAX_POWER_WATTS}W." >&2
    exit 2
fi

echo "[power] Setting every GPU on ${GPU_USER}@${GPU_HOST} to ${watts}W..."
ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new "${GPU_USER}@${GPU_HOST}" \
    "nvidia-smi -pl ${watts}"
