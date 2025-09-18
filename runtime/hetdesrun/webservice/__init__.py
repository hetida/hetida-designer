from functools import cache

from fastapi import FastAPI


@cache
def get_app() -> FastAPI:
    from hetdesrun.webservice.application import init_app  # noqa: PLC0415

    return init_app()
