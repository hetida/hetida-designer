"""Tests for selecting the latest / highest revision of revision groups"""

import datetime
import json
import os
from unittest import mock
from uuid import UUID

import pytest
from fastapi import HTTPException, status

from hetdesrun.models.revision_selection import RevisionSelection
from hetdesrun.models.wiring import WorkflowWiring
from hetdesrun.persistence.dbservice.exceptions import DBNotFoundError
from hetdesrun.persistence.dbservice.revision import (
    RevisionSelectionRow,
    store_single_transformation_revision,
)
from hetdesrun.persistence.models.io import IOInterface
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.persistence.models.workflow import WorkflowContent
from hetdesrun.trafoutils.io.load import load_json
from hetdesrun.trafoutils.trafo_collection import TrafoCollection
from hetdesrun.trafoutils.upgrade_operators import upgrade_operators_in_workflow
from hetdesrun.trafoutils.versioning import (
    pick_revision_ids_per_group,
    select_revision_id_of_group,
    select_revision_ids_per_group,
)
from hetdesrun.trafoutils.workflow_construction import WorkflowConstructor
from hetdesrun.utils import State, Type, get_uuid_from_seed

GROUP_A = get_uuid_from_seed("revision group alpha")
GROUP_B = get_uuid_from_seed("revision group beta")
GROUP_C = get_uuid_from_seed("revision group charlie")
GROUP_D = get_uuid_from_seed("revision group delta")
GROUP_E = get_uuid_from_seed("revision group echo")


def day(day_of_month: int) -> datetime.datetime:
    return datetime.datetime(2025, 1, day_of_month, tzinfo=datetime.UTC)


def trafo_id(seed: str) -> UUID:
    return get_uuid_from_seed("revision " + seed)


def trafo(
    seed: str,
    revision_group_id: UUID,
    version_tag: str,
    state: State = State.RELEASED,
    released: datetime.datetime | None = None,
    name: str = "Alpha",
    category: str = "Cat/A",
    type_: Type = Type.COMPONENT,
) -> TransformationRevision:
    return TransformationRevision(
        id=trafo_id(seed),
        revision_group_id=revision_group_id,
        name=name,
        description="",
        category=category,
        version_tag=version_tag,
        state=state,
        type=type_,
        content="code" if type_ is Type.COMPONENT else WorkflowContent(),
        io_interface=IOInterface(),
        test_wiring=WorkflowWiring(),
        documentation="",
        released_timestamp=released,
        disabled_timestamp=released + datetime.timedelta(hours=1)
        if state is State.DISABLED and released is not None
        else None,
    )


STORED_TRAFOS = [
    # Alpha: hotfix 1.0.1 is released after 2.0.0, so latest and highest differ
    trafo("a 1.0.0", GROUP_A, "1.0.0", released=day(1)),
    trafo("a 2.0.0", GROUP_A, "2.0.0", released=day(2)),
    trafo("a 1.0.1", GROUP_A, "1.0.1", released=day(3)),
    trafo("a 3.0.0", GROUP_A, "3.0.0", state=State.DISABLED, released=day(4)),
    trafo("a 4.0.0", GROUP_A, "4.0.0", state=State.DRAFT),
    # Beta: released revision has no semantic version tag
    trafo(
        "b custom",
        GROUP_B,
        "custom",
        released=day(1),
        name="Beta",
        category="Cat/B",
        type_=Type.WORKFLOW,
    ),
    trafo(
        "b 1.0.0",
        GROUP_B,
        "1.0.0",
        state=State.DRAFT,
        name="Beta",
        category="Cat/B",
        type_=Type.WORKFLOW,
    ),
    # Charlie: category changed between revisions
    trafo("c 1.0.0", GROUP_C, "1.0.0", released=day(1), name="Charlie", category="Cat/A"),
    trafo("c 1.1.0", GROUP_C, "1.1.0", released=day(2), name="Charlie", category="Cat/C"),
    # Delta: only a draft
    trafo("d 0.1.0", GROUP_D, "0.1.0", state=State.DRAFT, name="Delta", category="Cat/D"),
    # Echo: two revisions released at the same time with versions of the same precedence
    trafo("e 1.0.0", GROUP_E, "1.0.0", released=day(1), name="Echo", category="Cat/E"),
    trafo("e 1.0.0+build", GROUP_E, "1.0.0+build", released=day(1), name="Echo", category="Cat/E"),
]

