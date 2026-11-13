"""Manage nestings of workflows

Workflows can contain operators which are instances of workflows themselves.
This allows arbitrary nesting. This module contains helper functions for identifying
this structure, including the order of components importing each other via import_comp.
"""

import logging
from uuid import UUID

from hetdesrun.component.code_utils import CodeParsingException, get_global_component_imports
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.persistence.models.workflow import WorkflowContent
from hetdesrun.utils import Type

logger = logging.getLogger(__name__)


class NestingLevelCycleDetected(ValueError):
    pass


class MissingReferencedTransformation(KeyError):
    pass


def nesting_level(
    transformation_id: UUID,
    transformation_dict: dict[UUID, TransformationRevision],
    level: int = 0,
    seen: set[UUID] | None = None,
    base_trafo_id: UUID | None = None,
) -> int:
    """Recursively determine nesting level for a transformation

    The trafo itself and all transformations that can occur at some point as dependency must
    be provided via transformation_dict.

    level, seen, base_trafo_id are for recursion only and should not be set by invocing calls
    from other code.

    Raises:
    * NestingLevelCycleDetected: If cycle is detected while traversing from transformation_id
      down into its operators
    * MissingReferencedTransformation: If a referred transformation (both the starting trafo or
      referred via operator) is not contained in the provided transformation_dict
    """

    if base_trafo_id is None:
        base_trafo_id = transformation_id  # setting starting trafo id
    if seen is None:
        seen = set()

    if transformation_id in seen:
        # raise in order to avoid infinite recursion
        msg = (
            f"Cycle detected while determining nesting level for {transformation_id}"
            f" at current level {level} while recursing with base trafo {base_trafo_id}"
        )
        logger.error(msg)
        raise NestingLevelCycleDetected(msg)

    seen.add(transformation_id)

    try:
        transformation = transformation_dict[transformation_id]
    except KeyError as e:
        msg = (
            f"Missing transformation revision with id {transformation_id} in provided trafo set"
            f" while determining nesting level at current level {level} while recursing from"
            f" base trafo {base_trafo_id}"
        )
        logger.error(msg)
        raise MissingReferencedTransformation from e

    if transformation.type == Type.COMPONENT:
        return level

    level = level + 1
    nextlevel = level
    if not isinstance(transformation.content, WorkflowContent):
        raise TypeError(f"Expected type workflow of trafo {transformation_id}")
    for operator in transformation.content.operators:
        if operator.type == Type.WORKFLOW:
            logger.info(
                "transformation %s contains workflow %s at nesting level %i",
                str(transformation_id),
                operator.transformation_id,
                level,
            )
            if not operator.transformation_id in transformation_dict:
                msg = (
                    f"Missing transformation revision with id {operator.transformation_id} in"
                    f" provided trafo set while determining nesting level at current level {level}"
                    f" and at transformation {transformation_id} referred by operator "
                    f" {operator.name} with id {operator.id}"
                    f" while recursing from"
                    f" base trafo {base_trafo_id}"
                )
                logger.error(msg)
                raise MissingReferencedTransformation(msg)

            nextlevel = max(
                nextlevel,
                nesting_level(
                    operator.transformation_id,
                    transformation_dict=transformation_dict,
                    level=level,
                    seen=seen.copy(),
                    base_trafo_id=base_trafo_id,
                ),
            )

    return nextlevel


def structure_ids_by_nesting_level(
    transformation_dict: dict[UUID, TransformationRevision],
) -> dict[int, list[UUID]]:
    """Get ensemble of transformation structured by nesting level

    This implicitely gives an ordering for importing: Trafos should be
    imported from lowest to highest level to always guarantee that their dependencies
    are already present in the database in order to ensure that the database constraints
    are fulfilled.

    Components have nesting level ("depth") 0.

    Workflows with only component operators have nesting level 1.

    Generally the nesting level of a workflow is:
        maximum(nesting levels of trafo revisions of its operators) + 1

    The components are ordered such that components imported by other components via import_comp
    come before them, see order_by_component_imports.

    Raises:
    * NestingLevelCycleDetected: If a dependency cycle is detected while recursively traversing
      from transformation_id down into its operators.
    * MissingReferencedTransformation: If a referred transformation (both the starting trafo or
      referred via operator) is not contained in the provided transformation_dict
    """

    ids_by_nesting_level: dict[int, list[UUID]] = {}
    for tr_id, tr in transformation_dict.items():
        level = nesting_level(tr_id, transformation_dict)
        if level not in ids_by_nesting_level:
            ids_by_nesting_level[level] = []
        ids_by_nesting_level[level].append(tr_id)
        logger.info(
            "%s %s has nesting level %i",
            tr.type.value,
            str(tr_id),
            level,
        )

    if 0 in ids_by_nesting_level:
        ids_by_nesting_level[0] = order_by_component_imports(
            ids_by_nesting_level[0], transformation_dict
        )

    return ids_by_nesting_level


def component_imports(transformation: TransformationRevision) -> list[UUID]:
    """The ids of the components a component imports via import_comp"""
    if transformation.type is not Type.COMPONENT or not isinstance(transformation.content, str):
        return []
    try:
        # the ids are strings, despite the type hint
        return [
            UUID(str(trafo_id)) for trafo_id in get_global_component_imports(transformation.content)
        ]
    except CodeParsingException, NotImplementedError:
        # reported when the component is stored
        return []


def order_by_component_imports(
    component_ids: list[UUID], transformation_dict: dict[UUID, TransformationRevision]
) -> list[UUID]:
    """Order components such that the components they import via import_comp come first

    A released component can only be stored if the components it imports are stored already.
    Apart from that, the order of the components is kept. Imported components which are not among
    the given ones and cycles of imports, which only draft components may have, are ignored.
    """
    ordered: list[UUID] = []
    visited: set[UUID] = set()
    given = set(component_ids)

    def add_with_imports(component_id: UUID) -> None:
        if component_id in visited:
            return
        visited.add(component_id)
        for imported_id in component_imports(transformation_dict[component_id]):
            if imported_id in given:
                add_with_imports(imported_id)
        ordered.append(component_id)

    for component_id in component_ids:
        add_with_imports(component_id)

    return ordered
