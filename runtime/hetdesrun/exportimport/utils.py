import json
import logging
from datetime import datetime
from posixpath import join as posix_urljoin
from uuid import UUID

import requests

from hetdesrun.persistence.dbservice.exceptions import DBIntegrityError, DBNotFoundError
from hetdesrun.persistence.dbservice.revision import (
    delete_single_transformation_revision,
    get_multiple_transformation_revisions,
    update_or_create_single_transformation_revision,
)
from hetdesrun.persistence.models.exceptions import ModifyForbidden
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.trafoutils.filter.params import FilterParams
from hetdesrun.trafoutils.nestings import structure_ids_by_nesting_level
from hetdesrun.utils import State, get_backend_basic_auth
from hetdesrun.webservice.auth_dependency import sync_wrapped_get_auth_headers
from hetdesrun.webservice.auth_outgoing import ServiceAuthenticationError
from hetdesrun.webservice.config import get_config

logger = logging.getLogger(__name__)


def get_transformation_revisions(
    params: FilterParams = FilterParams(include_dependencies=False),
    directly_from_db: bool = False,
) -> list[TransformationRevision]:
    logger.info(
        "Getting transformation revisions with "  # noqa: G003
        + repr(params)
        + (" directly from db" if directly_from_db else "")
    )

    tr_list: list[TransformationRevision] = []

    if directly_from_db:
        tr_list = get_multiple_transformation_revisions(params)
    else:
        try:
            headers = sync_wrapped_get_auth_headers(external=True)
        except ServiceAuthenticationError as e:
            msg = (
                "Failed to get auth headers for external request for importing transformations."
                f" Error was:\n{str(e)}"
            )
            logger.error(msg)
            raise Exception(msg) from e
        get_response = requests.get(
            posix_urljoin(get_config().hd_backend_api_url, "transformations"),
            params=json.loads(params.json(exclude_none=True, by_alias=True)),
            verify=get_config().hd_backend_verify_certs,
            auth=get_backend_basic_auth(),  # type: ignore
            headers=headers,
            timeout=get_config().external_request_timeout,
        )

        if get_response.status_code != 200:
            msg = (
                "COULD NOT GET transformation revisions. "
                f"Response status code {get_response.status_code} "
                f"with response text:\n{get_response.text}"
            )
            logger.error(msg)
            return []

        for tr_json in get_response.json():
            tr_list.append(TransformationRevision(**tr_json))

    for tr in tr_list:
        logger.info(
            ("Found %s with id %s and revision group id %s in category '%s' with name '%s'"),
            tr.type.value,
            str(tr.id),
            str(tr.revision_group_id),
            tr.category,
            tr.name,
        )
    return tr_list


def update_or_create_transformation_revision(
    tr: TransformationRevision,
    directly_in_db: bool = False,
    allow_overwrite_released: bool = True,
    update_component_code: bool = True,
    strip_wiring: bool = False,
) -> None:
    if directly_in_db:
        logger.info(
            ("Update or create DB entry" " for %s with id %s\n" "in category %s with name %s"),
            tr.type.value,
            str(tr.id),
            tr.category,
            tr.name,
        )
        try:
            update_or_create_single_transformation_revision(
                tr,
                allow_overwrite_released=allow_overwrite_released,
                update_component_code=update_component_code,
                strip_wiring=strip_wiring,
            )
        except DBNotFoundError as not_found_err:
            logger.error(
                "Not found error in DB when trying to access entry for id %s\n%s",
                str(tr.id),
                not_found_err,
            )
        except DBIntegrityError as integrity_err:
            logger.error(
                "Integrity error in DB when trying to access entry for id %s\n%s",
                str(tr.id),
                integrity_err,
            )
        except ModifyForbidden as forbidden_err:
            if allow_overwrite_released:
                # This covers reasons independent of the state, such as changing the type
                logger.error(
                    "Update forbidden for entry with id %s:\n%s",
                    str(tr.id),
                    forbidden_err,
                )
                raise forbidden_err
            logger.info(
                "%s with id %s already in DB and released/deprecated",
                str(tr.id),
                forbidden_err,
            )

    else:
        try:
            headers = sync_wrapped_get_auth_headers(external=True)
        except ServiceAuthenticationError as e:
            msg = (
                "Failed to get auth headers for external request for importing transformations."
                f" Error was:\n{str(e)}"
            )
            logger.error(msg)
            raise Exception(msg) from e

        response = requests.put(
            posix_urljoin(get_config().hd_backend_api_url, "transformations", str(tr.id)),
            params={
                "allow_overwrite_released": allow_overwrite_released,
                "update_component_code": update_component_code,
                "strip_wiring": strip_wiring,
            },
            verify=get_config().hd_backend_verify_certs,
            json=json.loads(tr.json()),  # TODO: avoid double serialization.
            auth=get_backend_basic_auth(),  # type: ignore
            headers=headers,
            timeout=get_config().external_request_timeout,
        )
        logger.info(
            ("PUT %s with id %s in category %s with name %s"),
            tr.type.value,
            tr.id,
            tr.category,
            tr.name,
        )

        if response.status_code != 201:
            if allow_overwrite_released is False and response.status_code == 409:
                # other reason for 409: type of object in DB and of passed object do not match
                logger.info(
                    "%s with id %s already in DB and released/deprecated",
                    tr.type.value,
                    str(tr.id),
                )
            else:
                msg = (
                    f"COULD NOT PUT {str(tr.type)} with id {tr.id}.\n"
                    f"Response status code {response.status_code} "
                    f"with response text:\n{response.text}"
                )
                logger.error(msg)