# both for latest and highest the tie of Echo is broken by the id
ECHO_WINNER = max(["e 1.0.0", "e 1.0.0+build"], key=trafo_id)


@pytest.fixture()
def stored_revision_groups(mocked_clean_test_db_session):
    for tr in STORED_TRAFOS:
        store_single_transformation_revision(tr)


# Pure selection logic


def row(
    seed: str,
    version_tag: str,
    released: datetime.datetime | None,
    revision_group_id: UUID = GROUP_A,
) -> RevisionSelectionRow:
    return RevisionSelectionRow(trafo_id(seed), revision_group_id, version_tag, released)


def test_pick_latest_by_release_timestamp():
    rows = [
        row("2.0.0", "2.0.0", day(2)),
        row("1.0.1", "1.0.1", day(3)),
        row("custom", "custom", day(1)),
        row("draft", "3.0.0", None),
    ]
    assert pick_revision_ids_per_group(rows, RevisionSelection.LATEST) == {
        GROUP_A: trafo_id("1.0.1")
    }


def test_pick_latest_ignores_version_tags():
    rows = [row("1.0.0", "1.0.0", day(1)), row("custom", "custom", day(2))]
    assert pick_revision_ids_per_group(rows, RevisionSelection.LATEST) == {
        GROUP_A: trafo_id("custom")
    }


def test_pick_latest_tie_is_broken_by_id():
    rows = [row("x", "1.0.0", day(1)), row("y", "1.0.1", day(1))]
    expected = max(trafo_id("x"), trafo_id("y"))
    assert pick_revision_ids_per_group(rows, RevisionSelection.LATEST) == {GROUP_A: expected}
    assert pick_revision_ids_per_group(reversed(rows), RevisionSelection.LATEST) == {
        GROUP_A: expected
    }


@pytest.mark.parametrize(
    ("lower", "higher"),
    [
        ("1.9.0", "1.10.0"),
        ("1.0.0", "1.0.1"),
        ("2.0.0-rc.1", "2.0.0"),
        ("1.9.0", "2.0.0-rc.1"),
        ("2.0.0-alpha", "2.0.0-alpha.1"),
        ("2.0.0-alpha.2", "2.0.0-alpha.10"),
        ("2.0.0-rc.1+build.9", "2.0.0+build.1"),
    ],
)
def test_pick_highest_by_semantic_versioning_precedence(lower, higher):
    # the lower version is released later and must lose anyway
    rows = [row("higher", higher, day(1)), row("lower", lower, day(2))]
    assert pick_revision_ids_per_group(rows, RevisionSelection.HIGHEST) == {
        GROUP_A: trafo_id("higher")
    }
    assert pick_revision_ids_per_group(reversed(rows), RevisionSelection.HIGHEST) == {
        GROUP_A: trafo_id("higher")
    }


def test_pick_highest_ignores_non_semver_tags():
    rows = [
        row("1.0.0", "1.0.0", day(1)),
        row("v2.0.0", "v2.0.0", day(2)),
        row("2.0", "2.0", day(3)),
        row("02.0.0", "02.0.0", day(4)),
        row("latest-ish", "newest", day(5)),
    ]
    assert pick_revision_ids_per_group(rows, RevisionSelection.HIGHEST) == {
        GROUP_A: trafo_id("1.0.0")
    }


def test_pick_highest_omits_groups_without_semver_tags():
    rows = [
        row("custom", "custom", day(1), revision_group_id=GROUP_B),
        row("1.0.0", "1.0.0", day(1)),
    ]
    assert pick_revision_ids_per_group(rows, RevisionSelection.HIGHEST) == {
        GROUP_A: trafo_id("1.0.0")
    }
    assert pick_revision_ids_per_group(rows, RevisionSelection.LATEST) == {
        GROUP_A: trafo_id("1.0.0"),
        GROUP_B: trafo_id("custom"),
    }


