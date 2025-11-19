from typing import Protocol

from fastapi import FastAPI


class AppFactory(Protocol):
    __module__: str
    __name__: str

    def __call__(self) -> FastAPI: ...
