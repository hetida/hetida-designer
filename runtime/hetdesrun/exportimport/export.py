import logging
from posixpath import join as posix_urljoin
from typing import Any
from uuid import UUID

import requests
from pydantic import ValidationError

from hetdesrun.backend.models.component import ComponentRevisionFrontendDto
from hetdesrun.backend.models.workflow import WorkflowRevisionFrontendDto
from hetdesrun.exportimport.utils import get_transformation_revisions
from hetdesrun.models.code import NonEmptyValidStr, ValidStr
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.trafoutils.filter.params import FilterParams
from hetdesrun.trafoutils.io.save import save_transformation_into_directory
from hetdesrun.utils import State, Type, get_backend_basic_auth
from hetdesrun.webservice.auth_dependency import sync_wrapped_get_auth_headers
from hetdesrun.webservice.auth_outgoing import ServiceAuthenticationError
from hetdesrun.webservice.config import get_config

logger = logging.getLogger(__name__)


def get_transformation_from_java_backend(
    id: UUID,  # noqa: A002
    type: Type,  # noqa: A002
    headers: dict[str, str],
) -> TransformationRevision:
    """Get transformation via REST API from old backend (old endpoints)

    Loads a single transformation revision together with its documentation based on its id
    """
    if type == Type.COMPONENT:
        url = posix_urljoin(get_config().hd_backend_api_url, "components", str(id))
    else:
        url = posix_urljoin(get_config().hd_backend_api_url, "workflows", str(id))

    # Get transformation revision from old backend
    response = requests.get(
        url,
        verify=get_config().hd_backend_verify_certs,
        auth=get_backend_basic_auth(),  # type: ignore
        headers=headers,
        timeout=get_config().external_request_timeout,
    )
    logger.info(
        "GET %s status code: %i for %s with id %ss",
        type.value,
        response.status_code,
        type.value,
        str(id),
    )
    if response.status_code != 200:
        msg = (
            f"COULD NOT GET {type.value} with id {id}.\n"
            f"Response status code {response.status_code} "
            f"with response text:\n{response.json()['detail']}"
        )
        logger.error(msg)
        raise Exception(msg)

    revision_json = response.json()

    # Get documentation from old backend
    doc_response = requests.get(
        posix_urljoin(get_config().hd_backend_api_url, "documentations", str(id)),
        verify=get_config().hd_backend_verify_certs,
        auth=get_backend_basic_auth(),  # type: ignore
        headers=headers,
        timeout=get_config().external_request_timeout,
    )
    logger.info(
        "GET documentation status code: %i for %s with id %s",
        response.status_code,
        type.value,
        str(id),
    )
    if response.status_code != 200:
        msg = (
            f"COULD NOT GET documentation with id {id}.\n"
            f"Response status code {response.status_code} "
            f"with response text:\n{response.json()['detail']}"
        )
        logger.error(msg)
        raise Exception(msg)

    doc_text = doc_response.json().get("document", "")

    frontend_dto: ComponentRevisionFrontendDto | WorkflowRevisionFrontendDto

    # Generate transformation revision
    if type == Type.COMPONENT:
        frontend_dto = ComponentRevisionFrontendDto(
            **revision_json,
        )
    else:
        frontend_dto = WorkflowRevisionFrontendDto(
            **revision_json,
        )

    transformation_revision = frontend_dto.to_transformation_revision(documentation=doc_text)

    return transformation_revision


def get_base_item_jsons_from_java_backend(headers: dict[str, str]) -> Any:
    url = posix_urljoin(get_config().hd_backend_api_url, "base-items")
    response = requests.get(
        url,
        verify=get_config().hd_backend_verify_certs,
        auth=get_backend_basic_auth(),  # type: ignore
        headers=headers,
        timeout=get_config().external_request_timeout,
    )

    if response.status_code != 200:
        msg = (
            f"COULD NOT GET transformation revisions from URL {url}.\n"
            f"Response status code {str(response.status_code)} "
            f"with response text: {str(response.text)}"
        )
        raise Exception(msg)

    return response.json()


def selection_list_empty_or_contains_value(
    selection_list: list[Any] | None, actual_value: Any
) -> bool:
    if selection_list is None:
        return True
    return actual_value in selection_list


def criterion_unset_or_matches_value(criterion: Any | None, actual_value: Any) -> bool:
    if criterion is None:
        return True
    return bool(actual_value == criterion)


def passes_all_filters(
    trafo_json: Any,
    type: Type | None = None,  # noqa: A002
    categories: list[ValidStr] | None = None,
    ids: list[UUID | str] | None = None,
    names: list[NonEmptyValidStr] | None = None,
    include_deprecated: bool = True,
) -> bool:
    filter_type = criterion_unset_or_matches_value(type, Type(trafo_json["type"]))
    filter_ids = selection_list_empty_or_contains_value(ids, UUID(trafo_json["id"]))
    filter_names = selection_list_empty_or_contains_value(names, trafo_json["name"])
    filter_categories = selection_list_empty_or_contains_value(categories, trafo_json["category"])
    filter_state = include_deprecated or trafo_json["state"] != State.DISABLED

    combined_filter = (
        filter_type and filter_ids and filter_names and filter_categories and filter_state
    )

    return combined_filter


