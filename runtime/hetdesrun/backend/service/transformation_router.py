import datetime
import json
import logging
from copy import deepcopy
from typing import Annotated, Any
from uuid import UUID

import httpx
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Path,
    Query,
    Request,
    Response,
    status,
)
from fastapi.responses import HTMLResponse
from pydantic import HttpUrl, StrictInt, StrictStr

from hetdesrun.backend.execution import (
    TrafoExecutionInputValidationError,
    TrafoExecutionNotFoundError,
    TrafoExecutionResultValidationError,
    TrafoExecutionRuntimeConnectionError,
    perf_measured_execute_trafo_rev,
)
from hetdesrun.backend.models.info import ExecutionResponseFrontendDto
from hetdesrun.backend.service.dashboarding import (
    OverrideMode,
    calculate_timerange_timestamps,
    generate_dashboard_html,
    generate_login_dashboard_stub,
    override_timestamps_in_wiring,
)
from hetdesrun.backend.service.dashboarding_utils import (
    DashboardQueryParamValidationError,
    update_wiring_from_query_parameters,
)
from hetdesrun.component.code import expand_code, update_code
from hetdesrun.exportimport.importing import (
    TrafoUpdateProcessSummary,
    UpdateProcessStatus,
    import_importable,
)
from hetdesrun.models.code import NonEmptyValidStr, ValidStr
from hetdesrun.models.execution import ExecByIdInput, ExecLatestByGroupIdInput
from hetdesrun.models.wiring import GridstackItemPositioning, WorkflowWiring
from hetdesrun.persistence.dbservice.exceptions import DBIntegrityError, DBNotFoundError
from hetdesrun.persistence.dbservice.revision import (
    delete_single_transformation_revision,
    get_latest_revision_id,
    get_multiple_transformation_revisions,
    read_single_transformation_revision,
    store_single_transformation_revision,
    update_or_create_single_transformation_revision,
)
from hetdesrun.persistence.models.exceptions import ModelConstraintViolation
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.trafoutils.filter.params import FilterParams
from hetdesrun.trafoutils.io.load import (
    ComponentCodeImportError,
    Importable,
    ImportSourceConfig,
    MultipleTrafosUpdateConfig,
    transformation_revision_from_python_code,
)
from hetdesrun.utils import State, Type
from hetdesrun.webservice.auth_dependency import (
    get_auth_headers,
    is_authenticated_check_no_abort,
)
from hetdesrun.webservice.auth_outgoing import ServiceAuthenticationError
from hetdesrun.webservice.config import get_config
from hetdesrun.webservice.router import HandleTrailingSlashAPIRouter

logger = logging.getLogger(__name__)


transformation_router = HandleTrailingSlashAPIRouter(
    prefix="/transformations",
    tags=["transformations"],
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Bad Request"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        status.HTTP_404_NOT_FOUND: {"description": "Not Found"},
        status.HTTP_409_CONFLICT: {"description": "Conflict"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
    },
)


dashboard_router = HandleTrailingSlashAPIRouter(
    prefix="/transformations",
    tags=["transformations"],
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Bad Request"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        status.HTTP_404_NOT_FOUND: {"description": "Not Found"},
        status.HTTP_409_CONFLICT: {"description": "Conflict"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
    },
)


@transformation_router.post(
    "",
    response_model=TransformationRevision,
    response_model_exclude_none=True,  # needed because:
    # frontend handles attributes with value null in a different way than missing attributes
    summary="Creates a transformation revision.",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {"description": "Successfully created the transformation revision"}
    },
)
async def create_transformation_revision(
    transformation_revision: TransformationRevision,
) -> TransformationRevision:
    """Store a transformation revision in the data base."""
    logger.info("create transformation revision %s", transformation_revision.id)

    if transformation_revision.type == Type.COMPONENT:
        logger.debug("transformation revision has type %s", Type.COMPONENT)
        transformation_revision.content = update_code(transformation_revision)
        logger.debug("generated code:\n%s", transformation_revision.content)

    try:
        store_single_transformation_revision(transformation_revision)
        logger.info("created transformation revision")
    except DBIntegrityError as err:
        msg = f"Could not store transformation revision {transformation_revision.id}:\n{str(err)}"
        logger.error(msg)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=msg) from err

    try:
        persisted_transformation_revision = read_single_transformation_revision(
            transformation_revision.id
        )
    except DBNotFoundError as err:
        msg = f"Could not find transformation revision {transformation_revision.id}:\n{str(err)}"
        logger.error(msg)
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=msg) from err

    logger.debug(persisted_transformation_revision.json())

    return persisted_transformation_revision


def change_code(
    tr: TransformationRevision,
    expand_component_code: bool = False,
    update_component_code: bool = False,
) -> str:
    """Handle desired code changes"""
    tr_copy = tr.copy(deep=True)
    assert isinstance(tr_copy.content, str)  # for mypy # noqa: S101

    if update_component_code:
        tr_copy.content = update_code(tr_copy)
    if expand_component_code:
        tr_copy.content = expand_code(tr_copy)

    return tr_copy.content


