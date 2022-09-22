import json
import logging
from datetime import datetime
from posixpath import join as posix_urljoin
from typing import Any, Dict, List, Optional
from uuid import UUID

import requests
from pydantic import BaseModel

from hetdesrun.component.code import update_code
from hetdesrun.models.code import NonEmptyValidStr, ValidStr
from hetdesrun.persistence.dbservice.exceptions import DBIntegrityError, DBNotFoundError
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


def info(text: str, param: Optional[Any], case: Optional[bool] = None) -> str:
    if param is not None and case is None or case is True:
        return text + str(param)
    return ""


class FilterParams(BaseModel):
    type: Optional[Type]
    state: Optional[State]
    category: Optional[ValidStr]
    revision_group_id: Optional[UUID]
    ids: Optional[List[UUID]]
    names: Optional[List[NonEmptyValidStr]]
    include_deprecated: bool = True
    unused: bool = False

    def str(self) -> str:
        return (
            "all transformation revisions"
            + info(" of type ", self.type)
            + info(" in state ", self.state)
            + info(" in category ", self.category)
            + info(" with group_id ", self.revision_group_id)
            + info(
                " unless they are deprecated",
                self.include_deprecated,
                case=not self.include_deprecated,
            )
            + info(
                " that are unused",
                self.unused,
                case=self.unused,
            )
            + info("\nwith ids ", self.ids)
            + info("\nwith names ", self.names)
        )


def get_transformation_revisions(
    params: FilterParams = FilterParams(), directly_from_db: bool = False
) -> List[TransformationRevision]:
    logger.info("Getting " + params.str() + "directly from db" if directly_from_db else "")
    if directly_from_db:
        tr_list = select_multiple_transformation_revisions(
            **params.dict(exclude_none=True)
        )
    else:
        get_response = requests.get(
            posix_urljoin(get_config().hd_backend_api_url, "transformations"),
            params=json.loads(params.json(exclude_none=True)),
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
            return []

        tr_list: List[TransformationRevision] = []

        for tr_json in get_response.json():
            tr_list.append(TransformationRevision(**tr_json))

    for tr in tr_list:
        logger.info(
            ("Found %s with id %s\n" "in category %s with name %s"),
            str(tr.type.value),
            str(tr.id),
            tr.category,
            tr.name,
        )
    return tr_list


def update_or_create_transformation_revision(
    tr: TransformationRevision,
    directly_in_db: bool = False,
    update_component_code: bool = True,
) -> None:
    if directly_in_db:
        logger.info(
            (
                "Update or create DB entry"
                " for %s with id %s\n"
                "in category %s with name %s"
            ),
            str(tr.type),
            str(tr.id),
            tr.category,
            tr.name,
        )
        if update_component_code and tr.type == Type.COMPONENT:
            tr.content = update_code(tr)
        try:
            update_or_create_single_transformation_revision(tr)
        except DBNotFoundError as not_found_err:
            logger.error(
                "Not found error in DB when trying to access entry for id %s\n%s",
                id,
                not_found_err,
            )
        except DBIntegrityError as integrity_err:
            logger.error(
                "Integrity error in DB when trying to access entry for id %s\n%s",
                id,
                integrity_err,
            )
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
        try:
            logger.info(
                ("Delete transformation revision with id %s from DB"),
                id,
            )
            delete_single_transformation_revision(id, ignore_state=True)
        except DBNotFoundError as not_found_err:
            logger.error(
                "Not found error in DB when trying to access entry for id %s\n%s",
                id,
                not_found_err,
            )
    else:
        response = requests.delete(
            posix_urljoin(get_config().hd_backend_api_url, "transformations", str(id)),
            params={"ignore_state": True},
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
                f"COULD NOT DELETE transformation revision with id {id}\n."
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
        try:
            update_or_create_transformation_revision(tr, directly_in_db=directly_in_db)
        except DBNotFoundError as not_found_err:
            logger.error(
                "Not found error in DB when trying to access entry for id %s\n%s",
                tr.id,
                not_found_err,
            )
        except DBIntegrityError as integrity_err:
            logger.error(
                "Integrity error in DB when trying to access entry for id %s\n%s",
                tr.id,
                integrity_err,
            )
