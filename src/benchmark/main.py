import argparse
import random
from pathlib import Path

from benchmark.adapters.load_tester_locust import LocustLoadTester
from benchmark.adapters.locust_constants import (
    NEW_FLAG_NAME,
    NEW_FLAG_HELP,
    N_LOGS_REQ_DEFAULT,
    LOCUSTFILE_PATH,
    OUTPUT_DIR_PATH,
    N_USERS_DEFAULT,
    SPAWN_RATE_DEFAULT,
    RUN_TIME_DEFAULT,
)
from benchmark.adapters.listener_terminal import TerminalProgressListener
from benchmark.adapters.renderer_terminal import TerminalSummaryRenderer
from benchmark.adapters.results_parser_csv import CsvResultsParser
from benchmark.adapters.server_manager_uvicorn import UvicornServerManager
from benchmark.application.analyze_bench_runs import AnalyzeBenchRuns
from benchmark.application.autorun import AutoRun, AutoRunRequest
from benchmark.application.parse_bench_run import ParseBenchRun
from benchmark.application.run_bench import RunBench
from benchmark.cases import (
    cases_json,
    cases_orjson,
    cases_all,
    cases_fastest,
    cases_stable_vs_unstable,
)


def setup_autorun(
    locustfile: Path = LOCUSTFILE_PATH,
    output_dir: Path = OUTPUT_DIR_PATH,
    n_users: int = N_USERS_DEFAULT,
    spawn_rate: int = SPAWN_RATE_DEFAULT,
) -> AutoRun:
    listener = TerminalProgressListener()
    return AutoRun(
        run_bench=RunBench(
            server_mgr=UvicornServerManager(),
            load_tester=LocustLoadTester(
                locustfile=locustfile,
                output_dir=output_dir,
                n_users=n_users,
                spawn_rate=spawn_rate,
            ),
            listener=listener,
        ),
        parse_bench_run=ParseBenchRun(results_parser=CsvResultsParser()),
        analyze_bench_runs=AnalyzeBenchRuns(),
        listener=listener,
    )


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Logging benchmarking",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument(
        "--mode",
        choices=["all", "fastest", "json", "orjson", "stable_vs_unstable"],
        default="fastest",
        help="Preset of cases",
    )
    p.add_argument(
        NEW_FLAG_NAME,
        type=int,
        default=N_LOGS_REQ_DEFAULT,
        help=NEW_FLAG_HELP,
    )
    p.add_argument(
        "--time",
        dest="run_time",
        default=RUN_TIME_DEFAULT,
        help="Locust run time, e.g. 30s, 2m",
    )
    p.add_argument(
        "--shuffle",
        action="store_true",
        help="Shuffle order of cases before running",
    )
    return p.parse_args()


def main() -> None:
    factories = {
        "all": cases_all,
        "fastest": cases_fastest,
        "json": cases_json,
        "orjson": cases_orjson,
        "stable_vs_unstable": cases_stable_vs_unstable,
    }
    try:
        args = parse_args()
        cases_factory = factories[args.mode]
        cases = cases_factory(n_logs_req=args.n_logs_req, run_time=args.run_time)
        if args.shuffle:
            random.shuffle(cases)
        autorun = setup_autorun()
        renderer = TerminalSummaryRenderer()
        summary = autorun.execute(AutoRunRequest(cases))
        renderer.render(summary)
    except KeyboardInterrupt:
        print("Interrupted. Shutting down...")


if __name__ == "__main__":
    main()
