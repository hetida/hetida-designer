"""Storing transformation revisions like the backend and checking their nestings

See test_nesting_combinations.py.
"""

import random
from collections import defaultdict
from collections.abc import Iterable
from uuid import UUID

import pytest
from sqlalchemy import select

from hetdesrun.backend.execution import prepare_execution_input
from hetdesrun.models.execution import ExecByIdInput
from hetdesrun.models.wiring import WorkflowWiring
from hetdesrun.persistence.db_engine_and_session import get_session
from hetdesrun.persistence.dbmodels import NestingDBModel
from hetdesrun.persistence.dbservice.exceptions import DBIntegrityError, DBNestingCycleDetected
from hetdesrun.persistence.dbservice.revision import (
    delete_single_transformation_revision,
    filter_unused_transformation_ids,
    flag_deprecated_operators,
    select_containing_workflows,
    select_multiple_transformation_revisions,
    update_or_create_single_transformation_revision,
)
from hetdesrun.persistence.models.io import IOInterface
from hetdesrun.persistence.models.operator import Operator
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.persistence.models.workflow import WorkflowContent
from hetdesrun.trafoutils.upgrade_operators import upgrade_workflow_operator_in_place
from hetdesrun.utils import State, Type

# workflow_id, via_transformation_id, via_operator_id, depth, nested_transformation_id,
# nested_operator_id
Nesting = tuple[UUID, UUID, UUID, int, UUID, UUID]


def operators_by_workflow_id(
    trafos: Iterable[TransformationRevision],
) -> dict[UUID, list[Operator]]:
    return {
        trafo.id: trafo.content.operators
        for trafo in trafos
        if isinstance(trafo.content, WorkflowContent)
    }


def find_cycle(operators: dict[UUID, list[Operator]]) -> list[UUID] | None:
    """Workflows containing each other in a cycle, if there is one"""
    finished: set[UUID] = set()

    def visit(workflow_id: UUID, path: list[UUID]) -> list[UUID] | None:
        if workflow_id in path:
            return path[path.index(workflow_id) :] + [workflow_id]
        if workflow_id in finished or workflow_id not in operators:
            return None
        for operator in operators[workflow_id]:
            if (cycle := visit(operator.transformation_id, [*path, workflow_id])) is not None:
                return cycle
        finished.add(workflow_id)
        return None

    for workflow_id in operators:
        if (cycle := visit(workflow_id, [])) is not None:
            return cycle
    return None


def expected_nestings(operators: dict[UUID, list[Operator]]) -> set[Nesting]:
    """The nestings of all workflows as determined by their contents, which must be acyclic"""
    descendants_by_workflow_id: dict[UUID, set[tuple[int, UUID, UUID]]] = {}

    def descendants(workflow_id: UUID) -> set[tuple[int, UUID, UUID]]:
        if workflow_id not in descendants_by_workflow_id:
            result = set()
            for operator in operators.get(workflow_id, []):
                result.add((1, operator.transformation_id, operator.id))
                result.update(
                    (depth + 1, *descendant)
                    for depth, *descendant in descendants(operator.transformation_id)
                )
            descendants_by_workflow_id[workflow_id] = result
        return descendants_by_workflow_id[workflow_id]

    return {
        (workflow_id, operator.transformation_id, operator.id, depth, *descendant)
        for workflow_id, workflow_operators in operators.items()
        for operator in workflow_operators
        for depth, *descendant in [
            (1, operator.transformation_id, operator.id),
            *(
                (depth + 1, *descendant)
                for depth, *descendant in descendants(operator.transformation_id)
            ),
        ]
    }


def stored_nestings() -> set[Nesting]:
    with get_session()() as session:
        return {
            tuple(row)  # type: ignore[misc]
            for row in session.execute(
                select(
                    NestingDBModel.workflow_id,
                    NestingDBModel.via_transformation_id,
                    NestingDBModel.via_operator_id,
                    NestingDBModel.depth,
                    NestingDBModel.nested_transformation_id,
                    NestingDBModel.nested_operator_id,
                )
            )
        }


