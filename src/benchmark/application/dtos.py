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
    p95_ms: float
    p99_ms: float
    actual_rps: float


@dataclass(slots=True, frozen=True)
class BenchResult:
    metadata: BenchMetadata
    stats: ParsedStats
    log_lines_delivered: int


@dataclass(slots=True, frozen=True)
class EnrichedStats:
    overhead_ms: float
    overhead_pct: float
    log_delivery_pct: float | None


@dataclass(slots=True, frozen=True)
class EnrichedBenchResult:
    bench_result: BenchResult
    enriched: EnrichedStats


def enrich(
    bench_result: BenchResult,
    baseline: BenchResult,
) -> EnrichedBenchResult:
    if bench_result == baseline:
        stats = EnrichedStats(overhead_ms=0, overhead_pct=0, log_delivery_pct=None)
        return EnrichedBenchResult(bench_result, stats)
    else:
        overhead_ms = bench_result.stats.median_ms - baseline.stats.median_ms
        overhead_pct = (overhead_ms / baseline.stats.median_ms) * 100
        stats = EnrichedStats(
            overhead_ms=overhead_ms,
            overhead_pct=overhead_pct,
            log_delivery_pct=_log_delivery_pct(bench_result),
        )
        return EnrichedBenchResult(bench_result, stats)


def _log_delivery_pct(bench_result: BenchResult) -> float | None:
    expected = bench_result.stats.requests * bench_result.metadata.n_logs_req
    if expected == 0:
        return None
    return bench_result.log_lines_delivered / expected * 100


@dataclass(slots=True, frozen=True)
class Summary:
    baseline: EnrichedBenchResult
    best: EnrichedBenchResult
    results: list[EnrichedBenchResult]