def test_pick_highest_tie_is_broken_by_release_timestamp_and_id():
    # build metadata is ignored for precedence
    newer = row("newer", "1.0.0+b", day(2))
    older = row("older", "1.0.0+a", day(1))
    draft = row("draft", "1.0.0+c", None)
    for rows in ([newer, older, draft], [draft, older, newer]):
        assert pick_revision_ids_per_group(rows, RevisionSelection.HIGHEST) == {
            GROUP_A: trafo_id("newer")
        }

    # released wins against draft
    for rows in ([older, draft], [draft, older]):
        assert pick_revision_ids_per_group(rows, RevisionSelection.HIGHEST) == {
            GROUP_A: trafo_id("older")
        }

    same_time = [row("x", "1.0.0+x", day(1)), row("y", "1.0.0+y", day(1))]
    expected = max(trafo_id("x"), trafo_id("y"))
    assert pick_revision_ids_per_group(same_time, RevisionSelection.HIGHEST) == {GROUP_A: expected}
    assert pick_revision_ids_per_group(reversed(same_time), RevisionSelection.HIGHEST) == {
        GROUP_A: expected
    }


def test_pick_per_group():
    rows = [
        row("a1", "1.0.0", day(1), revision_group_id=GROUP_A),
        row("b2", "2.0.0", day(2), revision_group_id=GROUP_B),
        row("a2", "2.0.0", day(2), revision_group_id=GROUP_A),
        row("b1", "1.0.0", day(3), revision_group_id=GROUP_B),
    ]
    assert pick_revision_ids_per_group(rows, RevisionSelection.LATEST) == {
        GROUP_A: trafo_id("a2"),
        GROUP_B: trafo_id("b1"),
    }
    assert pick_revision_ids_per_group(rows, RevisionSelection.HIGHEST) == {
        GROUP_A: trafo_id("a2"),
        GROUP_B: trafo_id("b2"),
    }
    assert pick_revision_ids_per_group([], RevisionSelection.HIGHEST) == {}


# Selection from db


@pytest.mark.parametrize(
    ("by", "include_deprecated", "include_drafts", "expected_seed"),
    [
        (RevisionSelection.LATEST, False, False, "a 1.0.1"),
        (RevisionSelection.HIGHEST, False, False, "a 2.0.0"),
        (RevisionSelection.LATEST, True, False, "a 3.0.0"),
        (RevisionSelection.HIGHEST, True, False, "a 3.0.0"),
        (RevisionSelection.HIGHEST, False, True, "a 4.0.0"),
        (RevisionSelection.HIGHEST, True, True, "a 4.0.0"),
    ],
)
def test_select_revision_id_of_group(
    stored_revision_groups, by, include_deprecated, include_drafts, expected_seed
):
    assert select_revision_id_of_group(
        GROUP_A, by=by, include_deprecated=include_deprecated, include_drafts=include_drafts
    ) == trafo_id(expected_seed)


def test_select_revision_id_of_group_defaults_to_latest_released(stored_revision_groups):
    assert select_revision_id_of_group(GROUP_A) == trafo_id("a 1.0.1")


def test_select_revision_id_of_group_drafts_only_for_highest(stored_revision_groups):
    with pytest.raises(ValueError, match="Including drafts is only possible"):
        select_revision_id_of_group(GROUP_A, by=RevisionSelection.LATEST, include_drafts=True)


def test_select_revision_id_of_group_not_found(stored_revision_groups):
    with pytest.raises(
        DBNotFoundError,
        match=f"no released transformation revisions with revision group id {GROUP_D} found",
    ):
        select_revision_id_of_group(GROUP_D)

    with pytest.raises(
        DBNotFoundError,
        match=(
            f"no released or deprecated transformation revisions with revision group id {GROUP_B}"
            " and a semantic version as version tag found"
        ),
    ):
        select_revision_id_of_group(GROUP_B, by=RevisionSelection.HIGHEST, include_deprecated=True)

    assert select_revision_id_of_group(
        GROUP_B, by=RevisionSelection.HIGHEST, include_drafts=True
    ) == trafo_id("b 1.0.0")

    with pytest.raises(DBNotFoundError):
        select_revision_id_of_group(get_uuid_from_seed("unknown revision group"))


