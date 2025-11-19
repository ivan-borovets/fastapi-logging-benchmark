from dataclasses import dataclass

from benchmark.application.dtos import BenchMetadata, BenchResult


@dataclass(slots=True, frozen=True, kw_only=True)
class ProgressEvent:
    metadata: BenchMetadata
    operation: str


@dataclass(slots=True, frozen=True)
class BenchCompletedEvent:
    bench_result: BenchResult


@dataclass(slots=True, frozen=True)
class CaseStartedEvent:
    metadata: BenchMetadata
    index: int
    total: int
