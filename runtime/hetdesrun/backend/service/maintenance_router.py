import logging
import secrets
from collections.abc import Callable

from fastapi import HTTPException, Query, Response, status
from pydantic import BaseModel, Field, SecretStr

from hetdesrun.exportimport.importing import import_importables, import_transformations
from hetdesrun.exportimport.purge import (
    delete_all_and_refill,
    delete_drafts,
    delete_unused_deprecated,
    deprecate_all_but_latest_per_group,
    reset_test_wiring_to_release_wiring,
)
from hetdesrun.trafoutils.io.load import get_import_sources, load_import_sources
from hetdesrun.webservice.config import get_config
from hetdesrun.webservice.router import HandleTrailingSlashAPIRouter

logger = logging.getLogger(__name__)


class MaintenanceActionResult(BaseModel):
    success: bool = True
    error: str | None = None


class MaintenancePayload(BaseModel):
    maintenance_secret: SecretStr = Field(..., description="Required maintenance secret.")


maintenance_router = HandleTrailingSlashAPIRouter(
    prefix="/maintenance",
    tags=["maintenance"],
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Bad Request"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        status.HTTP_404_NOT_FOUND: {"description": "Not Found"},
        status.HTTP_409_CONFLICT: {"description": "Conflict"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
    },
)


def handle_maintenance_operation_request(
    maintenance_operation_name: str,
    secret_str: SecretStr,
    func: Callable,
    response: Response,
) -> MaintenanceActionResult:
    """Handle maintenance request

    func must be an ordinary function allowing for a directly_in_db keyword argument.
    maintenance_operation_name is for logging / messaging only
    """

    configured_maintenance_secret = get_config().maintenance_secret

    assert configured_maintenance_secret is not None  # for mypy # noqa: S101

    if not secrets.compare_digest(
        secret_str.get_secret_value(),
        configured_maintenance_secret.get_secret_value(),
    ):
        logger.error("maintenance secret check failed")
        raise HTTPException(
            status_code=403,
            detail={"authorization_error": "maintenance secret check failed"},
        )
    try:
        func(directly_in_db=True)
    except Exception as exc:  # noqa: BLE001
        msg = f"Exception during maintenance operation {maintenance_operation_name}:\n" + str(exc)
        logger.error(msg)
        response.status_code = 500
        return MaintenanceActionResult(success=False, error=msg)
    return MaintenanceActionResult()


@maintenance_router.post(
    "/reset_test_wiring_to_release_wiring",
    response_model=MaintenanceActionResult,
    summary="Reset test wiring of released transformation revision to their release wiring",
)
async def maintenance_reset_test_wiring_to_release_wiring(
    maintenance_payload: MaintenancePayload, response: Response
) -> MaintenanceActionResult:
    """Reset the current test wiring to the stored release wiring

    This affects released and deprecated transformation revisions.

    **Warning**: This resets test wirings. We recommend to backup, e.g.
    exporting / getting all transformation revisions before using this action!
    """
    return handle_maintenance_operation_request(
        "reset_test_wiring_to_release_wiring",
        maintenance_payload.maintenance_secret,
        reset_test_wiring_to_release_wiring,
        response=response,
    )


@maintenance_router.post(
    "/deprecate_all_but_latest_per_group",
    response_model=MaintenanceActionResult,
    summary="Deprecate old transformation revision and keep only latest",
)
async def maintenance_deprecate_all_but_latest_per_group(
    maintenance_payload: MaintenancePayload, response: Response
) -> MaintenanceActionResult:
    """Deprecate old transformation revision and keep only latest

    A transformation revision is considered "old" if it is released and there is a newer
    released transformation revision (i.e. newer release timestamp) in the same group.

    Note that this has nothing to to with version tags or any versioning scheme!

    **Warning**: This deprecates transformation revisions. We recommend to backup, e.g.
    exporting / getting all transformation revisions before using this action!
    """
    return handle_maintenance_operation_request(
        "deprecate_all_but_latest_per_group",
        maintenance_payload.maintenance_secret,
        deprecate_all_but_latest_per_group,
        response=response,
    )


@maintenance_router.post(
    "/delete_drafts",
    response_model=MaintenanceActionResult,
    summary="delete all transformation revisions with state DRAFT",
)
async def maintenance_delete_drafts(
    maintenance_payload: MaintenancePayload, response: Response
) -> MaintenanceActionResult:
    """Delete all transformation revisions with state DRAFT

    **Warning**: This irrevocably deletes transformation revisions. We recommend to backup, e.g.
    exporting / getting all transformation revisions before using this action!
    """
    return handle_maintenance_operation_request(
        "delete_drafts",
        maintenance_payload.maintenance_secret,
        delete_drafts,
        response=response,
    )


