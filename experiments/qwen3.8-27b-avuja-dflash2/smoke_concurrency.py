#!/usr/bin/env python3
"""Small streamed decode/concurrency smoke test for the DFlash2 experiment."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import time
import urllib.request
from dataclasses import dataclass


@dataclass
class Result:
    completion_tokens: int
    decode_seconds: float
    end_to_end_seconds: float

    @property
    def decode_tps(self) -> float:
        return self.completion_tokens / self.decode_seconds


def run_request(
    endpoint: str, model: str, max_tokens: int, prefix_words: int = 0
) -> Result:
    shared_prefix = "Shared immutable agent context. " * prefix_words
    payload = json.dumps(
        {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": shared_prefix
                    + (
                        "Write a production-quality Python LRU cache module with type "
                        "hints, O(1) get/put operations, clear error handling, and a "
                        "complete unittest suite. Explain the design after the code."
                    ),
                }
            ],
            "temperature": 0.0,
            "max_tokens": max_tokens,
            "stream": True,
            "stream_options": {"include_usage": True},
        }
    ).encode()
    request = urllib.request.Request(
        f"{endpoint.rstrip('/')}/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    started = time.perf_counter()
    first_token_at: float | None = None
    completion_tokens = 0
    with urllib.request.urlopen(request, timeout=300) as response:
        for raw_line in response:
            line = raw_line.decode().strip()
            if not line.startswith("data: ") or line == "data: [DONE]":
                continue
            event = json.loads(line[6:])
            choices = event.get("choices") or []
            if choices:
                content = choices[0].get("delta", {}).get("content")
                if content and first_token_at is None:
                    first_token_at = time.perf_counter()
            usage = event.get("usage")
            if usage:
                completion_tokens = int(usage.get("completion_tokens") or 0)
    ended = time.perf_counter()

    if first_token_at is None:
        raise RuntimeError("stream returned no content tokens")
    if completion_tokens <= 0:
        raise RuntimeError("stream returned no completion token count")
    return Result(
        completion_tokens=completion_tokens,
        decode_seconds=max(ended - first_token_at, 1e-9),
        end_to_end_seconds=ended - started,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", default="http://127.0.0.1:8080")
    parser.add_argument("--model", default="qwen3.8-27b")
    parser.add_argument("--concurrency", type=int, choices=(1, 2), required=True)
    parser.add_argument("--max-tokens", type=int, default=768)
    parser.add_argument("--prefix-words", type=int, default=0)
    args = parser.parse_args()

    wall_started = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(args.concurrency) as executor:
        futures = [
            executor.submit(
                run_request,
                args.endpoint,
                args.model,
                args.max_tokens,
                args.prefix_words,
            )
            for _ in range(args.concurrency)
        ]
        results = [future.result() for future in futures]
    wall_seconds = time.perf_counter() - wall_started

    for index, result in enumerate(results, start=1):
        print(
            f"request {index}: tokens={result.completion_tokens} "
            f"decode={result.decode_tps:.2f} t/s "
            f"e2e={result.end_to_end_seconds:.2f}s"
        )
    total_tokens = sum(result.completion_tokens for result in results)
    print(f"aggregate wall throughput: {total_tokens / wall_seconds:.2f} t/s")
    print(
        "mean per-agent streamed decode: "
        f"{sum(result.decode_tps for result in results) / len(results):.2f} t/s"
    )


if __name__ == "__main__":
    main()
