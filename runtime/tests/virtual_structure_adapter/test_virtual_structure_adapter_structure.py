import pytest

from hetdesrun.adapters.virtual_structure_adapter.models import (
    StructureThingNode,
    StructureVirtualSink,
    StructureVirtualSource,
)
from hetdesrun.adapters.virtual_structure_adapter.structure import (
    get_structure,
)


@pytest.mark.usefixtures("_fill_db")
def test_get_structure_with_none():
    structure = get_structure(None)

    assert structure.sources == structure.sinks == []
    assert len(structure.thingNodes) == 1
    assert isinstance(structure.thingNodes[0], StructureThingNode)
    assert structure.thingNodes[0].name == "Wasserwerk 1"


@pytest.mark.usefixtures("_fill_db")
def test_get_level_with_existing_uuid():
    structure = get_structure(None)
    structure = get_structure(structure.thingNodes[0].id)
    structure = get_structure(structure.thingNodes[0].id)
    structure = get_structure(structure.thingNodes[0].id)

    # Check ThingNodes
    assert structure.thingNodes == []

    # Check Sources
    assert len(structure.sources) == 2
    assert isinstance(structure.sources[0], StructureVirtualSource)
    expected_source_names = [
        "Energieverbräuche mit preset filter",
        "Energieverbräuche mit passthrough filters",
    ]
    for source in structure.sources:
        assert source.name in expected_source_names

    # Check Sinks
    assert len(structure.sinks) == 1
    assert isinstance(structure.sinks[0], StructureVirtualSink)
    assert structure.sinks[0].name == "Anomaliescore des Pumpensystems in Hochbehälter"
