from collections.abc import Callable

from hetdesrun.adapters.external_sources.models import ExternalSourcesStructureSink

sinks: dict[str, ExternalSourcesStructureSink] = {}  # sink_id id -> ExternalSourcesStructureSink

sink_load_functions: dict[str, Callable] = {}  # sink_id -> load func