@transformation_router.get(
    "",
    response_model=list[TransformationRevision | str],
    response_model_exclude_none=True,  # needed because:
    # frontend handles attributes with value null in a different way than missing attributes
    summary="Returns combined list of all transformation revisions (components and workflows)",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "Successfully got all transformation revisions"}
    },
)
async def get_all_transformation_revisions(
    type: Type  # noqa: A002
    | None = Query(
        None,
        description="Filter for specified type.",
    ),
    state: State | None = Query(
        None,
        description="Filter for specified state.",
    ),
    categories: list[ValidStr] | None = Query(
        None, description="Filter for specified list of categories.", alias="category"
    ),
    category_prefix: ValidStr | None = Query(
        None,
        description="Category prefix that must be matched exactly (case-sensitive).",
    ),
    revision_group_id: UUID | None = Query(
        None, description="Filter for specified revision group id."
    ),
    ids: list[UUID] | None = Query(
        None, description="Filter for specified list of ids.", alias="id"
    ),
    names: list[NonEmptyValidStr] | None = Query(
        None, description=("Filter for specified list of names."), alias="name"
    ),
    include_dependencies: bool = Query(
        False,
        description=(
            "Set to True to additionally get those transformation revisions "
            "that the selected/filtered ones depend on."
        ),
    ),
    include_deprecated: bool = Query(
        True,
        description=(
            "Set to False to omit transformation revisions with state DISABLED "
            "this will not affect included dependent transformation revisions."
        ),
    ),
    unused: bool = Query(
        False,
        description=(
            "Set to True to obtain only those transformation revisions that are "
            "not contained in workflows that do not have the state DISABLED."
        ),
    ),
    components_as_code: bool = Query(
        False,
        description=(
            "Set to True to obtain transformation revisions of type COMPOPNENT "
            "as a string of their python code instead of as JSON."
        ),
    ),
    expand_component_code: bool = Query(
        False,
        description=(
            "Set to True to add the documentation as module docstring and "
            "the test wiring as dictionary to component code."
            ""
            "Note: "
            "Enabling this option leads to changed component code in the output of this request."
            " In particular the component code hash changes which in turn is used in the Python"
            " import module path. This affects serialized objects (e.g. trained models) based on"
            " this component: They cannot be deserialized in runtime containers / processes where"
            " the old component is not present anymore. When putting such components to hetida"
            " designer instances it is necessary to recreate such serialized objects."
        ),
    ),
    update_component_code: bool = Query(
        False,
        description=(
            "Set to true to update the component code, in particular the main function "
            "definition and the COMPONENT_INFO in the response of this. For example this "
            "can be used to update old, deprecated and since 0.9.5 from code non-importable"
            " @register decorator style components to the new more flexible  components with"
            " a COMPONENT_INFO dict."
            ""
            "Note: "
            "Enabling this option leads to changed component code in the output of this request."
            " In particular the component code hash changes which in turn is used in the Python"
            " import module path. This affects serialized objects (e.g. trained models) based on"
            " this component: They cannot be deserialized in runtime containers / processes where"
            " the old component is not present anymore. When putting such components to hetida"
            " designer instances it is necessary to recreate such serialized objects."
        ),
    ),
    strip_wirings: bool = Query(
        False,
        description=(
            "Whether test wirings should be completely removed and be replaced"
            " with an empty test wiring."
            " Note that expand_component_code needs to be true for this to affect"
            " the test wiring stored in the component code. In particular if component_as_code"
            " is true."
        ),
    ),
    strip_wirings_with_adapter_ids: set[StrictInt | StrictStr] = Query(
        set(),
        description="Remove all input wirings and output wirings from the trafo's"
        " test wiring with this adapter id. Can be provided multiple times."
        " In contrast to strip_wirings this allows to"
        " fine-granulary exclude only those parts of test wirings corresponding to"
        " adapters which are not present."
        " Note that expand_component_code needs to be true for this to affect"
        " the test wiring stored in the component code. In particular if component_as_code"
        " is true.",
        alias="strip_wirings_with_adapter_id",
    ),
    keep_only_wirings_with_adapter_ids: set[StrictInt | StrictStr] = Query(
        set(),
        description="In each test wiring keep only the input wirings and output wirings"
        " with the given adapter id. Can be set multiple times and then only wirings with"
        " any of the given ids are kept. If not set, this has no effect (use strip_wirings"
        " if you actually want to remove all wirings in the test wiring). A typical case"
        " is when you want to only keep the wirings with adapter id direct_provisioning,"
        " i.e. manual inputs of the test wiring, in order to remove dependencies from"
        " external adapters not present on the target hetida designer installation."
        " Note that expand_component_code needs to be true for this to affect"
        " the test wiring stored in the component code. In particular if component_as_code"
        " is true.",
        alias="keep_only_wirings_with_adapter_id",
    ),
    strip_release_wirings: bool = Query(
        False,
        description=(
            "Whether release wirings should be completely removed and be replaced"
            " with null."
            " Note that expand_component_code needs to be true for this to affect"
            " the release wiring stored in the component code. In particular if component_as_code"
            " is true."
        ),
    ),
    strip_release_wirings_with_adapter_ids: set[StrictInt | StrictStr] = Query(
        set(),
        description="Remove all input wirings and output wirings from the trafo's"
        " release wiring with this adapter id. Can be provided multiple times."
        " In contrast to strip_release_wirings this allows to"
        " fine-granulary exclude only those parts of release wirings corresponding to"
        " adapters which are not present."
        " Note that expand_component_code needs to be true for this to affect"
        " the release wiring stored in the component code. In particular if component_as_code"
        " is true.",
        alias="strip_release_wirings_with_adapter_id",
    ),
    keep_only_release_wirings_with_adapter_ids: set[StrictInt | StrictStr] = Query(
        set(),
        description="In each release wiring keep only the input wirings and output wirings"
        " with the given adapter id. Can be set multiple times and then only wirings with"
        " any of the given ids are kept. If not set, this has no effect (use strip_release_wirings"
        " if you actually want to remove all wirings in the release wiring). A typical case"
        " is when you want to only keep the wirings with adapter id direct_provisioning,"
        " i.e. manual inputs of the release wiring, in order to remove dependencies from"
        " external adapters not present on the target hetida designer installation."
        " Note that expand_component_code needs to be true for this to affect"
        " the release wiring stored in the component code. In particular if component_as_code"
        " is true.",
        alias="keep_only_wirings_with_adapter_id",
    ),
) -> list[TransformationRevision | str]:
    """Get all transformation revisions from the data base.

    Used by frontend for initial loading of all transformations to populate the sidebar
    and to export selected transformation revisions.

    The parameters filtering the transformation revisions are logically combined as follows
    * OR for the same filter, e.g. providing two ids will yield both trafos.
    * AND between different filters.
    """

    filter_params = FilterParams(
        type=type,
        state=state,
        categories=categories,
        category_prefix=category_prefix,
        revision_group_id=revision_group_id,
        ids=ids,
        names=names,
        include_dependencies=include_dependencies,
        include_deprecated=include_deprecated,
        unused=unused,
    )

    logger.info("get all transformation revisions with %s", repr(filter_params))

    try:
        transformation_revision_list = get_multiple_transformation_revisions(filter_params)
    except DBIntegrityError as err:
        msg = f"At least one entry in the DB is no valid transformation revision:\n{str(err)}"
        logger.error(msg)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=msg) from err

    for tr in transformation_revision_list:
        tr.strip_wirings(
            strip_wiring=strip_wirings,
            strip_wirings_with_adapter_ids=strip_wirings_with_adapter_ids,
            keep_only_wirings_with_adapter_ids=keep_only_wirings_with_adapter_ids,
            strip_release_wiring=strip_release_wirings,
            strip_release_wirings_with_adapter_ids=strip_release_wirings_with_adapter_ids,
            keep_only_release_wirings_with_adapter_ids=keep_only_release_wirings_with_adapter_ids,
        )

    code_list: list[str] = []
    component_indices: list[int] = []

    component_indices = [
        index for index, tr in enumerate(transformation_revision_list) if tr.type == Type.COMPONENT
    ]
    component_indices.sort(reverse=True)

    if components_as_code:
        for index in component_indices:
            component_tr = transformation_revision_list.pop(index)
            code_list.append(
                change_code(component_tr, expand_component_code, update_component_code)
            )
    else:
        for index in component_indices:
            component_tr = transformation_revision_list[index]
            component_tr.content = change_code(
                component_tr, expand_component_code, update_component_code
            )

    return transformation_revision_list + code_list


