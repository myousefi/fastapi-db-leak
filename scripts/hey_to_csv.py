import csv
import re
import sys
from pathlib import Path


LOG_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("logs")
OUTPUT = Path(sys.argv[2]) if len(sys.argv) > 2 else LOG_DIR / "summary.csv"

rows: list[dict[str, object]] = []
for path in LOG_DIR.rglob("*.txt"):
    text = path.read_text(errors="ignore")
    endpoint_match = re.search(r"https?://[^\s]+(/[^ \n]+)", text)
    endpoint = endpoint_match.group(1) if endpoint_match else ""

    concurrency_match = re.search(r"concurrency-(\d+)", path.name)
    if concurrency_match is None:
        concurrency_match = re.search(r"-c\s+(\d+)", text)
    concurrency = int(concurrency_match.group(1)) if concurrency_match else None

    throughput_match = re.search(r"Requests/sec:\s+([0-9.]+)", text)
    throughput = float(throughput_match.group(1)) if throughput_match else None

    successes_match = re.search(r"2xx:\s*(\d+)", text)
    if successes_match is None:
        successes_match = re.search(r"status code:\s*200\s+(\d+)", text, re.IGNORECASE)
    successes = int(successes_match.group(1)) if successes_match else None

    p50_match = re.search(r"50% in ([0-9.]+) secs", text)
    p95_match = re.search(r"95% in ([0-9.]+) secs", text)

    errors = None
    if "Non-2xx or 3xx responses: 0" in text or "errors=0" in text:
        errors = 0

    rows.append(
        {
            "file": str(path),
            "endpoint": endpoint,
            "concurrency": concurrency,
            "throughput_rps": throughput,
            "successes": successes,
            "p50_s": float(p50_match.group(1)) if p50_match else None,
            "p95_s": float(p95_match.group(1)) if p95_match else None,
            "errors": errors,
        }
    )

if not rows:
    print(f"No hey logs found under {LOG_DIR}")
    sys.exit(0)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
fieldnames = list(rows[0].keys())
with OUTPUT.open("w", newline="") as fh:
    writer = csv.DictWriter(fh, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)

print(f"Wrote {OUTPUT}")
