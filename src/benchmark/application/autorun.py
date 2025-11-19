import time
from dataclasses import dataclass
from typing import Collection, Final

from benchmark.application.analyze_bench_runs import (
    AnalyzeBenchRuns,
    AnalyzeBenchRunsRequest,
)
from benchmark.application.events import BenchCompletedEvent, CaseStartedEvent
from benchmark.application.parse_bench_run import (
    ParseBenchRunRequest,
    ParseBenchRun,
)
from benchmark.application.ports import ProgressListener
from benchmark.application.dtos import BenchResult, Summary

from benchmark.application.run_bench import (
    RunBenchRequest,
    RunBench,
)

COOLDOWN_BETWEEN_CASES_S: Final[float] = 5.0


@dataclass(slots=True, frozen=True)
class AutoRunRequest:
    benches: Collection[RunBenchRequest]


class AutoRun:
    def __init__(
        self,
        run_bench: RunBench,
        parse_bench_run: ParseBenchRun,
        analyze_bench_runs: AnalyzeBenchRuns,
        listener: ProgressListener,
    ) -> None:
        self._run_bench = run_bench
        self._parse_bench_run = parse_bench_run
        self._analyze_bench_runs = analyze_bench_runs
        self._listener = listener

    def execute(self, request: AutoRunRequest) -> Summary:
        results: list[BenchResult] = []
        benches = tuple(request.benches)
        total = len(benches)
        for idx, bench_req in enumerate(benches, start=1):
            self._listener.on_case_started(
                CaseStartedEvent(
                    index=idx,
                    total=total,
                    metadata=bench_req.metadata,
                )
            )
            run_result_path = self._run_bench.execute(bench_req).output_path
            parsed_stats = self._parse_bench_run.execute(
                ParseBenchRunRequest(bench_req.metadata, run_result_path)
            )
            results.append(parsed_stats)
            self._listener.on_bench_completed(BenchCompletedEvent(parsed_stats))

            if COOLDOWN_BETWEEN_CASES_S > 0 and idx < total:
                time.sleep(COOLDOWN_BETWEEN_CASES_S)

        return self._analyze_bench_runs.execute(
            AnalyzeBenchRunsRequest(bench_results=results)
        )
