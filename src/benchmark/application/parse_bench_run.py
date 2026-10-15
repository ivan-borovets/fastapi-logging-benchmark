from dataclasses import dataclass
from pathlib import Path

from benchmark.application.exceptions import ParsingFailedError
from benchmark.application.ports import ResultsParser
from benchmark.application.dtos import BenchMetadata, BenchResult


@dataclass(slots=True, frozen=True)
class ParseBenchRunRequest:
    metadata: BenchMetadata
    stats_file: Path
    log_lines_delivered: int


class ParseBenchRun:
    def __init__(self, results_parser: ResultsParser) -> None:
        self._results_parser = results_parser

    def execute(self, request: ParseBenchRunRequest) -> BenchResult:
        try:
            stats = self._results_parser.parse(stats_file=request.stats_file)
        except (FileNotFoundError, ValueError, KeyError) as e:
            raise ParsingFailedError(
                f"Failed to parse {request.metadata.bench_title}: {e}"
            ) from e

        return BenchResult(
            metadata=request.metadata,
            stats=stats,
            log_lines_delivered=request.log_lines_delivered,
        )
