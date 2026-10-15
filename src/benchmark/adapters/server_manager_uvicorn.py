import http.client
import sys
import time
from contextlib import contextmanager
import socket
from typing import Final, Iterator
import subprocess as sp
from benchmark.adapters.log_sink import LogSinkProfile, PipeDrain
from benchmark.application.ports import ServerManager
from benchmark.application.dtos import RunContext
from benchmark.domain.app_factory import AppFactory
from benchmark.domain.bench_case import BenchCase

LOCALHOST: Final[str] = "127.0.0.1"
STARTUP_TIMEOUT_S: Final[float] = 10.0
WAIT_INTERVAL_S: Final[float] = 0.2
STOP_TIMEOUT_S: Final[float] = 5.0


class UvicornServerManager(ServerManager):
    def __init__(self, sink_profile: LogSinkProfile, host: str = LOCALHOST) -> None:
        self._sink_profile = sink_profile
        self._host = host
        self._drain: PipeDrain | None = None

    @contextmanager
    def run(self, bench_case: BenchCase) -> Iterator[RunContext]:  # type: ignore
        port = self._pick_free_port()
        process = self._start_server(bench_case.app_factory, port)
        if process.stdout is None:
            raise RuntimeError("Server output pipe is not attached")
        self._drain = PipeDrain(process.stdout, self._sink_profile)
        self._drain.start()

        try:
            health_path = f"/{bench_case.title}?n=1"
            if not self._wait_ready(port, health_path, timeout_s=STARTUP_TIMEOUT_S):
                raise RuntimeError(f"Server not ready at {health_path}")

            yield RunContext(self._host, port)
        finally:
            self._stop_server(process)
            self._drain.join()
            self._drain = None

    def log_lines_delivered(self) -> int:
        if self._drain is None:
            raise RuntimeError("Server is not running")
        return self._drain.lines

    def _pick_free_port(self) -> int:
        with socket.socket() as s:
            s.bind((self._host, 0))
            return int(s.getsockname()[1])

    def _start_server(self, app_factory: AppFactory, port: int) -> sp.Popen[bytes]:
        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            f"{app_factory.__module__}:{app_factory.__name__}",
            "--factory",
            "--host",
            self._host,
            "--port",
            str(port),
            "--no-access-log",
        ]
        return sp.Popen(
            cmd,
            stdin=sp.DEVNULL,
            stdout=sp.PIPE,
            stderr=sp.STDOUT,
            start_new_session=True,
        )

    def _wait_ready(self, port: int, health_path: str, timeout_s: float) -> bool:
        deadline: float = time.time() + timeout_s

        while time.time() < deadline:
            conn = http.client.HTTPConnection(self._host, port, timeout=1.0)
            try:
                conn.request("GET", health_path)
                resp = conn.getresponse()
                if 200 <= resp.status < 300:
                    return True
            except (OSError, http.client.HTTPException):
                pass
            finally:
                conn.close()

            time.sleep(WAIT_INTERVAL_S)

        return False

    def _stop_server(self, process: sp.Popen[bytes]) -> None:
        if process.poll() is not None:
            return

        process.terminate()
        try:
            process.wait(timeout=STOP_TIMEOUT_S)
        except sp.TimeoutExpired:
            process.kill()
            process.wait()
