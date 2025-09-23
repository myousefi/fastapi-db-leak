#!/usr/bin/env python3
"""Convert hey CLI output into structured JSON for experiments."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SUMMARY_PATTERNS = {
    "total_seconds": re.compile(r"Total:\s+([0-9.]+)\s+secs"),
    "slowest_seconds": re.compile(r"Slowest:\s+([0-9.]+)\s+secs"),
    "fastest_seconds": re.compile(r"Fastest:\s+([0-9.]+)\s+secs"),
    "average_seconds": re.compile(r"Average:\s+([0-9.]+)\s+secs"),
    "requests_per_sec": re.compile(r"Requests/sec:\s+([0-9.]+)"),
    "total_bytes": re.compile(r"Total data:\s+([0-9]+)\s+bytes"),
    "bytes_per_request": re.compile(r"Size/request:\s+([0-9]+)\s+bytes"),
}

LATENCY_RE = re.compile(r"\s*([0-9]+)% in ([0-9.]+) secs")
STATUS_RE = re.compile(r"\[(\d+)\]\s+([0-9]+) responses")
ERROR_RE = re.compile(r"\[(\d+)\]\s+(.+)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Path to raw hey stdout")
    parser.add_argument("--output", required=True, help="Destination JSON file")
    parser.add_argument("--status", required=True, type=int)
    parser.add_argument("--timestamp", required=True)
    parser.add_argument("--display-command", required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--path", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--concurrency", required=True)
    parser.add_argument("--duration", required=True)
    parser.add_argument("--rps", default="")
    parser.add_argument("--method", default="GET")
    parser.add_argument("--headers", default="")
    parser.add_argument("--extra-args", default="")
    parser.add_argument("--label", default="")
    parser.add_argument("--has-auth", required=True)
    return parser.parse_args()


def _coerce_number(value: str) -> float | int:
    if "." in value:
        return float(value)
    return int(value)


def _maybe(value: str) -> str | None:
    value = value.strip()
    return value or None


def parse_text(lines: list[str]) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    for key, pattern in SUMMARY_PATTERNS.items():
        for line in lines:
            match = pattern.search(line)
            if match:
                metrics[key] = _coerce_number(match.group(1))
                break

    latency_distribution: dict[str, float] = {}
    for line in lines:
        match = LATENCY_RE.search(line)
        if match:
            latency_distribution[match.group(1)] = float(match.group(2))

    status_codes: dict[str, int] = {}
    collecting_status = False
    for line in lines:
        if "Status code distribution:" in line:
            collecting_status = True
            continue
        if collecting_status:
            if not line.strip():
                collecting_status = False
                continue
            match = STATUS_RE.search(line)
            if match:
                status_codes[match.group(1)] = int(match.group(2))

    error_distribution: dict[str, list[str]] = {}
    collecting_errors = False
    for line in lines:
        if "Error distribution:" in line:
            collecting_errors = True
            continue
        if collecting_errors:
            if not line.strip():
                collecting_errors = False
                continue
            match = ERROR_RE.search(line)
            if match:
                bucket, message = match.groups()
                error_distribution.setdefault(bucket, []).append(message)

    metrics["latency_distribution"] = latency_distribution or None
    metrics["status_codes"] = status_codes or None
    metrics["error_distribution"] = error_distribution or None

    return metrics


def main() -> None:
    args = parse_args()

    raw_text = Path(args.input).read_text()
    lines = raw_text.splitlines()

    try:
        concurrency: int | str = int(args.concurrency)
    except ValueError:
        concurrency = args.concurrency

    payload = {
        "timestamp": args.timestamp,
        "status": args.status,
        "command": args.display_command,
        "parameters": {
            "base_url": args.base_url,
            "path": args.path,
            "url": args.url,
            "concurrency": concurrency,
            "duration": args.duration,
            "rps": _maybe(args.rps),
            "method": _maybe(args.method) or "GET",
            "headers": _maybe(args.headers),
            "extra_args": _maybe(args.extra_args),
            "label": _maybe(args.label),
            "auth_header": bool(int(args.has_auth)),
        },
        "metrics": parse_text(lines),
        "raw_output": lines,
    }

    Path(args.output).write_text(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
