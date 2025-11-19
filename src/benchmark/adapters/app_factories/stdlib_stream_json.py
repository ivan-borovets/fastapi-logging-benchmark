import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from benchmark.adapters.app_factories._constants import LOG_INFO_MSG
from benchmark.adapters.log_format import JsonFormatter


def make_app_stdlib_stream_json(log_lvl: str = "INFO") -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logging.basicConfig(level=log_lvl, handlers=[handler])

        yield

    app = FastAPI(lifespan=lifespan)
    log = logging.getLogger(__name__)

    @app.get("/stdlib_stream_json")
    async def stdlib_stream_json(n: int) -> dict[str, bool]:
        for _ in range(n):
            log.info(LOG_INFO_MSG)
        return {"ok": True}

    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(make_app_stdlib_stream_json())