@transformation_router.get(
    "/{id}",
    response_model=TransformationRevision,
    response_model_exclude_none=True,  # needed because:
    # frontend handles attributes with value null in a different way than missing attributes
    summary="Returns the transformation revision with the given id.",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_200_OK: {"description": "Successfully got the transformation revision"}},
)
async def get_transformation_revision_by_id(
    id: UUID = Path(  # noqa: A002
        ...,
        examples=[UUID("123e4567-e89b-12d3-a456-426614174000")],
    ),
) -> TransformationRevision:
    logger.info("get transformation revision %s", id)

    try:
        transformation_revision = read_single_transformation_revision(id)
        logger.info("found transformation revision with id %s", id)
    except DBNotFoundError as err:
        msg = f"Could not find transformation revision {id}:\n{str(err)}"
        logger.error(msg)
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=msg) from err

    logger.debug(transformation_revision.json())

    return transformation_revision


@transformation_router.put(
    "",
    status_code=status.HTTP_207_MULTI_STATUS,
    summary="Update (import) a list of transformation revisions",
    responses={
        status.HTTP_207_MULTI_STATUS: {
            "description": (
                "Processed request to update multiple transformation revisions. "
                "See response for details."
            )
        }
    },
)
async def update_transformation_revisions(
    updated_transformation_revisions_and_code_strings: list[TransformationRevision | str],
    response: Response,
    type: Type  # noqa: A002
    | None = Query(
        None,
        description="Filter for specified type.",
    ),
    state: State | None = Query(
        None,
        description="Filter for specified state.",
    ),
    categories: list[ValidStr] | None = Query(
        None, description="Filter for specified list of categories.", alias="category"
    ),
    category_prefix: str | None = Query(
        None,
        description="Category prefix that must be matched exactly (case-sensitive).",
    ),
    revision_group_id: UUID | None = Query(
        None, description="Filter for specified revision group id."
    ),
    ids: list[UUID] | None = Query(
        None, description="Filter for specified list of ids.", alias="id"
    ),
    names: list[NonEmptyValidStr] | None = Query(
        None, description=("Filter for specified list of names."), alias="name"
    ),
    release_drafts: bool = Query(
        False, description="If true, all trafos in draft state will be released"
    ),
    include_deprecated: bool = Query(
        True,
        description=(
            "Set to False to omit transformation revisions with state DISABLED "
            "this will not affect included dependent transformation revisions"
        ),
    ),
    include_dependencies: bool = Query(
        True,
        description=(
            "Set to True to additionally import those transformation revisions "
            "of the provided trafos that the selected/filtered ones depend on."
        ),
    ),
    allow_overwrite_released: bool = Query(False, description="Only set to True for deployment."),
    update_component_code: bool = Query(True, description="Only set to False for deployment."),
    strip_wirings: bool = Query(
        False,
        description=(
            "Whether test wirings should be removed before importing."
            "This can be necessary if an adapter used in a test wiring is not "
            "available on this system."
        ),
    ),
    strip_wirings_with_adapter_ids: set[StrictInt | StrictStr] = Query(
        set(),
        description="Remove all input wirings and output wirings from the trafo's"
        " test wiring with this adapter id. Can be provided multiple times."
        " In contrast to strip_wirings this allows to"
        " fine-granulary exclude only those parts of test wirings corresponding to"
        " adapters which are not present.",
        alias="strip_wirings_with_adapter_id",
    ),
    keep_only_wirings_with_adapter_ids: set[StrictInt | StrictStr] = Query(
        set(),
        description="In each test wiring keep only the input wirings and output wirings"
        " with the given adapter id. Can be set multiple times and then only wirings with"
        " any of the given ids are kept. If not set, this has no effect (use strip_wirings"
        " if you actually want to remove all wirings in the test wiring). A typical case"
        " is when you want to only keep the wirings with adapter id direct_provisioning,"
        " i.e. manual inputs of the test wiring, in order to remove dependencies from"
        " external adapters not present on the target hetida designer installation.",
        alias="keep_only_wirings_with_adapter_id",
    ),
    strip_release_wirings: bool = Query(
        False,
        description=(
            "Whether release wirings should be removed before importing."
            "This can be necessary if an adapter used in a release wiring is not "
            "available on this system."
        ),
    ),
    strip_release_wirings_with_adapter_ids: set[StrictInt | StrictStr] = Query(
        set(),
        description="Remove all input wirings and output wirings from the trafo's"
        " release wiring with this adapter id. Can be provided multiple times."
        " In contrast to strip_release_wirings this allows to"
        " fine-granulary exclude only those parts of release wirings corresponding to"
        " adapters which are not present.",
        alias="strip_release_wirings_with_adapter_id",
    ),
    keep_only_release_wirings_with_adapter_ids: set[StrictInt | StrictStr] = Query(
        set(),
        description="In each release wiring keep only the input wirings and output wirings"
        " with the given adapter id. Can be set multiple times and then only wirings with"
        " any of the given ids are kept. If not set, this has no effect (use strip_release_wirings"
        " if you actually want to remove all wirings in the release wiring). A typical case"
        " is when you want to only keep the wirings with adapter id direct_provisioning,"
        " i.e. manual inputs of the release wiring, in order to remove dependencies from"
        " external adapters not present on the target hetida designer installation.",
        alias="keep_only_release_wirings_with_adapter_id",
    ),
    abort_on_error: bool = Query(
        False,
        description=(
            "If updating/creating fails for some trafo revisions and this setting is true,"
            " no attempt will be made to update/create the remaining trafo revs."
            " Note that the order in which updating/creating happens may differ from"
            " the ordering of the provided list since they are ordered by dependency"
            " relation before trying to process them. So it may be difficult to determine."
            " which trafos have been skipped / are missing and which have been successfully"
            " processed. Note that already processed actions will not be reversed."
        ),
    ),
    deprecate_older_revisions: bool = Query(
        False,
        description=(
            "Whether older revisions in the same trafo revision group should be deprecated."
            " If this is True, this is done for every revision group for which any trafo"
            " rev passes the filters and even for those that are included as dependencies"
            " via the include_dependencies property of the filter params!"
            " Note that this might not be done if abort_on_error is True and there is"
            " an error anywhere."
        ),
    ),
) -> dict[UUID | str, TrafoUpdateProcessSummary]:
    """Update/store multiple transformation revisions

    This updates or creates the given transformation revisions. Automatically
    determines correct order (by dependency / nesting) so that depending trafo
    revisions can be provided in arbitrary order to this endpoint.

    Returns detailed info about success/failure for each transformation revision.

    This endpoint can be used to import related sets of transformation revisions.
    Such a set does not have to be closed under dependency relation, e.g. elements
    of it can refer base components.

    This endpoint allows for filltering transformation revisions like the corresponding
    get endpoint. This means of all provided trafos in the payload only those matching the
    filter parameters will be updated/stored. Transformation revisions that where excluded
    will be marked as ignored in the response.

    The parameters filtering the transformation revisions are logically combined as follows
    * OR for the same filter, e.g. providing two ids will store both trafos.
    * AND between different filters.
    """
    filter_params = FilterParams(
        type=type,
        state=state,
        categories=categories,
        category_prefix=category_prefix,
        revision_group_id=revision_group_id,
        ids=ids,
        names=names,
        include_deprecated=include_deprecated,
        include_dependencies=include_dependencies,
    )

    multi_import_config = MultipleTrafosUpdateConfig(
        allow_overwrite_released=allow_overwrite_released,
        update_component_code=update_component_code,
        strip_wirings=strip_wirings,
        strip_wirings_with_adapter_ids=strip_wirings_with_adapter_ids,
        keep_only_wirings_with_adapter_ids=keep_only_wirings_with_adapter_ids,
        strip_release_wiring=strip_release_wirings,
        strip_release_wirings_with_adapter_ids=strip_release_wirings_with_adapter_ids,
        keep_only_release_wirings_with_adapter_ids=keep_only_release_wirings_with_adapter_ids,
        abort_on_error=abort_on_error,
        deprecate_older_revisions=deprecate_older_revisions,
    )

    updated_transformation_revisions: list[TransformationRevision] = []
    updated_component_code_strings: list[str] = []
    for item in updated_transformation_revisions_and_code_strings:
        if isinstance(item, TransformationRevision):
            updated_transformation_revisions.append(item)
        else:
            updated_component_code_strings.append(item)

    broken_component_codes: list[tuple[str, str]] = []
    for ccs in updated_component_code_strings:
        try:
            tr = transformation_revision_from_python_code(ccs)
        except ComponentCodeImportError as error:
            broken_component_codes.append((str(error), ccs))
        else:
            updated_transformation_revisions.append(tr)

    if release_drafts:
        for trafo in updated_transformation_revisions:
            if trafo.state is State.DRAFT:
                trafo.release()

    importable = Importable(
        transformation_revisions=updated_transformation_revisions,
        import_config=ImportSourceConfig(
            filter_params=filter_params, update_config=multi_import_config
        ),
    )

    success_per_trafo = import_importable(importable)
    for msg, ccs in broken_component_codes:
        success_per_trafo[ccs] = TrafoUpdateProcessSummary(
            status=UpdateProcessStatus.FAILED,
            msg=msg,
            name="UNKNOWN",
            version_tag="UNKNOWN",
        )

    response.status_code = status.HTTP_207_MULTI_STATUS

    return success_per_trafo