@maintenance_router.post(
    "/delete_unused_deprecated",
    response_model=MaintenanceActionResult,
    summary="delete all unused deprecated transformation revisions",
)
async def maintenance_delete_unused_deprecated(
    maintenance_payload: MaintenancePayload, response: Response
) -> MaintenanceActionResult:
    """Delete all unused deprecated transformation revisions

    "Unused" deprecated transformation revisions are those that are either not used in any workflow
    or only in workflows that themselves are deprecated (and hence will be deleted as well).

    This handles nesting, i.e. a deprecated trafo rev will not be deleted if it is used indirectly
    across multiple nesting levels in a workflow which is not deprecated.

    **Warning**: This irrevocably deletes transformation revisions. We recommend to backup, e.g.
    exporting / getting all transformation revisions before using this action!
    """
    return handle_maintenance_operation_request(
        "delete_unused_deprecated",
        maintenance_payload.maintenance_secret,
        delete_unused_deprecated,
        response=response,
    )


@maintenance_router.post(
    "/purge",
    response_model=MaintenanceActionResult,
    summary="purge and deploy base trafos afterwards",
)
async def maintenance_purge(
    maintenance_payload: MaintenancePayload, response: Response
) -> MaintenanceActionResult:
    """Purge and reinstall base components/workflows

    This deletes all transformation revisions and afterwards deploys the base
    components and workflows present in the running backend instance's image at the
    default path.

    **Warning**: This irrevocably deletes transformation revisions. We recommend to backup, e.g.
    exporting / getting all transformation revisions before using this action!
    """
    return handle_maintenance_operation_request(
        "purge",
        maintenance_payload.maintenance_secret,
        delete_all_and_refill,
        response=response,
    )


@maintenance_router.post(
    "/deploy_base_trafos",
    response_model=MaintenanceActionResult,
    summary="Deploy base trafos from the running backend",
)
async def deploy_base_trafos(
    maintenance_payload: MaintenancePayload,
    response: Response,
    allow_overwrite_released: bool = Query(
        False,
        description=(
            "Whether released trafo revisions are overwritten."
            " If inactive changes/improvements on existing trafo revisions will not"
            " be deployed. If active this may negatively affect existing worklows"
            " if changes introduce bugs and in particular undermines reproducibility!"
        ),
    ),
    update_component_code: bool = Query(
        False,
        description=(
            "Whether autogenerated component code will be automatically "
            "updated during import. This may introduce bugs and negatively affect"
            " reproducibility."
        ),
    ),
) -> MaintenanceActionResult:
    """Deploy base trafos from the running backend

    This deploys base trafos from the running backend, i.e. from its
    ./transformations directory. This is similar to what autodeploy does
    at the first start, but allows to trigger this manually, e.g. when new
    or improved base trafos arrive in a new backend version.

    As already said, this is useful after updating the backend/runtime to a newer
    version which comes with new or improved base transformations, since
    those won't be deployed automatically even with active autodeploy if the
    HD_BACKEND_PRESERVE_DB_ON_AUTODEPLOY is true (see
    https://github.com/hetida/hetida-designer/blob/release/docs/base_component_deployment.md
    ).

    Activating the available query parameter options can affect existing workflow
    execution and reproducibility if trafo revisions used in them are overwritten
    or changed. Please double-check whether this is what you want!
    """

    def handle_base_deployment(directly_in_db: bool = True) -> None:
        import_transformations(
            "./transformations/",
            directly_into_db=directly_in_db,
            allow_overwrite_released=allow_overwrite_released,
            update_component_code=update_component_code,
        )

    return handle_maintenance_operation_request(
        "deploy_base_trafos",
        maintenance_payload.maintenance_secret,
        handle_base_deployment,
        response=response,
    )


def autoimport(directly_in_db: bool = True) -> None:  # noqa: ARG001
    autoimport_dir = get_config().autoimport_directory
    logger.info("Trying autoimport from %s", autoimport_dir)

    import_importables(load_import_sources(get_import_sources(autoimport_dir)))
    logger.info("Finished autoimport")


@maintenance_router.post(
    "/trigger_automimport",
    response_model=MaintenanceActionResult,
    summary="Trigger autoimport",
)
async def trigger_autoimport(
    maintenance_payload: MaintenancePayload,
    response: Response,
) -> MaintenanceActionResult:
    """Triggers autoimport from the configured autoimport directory

    This uses the autoimport system which allows to provide config files
    containing import options and filters. The autoimport directory is
    configured via the HD_BACKEND_AUTOIMPORT_DIRECTORY environment variable.
    """
    return handle_maintenance_operation_request(
        "trigger_automimport",
        maintenance_payload.maintenance_secret,
        autoimport,
        response=response,
    )
