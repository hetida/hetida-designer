import logging
from typing import Set
from uuid import UUID

from hetdesrun.exportimport.importing import import_transformations
from hetdesrun.exportimport.utils import (
    FilterParams,
    delete_transformation_revisions,
    deprecate_all_but_latest_in_group,
    get_transformation_revisions,
)
from hetdesrun.utils import State

logger = logging.getLogger(__name__)


def deprecate_all_but_latest_per_group(directly_in_db: bool = False) -> None:
    tr_list = get_transformation_revisions(
        params=FilterParams(state=State.RELEASED), directly_from_db=directly_in_db
    )

    revision_group_ids: Set[UUID] = set()

    for tr in tr_list:
        revision_group_ids.add(tr.revision_group_id)

    for revision_group_id in revision_group_ids:
        deprecate_all_but_latest_in_group(
            revision_group_id, directly_in_db=directly_in_db
        )


def delete_drafts(directly_in_db: bool = False) -> None:
    tr_list = get_transformation_revisions(
        params=FilterParams(state=State.DRAFT), directly_from_db=directly_in_db
    )

    delete_transformation_revisions(tr_list, directly_in_db=directly_in_db)


def delete_unused_deprecated(directly_in_db: bool = False) -> None:
    tr_list = get_transformation_revisions(
        params=FilterParams(state=State.DISABLED, unused=True),
        directly_from_db=directly_in_db,
    )

    delete_transformation_revisions(tr_list, directly_in_db=directly_in_db)


def delete_all_and_refill(directly_in_db: bool = False) -> None:
    tr_list = get_transformation_revisions(directly_from_db=directly_in_db)

    delete_transformation_revisions(tr_list, directly_in_db=directly_in_db)

    import_transformations("./transformations", directly_into_db=directly_in_db)