@transformation_router.put(
    "/{id}",
    response_model=TransformationRevision,
    response_model_exclude_none=True,  # needed because:
    # frontend handles attributes with value null in a different way than missing attributes
    summary="Updates a transformation revision.",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "description": "Successfully updated the transformation revision"
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Id from path does not match id from object in request body"
        },
        status.HTTP_409_CONFLICT: {
            "description": "DB entry is not modifiable due to status or non-matching types"
        },
    },
)
async def update_transformation_revision(
    id: UUID,  # noqa: A002
    updated_transformation_revision: TransformationRevision,
    allow_overwrite_released: bool = Query(False, description="Only set to True for deployment"),
    update_component_code: bool = Query(True, description="Only set to False for deployment"),
    strip_wiring: bool = Query(False, description="Set to True to discard test wiring"),
) -> TransformationRevision:
    """Update or store a transformation revision in the database.

    If no DB entry with the provided id is found, it will be created.

    Updating a transformation revision is only possible if it is in state DRAFT
    or to change the state from RELEASED to DISABLED.

    Unset attributes of the json sent in the request body will be set to default values,
    possibly changing the attribute saved in the DB.
    """

    logger.info("update transformation revision %s", id)

    if id != updated_transformation_revision.id:
        msg = (
            f"The id {id} does not match the id of the provided "
            f"transformation revision DTO {updated_transformation_revision.id}"
        )
        logger.error(msg)
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=msg)

    try:
        persisted_transformation_revision = update_or_create_single_transformation_revision(
            updated_transformation_revision,
            allow_overwrite_released=allow_overwrite_released,
            update_component_code=update_component_code,
            strip_wiring=strip_wiring,
        )
        logger.info("updated transformation revision %s", id)
    except DBIntegrityError as err:
        msg = f"Integrity error in DB when trying to access entry for id {id}:\n{str(err)}"
        logger.error(msg)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=msg) from err
    except DBNotFoundError as err:
        msg = f"Not found error in DB when trying to access entry for id {id}:\n{str(err)}"
        logger.error(msg)
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=msg) from err
    except ModelConstraintViolation as err:
        msg = f"Update forbidden for transformation with id {id}:\n{str(err)}s"
        logger.error(msg)
        raise HTTPException(status.HTTP_409_CONFLICT, detail=msg) from err

    logger.debug(persisted_transformation_revision.json())

    return persisted_transformation_revision


