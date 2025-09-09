import logging
from typing import Any
from uuid import UUID

from hetdesrun.exportimport.utils import get_transformation_revisions
from hetdesrun.models.code import NonEmptyValidStr, ValidStr
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.trafoutils.filter.params import FilterParams
from hetdesrun.trafoutils.io.save import save_transformation_into_directory
from hetdesrun.utils import State, Type

logger = logging.getLogger(__name__)


def selection_list_empty_or_contains_value(
    selection_list: list[Any] | None, actual_value: Any
) -> bool:
    if selection_list is None:
        return True
    return actual_value in selection_list


def criterion_unset_or_matches_value(criterion: Any | None, actual_value: Any) -> bool:
    if criterion is None:
        return True
    return bool(actual_value == criterion)


def passes_all_filters(
    trafo_json: Any,
    type: Type | None = None,  # noqa: A002
    categories: list[ValidStr] | None = None,
    ids: list[UUID | str] | None = None,
    names: list[NonEmptyValidStr] | None = None,
    include_deprecated: bool = True,
) -> bool:
    filter_type = criterion_unset_or_matches_value(type, Type(trafo_json["type"]))
    filter_ids = selection_list_empty_or_contains_value(ids, UUID(trafo_json["id"]))
    filter_names = selection_list_empty_or_contains_value(names, trafo_json["name"])
    filter_categories = selection_list_empty_or_contains_value(categories, trafo_json["category"])
    filter_state = include_deprecated or trafo_json["state"] != State.DISABLED

    combined_filter = (
        filter_type and filter_ids and filter_names and filter_categories and filter_state
    )

    return combined_filter


def convert_id_type_to_uuid(
    ids: list[UUID | str] | None,
) -> list[UUID | str] | None:
    if ids is None:
        return None
    return [UUID(id_) for id_ in ids if isinstance(id_, str)]


##Export transformations based on type, id, name and category if provided
def export_transformations(
    download_path: str,
    type: Type | None = None,  # noqa: A002
    state: State | None = None,
    categories: list[ValidStr] | None = None,
    category_prefix: ValidStr | None = None,
    ids: list[UUID | str] | None = None,
    names: list[NonEmptyValidStr] | None = None,
    include_deprecated: bool = True,
    components_as_code: bool = False,
    expand_component_code: bool = False,
    directly_from_db: bool = False,
) -> None:
    """Export transformation revisions.

    Exports all transformations, together with their documentation, and saves them as json files
    in subdirectories of the provided path corresponding to the respective category,
    based on the provide criteria. If more than one criterion is provided,
    only transformations which fulfilll all criteria will be exported.

    WARNING: Overwrites existing files with the same name!

    Arguments:
        download_path (str): The directory on the local system, where we save the transformations.

    Keyword Arguments:
        type (Type): One of the two values of the enum Type: WORKFLOW or COMPONENT
        state (State): One of the three values of the enum State: DRAFT, RELEASED or DISABLED
        category (str): The category of the transformations.
        ids (List[UUID]): The ids of the transformations.
        names (List[str]): The names of the transformations.
        include_deprecated (bool = True): Set to False to export only transformation revisions
            with state DRAFT or RELEASED.
        components_as_code (bool = False): Set to True to obtain python files instead of json files
            for components.
        expand_component_code (bool = False): Set to True to add the documentation as module
            docstring and the test wiring as dictionary to the component code.
        directly_from_db (bool = False): Set to True to export directly from the databse.

    Usage examples:
        export_transformations("/mnt/obj_repo/migration_data")
        export_transformations(
            "/mnt/obj_repo/migration_data",
            ids=["d71a0cef-1d56-818f-a1a5-dd6bb6d50399","806df1b9-2fc8-4463-943f-3d258c569663"]
        )
        export_transformations("/mnt/obj_repo/migration_data/components", type="COMPONENT")
        export_transformations(
            "/mnt/obj_repo/migration_data/components",
            type="COMPONENT",
            names=["Divide", "Add"]
        )
        export_transformations(
            "/mnt/obj_repo/migration_data/workflows",
            type="WORKFLOW",
            category="Examples"
        )

    """
    import hetdesrun.models.wiring  # noqa: PLC0415

    hetdesrun.models.wiring.ALLOW_UNCONFIGURED_ADAPTER_IDS_IN_WIRINGS = True

    transformation_list: list[TransformationRevision] = []

    params = FilterParams(
        type=type,
        state=state,
        categories=categories,
        category_prefix=category_prefix,
        ids=ids,
        names=names,
        include_dependencies=True,
        include_deprecated=include_deprecated,
    )

    transformation_list = get_transformation_revisions(
        params=params, directly_from_db=directly_from_db
    )

    # Export individual transformation
    for transformation in transformation_list:
        save_transformation_into_directory(
            transformation, download_path, components_as_code, expand_component_code
        )
