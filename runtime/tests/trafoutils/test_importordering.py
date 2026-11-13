from hetdesrun.trafoutils.importorder import order_for_importing
from hetdesrun.trafoutils.io.load import load_trafo_from_python_file
from hetdesrun.utils import Type


def test_importordering(all_base_trafos_from_file):
    result = order_for_importing(all_base_trafos_from_file)

    assert len(result) == len(all_base_trafos_from_file)
    assert sorted(all_base_trafos_from_file, key=lambda x: x.id) != result

    # component and workflows grouped:
    last_type = Type.COMPONENT
    type_changes = 0
    for x in result:
        if x.type != last_type:
            type_changes += 1
        last_type = x.type

    assert type_changes == 1

    # components at the beginning
    assert result[0].type == Type.COMPONENT
    assert result[-1].type == Type.WORKFLOW

    # TODO: Add explicit ordering test!


def test_importordering_imports_imported_components_first():
    components_path = "./tests/data/components/"
    # each imports the one after it
    importing_chain = [
        load_trafo_from_python_file(components_path + file)
        for file in (
            "component_2_level_import.py",
            "component_importing_func_from_other.py",
            "component_with_functions_for_importing.py",
        )
    ]
    # draft components importing each other or themselves
    import_cycles = [
        load_trafo_from_python_file(components_path + file)
        for file in (
            "component_a_imports_b.py",
            "component_b_imports_a.py",
            "component_self_import.py",
        )
    ]

    result = order_for_importing(import_cycles[:1] + importing_chain + import_cycles[1:])

    assert [tr.id for tr in result] == [
        import_cycles[1].id,
        import_cycles[0].id,
        *(tr.id for tr in reversed(importing_chain)),
        import_cycles[2].id,
    ]
