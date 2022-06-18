from functools import cache


@cache
def get_app():
    from hetdesrun.webservice.application import init_app

    return init_app()
