from typing import cast
from uuid import UUID

from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.persistence.models.workflow import WorkflowContent
from hetdesrun.utils import Type


def get_direct_dependencies(
    transformation_revision: TransformationRevision,
) -> list[UUID]:
    """Obtain the direct dependencies of a transformation revision

    A component has no direct dependencies. For a workflow, this returns
    a list containing all transformation_id 's of the operators of the workflow.

    The result does not include transitive dependencies, i.e. if a workflow has operators
    which are instances of workflows themselves, their dependencies are not included
    and so on.
    """
    if transformation_revision.type == Type.COMPONENT:
        return []

    # Type.WORKFLOW
    wf_content = cast(WorkflowContent, transformation_revision.content)
    return [operator.transformation_id for operator in wf_content.operators]
