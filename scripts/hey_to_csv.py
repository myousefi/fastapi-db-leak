#!/usr/bin/env python3
"""Parse hey benchmark logs and emit a JSON summary."""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("logs")
OUTPUT_JSON = Path(sys.argv[2]) if len(sys.argv) > 2 else LOG_DIR / "summary.json"
RUN_NAME = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else None


SANITIZE_REPL = {"/": "-"}


def sanitize_endpoint(endpoint: str) -> str:
    out = endpoint
    for src, dst in SANITIZE_REPL.items():
        out = out.replace(src, dst)
    return out


def load_endpoint_map() -> dict[str, str]:
    makefile = ROOT / "Makefile"
    if not makefile.exists():
        raise FileNotFoundError("Makefile not found for endpoint inference")

    text = makefile.read_text()
    match = re.search(r"ENDPOINTS\s*:=\s*(.*?)(?:\n\S|\Z)", text, re.DOTALL)
    if not match:
        raise ValueError("Could not locate ENDPOINTS block in Makefile")

    endpoints: list[str] = []
    for line in match.group(1).splitlines():
        cleaned = line.strip().rstrip("\\").strip()
        if cleaned and cleaned.startswith("/"):
            endpoints.append(cleaned)
    if not endpoints:
        raise ValueError("No endpoints parsed from ENDPOINTS block")
    mapping: dict[str, str] = {}
    for endpoint in endpoints:
        mapping[sanitize_endpoint(endpoint)] = endpoint
    return mapping


ENDPOINT_MAP = load_endpoint_map()


def infer_run(path: Path) -> str:
    if RUN_NAME:
        return RUN_NAME
    relative = path.relative_to(LOG_DIR)
    if not relative.parts:
        raise ValueError(f"Could not infer run name from {path}")
    return relative.parts[0]


def sanitized_endpoint_from_path(path: Path) -> str:
    relative = path.relative_to(LOG_DIR)

    for part in relative.parts:
        if part.startswith("-"):
            return part
    raise ValueError(f"Could not infer sanitized endpoint from {path}")


def infer_endpoint(path: Path) -> tuple[str, str]:
    sanitized = sanitized_endpoint_from_path(path)
    try:
        endpoint = ENDPOINT_MAP[sanitized]
    except KeyError as exc:
        raise KeyError(f"Endpoint mapping not found for {sanitized}") from exc
    return endpoint, sanitized


FLOAT_PATTERNS = {
    "total_seconds": r"Total:\s*([0-9.]+)\s*secs",
    "slowest_seconds": r"Slowest:\s*([0-9.]+)\s*secs",
    "fastest_seconds": r"Fastest:\s*([0-9.]+)\s*secs",
    "average_seconds": r"Average:\s*([0-9.]+)\s*secs",
    "requests_per_sec": r"Requests/sec:\s*([0-9.]+)",
    "p10": r"10% in ([0-9.]+) secs",
    "p25": r"25% in ([0-9.]+) secs",
    "p50": r"50% in ([0-9.]+) secs",
    "p75": r"75% in ([0-9.]+) secs",
    "p90": r"90% in ([0-9.]+) secs",
    "p95": r"95% in ([0-9.]+) secs",
    "p99": r"99% in ([0-9.]+) secs",
}


@dataclass
class Sample:
    run: str
    endpoint: str
    sanitized_endpoint: str
    file: str
    concurrency: int | None
    metrics: dict[str, float | None]
    status_counts: dict[int, int]
    error_details: list[dict[str, Any]]

    @property
    def requests_per_sec(self) -> float:
        value = self.metrics.get("requests_per_sec")
        return float(value) if value is not None else 0.0

    @property
    def total_responses(self) -> int:
        return sum(self.status_counts.values())

    @property
    def successes(self) -> int:
        return sum(count for status, count in self.status_counts.items() if 200 <= status < 400)

    @property
    def failures(self) -> int:
        return self.total_responses - self.successes


def extract_metrics(text: str) -> dict[str, float | None]:
    metrics: dict[str, float | None] = {}
    for key, pattern in FLOAT_PATTERNS.items():
        match = re.search(pattern, text)
        metrics[key] = float(match.group(1)) if match else None
    return metrics


def extract_status_counts(text: str) -> dict[int, int]:
    counts: dict[int, int] = {}
    for match in re.finditer(r"\[(\d+)\]\s*(\d+)\s+responses", text):
        counts[int(match.group(1))] = int(match.group(2))
    return counts


