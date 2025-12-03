import pytest

from hetdesrun.structure.db.structure_service import load_structure_from_json_file
from hetdesrun.structure.models import CompleteStructure


@pytest.mark.usefixtures("_db_test_structure")
@pytest.mark.asyncio
async def test_load_complete_structure_from_web_endpoint(
    mocked_clean_test_db_session, async_test_client
):
    test_structure = load_structure_from_json_file("tests/structure/data/db_test_structure.json")

    async with async_test_client as ac:
        response = await ac.get("/api/structure/complete")

        assert response.status_code == 200

    loaded_structure = CompleteStructure(**response.json())

    assert len(loaded_structure.sources) == len(test_structure.sources)

    test_structure_source_names = {src.name for src in test_structure.sources}
    for src in loaded_structure.sources:
        assert src.name in test_structure_source_names

    assert len(loaded_structure.sinks) == len(test_structure.sinks)
    test_structure_sink_names = {snk.name for snk in test_structure.sinks}
    for snk in loaded_structure.sinks:
        assert snk.name in test_structure_sink_names

    assert len(loaded_structure.thing_nodes) == len(test_structure.thing_nodes)
    test_structure_thing_node_names = {tn.name for tn in test_structure.thing_nodes}
    for tn in loaded_structure.thing_nodes:
        assert tn.name in test_structure_thing_node_names

    assert len(loaded_structure.element_types) == len(test_structure.element_types)
    test_structure_element_types_names = {et.name for et in test_structure.element_types}
    for et in loaded_structure.element_types:
        assert et.name in test_structure_element_types_names
