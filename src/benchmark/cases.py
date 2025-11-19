from benchmark.adapters.app_factories.aiologger_no_await_json import (
    make_app_aiologger_no_await_json,
)
from benchmark.adapters.app_factories.aiologger_no_await_orjson import (
    make_app_aiologger_no_await_orjson,
)
from benchmark.adapters.app_factories.aiologger_with_await_json import (
    make_app_aiologger_with_await_json,
)
from benchmark.adapters.app_factories.aiologger_with_await_orjson import (
    make_app_aiologger_with_await_orjson,
)
from benchmark.adapters.app_factories.baseline import make_app_baseline
from benchmark.adapters.app_factories.stdlib_queue_json import (
    make_app_stdlib_queue_json,
)
from benchmark.adapters.app_factories.stdlib_queue_orjson import (
    make_app_stdlib_queue_orjson,
)
from benchmark.adapters.app_factories.stdlib_stream_json import (
    make_app_stdlib_stream_json,
)
from benchmark.adapters.app_factories.stdlib_stream_orjson import (
    make_app_stdlib_stream_orjson,
)
from benchmark.adapters.app_factories.structlog_async_json import (
    make_app_structlog_async_json,
)
from benchmark.adapters.app_factories.structlog_async_orjson import (
    make_app_structlog_async_orjson,
)
from benchmark.adapters.app_factories.structlog_experimental_orjson import (
    make_app_structlog_experimental_orjson,
)
from benchmark.adapters.app_factories.structlog_sync_json import (
    make_app_structlog_sync_json,
)
from benchmark.adapters.app_factories.structlog_sync_orjson import (
    make_app_structlog_sync_orjson,
)
from benchmark.adapters.locust_constants import N_LOGS_REQ_DEFAULT, RUN_TIME_DEFAULT

from benchmark.application.dtos import BenchMetadata
from benchmark.application.run_bench import RunBenchRequest


def cases_all(
    n_logs_req: int = N_LOGS_REQ_DEFAULT,
    run_time: str = RUN_TIME_DEFAULT,
) -> list[RunBenchRequest]:
    return [
        RunBenchRequest(
            BenchMetadata("baseline", n_logs_req, run_time),
            make_app_baseline,
        ),
        RunBenchRequest(
            BenchMetadata("aiologger_no_await_json", n_logs_req, run_time),
            make_app_aiologger_no_await_json,
        ),
        RunBenchRequest(
            BenchMetadata("aiologger_no_await_orjson", n_logs_req, run_time),
            make_app_aiologger_no_await_orjson,
        ),
        RunBenchRequest(
            BenchMetadata("aiologger_with_await_json", n_logs_req, run_time),
            make_app_aiologger_with_await_json,
        ),
        RunBenchRequest(
            BenchMetadata("aiologger_with_await_orjson", n_logs_req, run_time),
            make_app_aiologger_with_await_orjson,
        ),
        RunBenchRequest(
            BenchMetadata("stdlib_queue_json", n_logs_req, run_time),
            make_app_stdlib_queue_json,
        ),
        RunBenchRequest(
            BenchMetadata("stdlib_queue_orjson", n_logs_req, run_time),
            make_app_stdlib_queue_orjson,
        ),
        RunBenchRequest(
            BenchMetadata("stdlib_stream_json", n_logs_req, run_time),
            make_app_stdlib_stream_json,
        ),
        RunBenchRequest(
            BenchMetadata("stdlib_stream_orjson", n_logs_req, run_time),
            make_app_stdlib_stream_orjson,
        ),
        RunBenchRequest(
            BenchMetadata("structlog_async_json", n_logs_req, run_time),
            make_app_structlog_async_json,
        ),
        RunBenchRequest(
            BenchMetadata("structlog_async_orjson", n_logs_req, run_time),
            make_app_structlog_async_orjson,
        ),
        RunBenchRequest(
            BenchMetadata("structlog_sync_json", n_logs_req, run_time),
            make_app_structlog_sync_json,
        ),
        RunBenchRequest(
            BenchMetadata("structlog_sync_orjson", n_logs_req, run_time),
            make_app_structlog_sync_orjson,
        ),
        RunBenchRequest(
            BenchMetadata("structlog_experimental_orjson", n_logs_req, run_time),
            make_app_structlog_experimental_orjson,
        ),
    ]