def convert_id_type_to_uuid(
    ids: list[UUID | str] | None,
) -> list[UUID | str] | None:
    if ids is None:
        return None
    return [UUID(id_) for id_ in ids if isinstance(id_, str)]


##Export transformations based on type, id, name and category if provided
def export_transformations(
    download_path: str,
    type: Type | None = None,  # noqa: A002
    state: State | None = None,
    categories: list[ValidStr] | None = None,
    category_prefix: ValidStr | None = None,
    ids: list[UUID | str] | None = None,
    names: list[NonEmptyValidStr] | None = None,
    include_deprecated: bool = True,
    components_as_code: bool = False,
    expand_component_code: bool = False,
    directly_from_db: bool = False,
    java_backend: bool = False,
) -> None:
    """Export transformation revisions.

    Exports all transformations, together with their documentation, and saves them as json files
    in subdirectories of the provided path corresponding to the respective category,
    based on the provide criteria. If more than one criterion is provided,
    only transformations which fulfilll all criteria will be exported.

    WARNING: Overwrites existing files with the same name!

    Arguments:
        download_path (str): The directory on the local system, where we save the transformations.

    Keyword Arguments:
        type (Type): One of the two values of the enum Type: WORKFLOW or COMPONENT
        state (State): One of the three values of the enum State: DRAFT, RELEASED or DISABLED
        category (str): The category of the transformations.
        ids (List[UUID]): The ids of the transformations.
        names (List[str]): The names of the transformations.
        include_deprecated (bool = True): Set to False to export only transformation revisions
            with state DRAFT or RELEASED.
        components_as_code (bool = False): Set to True to obtain python files instead of json files
            for components.
        expand_component_code (bool = False): Set to True to add the documentation as module
            docstring and the test wiring as dictionary to the component code.
        directly_from_db (bool = False): Set to True to export directly from the databse.
        java_backend (bool = False): Set to True to export from a hetida designer instance with a
            version smaller than 0.7.

    Usage examples:
        export_transformations("/mnt/obj_repo/migration_data")
        export_transformations(
            "/mnt/obj_repo/migration_data",
            ids=["d71a0cef-1d56-818f-a1a5-dd6bb6d50399","806df1b9-2fc8-4463-943f-3d258c569663"]
        )
        export_transformations("/mnt/obj_repo/migration_data/components", type="COMPONENT")
        export_transformations(
            "/mnt/obj_repo/migration_data/components",
            type="COMPONENT",
            names=["Divide", "Add"]
        )
        export_transformations(
            "/mnt/obj_repo/migration_data/workflows",
            type="WORKFLOW",
            category="Examples"
        )

    """
    import hetdesrun.models.wiring

    hetdesrun.models.wiring.ALLOW_UNCONFIGURED_ADAPTER_IDS_IN_WIRINGS = True

    import hetdesrun.backend.models.wiring

    hetdesrun.backend.models.wiring.ALLOW_UNCONFIGURED_ADAPTER_IDS_IN_WIRINGS = True

    transformation_list: list[TransformationRevision] = []
    try:
        headers = sync_wrapped_get_auth_headers(external=True)
    except ServiceAuthenticationError as e:
        msg = (
            "Failed to get auth headers for external request for exporting transformations."
            f" Error was:\n{str(e)}"
        )
        logger.error(msg)
        raise Exception(msg) from e

    if java_backend:
        if category_prefix is not None:
            msg = 'For the java backend the filter option "categories_with_prefix" is not provided!'
            logger.error(msg)
            raise Exception(msg)

        base_item_jsons = get_base_item_jsons_from_java_backend(headers)

        failed_exports: list[Any] = []
        for base_item_json in base_item_jsons:
            if passes_all_filters(base_item_json, type, categories, ids, names, include_deprecated):
                try:
                    transformation = get_transformation_from_java_backend(
                        UUID(base_item_json["id"]),
                        Type(base_item_json["type"]),
                        headers,
                    )
                except ValidationError as e:
                    failed_exports.append((base_item_json, e))
                else:
                    save_transformation_into_directory(transformation, download_path)
        for export in failed_exports:
            base_item_json = export[0]
            error = export[1]
            logger.error(
                "Could not export %s with id %s in category '%s' with name '%s' and tag '%s':\n%s",
                base_item_json["type"],
                base_item_json["id"],
                base_item_json["category"],
                base_item_json["name"],
                base_item_json["tag"],
                error,
            )
    else:
        params = FilterParams(
            type=type,
            state=state,
            categories=categories,
            category_prefix=category_prefix,
            ids=ids,
            names=names,
            include_dependencies=True,
            include_deprecated=include_deprecated,
        )

        transformation_list = get_transformation_revisions(
            params=params, directly_from_db=directly_from_db
        )

        # Export individual transformation
        for transformation in transformation_list:
            save_transformation_into_directory(
                transformation, download_path, components_as_code, expand_component_code
            )
