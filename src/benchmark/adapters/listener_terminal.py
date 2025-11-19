import time
import threading

from rich.console import Console
from rich.live import Live

from benchmark.application.events import (
    ProgressEvent,
    BenchCompletedEvent,
    CaseStartedEvent,
)
from benchmark.application.ports import ProgressListener
from benchmark.application.dtos import BenchMetadata


class TerminalProgressListener(ProgressListener):
    def __init__(self) -> None:
        self.console: Console = Console()
        self.live: Live | None = None
        self.metadata: BenchMetadata | None = None
        self.operation: str | None = None
        self.start_time: float = 0.0
        self.running: bool = False

    def on_start(self, event: ProgressEvent) -> None:
        self.metadata = event.metadata
        self.operation = event.operation
        self.start_time = time.time()
        self.running = True

        self.console.print(f"START {self.operation} → {self.metadata.bench_title}")

        self.live = Live(console=self.console, refresh_per_second=4)
        self.live.start()

        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self) -> None:
        while self.running:
            time.sleep(1)

            if self.live is None or self.metadata is None or self.operation is None:
                return

            elapsed = int(time.time() - self.start_time)
            self.live.update(
                f"[PROGRESS] {self.operation} → {self.metadata.bench_title}, "
                f"{elapsed}s / {self.metadata.run_time}"
            )

    def on_complete(self, event: ProgressEvent) -> None:
        self.running = False

        if self.live and self.metadata and self.operation:
            elapsed = int(time.time() - self.start_time)
            self.live.update(
                f"[PROGRESS] {self.operation} → {self.metadata.bench_title}, "
                f"{elapsed}s / {self.metadata.run_time}"
            )
            self.live.stop()

        self.console.print(f"DONE {event.operation} → {event.metadata.bench_title}")

        self.live = None
        self.metadata = None
        self.operation = None

    def on_bench_completed(self, event: BenchCompletedEvent) -> None:
        br = event.bench_result
        md = br.metadata
        s = br.stats
        self.console.print(
            f"""
            RESULT {md.bench_title} ({md.n_logs_req} logs/req, {md.run_time})
            Requests:   {s.requests} (failures: {s.failures})
            Median:     {s.median_ms:.2f} ms
            Average:    {s.avg_ms:.2f} ms
            Min / Max:  {s.min_ms:.2f} / {s.max_ms:.2f} ms
            RPS:        {s.actual_rps:.2f}
            """
        )

    def on_case_started(self, event: CaseStartedEvent) -> None:
        md = event.metadata
        self.console.print(
            f"\n=== Case {event.index}/{event.total}: "
            f"{md.bench_title} ({md.n_logs_req} logs/req, {md.run_time}) ==="
        )