def cases_json(
    n_logs_req: int = N_LOGS_REQ_DEFAULT,
    run_time: str = RUN_TIME_DEFAULT,
) -> list[RunBenchRequest]:
    return [
        RunBenchRequest(
            BenchMetadata("baseline", n_logs_req, run_time),
            make_app_baseline,
        ),
        RunBenchRequest(
            BenchMetadata("aiologger_no_await_json", n_logs_req, run_time),
            make_app_aiologger_no_await_json,
        ),
        RunBenchRequest(
            BenchMetadata("aiologger_with_await_json", n_logs_req, run_time),
            make_app_aiologger_with_await_json,
        ),
        RunBenchRequest(
            BenchMetadata("stdlib_queue_json", n_logs_req, run_time),
            make_app_stdlib_queue_json,
        ),
        RunBenchRequest(
            BenchMetadata("stdlib_stream_json", n_logs_req, run_time),
            make_app_stdlib_stream_json,
        ),
        RunBenchRequest(
            BenchMetadata("structlog_async_json", n_logs_req, run_time),
            make_app_structlog_async_json,
        ),
        RunBenchRequest(
            BenchMetadata("structlog_sync_json", n_logs_req, run_time),
            make_app_structlog_sync_json,
        ),
    ]


def cases_orjson(
    n_logs_req: int = N_LOGS_REQ_DEFAULT,
    run_time: str = RUN_TIME_DEFAULT,
) -> list[RunBenchRequest]:
    return [
        RunBenchRequest(
            BenchMetadata("baseline", n_logs_req, run_time),
            make_app_baseline,
        ),
        RunBenchRequest(
            BenchMetadata("aiologger_no_await_orjson", n_logs_req, run_time),
            make_app_aiologger_no_await_orjson,
        ),
        RunBenchRequest(
            BenchMetadata("aiologger_with_await_orjson", n_logs_req, run_time),
            make_app_aiologger_with_await_orjson,
        ),
        RunBenchRequest(
            BenchMetadata("stdlib_queue_orjson", n_logs_req, run_time),
            make_app_stdlib_queue_orjson,
        ),
        RunBenchRequest(
            BenchMetadata("stdlib_stream_orjson", n_logs_req, run_time),
            make_app_stdlib_stream_orjson,
        ),
        RunBenchRequest(
            BenchMetadata("structlog_async_orjson", n_logs_req, run_time),
            make_app_structlog_async_orjson,
        ),
        RunBenchRequest(
            BenchMetadata("structlog_sync_orjson", n_logs_req, run_time),
            make_app_structlog_sync_orjson,
        ),
        RunBenchRequest(
            BenchMetadata("structlog_experimental_orjson", n_logs_req, run_time),
            make_app_structlog_experimental_orjson,
        ),
    ]


def cases_fastest(
    n_logs_req: int = N_LOGS_REQ_DEFAULT,
    run_time: str = RUN_TIME_DEFAULT,
) -> list[RunBenchRequest]:
    return [
        RunBenchRequest(
            BenchMetadata("baseline", n_logs_req, run_time),
            make_app_baseline,
        ),
        RunBenchRequest(
            BenchMetadata("structlog_experimental_orjson", n_logs_req, run_time),
            make_app_structlog_experimental_orjson,
        ),
        RunBenchRequest(
            BenchMetadata("structlog_sync_orjson", n_logs_req, run_time),
            make_app_structlog_sync_orjson,
        ),
        RunBenchRequest(
            BenchMetadata("aiologger_no_await_orjson", n_logs_req, run_time),
            make_app_aiologger_no_await_orjson,
        ),
        RunBenchRequest(
            BenchMetadata("stdlib_stream_orjson", n_logs_req, run_time),
            make_app_stdlib_stream_orjson,
        ),
    ]


def cases_stable_vs_unstable(
    n_logs_req: int = N_LOGS_REQ_DEFAULT,
    run_time: str = RUN_TIME_DEFAULT,
) -> list[RunBenchRequest]:
    return [
        RunBenchRequest(
            BenchMetadata("baseline", n_logs_req, run_time),
            make_app_baseline,
        ),
        RunBenchRequest(
            BenchMetadata("structlog_experimental_orjson", n_logs_req, run_time),
            make_app_structlog_experimental_orjson,
        ),
        RunBenchRequest(
            BenchMetadata("stdlib_queue_orjson", n_logs_req, run_time),
            make_app_stdlib_queue_orjson,
        ),
        RunBenchRequest(
            BenchMetadata("aiologger_no_await_orjson", n_logs_req, run_time),
            make_app_aiologger_no_await_orjson,
        ),
    ]
