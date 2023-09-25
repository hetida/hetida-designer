import logging
from uuid import UUID

from hetdesrun.exportimport.importing import import_transformations
from hetdesrun.exportimport.utils import (
    delete_transformation_revisions,
    deprecate_all_but_latest_in_group,
    get_transformation_revisions,
    update_or_create_transformation_revision,
)
from hetdesrun.persistence.models.workflow import WorkflowContent
from hetdesrun.trafoutils.filter.params import FilterParams
from hetdesrun.utils import State, Type

logger = logging.getLogger(__name__)


def deprecate_all_but_latest_per_group(directly_in_db: bool = False) -> None:
    tr_list = get_transformation_revisions(
        params=FilterParams(state=State.RELEASED, include_dependencies=False),
        directly_from_db=directly_in_db,
    )

    revision_group_ids: set[UUID] = set()

    for tr in tr_list:
        revision_group_ids.add(tr.revision_group_id)

    for revision_group_id in revision_group_ids:
        deprecate_all_but_latest_in_group(
            revision_group_id, directly_in_db=directly_in_db
        )


def correct_output_connector_name(directly_in_db: bool = False) -> None:
    """Correct output connector name.

    Update the connector_name attribute of outputs to the correct value if it was incorrectly set
    to the default value "connector_name" due to a faulty implementation in the
    get_operator_and_connector_name function. This function is used to transform
    WorklfowRevisionFrontendDto instances to TransformationRevision instances. The incorrect
    implementation existed from release 0.7.1 up to and including release 0.8.8.
    """
    tr_list = get_transformation_revisions(
        params=FilterParams(type=Type.WORKFLOW, include_dependencies=False),
        directly_from_db=directly_in_db,
    )

    for tr in tr_list:
        assert isinstance(tr.content, WorkflowContent)  # noqa: S101
        applicable = False
        if len(tr.content.outputs) != 0:
            for output in tr.content.outputs:
                if output.connector_name == "connector_name":
                    applicable = True
                    for operator in tr.content.operators:
                        if operator.id == output.operator_id:
                            for output_connector in operator.outputs:
                                if output_connector.id == output.connector_id:
                                    assert (  # noqa: S101
                                        output_connector.name is not None
                                    )
                                    output.connector_name = output_connector.name
        if applicable:
            update_or_create_transformation_revision(tr, directly_in_db=directly_in_db)


def delete_drafts(directly_in_db: bool = False) -> None:
    tr_list = get_transformation_revisions(
        params=FilterParams(state=State.DRAFT, include_dependencies=False),
        directly_from_db=directly_in_db,
    )

    delete_transformation_revisions(tr_list, directly_in_db=directly_in_db)


def delete_unused_deprecated(directly_in_db: bool = False) -> None:
    tr_list = get_transformation_revisions(
        params=FilterParams(
            state=State.DISABLED, include_dependencies=False, unused=True
        ),
        directly_from_db=directly_in_db,
    )

    delete_transformation_revisions(tr_list, directly_in_db=directly_in_db)


def delete_all_and_refill(directly_in_db: bool = False) -> None:
    tr_list = get_transformation_revisions(directly_from_db=directly_in_db)

    delete_transformation_revisions(tr_list, directly_in_db=directly_in_db)

    import_transformations("./transformations", directly_into_db=directly_in_db)
