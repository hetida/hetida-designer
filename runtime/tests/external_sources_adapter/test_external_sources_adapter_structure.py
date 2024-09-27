from hetdesrun.adapters.external_sources.config import get_external_sources_adapter_config
from hetdesrun.adapters.external_sources.structure import (
    get_sink_by_id,
    get_sinks,
    get_source_by_id,
    get_sources,
    get_structure,
)


def test_config_works():
    get_external_sources_adapter_config()


def test_external_sources_adapter_structure():
    structure_results = get_structure()
    assert len(structure_results.thingNodes) == 1
    assert len(structure_results.sources) == 0
    assert len(structure_results.sinks) == 0

    structure_results = get_structure(structure_results.thingNodes[0].id)
    assert len(structure_results.thingNodes) == 0
    assert len(structure_results.sources) == 4
    assert len(structure_results.sinks) == 0

    for src in structure_results.sources:
        assert src == get_source_by_id(src.id)

    for snk in structure_results.sinks:
        assert snk == get_sink_by_id(snk.id)

    # get all sources
    all_sources = get_sources()
    assert len(all_sources) == 4
    for src in all_sources:
        assert src == get_source_by_id(src.id)

    # get all sinks
    all_sinks = get_sinks()
    assert len(all_sinks) == 0
    for snk in all_sinks:
        assert snk == get_sink_by_id(snk.id)
