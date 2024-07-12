"""Filtering ensembles of transoformation revisions

Of a given collection of transformation revisions one is often interested
in only a subset, e.g. when importing. For example all workflows in a certain
category together with the transitive dependency closure.

This module contains filtering functions for ensembles of transformation revisions.
"""

from uuid import UUID

from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.trafoutils.dependencies import get_direct_dependencies
from hetdesrun.trafoutils.filter.params import FilterParams
from hetdesrun.trafoutils.nestings import structure_ids_by_nesting_level
from hetdesrun.utils import State


def basic_trafo_filter_map(
    transformation_revisions: list[TransformationRevision], filter_params: FilterParams
) -> dict[UUID, bool]:
    """Get a filter map which does not consider dependencies and unused criteria

    If criteria are set, they all must be fulfilled (logical AND). If no criteria
    are set, all are included by default.

    This does not handle the "include_dependencies" filter parameter, which must be
    handled in a separate step using nesting information.

    This does not handle the "unused" filter parameter, which requires dependency information
    and must therefore be handled in a separate step.
    """

    filter_map = {trafo.id: True for trafo in transformation_revisions}

    for trafo in transformation_revisions:
        allow = True
        if filter_params.type is not None and trafo.type != filter_params.type:
            allow = False
        if filter_params.state is not None and trafo.state != filter_params.state:
            allow = False
        if filter_params.categories is not None and trafo.category not in filter_params.categories:
            allow = False
        if filter_params.category_prefix is not None and not trafo.category.startswith(
            filter_params.category_prefix
        ):
            allow = False

        if (
            filter_params.revision_group_id is not None
            and trafo.revision_group_id != filter_params.revision_group_id
        ):
            allow = False
        if filter_params.ids is not None and trafo.id not in filter_params.ids:
            allow = False
        if filter_params.names is not None and trafo.name not in filter_params.names:
            allow = False
        if (not filter_params.include_deprecated) and trafo.state == State.DISABLED:
            allow = False

        filter_map[trafo.id] = allow
    return filter_map


def update_filter_for_dependencies(
    filter_map: dict[UUID, bool],
    ids_by_nesting_level: dict[int, list[UUID]],
    transformation_dict: dict[UUID, TransformationRevision],
    raise_on_missing_dependency: bool = False,
) -> None:
    """Update filter_map inplace to include dependencies

    The filter_map is expected to already have true values for each trafo id
    which has passed the filter criteria. It is then updated inplace to also
    let pass their dependencies for which there are entries in the filter_map (by
    setting their value to True).

    This function ignores missing entries in the filter_map if
    raise_on_missing_dependency is set to False (default). Otherwise it raises
    an appropriate Key Error.

    Note: Dependencies always have strictly smaller level(=depth). This allows to
    iterate from higher level to lower level.
    """
    for level in sorted(ids_by_nesting_level, reverse=True):
        for transformation_id in ids_by_nesting_level[level]:
            if filter_map[transformation_id]:
                transformation = transformation_dict[transformation_id]
                direct_dependency_ids = get_direct_dependencies(transformation)
                for direct_dependency_id in direct_dependency_ids:
                    try:
                        filter_map[direct_dependency_id] = True
                    except KeyError as e:
                        if raise_on_missing_dependency:
                            raise KeyError(
                                f"Could not find dependency with id {direct_dependency_id} of "
                                f"trafo {transformation.name} with id {transformation_id} in"
                                " filter_map."
                            ) from e


def complete_trafo_filter_map(
    transformation_revisions: list[TransformationRevision],
    filter_params: FilterParams,
    ids_by_nesting_level: dict[int, list[UUID]],
    raise_on_missing_dependency: bool = False,
) -> dict[UUID, bool]:
    filter_map = basic_trafo_filter_map(transformation_revisions, filter_params)

    if filter_params.include_dependencies:
        update_filter_for_dependencies(
            filter_map,
            ids_by_nesting_level,
            {trafo.id: trafo for trafo in transformation_revisions},
            raise_on_missing_dependency=raise_on_missing_dependency,
        )
    # TODO: Should we also handle unused filter param?
    return filter_map


def filter_and_order_trafos(
    transformation_revisions: list[TransformationRevision],
    filter_params: FilterParams,
    raise_on_missing_dependency: bool = False,
) -> list[TransformationRevision]:
    """Filter trafos and order them for import

    This filters the given transformation_revisions using filter_params
    and returns them in the correct order for importing, i.e. all
    dependencies of a workflow occur before it.

    The resulting list then can be imported/put/updated one after another.
    """
    transformation_dict = {trafo_rev.id: trafo_rev for trafo_rev in transformation_revisions}
    ids_by_nesting_level = structure_ids_by_nesting_level(transformation_dict)

    # obtain filter map including dependency handling
    filter_map = complete_trafo_filter_map(
        transformation_revisions,
        filter_params,
        ids_by_nesting_level,
        raise_on_missing_dependency=raise_on_missing_dependency,
    )

    # apply filter and order by increasing level for importability
    filtered_and_ordered = []

    for level in sorted(ids_by_nesting_level):
        filtered_and_ordered += [
            transformation_dict[transformation_id]
            for transformation_id in ids_by_nesting_level[level]
            if filter_map[transformation_id]
        ]

    return filtered_and_ordered
