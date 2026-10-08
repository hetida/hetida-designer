"""Function around semantic versioning and released_timestamp"""

from collections.abc import Iterable
from typing import Any
from uuid import UUID

import semver

from hetdesrun.models.code import NonEmptyValidStr, ValidStr
from hetdesrun.models.revision_selection import RevisionSelection, validate_revision_selection
from hetdesrun.persistence.dbservice.exceptions import DBNotFoundError
from hetdesrun.persistence.dbservice.revision import (
    RevisionSelectionRow,
    get_multiple_transformation_revisions,
    select_multiple_transformation_revision_stubs,
    select_multiple_transformation_revisions,
    select_revision_selection_rows,
)
from hetdesrun.persistence.models.transformation import (
    TransformationRevision,
    TransformationRevisionStub,
)
from hetdesrun.trafoutils.filter.params import FilterParams
from hetdesrun.utils import State, Type


def parse_semver_or_None(version_tag: str) -> semver.Version | None:
    """Parses a version tag defaulting to None if it is not semver parsable"""
    try:
        ver = semver.Version.parse(version_tag)
    except ValueError:
        # not parsable
        return None
    return ver


def get_current_revision_for_drafts(trafo_ids: set[UUID]) -> dict[UUID, TransformationRevision]:
    draft_trafos = get_multiple_transformation_revisions(
        FilterParams(
            ids=list(trafo_ids),
            include_dependencies=False,
        )
    )
    return {trafo.id: trafo for trafo in draft_trafos}


def revision_selection_states(include_deprecated: bool, include_drafts: bool) -> list[State]:
    """States of the revisions which may be selected as latest / highest revision"""
    states = [State.RELEASED]
    if include_deprecated:
        states.append(State.DISABLED)
    if include_drafts:
        states.append(State.DRAFT)
    return states


def revision_selection_key(
    row: RevisionSelectionRow, by: RevisionSelection
) -> tuple[Any, ...] | None:
    """Key by which the latest / highest revision of a revision group is the maximum

    Returns None if the revision cannot be selected: For LATEST if it has no release
    timestamp (drafts), for HIGHEST if its version tag is no semantic version.

    Semantic versions are compared by their precedence, i.e. pre-releases are lower
    than the corresponding release and build metadata is ignored.

    Ties are broken deterministically: For LATEST by the id. For HIGHEST (version tags
    differing only in build metadata) by the release timestamp, where released revisions
    win against drafts, and then by the id.
    """
    if by is RevisionSelection.LATEST:
        if row.released_timestamp is None:
            return None
        return (row.released_timestamp, row.id)

    version = parse_semver_or_None(row.version_tag)
    if version is None:
        return None
    # checking for presence first avoids comparing a release timestamp with None
    return (version, row.released_timestamp is not None, row.released_timestamp, row.id)


def pick_revision_ids_per_group(
    rows: Iterable[RevisionSelectionRow], by: RevisionSelection
) -> dict[UUID, UUID]:
    """Pick the latest / highest revision of each revision group among the given rows

    Returns a dict mapping revision group ids to the id of the picked revision. Revision
    groups without a revision which can be selected are missing.
    """
    picked_keys: dict[UUID, tuple[Any, ...]] = {}
    picked_ids: dict[UUID, UUID] = {}
    for row in rows:
        key = revision_selection_key(row, by)
        if key is None:
            continue
        if row.revision_group_id not in picked_keys or key > picked_keys[row.revision_group_id]:
            picked_keys[row.revision_group_id] = key
            picked_ids[row.revision_group_id] = row.id
    return picked_ids


def select_revision_ids_per_group(
    by: RevisionSelection = RevisionSelection.LATEST,
    include_deprecated: bool = False,
    include_drafts: bool = False,
    type: Type | None = None,  # noqa: A002
    categories: list[ValidStr] | None = None,
    category_prefix: ValidStr | None = None,
    revision_group_ids: list[UUID] | None = None,
    names: list[NonEmptyValidStr] | None = None,
) -> dict[UUID, UUID]:
    """Select the latest / highest revision of each revision group from db

    By default only released revisions are considered. Deprecated revisions can be
    included and, only for HIGHEST, drafts, too.

    The filters are applied first: Revision groups with at least one revision matching
    all filters are considered and among their revisions matching the filters the
    latest / highest is selected.

    Returns a dict mapping revision group ids to the id of the selected revision.
    """
    validate_revision_selection(by, include_drafts)
    rows = select_revision_selection_rows(
        states=revision_selection_states(include_deprecated, include_drafts),
        type=type,
        categories=categories,
        category_prefix=category_prefix,
        revision_group_ids=revision_group_ids,
        names=names,
    )
    return pick_revision_ids_per_group(rows, by)


def select_revision_id_of_group(
    revision_group_id: UUID,
    by: RevisionSelection = RevisionSelection.LATEST,
    include_deprecated: bool = False,
    include_drafts: bool = False,
) -> UUID:
    """Select the latest / highest revision of one revision group from db

    All endpoints providing or executing the latest / highest revision of a revision
    group rely on this, so that they always agree on the selected revision.

    Raises DBNotFoundError if the revision group has no revision which can be selected.
    """
    selected = select_revision_ids_per_group(
        by=by,
        include_deprecated=include_deprecated,
        include_drafts=include_drafts,
        revision_group_ids=[revision_group_id],
    )
    if revision_group_id not in selected:
        states = " or ".join(
            state.lower() if state is not State.DISABLED else "deprecated"
            for state in revision_selection_states(include_deprecated, include_drafts)
        )
        semver_hint = (
            " and a semantic version as version tag" if by is RevisionSelection.HIGHEST else ""
        )
        raise DBNotFoundError(
            f"no {states} transformation revisions with revision group id"
            f" {revision_group_id}{semver_hint} found in the database"
        )
    return selected[revision_group_id]


def select_revisions_of_groups(
    revision_group_ids: Iterable[UUID],
    by: RevisionSelection = RevisionSelection.LATEST,
) -> dict[UUID, TransformationRevision | None]:
    """Select the latest / highest released revision of each given revision group from db

    The revisions are selected exactly as by select_revision_id_of_group. Revision groups
    without a revision which can be selected are mapped to None.
    """
    revision_group_ids = list(revision_group_ids)
    selected_ids = select_revision_ids_per_group(by=by, revision_group_ids=revision_group_ids)
    trafos_by_id = {
        trafo.id: trafo
        for trafo in select_multiple_transformation_revisions(ids=list(selected_ids.values()))
    }
    return {
        revision_group_id: (
            trafos_by_id.get(selected_ids[revision_group_id])
            if revision_group_id in selected_ids
            else None
        )
        for revision_group_id in revision_group_ids
    }


def load_selected_revision_stubs(
    revision_ids_by_group: dict[UUID, UUID],
) -> list[TransformationRevisionStub]:
    """Load stubs of selected revisions ordered by name and revision group id"""
    stubs = select_multiple_transformation_revision_stubs(ids=list(revision_ids_by_group.values()))
    return sorted(stubs, key=lambda stub: (stub.name, str(stub.revision_group_id)))


def load_selected_revisions(
    revision_ids_by_group: dict[UUID, UUID],
) -> list[TransformationRevision]:
    """Load selected revisions ordered by name and revision group id"""
    trafos = select_multiple_transformation_revisions(ids=list(revision_ids_by_group.values()))
    return sorted(trafos, key=lambda trafo: (trafo.name, str(trafo.revision_group_id)))