class NestingWorld:
    """Transformation revisions stored via the db services and checks of their nestings

    Ids are drawn from the random number generator, so that a seed determines everything.
    The contents of the stored transformation revisions are the ground truth.
    """

    def __init__(self, seed: int = 0) -> None:
        self.rng = random.Random(seed)  # noqa: S311
        self.log: list[str] = []
        self.counts: dict[str, int] = defaultdict(int)
        self.labels: dict[UUID, str] = {}

    def new_id(self) -> UUID:
        return UUID(int=self.rng.getrandbits(128), version=4)

    def label(self, trafo_id: UUID) -> str:
        return self.labels.get(trafo_id, str(trafo_id))

    def fail(self, message: str) -> None:
        operations = "\n".join(f"  {i + 1}. {entry}" for i, entry in enumerate(self.log))
        pytest.fail(f"{message}\n\nOperations:\n{operations}", pytrace=False)

    def trafos(self) -> dict[UUID, TransformationRevision]:
        return {trafo.id: trafo for trafo in select_multiple_transformation_revisions()}

    def get(self, trafo: TransformationRevision) -> TransformationRevision:
        return self.trafos()[trafo.id]

    # operations

    def _new_trafo(
        self, prefix: str, type_: Type, content: str | WorkflowContent
    ) -> TransformationRevision:
        self.counts[prefix] += 1
        return TransformationRevision(
            id=self.new_id(),
            revision_group_id=self.new_id(),
            name=f"{prefix}{self.counts[prefix]}",
            category="nestings",
            version_tag="1",
            type=type_,
            state=State.DRAFT,
            documentation="",
            content=content,
            io_interface=IOInterface(),
            test_wiring=WorkflowWiring(),
        )

    def operator(self, trafo: TransformationRevision) -> Operator:
        operator = trafo.to_operator()
        operator.id = self.new_id()
        return operator

    def store(
        self,
        trafo: TransformationRevision,
        description: str,
        allow_overwrite_released: bool = False,
    ) -> TransformationRevision | None:
        """Store like the backend, expecting a rejection exactly if it closes a cycle

        Returns None if it is rejected.
        """
        self.labels.setdefault(trafo.id, f"{trafo.name}@{trafo.version_tag}")
        description = description.format(label=self.label(trafo.id))
        trafos = self.trafos()
        previous = trafos.get(trafo.id)
        cycle = find_cycle(operators_by_workflow_id({**trafos, trafo.id: trafo}.values()))
        try:
            stored = update_or_create_single_transformation_revision(
                trafo, allow_overwrite_released=allow_overwrite_released
            )
        except DBNestingCycleDetected as error:
            rejection = str(error)
        else:
            rejection = None

        if rejection is not None:
            self.log.append(f"{description} -> rejected as cycle")
            if cycle is None:
                self.fail(f"{description} was rejected as cycle, but closes none: {rejection}")
            if self.trafos().get(trafo.id) != previous:
                self.fail(f"{description} was rejected as cycle, but changed the db")
            return None
        self.log.append(description)
        if cycle is not None:
            self.fail(
                f"{description} was stored, although it closes the cycle "
                + " > ".join(self.label(workflow_id) for workflow_id in cycle)
            )
        return stored

    def component(self, released: bool = True) -> TransformationRevision:
        trafo = self._new_trafo("C", Type.COMPONENT, "")
        if released:
            trafo.release()
        stored = self.store(trafo, "{label} = " + ("released " if released else "") + "component")
        assert stored is not None
        return stored

    def workflow(self, children: list[TransformationRevision]) -> TransformationRevision:
        trafo = self._new_trafo(
            "W",
            Type.WORKFLOW,
            WorkflowContent(operators=[self.operator(child) for child in children]),
        )
        stored = self.store(
            trafo,
            "{label} = workflow of [" + ", ".join(self.label(child.id) for child in children) + "]",
        )
        assert stored is not None
        return stored

    def new_revision(
        self, trafo: TransformationRevision, copy: bool = False
    ) -> TransformationRevision:
        """A new revision or copy as created by the frontend, keeping the operator ids"""
        trafos = self.trafos()
        if copy:
            prefix = "C" if trafo.type is Type.COMPONENT else "W"
            self.counts[prefix] += 1
            name, revision_group_id, version_tag = (
                f"{prefix}{self.counts[prefix]}",
                self.new_id(),
                "1",
            )
        else:
            name, revision_group_id = trafo.name, trafo.revision_group_id
            version_tag = str(
                max(
                    int(other.version_tag)
                    for other in trafos.values()
                    if other.revision_group_id == trafo.revision_group_id
                )
                + 1
            )
        new_trafo = TransformationRevision(
            **{
                **trafo.model_dump(),
                "id": self.new_id(),
                "revision_group_id": revision_group_id,
                "name": name,
                "version_tag": version_tag,
                "state": State.DRAFT,
                "released_timestamp": None,
                "disabled_timestamp": None,
                "release_wiring": None,
            }
        )
        stored = self.store(
            new_trafo,
            "{label} = " + ("copy" if copy else "new revision") + f" of {self.label(trafo.id)}",
        )
        assert stored is not None
        return stored

    def _store_operators(
        self,
        workflow: TransformationRevision,
        operators: list[Operator],
        description: str,
        allow_overwrite_released: bool = False,
    ) -> TransformationRevision | None:
        trafo = self.get(workflow)
        return self.store(
            TransformationRevision(
                **{**trafo.model_dump(), "content": WorkflowContent(operators=operators)}
            ),
            description,
            allow_overwrite_released=allow_overwrite_released,
        )

    def add_operator(
        self,
        workflow: TransformationRevision,
        child: TransformationRevision,
        allow_overwrite_released: bool = False,
    ) -> TransformationRevision | None:
        """Add an operator, to a released workflow like the deployment of base trafos"""
        return self._store_operators(
            workflow,
            [*self.get(workflow).content.operators, self.operator(child)],  # type: ignore[union-attr]
            f"add {self.label(child.id)} to "
            + ("released " if allow_overwrite_released else "")
            + "{label}",
            allow_overwrite_released=allow_overwrite_released,
        )

    def remove_operator(
        self, workflow: TransformationRevision, child: TransformationRevision
    ) -> TransformationRevision | None:
        """Remove one of the operators instantiating child"""
        operators = list(self.get(workflow).content.operators)  # type: ignore[union-attr]
        operators.remove(
            next(operator for operator in operators if operator.transformation_id == child.id)
        )
        return self._store_operators(
            workflow, operators, f"remove {self.label(child.id)} from " + "{label}"
        )

    def upgrade_operator(
        self,
        workflow: TransformationRevision,
        child: TransformationRevision,
        new_child: TransformationRevision,
    ) -> TransformationRevision | None:
        """Upgrade one of the operators instantiating child to new_child, keeping its id"""
        trafo = self.get(workflow)
        assert isinstance(trafo.content, WorkflowContent)
        operator = next(
            operator
            for operator in trafo.content.operators
            if operator.transformation_id == child.id
        )
        upgrade_workflow_operator_in_place(trafo, operator.id, operator, new_child)
        return self.store(
            trafo,
            f"upgrade {self.label(child.id)} to {self.label(new_child.id)} in " + "{label}",
        )

    def resave(self, workflow: TransformationRevision) -> TransformationRevision | None:
        return self.store(self.get(workflow), "store {label} again")

    def release(self, trafo: TransformationRevision) -> TransformationRevision:
        trafos = self.trafos()
        trafo = trafos[trafo.id]
        if isinstance(trafo.content, WorkflowContent) and any(
            operator.state is State.DRAFT for operator in trafo.content.operators
        ):
            # Operators instantiating DRAFTs which have been released since must show their
            # current state before releasing, which keeps the stored content.
            for operator in trafo.content.operators:
                if operator.state is State.DRAFT:
                    operator.state = trafos[operator.transformation_id].state
            stored = self.store(trafo, "update the operator states of {label}")
            assert stored is not None
            trafo = stored
        trafo.release()
        stored = self.store(trafo, "release {label}")
        assert stored is not None
        return stored

    def deprecate(self, trafo: TransformationRevision) -> TransformationRevision:
        trafo = self.get(trafo)
        trafo.deprecate()
        stored = self.store(trafo, "deprecate {label}")
        assert stored is not None
        return stored

    def delete(self, trafo: TransformationRevision) -> None:
        """Delete a DRAFT, expecting a refusal exactly if a workflow refers to it"""
        referring = sorted(
            self.label(workflow_id)
            for workflow_id, operators in operators_by_workflow_id(self.trafos().values()).items()
            if any(operator.transformation_id == trafo.id for operator in operators)
        )
        description = f"delete {self.label(trafo.id)}"
        try:
            delete_single_transformation_revision(trafo.id)
        except DBIntegrityError:
            deleted = False
        else:
            deleted = True

        self.log.append(description if deleted else f"{description} -> refused")
        if deleted and len(referring) > 0:
            self.fail(f"{description} was deleted, although {referring} refer to it")
        if not deleted and len(referring) == 0:
            self.fail(f"{description} was refused, although no workflow refers to it")

    # checks

    def check(self) -> None:
        trafos = self.trafos()
        operators = operators_by_workflow_id(trafos.values())
        if (cycle := find_cycle(operators)) is not None:
            self.fail(
                "The stored workflows contain the cycle "
                + " > ".join(self.label(workflow_id) for workflow_id in cycle)
            )
        expected = expected_nestings(operators)

        violations = [
            *self.check_nestings(expected),
            *self.check_execution(trafos),
            *self.check_containing_workflows(trafos, expected),
            *self.check_unused(trafos, expected),
            *self.check_deprecation_flags(trafos, expected),
        ]
        if len(violations) > 0:
            self.fail("\n".join(violations))

    def describe(self, nesting: Nesting) -> str:
        workflow_id, via_transformation_id, via_operator_id, depth, nested_id, operator_id = nesting
        return (
            f"{self.label(workflow_id)} via {self.label(via_transformation_id)}"
            f" (operator {str(via_operator_id)[:8]}) at depth {depth}:"
            f" {self.label(nested_id)} (operator {str(operator_id)[:8]})"
        )

    def check_nestings(self, expected: set[Nesting]) -> list[str]:
        stored = stored_nestings()
        return [
            *(f"Missing nesting {self.describe(nesting)}" for nesting in sorted(expected - stored)),
            *(
                f"Unexpected nesting {self.describe(nesting)}"
                for nesting in sorted(stored - expected)
            ),
        ]

    def check_execution(self, trafos: dict[UUID, TransformationRevision]) -> list[str]:
        violations = []
        for trafo in trafos.values():
            if trafo.type is Type.WORKFLOW:
                try:
                    prepare_execution_input(ExecByIdInput(id=trafo.id))
                except Exception as error:  # noqa: BLE001
                    violations.append(
                        f"Preparing the execution of {self.label(trafo.id)} failed: {error!r}"
                    )
        return violations

    def check_containing_workflows(
        self, trafos: dict[UUID, TransformationRevision], expected: set[Nesting]
    ) -> list[str]:
        expected_by_id: dict[UUID, dict[UUID, tuple[set[UUID], set[UUID]]]] = defaultdict(dict)
        for workflow_id, via_transformation_id, via_operator_id, depth, nested_id, _ in expected:
            direct, via = expected_by_id[nested_id].setdefault(workflow_id, (set(), set()))
            if depth == 1:
                direct.add(via_operator_id)
            else:
                via.add(via_transformation_id)

        violations = []
        for trafo_id in trafos:
            containing = {
                workflow.id: (set(workflow.direct_operator_ids), set(workflow.via_workflow_ids))
                for workflow in select_containing_workflows(trafo_id)
            }
            if containing != expected_by_id[trafo_id]:
                violations.append(
                    f"Containing workflows of {self.label(trafo_id)} are"
                    f" {sorted(map(self.label, containing))} instead of"
                    f" {sorted(map(self.label, expected_by_id[trafo_id]))}"
                    " or differ in their operators or the workflows they contain it via"
                )
        return violations

    def check_unused(
        self, trafos: dict[UUID, TransformationRevision], expected: set[Nesting]
    ) -> list[str]:
        used = {
            nested_id
            for workflow_id, _, _, _, nested_id, _ in expected
            if trafos[workflow_id].state is not State.DISABLED
        }
        unused = filter_unused_transformation_ids(list(trafos))
        return [
            f"{self.label(trafo_id)} is {'unused' if trafo_id in unused else 'used'},"
            f" but should be {'used' if trafo_id in used else 'unused'}"
            for trafo_id in trafos
            if (trafo_id in unused) == (trafo_id in used)
        ]

    def check_deprecation_flags(
        self, trafos: dict[UUID, TransformationRevision], expected: set[Nesting]
    ) -> list[str]:
        """Exactly the operators containing a deprecated trafo at any depth are flagged

        They are flagged when providing the workflows, e.g. to the frontend, and the stored
        workflows contain no flags.
        """
        expected_flagged = {
            (workflow_id, via_operator_id)
            for workflow_id, _, via_operator_id, _, nested_id, _ in expected
            if trafos[nested_id].state is State.DISABLED
        }
        provided = self.trafos()
        flag_deprecated_operators(provided.values())

        violations = []
        for workflow_id, operators in operators_by_workflow_id(trafos.values()).items():
            provided_operators = {
                operator.id: operator
                for operator in provided[workflow_id].content.operators  # type: ignore[union-attr]
            }
            for operator in operators:
                description = (
                    f"The operator {str(operator.id)[:8]} instantiating"
                    f" {self.label(operator.transformation_id)} in {self.label(workflow_id)}"
                )
                if operator.state is State.DISABLED:
                    violations.append(f"{description} is stored flagged as deprecated")
                provided_state = provided_operators[operator.id].state
                if (workflow_id, operator.id) in expected_flagged:
                    if provided_state is not State.DISABLED:
                        violations.append(
                            f"{description} is not flagged as deprecated, although it"
                            " contains a deprecated transformation revision"
                        )
                elif provided_state is not operator.state:
                    violations.append(
                        f"{description} is provided as {provided_state.value} instead of"
                        f" {operator.state.value}"
                    )
        return violations