@pytest.mark.parametrize(
    ("selection_kwargs", "expected_seeds"),
    [
        ({}, {"a 1.0.1", "b custom", "c 1.1.0", ECHO_WINNER}),
        ({"by": RevisionSelection.HIGHEST}, {"a 2.0.0", "c 1.1.0", ECHO_WINNER}),
        (
            {"by": RevisionSelection.HIGHEST, "include_drafts": True},
            {"a 4.0.0", "b 1.0.0", "c 1.1.0", "d 0.1.0", ECHO_WINNER},
        ),
        # filters are applied first, then the latest / highest is selected per group
        ({"categories": ["Cat/A"]}, {"a 1.0.1", "c 1.0.0"}),
        ({"by": RevisionSelection.HIGHEST, "categories": ["Cat/A"]}, {"a 2.0.0", "c 1.0.0"}),
        ({"categories": ["Cat/A", "Cat/B"]}, {"a 1.0.1", "b custom", "c 1.0.0"}),
        ({"category_prefix": "Cat/"}, {"a 1.0.1", "b custom", "c 1.1.0", ECHO_WINNER}),
        ({"type": Type.WORKFLOW}, {"b custom"}),
        ({"names": ["Alpha", "Charlie"]}, {"a 1.0.1", "c 1.1.0"}),
        ({"revision_group_ids": [GROUP_A, GROUP_C, GROUP_D]}, {"a 1.0.1", "c 1.1.0"}),
        ({"names": ["Delta"]}, set()),
    ],
)
def test_select_revision_ids_per_group(stored_revision_groups, selection_kwargs, expected_seeds):
    selected = select_revision_ids_per_group(**selection_kwargs)
    assert set(selected.values()) == {trafo_id(seed) for seed in expected_seeds}
    for revision_group_id, revision_id in selected.items():
        assert (
            next(tr for tr in STORED_TRAFOS if tr.id == revision_id).revision_group_id
            == revision_group_id
        )


# Endpoints


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("params", "expected_seed"),
    [
        ({}, "a 1.0.1"),
        ({"by": "latest"}, "a 1.0.1"),
        ({"by": "highest"}, "a 2.0.0"),
        ({"by": "latest", "include_deprecated": True}, "a 3.0.0"),
        ({"by": "highest", "include_drafts": True}, "a 4.0.0"),
    ],
)
async def test_get_selected_revision_of_revision_group(
    async_test_client, stored_revision_groups, params, expected_seed
):
    async with async_test_client as ac:
        response = await ac.get(f"/api/transformations/revision_groups/{GROUP_A}", params=params)
        stub_response = await ac.get(
            f"/api/transformations/revision_groups/{GROUP_A}/stub", params=params
        )

    assert response.status_code == 200
    assert response.json()["id"] == str(trafo_id(expected_seed))
    assert response.json()["content"] == "code"

    assert stub_response.status_code == 200
    assert stub_response.json()["id"] == str(trafo_id(expected_seed))
    assert "content" not in stub_response.json()
    assert "io_interface" in stub_response.json()


@pytest.mark.asyncio
@pytest.mark.parametrize("path_suffix", ["", "/stub"])
async def test_get_selected_revision_of_revision_group_errors(
    async_test_client, stored_revision_groups, path_suffix
):
    async with async_test_client as ac:
        not_found_response = await ac.get(
            f"/api/transformations/revision_groups/{GROUP_B}{path_suffix}",
            params={"by": "highest"},
        )
        drafts_for_latest_response = await ac.get(
            f"/api/transformations/revision_groups/{GROUP_A}{path_suffix}",
            params={"include_drafts": True},
        )
        invalid_by_response = await ac.get(
            f"/api/transformations/revision_groups/{GROUP_A}{path_suffix}",
            params={"by": "newest"},
        )

    assert not_found_response.status_code == 404
    assert "a semantic version as version tag" in not_found_response.json()["detail"]

    assert drafts_for_latest_response.status_code == 422
    assert "Including drafts is only possible" in drafts_for_latest_response.json()["detail"]

    assert invalid_by_response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.parametrize("path_suffix", ["", "/stubs"])
