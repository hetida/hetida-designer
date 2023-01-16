"""Manage nestings of workflows

Workflows can contain operators which are instances of workflows themselves.
This allows arbitrary nesting. This module contains helper functions for identifying
this structure.
"""

import logging
from typing import Dict, List
from uuid import UUID

from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.persistence.models.workflow import WorkflowContent
from hetdesrun.utils import Type

logger = logging.getLogger(__name__)


def structure_ids_by_nesting_level(
    transformation_dict: Dict[UUID, TransformationRevision]
) -> Dict[int, List[UUID]]:
    """Get ensemble of transformation structured by nesting level

    Components have nesting level ("depth") 0.

    Workflows with only component operators have nesting level 1.

    Generally the nesting level of a workflow is the maximum nesting level of the
    trafo revisions of its operators + 1.
    """

    def nesting_level(
        transformation_id: UUID,
        level: int = 0,
    ) -> int:
        transformation = transformation_dict[transformation_id]

        if transformation.type == Type.COMPONENT:
            return level

        level = level + 1
        nextlevel = level
        assert isinstance(transformation.content, WorkflowContent)
        for operator in transformation.content.operators:
            if operator.type == Type.WORKFLOW:
                logger.info(
                    "transformation %s contains workflow %s at nesting level %i",
                    str(transformation_id),
                    operator.transformation_id,
                    level,
                )
                nextlevel = max(
                    nextlevel, nesting_level(operator.transformation_id, level=level)
                )

        return nextlevel

    ids_by_nesting_level: Dict[int, List[UUID]] = {}
    for tr_id, tr in transformation_dict.items():
        level = nesting_level(tr_id)
        if level not in ids_by_nesting_level:
            ids_by_nesting_level[level] = []
        ids_by_nesting_level[level].append(tr_id)
        logger.info(
            "%s %s has nesting level %i",
            tr.type.value,
            str(tr_id),
            level,
        )

    return ids_by_nesting_level
