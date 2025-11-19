from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import structlog
from fastapi import FastAPI

from benchmark.adapters.app_factories._constants import LOG_INFO_MSG


def make_app_structlog_async_json(log_lvl: str = "INFO") -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        """1. same output, different format"""
        structlog.configure(
            processors=[
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.CallsiteParameterAdder(
                    [
                        structlog.processors.CallsiteParameter.PATHNAME,
                        structlog.processors.CallsiteParameter.FUNC_NAME,
                        structlog.processors.CallsiteParameter.LINENO,
                    ],
                ),
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(log_lvl),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )

        yield

    app = FastAPI(lifespan=lifespan)
    log = structlog.get_logger(__name__)

    @app.get("/structlog_async_json")
    async def structlog_async_json(n: int) -> dict[str, bool]:
        for _ in range(n):
            await log.ainfo(LOG_INFO_MSG)
        return {"ok": True}

    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(make_app_structlog_async_json())
