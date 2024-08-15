import logging
from uuid import UUID

from hetdesrun.models.wiring import InputWiring, OutputWiring
from hetdesrun.structure.models import Sink, Source
from hetdesrun.structure.structure_service import (
    delete_structure,
    get_collection_of_sinks_from_db,
    get_collection_of_sources_from_db,
    is_database_empty,
    update_structure,
)
from hetdesrun.webservice.config import get_config

logger = logging.getLogger(__name__)


def get_referenced_sources_and_sinks_for_virtual_sources_and_sinks(
    input_id_list: list[str], output_id_list: list[str]
) -> tuple[dict[UUID, Source], dict[UUID, Sink]]:
    referenced_sources = get_collection_of_sources_from_db(
        [UUID(input_id) for input_id in input_id_list]
    )
    referenced_sinks = get_collection_of_sinks_from_db(
        [UUID(output_id) for output_id in output_id_list]
    )

    return referenced_sources, referenced_sinks


def create_new_wirings_based_on_referenced_sources_and_sinks(
    input_id_list: list[str], output_id_list: list[str]
) -> tuple[dict[str, InputWiring], dict[str, OutputWiring]]:
    referenced_sources, referenced_sinks = (
        get_referenced_sources_and_sinks_for_virtual_sources_and_sinks(
            input_id_list, output_id_list
        )
    )

    actual_input_wirings = {
        str(src_id): InputWiring.from_structure_source(src)
        for src_id, src in referenced_sources.items()
    }

    actual_output_wirings = {
        str(sink_id): OutputWiring.from_structure_sink(sink)
        for sink_id, sink in referenced_sinks.items()
    }

    return actual_input_wirings, actual_output_wirings


def get_enumerated_ids_of_vst_sources_or_sinks(
    wirings: list[InputWiring] | list[OutputWiring],
) -> list[tuple[int, str]]:
    return [
        (i, wiring.ref_id)  # type: ignore[attr-defined]
        for i, wiring in enumerate(wirings)
        if wiring.adapter_id == "virtual-structure-adapter"  # type: ignore[attr-defined]
    ]


def prepopulate_structure() -> None:
    """This function handles the population of the virtual structure adapter
    with a user defined structure, if one is provided.
    """
    logger.info("Starting the prepopulation process for the virtual structure adapter")
    if not get_config().prepopulate_virtual_structure_adapter_at_designer_startup:
        logger.info(
            "Structure of the virtual structure adapter was not prepopulated, "
            "because the environment variable "
            "'PREPOPULATE_VST_ADAPTER_AT_HD_STARTUP' is set to false"
        )
        return
    if complete_structure := get_config().structure_to_prepopulate_virtual_structure_adapter:
        is_db_empty = is_database_empty()
        if get_config().completely_overwrite_an_existing_virtual_structure_at_hd_startup:
            if not is_db_empty:
                delete_structure()
                logger.info(
                    "An existing structure was found in the database and deleted, "
                    "during the prepopulation process of the virtual structure adapter"
                )
            update_structure(complete_structure)
        else:
            update_structure(complete_structure)
            logger.info(
                "%s and the update_structure function was executed.",
                "An existing structure was found in the database"
                if is_db_empty
                else "No existing structure was found in the database",
            )
        return
    logger.info(
        "Structure of the virtual structure adapter was not prepopulated, "
        "because no structure was provided "
        "via the environment variable 'STRUCTURE_TO_PREPOPULATE_VST_ADAPTER'"
    )
