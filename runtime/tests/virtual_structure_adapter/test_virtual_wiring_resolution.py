import pytest

from hetdesrun.wiring import resolve_virtual_structure_wirings
from hetdesrun.models.wiring import InputWiring, WorkflowWiring
from hetdesrun.structure.models import Source
from hetdesrun.adapters.virtual_structure_adapter.models import StructureVirtualSource
from hetdesrun.structure.structure_service import get_children

@pytest.fixture()
def create_workflow_wiring():
    # TODO also add a sink to the wiring
    # Create Source mapping onto Python-Demo-Adapter
    src_dict = {
            "external_id": "Energieverbraeuche_Pumpensystem_Hochbehaelter",
            "stakeholder_key": "GW",
            "name": "Energieverbräuche des Pumpensystems in Hochbehälter",
            "type": "series(float)",
            "adapter_key": "python-demo-adapter",
            "source_id": "root.plantA.picklingUnit.influx.temp",
            "meta_data": {
                "Influx": {"nf": 23}
            },
            "passthrough_filters": [
                "timestampFrom",
                "timestampTo"
            ],
            "thing_node_external_ids": [
                "Wasserwerk1_Anlage1_Hochbehaelter1"
            ]
        }
    src = Source(**src_dict)

    # Create StructureVirtualSource from it
    struct_src = StructureVirtualSource.from_structure_service(src)
    
    # Create InputWiring with StructureSource in it
    # This is created according to StructureVirtualSource not Source
    input_wiring = InputWiring(workflow_input_name="nf", adapter_id="virtual-structure-adapter", ref_id=str(struct_src.id), type=struct_src.type, filters={
      "timestampFrom": "2024-07-10T09:36:00.000000000Z",
      "timestampTo": "2024-07-11T09:36:00.000000000Z"
    })
    # Create WorkflowWiring with InputWiring in it
    wf_wiring = WorkflowWiring(input_wirings=[input_wiring])

    return wf_wiring


# @pytest.mark.skip(reason="unfinished")
@pytest.mark.usefixtures("_fill_db")
def test_virtual_wiring_resolution_with_one_source(create_workflow_wiring):
    # TODO currently does not work, as the ID generated for the dummy source from the fixture is not in the DB
    # Replace wirings
    resolve_virtual_structure_wirings(create_workflow_wiring)
    # Check if the wiring was correctly replaced
    assert create_workflow_wiring.input_wirings[0].adapter_id == "demo-adapter-python"