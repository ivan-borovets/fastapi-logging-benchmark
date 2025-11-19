import argparse

from locust import HttpUser, task, constant_throughput, tag, events
from locust.env import Environment

from benchmark.adapters.locust_constants import (
    NEW_FLAG_NAME,
    NEW_FLAG_HELP,
    N_LOGS_REQ_DEFAULT,
    CONSTANT_THROUGHPUT_DEFAULT,
)


@events.init_command_line_parser.add_listener  # type: ignore
def add_n_logs_req_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(NEW_FLAG_NAME, type=int, help=NEW_FLAG_HELP)


@events.init.add_listener  # type: ignore
def apply_n_logs_req_arg(environment: Environment, **_: object) -> None:
    n = environment.parsed_options.n_logs_req  # type: ignore
    if n is None:
        return
    if (n_int := int(n)) <= 0:
        raise ValueError(f"{NEW_FLAG_NAME} must be a positive integer")
    WebsiteUser.n_logs_req = n_int


class WebsiteUser(HttpUser):
    wait_time = constant_throughput(CONSTANT_THROUGHPUT_DEFAULT)  # type: ignore
    n_logs_req = N_LOGS_REQ_DEFAULT

    @tag("baseline")
    @task
    def baseline(self) -> None:
        self.client.get("/baseline", params={"n": self.n_logs_req})

    @tag("stdlib_stream_json")
    @task
    def stdlib_stream_json(self) -> None:
        self.client.get("/stdlib_stream_json", params={"n": self.n_logs_req})

    @tag("stdlib_stream_orjson")
    @task
    def stdlib_stream_orjson(self) -> None:
        self.client.get("/stdlib_stream_orjson", params={"n": self.n_logs_req})

    @tag("stdlib_queue_json")
    @task
    def stdlib_queue_json(self) -> None:
        self.client.get("/stdlib_queue_json", params={"n": self.n_logs_req})

    @tag("stdlib_queue_orjson")
    @task
    def stdlib_queue_orjson(self) -> None:
        self.client.get("/stdlib_queue_orjson", params={"n": self.n_logs_req})

    @tag("aiologger_no_await_json")
    @task
    def aiologger_no_await_json(self) -> None:
        self.client.get("/aiologger_no_await_json", params={"n": self.n_logs_req})

    @tag("aiologger_no_await_orjson")
    @task
    def aiologger_no_await_orjson(self) -> None:
        self.client.get("/aiologger_no_await_orjson", params={"n": self.n_logs_req})

    @tag("aiologger_with_await_json")
    @task
    def aiologger_with_await_json(self) -> None:
        self.client.get("/aiologger_with_await_json", params={"n": self.n_logs_req})

    @tag("aiologger_with_await_orjson")
    @task
    def aiologger_with_await_orjson(self) -> None:
        self.client.get("/aiologger_with_await_orjson", params={"n": self.n_logs_req})

    @tag("structlog_sync_json")
    @task
    def structlog_sync_json(self) -> None:
        self.client.get("/structlog_sync_json", params={"n": self.n_logs_req})

    @tag("structlog_sync_orjson")
    @task
    def structlog_sync_orjson(self) -> None:
        self.client.get("/structlog_sync_orjson", params={"n": self.n_logs_req})

    @tag("structlog_async_json")
    @task
    def structlog_async_json(self) -> None:
        self.client.get("/structlog_async_json", params={"n": self.n_logs_req})

    @tag("structlog_async_orjson")
    @task
    def structlog_async_orjson(self) -> None:
        self.client.get("/structlog_async_orjson", params={"n": self.n_logs_req})

    @tag("structlog_experimental_orjson")
    @task
    def structlog_experimental_orjson(self) -> None:
        self.client.get("/structlog_experimental_orjson", params={"n": self.n_logs_req})
