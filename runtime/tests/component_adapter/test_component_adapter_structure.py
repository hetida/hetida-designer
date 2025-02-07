from unittest import mock

import pytest

from hetdesrun.adapters.component_adapter.config import get_component_adapter_config
from hetdesrun.adapters.component_adapter.structure import (
    get_sink_by_id,
    get_sinks,
    get_source_by_id,
    get_sources,
    get_structure,
)


def test_config_works():
    get_component_adapter_config()


@pytest.mark.usefixtures("_components_for_component_adapter_tests", "_markdown_file_component_sink")
def test_component_adapter_structure(  # noqa: PLR0915
    mocked_clean_test_db_session,
):
    structure_results = get_structure()

    assert len(structure_results.thingNodes) == 5
    assert {x.name for x in structure_results.thingNodes} == {
        "Data Sources",
        "Anomaly Detection",
        "Connectors",
        "Test",  # occurs since category exists.
        "Data Sinks",
    }
    assert len(structure_results.sources) == 0
    assert len(structure_results.sinks) == 0

    structure_results = get_structure("Data Sources")
    assert len(structure_results.thingNodes) == 0
    assert len(structure_results.sources) == 0  # since the only component there is DRAFT

    with mock.patch(
        "hetdesrun.adapters.component_adapter.config.component_adapter_config.allow_draft_components",
        True,
    ):
        structure_results = get_structure("Data Sources")
        assert len(structure_results.thingNodes) == 0
        assert len(structure_results.sources) == 1  # now draft component is included

        with (
            mock.patch(
                "hetdesrun.adapters.component_adapter.config.component_adapter_config.allowed_source_categories",
                {"Data Sources"},
            ),
            mock.patch(
                "hetdesrun.adapters.component_adapter.config.component_adapter_config.allowed_sink_categories",
                {"Data Sources"},
            ),
        ):
            structure_results = get_structure()
            assert len(structure_results.thingNodes) == 1
            assert structure_results.thingNodes[0].name == "Data Sources"

            assert len(structure_results.sources) == 0
            assert len(structure_results.sinks) == 0

            structure_results = get_structure("Data Sources")
            assert len(structure_results.thingNodes) == 0
            assert len(structure_results.sources) == 1  # now draft component is included

            ts_random_sources = get_sources(filter_str="Generate Random Timeseries Data")
            assert len(ts_random_sources) == 1
            ts_random_source = get_source_by_id(ts_random_sources[0].id)
            assert ts_random_source is not None

            # only one source since other category not allowed

        # now other category allowed, draft allowed
        possible_sources = get_sources(filter_str=None)
        assert len(possible_sources) == 2

        # both have an "a" in name (if lower-cased)
        possible_sources = get_sources(filter_str="a")
        assert len(possible_sources) == 2

        # only one has a "d" in name
        possible_sources = get_sources(filter_str="d")
        assert len(possible_sources) == 1

    structure_results = get_structure("Anomaly Detection")
    assert len(structure_results.thingNodes) == 0
    assert len(structure_results.sources) == 1  # now only one released component is included
    assert len(structure_results.sinks) == 0
    alert_sources = get_sources(filter_str="Alerts from Score")
    assert len(alert_sources) == 1
    alert_source = get_source_by_id(alert_sources[0].id)
    assert alert_source is not None

    # DISABLED component as source
    structure_results = get_structure("Connectors")
    assert len(structure_results.thingNodes) == 0
    assert len(structure_results.sources) == 0  # disabled component should not occur in structure
    assert len(structure_results.sinks) == 0

    pass_through_sources = get_sources(filter_str="Pass Through")
    assert len(pass_through_sources) == 0  # disabled source does not occur here
    assert len(structure_results.sinks) == 0

    # but disabled is available if queried directly
    disabled_comp_source = get_source_by_id(
        "1946d5f8-44a8-724c-176f-123456aaaaaa"
    )  # the disabled component
    assert disabled_comp_source is not None

    # component with more than one output does not occur as source
    structure_results = get_structure("Test")
    assert len(structure_results.thingNodes) == 0
    assert len(structure_results.sinks) == 0
    assert len(structure_results.sources) == 0  # component has more outputs, cannot work as source
    possible_sources = get_sources(filter_str="Test Component Code Repr")
    assert len(possible_sources) == 0  # disabled source does not occur here

    # even not available as source if queried directly
    invalid_component_source = get_source_by_id(
        "31cb6a1a-d409-4bb7-87a7-ee3d97940dfc"
    )  # the component which is not a valid source
    assert invalid_component_source is None

    structure_results = get_structure("Data Sinks")
    assert len(structure_results.thingNodes) == 0
    assert len(structure_results.sources) == 0
    assert len(structure_results.sinks) == 1
    possible_sinks = get_sinks(filter_str="Markdown")
    assert len(possible_sinks) == 1
    assert possible_sinks[0] == get_sink_by_id(possible_sinks[0].metadataKey)  # is a metadata sink

    possible_sinks = get_sinks(filter_str="Nothing")
    assert len(possible_sinks) == 0