def extract_errors(text: str) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    lines = text.splitlines()
    capturing = False
    for line in lines:
        stripped = line.strip()
        if stripped == "Error distribution:":
            capturing = True
            continue
        if capturing:
            if not stripped:
                break
            match = re.match(r"\[(\d+)\]\s*(.*)", stripped)
            if match:
                status = int(match.group(1))
                detail = match.group(2).strip()
                errors.append({"status": status, "detail": detail})
            else:
                errors.append({"status": None, "detail": stripped})
    return errors


samples: list[Sample] = []
for path in sorted(LOG_DIR.rglob("*.txt")):
    text = path.read_text(errors="ignore")
    endpoint, sanitized = infer_endpoint(path)
    run = infer_run(path)

    concurrency_match = re.search(r"concurrency-(\d+)", path.name)
    concurrency = int(concurrency_match.group(1)) if concurrency_match else None

    metrics = extract_metrics(text)
    statuses = extract_status_counts(text)
    errors = extract_errors(text)

    samples.append(
        Sample(
            run=run,
            endpoint=endpoint,
            sanitized_endpoint=sanitized,
            file=str(path),
            concurrency=concurrency,
            metrics=metrics,
            status_counts=statuses,
            error_details=errors,
        )
    )

if not samples:
    print(f"No hey logs found under {LOG_DIR}")
    sys.exit(0)

run_groups: dict[str, list[Sample]] = defaultdict(list)
for sample in samples:
    run_groups[sample.run].append(sample)

json_payload: dict[str, Any] = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "log_dir": str(LOG_DIR),
    "runs": [],
}

for run, run_samples in sorted(run_groups.items()):
    endpoints: dict[str, list[Sample]] = defaultdict(list)
    for sample in run_samples:
        endpoints[sample.endpoint].append(sample)

    endpoint_summaries: list[dict[str, Any]] = []
    for endpoint, endpoint_samples in sorted(endpoints.items()):
        endpoint_samples.sort(key=lambda s: (s.concurrency or 0, s.file))
        total_requests = sum(s.total_responses for s in endpoint_samples)
        total_failures = sum(s.failures for s in endpoint_samples)
        max_concurrency = max((s.concurrency or 0) for s in endpoint_samples)
        best_throughput = max(endpoint_samples, key=lambda s: s.requests_per_sec, default=None)
        best_latency = min(
            (s for s in endpoint_samples if s.metrics.get("p95") is not None),
            key=lambda s: s.metrics["p95"],
            default=None,
        )
        unique_errors = []
        seen_errors = set()
        for sample in endpoint_samples:
            for err in sample.error_details:
                key = (err.get("status"), err.get("detail"))
                if key not in seen_errors:
                    seen_errors.add(key)
                    unique_errors.append(err)

        endpoint_summaries.append(
            {
                "endpoint": endpoint,
                "sample_count": len(endpoint_samples),
                "max_concurrency": max_concurrency,
                "total_requests": total_requests,
                "total_failures": total_failures,
                "error_rate": (total_failures / total_requests) if total_requests else None,
                "best_throughput": {
                    "requests_per_sec": best_throughput.metrics.get("requests_per_sec") if best_throughput else None,
                    "concurrency": best_throughput.concurrency if best_throughput else None,
                    "file": best_throughput.file if best_throughput else None,
                },
                "best_p95": {
                    "p95_s": best_latency.metrics.get("p95") if best_latency else None,
                    "concurrency": best_latency.concurrency if best_latency else None,
                    "file": best_latency.file if best_latency else None,
                },
                "errors": unique_errors,
                "samples": [
                    {
                        "file": sample.file,
                        "sanitized_endpoint": sample.sanitized_endpoint,
                        "concurrency": sample.concurrency,
                        "requests_per_sec": sample.metrics.get("requests_per_sec"),
                        "total_responses": sample.total_responses,
                        "successes": sample.successes,
                        "failures": sample.failures,
                        "latency": {
                            "average_s": sample.metrics.get("average_seconds"),
                            "p50_s": sample.metrics.get("p50"),
                            "p95_s": sample.metrics.get("p95"),
                            "p99_s": sample.metrics.get("p99"),
                        },
                        "status_counts": sample.status_counts,
                        "error_details": sample.error_details,
                    }
                    for sample in endpoint_samples
                ],
            }
        )

    json_payload["runs"].append(
        {
            "run": run,
            "sample_count": len(run_samples),
            "endpoint_count": len(endpoint_summaries),
            "endpoints": endpoint_summaries,
        }
    )

OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_JSON.write_text(json.dumps(json_payload, indent=2), encoding="utf-8")

print(f"Wrote {OUTPUT_JSON}")
