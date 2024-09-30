import json
import logging
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from hetdesrun import VERSION
from hetdesrun.adapters.external_sources.config import get_external_sources_adapter_config
from hetdesrun.adapters.kafka.config import get_kafka_adapter_config
from hetdesrun.adapters.sql_adapter.config import get_sql_adapter_config
from hetdesrun.adapters.virtual_structure_adapter.config import get_vst_adapter_config
from hetdesrun.backend.service.adapter_router import adapter_router
from hetdesrun.backend.service.base_item_router import base_item_router
from hetdesrun.backend.service.component_router import component_router
from hetdesrun.backend.service.documentation_router import documentation_router
from hetdesrun.backend.service.info_router import info_router
from hetdesrun.backend.service.maintenance_router import maintenance_router
from hetdesrun.backend.service.transformation_router import (
    dashboard_router,
    transformation_router,
)
from hetdesrun.backend.service.virtual_structure_router import virtual_structure_router
from hetdesrun.backend.service.wiring_router import wiring_router
from hetdesrun.backend.service.workflow_router import workflow_router
from hetdesrun.webservice.auth_dependency import get_auth_deps
from hetdesrun.webservice.config import get_config

if get_config().hd_kafka_consumer_enabled:
    from hetdesrun.backend.kafka.consumer import get_kafka_worker_context


logger = logging.getLogger(__name__)


class AdditionalLoggingRoute(APIRoute):
    """Additional logging and information in case of errors

    Makes sure that requests are logged in every situation.
    """

    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            try:
                json_data = await request.json()
            except json.decoder.JSONDecodeError:
                body = await request.body()
                logger.info("RECEIVED BODY (could not parse as json):\n%s", body.decode())
            else:
                logger.info(
                    "RECEIVED JSON BODY: \n%s",
                    json.dumps(json_data, indent=2, sort_keys=True),
                )
            try:
                return await original_route_handler(request)  # type: ignore
            except RequestValidationError as exc:
                body = await request.body()
                detail = {"errors": exc.errors(), "body": body.decode()}
                logger.info("Request Validation Error: %s", str(exc))
                raise HTTPException(status_code=422, detail=detail) from exc

        return custom_route_handler


middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=get_config().allowed_origins.split(","),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:  # noqa: ARG001
    logger.info("Initializing application ...")
    if get_config().hd_kafka_consumer_enabled and get_config().is_backend_service:
        logger.info("Initializing Kafka consumer...")
        kakfa_worker_context = get_kafka_worker_context()
        await kakfa_worker_context.start()
    yield
    logger.info("Shutting down application...")
    if get_config().hd_kafka_consumer_enabled and get_config().is_backend_service:
        logger.info("Shutting down Kafka consumer...")
        kakfa_worker_context = get_kafka_worker_context()
        await kakfa_worker_context.stop()


def app_desc_part() -> str:
    if len(get_config().restrict_to_trafo_exec_service) > 0:
        restriced_exec_suffix = " (restricted execution service mode)"
    else:
        restriced_exec_suffix = ""

    if get_config().is_backend_service and get_config().is_runtime_service:
        return "Runtime + Backend" + restriced_exec_suffix
    if get_config().is_backend_service and not get_config().is_runtime_service:
        return "Backend" + restriced_exec_suffix
    return "Runtime" + restriced_exec_suffix


