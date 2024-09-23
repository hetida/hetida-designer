import logging
import os
from collections.abc import Iterable
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field

from hetdesrun.exportimport.utils import (
    deprecate_all_but_latest_in_group,
    update_or_create_transformation_revision,
)
from hetdesrun.persistence.dbservice.exceptions import DBIntegrityError, DBNotFoundError
from hetdesrun.persistence.dbservice.revision import (
    update_or_create_single_transformation_revision,
)
from hetdesrun.persistence.models.exceptions import ModelConstraintViolation
from hetdesrun.trafoutils.filter.mapping import filter_and_order_trafos
from hetdesrun.trafoutils.io.load import (
    Importable,
    load_transformation_revisions_from_directory,
)
from hetdesrun.trafoutils.nestings import structure_ids_by_nesting_level

logger = logging.getLogger(__name__)


class UpdateProcessStatus(str, Enum):
    NOT_TRIED = "NOT_TRIED"
    FAILED = "FAILED"
    SUCCESS = "SUCCESS"
    IGNORED = "IGNORED"


class TrafoUpdateProcessSummary(BaseModel):
    status: UpdateProcessStatus
    msg: str = Field("", description="details / error messages")
    name: str | None
    version_tag: str | None


def import_importable(
    importable: Importable,
    raise_on_missing_dependency: bool = False,
) -> dict[UUID | str, TrafoUpdateProcessSummary]:
    """Imports trafo revs from a single importable into the database

    An importable contains transformation revisions (for example loaded from
    a directory on disk or a json file containing a list of trafo revs).

    Additionally it contains
    * filter params: filter during import, i.e. only import a subset
    * update config: configuration for the db updating process

    This function catches typical exceptions during import and instead provides
    a detailed processing status result for each transformation by id.
    """

    trafo_revs = importable.transformation_revisions
    filter_params = importable.import_config.filter_params
    multi_import_config = importable.import_config.update_config

    trafos_to_process = filter_and_order_trafos(
        trafo_revs,
        filter_params,
        raise_on_missing_dependency=raise_on_missing_dependency,
    )

    trafos_to_process_dict = {trafo_rev.id: trafo_rev for trafo_rev in trafos_to_process}

    success_per_trafo: dict[UUID | str, TrafoUpdateProcessSummary] = {
        trafo.id: (
            TrafoUpdateProcessSummary(
                status=UpdateProcessStatus.NOT_TRIED,
                msg="",
                name=trafo.name,
                version_tag=trafo.version_tag,
            )
            if trafo.id in trafos_to_process_dict
            else TrafoUpdateProcessSummary(
                status=UpdateProcessStatus.IGNORED,
                msg="filtered out",
                name=trafo.name,
                version_tag=trafo.version_tag,
            )
        )
        for trafo in trafo_revs
    }

    for transformation in trafos_to_process:
        logger.debug(
            "Importing transformation %s with tag %s with id %s",
            transformation.name,
            transformation.version_tag,
            str(transformation.id),
        )
        try:
            update_or_create_single_transformation_revision(
                transformation,
                allow_overwrite_released=multi_import_config.allow_overwrite_released,
                update_component_code=multi_import_config.update_component_code,
                strip_wiring=multi_import_config.strip_wirings,
                strip_wirings_with_adapter_ids=multi_import_config.strip_wirings_with_adapter_ids,
                keep_only_wirings_with_adapter_ids=multi_import_config.keep_only_wirings_with_adapter_ids,
                strip_release_wiring=multi_import_config.strip_release_wirings,
                strip_release_wirings_with_adapter_ids=multi_import_config.strip_release_wirings_with_adapter_ids,
                keep_only_release_wirings_with_adapter_ids=multi_import_config.keep_only_release_wirings_with_adapter_ids,
            )

        except (
            DBIntegrityError,
            DBNotFoundError,
            ModelConstraintViolation,
        ) as e:
            success_per_trafo[transformation.id].status = UpdateProcessStatus.FAILED

            msg = (
                f"Update of trafo {transformation.name} with tag {transformation.version_tag}"
                f" with id {str(transformation.id)} as part of multiple update failed."
                f" Error was: {str(e)}"
            )
            logger.warning(msg)
            success_per_trafo[transformation.id].msg = msg

            if multi_import_config.abort_on_error:
                abort_msg = (
                    "Aborting multiple update process due to error while updating trafo"
                    f" {transformation.name} with id {transformation.id}. Error was:\n{str(e)}"
                )
                logger.error(abort_msg)
                return success_per_trafo
        else:
            logger.info(
                "Successfully imported transformation revision %s with tag %s with id %s",
                transformation.name,
                transformation.version_tag,
                str(transformation.id),
            )
            success_per_trafo[transformation.id].status = UpdateProcessStatus.SUCCESS

    if multi_import_config.deprecate_older_revisions:
        revision_group_ids = {
            transformation.revision_group_id for _, transformation in trafos_to_process_dict.items()
        }
        logger.info("deprecate all but latest revision of imported revision groups")
        for revision_group_id in revision_group_ids:
            logger.debug(
                "deprecate older revisions of revision group id %s",
                str(revision_group_id),
            )
            deprecate_all_but_latest_in_group(revision_group_id, directly_in_db=True)
    return success_per_trafo