async def test_get_selected_revisions_of_revision_groups(
    async_test_client, stored_revision_groups, path_suffix
):
    async with async_test_client as ac:
        default_response = await ac.get(f"/api/transformations/revision_groups{path_suffix}")
        filtered_response = await ac.get(
            f"/api/transformations/revision_groups{path_suffix}",
            params={
                "by": "highest",
                "include_deprecated": True,
                "include_drafts": True,
                "category_prefix": "Cat/",
                "revision_group_id": [str(GROUP_A), str(GROUP_B), str(GROUP_C)],
                "type": "COMPONENT",
            },
        )
        drafts_for_latest_response = await ac.get(
            f"/api/transformations/revision_groups{path_suffix}",
            params={"include_drafts": True},
        )

    assert default_response.status_code == 200
    # ordered by name
    assert [tr["id"] for tr in default_response.json()] == [
        str(trafo_id(seed)) for seed in ["a 1.0.1", "b custom", "c 1.1.0", ECHO_WINNER]
    ]
    assert all(("content" in tr) is (path_suffix == "") for tr in default_response.json())

    assert filtered_response.status_code == 200
    assert [tr["id"] for tr in filtered_response.json()] == [
        str(trafo_id(seed)) for seed in ["a 4.0.0", "c 1.1.0"]
    ]

    assert drafts_for_latest_response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.parametrize("revision_group_id", [GROUP_A, GROUP_E])
@pytest.mark.parametrize(
    ("by", "selection_options"),
    [
        ("latest", {}),
        ("latest", {"include_deprecated": True}),
        ("highest", {}),
        ("highest", {"include_deprecated": True}),
        ("highest", {"include_drafts": True}),
        ("highest", {"include_deprecated": True, "include_drafts": True}),
    ],
)
async def test_execute_by_revision_group_executes_selected_revision(
    async_test_client, stored_revision_groups, revision_group_id, by, selection_options
):
    """The execute endpoints must execute the revision the GET endpoints provide"""
    mocked_execution = mock.AsyncMock(side_effect=HTTPException(status.HTTP_418_IM_A_TEAPOT))
    with mock.patch(
        "hetdesrun.backend.service.transformation_router.handle_trafo_revision_execution_request",
        new=mocked_execution,
    ):
        async with async_test_client as ac:
            get_response = await ac.get(
                f"/api/transformations/revision_groups/{revision_group_id}",
                params={"by": by} | selection_options,
            )
            exec_response = await ac.post(
                f"/api/transformations/execute-{by}",
                json={
                    "revision_group_id": str(revision_group_id),
                    "wiring": WorkflowWiring().model_dump(mode="json"),
                }
                | selection_options,
            )

    assert get_response.status_code == 200
    assert exec_response.status_code == 418
    mocked_execution.assert_called_once()
    assert str(mocked_execution.call_args.args[0].id) == get_response.json()["id"]


@pytest.mark.asyncio
@pytest.mark.parametrize("endpoint", ["execute-latest", "execute-latest-async"])
async def test_execute_latest_rejects_drafts(async_test_client, stored_revision_groups, endpoint):
    mocked_execution = mock.AsyncMock()
    with mock.patch(
        "hetdesrun.backend.service.transformation_router.handle_trafo_revision_execution_request",
        new=mocked_execution,
    ):
        async with async_test_client as ac:
            response = await ac.post(
                f"/api/transformations/{endpoint}",
                json={
                    "revision_group_id": str(GROUP_A),
                    "wiring": WorkflowWiring().model_dump(mode="json"),
                    "include_drafts": True,
                },
                params={"callback_url": "http://callback-url.com/"},
            )

    assert response.status_code == 422
    assert "Including drafts is only possible" in response.text
    mocked_execution.assert_not_called()


