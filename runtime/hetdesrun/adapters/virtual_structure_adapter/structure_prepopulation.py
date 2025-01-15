import logging

from hetdesrun.adapters.virtual_structure_adapter.config import get_vst_adapter_config
from hetdesrun.adapters.virtual_structure_adapter.exceptions import StructurePrepopulationError
from hetdesrun.structure.db.exceptions import (
    DBAssociationError,
    DBConnectionError,
    DBError,
    DBIntegrityError,
    DBUpdateError,
    JsonParsingError,
)
from hetdesrun.structure.db.structure_service import (
    are_structure_tables_empty,
    delete_structure,
    load_structure_from_json_file,
    update_structure,
)

logger = logging.getLogger(__name__)


def prepopulate_structure() -> None:
    """Handles the population of the virtual structure adapter with a user defined structure."""

    # Set the structure for prepopulation
    if get_vst_adapter_config().prepopulate_virtual_structure_adapter_via_file:
        structure_filepath = (
            get_vst_adapter_config().structure_filepath_to_prepopulate_virtual_structure_adapter
        )
        logger.info("Prepopulating the virtual structure adapter via a file")
        try:
            complete_structure = load_structure_from_json_file(structure_filepath)  # type: ignore
        except (FileNotFoundError, JsonParsingError, DBError) as e:
            logger.error(
                "Loading the structure from a JSON failed during the prepopulation process: %s", e
            )
            raise StructurePrepopulationError(
                "Error during the prepopulation process: %s", e
            ) from e
    else:
        logger.info(
            "Prepopulating the virtual structure adapter via "
            "structure_to_prepopulate_virtual_structure_adapter"
        )
        complete_structure = (
            get_vst_adapter_config().structure_to_prepopulate_virtual_structure_adapter  # type: ignore
        )

    # Overwrite structure if configured
    if (
        get_vst_adapter_config().completely_overwrite_an_existing_virtual_structure_at_hd_startup
        and not are_structure_tables_empty()
    ):
        logger.info(
            "An existing structure was found in the database. The deletion process starts now"
        )
        try:
            delete_structure()
        except (DBIntegrityError, DBError) as e:
            logger.error(
                "Deletion of a potentially existing structure failed"
                "during the prepopulation process: %s",
                e,
            )
            raise StructurePrepopulationError(
                "Error during the prepopulation process: %s", e
            ) from e
        logger.info(
            "The existing structure was successfully deleted, "
            "during the prepopulation process of the virtual structure adapter"
        )

    try:
        update_structure(complete_structure)
    except (DBIntegrityError, DBConnectionError, DBAssociationError, DBUpdateError, DBError) as e:
        logger.error(
            "Update of the structure failed during the prepopulation process: %s",
            e,
        )
        raise StructurePrepopulationError("Error during the prepopulation process: %s", e) from e
    logger.info("The structure was successfully populated.")
