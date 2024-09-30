import uuid

import pytest

from hetdesrun.adapters.virtual_structure_adapter.models import (
    StructureVirtualSink,
    StructureVirtualSource,
)
from hetdesrun.models.wiring import InputWiring, OutputWiring, WorkflowWiring
from hetdesrun.structure.db.exceptions import DBNotFoundError
from hetdesrun.structure.structure_service import get_all_sinks_from_db, get_all_sources_from_db
from hetdesrun.wiring import resolve_virtual_structure_wirings


@pytest.mark.usefixtures("_fill_db")
def test_virtual_wiring_resolution_with_one_source_and_sink():
    # Create Input- and OutputWiring for the source and sink from the test json
    sources = get_all_sources_from_db()
    sinks = get_all_sinks_from_db()
    struct_src = StructureVirtualSource.from_structure_service(sources[0])
    struct_sink = StructureVirtualSink.from_structure_service(sinks[0])
    example_filters = {
        "timestampFrom": "2024-07-10T09:36:00.000000000Z",
        "timestampTo": "2024-07-11T09:36:00.000000000Z",
    }
    input_wiring = InputWiring(
        workflow_input_name="nf",
        adapter_id="virtual-structure-adapter",
        ref_id=str(struct_src.id),
        type=struct_src.type,
        filters=example_filters,
    )
    output_wiring = OutputWiring(
        workflow_output_name="nf2",
        adapter_id="virtual-structure-adapter",
        ref_id=str(struct_sink.id),
        type=struct_sink.type,
        filters=example_filters,
    )

    wf_wiring = WorkflowWiring(input_wirings=[input_wiring], output_wirings=[output_wiring])

    # Replace wirings
    resolve_virtual_structure_wirings(wf_wiring)

    # Check if the wiring was correctly replaced
    assert (
        wf_wiring.input_wirings[0].adapter_id == "demo-adapter-python"
    )  # Should replace virtual-structure-adapter
    assert (
        wf_wiring.output_wirings[0].adapter_id == "demo-adapter-python"
    )  # Should replace virtual-structure-adapter

    assert wf_wiring.input_wirings[0].workflow_input_name == "nf"  # Should keep the original name
    assert (
        wf_wiring.output_wirings[0].workflow_output_name == "nf2"
    )  # Should keep the original name

    assert (
        wf_wiring.input_wirings[0].filters == sources[0].preset_filters | example_filters
    )  # Should be a combination of preset and passthrough filters
    assert (
        wf_wiring.output_wirings[0].filters == sinks[0].preset_filters | example_filters
    )  # Should be a combination of preset and passthrough filters


@pytest.mark.usefixtures("_fill_db")
def test_virtual_wiring_resolution_with_empty_workflow_wiring():
    wf_wiring = WorkflowWiring()
    original_wiring_id = id(wf_wiring)

    resolve_virtual_structure_wirings(wf_wiring)

    # Verify that object did not change
    assert id(wf_wiring) == original_wiring_id
    assert wf_wiring.input_wirings == wf_wiring.output_wirings == []


@pytest.mark.usefixtures("_fill_db")
def test_virtual_wiring_resolution_with_other_adapter_key():
    # Create example InputWiring
    sources = get_all_sources_from_db()
    struct_src = StructureVirtualSource.from_structure_service(sources[0])
    example_filters = {
        "timestampFrom": "2024-07-10T09:36:00.000000000Z",
        "timestampTo": "2024-07-11T09:36:00.000000000Z",
    }
    input_wiring = InputWiring(
        workflow_input_name="nf",
        adapter_id="sql-adapter",
        ref_id=str(struct_src.id),
        type=struct_src.type,
        filters=example_filters,
    )

    wf_wiring = WorkflowWiring(input_wirings=[input_wiring])
    original_wiring_id = id(wf_wiring)

    resolve_virtual_structure_wirings(wf_wiring)

    # Verify that object did not change
    assert id(wf_wiring) == original_wiring_id
    assert len(wf_wiring.input_wirings) == 1
    assert wf_wiring.input_wirings[0] == input_wiring


@pytest.mark.usefixtures("_fill_db")
def test_virtual_wiring_resolution_with_non_existent_source_or_sink_id():
    # Create example InputWiring
    # Only a source is created because the retrieval process for
    # sources and sinks is identical
    sources = get_all_sources_from_db()
    struct_src = StructureVirtualSource.from_structure_service(sources[0])
    struct_src.id = uuid.uuid4()  # Overwrite existing ID

    example_filters = {
        "timestampFrom": "2024-07-10T09:36:00.000000000Z",
        "timestampTo": "2024-07-11T09:36:00.000000000Z",
    }
    input_wiring = InputWiring(
        workflow_input_name="nf",
        adapter_id="virtual-structure-adapter",
        ref_id=str(struct_src.id),
        type=struct_src.type,
        filters=example_filters,
    )

    wf_wiring = WorkflowWiring(input_wirings=[input_wiring])

    with pytest.raises(DBNotFoundError):
        resolve_virtual_structure_wirings(wf_wiring)
