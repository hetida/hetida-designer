import json
import logging
import os
import re
import unicodedata
from pathlib import Path
from posixpath import join as posix_urljoin
from typing import Any, List, Optional, Union
from uuid import UUID

import requests

from hetdesrun.backend.models.component import ComponentRevisionFrontendDto
from hetdesrun.backend.models.workflow import WorkflowRevisionFrontendDto
from hetdesrun.exportimport.utils import FilterParams, get_transformation_revisions
from hetdesrun.models.code import NonEmptyValidStr
from hetdesrun.utils import State, Type, get_backend_basic_auth
from hetdesrun.webservice.auth_dependency import get_auth_headers
from hetdesrun.webservice.config import get_config

logger = logging.getLogger(__name__)


def slugify(value: str, allow_unicode: bool = False) -> str:
    """Sanitize string to make it usable as a file name

    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = (
            unicodedata.normalize("NFKD", value)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
    value = re.sub(r"[^\w\s-]", "", value.lower())
    return re.sub(r"[-\s]+", "-", value).strip("-_")


##Base function to save transformation
def save_transformation(tr_json: dict, download_path: str) -> None:
    # Create directory on local system
    uuid = tr_json["id"]
    name = tr_json["name"]
    # pylint: disable=redefined-builtin
    type = tr_json["type"]
    category = tr_json["category"]
    tag = tr_json["version_tag"]
    cat_dir = os.path.join(download_path, type.lower() + "s", slugify(category))
    Path(cat_dir).mkdir(parents=True, exist_ok=True)
    path = os.path.join(
        cat_dir,
        slugify(name) + "_" + slugify(tag) + "_" + uuid.lower() + ".json",
    )

    # Save the transformation revision
    with open(path, "w", encoding="utf8") as f:
        try:
            json.dump(dict(tr_json.items()), f, indent=2, sort_keys=True)
            logger.info("exported %s '%s' to %s", type, name, path)
        except KeyError:
            logger.error(
                "Could not safe the %s with id %s on the local system.", type, uuid
            )


##Base function to get transformation via REST API from DB (old endpoints)
# pylint: disable=redefined-builtin
def get_transformation_from_java_backend(id: UUID, type: Type) -> Any:
    """
    Loads a single transformation revision together with its documentation based on its id
    """

    headers = get_auth_headers()

    if type == Type.COMPONENT:
        url = posix_urljoin(get_config().hd_backend_api_url, "components", str(id))
    else:
        url = posix_urljoin(get_config().hd_backend_api_url, "workflows", str(id))

    # Get transformation revision from old backend
    response = requests.get(
        url,
        verify=get_config().hd_backend_verify_certs,
        auth=get_backend_basic_auth()  # type: ignore
        if get_config().hd_backend_use_basic_auth
        else None,
        headers=headers,
        timeout=get_config().external_request_timeout,
    )
    logger.info(
        "GET %s status code: %i for %s with id %ss",
        type,
        response.status_code,
        type,
        str(id),
    )
    if response.status_code != 200:
        msg = (
            f"COULD NOT GET {type} with id {id}.\n"
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
        auth=get_backend_basic_auth()  # type: ignore
        if get_config().hd_backend_use_basic_auth
        else None,
        headers=headers,
        timeout=get_config().external_request_timeout,
    )
    logger.info(
        "GET documentation status code: %i for %s with id %s",
        response.status_code,
        type,
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

    frontend_dto: Union[ComponentRevisionFrontendDto, WorkflowRevisionFrontendDto]

    # Generate transformation revision
    if type == Type.COMPONENT:
        frontend_dto = ComponentRevisionFrontendDto(
            **revision_json,
        )
    else:
        frontend_dto = WorkflowRevisionFrontendDto(
            **revision_json,
        )

    transformation_revision = frontend_dto.to_transformation_revision(
        documentation=doc_text
    )

    # for consistency with endpoints exclude none in JSON
    tr_json = json.loads(transformation_revision.json(exclude_none=True))

    return tr_json


##Export transformations based on type, id, name and category if provided
# pylint: disable=redefined-builtin
def export_transformations(
    download_path: str,
    type: Optional[Type] = None,
    state: Optional[State] = None,
    category: Optional[str] = None,
    ids: Optional[List[UUID]] = None,
    names: Optional[List[NonEmptyValidStr]] = None,
    include_deprecated: bool = True,
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
    import hetdesrun.models.wiring  # pylint: disable=import-outside-toplevel

    hetdesrun.models.wiring.EXPORT_MODE = True

    import hetdesrun.backend.models.wiring  # pylint: disable=import-outside-toplevel

    hetdesrun.backend.models.wiring.EXPORT_MODE = True

    if java_backend:
        url = posix_urljoin(get_config().hd_backend_api_url, "base-items")
        response = requests.get(
            url,
            verify=get_config().hd_backend_verify_certs,
            auth=get_backend_basic_auth()  # type: ignore
            if get_config().hd_backend_use_basic_auth
            else None,
            headers=get_auth_headers(),
            timeout=get_config().external_request_timeout,
        )

        if response.status_code != 200:
            msg = (
                f"COULD NOT GET transformation revisions from URL {url}.\n"
                f"Response status code {str(response.status_code)} "
                f"with response text: {str(response.text)}"
            )
            raise Exception(msg)

        transformation_list: List[dict] = []
        for trafo_json in response.json():
            transformation_list.append(
                get_transformation_from_java_backend(
                    trafo_json["id"], trafo_json["type"]
                )
            )
    else:
        params = FilterParams(
            type=type,
            state=state,
            category=category,
            ids=[str(id) for id in ids] if ids is not None else None,
            names=names,
            include_dependencies=True,
            include_deprecated=include_deprecated,
        )

        get_transformation_revisions(params=params, directly_from_db=directly_from_db)

    # Export individual transformation
    for transformation in transformation_list:
        save_transformation(transformation, download_path)
