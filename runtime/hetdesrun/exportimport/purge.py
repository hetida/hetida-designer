import logging
from uuid import UUID

from hetdesrun.exportimport.importing import import_transformations
from hetdesrun.exportimport.utils import (
    delete_transformation_revisions,
    deprecate_all_but_latest_in_group,
    get_transformation_revisions,
    update_or_create_transformation_revision,
)
from hetdesrun.trafoutils.filter.params import FilterParams
from hetdesrun.utils import State

logger = logging.getLogger(__name__)


def reset_test_wiring_to_release_wiring(directly_in_db: bool = False) -> None:
    tr_list = get_transformation_revisions(
        params=FilterParams(state=State.RELEASED, include_dependencies=False),
        directly_from_db=directly_in_db,
    )

    for tr in tr_list:
        if tr.release_wiring is not None:
            tr.test_wiring = tr.release_wiring
            update_or_create_transformation_revision(
                tr, directly_in_db=directly_in_db, allow_overwrite_released=True
            )

    tr_list = get_transformation_revisions(
        params=FilterParams(state=State.DISABLED, include_dependencies=False),
        directly_from_db=directly_in_db,
    )

    for tr in tr_list:
        if tr.release_wiring is not None:
            tr.test_wiring = tr.release_wiring
            update_or_create_transformation_revision(
                tr, directly_in_db=directly_in_db, allow_overwrite_released=True
            )


def deprecate_all_but_latest_per_group(directly_in_db: bool = False) -> None:
    tr_list = get_transformation_revisions(
        params=FilterParams(state=State.RELEASED, include_dependencies=False),
        directly_from_db=directly_in_db,
    )

    revision_group_ids: set[UUID] = set()

    for tr in tr_list:
        revision_group_ids.add(tr.revision_group_id)

    for revision_group_id in revision_group_ids:
        deprecate_all_but_latest_in_group(revision_group_id, directly_in_db=directly_in_db)


def delete_drafts(directly_in_db: bool = False) -> None:
    tr_list = get_transformation_revisions(
        params=FilterParams(state=State.DRAFT, include_dependencies=False),
        directly_from_db=directly_in_db,
    )

    delete_transformation_revisions(tr_list, directly_in_db=directly_in_db)


def delete_unused_deprecated(directly_in_db: bool = False) -> None:
    tr_list = get_transformation_revisions(
        params=FilterParams(state=State.DISABLED, include_dependencies=False, unused=True),
        directly_from_db=directly_in_db,
    )

    delete_transformation_revisions(tr_list, directly_in_db=directly_in_db)


def delete_all_and_refill(directly_in_db: bool = False) -> None:
    tr_list = get_transformation_revisions(directly_from_db=directly_in_db)

    delete_transformation_revisions(tr_list, directly_in_db=directly_in_db)

    import_transformations("./transformations", directly_into_db=directly_in_db)
