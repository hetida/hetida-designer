import json
from unittest import mock

import pytest
from httpx import ASGITransport, AsyncClient

from hetdesrun.backend.service.dashboarding_utils import (
    __all_wiring_attribute_url_alias_sets__,
    update_wiring_from_query_parameters,
)
from hetdesrun.models.wiring import (
    GridstackItemPositioning,
    InputWiring,
    OutputWiring,
    WorkflowWiring,
)
from hetdesrun.persistence.dbservice.revision import (
    store_single_transformation_revision,
)
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.webservice.application import init_app


@pytest.fixture()
def _db_with_multits_viz_component(mocked_clean_test_db_session):
    with open(
        "transformations/components/visualization/multitsframe-plot-with-multiple-y-axes_100_28120522-a6a5-418f-a658-ab19d5beefe2.json"
    ) as f:
        trafo_data = json.load(f)
    store_single_transformation_revision(TransformationRevision(**trafo_data))


@pytest.fixture()
def activate_auth():
    with mock.patch("hetdesrun.webservice.config.runtime_config.auth", True) as _fixture:
        yield _fixture


@pytest.fixture()
def app_with_auth(activate_auth):
    return init_app()


@pytest.fixture
def async_test_client_with_auth(app_with_auth):
    return AsyncClient(transport=ASGITransport(app=app_with_auth), base_url="http://test")


@pytest.mark.asyncio
async def test_unauthorized_dashboard_endpoint(
    _db_with_multits_viz_component,  # noqa: PT019
    async_test_client,
):
    async with async_test_client as client:
        response = await client.get(
            "/api/transformations/28120522-a6a5-418f-a658-ab19d5beefe2/dashboard"
        )

        assert response.status_code == 200
        assert "<html" in response.text
        assert "gridstack" in response.text  # actually a dashboard and not the login stub


@pytest.mark.asyncio
async def test_unauthorized_dashboard_positioning(
    _db_with_multits_viz_component,  # noqa: PT019
    async_test_client,
):
    async with async_test_client as client:
        response = await client.put(
            "/api/transformations/28120522-a6a5-418f-a658-ab19d5beefe2/dashboard/positioning",
            json=[{"x": 2, "y": 2, "w": 8, "h": 5, "id": "plot"}],
        )
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_authorized_dashboard_endpoint(
    _db_with_multits_viz_component,  # noqa: PT019
    async_test_client_with_auth,
):
    async with async_test_client_with_auth as client:
        response = await client.get(
            "/api/transformations/28120522-a6a5-418f-a658-ab19d5beefe2/dashboard"
        )
        assert response.status_code == 200
        assert "<html" in response.text
        assert "gridstack" not in response.text  # actually a dashboard and not the login stub


def test_wiring_url_aliases():
    """The alias sets for wiring attributes in urls should not overlap"""

    set_sum = sum(len(alias_set) for alias_set in __all_wiring_attribute_url_alias_sets__)

    union = set().union(*__all_wiring_attribute_url_alias_sets__)

    assert set_sum == len(union)


def test_create_wiring_from_query_paramaters():
    new_wiring = update_wiring_from_query_parameters(
        None,
        [
            ("input.param1.value", "32"),
            ("in.param1.value", "42"),
            ("input.param2.value", "abc"),
            ("outp.out1.ref_id", "some_sink_id"),
            ("outp.out1.adapter_id", "some_adapter"),
            ("outp.out1.pos", "3_0_12_3"),
        ],
    )
    assert len(new_wiring.input_wirings) == 2
    assert new_wiring.input_wirings[0].filters["value"] == "42"  # last provided query param wins

    assert new_wiring.input_wirings[0].adapter_id == "direct_provisioning"

    assert new_wiring.input_wirings[1].adapter_id == "direct_provisioning"

    assert len(new_wiring.output_wirings) == 1
    assert new_wiring.output_wirings[0].adapter_id == "some_adapter"
    assert new_wiring.output_wirings[0].ref_id == "some_sink_id"

    assert len(new_wiring.dashboard_positionings) == 1
    positioning = new_wiring.dashboard_positionings[0]
    assert positioning.x == 3 and positioning.y == 0 and positioning.w == 12 and positioning.h == 3  # noqa: PT018


