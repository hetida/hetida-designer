from hetdesrun.adapters.kafka.config import get_kafka_adapter_config
from hetdesrun.adapters.kafka.structure import (
    get_sink_by_id,
    get_sinks,
    get_source_by_id,
    get_sources,
    get_structure,
)


def test_config_works(two_kafka_configs):
    assert len(get_kafka_adapter_config().kafka_configs) == 2


def test_kafka_adapter_structure(two_kafka_configs):
    structure_results = get_structure()
    assert len(structure_results.thingNodes) == 1
    assert len(structure_results.sources) == 0
    assert len(structure_results.sinks) == 0

    structure_results = get_structure("base")
    assert len(structure_results.thingNodes) == 0
    assert len(structure_results.sources) == 21
    assert len(structure_results.sinks) == 21

    for src in structure_results.sources:
        assert src == get_source_by_id(src.id)

    for snk in structure_results.sinks:
        assert snk == get_sink_by_id(snk.id)

    # get all sources
    all_sources = get_sources()
    assert len(all_sources) == 21
    for src in all_sources:
        assert src == get_source_by_id(src.id)

    # get all sinks
    all_sinks = get_sinks()
    assert len(all_sinks) == 21
    for snk in all_sinks:
        assert snk == get_sink_by_id(snk.id)
