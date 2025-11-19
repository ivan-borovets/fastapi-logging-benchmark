from abc import abstractmethod
from pathlib import Path
from typing import Protocol, Iterator

from benchmark.application.dtos import RunContext, ParsedStats
from benchmark.application.events import (
    ProgressEvent,
    BenchCompletedEvent,
    CaseStartedEvent,
)
from benchmark.domain.bench_case import BenchCase


class ServerManager(Protocol):
    @abstractmethod
    def run(self, bench_case: BenchCase) -> Iterator[RunContext]: ...


class LoadTester(Protocol):
    @abstractmethod
    def run(self, bench_case: BenchCase, context: RunContext) -> Path: ...


class ProgressListener(Protocol):
    @abstractmethod
    def on_start(self, event: ProgressEvent) -> None: ...
    @abstractmethod
    def on_complete(self, event: ProgressEvent) -> None: ...
    @abstractmethod
    def on_bench_completed(self, event: BenchCompletedEvent) -> None: ...
    @abstractmethod
    def on_case_started(self, event: CaseStartedEvent) -> None: ...


class ResultsParser(Protocol):
    @abstractmethod
    def parse(self, stats_file: Path) -> ParsedStats: ...
