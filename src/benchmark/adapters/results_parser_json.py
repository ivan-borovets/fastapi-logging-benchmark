import json
from pathlib import Path

from benchmark.application.dtos import ParsedStats
from benchmark.application.ports import ResultsParser


class JsonResultsParser(ResultsParser):
    """Locust CSV is rewritten once per second and misses last second of load"""

    def parse(self, stats_file: Path) -> ParsedStats:
        with stats_file.open("r") as f:
            entries = json.load(f)

        if len(entries) != 1:
            raise ValueError(
                f"Expected single endpoint in {stats_file}, got {len(entries)}"
            )
        entry = entries[0]

        requests = int(entry["num_requests"])
        timed_requests = requests - int(entry["num_none_requests"])
        if timed_requests == 0:
            raise ValueError(f"No timed requests in {stats_file}")
        # Locust rounds times from 100 ms to float, so keys come as "120.0"
        response_times = {
            float(response_time): int(count)
            for response_time, count in entry["response_times"].items()
        }
        duration_s = entry["last_request_timestamp"] - entry["start_time"]

        return ParsedStats(
            requests=requests,
            failures=int(entry["num_failures"]),
            min_ms=float(entry["min_response_time"]),
            median_ms=_percentile(response_times, requests=timed_requests, share=0.5),
            avg_ms=entry["total_response_time"] / timed_requests,
            max_ms=float(entry["max_response_time"]),
            p95_ms=_percentile(response_times, requests=timed_requests, share=0.95),
            p99_ms=_percentile(response_times, requests=timed_requests, share=0.99),
            actual_rps=requests / duration_s,
        )


def _percentile(
    response_times: dict[float, int],
    *,
    requests: int,
    share: float,
) -> float:
    """Copy of locust percentile calc: importing locust patches process with gevent"""
    n_within = int(requests * share)
    processed = 0
    for response_time in sorted(response_times, reverse=True):
        processed += response_times[response_time]
        if requests - processed <= n_within:
            return response_time
    return 0.0
