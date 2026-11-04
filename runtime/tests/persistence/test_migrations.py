import os
from collections.abc import Generator
from pathlib import Path
from unittest import mock
from uuid import UUID, uuid4

import pytest
import sqlalchemy as sa
from alembic.config import Config
from sqlalchemy.future.engine import Engine

from alembic import command
from hetdesrun.persistence.db_engine_and_session import get_db_engine, get_session, sessionmaker
from hetdesrun.persistence.dbmodels import Descendant, NestingDBModel
from hetdesrun.persistence.dbservice.nesting import find_all_nested_transformation_revisions
from hetdesrun.persistence.dbservice.revision import (
    add_tr,
    get_all_nested_transformation_revisions,
    update_tr,
)
from hetdesrun.persistence.models.workflow import WorkflowContent
from hetdesrun.trafoutils.trafo_collection import TrafoCollection
from hetdesrun.trafoutils.upgrade_operators import upgrade_workflow_operator_in_place
from hetdesrun.trafoutils.workflow_construction import WorkflowConstructor
from hetdesrun.utils import State
from tests.persistence.nesting_world import NestingWorld


def drop_all_tables(engine: Engine) -> None:
    metadata = sa.MetaData()
    metadata.reflect(engine)
    metadata.drop_all(engine)
    if engine.dialect.name == "postgresql":
        # the enum types created by the migrations are not dropped with the reflected tables
        with engine.begin() as connection:
            for enum in sa.inspect(connection).get_enums():
                connection.execute(sa.text(f'DROP TYPE "{enum["name"]}"'))


@pytest.fixture()
def migration_db_engine(
    use_in_memory_db: bool, test_db_engine: Engine, tmp_path: Path
) -> Generator[Engine]:
    """Empty db to run the migrations on, also used by the db services

    A SQLite file, with --dont-use-in-memory-db the configured db, e.g. postgres.
    """
    engine = (
        get_db_engine(override_db_url=f"sqlite+pysqlite:///{tmp_path / 'hd.sqlite'}")
        if use_in_memory_db
        else test_db_engine
    )
    drop_all_tables(engine)
    with (
        mock.patch(
            "hetdesrun.persistence.db_engine_and_session.get_db_engine", return_value=engine
        ),
        mock.patch("hetdesrun.persistence.db_engine_and_session.Session", sessionmaker(engine)),
    ):
        yield engine
    drop_all_tables(engine)


def alembic_config() -> Config:
    config = Config()
    config.set_main_option("script_location", "alembic")
    return config


def nestings_primary_key(engine: Engine) -> list[str]:
    return sa.inspect(engine).get_pk_constraint("nestings")["constrained_columns"]


def descendants(workflow_id: UUID) -> set[Descendant]:
    with get_session()() as session:
        return set(find_all_nested_transformation_revisions(session, workflow_id))


