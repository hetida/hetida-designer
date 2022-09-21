import json
import logging
from datetime import datetime
from posixpath import join as posix_urljoin
from typing import Dict, List, Optional
from uuid import UUID

import requests
from pydantic import BaseModel

from hetdesrun.models.code import NonEmptyValidStr, ValidStr
from hetdesrun.persistence.dbservice.revision import (
    delete_single_transformation_revision,
    select_multiple_transformation_revisions,
    update_or_create_single_transformation_revision,
)
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.utils import State, Type, get_backend_basic_auth
from hetdesrun.webservice.auth_dependency import get_auth_headers
from hetdesrun.webservice.config import get_config

logger = logging.getLogger(__name__)


class FilterParams(BaseModel):
    type: Optional[Type]
    state: Optional[State]
    category: Optional[ValidStr]
    revision_group_id: Optional[UUID]
    ids: Optional[List[UUID]]
    names: Optional[List[NonEmptyValidStr]]
    include_deprecated: bool = True
    unused: bool = False


def get_transformation_revisions(
    params: Optional[FilterParams] = None, directly_from_db: bool = False
) -> List[TransformationRevision]:
    if params is None:
        params = {}

    if directly_from_db:
        return select_multiple_transformation_revisions(**params)

    get_response = requests.get(
        posix_urljoin(get_config().hd_backend_api_url, "transformations"),
        params=json.loads(params.json()),
        verify=get_config().hd_backend_verify_certs,
        auth=get_backend_basic_auth()  # type: ignore
        if get_config().hd_backend_use_basic_auth
        else None,
        headers=get_auth_headers(),
        timeout=get_config().external_request_timeout,
    )

    if get_response.status_code != 200:
        msg = (
            "COULD NOT GET transformation revisions. "
            f"Response status code {get_response.status_code}"
            f"with response text:\n{get_response.text}"
        )
        logger.error(msg)

    tr_list: List[TransformationRevision] = []

    for tr_json in get_response.json():
        tr_list.append(TransformationRevision(**tr_json))

    return tr_list


def update_or_create_transformation_revision(
    tr: TransformationRevision,
    directly_in_db: bool = False,
    update_component_code: bool = True,
) -> None:
    if directly_in_db:
        logger.info(
            (
                "Update or create database entry"
                " for transformation revision %s of type %s\n"
                "in category %s with name %s"
            ),
            str(tr.id),
            str(tr.type),
            tr.category,
            tr.name,
        )
        update_or_create_single_transformation_revision(tr)
    else:
        response = requests.put(
            posix_urljoin(
                get_config().hd_backend_api_url, "transformations", str(tr.id)
            ),
            params={
                "allow_overwrite_released": True,
                "update_component_code": update_component_code,
            },
            verify=get_config().hd_backend_verify_certs,
            json=json.loads(tr.json()),
            auth=get_backend_basic_auth()  # type: ignore
            if get_config().hd_backend_use_basic_auth
            else None,
            headers=get_auth_headers(),
            timeout=get_config().external_request_timeout,
        )
        logger.info(
            ("PUT %s with id %s in category %s with name %s"),
            tr.type,
            tr.id,
            tr.category,
            tr.name,
        )
        if response.status_code != 201:
            msg = (
                f"COULD NOT PUT {tr.type} with id {tr.id}\n."
                f"Response status code {response.status_code}"
                f"with response text:\n{response.text}"
            )
            logger.error(msg)


def delete_transformation_revision(
    id: UUID, directly_in_db: bool = False  # pylint: disable=redefined-builtin
) -> None:
    if directly_in_db:
        delete_single_transformation_revision(id)
    else:
        response = requests.delete(
            posix_urljoin(get_config().hd_backend_api_url, "transformations", str(id)),
            verify=get_config().hd_backend_verify_certs,
            auth=get_backend_basic_auth()  # type: ignore
            if get_config().hd_backend_use_basic_auth
            else None,
            headers=get_auth_headers(),
            timeout=get_config().external_request_timeout,
        )
        logger.info(
            ("DELETE transformation revision with id %s "),
            id,
        )
        if response.status_code != 204:
            msg = (
                f"COULD NOT DELETE transforamtion revision with id {id}\n."
                f"Response status code {response.status_code}"
                f"with response text:\n{response.text}"
            )
            logger.error(msg)


def deprecate_all_but_latest_in_group(
    revision_group_id: UUID, directly_in_db: bool = False
) -> None:
    logger.info(
        "Deprecate outdated transformation revisions of revision revision group %s",
        str(revision_group_id),
    )

    tr_list = get_transformation_revisions(
        params=FilterParams(revision_group_id=revision_group_id, state=State.RELEASED),
        directly_from_db=directly_in_db,
    )

    released_tr_dict: Dict[datetime, TransformationRevision] = {}
    for released_tr in tr_list:
        assert released_tr.released_timestamp is not None  # hint for mypy
        released_tr_dict[released_tr.released_timestamp] = released_tr

    latest_timestamp = max(released_tr_dict.keys())
    del released_tr_dict[latest_timestamp]

    for released_timestamp, tr in released_tr_dict.items():
        tr.deprecate()
        logger.info(
            "Deprecated transformation revision %s with released timestamp %s",
            tr.id,
            released_timestamp,
        )
        update_or_create_transformation_revision(tr, directly_in_db=directly_in_db)
