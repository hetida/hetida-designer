import json
import uuid

import pytest

from hetdesrun.adapters.exceptions import AdapterHandlingException
from hetdesrun.adapters.virtual_structure_adapter.models import (
    VirtualStructureAdapterSink,
    VirtualStructureAdapterSource,
    VirtualStructureAdapterThingNode,
)
from hetdesrun.adapters.virtual_structure_adapter.structure import (
    get_single_sink,
    get_single_source,
    get_single_thingnode,
    get_structure,
)


@pytest.mark.usefixtures("_fill_db")
def test_get_structure_with_none():
    structure = get_structure(None)

    # Verify that the root node of the structure is returned
    assert structure.sources == structure.sinks == []
    assert len(structure.thingNodes) == 1
    assert isinstance(structure.thingNodes[0], VirtualStructureAdapterThingNode)
    assert structure.thingNodes[0].parentId is None
    assert structure.thingNodes[0].name == "Waterworks 1"


@pytest.mark.usefixtures("_fill_db")
def test_get_structure_with_non_existent_uuid():
    non_existent_uuid = uuid.uuid4()
    with pytest.raises(
        AdapterHandlingException,
        match=f"The prodived ID {non_existent_uuid} has no corresponding node in the database",
    ):
        _ = get_structure(non_existent_uuid)


@pytest.mark.usefixtures("_fill_db")
def test_get_structure_with_existing_uuid():
    # Load structure for reference
    filepath = "tests/virtual_structure_adapter/data/simple_end_to_end_with_any_test.json"
    with open(filepath) as file:
        structure_ref = json.load(file)

    # Make multiple calls to get structure, as the IDs are not known
    structure = get_structure(None)
    structure = get_structure(structure.thingNodes[0].id)
    structure = get_structure(structure.thingNodes[0].id)
    structure = get_structure(structure.thingNodes[0].id)

    # Check ThingNodes
    assert structure.thingNodes == []

    # Check Sources
    assert len(structure.sources) == 3
    assert isinstance(structure.sources[0], VirtualStructureAdapterSource)

    expected_source_names = [src["name"] for src in structure_ref["sources"]]

    for source in structure.sources:
        assert source.name in expected_source_names

    # Check Sinks
    assert len(structure.sinks) == 1
    assert isinstance(structure.sinks[0], VirtualStructureAdapterSink)
    assert structure.sinks[0].name == structure_ref["sinks"][0]["name"]


@pytest.mark.usefixtures("_fill_db")
def test_get_single_element_functions_with_non_existent_id():
    random_uuid = uuid.uuid4()  # Non-existent UUID

    source = get_single_source(random_uuid)
    sink = get_single_sink(random_uuid)
    thingnode = get_single_thingnode(random_uuid)

    assert source == sink == thingnode
    assert source is None
