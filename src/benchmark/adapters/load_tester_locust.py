import subprocess as sp
from pathlib import Path

from benchmark.adapters.locust_constants import NEW_FLAG_NAME
from benchmark.application.ports import LoadTester
from benchmark.application.dtos import RunContext
from benchmark.domain.bench_case import BenchCase


class LocustLoadTester(LoadTester):
    def __init__(
        self,
        locustfile: Path,
        output_dir: Path,
        n_users: int,
        spawn_rate: int,
    ) -> None:
        self._locustfile: Path = locustfile
        self._output_dir: Path = output_dir
        self._n_users: int = n_users
        self._spawn_rate: int = spawn_rate

    def run(self, bench_case: BenchCase, context: RunContext) -> Path:
        self._output_dir.mkdir(parents=True, exist_ok=True)
        host_url = f"http://{context.host}:{context.port}"
        csv_prefix = (
            self._output_dir / f"{bench_case.n_logs_req}logs_{bench_case.title}"
        )
        stats_csv = csv_prefix.with_name(f"{csv_prefix.name}{'_stats.csv'}")

        cmd = [
            "locust",
            "--headless",
            "-f",
            str(self._locustfile),
            "-u",
            str(self._n_users),
            "-r",
            str(self._spawn_rate),
            "-t",
            bench_case.run_time,
            "--tag",
            bench_case.title,
            "--host",
            host_url,
            "--csv",
            str(csv_prefix),
            "--only-summary",
            f"{NEW_FLAG_NAME}",
            str(bench_case.n_logs_req),
        ]
        sp.run(
            cmd,
            stdout=sp.DEVNULL,
            stderr=sp.DEVNULL,
            check=True,
        )

        return stats_csv
