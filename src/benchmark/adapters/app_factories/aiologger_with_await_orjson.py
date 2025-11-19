import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import aiologger
import aiologger.loggers.json
from fastapi import FastAPI

from benchmark.adapters.app_factories._constants import LOG_INFO_MSG
from benchmark.adapters.log_format import orjson_serializer_to_str


def make_app_aiologger_with_await_orjson(log_lvl: str = "INFO") -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        """
        1. hard to adjust formatting
        2. no hierarchy, has to be attached to app
        """
        app.state.logger = aiologger.loggers.json.JsonLogger.with_default_handlers(
            level=getattr(logging, log_lvl),
            serializer=orjson_serializer_to_str,
        )

        yield

        await app.state.logger.shutdown()

    app = FastAPI(lifespan=lifespan)

    @app.get("/aiologger_with_await_orjson")
    async def aiologger_with_await_orjson(n: int) -> dict[str, bool]:
        log = app.state.logger
        for _ in range(n):
            await log.info(LOG_INFO_MSG)
        return {"ok": True}

    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(make_app_aiologger_with_await_orjson())
