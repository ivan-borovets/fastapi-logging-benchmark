import logging
import queue
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from logging.handlers import QueueHandler, QueueListener
from fastapi import FastAPI

from benchmark.adapters.app_factories._constants import LOG_INFO_MSG
from benchmark.adapters.log_format import JsonFormatter


def make_app_stdlib_queue_json(log_lvl: str = "INFO") -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        s_handler = logging.StreamHandler()
        s_handler.setFormatter(JsonFormatter())

        q: queue.Queue[logging.LogRecord] = queue.Queue(-1)
        q_handler = QueueHandler(q)

        root_logger = logging.getLogger()
        root_logger.setLevel(log_lvl)
        root_logger.addHandler(q_handler)

        q_listener = QueueListener(q, s_handler)
        q_listener.start()

        yield

        root_logger.removeHandler(q_handler)
        q_listener.stop()

    app = FastAPI(lifespan=lifespan)
    log = logging.getLogger(__name__)

    @app.get("/stdlib_queue_json")
    async def stdlib_queue_json(n: int) -> dict[str, bool]:
        for _ in range(n):
            log.info(LOG_INFO_MSG)
        return {"ok": True}

    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(make_app_stdlib_queue_json())