# Upgrading operators


def store_pass_through_revisions(
    json_file_name: str, revisions: list[tuple[str, str, State, datetime.datetime | None]]
) -> TransformationRevision:
    """Store revisions of a base pass through component

    Returns the original component revision, whose released timestamp is set to day 1.
    """
    original = TransformationRevision(
        **load_json(os.path.join("transformations", "components", "connectors", json_file_name))
    )
    original.released_timestamp = day(1)
    store_single_transformation_revision(original)

    for seed, version_tag, state, released in revisions:
        store_single_transformation_revision(
            original.model_copy(
                deep=True,
                update={
                    "id": trafo_id(seed),
                    "version_tag": version_tag,
                    "state": state,
                    "released_timestamp": released,
                    "disabled_timestamp": day(28) if state is State.DISABLED else None,
                },
            )
        )
    return original


@pytest.fixture()
def workflow_with_outdated_operators(mocked_clean_test_db_session):
    pt_integer = store_pass_through_revisions(
        "pass-through-integer_100_57eea09f-d28e-89af-4e81-2027697a3f0f.json",
        [
            ("int 2.0.0", "2.0.0", State.RELEASED, day(2)),
            ("int 1.0.1", "1.0.1", State.RELEASED, day(3)),
            ("int 3.0.0", "3.0.0", State.DISABLED, day(4)),
            ("int 4.0.0", "4.0.0", State.DRAFT, None),
        ],
    )
    pt_string = store_pass_through_revisions(
        "pass-through-string_100_2b1b474f-ddf5-1f4d-fec4-17ef9122112b.json",
        [
            ("str 1.0.1", "1.0.1", State.RELEASED, day(2)),
            ("str 1.0.2", "1.0.2", State.RELEASED, day(2)),
        ],
    )

    with WorkflowConstructor(
        trafo_collector=TrafoCollection(), name="Outdated", version_tag="0.1.0"
    ) as wf:
        integer_op = wf.op(pt_integer, "integer")
        string_op = wf.op(pt_string, "string")
        wf.input("integer_in", integer_op.i["input"])
        wf.input("string_in", string_op.i["input"])
        wf.output("integer_out", integer_op.o["output"])
        wf.output("string_out", string_op.o["output"])

    store_single_transformation_revision(wf.result)
    return wf.result


@pytest.mark.asyncio
async def test_upgrade_operators_endpoint_upgrades_to_latest_revision(
    async_test_client, workflow_with_outdated_operators
):
    """The upgrade operators button must upgrade to the revision the GET endpoints provide"""
    workflow = workflow_with_outdated_operators
    revision_group_ids = {op.revision_group_id for op in workflow.content.operators}

    async with async_test_client as ac:
        latest_ids = {
            (await ac.get(f"/api/transformations/revision_groups/{revision_group_id}")).json()["id"]
            for revision_group_id in revision_group_ids
        }
        response = await ac.put(
            f"/api/transformations/{workflow.id}/upgrade_operators",
            json=json.loads(workflow.model_dump_json()),
        )

    assert response.status_code == 201
    upgraded_ids = {op["transformation_id"] for op in response.json()["content"]["operators"]}
    assert upgraded_ids == latest_ids
    # latest, not highest (2.0.0), not deprecated (3.0.0), not draft (4.0.0)
    assert str(trafo_id("int 1.0.1")) in upgraded_ids
    # tie of same release timestamp broken by id
    assert str(max(trafo_id("str 1.0.1"), trafo_id("str 1.0.2"))) in upgraded_ids


@pytest.mark.parametrize("by", list(RevisionSelection))
def test_upgrade_operators_in_workflow_selects_like_revision_group_selection(
    workflow_with_outdated_operators, by
):
    upgraded = upgrade_operators_in_workflow(
        workflow_with_outdated_operators, only_check_deprecated=False, by=by
    )

    assert {op.transformation_id for op in upgraded.content.operators} == {
        select_revision_id_of_group(op.revision_group_id, by=by)
        for op in workflow_with_outdated_operators.content.operators
    }
