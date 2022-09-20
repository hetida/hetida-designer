import logging
from datetime import datetime
from typing import Dict, Set
from uuid import UUID

from hetdesrun.exportimport.utils import (
    delete_transformation_revision,
    get_transformation_revisions,
    update_or_create_transformation_revision,
)
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.utils import State
from runtime.hetdesrun.exportimport.importing import import_transformations

logger = logging.getLogger(__name__)


def deprecate_all_but_latest_in_group(
    revision_group_id: UUID, directly_into_db: bool = False
) -> None:
    logger.info(
        "Deprecate outdated transformation revisions of revision revision group %s",
        str(revision_group_id),
    )

    tr_list = get_transformation_revisions(
        params={"revision_group_id": revision_group_id, "state": State.RELEASED},
        directly_into_db=directly_into_db,
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
        update_or_create_transformation_revision(tr, directly_into_db=directly_into_db)


def deprecate_all_but_latest_per_group(directly_into_db: bool = False) -> None:
    tr_list = get_transformation_revisions(params={"state": State.RELEASED})

    revision_group_ids: Set[UUID] = set()

    for tr in tr_list:
        revision_group_ids.add(tr.revision_group_id)

    for revision_group_id in revision_group_ids:
        deprecate_all_but_latest_in_group(revision_group_id, directly_into_db)


def delete_drafts(directly_into_db: bool = False) -> None:
    tr_list = get_transformation_revisions(params={"state": State.DRAFT})

    for tr in tr_list:
        delete_transformation_revision(tr.id, directly_into_db=directly_into_db)


def delete_all_restart(directly_into_db: bool = False) -> None:
    tr_list = get_transformation_revisions()

    for tr in tr_list:
        delete_transformation_revision(tr.id, directly_into_db=directly_into_db)

    import_transformations("./transformations", directly_into_db=directly_into_db)
