import os
import threading
import time
from dataclasses import dataclass
from typing import IO, Final

CHUNK_SIZE: Final[int] = 64 * 1024


@dataclass(frozen=True, slots=True)
class LogSinkProfile:
    pause_ms: int
    pause_every_ms: int


class PipeDrain:
    """Reads app output like container log collector; while it pauses, writes block"""

    def __init__(self, pipe: IO[bytes], profile: LogSinkProfile) -> None:
        self._pipe = pipe
        self._profile = profile
        self._lines = 0
        self._thread = threading.Thread(target=self._drain)

    @property
    def lines(self) -> int:
        return self._lines

    def start(self) -> None:
        self._thread.start()

    def join(self) -> None:
        self._thread.join()
        self._pipe.close()

    def _drain(self) -> None:
        fd = self._pipe.fileno()
        pause_s = self._profile.pause_ms / 1000
        pause_every_s = self._profile.pause_every_ms / 1000
        next_pause_at = time.monotonic() + pause_every_s
        while chunk := os.read(fd, CHUNK_SIZE):
            self._lines += chunk.count(b"\n")
            if pause_s > 0 and time.monotonic() >= next_pause_at:
                time.sleep(pause_s)
                next_pause_at = time.monotonic() + pause_every_s
