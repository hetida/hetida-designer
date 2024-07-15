import json
from hetdesrun.structure.models import CompleteStructure


def test_object_creation_from_json():
    file_path = "tests/structure/data/db_test_structure.json"
    with open(file_path) as file:
        structure_json = json.load(file)
    complete_structure = CompleteStructure(**structure_json)
    assert len(complete_structure.element_types) == 3
    assert len(complete_structure.thing_nodes) == 7
    assert len(complete_structure.sources) == 2
    assert len(complete_structure.sinks) == 2

    thing_node_names = [tn.name for tn in complete_structure.thing_nodes]
    expected_names = [
            "Wasserwerk",
            "Anlage 1",
            "Anlage 2",
            "Hochbehälter 1 Anlage 1",
            "Hochbehälter 2 Anlage 1",
            "Hochbehälter 1 Anlage 2",
            "Hochbehälter 2 Anlage 2",
        ]

    for name in expected_names:
        assert name in thing_node_names