def import_importables(
    importables: Iterable[Importable],
) -> list[dict[UUID | str, TrafoUpdateProcessSummary]]:
    """Import all trafo rev sets from multiple importables"""
    return [import_importable(importable) for importable in importables]


def import_transformations(
    download_path: str,
    strip_wirings: bool = False,
    directly_into_db: bool = False,
    allow_overwrite_released: bool = True,
    update_component_code: bool = True,
    deprecate_older_revisions: bool = False,
) -> None:
    """Import all transforamtions from specified download path.

    This function imports all transformations together with their documentations.
    The download_path should be a path which contains the exported transformations
    organized in subdirectories corresponding to the categories.
    The following parameters can be used to

    - directly_into_db: If direct access to the database is possible, set this to true
        to ommit the detour via the backend
    - strip_wirings: Set to true to reset the test wiring to empty input and output
        wirings for each transformation revision
    - allow_overwrite_released: Set to false to disable overwriting of transformation
        revisions with state "RELEASED" or "DISABLED"
    - update_component_code: Set to false if you want to keep the component code
        unchanged
    - deprecate_older_revisions: Set to true to deprecate all but the latest revision
        for all revision groups imported. This might result in all imported revisions to
        be deprecated if these are older than the latest revision in the database.

    WARNING: Overwrites possibly existing transformation revisions!

    Usage:
        import_transformations("./transformations")
    """

    transformation_dict, _ = load_transformation_revisions_from_directory(download_path)

    ids_by_nesting_level = structure_ids_by_nesting_level(transformation_dict)

    for level in sorted(ids_by_nesting_level):
        logger.info("importing level %i transformation revisions", level)
        for transformation_id in ids_by_nesting_level[level]:
            transformation = transformation_dict[transformation_id]
            update_or_create_transformation_revision(
                transformation,
                directly_in_db=directly_into_db,
                allow_overwrite_released=allow_overwrite_released,
                update_component_code=update_component_code,
                strip_wiring=strip_wirings,
            )

    logger.info("finished importing")

    if deprecate_older_revisions:
        revision_group_ids = {
            transformation.revision_group_id for _, transformation in transformation_dict.items()
        }
        logger.info("deprecate all but latest revision of imported revision groups")
        for revision_group_id in revision_group_ids:
            deprecate_all_but_latest_in_group(revision_group_id, directly_in_db=directly_into_db)


def generate_import_order_file(
    download_path: str, destination: str, transform_py_to_json: bool = False
) -> None:
    """Generate a file with paths sorted in import order.

    Generate a file the paths to all json files in download_path in the order in which they should
    be imported in order to avoid issues due to not yet imported nested revisions.

    To make sure, that all required nested revisions are actually included in those json files it is
    strongly recommended to use the root path of files generated by an export call. Presence of
    required files can only be assured during export. Use the filter features of the export function
    such as 'type', 'categories', 'ids', 'names' and so on instead of subfolders for the import or
    even removing paths from the generated file.

    Set the parameter transform_py_to_json to True, to generate .json files based on the .py files
    for components (if creating TransformationRevisions out of them works) and include their paths
    in the generated file.
    """
    transformation_dict, path_dict = load_transformation_revisions_from_directory(
        download_path, transform_py_to_json
    )

    ids_by_nesting_level = structure_ids_by_nesting_level(transformation_dict)

    with open(os.path.join(destination), "w", encoding="utf8") as file:
        for level in sorted(ids_by_nesting_level):
            logger.info("importing level %i transformation revisions", level)
            for transformation_id in ids_by_nesting_level[level]:
                if transformation_id in path_dict:
                    file.write(path_dict[transformation_id])
                    file.write("\n")
