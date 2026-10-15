from operator import attrgetter
from typing import Final

from benchmark.adapters.locust_constants import TARGET_RPS_DEFAULT
from benchmark.adapters.log_sink import LogSinkProfile
from benchmark.application.dtos import ParsedStats, Summary

MIN_RPS_SHARE: Final[float] = 0.9


class TerminalSummaryRenderer:
    def __init__(self, sink_profile: LogSinkProfile) -> None:
        self._sink_profile = sink_profile

    def render(self, summary: Summary) -> None:
        baseline_metadata = summary.baseline.bench_result.metadata
        baseline_stats = summary.baseline.bench_result.stats

        best_metadata = summary.best.bench_result.metadata
        best_stats = summary.best.bench_result.stats
        best_enriched = summary.best.enriched

        print("\n===== BENCHMARK SUMMARY =====\n")

        print(f"Log sink: {self._describe_sink()}")
        print(f"Best: {best_metadata.bench_title:25} ({best_stats.median_ms:.2f} ms)")
        print(
            f"Baseline: {baseline_metadata.bench_title:25} ({baseline_stats.median_ms:.2f} ms)"
        )
        sign = "+" if best_enriched.overhead_pct >= 0 else ""
        print(
            f"Overhead: {sign}{best_enriched.overhead_pct:.1f}% "
            f"({best_enriched.overhead_ms:.2f} ms)"
        )

        print("\n-- All response times (ms), overhead by median --")

        sorted_by_median = sorted(
            summary.results, key=attrgetter("bench_result.stats.median_ms")
        )
        left_width = (
            max(
                len(
                    f"{ebr.bench_result.metadata.bench_title} "
                    f"({ebr.bench_result.metadata.n_logs_req} logs, "
                    f"{ebr.bench_result.metadata.run_time})"
                )
                for ebr in sorted_by_median
            )
            + 2
        )

        max_overhead_ms = max(abs(ebr.enriched.overhead_ms) for ebr in sorted_by_median)
        overhead_ms_width = max(7, len(f"{max_overhead_ms:.2f}"))

        for ebr in sorted_by_median:
            metadata = ebr.bench_result.metadata
            title = metadata.bench_title
            n_logs_req = metadata.n_logs_req
            run_time = metadata.run_time

            stats = ebr.bench_result.stats
            overhead_pct = ebr.enriched.overhead_pct
            overhead_ms = ebr.enriched.overhead_ms
            delivery_pct = ebr.enriched.log_delivery_pct
            delivery = "-" if delivery_pct is None else f"{delivery_pct:.0f}%"

            left = f"{title} ({n_logs_req} logs, {run_time})"
            sign = "+" if overhead_pct >= 0 else ""
            print(
                f"{left:<{left_width}}"
                f"median: {stats.median_ms:8.2f} "
                f"p95: {stats.p95_ms:8.2f} "
                f"p99: {stats.p99_ms:8.2f} "
                f"{sign}{overhead_pct:6.1f}% "
                f"({overhead_ms:{overhead_ms_width}.2f} ms) "
                f"rps: {stats.actual_rps:6.1f} "
                f"logs delivered: {delivery:>4}"
                f"{self._describe_invalid_load(stats)}"
            )

        print(
            f"\n'logs delivered' - logs that reached sink before load ended.\n"
            f"Below 100% - logger lags behind and defers work past measured window.\n"
            f"Runs below {MIN_RPS_SHARE:.0%} of {TARGET_RPS_DEFAULT} RPS "
            f"or with failures are not comparable."
        )
        print("\n=============================\n")

    def _describe_sink(self) -> str:
        if self._sink_profile.pause_ms == 0:
            return "pipe, collector reads without pauses"
        return (
            f"pipe, collector stops for {self._sink_profile.pause_ms} ms "
            f"after every {self._sink_profile.pause_every_ms} ms of reading"
        )

    def _describe_invalid_load(self, stats: ParsedStats) -> str:
        problems: list[str] = []
        if stats.actual_rps < TARGET_RPS_DEFAULT * MIN_RPS_SHARE:
            problems.append("load not sustained")
        if stats.failures > 0:
            problems.append(f"{stats.failures} failures")
        if not problems:
            return ""
        return f"  [!] {', '.join(problems)}"
