from functools import cache

from fastapi import FastAPI


@cache
def get_app() -> FastAPI:
    from hetdesrun.webservice.application import init_app

    return init_app()
