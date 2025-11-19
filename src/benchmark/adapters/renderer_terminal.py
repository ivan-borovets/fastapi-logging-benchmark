from operator import attrgetter

from benchmark.application.dtos import Summary


class TerminalSummaryRenderer:
    def render(self, summary: Summary) -> None:
        baseline_metadata = summary.baseline.bench_result.metadata
        baseline_stats = summary.baseline.bench_result.stats

        best_metadata = summary.best.bench_result.metadata
        best_stats = summary.best.bench_result.stats
        best_enriched = summary.best.enriched

        print("\n===== BENCHMARK SUMMARY =====\n")

        print(f"Best: {best_metadata.bench_title:25} ({best_stats.median_ms:.2f} ms)")
        print(
            f"Baseline: {baseline_metadata.bench_title:25} ({baseline_stats.median_ms:.2f} ms)"
        )
        sign = "+" if best_enriched.overhead_pct >= 0 else ""
        print(
            f"Overhead: {sign}{best_enriched.overhead_pct:.1f}% "
            f"({best_enriched.overhead_ms:.2f} ms)"
        )

        print("\n-- All median response times (ms) --")

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

            median = ebr.bench_result.stats.median_ms
            overhead_pct = ebr.enriched.overhead_pct
            overhead_ms = ebr.enriched.overhead_ms

            left = f"{title} ({n_logs_req} logs, {run_time})"
            sign = "+" if overhead_pct >= 0 else ""
            print(
                f"{left:<{left_width}}"
                f"median (ms): {median:8.2f} "
                f"{sign}{overhead_pct:6.1f}% "
                f"({overhead_ms:{overhead_ms_width}.2f} ms)"
            )

        print("\n=============================\n")
