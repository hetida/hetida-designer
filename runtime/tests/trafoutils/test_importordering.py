from hetdesrun.trafoutils.importorder import (
    filter_and_order_trafos,
    order_for_importing,
)
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
