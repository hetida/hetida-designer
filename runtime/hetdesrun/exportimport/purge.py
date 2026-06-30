import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from pydantic import AwareDatetime

from hetdesrun.exportimport.importing import import_transformations_from_dir
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


def delete_unused_deprecated(
    directly_in_db: bool = False,
    exclude: list[UUID] | None = None,
    cutoff_date: AwareDatetime | None = None,
) -> None:

    tr_list = get_transformation_revisions(
        params=FilterParams(state=State.DISABLED, include_dependencies=False, unused=True),
        directly_from_db=directly_in_db,
    )

    excluded_ids = exclude if exclude is not None else []
    cutoff_date_dt = cutoff_date if cutoff_date else datetime.now(timezone.utc) + timedelta(days=1)
    tr_list_reduced = []

    for trafo in tr_list:
        # Skip explicitly excluded entries
        if trafo.id in excluded_ids:
            logger.debug(
                "Transformation %s (%s) not deleted - it was explicitly excluded",
                trafo.name,
                trafo.version_tag,
            )
            continue

        # Skip entries newer than the cutoff date
        if trafo.disabled_timestamp and trafo.disabled_timestamp > cutoff_date_dt:
            logger.debug(
                "Transformation %s (%s) not deleted - deprecation later than specified cutoff date",
                trafo.name,
                trafo.version_tag,
            )
            continue

        tr_list_reduced.append(trafo)

    delete_transformation_revisions(tr_list_reduced, directly_in_db=directly_in_db)


def delete_all_and_refill(directly_in_db: bool = False) -> None:
    tr_list = get_transformation_revisions(directly_from_db=directly_in_db)

    delete_transformation_revisions(tr_list, directly_in_db=directly_in_db)

    import_transformations_from_dir("./transformations", directly_into_db=directly_in_db)
