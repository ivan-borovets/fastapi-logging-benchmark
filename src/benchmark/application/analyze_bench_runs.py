from collections.abc import Collection
from dataclasses import dataclass
from operator import attrgetter

from benchmark.application.dtos import (
    Summary,
    BenchResult,
    EnrichedBenchResult,
    enrich,
)


@dataclass(slots=True, frozen=True)
class AnalyzeBenchRunsRequest:
    bench_results: Collection[BenchResult]


class AnalyzeBenchRuns:
    def execute(self, request: AnalyzeBenchRunsRequest) -> Summary:
        bench_results = request.bench_results
        if not bench_results:
            raise ValueError("No bench results to analyze")

        raw_baselines = [
            br for br in bench_results if br.metadata.bench_title == "baseline"
        ]
        if not raw_baselines:
            raise ValueError("Meaningless analysis: no baseline")
        if len(raw_baselines) > 1:
            raise ValueError(f"Multiple baselines found ({len(raw_baselines)})")

        raw_competitors = [
            br for br in bench_results if br.metadata.bench_title != "baseline"
        ]
        if not raw_competitors:
            raise ValueError("No competitors to analyze (only baseline present)")

        raw_baseline = raw_baselines.pop()

        enriched: list[EnrichedBenchResult] = []
        for br in bench_results:
            enriched.append(enrich(br, raw_baseline))

        baseline = [
            e for e in enriched if e.bench_result.metadata.bench_title == "baseline"
        ].pop()
        competitors = [
            e for e in enriched if e.bench_result.metadata.bench_title != "baseline"
        ]
        best = min(competitors, key=attrgetter("bench_result.stats.median_ms"))

        return Summary(
            baseline=baseline,
            best=best,
            results=enriched,
        )