@transformation_router.delete(
    "/{id}",
    summary="Deletes a transformation revision.",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Successfully deleted the transformation revision"
        },
        status.HTTP_409_CONFLICT: {
            "description": "Transformation revision is already released or deprecated"
        },
    },
)
async def delete_transformation_revision(
    id: UUID,  # noqa: A002
    ignore_state: bool = Query(
        False,
        description=(
            "Set to true to enable deletion of released and deprecated transformation revisions"
        ),
    ),
) -> None:
    """Delete a transformation revision from the data base.

    Deleting a transformation revision is only possible if it is in state DRAFT.
    """

    logger.info("delete transformation revision %s", id)

    try:
        delete_single_transformation_revision(id, ignore_state=ignore_state)
        logger.info("deleted transformation revision %s", id)

    except DBNotFoundError as err:
        msg = f"Could not find transformation revision {id}:\n{str(err)}"
        logger.error(msg)
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=msg) from err

    except (ModelConstraintViolation, DBIntegrityError) as err:
        msg = f"Could not delete transformation revision {id}:\n{str(err)}"
        logger.error(msg)
        raise HTTPException(status.HTTP_409_CONFLICT, detail=msg) from err


async def handle_trafo_revision_execution_request(
    exec_by_id: ExecByIdInput,
) -> ExecutionResponseFrontendDto:
    try:
        exec_response = await perf_measured_execute_trafo_rev(exec_by_id)

    except TrafoExecutionInputValidationError as err:
        msg = f"Could not validate execution input\n{exec_by_id.json(indent=2)}:\n{str(err)}"
        logger.error(msg)
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=msg) from err

    except TrafoExecutionNotFoundError as err:
        msg = f"Could not find transformation revision {exec_by_id.id}:\n{str(err)}"
        logger.error(msg)
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=msg) from err

    except TrafoExecutionRuntimeConnectionError as err:
        msg = f"Could not connect to runtime to execute transformation {exec_by_id.id}:\n{str(err)}"
        logger.error(msg)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=msg) from err

    except TrafoExecutionResultValidationError as err:
        msg = f"Could not validate execution result for transformation {exec_by_id.id}:\n{str(err)}"
        logger.error(msg)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=msg) from err

    return exec_response


