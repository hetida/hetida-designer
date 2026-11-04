"""Checks of the nestings with diverse and random nesting combinations

The nestings (see update_nesting) store for each workflow all operators nested in it at any
depth, together with their transformation revisions. They are derived data: The contents of
the stored workflows determine them. These tests store transformation revisions via the db
services like the backend does for requests of the frontend, e.g. new revisions and copies
keeping the operator ids, upgrades of operators, releases, deprecations and deletions, as
well as for overwriting released workflows like the deployment of the base trafos. After
each operation they compare the nestings and everything relying on them with what the
contents of all stored workflows determine:

* the nestings themselves
* preparing the execution of each workflow
* the workflows containing each transformation revision
* the unused transformation revisions
* the deprecation flags of operators containing deprecated transformation revisions
* rejecting exactly the workflows closing a cycle when storing them
* refusing exactly the deletion of transformation revisions referenced by a workflow

The components have neither inputs nor outputs, so that workflows can be released without
links.

Run with --check-nestings (or --extended). The random sequences use --nesting-seeds seeds
(default 30) with --nesting-steps operations each (default 40), a single one e.g. via
-k "seed-7". A failure lists the operations so far.
"""

import pytest

from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.persistence.models.workflow import WorkflowContent
from hetdesrun.utils import State, Type
from tests.persistence.nesting_world import NestingWorld, stored_nestings

pytestmark = pytest.mark.nestings


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "seed" in metafunc.fixturenames:
        seeds = range(metafunc.config.getoption("nesting_seeds"))
        metafunc.parametrize("seed", seeds, ids=[f"seed-{seed}" for seed in seeds])


@pytest.fixture()
def world(mocked_clean_test_db_session) -> NestingWorld:
    return NestingWorld()


# scenarios


def test_same_workflow_twice_two_levels_down(world):
    component = world.component()
    inner = world.workflow([component])
    middle = world.workflow([inner, inner])
    world.workflow([middle])
    world.check()


def test_two_revisions_with_upgraded_operator_two_levels_down(world):
    component = world.component()
    inner = world.workflow([component])
    inner_new = world.new_revision(inner)
    world.upgrade_operator(inner_new, component, world.new_revision(component))
    middle = world.workflow([inner, inner_new])
    world.workflow([middle])
    world.check()


def test_copies_and_revisions_side_by_side(world):
    first, second = world.component(), world.component()
    inner = world.workflow([first, second, first])
    copy = world.new_revision(inner, copy=True)
    world.upgrade_operator(copy, second, first)
    revision = world.new_revision(inner)
    middle = world.workflow([inner, copy, revision, copy])
    top = world.workflow([middle, inner, middle])
    world.workflow([top, world.new_revision(top, copy=True)])
    world.check()


def test_diamond(world):
    component = world.component()
    bottom = world.workflow([component])
    left, right = world.workflow([bottom]), world.workflow([bottom, component])
    world.workflow([left, right])
    world.check()


def test_deep_chain(world):
    workflow = world.workflow([world.component()])
    for _ in range(6):
        workflow = world.workflow([workflow, workflow])
    world.check()


def test_cycles_are_rejected(world):
    component = world.component(released=False)
    bottom = world.workflow([component])
    middle = world.workflow([bottom])
    top = world.workflow([middle])
    assert world.add_operator(bottom, bottom) is None
    assert world.add_operator(bottom, top) is None
    assert world.add_operator(middle, top) is None
    world.check()


def test_deletion(world):
    component = world.component(released=False)
    unused = world.component(released=False)
    inner = world.workflow([component])
    middle = world.workflow([inner])
    world.delete(component)
    world.delete(inner)
    world.delete(unused)
    world.remove_operator(middle, inner)
    world.delete(inner)
    world.check()


def test_deprecation_is_passed_on(world):
    component = world.component()
    inner = world.release(world.workflow([component]))
    middle = world.release(world.workflow([inner, inner]))
    world.workflow([middle])
    world.deprecate(component)
    world.check()


# random sequences of operations


