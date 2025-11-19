from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BenchMetadata:
    bench_title: str
    n_logs_req: int
    run_time: str


@dataclass(frozen=True, slots=True)
class RunContext:
    host: str
    port: int


@dataclass(slots=True, frozen=True)
class ParsedStats:
    requests: int
    failures: int
    min_ms: float
    median_ms: float
    avg_ms: float
    max_ms: float
    actual_rps: float


@dataclass(slots=True, frozen=True)
class BenchResult:
    metadata: BenchMetadata
    stats: ParsedStats


@dataclass(slots=True, frozen=True)
class EnrichedStats:
    overhead_ms: float
    overhead_pct: float


@dataclass(slots=True, frozen=True)
class EnrichedBenchResult:
    bench_result: BenchResult
    enriched: EnrichedStats


def enrich(
    bench_result: BenchResult,
    baseline: BenchResult,
) -> EnrichedBenchResult:
    if bench_result == baseline:
        stats = EnrichedStats(0, 0)
        return EnrichedBenchResult(bench_result, stats)
    else:
        overhead_ms = bench_result.stats.median_ms - baseline.stats.median_ms
        overhead_pct = (overhead_ms / baseline.stats.median_ms) * 100
        stats = EnrichedStats(overhead_ms, overhead_pct)
        return EnrichedBenchResult(bench_result, stats)


@dataclass(slots=True, frozen=True)
class Summary:
    baseline: EnrichedBenchResult
    best: EnrichedBenchResult
    results: list[EnrichedBenchResult]
