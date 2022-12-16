from hetdesrun.trafoutils.filter import filter_and_order_trafos
from hetdesrun.trafoutils.filter.params import FilterParams


def test_filtering(all_base_trafos_from_file):
    result_examples = filter_and_order_trafos(
        all_base_trafos_from_file,
        FilterParams(categories=["Examples"], include_dependencies=True),
    )
    result_examples_plus_arithmetic = filter_and_order_trafos(
        all_base_trafos_from_file,
        FilterParams(categories=["Examples", "Arithmetic"], include_dependencies=True),
    )

    result_examples_iso_forest = filter_and_order_trafos(
        all_base_trafos_from_file,
        FilterParams(
            categories=["Examples"],
            names=["Iso Forest Example"],
            include_dependencies=True,
        ),
    )
    assert len(result_examples) < len(all_base_trafos_from_file)
    assert len(result_examples_plus_arithmetic) > len(result_examples)

    assert len(result_examples_iso_forest) < len(result_examples)

    # TODO: Add more filtering tests!
