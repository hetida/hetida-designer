"""Selecting one revision of a revision group"""

from enum import StrEnum


class RevisionSelection(StrEnum):
    """Criterion for selecting one revision of a revision group

    LATEST selects the revision with the newest release timestamp.
    HIGHEST selects the revision with the highest semantic version as version tag,
    ignoring revisions whose version tag is not a semantic version.
    """

    LATEST = "latest"
    HIGHEST = "highest"


def validate_revision_selection(by: RevisionSelection, include_drafts: bool) -> None:
    """Raise ValueError if drafts are included where they cannot be selected

    Drafts have no release timestamp, so they can never be the latest revision.
    """
    if include_drafts and by is RevisionSelection.LATEST:
        raise ValueError(
            "Including drafts is only possible when selecting the highest revision:"
            " Drafts have no release timestamp and hence can never be the latest revision."
        )