@transformation_router.post(
    "/execute",
    response_model=ExecutionResponseFrontendDto,
    summary="Executes a transformation revision",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "Successfully executed the transformation revision"}
    },
)
async def execute_transformation_revision_endpoint(
    exec_by_id: ExecByIdInput,
) -> ExecutionResponseFrontendDto:
    """Execute a transformation revision.

    The transformation will be loaded from the DB and executed with the wiring sent in the request
    body.

    The test wiring will not be updated.
    """
    return await handle_trafo_revision_execution_request(exec_by_id)


callback_router = APIRouter()


@callback_router.post("{$callback_url}", response_model=ExecutionResponseFrontendDto)
def receive_execution_response(
    body: ExecutionResponseFrontendDto,  # noqa: ARG001
) -> None:
    pass


async def send_result_to_callback_url(
    callback_url: HttpUrl, result: ExecutionResponseFrontendDto
) -> None:
    try:
        headers = await get_auth_headers(external=True)
    except ServiceAuthenticationError as e:
        msg = (
            "Failed to get auth headers for sending result to callback url."
            f" Error was:\n{str(e)}"
        )
        logger.error(msg)

    async with httpx.AsyncClient(
        verify=get_config().hd_backend_verify_certs,
        timeout=get_config().external_request_timeout,
    ) as client:
        try:
            await client.post(
                callback_url,
                headers=headers,
                json=json.loads(result.json()),  # TODO: avoid double serialization.
                # see https://github.com/samuelcolvin/pydantic/issues/1409 and
                # https://github.com/samuelcolvin/pydantic/issues/1409#issuecomment-877175194
            )
        except httpx.HTTPError as http_err:
            # handles both request errors (connection problems)
            # and 4xx and 5xx errors. See https://www.python-httpx.org/exceptions/
            msg = f"Failure connecting to callback url ({callback_url}):\n{str(http_err)}"
            logger.error(msg)
            # no re-raise reasonable, see comment in execute_and_post function


async def execute_and_post(exec_by_id: ExecByIdInput, callback_url: HttpUrl) -> None:
    # necessary general try-except block due to issue of starlette exception handler
    # overwriting uncaught exceptions https://github.com/tiangolo/fastapi/issues/2505
    try:
        try:
            result = await handle_trafo_revision_execution_request(exec_by_id)
            logger.info("Finished execution with job_id=%s", str(exec_by_id.job_id))
        except HTTPException as http_exc:
            logger.error(
                "Execution with job_id=%s as background task failed:\n%s",
                str(exec_by_id.job_id),
                str(http_exc.detail),
            )
            # no re-raise reasonable due to issue mentioned above
        else:
            await send_result_to_callback_url(callback_url, result)
            logger.info("Sent result of execution with job_id=%s", str(exec_by_id.job_id))
    except Exception as e:
        logger.error(
            "An unexpected error occurred during execution with job_id=%s as background task:\n%s",
            str(exec_by_id.job_id),
            str(e),
        )
        raise e


@transformation_router.post(
    "/execute-async",
    callbacks=callback_router.routes,
    summary="Executes a transformation revision asynchronously",
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        status.HTTP_202_ACCEPTED: {"description": "Accepted execution request"},
    },
)
async def execute_asynchronous_transformation_revision_endpoint(
    exec_by_id: ExecByIdInput,
    background_tasks: BackgroundTasks,
    callback_url: HttpUrl = Query(
        ...,
        description="If provided execute asynchronous and post response to callback_url",
    ),
) -> Any:
    """Execute a transformation revision of asynchronously.

    A valid input is accepted with a corresponding response and the execution then runs in the
    background. The result of the execution is sent to the specified callback_url.
    You should have implemented an appropriate endpoint before using this one.

    The transformation will be loaded from the DB and executed with the wiring sent in the request
    body.

    The test wiring will not be updated.
    """
    background_tasks.add_task(execute_and_post, exec_by_id, callback_url)

    return {"message": f"Execution request with job_id={exec_by_id.job_id} accepted"}


async def handle_latest_trafo_revision_execution_request(
    exec_latest_by_group_id_input: ExecLatestByGroupIdInput,
) -> ExecutionResponseFrontendDto:
    try:
        id_ = get_latest_revision_id(exec_latest_by_group_id_input.revision_group_id)
    except DBNotFoundError as err:
        msg = (
            "Could not find any transformation revision with "
            f"revision group id {exec_latest_by_group_id_input.revision_group_id}:\n{str(err)}"
        )
        logger.error(msg)
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=msg) from err

    exec_by_id_input = exec_latest_by_group_id_input.to_exec_by_id(id_)

    return await handle_trafo_revision_execution_request(exec_by_id_input)


