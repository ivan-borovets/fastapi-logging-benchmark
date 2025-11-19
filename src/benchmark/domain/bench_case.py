from dataclasses import dataclass

from benchmark.domain.app_factory import AppFactory


@dataclass(slots=True, frozen=True)
class BenchCase:
    title: str
    n_logs_req: int
    run_time: str
    app_factory: AppFactory