def init_app() -> FastAPI:  # noqa: PLR0912,PLR0915
    import sys

    # reimporting runtime_router and local_file router since they have
    # endpoint-individual auth settings and therefore load config during
    # module import. This enables (unit) testing with different configurations.
    try:  # noqa: SIM105
        del sys.modules["hetdesrun.service.runtime_router"]
    except KeyError:
        pass
    from hetdesrun.service.runtime_router import runtime_router

    # same for restricted_transformation_router
    try:  # noqa: SIM105
        del sys.modules["hetdesrun.backend.service.exec_only_router"]
    except KeyError:
        pass
    from hetdesrun.backend.service.exec_only_router import (
        restricted_transformation_router,
    )

    try:  # noqa: SIM105
        del sys.modules["hetdesrun.adapters.local_file.webservice"]
    except KeyError:
        pass

    try:  # noqa: SIM105
        del sys.modules["hetdesrun.adapters.blob_storage.webservice"]
    except KeyError:
        pass

    try:  # noqa: SIM105
        del sys.modules["hetdesrun.adapters.sql_adapter.webservice"]
    except KeyError:
        pass

    try:  # noqa: SIM105
        del sys.modules["hetdesrun.adapters.kafka.webservice"]
    except KeyError:
        pass

    try:  # noqa: SIM105
        del sys.modules["hetdesrun.adapters.virtual_structure_adapter.webservice"]
    except KeyError:
        pass

    try:  # noqa: SIM105
        del sys.modules["hetdesrun.adapters.external_sources.webservice"]
    except KeyError:
        pass

    from hetdesrun.adapters.blob_storage.config import get_blob_adapter_config
    from hetdesrun.adapters.blob_storage.webservice import (
        blob_storage_adapter_router,
    )
    from hetdesrun.adapters.external_sources.webservice import external_sources_adapter_router
    from hetdesrun.adapters.kafka.webservice import kafka_adapter_router
    from hetdesrun.adapters.local_file.webservice import (
        local_file_adapter_router,
    )
    from hetdesrun.adapters.sql_adapter.webservice import sql_adapter_router
    from hetdesrun.adapters.virtual_structure_adapter.webservice import (
        virtual_structure_adapter_router,
    )

    app = FastAPI(
        title="Hetida Designer " + app_desc_part() + " API",
        description="Hetida Designer " + app_desc_part() + " Web Services API",
        version=VERSION,
        lifespan=lifespan,
        root_path=get_config().swagger_prefix,
        middleware=middleware,
    )

    app.router.route_class = AdditionalLoggingRoute

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        logger.info("Request validation failed:\n%s", str(exc))
        return await request_validation_exception_handler(request, exc)

    if get_config().is_runtime_service and len(get_config().restrict_to_trafo_exec_service) == 0:
        app.include_router(
            local_file_adapter_router
        )  # auth dependency set individually per endpoint
        if get_kafka_adapter_config().active and get_kafka_adapter_config().service_in_runtime:
            app.include_router(kafka_adapter_router)
        if get_sql_adapter_config().active and get_sql_adapter_config().service_in_runtime:
            app.include_router(sql_adapter_router)  # auth dependency set individually per endpoint
        if (
            get_external_sources_adapter_config().active
            and get_external_sources_adapter_config().service_in_runtime
        ):
            app.include_router(
                external_sources_adapter_router
            )  # auth dependency set individually per endpoint

        if get_blob_adapter_config().adapter_hierarchy_location != "":
            app.include_router(
                blob_storage_adapter_router
            )  # auth dependency set individually per endpoint
        if get_vst_adapter_config().active and get_vst_adapter_config().service_in_runtime:
            app.include_router(virtual_structure_adapter_router)
        app.include_router(
            runtime_router, prefix="/engine"
        )  # auth dependency set individually per endpoint

    if get_config().is_backend_service and len(get_config().restrict_to_trafo_exec_service) == 0:
        app.include_router(virtual_structure_adapter_router)
        if get_sql_adapter_config().active and not get_sql_adapter_config().service_in_runtime:
            app.include_router(sql_adapter_router)  # auth dependency set individually per endpoint
        if (
            get_external_sources_adapter_config().active
            and not get_external_sources_adapter_config().service_in_runtime
        ):
            app.include_router(
                external_sources_adapter_router
            )  # auth dependency set individually per endpoint

        if get_kafka_adapter_config().active and not get_kafka_adapter_config().service_in_runtime:
            app.include_router(
                kafka_adapter_router
            )  # auth dependency set individually per endpoint
        if get_vst_adapter_config().active and not get_vst_adapter_config().service_in_runtime:
            app.include_router(virtual_structure_adapter_router)
        app.include_router(adapter_router, prefix="/api", dependencies=get_auth_deps())
        app.include_router(base_item_router, prefix="/api", dependencies=get_auth_deps())
        app.include_router(documentation_router, prefix="/api", dependencies=get_auth_deps())
        app.include_router(info_router, prefix="/api")  # reachable without authorization
        app.include_router(component_router, prefix="/api", dependencies=get_auth_deps())
        app.include_router(workflow_router, prefix="/api", dependencies=get_auth_deps())
        app.include_router(wiring_router, prefix="/api", dependencies=get_auth_deps())
        app.include_router(transformation_router, prefix="/api", dependencies=get_auth_deps())
        app.include_router(
            dashboard_router,
            prefix="/api",  # individual auth dependency
        )
        app.include_router(virtual_structure_router, prefix="/api", dependencies=get_auth_deps())
        possible_maintenance_secret = get_config().maintenance_secret
        if (
            possible_maintenance_secret is not None
            and len(possible_maintenance_secret.get_secret_value()) > 0
        ):
            app.include_router(maintenance_router, prefix="/api", dependencies=get_auth_deps())
    if len(get_config().restrict_to_trafo_exec_service) != 0:
        app.include_router(info_router, prefix="/api")  # reachable without authorization
        app.include_router(
            restricted_transformation_router,
            prefix="/api",
            dependencies=get_auth_deps(),
        )

    return app
