import os
import json
import logging

from uuid import UUID
from posixpath import join as posix_urljoin
from typing import List, Dict, Any, Optional

import requests

from hetdesrun.utils import (
    Type,
    get_auth_headers,
    get_backend_basic_auth,
    selection_list_empty_or_contains_value,
    criterion_unset_or_matches_value,
)

from hetdesrun.webservice.config import runtime_config

logger = logging.getLogger(__name__)


def load_json(path: str) -> Any:
    try:
        with open(path, encoding="utf-8") as f:
            workflow_json = json.load(f)
    except FileNotFoundError:
        logger.error("Could not find json file at path %s", path)
        workflow_json = None
    return workflow_json


##Base function to import a transformation revision from a json file
def import_transformation(path: str) -> None:
    """
    Imports a transformation revision based on its path on the local system.

    WARNING: Overwrites possible existing transformation revision!

    Args:
        path (str): The local path of the transformation revision.

    Usage:
        import_transformation(
            "transformations/components/arithmetic/e_100_13d3376a-9c08-d78f-8ad4-6d24fef504ca.json"
        )
    """

    tr_json = load_json(path)

    headers = get_auth_headers()

    response = requests.put(
        posix_urljoin(
            runtime_config.hd_backend_api_url, "transformations", tr_json["id"]
        )
        + "?allow_overwrite_released=True",
        verify=runtime_config.hd_backend_verify_certs,
        json=tr_json,
        auth=get_backend_basic_auth()
        if runtime_config.hd_backend_use_basic_auth
        else None,
        headers=headers,
    )
    logger.info(
        (
            "PUT transformation status code: %d"
            " for transformation %s"
            " of type %s\n"
            "with name %s"
            " in category %s"
        ),
        response.status_code,
        tr_json["id"],
        tr_json["type"],
        tr_json["name"],
        tr_json["category"],
    )
    if response.status_code != 201:
        msg = (
            f"COULD NOT PUT {tr_json['type']} from path {path}\n."
            f"Response status code {response.status_code}"
            f"with response text:\n{response.text}"
        )
        logger.error(msg)


# Import all transformations based on type, id, name and category
def import_transformations(
    download_path: str,
    ids: Optional[List[UUID]] = None,
    names: Optional[List[str]] = None,
    category: Optional[str] = None,
) -> None:
    """
    This function imports all transformations together with their documentations
    that match all provided criteria.
    The download_path should be a path which contains the exported transformations
    organized in subdirectories corresponding to the categories.

    WARNING: Overwrites possible existing files!

    Usage:
        import_transformations("./transformations/components")
    """

    path_dict = {}
    transformation_dict = {}

    for root, _, files in os.walk(download_path):
        for file in files:
            path = os.path.join(root, file)
            transformation_json = load_json(path)
            transformation_dict[transformation_json["id"]] = transformation_json
            path_dict[transformation_json["id"]] = path

    def nesting_level(transformation_id: UUID, level: int) -> int:

        transformation = transformation_dict[transformation_id]

        level = level + 1
        nextlevel = level

        for operator in transformation["content"]["operators"]:
            if operator["type"] == Type.WORKFLOW:
                logger.info(
                    "workflow %s contains workflow %s -> nesting level %i",
                    str(transformation_id),
                    operator["transformation_id"],
                    level,
                )
                nextlevel = max(
                    nextlevel, nesting_level(operator["transformation_id"], level=level)
                )

        return nextlevel

    level_dict: Dict[int, List[UUID]] = {}

    for transformation_id, transformation in transformation_dict.items():
        level = 0
        if transformation["type"] == Type.WORKFLOW:
            level = nesting_level(transformation_id, level=level)
        if level not in level_dict:
            level_dict[level] = []
        level_dict[level].append(transformation_id)
        logger.info(
            "transformation %s has nesting level %i", str(transformation_id), level
        )

    for level in sorted(level_dict):
        logger.info("importing level %i transformations", level)
        for transformation_id in level_dict[level]:
            transformation = transformation_dict[transformation_id]
            if (
                selection_list_empty_or_contains_value(ids, transformation_id)
                and selection_list_empty_or_contains_value(
                    names, transformation["name"]
                )
                and criterion_unset_or_matches_value(
                    category, transformation["category"]
                )
            ):
                import_transformation(path_dict[transformation_id])

    logger.info("finished importing")


def import_all(download_path: str) -> None:
    import_transformations(os.path.join(download_path, "components"))
    import_transformations(os.path.join(download_path, "workflows"))
