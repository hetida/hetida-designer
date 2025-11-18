import logging
import os
from collections.abc import Iterable
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from hetdesrun.component.code import ParseDefaultValueError
from hetdesrun.exportimport.utils import (
    deprecate_all_but_latest_in_group,
    import_using_api,
)
from hetdesrun.persistence.dbservice.exceptions import (
    DBIntegrityError,
    DBNestingCycleDetected,
    DBNotFoundError,
)
from hetdesrun.persistence.dbservice.revision import (
    ComponentImportComponentError,
    update_or_create_single_transformation_revision,
)
from hetdesrun.persistence.models.exceptions import ModelConstraintViolation
from hetdesrun.trafoutils.filter.mapping import filter_and_order_trafos
from hetdesrun.trafoutils.io.load import (
    Importable,
    ImportSource,
    MultipleTrafosUpdateConfig,
    load_import_sources,
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
    name: str | None = None
    version_tag: str | None = None


class TrafosUpdateProcessSummary(BaseModel):
    failure: list[str] = []
    ignore: list[str] = []
    success: list[str] = []
    other: list[str] = []
    not_tried: list[str] = []


def _evaluate_success_reports(
    reports: list[dict[UUID | str, TrafoUpdateProcessSummary]],
) -> TrafosUpdateProcessSummary:
    result = TrafosUpdateProcessSummary()
    for report in reports:
        evaluation = _evaluate_single_success_report(report)
        result.failure.extend(evaluation.failure)
        result.ignore.extend(evaluation.ignore)
        result.success.extend(evaluation.success)
        result.other.extend(evaluation.other)
        result.not_tried.extend(evaluation.not_tried)

    return result


def _evaluate_single_success_report(
    report: dict[UUID | str, TrafoUpdateProcessSummary],
) -> TrafosUpdateProcessSummary:
    evaluation = TrafosUpdateProcessSummary()
    for trafo_report in report.values():
        current_trafo = str(trafo_report.name) + " (" + str(trafo_report.version_tag) + ")"
        match trafo_report.status:
            case UpdateProcessStatus.FAILED:
                evaluation.failure.append(current_trafo)
            case UpdateProcessStatus.IGNORED:
                evaluation.ignore.append(current_trafo)
            case UpdateProcessStatus.SUCCESS:
                evaluation.success.append(current_trafo)
            case UpdateProcessStatus.NOT_TRIED:
                evaluation.not_tried.append(current_trafo)
            case _:
                evaluation.other.append(current_trafo)
    return evaluation


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

    logger.debug("Settings for imports are %s", str(multi_import_config))

    for transformation in trafos_to_process:
        logger.debug(
            "Importing transformation %s with tag %s with id %s",
            transformation.name,
            transformation.version_tag,
            str(transformation.id),
            extra={
                "allow_overwrite_released": multi_import_config.allow_overwrite_released,
                "update_component_code": multi_import_config.update_component_code,
                "expand_component_code": multi_import_config.expand_component_code,
                "strip_wiring": multi_import_config.strip_wirings,
                "strip_release_wiring": multi_import_config.strip_release_wirings,
            },
        )

        try:
            update_or_create_single_transformation_revision(
                transformation,
                allow_overwrite_released=multi_import_config.allow_overwrite_released,
                update_component_code=multi_import_config.update_component_code,
                expand_component_code=multi_import_config.expand_component_code,
                strip_wiring=multi_import_config.strip_wirings,
                strip_wirings_with_adapter_ids=multi_import_config.strip_wirings_with_adapter_ids,
                keep_only_wirings_with_adapter_ids=multi_import_config.keep_only_wirings_with_adapter_ids,
                strip_release_wiring=multi_import_config.strip_release_wirings,
                strip_release_wirings_with_adapter_ids=multi_import_config.strip_release_wirings_with_adapter_ids,
                keep_only_release_wirings_with_adapter_ids=multi_import_config.keep_only_release_wirings_with_adapter_ids,
            )

        except (
            DBIntegrityError,
            ComponentImportComponentError,
            DBNestingCycleDetected,
            DBNotFoundError,
            ModelConstraintViolation,
            ParseDefaultValueError,
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
    success_reports = [import_importable(importable) for importable in importables]
    summary = _evaluate_success_reports(success_reports)
    logger.info(
        "Import Summary: %i failed, %i ignored, %i successfully, %i not tried, %i undefined",
        len(summary.failure),
        len(summary.ignore),
        len(summary.success),
        len(summary.not_tried),
        len(summary.other),
        extra={
            "number_failed": len(summary.failure),
            "number_ignored": len(summary.ignore),
            "number_undefined": len(summary.other),
            "failed_workflows": summary.failure,
            "ignored_workflows": summary.ignore,
            "undefined_workflows": summary.other,
        },
    )
    return success_reports


class AutoImportSettings(BaseSettings):
    strip_wirings: bool = Field(
        alias="HD_BACKEND_AUTOIMPORT_DIRECTORY_STRIP_WIRINGS", default=False
    )
    allow_overwrite_released: bool = Field(
        alias="HD_BACKEND_AUTOIMPORT_DIRECTORY_ALLOW_OVERWRITE_RELEASED", default=False
    )
    update_component_code: bool = Field(
        alias="HD_BACKEND_AUTOIMPORT_DIRECTORY_UPDATE_COMPONENT_CODE", default=False
    )
    deprecate_older_revisions: bool = Field(
        alias="HD_BACKEND_AUTOIMPORT_DIRECTORY_DEPRECATE_OLDER_REVISIONS", default=False
    )
    directly_into_db: bool = True


def import_transformations_from_dir(
    import_dir: str,
    strip_wirings: bool = False,
    allow_overwrite_released: bool = False,
    update_component_code: bool = False,
    deprecate_older_revisions: bool = False,
    directly_into_db: bool = False,
) -> None:
    """Import all transformations from specified download path.

    This function imports all transformations together with their documentations.
    The import_dir should be a path which contains the exported transformations
    organized in subdirectories corresponding to the categories.
    The following parameters can be used to

    - strip_wirings: Set to true to reset the test wiring to empty input and output
        wirings for each transformation revision
    - allow_overwrite_released: Set to false to disable overwriting of transformation
        revisions with state "RELEASED" or "DISABLED"
    - update_component_code: Set to false if you want to keep the component code
        unchanged
    - deprecate_older_revisions: Set to true to deprecate all but the latest revision
        for all revision groups imported. This might result in all imported revisions to
        be deprecated if these are older than the latest revision in the database.
    - directly_into_db: If direct access to the database is possible, set this to true
        to ommit the detour via the backend.

    WARNING: Possibly overwrites existing transformation revisions depending on parameter!

    Usage:
        import_transformations_from_dir("./transformations")
    """

    logger.info(
        "Import using the following settings:  dir=%s, strip_wirings=%s,allow_overwrite_released=%s, update_component_code=%s, deprecate_older_revisions=%s",  # noqa: E501
        import_dir,
        strip_wirings,
        allow_overwrite_released,
        update_component_code,
        deprecate_older_revisions,
    )

    importables = load_import_sources([ImportSource(path=import_dir, is_dir=True)])

    if directly_into_db is False:
        logger.info("Using endpoint for auto-import.")

        for importable in importables:
            import_using_api(
                trafos=importable.transformation_revisions,
                allow_overwrite_released=allow_overwrite_released,
                update_component_code=update_component_code,
                strip_wiring=strip_wirings,
                deprecate_older_revisions=deprecate_older_revisions,
            )

    else:
        update_config = MultipleTrafosUpdateConfig(
            strip_wirings=strip_wirings,
            allow_overwrite_released=allow_overwrite_released,
            update_component_code=update_component_code,
            deprecate_older_revisions=deprecate_older_revisions,
        )

        for importable in importables:
            importable.import_config.update_config = update_config

        _ = import_importables(importables)


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
