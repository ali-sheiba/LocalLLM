#!/usr/bin/env python3
"""Run a reproducible LocalLLM quality and throughput benchmark.

Each invocation writes exactly two immutable artifacts under benchmarks/runs:
``run.json`` (canonical evidence) and ``report.md`` (generated summary).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import http.client
import json
import os
import re
import secrets
import shlex
import signal
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
BENCHMARKS = ROOT / "benchmarks"
REPORTER = ROOT / "helpers" / "build-benchmark-index.py"
POWER_LIMIT_SCRIPT = ROOT / "helpers" / "set-gpu-power-limit.sh"
SENSITIVE_ENV = re.compile(r"(?:key|token|secret|password|credential|auth)", re.IGNORECASE)
GPU_FIELDS = [
    "index",
    "name",
    "uuid",
    "driver_version",
    "pstate",
    "power.limit",
    "power.default_limit",
    "power.min_limit",
    "power.max_limit",
    "power.draw",
    "temperature.gpu",
    "clocks.sm",
    "clocks.mem",
    "utilization.gpu",
    "utilization.memory",
    "memory.total",
    "pcie.link.gen.current",
    "pcie.link.width.current",
]


class BenchmarkError(RuntimeError):
    """Expected failure that should become a recorded failed run."""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run_command(
    argv: list[str],
    *,
    cwd: Path | None = None,
    check: bool = True,
    timeout: float | None = None,
) -> subprocess.CompletedProcess[str]:
    try:
        completed = subprocess.run(
            argv,
            cwd=cwd,
            check=False,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise BenchmarkError(f"Command not found: {argv[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise BenchmarkError(f"Command timed out: {shlex.join(argv)}") from exc
    if check and completed.returncode != 0:
        error = completed.stderr.strip() or completed.stdout.strip() or "no command output"
        raise BenchmarkError(f"Command failed ({completed.returncode}): {shlex.join(argv)}\n{error}")
    return completed


def trimmed_output(text: str, limit: int = 4000) -> str:
    text = text.strip()
    return text if len(text) <= limit else f"{text[:limit]}\n… [truncated]"


def redact_argv(argv: list[str]) -> list[str]:
    redacted: list[str] = []
    redact_next = False
    for argument in argv:
        if redact_next:
            redacted.append("<redacted>")
            redact_next = False
        elif argument in {"--api-key", "--token", "--password"}:
            redacted.append(argument)
            redact_next = True
        elif re.match(r"--(?:api[-_]?key|token|password)=", argument, re.IGNORECASE):
            redacted.append(argument.split("=", 1)[0] + "=<redacted>")
        else:
            redacted.append(argument)
    return redacted


def sanitize_environment(environment: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in environment:
        key, separator, value = item.partition("=")
        if not separator:
            continue
        result[key] = "<redacted>" if SENSITIVE_ENV.search(key) else value
    return dict(sorted(result.items()))


def parse_json_output(command: list[str], *, cwd: Path | None = None) -> Any:
    output = run_command(command, cwd=cwd).stdout.strip()
    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        raise BenchmarkError(f"Expected JSON from {shlex.join(command)}: {output[:500]}") from exc


def compose_command(compose_file: Path, environment_file: Path | None, *arguments: str) -> list[str]:
    command = ["docker", "compose"]
    if environment_file is not None:
        command.extend(["--env-file", str(environment_file)])
    command.extend(["-f", str(compose_file), *arguments])
    return command


def discover_service(compose_file: Path, requested: str | None, environment_file: Path | None) -> str:
    services = [
        line
        for line in run_command(compose_command(compose_file, environment_file, "config", "--services")).stdout.splitlines()
        if line
    ]
    if requested:
        if requested not in services:
            raise BenchmarkError(f"Service {requested!r} is not in {compose_file}; available: {', '.join(services)}")
        return requested
    if len(services) != 1:
        raise BenchmarkError("--service is required when the compose file has multiple services: " + ", ".join(services))
    return services[0]


def inspect_container(
    compose_file: Path, service: str, start: bool, environment_file: Path | None
) -> tuple[str, dict[str, Any]]:
    if start:
        run_command(compose_command(compose_file, environment_file, "up", "-d", service))
    container_id = run_command(
        compose_command(compose_file, environment_file, "ps", "-q", service)
    ).stdout.strip()
    if not container_id:
        raise BenchmarkError(
            f"No running container for {service!r}. Start it first or pass --start."
        )
    inspected = parse_json_output(["docker", "inspect", container_id])
    if not isinstance(inspected, list) or len(inspected) != 1 or not isinstance(inspected[0], dict):
        raise BenchmarkError(f"Unexpected docker inspect result for {container_id}")
    state = inspected[0].get("State", {})
    if not isinstance(state, dict) or not state.get("Running"):
        raise BenchmarkError(f"Container for {service!r} is not running")
    return container_id, inspected[0]


def image_digest(image: str) -> str | None:
    if not image:
        return None
    completed = run_command(["docker", "image", "inspect", image], check=False)
    if completed.returncode != 0:
        return None
    try:
        data = json.loads(completed.stdout)
        digests = data[0].get("RepoDigests", [])
        if isinstance(digests, list) and digests:
            return str(digests[0])
        return data[0].get("Id")
    except (json.JSONDecodeError, IndexError, AttributeError):
        return None


def compact_container(inspected: dict[str, Any]) -> dict[str, Any]:
    config = inspected.get("Config", {}) if isinstance(inspected.get("Config"), dict) else {}
    host_config = inspected.get("HostConfig", {}) if isinstance(inspected.get("HostConfig"), dict) else {}
    mounts = inspected.get("Mounts", []) if isinstance(inspected.get("Mounts"), list) else []
    mount_rows = []
    for mount in mounts:
        if not isinstance(mount, dict):
            continue
        mount_rows.append(
            {
                "source": mount.get("Source"),
                "destination": mount.get("Destination"),
                "mode": mount.get("Mode"),
                "read_only": mount.get("RW") is False,
            }
        )
    return {
        "id": inspected.get("Id"),
        "name": str(inspected.get("Name", "")).lstrip("/"),
        "image": config.get("Image"),
        "image_digest": image_digest(str(config.get("Image") or "")),
        "entrypoint": config.get("Entrypoint"),
        "command": config.get("Cmd"),
        "environment": sanitize_environment(config.get("Env", [])),
        "mounts": mount_rows,
        "network_mode": host_config.get("NetworkMode"),
    }


def derive_model(container: dict[str, Any], explicit_source: str | None, served_name: str | None) -> dict[str, str | None]:
    source = explicit_source
    if not source:
        candidates = []
        for mount in container.get("mounts", []):
            source_path = str(mount.get("source") or "")
            destination = str(mount.get("destination") or "")
            if (
                destination.startswith("/models")
                and source_path
                and not source_path.lower().endswith((".jinja", ".json", ".yaml", ".yml"))
            ):
                candidates.append(source_path)
        if candidates:
            source = candidates[0]
    hf_repository: str | None = None
    if source and not source.startswith("/") and source.count("/") == 1:
        hf_repository = source
    elif source:
        parts = Path(source).parts
        for root_name in ("models",):
            if root_name in parts:
                position = len(parts) - 1 - list(reversed(parts)).index(root_name)
                tail = parts[position + 1 :]
                if len(tail) >= 2:
                    hf_repository = f"{tail[0]}/{tail[1]}"
                break
    return {"host_path": source, "hf_repository": hf_repository, "served_name": served_name}


def git_metadata() -> dict[str, Any]:
    def optional(args: list[str]) -> str | None:
        completed = run_command(args, cwd=ROOT, check=False)
        return completed.stdout.strip() if completed.returncode == 0 else None

    return {
        "commit": optional(["git", "rev-parse", "HEAD"]),
        "short_commit": optional(["git", "rev-parse", "--short", "HEAD"]),
        "dirty_paths": (optional(["git", "status", "--porcelain"]) or "").splitlines(),
    }


def docker_metadata() -> dict[str, Any]:
    version = run_command(["docker", "version", "--format", "{{json .}}"], check=False)
    payload: Any = None
    if version.returncode == 0:
        try:
            payload = json.loads(version.stdout)
        except json.JSONDecodeError:
            payload = version.stdout.strip()
    compose = run_command(["docker", "compose", "version", "--short"], check=False)
    return {"version": payload, "compose_version": compose.stdout.strip() if compose.returncode == 0 else None}


def gpu_snapshot() -> dict[str, Any]:
    query = ",".join(GPU_FIELDS)
    command = ["nvidia-smi", f"--query-gpu={query}", "--format=csv,noheader,nounits"]
    completed = run_command(command, check=False)
    result: dict[str, Any] = {"target": "local", "gpus": []}
    if completed.returncode != 0:
        result["error"] = trimmed_output(completed.stderr or completed.stdout)
        return result
    try:
        for values in csv.reader(completed.stdout.splitlines(), skipinitialspace=True):
            if len(values) != len(GPU_FIELDS):
                continue
            result["gpus"].append(dict(zip(GPU_FIELDS, values, strict=True)))
    except csv.Error as exc:
        result["error"] = str(exc)
    return result


def selected_gpu_ids(container: dict[str, Any], snapshot: dict[str, Any]) -> list[str]:
    environment = container.get("environment", {})
    requested = environment.get("NVIDIA_VISIBLE_DEVICES") or environment.get("CUDA_VISIBLE_DEVICES")
    if requested and requested not in {"all", "void", "none"}:
        ids = [item.strip() for item in requested.split(",") if item.strip().isdigit()]
        if ids:
            return ids
    return [str(gpu.get("index")) for gpu in snapshot.get("gpus", []) if gpu.get("index") is not None]


def power_limits(snapshot: dict[str, Any], gpu_ids: list[str]) -> dict[str, float]:
    values: dict[str, float] = {}
    wanted = set(gpu_ids)
    for gpu in snapshot.get("gpus", []):
        identifier = str(gpu.get("index"))
        if identifier not in wanted:
            continue
        try:
            values[identifier] = float(str(gpu.get("power.limit")))
        except (TypeError, ValueError):
            raise BenchmarkError(f"Could not read power limit for GPU {identifier}") from None
    if set(values) != wanted:
        raise BenchmarkError("Could not read power limits for all selected GPUs")
    return values


def validate_power_limit(snapshot: dict[str, Any], gpu_ids: list[str], watts: float) -> None:
    wanted = set(gpu_ids)
    for gpu in snapshot.get("gpus", []):
        identifier = str(gpu.get("index"))
        if identifier not in wanted:
            continue
        try:
            minimum = float(str(gpu.get("power.min_limit")))
            maximum = float(str(gpu.get("power.max_limit")))
        except (TypeError, ValueError):
            raise BenchmarkError(f"Could not read supported power range for GPU {identifier}") from None
        if not minimum <= watts <= maximum:
            raise BenchmarkError(
                f"Requested {watts:g}W is outside GPU {identifier}'s supported range "
                f"({minimum:g}W–{maximum:g}W)"
            )


def set_power_limit(watts: int | float) -> None:
    if not POWER_LIMIT_SCRIPT.is_file():
        raise BenchmarkError(f"Power-limit helper does not exist: {POWER_LIMIT_SCRIPT}")
    numeric_watts = float(watts)
    if not numeric_watts.is_integer():
        raise BenchmarkError(f"Power limit must be a whole number of watts, got {watts}")
    run_command([str(POWER_LIMIT_SCRIPT), str(int(numeric_watts))])


def fetch_served_model(base_url: str, api_key: str | None) -> str:
    url = base_url.rstrip("/") + "/v1/models"
    request = urllib.request.Request(url)
    if api_key:
        request.add_header("Authorization", f"Bearer {api_key}")
    try:
        with urllib.request.urlopen(request, timeout=15) as response:  # noqa: S310
            data = json.load(response)
    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        http.client.HTTPException,
        OSError,
        TimeoutError,
        json.JSONDecodeError,
    ) as exc:
        # During vLLM initialization the port can accept a connection and then
        # reset it while workers are still loading. Treat every transport-level
        # failure as a not-ready response; wait_for_served_model owns retries.
        raise BenchmarkError(f"Could not discover served model from {url}: {exc}") from exc
    models = data.get("data", []) if isinstance(data, dict) else []
    if not models or not isinstance(models[0], dict) or not models[0].get("id"):
        raise BenchmarkError(f"No models returned by {url}")
    return str(models[0]["id"])


def wait_for_served_model(base_url: str, api_key: str | None, timeout_seconds: float) -> str:
    deadline = time.monotonic() + timeout_seconds
    started = time.monotonic()
    last_error: BenchmarkError | None = None
    attempts = 0
    while time.monotonic() < deadline:
        try:
            return fetch_served_model(base_url, api_key)
        except BenchmarkError as exc:
            last_error = exc
            attempts += 1
            elapsed = time.monotonic() - started
            # Print the first failure and then once per 30 seconds. Large models
            # commonly need several minutes before /v1/models is available.
            if attempts == 1 or attempts % 6 == 0:
                print(
                    f"[benchmark] Server not ready after {elapsed:.0f}s/{timeout_seconds:g}s; retrying: {exc}",
                    flush=True,
                )
            remaining = deadline - time.monotonic()
            if remaining > 0:
                time.sleep(min(5, remaining))
    detail = str(last_error) if last_error else "no response received"
    raise BenchmarkError(f"Server was not ready within {timeout_seconds:g}s: {detail}")


def executable_version(argv: list[str], cwd: Path | None = None) -> str | None:
    try:
        completed = run_command(argv, cwd=cwd, check=False)
    except BenchmarkError:
        return None
    return completed.stdout.strip() if completed.returncode == 0 else None


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise BenchmarkError(f"Expected a JSON object in {path}")
    return data


def write_json(path: Path, content: dict[str, Any]) -> None:
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(content, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def add_command_record(records: list[dict[str, Any]], name: str, argv: list[str], completed: subprocess.CompletedProcess[str]) -> None:
    records.append(
        {
            "name": name,
            "argv": redact_argv(argv),
            "returncode": completed.returncode,
            "stdout": trimmed_output(completed.stdout),
            "stderr": trimmed_output(completed.stderr),
        }
    )


def make_run_id(model: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", model.lower()).strip("-")[:48] or "model"
    return f"{utc_now().strftime('%Y%m%dT%H%M%SZ')}-{slug}-{secrets.token_hex(4)}"


def main() -> int:
    def log(message: str, *, error: bool = False) -> None:
        print(f"[benchmark] {message}", file=sys.stderr if error else sys.stdout, flush=True)

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stack", required=True, help="Compose file, relative to LocalLLM or absolute")
    parser.add_argument("--env-file", type=Path, help="Optional Compose environment file; its path and SHA-256 are recorded, not its contents")
    parser.add_argument("--service", help="Compose service to benchmark; required for multi-service files")
    parser.add_argument("--start", action="store_true", help="Start the selected service; never stops another stack")
    parser.add_argument("--ready-timeout", type=float, default=900, help="Seconds to wait for a --start service to expose /v1/models")
    parser.add_argument("--base-url", default=os.environ.get("TOOL_EVAL_BASE_URL", "http://localhost:8080"))
    parser.add_argument("--model", help="Served API model name; discovered from /v1/models when omitted")
    parser.add_argument("--backend", choices=("vllm", "llamacpp", "litellm"), help="Optional tool-eval backend label")
    parser.add_argument("--model-source", help="Override the HF-style source/model path inferred from container mounts")
    parser.add_argument("--tokenizer", help="Local tokenizer path passed to llama-benchy")
    parser.add_argument("--tool-eval-dir", type=Path, default=Path.home() / "bench" / "tool-eval-bench")
    parser.add_argument("--uv", help="Path to the uv executable (defaults to uv found on PATH)")
    parser.add_argument("--api-key-env", default="TOOL_EVAL_API_KEY", help="Environment variable containing an optional API key")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--depth", default="0,8192,32768")
    parser.add_argument("--concurrency", default="1,2")
    parser.add_argument("--pp", type=int, default=2048)
    parser.add_argument("--tg", type=int, default=128)
    parser.add_argument("--runs", type=int, default=3, help="llama-benchy measurement iterations per point")
    parser.add_argument("--latency-mode", choices=("api", "generation", "none"), default="generation")
    parser.add_argument("--power-limit", type=int, help="Temporarily set all benchmark-host GPUs to this watt limit; exact prior limits are restored")
    args = parser.parse_args()

    compose_file = Path(args.stack).expanduser()
    if not compose_file.is_absolute():
        compose_file = ROOT / compose_file
    compose_file = compose_file.resolve()
    if not compose_file.is_file():
        parser.error(f"Compose file does not exist: {compose_file}")

    environment_file: Path | None = args.env_file
    if environment_file is not None:
        environment_file = environment_file.expanduser()
        if not environment_file.is_absolute():
            environment_file = ROOT / environment_file
        environment_file = environment_file.resolve()
        if not environment_file.is_file():
            parser.error(f"Compose environment file does not exist: {environment_file}")

    if not args.tool_eval_dir.is_dir():
        parser.error(f"tool-eval-bench checkout does not exist: {args.tool_eval_dir}")

    uv_executable = args.uv or shutil.which("uv")
    if not uv_executable:
        parser.error(
            "Required executable 'uv' was not found on PATH. Install uv, add its directory "
            "to PATH, or pass --uv /absolute/path/to/uv."
        )
    uv_path = Path(uv_executable).expanduser()
    if not uv_path.is_file() or not os.access(uv_path, os.X_OK):
        parser.error(f"uv executable is not runnable: {uv_path}")
    uv_executable = str(uv_path.resolve())

    commands: list[dict[str, Any]] = []
    power: dict[str, Any] = {"enabled": args.power_limit is not None, "restore_status": "not-needed"}
    hardware: dict[str, Any] = {}
    run_path: Path | None = None
    started_at = utc_now()
    status = "failed"
    results: dict[str, Any] = {"error": "Benchmark did not start"}
    service = "unknown"
    served_name = args.model or "unknown"
    model: dict[str, str | None] = {"host_path": args.model_source, "hf_repository": None, "served_name": served_name}
    container: dict[str, Any] = {}
    base_url = args.base_url.rstrip("/")
    tool_prefix = [uv_executable, "run", "--extra", "perf"]
    return_code = 0
    interrupted = False

    def interrupt_handler(_signum: int, _frame: Any) -> None:
        nonlocal interrupted
        interrupted = True
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, interrupt_handler)
    signal.signal(signal.SIGTERM, interrupt_handler)

    try:
        log(f"Resolving Compose service from {compose_file}")
        service = discover_service(compose_file, args.service, environment_file)
        if args.start:
            log(f"Starting service {service}")
        _, inspected = inspect_container(compose_file, service, args.start, environment_file)
        container = compact_container(inspected)
        log(f"Using running container {container.get('name', service)}")
        api_key = os.environ.get(args.api_key_env)
        log(f"Discovering served model at {base_url}")
        served_name = args.model or (
            wait_for_served_model(args.base_url, api_key, args.ready_timeout)
            if args.start
            else fetch_served_model(args.base_url, api_key)
        )
        model = derive_model(container, args.model_source, served_name)
        run_id = make_run_id(str(model.get("hf_repository") or served_name))
        now = utc_now()
        run_path = BENCHMARKS / "runs" / now.strftime("%Y") / now.strftime("%m") / run_id
        run_path.mkdir(parents=True, exist_ok=False)
        log(f"Recording run {run_path.relative_to(ROOT)} for model {served_name}")

        snapshot_target = "local"
        log("Capturing pre-run GPU state")
        hardware["before"] = gpu_snapshot()
        selected = selected_gpu_ids(container, hardware["before"])
        if args.power_limit is not None:
            all_gpus = {
                str(gpu.get("index"))
                for gpu in hardware["before"].get("gpus", [])
                if gpu.get("index") is not None
            }
            if not all_gpus or set(selected) != all_gpus:
                raise BenchmarkError(
                    "The power-limit helper changes every GPU on the benchmark host; "
                    "refusing to change power while the stack does not own every detected GPU."
                )
            before_limits = power_limits(hardware["before"], selected)
            if len(set(before_limits.values())) != 1:
                raise BenchmarkError(
                    "The selected GPUs have different existing power limits; the one-value power helper "
                    "cannot restore them safely. Normalize the limits first."
                )
            validate_power_limit(hardware["before"], selected, args.power_limit)
            power.update(
                {
                    "target": snapshot_target,
                    "selected_gpus": selected,
                    "requested_watts": args.power_limit,
                    "before_watts": before_limits,
                    "restore_status": "pending",
                }
            )
            log(f"Applying {args.power_limit:g}W power limit to every benchmark-host GPU")
            set_power_limit(args.power_limit)
            power["applied"] = True

        bench_base_url = base_url if base_url.endswith("/v1") else f"{base_url}/v1"
        with tempfile.TemporaryDirectory(prefix="localllm-bench-") as temporary_dir:
            temporary = Path(temporary_dir)
            performance_path = temporary / "performance.json"
            quality_path = temporary / "quality.json"
            perf_command = tool_prefix + [
                "llama-benchy",
                "--base-url", bench_base_url,
                "--model", served_name,
                "--pp", str(args.pp),
                "--tg", str(args.tg),
                "--depth", *[part.strip() for part in args.depth.split(",") if part.strip()],
                "--concurrency", *[part.strip() for part in args.concurrency.split(",") if part.strip()],
                "--runs", str(args.runs),
                "--latency-mode", args.latency_mode,
                "--no-cache",
                "--skip-coherence",
                "--no-adapt-prompt",
                "--format", "json",
                "--save-result", str(performance_path),
            ]
            if args.tokenizer:
                perf_command.extend(["--tokenizer", args.tokenizer])
            if api_key:
                perf_command.extend(["--api-key", api_key])
            log("Running llama-benchy throughput sweep")
            completed_perf = run_command(perf_command, cwd=args.tool_eval_dir, check=False)
            add_command_record(commands, "llama-benchy", perf_command, completed_perf)
            if completed_perf.returncode != 0:
                raise BenchmarkError(trimmed_output(completed_perf.stderr or completed_perf.stdout))
            if not performance_path.is_file():
                raise BenchmarkError("llama-benchy completed without writing its result JSON")
            performance = read_json(performance_path)

            quality_command = tool_prefix + [
                "tool-eval-bench", "run",
                "--seed", str(args.seed),
                "--base-url", base_url,
                "--model", served_name,
                "--json-file", str(quality_path),
                "--output-dir", str(temporary / "upstream-reports"),
                "--no-live",
            ]
            if args.backend:
                quality_command.extend(["--backend", args.backend])
            if api_key:
                quality_command.extend(["--api-key", api_key])
            log("Running tool-eval-bench quality suite")
            completed_quality = run_command(quality_command, cwd=args.tool_eval_dir, check=False)
            add_command_record(commands, "tool-eval-bench", quality_command, completed_quality)
            if completed_quality.returncode != 0:
                raise BenchmarkError(trimmed_output(completed_quality.stderr or completed_quality.stdout))
            if not quality_path.is_file():
                raise BenchmarkError("tool-eval-bench completed without writing its JSON result")
            quality = read_json(quality_path)

        status = "completed"
        results: dict[str, Any] = {"performance": performance, "quality": quality}
    except KeyboardInterrupt:
        status = "interrupted"
        return_code = 130
        results = {"error": "Interrupted by signal"}
        log("Interrupted by signal; restoring the prior power limits if needed", error=True)
    except (BenchmarkError, OSError, json.JSONDecodeError) as exc:
        status = "failed"
        return_code = 1
        results = {"error": str(exc)}
        log(f"Failed: {exc}", error=True)
    except Exception as exc:  # Always persist unexpected runner failures.
        status = "failed"
        return_code = 1
        results = {"error": f"Unexpected runner error: {exc}"}
        log(f"Unexpected failure: {exc}", error=True)
    finally:
        if args.power_limit is not None and power.get("before_watts"):
            restored: dict[str, float] = {}
            try:
                original_watts = next(iter(power["before_watts"].values()))
                set_power_limit(float(original_watts))
                restored = {gpu_id: float(watts) for gpu_id, watts in power["before_watts"].items()}
                power["restored_watts"] = restored
                power["restore_status"] = "succeeded"
            except BenchmarkError as exc:
                power["restore_status"] = "failed"
                power["restore_error"] = str(exc)
                return_code = return_code or 1
                status = "failed"
            original_watts = next(iter(power["before_watts"].values()))
            rendered_watts = int(original_watts) if float(original_watts).is_integer() else original_watts
            power["manual_recovery_command"] = f"./helpers/set-gpu-power-limit.sh {rendered_watts}"

        log("Capturing post-run GPU state")
        hardware["after"] = gpu_snapshot()
        if run_path is not None:
            comparison_hardware = ",".join(
                str(gpu.get("name", "unknown")) for gpu in hardware.get("before", {}).get("gpus", [])
            )
            payload: dict[str, Any] = {
                "schema_version": 1,
                "run_id": run_path.name,
                "status": status,
                "started_at": started_at.isoformat(),
                "finished_at": utc_now().isoformat(),
                "protocol": "tool-eval-69-perf-v1",
                "comparison_key": f"{model.get('hf_repository') or served_name}|tool-eval-69-perf-v1|{comparison_hardware}",
                "model": model,
                "stack": {
                    "compose_file": str(compose_file.relative_to(ROOT)) if compose_file.is_relative_to(ROOT) else str(compose_file),
                    "compose_sha256": sha256_file(compose_file),
                    "environment_file": (
                        {
                            "path": str(environment_file.relative_to(ROOT))
                            if environment_file.is_relative_to(ROOT)
                            else str(environment_file),
                            "sha256": sha256_file(environment_file),
                        }
                        if environment_file is not None
                        else None
                    ),
                    "service": service,
                    "engine": args.backend or "auto-detected",
                    "container": container,
                },
                "benchmark": {
                    "base_url": base_url,
                    "seed": args.seed,
                    "pp": args.pp,
                    "tg": args.tg,
                    "depth": args.depth,
                    "concurrency": args.concurrency,
                    "runs": args.runs,
                    "latency_mode": args.latency_mode,
                    "tokenizer": args.tokenizer,
                    "ready_timeout_seconds": args.ready_timeout if args.start else None,
                },
                "tooling": {
                    "tool_eval_checkout": str(args.tool_eval_dir),
                    "tool_eval_git_commit": run_command(["git", "rev-parse", "HEAD"], cwd=args.tool_eval_dir, check=False).stdout.strip() or None,
                    "uv_version": executable_version([uv_executable, "--version"]),
                    "llama_benchy_version": executable_version(tool_prefix + ["llama-benchy", "--version"], cwd=args.tool_eval_dir),
                },
                "docker": docker_metadata(),
                "git": git_metadata(),
                "hardware": hardware,
                "power_policy": power,
                "commands": commands,
                "results": results,
            }
            write_json(run_path / "run.json", payload)
            report = run_command([sys.executable, str(REPORTER), "--report", str(run_path / "run.json")], check=False)
            if report.returncode != 0:
                print(trimmed_output(report.stderr or report.stdout), file=sys.stderr)
                return_code = return_code or 1
            index = run_command([sys.executable, str(REPORTER), "--index"], check=False)
            if index.returncode != 0:
                print(trimmed_output(index.stderr or index.stdout), file=sys.stderr)
                return_code = return_code or 1
            log(f"Benchmark {status}: {run_path.relative_to(ROOT)}")
            log(f"Report: {run_path.relative_to(ROOT) / 'report.md'}")
            if power.get("restore_status") == "failed":
                log("Power restoration failed. Recovery command:", error=True)
                print(power.get("manual_recovery_command"), file=sys.stderr)

    return return_code


if __name__ == "__main__":
    sys.exit(main())
