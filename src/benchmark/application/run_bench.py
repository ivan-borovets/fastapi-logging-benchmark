from dataclasses import dataclass
from pathlib import Path

from benchmark.application.dtos import BenchMetadata
from benchmark.application.events import ProgressEvent
from benchmark.application.exceptions import BenchRunError
from benchmark.application.ports import (
    ServerManager,
    LoadTester,
    ProgressListener,
)
from benchmark.domain.app_factory import AppFactory
from benchmark.domain.bench_case import BenchCase


@dataclass(slots=True, frozen=True)
class RunBenchRequest:
    metadata: BenchMetadata
    app_factory: AppFactory


@dataclass(slots=True, frozen=True)
class RunBenchResponse:
    output_path: Path
    log_lines_delivered: int


class RunBench:
    def __init__(
        self,
        server_mgr: ServerManager,
        load_tester: LoadTester,
        listener: ProgressListener,
    ) -> None:
        self._server_mgr = server_mgr
        self._load_tester = load_tester
        self._listener = listener

    def execute(self, request: RunBenchRequest) -> RunBenchResponse:
        metadata = request.metadata
        bench_case = BenchCase(
            metadata.bench_title,
            metadata.n_logs_req,
            metadata.run_time,
            request.app_factory,
        )
        event = ProgressEvent(metadata=metadata, operation="RunBench")
        self._listener.on_start(event)

        try:
            with self._server_mgr.run(bench_case) as ctx:  # type: ignore[attr-defined]
                lines_before = self._server_mgr.log_lines_delivered()
                output_path = self._load_tester.run(bench_case, ctx)
                lines_after = self._server_mgr.log_lines_delivered()
        except Exception as e:
            raise BenchRunError(f"Failed to run {bench_case.title}") from e

        self._listener.on_complete(event)
        return RunBenchResponse(output_path, lines_after - lines_before)