def delete_transformation_revision(
    id: UUID,  # noqa: A002
    directly_in_db: bool = False,
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
        try:
            headers = sync_wrapped_get_auth_headers(external=True)
        except ServiceAuthenticationError as e:
            msg = (
                "Failed to get auth headers for external request for importing transformations."
                f" Error was:\n{str(e)}"
            )
            logger.error(msg)
            raise Exception(msg) from e

        response = requests.delete(
            posix_urljoin(get_config().hd_backend_api_url, "transformations", str(id)),
            params={"ignore_state": True},
            verify=get_config().hd_backend_verify_certs,
            auth=get_backend_basic_auth(),  # type: ignore
            headers=headers,
            timeout=get_config().external_request_timeout,
        )
        logger.info(
            ("DELETE transformation revision with id %s "),
            id,
        )
        if response.status_code != 204:
            msg = (
                f"COULD NOT DELETE transformation revision with id {id}\n."
                f"Response status code {response.status_code} "
                f"with response text:\n{response.text}"
            )
            logger.error(msg)


def delete_transformation_revisions(
    tr_list: list[TransformationRevision], directly_in_db: bool = False
) -> None:
    delete_tr_ids = [tr.id for tr in tr_list]
    tr_list_including_dependencies = get_transformation_revisions(
        params=FilterParams(ids=delete_tr_ids, include_dependencies=True),
        directly_from_db=directly_in_db,
    )
    depencency_tr_dict = {tr.id: tr for tr in tr_list_including_dependencies}
    level_dict = structure_ids_by_nesting_level(depencency_tr_dict)

    for level in sorted(level_dict, reverse=True):
        logger.info("Deleting level %i transformation revisions", level)
        for tr_id in level_dict[level]:
            if tr_id in delete_tr_ids:
                delete_transformation_revision(tr_id, directly_in_db=directly_in_db)


def deprecate_all_but_latest_in_group(
    revision_group_id: UUID, directly_in_db: bool = False
) -> None:
    logger.info(
        "Deprecate outdated transformation revisions of revision revision group %s",
        str(revision_group_id),
    )

    tr_list = get_transformation_revisions(
        params=FilterParams(
            revision_group_id=revision_group_id,
            state=State.RELEASED,
            include_dependencies=False,
        ),
        directly_from_db=directly_in_db,
    )

    if len(tr_list) == 0:
        return

    released_tr_by_release_timestamp_dict: dict[datetime, TransformationRevision] = {}
    for released_tr in tr_list:
        assert released_tr.released_timestamp is not None  # noqa: S101  # hint for mypy
        released_tr_by_release_timestamp_dict[released_tr.released_timestamp] = released_tr

    latest_timestamp = max(released_tr_by_release_timestamp_dict.keys())
    del released_tr_by_release_timestamp_dict[latest_timestamp]

    for released_timestamp, tr in released_tr_by_release_timestamp_dict.items():
        tr.deprecate()
        logger.info(
            "Deprecated transformation revision %s with released timestamp %s",
            tr.id,
            released_timestamp,
        )
        update_or_create_transformation_revision(tr, directly_in_db=directly_in_db)