@transformation_router.post(
    "/execute-latest",
    response_model=ExecutionResponseFrontendDto,
    summary="Executes the latest transformation revision of a revision group",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Successfully executed the latest transformation revision"
        }
    },
)
async def execute_latest_transformation_revision_endpoint(
    exec_latest_by_group_id_input: ExecLatestByGroupIdInput,
) -> ExecutionResponseFrontendDto:
    """Execute the latest transformation revision of a revision group.

    WARNING: Even when the input is not changed, the execution response might change if a new latest
    transformation revision exists.

    WARNING: The inputs and outputs may be different for different revisions. In such a case,
    calling this endpoint with the same payload as before will not work, but will result in errors.

    The latest transformation will be determined by the released_timestamp of the released revisions
    of the revision group which are stored in the database.

    This transformation will be loaded from the DB and executed with the wiring sent in the request
    body.

    The test wiring will not be updated.
    """

    return await handle_latest_trafo_revision_execution_request(exec_latest_by_group_id_input)


async def execute_latest_and_post(
    exec_latest_by_group_id_input: ExecLatestByGroupIdInput, callback_url: HttpUrl
) -> None:
    # necessary general try-except block due to issue of starlette exception handler
    # overwriting uncaught exceptions https://github.com/tiangolo/fastapi/issues/2505
    try:
        try:
            result = await handle_latest_trafo_revision_execution_request(
                exec_latest_by_group_id_input
            )
            logger.info(
                "Finished execution with job_id=%s",
                str(exec_latest_by_group_id_input.job_id),
            )
        except HTTPException as http_exc:
            logger.error(
                "Execution with job_id=%s as background task failed:\n%s",
                str(exec_latest_by_group_id_input.job_id),
                str(http_exc.detail),
            )
            # no re-raise reasonable due to issue mentioned above
        else:
            await send_result_to_callback_url(callback_url, result)
            logger.info(
                "Sent result of execution with job_id %s",
                str(exec_latest_by_group_id_input.job_id),
            )
    except Exception as e:
        logger.error(
            "An unexpected error occurred during execution with job_id=%s as background task:\n%s",
            str(exec_latest_by_group_id_input.job_id),
            str(e),
        )
        raise e


@transformation_router.post(
    "/execute-latest-async",
    callbacks=callback_router.routes,
    summary="Executes the latest transformation revision of a revision group asynchronously",
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        status.HTTP_202_ACCEPTED: {
            "description": "Accepted execution request for latest revision of revision group"
        },
    },
)
async def execute_asynchronous_latest_transformation_revision_endpoint(
    exec_latest_by_group_id_input: ExecLatestByGroupIdInput,
    background_tasks: BackgroundTasks,
    callback_url: HttpUrl = Query(
        ...,
        description="If provided execute asynchronous and post response to callback_url",
    ),
) -> Any:
    """Execute the latest transformation revision of a revision group asynchronously.

    WARNING: Even when the input is not changed, the execution response might change if a new latest
    transformation revision exists.

    WARNING: The inputs and outputs may be different for different revisions. In such a case,
    calling this endpoint with the same payload as before will not work, but will result in errors.

    A valid input is accepted with a corresponding response and the execution then runs in the
    background. The result of the execution is sent to the specified callback_url.
    You should have implemented an appropriate endpoint before using this one.

    The latest transformation will be determined by the released_timestamp of the released revisions
    of the revision group which are stored in the database.

    This transformation will be loaded from the DB and executed with the wiring sent in the request
    body.

    The test wiring will not be updated.
    """
    background_tasks.add_task(execute_latest_and_post, exec_latest_by_group_id_input, callback_url)

    return {
        "message": "Execution request for latest revision with "
        f"job_id={exec_latest_by_group_id_input.job_id} accepted"
    }


@transformation_router.put(
    "/{id}/dashboard/positioning",
    summary="Update dashboard positions for a trafo revision",
    status_code=status.HTTP_200_OK,
    response_class=HTMLResponse,
    responses={
        status.HTTP_200_OK: {"description": "Successfully generated dashboard"},
    },
)
async def update_transformation_dashboard_positioning(
    gridstack_item_positions: list[GridstackItemPositioning],
    id: UUID = Path(  # noqa: A002
        ...,
        examples=[UUID("123e4567-e89b-12d3-a456-426614174000")],
    ),
) -> None:
    logger.debug("put transformation revision %s positions", id)

    try:
        transformation_revision = read_single_transformation_revision(id)
        logger.info("found transformation revision with id %s", id)
    except DBNotFoundError as err:
        msg = f"Could not find transformation revision with {id}:\n{str(err)}"
        logger.error(msg)
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=msg) from err

    transformation_revision.test_wiring.dashboard_positionings = gridstack_item_positions

    try:
        update_or_create_single_transformation_revision(
            transformation_revision,
            allow_overwrite_released=False,
            update_component_code=False,
            strip_wiring=False,
        )
    except DBIntegrityError as err:
        msg = f"Integrity error in DB when trying to access entry for id {id}:\n{str(err)}"
        logger.error(msg)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=msg) from err
    except DBNotFoundError as err:
        msg = f"Not found error in DB when trying to access entry for id {id}:\n{str(err)}"
        logger.error(msg)
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=msg) from err
    except ModelConstraintViolation as err:
        msg = f"Update forbidden for transformation with id {id}:\n{str(err)}"
        logger.error(msg)
        raise HTTPException(status.HTTP_409_CONFLICT, detail=msg) from err

    logger.debug(transformation_revision.json())


