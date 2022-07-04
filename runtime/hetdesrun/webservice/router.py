from typing import Any, Callable

from fastapi import APIRouter as FastAPIRouter
from fastapi.types import DecoratedCallable


class HandleTrailingSlashAPIRouter(FastAPIRouter):
    """Replacement for FastAPI APIRouter class handling trailing slashes

    By default trailing slashes of endpoint pathes matter in FastAPI, i.e. the application
    listens on the exact variant specified in the path operation decorator and not on the
    other (as is the default for other frameworks, e.g. Spring Boot).

    This alternative automatically registers endpoints both with and without trailing slash.
    The exported API schema / the OpenAPI documentation only includes the non-trailing slash
    variant.

    Examples:

        @router.get("/some/path", include_in_schema=False) - nothing included in the OpenAPI schema,
        but responds to both the naked url (/some/path) and /some/path/

        @router.get("/some/path") - included in the OpenAPI schema as /some/path, responds to both
        /some/path and /some/path/

        @router.get("/some/path/") - included in the OpenAPI schema as /some/path, responds to both
        /some/path and /some/path/


        There is a special case if you have an empty prefix: FastAPI does not allow both
        empty prefix and empty path.
        So in this case or when you specify "/" with empty prefix to circumvent this, only
        the (FastAPI compatible) "/" variant will be added as route. It will be included in
        the schema if included_in_schema is True (by default True).


    Adapted from https://github.com/tiangolo/fastapi/issues/2060#issuecomment-974527690 and
    https://github.com/tiangolo/fastapi/issues/2060#issuecomment-1158967722
    """

    def api_route(
        self, path: str, *, include_in_schema: bool = True, **kwargs: Any
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:

        if self.prefix == "" and path == "":
            path = "/"

        if self.prefix == "" and path == "/":
            return super().api_route(
                path, include_in_schema=include_in_schema, **kwargs
            )

        if path.endswith("/"):
            path = path[:-1]
        add_path = super().api_route(
            path, include_in_schema=include_in_schema, **kwargs
        )

        alternate_path = path + "/"
        add_alternate_path = super().api_route(
            alternate_path, include_in_schema=False, **kwargs
        )

        def decorator(func: DecoratedCallable) -> DecoratedCallable:
            add_alternate_path(func)
            return add_path(func)

        return decorator
