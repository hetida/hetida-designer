import pytest

from hetdesrun.adapters.virtual_structure_adapter.models import (
    StructureThingNode,
    StructureVirtualSource,
)
from hetdesrun.adapters.virtual_structure_adapter.structure import (
    get_structure,
)



# @pytest.mark.skip(reason="Wait for get_children to work")
@pytest.mark.usefixtures("_fill_db")
def test_get_structure_with_none():
    structure = get_structure(None)

    assert structure.sources == structure.sinks == []
    assert len(structure.thingNodes) == 1
    assert isinstance(structure.thingNodes[0], StructureThingNode)
    assert structure.thingNodes[0].name == "Wasserwerk 1"


# @pytest.mark.skip(reason="Wait for get_children to work")
@pytest.mark.usefixtures("_fill_db")
def test_get_level_with_existing_uuid():
    structure = get_structure(None)
    structure = get_structure(structure.thingNodes[0].id)
    structure = get_structure(structure.thingNodes[0].id)  # Might need to adjust

    # Check ThingNodes
    assert structure.thingNodes == []
    assert structure.sinks == []

    # Check Sources
    assert len(structure.sources) == 1
    assert isinstance(structure.sources[0], StructureVirtualSource)
    assert structure.sources[0].name == "Energieverbräuche des Pumpensystems in Hochbehälter"