@dashboard_router.get(
    "/{id}/dashboard",
    summary="A dashboard generated from the transformation and its test wiring.",
    status_code=status.HTTP_200_OK,
    response_class=HTMLResponse,
    responses={
        status.HTTP_200_OK: {"description": "Successfully generated dashboard"},
    },
)
async def transformation_dashboard(
    request: Request,
    authenticated: Annotated[bool, Depends(is_authenticated_check_no_abort)],
    id: UUID = Path(  # noqa: A002
        ...,
        examples=[UUID("123e4567-e89b-12d3-a456-426614174000")],
    ),
    fromTimestamp: datetime.datetime | None = Query(
        None, description="Override from timestamp. Expected to be explicit UTC."
    ),
    toTimestamp: datetime.datetime | None = Query(
        None, description="Override to timestamp. Expected to be explicit UTC."
    ),
    relNow: str | None = Query(
        None,
        description=(
            'Override timerange relative to "now". '
            'E.g. "5min" describes the timerange [now - 5 minutes, now].'
        ),
    ),
    autoreload: int | None = Query(None, description=("Autoreload interval in seconds")),
    exposed_inputs: str = Query(
        "",
        description=(
            "Comma-separated list of trafo inputs,"
            " that should be exposed to be entered/changed manually in the dashboard UI"
        ),
    ),
    use_release_wiring: bool = Query(
        False,
        descripton=(
            "Whether release_wiring should be used as basis instead of the current test_wiring."
            " Using a released trafo and its fixed release wiring guarantees reproducibility of"
            " the dashboard view."
        ),
    ),
    locked: bool = Query(
        False, description="Whether dashboard elements should be draggable and resizable"
    ),
) -> str:
    """Dashboard fed by transformation revision plot outputs

    WARNING: This is an experimental feature / prototype. It may not work as
    expected.

    Generates a html page containing the result plots in movable and resizable
    rectangles, i.e. an elementary dashboard.

    The dashboard uses this same endpoint to update itself when configuration is
    changed or autoreload is active.

    Notes:
    * The dashboard uses the stored test wiring of the transformation revision. In
      particular after changing a trafo it must be executed at least once in order to
      have a working test wiring as basis for the dashboard. Otherwise dashboarding will
      fail to generate a working dashboard.
    * Timeranges of the wiring can be overriden from the dashboard UI. For every other
      aspect of the test wiring, the test wiring itself needs to be adapted by other means
      (usually by executing the trafo from inside the designer UI)
    * Positioning / Layout of the dashboard is automatically stored (autosave) as part of
      the test wiring
    * Timerange overrides / selections can be stored by copying the resulting URL.
    """

    if not authenticated:
        logger.debug("Not authenticated. Providing Login page instead.")
        return generate_login_dashboard_stub()

    # Validate query params
    if int(fromTimestamp is None) + int(toTimestamp is None) == 1:
        msg = "Either none or both of fromTimestamp and toTimestamp must be set."
        logger.error(msg)
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=msg)

    if fromTimestamp is not None and toTimestamp is not None and fromTimestamp > toTimestamp:
        msg = "fromTimestamp must be <= toTimestamp"
        logger.error(msg)
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=msg)

    if relNow is not None and fromTimestamp is not None:
        msg = "Cannot both specify absolute and relative timerange overrides!"
        logger.error(msg)
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=msg)

    inputs_to_expose = {inp_name for inp_name in exposed_inputs.split(",") if inp_name != ""}

    # Calculate override mode
    override_mode: OverrideMode = (
        OverrideMode.Absolute
        if (fromTimestamp is not None)
        else (OverrideMode.RelativeNow if relNow is not None else OverrideMode.NoOverride)
    )

    # obtain transformation revisions (including wiring)
    logger.info("Get transformation revision %s", id)

    try:
        transformation_revision = read_single_transformation_revision(id)
        logger.info("Found transformation revision with id %s", id)
    except DBNotFoundError as err:
        msg = f"Could not find transformation revision {id}:\n{str(err)}"
        logger.error(msg)
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=msg) from err
    logger.debug(transformation_revision.json())

    # obtain test wiring
    wiring = (
        deepcopy(transformation_revision.release_wiring)
        if use_release_wiring
        else deepcopy(transformation_revision.test_wiring)
    )

    if wiring is None:
        wiring = WorkflowWiring()

    try:
        wiring = update_wiring_from_query_parameters(wiring, request.query_params.items())
    except DashboardQueryParamValidationError as e:
        msg = str(e)
        logger.error(msg)
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=msg) from e

    # compute possible override time range setting
    calculated_from_timestamp, calculated_to_timestamp = calculate_timerange_timestamps(
        fromTimestamp, toTimestamp, relNow
    )

    # override timerange if requested:
    if calculated_from_timestamp is not None and calculated_to_timestamp is not None:
        override_timestamps_in_wiring(wiring, calculated_from_timestamp, calculated_to_timestamp)

    # construct execution payload
    exec_by_id: ExecByIdInput = ExecByIdInput(
        id=id,
        wiring=wiring,  # possibly edited wiring
        run_pure_plot_operators=True,
    )

    # execute
    exec_resp: ExecutionResponseFrontendDto = await handle_trafo_revision_execution_request(
        exec_by_id
    )

    # construct dashboard html response
    return generate_dashboard_html(
        transformation_revision=transformation_revision,
        actually_used_wiring=wiring,
        exec_resp=exec_resp,
        autoreload=autoreload,
        override_mode=override_mode,
        calculated_from_timestamp=calculated_from_timestamp,
        calculated_to_timestamp=calculated_to_timestamp,
        relNow=relNow,
        inputs_to_expose=inputs_to_expose,
        use_release_wiring=use_release_wiring,
        locked=locked,
    )