def random_operation(world: NestingWorld) -> None:  # noqa: PLR0915
    rng = world.rng
    trafos = sorted(world.trafos().values(), key=lambda trafo: (trafo.name, int(trafo.version_tag)))
    usable = [trafo for trafo in trafos if trafo.state is not State.DISABLED]
    workflows = [trafo for trafo in trafos if trafo.type is Type.WORKFLOW]
    drafts = [trafo for trafo in trafos if trafo.state is State.DRAFT]
    draft_workflows = [trafo for trafo in drafts if trafo.type is Type.WORKFLOW]
    by_id = {trafo.id: trafo for trafo in trafos}

    def children(workflow: TransformationRevision) -> list[TransformationRevision]:
        assert isinstance(workflow.content, WorkflowContent)
        return [by_id[operator.transformation_id] for operator in workflow.content.operators]

    def other_revisions(trafo: TransformationRevision) -> list[TransformationRevision]:
        return [
            other
            for other in usable
            if other.revision_group_id == trafo.revision_group_id and other.id != trafo.id
        ]

    def related(trafo: TransformationRevision) -> TransformationRevision:
        """Often the same transformation revision or another revision of it"""
        if rng.random() < 0.3:
            return trafo
        if rng.random() < 0.3 and len(other_revisions(trafo)) > 0:
            return rng.choice(other_revisions(trafo))
        return random_child()

    def random_child() -> TransformationRevision:
        """Preferably a workflow, so that the nesting gets deeper"""
        usable_workflows = [trafo for trafo in usable if trafo.type is Type.WORKFLOW]
        if len(usable_workflows) > 0 and rng.random() < 0.6:
            return rng.choice(usable_workflows)
        return rng.choice(usable)

    def random_children() -> list[TransformationRevision]:
        result = [random_child()]
        for _ in range(rng.randint(0, 3)):
            result.append(related(result[-1]))
        return result

    def add_operator() -> None:
        workflow = rng.choice(draft_workflows)
        containing = [
            by_id[nesting[0]] for nesting in stored_nestings() if nesting[4] == workflow.id
        ]
        if rng.random() < 0.2 and len(containing) > 0:
            # try to close a cycle
            child = rng.choice([workflow, *containing])
        elif len(children(workflow)) > 0:
            child = related(rng.choice(children(workflow)))
        else:
            child = random_child()
        world.add_operator(workflow, child)

    def add_operator_to_released() -> None:
        """Like the deployment of base trafos, overwriting released ones"""
        workflow = rng.choice(released_workflows)
        world.add_operator(
            workflow,
            rng.choice([trafo for trafo in usable if trafo.state is State.RELEASED]),
            allow_overwrite_released=True,
        )

    def remove_operator() -> None:
        workflow = rng.choice([workflow for workflow in draft_workflows if children(workflow)])
        world.remove_operator(workflow, rng.choice(children(workflow)))

    def upgrade_operator() -> None:
        workflow, child = rng.choice(upgradable)
        world.upgrade_operator(workflow, child, rng.choice(other_revisions(child)))

    def new_revision() -> None:
        """New revision, a workflow often with an upgraded operator like after "+1" """
        revision = world.new_revision(rng.choice(trafos))
        candidates = [
            child
            for child in (children(revision) if revision.type is Type.WORKFLOW else [])
            if len(other_revisions(child)) > 0
        ]
        if len(candidates) > 0 and rng.random() < 0.7:
            child = rng.choice(candidates)
            world.upgrade_operator(revision, child, rng.choice(other_revisions(child)))

    upgradable = sorted(
        {
            (workflow.id, child.id): (workflow, child)
            for workflow in draft_workflows
            for child in children(workflow)
            if len(other_revisions(child)) > 0
        }.values(),
        key=lambda pair: (pair[0].name, int(pair[0].version_tag), pair[1].name),
    )
    releasable = [
        trafo
        for trafo in drafts
        if trafo.type is Type.COMPONENT
        or all(child.state is not State.DRAFT for child in children(trafo))
    ]
    released = [trafo for trafo in trafos if trafo.state is State.RELEASED]
    released_workflows = [trafo for trafo in released if trafo.type is Type.WORKFLOW]

    operations = [
        (4, True, lambda: world.component(released=rng.random() < 0.7)),
        (4, len(usable) > 0, lambda: world.workflow(random_children())),
        (3, len(trafos) > 0, new_revision),
        (1, len(workflows) > 0, lambda: world.new_revision(rng.choice(workflows), copy=True)),
        (5, len(draft_workflows) > 0 and len(usable) > 0, add_operator),
        (1, len(released_workflows) > 0, add_operator_to_released),
        (2, any(children(workflow) for workflow in draft_workflows), remove_operator),
        (4, len(upgradable) > 0, upgrade_operator),
        (3, len(releasable) > 0, lambda: world.release(rng.choice(releasable))),
        (1, len(released) > 0, lambda: world.deprecate(rng.choice(released))),
        (2, len(drafts) > 0, lambda: world.delete(rng.choice(drafts))),
        (1, len(draft_workflows) > 0, lambda: world.resave(rng.choice(draft_workflows))),
    ]
    applicable = [(weight, operation) for weight, condition, operation in operations if condition]
    rng.choices(
        [operation for _, operation in applicable],
        weights=[weight for weight, _ in applicable],
    )[0]()


def test_random_operations(mocked_clean_test_db_session, request, seed):
    world = NestingWorld(seed)
    for _ in range(request.config.getoption("nesting_steps")):
        random_operation(world)
        world.check()