def test_actually_update_wiring_from_query_parameters():
    existing_wiring = WorkflowWiring(
        input_wirings=[
            InputWiring(
                adapter_id="direct_provisioning",
                workflow_input_name="inp_1",
                filters={
                    "value": '{"2020-05-01T00:00:00.000Z": 1.2, "2020-05-01T01:00:00.000Z": 3.14, "2020-05-01T02:00:00.000Z": 5, "2020-05-01T03:00:00.000Z": null}'  # noqa: E501
                },
            ),
            InputWiring(
                adapter_id="some_adapter",
                ref_id="some_ref_id",
                workflow_input_name="inp_2",
            ),
        ],
        output_wirings=[
            OutputWiring(
                adapter_id="some_adapter_id",
                ref_id="some_ref_id",
                workflow_output_name="outp_1",
            ),
            OutputWiring(
                adapter_id="direct_provisioning",
                workflow_output_name="outp_2",
            ),
        ],
        dashboard_positionings=[
            GridstackItemPositioning(id="outp_1", x=0, y=0, w=6, h=6),
            GridstackItemPositioning(id="outp_2", x=6, y=0, w=6, h=6),
        ],
    )

    new_wiring = update_wiring_from_query_parameters(
        existing_wiring,
        [
            ("input.param1.value", "32"),  # create new one
            ("in.inp_1.value", "42"),  # update existing one
            ("outp.outp_1.ref_id", "another_ref_id"),  # update existing one
            ("o.outp_3.adapter_id", "another_adapter_id"),  # create new one
            ("o.outp_3.ref_id", "yet_another_ref_id"),  # proceeding creating
            ("o.outp_1.pos", "3_3_3_3"),  # edit positioning
            ("o.outp_3.pos", "12_0_6_6"),  # create new positioning
        ],
    )

    assert len(new_wiring.input_wirings) == 3
    assert {input_wiring.workflow_input_name for input_wiring in new_wiring.input_wirings} == {
        "inp_1",
        "inp_2",
        "param1",
    }
    assert len(new_wiring.output_wirings) == 3
    assert {output_wiring.workflow_output_name for output_wiring in new_wiring.output_wirings} == {
        "outp_1",
        "outp_2",
        "outp_3",
    }
    assert len(new_wiring.dashboard_positionings) == 3
    assert {positioning.id for positioning in new_wiring.dashboard_positionings} == {
        "outp_1",
        "outp_2",
        "outp_3",
    }

    inp_wirings_by_name = {inp_w.workflow_input_name: inp_w for inp_w in new_wiring.input_wirings}

    assert inp_wirings_by_name["param1"].filters["value"] == "32"
    assert inp_wirings_by_name["param1"].adapter_id == "direct_provisioning"
    assert inp_wirings_by_name["inp_1"].filters["value"] == "42"
    assert inp_wirings_by_name["inp_2"].ref_id == "some_ref_id"

    outp_wirings_by_name = {
        outp_w.workflow_output_name: outp_w for outp_w in new_wiring.output_wirings
    }

    assert outp_wirings_by_name["outp_2"].adapter_id == "direct_provisioning"
    assert outp_wirings_by_name["outp_1"].ref_id == "another_ref_id"
    assert outp_wirings_by_name["outp_3"].adapter_id == "another_adapter_id"
    assert outp_wirings_by_name["outp_3"].ref_id == "yet_another_ref_id"

    positionings_by_name = {
        positioning.id: positioning for positioning in new_wiring.dashboard_positionings
    }
    assert (  # noqa: PT018
        positionings_by_name["outp_1"].x == 3
        and positionings_by_name["outp_1"].y == 3
        and positionings_by_name["outp_1"].w == 3
        and positionings_by_name["outp_1"].h == 3
    )
    assert (  # noqa: PT018
        positionings_by_name["outp_2"].x == 6
        and positionings_by_name["outp_2"].y == 0
        and positionings_by_name["outp_2"].w == 6
        and positionings_by_name["outp_2"].h == 6
    )
    assert (  # noqa: PT018
        positionings_by_name["outp_3"].x == 12
        and positionings_by_name["outp_3"].y == 0
        and positionings_by_name["outp_3"].w == 6
        and positionings_by_name["outp_3"].h == 6
    )
