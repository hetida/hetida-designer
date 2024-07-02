from uuid import UUID

import pytest

from hetdesrun.adapters.virtual_structure_adapter.models import (
    StructureThingNode,
    StructureVirtualSink,
    StructureVirtualSource,
)
from hetdesrun.adapters.virtual_structure_adapter.structure import (
    get_level_from_struct_service,
    get_structure,
)
from hetdesrun.structure.db.exceptions import DBNotFoundError
from hetdesrun.structure.db.orm_service import update_structure

# TODO Check if tests are overkill


@pytest.fixture()
def _fill_db(mocked_clean_test_db_session):
    file_path = "tests/virtual_structure_adapter/data/structure_test.json"
    update_structure(file_path)


@pytest.mark.skip(reason="Wait until necessity of description is clarified")
@pytest.mark.usefixtures("_fill_db")
def test_get_level_with_none():
    thing_nodes, sources, sinks = get_level_from_struct_service(None)

    assert sources == sinks == []
    assert len(thing_nodes) == 1
    assert isinstance(thing_nodes[0], StructureThingNode)
    assert thing_nodes[0].name == "RootNode"


@pytest.mark.usefixtures("_fill_db")
def test_get_level_with_existing_uuid():
    thing_nodes, sources, sinks = get_level_from_struct_service(
        "55555555-5555-5555-5555-555555555555"
    )

    # Check ThingNodes
    assert thing_nodes == []

    # Check Sources
    assert len(sources) == 1
    assert isinstance(sources[0], StructureVirtualSource)
    assert sources[0].name == "Source3"

    # Check Sinks
    assert len(sinks) == 2
    assert isinstance(sinks[0], StructureVirtualSink)
    assert sinks[0].name == "Sink1"
    assert isinstance(sinks[1], StructureVirtualSink)
    assert sinks[1].name == "Sink2"


@pytest.mark.usefixtures("_fill_db")
def test_get_structure():
    structure_response = get_structure("55555555-5555-5555-5555-555555555555")

    assert isinstance(structure_response.sources[0], StructureVirtualSource)
    assert isinstance(structure_response.sinks[0], StructureVirtualSink)
