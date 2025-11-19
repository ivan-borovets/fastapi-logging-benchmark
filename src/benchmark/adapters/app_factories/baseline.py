from fastapi import FastAPI


def make_app_baseline(log_lvl: str = "INFO") -> FastAPI:
    _ = log_lvl
    app = FastAPI()

    @app.get("/baseline")
    async def baseline(n: int) -> dict[str, bool]:
        for _ in range(n):
            pass
        return {"ok": True}

    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(make_app_baseline())
