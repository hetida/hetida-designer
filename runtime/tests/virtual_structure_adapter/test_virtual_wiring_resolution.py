import pytest

from hetdesrun.adapters.virtual_structure_adapter.models import StructureVirtualSource
from hetdesrun.models.wiring import InputWiring, WorkflowWiring
from hetdesrun.structure.structure_service import get_all_sources_from_db
from hetdesrun.wiring import resolve_virtual_structure_wirings


@pytest.mark.usefixtures("_fill_db")
def test_virtual_wiring_resolution_with_one_source():
    sources = get_all_sources_from_db()
    struct_src = StructureVirtualSource.from_structure_service(sources[0])
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
    # Create WorkflowWiring with InputWiring in it
    wf_wiring = WorkflowWiring(input_wirings=[input_wiring])
    # Replace wirings
    resolve_virtual_structure_wirings(wf_wiring)
    # Check if the wiring was correctly replaced
    assert (
        wf_wiring.input_wirings[0].adapter_id == "python-demo-adapter"
    )  # Should replace virtual-structure-adapter
    assert wf_wiring.input_wirings[0].workflow_input_name == "nf"  # Should keep the original name
    assert (
        wf_wiring.input_wirings[0].filters == example_filters
    )  # Should remain the same as there are no preset filters
