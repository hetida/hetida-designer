"""Function around semantic versioning and released_timestamp"""

import datetime
from functools import cmp_to_key
from typing import Any, Literal
from uuid import UUID

import semver

from hetdesrun.persistence.dbservice.revision import get_multiple_transformation_revisions
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.trafoutils.filter.params import FilterParams
from hetdesrun.utils import State


def parse_semver_or_None(version_tag: str) -> semver.Version | None:
    """Parses a version tag defaulting to None if it is not semver parsable"""
    try:
        ver = semver.Version.parse(version_tag)
    except ValueError:
        # not parsable
        return None
    return ver


def safe_compare(
    item1: tuple[Any, semver.Version | None], item2: tuple[Any, semver.Version | None]
) -> Literal[-1, 0, 1]:
    val1 = item1[1]
    val2 = item2[1]

    # Handle None cases
    if val1 is None and val2 is None:
        return 0
    if val1 is None:
        return -1  # None comes first
    if val2 is None:
        return 1

    # handle non-None case by defering to semvers comparison operators
    return -1 if val1 < val2 else (1 if val2 < val1 else 0)


def get_newest_by_semver(trafos: list[TransformationRevision]) -> TransformationRevision | None:
    if len(trafos) == 0:
        return None

    trafos_by_id = {trafo.id: trafo for trafo in trafos}
    trafo_versions_by_id = {trafo.id: parse_semver_or_None(trafo.version_tag) for trafo in trafos}

    sorted_items = sorted(trafo_versions_by_id.items(), key=cmp_to_key(safe_compare))
    winner_id, winner_version = sorted_items[-1]

    if winner_version is None:
        return None

    return trafos_by_id[winner_id]


def get_newest_released_revision(
    trafos: list[TransformationRevision], use_release_date: bool = False
) -> TransformationRevision | None:
    """Among the given trafos, find the newest

    Returns None if a newest cannot be found for whatever reason.

    Defaults to using semver versioning, returning None if nothing is parsable as semver.

    Uses released_date timestampt instead if use_release_date is True.
    """

    if len(trafos) == 0:
        return None

    if use_release_date:
        return sorted(
            trafos,
            key=lambda x: (
                x.released_timestamp or datetime.datetime.min.replace(tzinfo=datetime.UTC)
            ),
        )[-1]

    return get_newest_by_semver(trafos)


def get_newest_released_trafo_rev(
    trafo_revision_group_ids: list[UUID], use_release_date: bool = False
) -> dict[UUID, TransformationRevision | None]:
    """Get possibly newest revision from db

    If no newer, released (not DRAFT, not DISABLED) transformation is
    found in the same transformation revision group, None is returned for
    that trafo revision.

    "Newer" can be chosen to be evaluated by using the release_timestamp. The
    default uses semantic versioning.
    """

    newest_per_revision_group: dict[UUID, TransformationRevision | None] = {}
    for rev_group_id in trafo_revision_group_ids:
        released_trafos_in_revision_group = get_multiple_transformation_revisions(
            FilterParams(
                state=State.RELEASED,
                revision_group_id=rev_group_id,
                include_dependencies=False,
            )
        )
        newest_per_revision_group[rev_group_id] = get_newest_released_revision(
            released_trafos_in_revision_group, use_release_date=use_release_date
        )

    return newest_per_revision_group


def get_current_revision_for_drafts(trafo_ids: set[UUID]) -> dict[UUID, TransformationRevision]:
    draft_trafos = get_multiple_transformation_revisions(
        FilterParams(
            ids=list(trafo_ids),
            include_dependencies=False,
        )
    )
    return {trafo.id: trafo for trafo in draft_trafos}