def test_nested_transformation_in_nestings_primary_key(migration_db_engine):
    command.upgrade(alembic_config(), "c4d81f6a2b90")
    assert nestings_primary_key(migration_db_engine) == [
        "workflow_id",
        "via_operator_id",
        "depth",
        "nested_operator_id",
    ]

    # Top contains Middle, which contains Inner and its new revision, in which the operator
    # is upgraded, see test_storing_workflow_with_two_revisions_of_a_sub_workflow_two_levels_down
    connectors_dir = os.path.join("transformations", "components", "connectors")
    with TrafoCollection(save_to_db=True) as tc:
        pt_string = tc.add_from_json_file(
            os.path.join(
                connectors_dir, "pass-through-string_100_2b1b474f-ddf5-1f4d-fec4-17ef9122112b.json"
            )
        )
        pt_string_new = tc.add(
            pt_string.model_copy(update={"id": uuid4(), "version_tag": "1.0.1"}, deep=True)
        )
        with WorkflowConstructor(trafo_collector=tc, name="Inner", version_tag="1.0.0") as inner:
            inner_op = inner.op(pt_string)
        inner_new = inner.result.model_copy(
            update={"id": uuid4(), "version_tag": "1.0.1"}, deep=True
        )
        assert isinstance(inner_new.content, WorkflowContent)
        upgrade_workflow_operator_in_place(
            inner_new, inner_op.operator.id, inner_new.content.operators[0], pt_string_new
        )
        tc.add(inner_new)
        with WorkflowConstructor(trafo_collector=tc, name="Middle", version_tag="1.0.0") as middle:
            middle_op = middle.op(inner.result)
            middle_op_new = middle.op(inner_new)
    with WorkflowConstructor(
        trafo_collector=TrafoCollection(), name="Top", version_tag="1.0.0"
    ) as top:
        top_op = top.op(middle.result)

    # store Top with its nestings as up to release 0.14.0: one of the nestings of the
    # upgraded operator via Inner and its new revision is lost
    descendants_of_top_before = {
        Descendant(1, middle.result.id, top_op.operator.id),
        Descendant(2, inner.result.id, middle_op.operator.id),
        Descendant(2, inner_new.id, middle_op_new.operator.id),
        Descendant(3, pt_string_new.id, inner_op.operator.id),
    }
    with get_session()() as session, session.begin():
        add_tr(session, top.result)
        session.add_all(
            NestingDBModel(
                workflow_id=top.result.id,
                via_transformation_id=middle.result.id,
                via_operator_id=top_op.operator.id,
                depth=descendant.depth,
                nested_transformation_id=descendant.transformation_id,
                nested_operator_id=descendant.operator_id,
            )
            for descendant in descendants_of_top_before
        )
    descendants_of_middle = descendants(middle.result.id)

    command.upgrade(alembic_config(), "ad713bfdec0f")

    assert nestings_primary_key(migration_db_engine) == [
        "workflow_id",
        "via_operator_id",
        "depth",
        "nested_transformation_id",
        "nested_operator_id",
    ]
    lost_descendant = Descendant(3, pt_string.id, inner_op.operator.id)
    assert descendants(top.result.id) == {*descendants_of_top_before, lost_descendant}
    assert descendants(middle.result.id) == descendants_of_middle
    assert set(get_all_nested_transformation_revisions(top.result, allow_caching=False)) == {
        middle.result.id,
        inner.result.id,
        inner_new.id,
        pt_string.id,
        pt_string_new.id,
    }

    command.downgrade(alembic_config(), "c4d81f6a2b90")

    assert nestings_primary_key(migration_db_engine) == [
        "workflow_id",
        "via_operator_id",
        "depth",
        "nested_operator_id",
    ]
    # only one of the nestings differing only in their nested transformation revision is kept
    descendants_of_top_downgraded = descendants(top.result.id)
    assert len(descendants_of_top_downgraded) == 4
    assert descendants_of_top_downgraded <= {*descendants_of_top_before, lost_descendant}
    assert descendants(middle.result.id) == descendants_of_middle


def test_deprecation_flags_of_operators_are_removed(migration_db_engine):
    command.upgrade(alembic_config(), "ad713bfdec0f")

    world = NestingWorld()
    component = world.component()
    draft = world.workflow([world.component()])
    released = world.release(world.workflow([component]))
    workflow = world.workflow([component, draft, released])
    world.deprecate(component)

    # flags as stored by previous versions, including an outdated one of the operator
    # instantiating the DRAFT, which contains no deprecated transformation revision
    for trafo in (released, workflow):
        stored = world.get(trafo)
        assert isinstance(stored.content, WorkflowContent)
        for operator in stored.content.operators:
            operator.state = State.DISABLED
            operator.name = operator.name.removeprefix("(DRAFT) ")
        with get_session()() as session, session.begin():
            update_tr(session, stored)

    command.upgrade(alembic_config(), "2a99b886851b")

    transformation_revisions = sa.table(
        "transformation_revisions", sa.column("workflow_content", sa.JSON())
    )
    with migration_db_engine.connect() as connection:
        stored_operators = {
            operator["transformation_id"]: (operator["state"], operator["name"])
            for content in connection.execute(
                sa.select(transformation_revisions.c.workflow_content)
            ).scalars()
            if content is not None
            for operator in content["operators"]
        }
    assert stored_operators[str(component.id)] == ("RELEASED", component.name)
    assert stored_operators[str(draft.id)] == ("DRAFT", f"(DRAFT) {draft.name}")
    assert stored_operators[str(released.id)] == ("RELEASED", released.name)
    # the operators instantiating the deprecated component and the released workflow
    # containing it are flagged when providing the workflows
    world.check()
