import http.client
import sys
import time
from contextlib import contextmanager
import socket
from typing import Final, Iterator
import subprocess as sp
from benchmark.application.ports import ServerManager
from benchmark.application.dtos import RunContext
from benchmark.domain.app_factory import AppFactory
from benchmark.domain.bench_case import BenchCase

LOCALHOST: Final[str] = "127.0.0.1"
STARTUP_TIMEOUT_S: Final[float] = 10.0
WAIT_INTERVAL_S: Final[float] = 0.2
STOP_TIMEOUT_S: Final[float] = 5.0


class UvicornServerManager(ServerManager):
    def __init__(self, host: str = LOCALHOST) -> None:
        self._host = host
        self._port: int | None = None
        self._process: sp.Popen[bytes] | None = None

    @contextmanager
    def run(self, bench_case: BenchCase) -> Iterator[RunContext]:  # type: ignore
        self._port = self._pick_free_port()
        self._process = self._start_server(bench_case.app_factory, self._port)

        health_path = f"/{bench_case.title}?n=1"
        if not self._wait_ready(self._port, health_path, timeout_s=STARTUP_TIMEOUT_S):
            raise RuntimeError(f"Server not ready at {health_path}")

        yield RunContext(self._host, self._port)

        self._stop_server()
        self._port, self._process = None, None

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
            stdout=sp.DEVNULL,
            stderr=sp.DEVNULL,
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

    def _stop_server(self) -> None:
        if self._process is None or self._process.poll() is not None:
            return

        self._process.terminate()
        try:
            self._process.wait(timeout=STOP_TIMEOUT_S)
        except sp.TimeoutExpired:
            self._process.kill()
            self._process.wait()
