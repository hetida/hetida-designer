import logging
import os
from collections.abc import Callable

from hetdesrun.adapters.exceptions import AdapterHandlingException
from hetdesrun.adapters.generic_rest.external_types import ExternalType
from hetdesrun.adapters.local_file.config import local_file_adapter_config
from hetdesrun.adapters.local_file.detect import (
    LocalFile,
    get_local_files_and_dirs,
    local_file_from_path,
)
from hetdesrun.adapters.local_file.extensions import handlers_by_extension
from hetdesrun.adapters.local_file.models import (
    FilterType,
    LocalFileStructureSink,
    LocalFileStructureSource,
    StructureFilter,
    StructureResponse,
    StructureThingNode,
)
from hetdesrun.adapters.local_file.utils import (
    from_url_representation,
    to_url_representation,
)

logger = logging.getLogger(__name__)


def source_from_local_file(local_file: LocalFile) -> LocalFileStructureSource:
    file_support_handler = local_file.file_support_handler()
    assert file_support_handler is not None  # for mypy # noqa: S101
    external_type = file_support_handler.adapter_data_type

    return LocalFileStructureSource(
        id=to_url_representation(local_file.path),
        thingNodeId=to_url_representation(local_file.dir_path),
        name=os.path.basename(local_file.path),
        type=external_type,
        visible=True,
        metadataKey=to_url_representation(local_file.path)
        if external_type is ExternalType.METADATA_ANY
        else None,
        path=local_file.path,
        filters={},
    )


def sink_from_local_file(local_file: LocalFile) -> LocalFileStructureSink:
    file_support_handler = local_file.file_support_handler()
    assert file_support_handler is not None  # for mypy # noqa: S101
    external_type = file_support_handler.adapter_data_type

    return LocalFileStructureSink(
        id=to_url_representation(local_file.path),
        thingNodeId=to_url_representation(local_file.dir_path),
        name=os.path.basename(local_file.path),
        type=external_type,
        visible=True,
        metadataKey=to_url_representation(local_file.path)
        if external_type is ExternalType.METADATA_ANY
        else None,
        path=local_file.path,
        filters={},
    )


def local_file_loadable(local_file: LocalFile) -> bool:
    return (
        local_file.parsed_settings_file is None  # loadable by default config
        or local_file.parsed_settings_file.loadable is None  # loadable null is interpreted as True
        or local_file.parsed_settings_file.loadable
    ) and (  # cannot load if extension is not registered
        local_file.file_support_handler() is not None
    )


def local_file_writable(local_file: LocalFile) -> bool:
    return (
        local_file.parsed_settings_file is not None
        and local_file.parsed_settings_file.writable is not None
        and local_file.parsed_settings_file.writable
    ) and (  # cannot load if extension is not registered
        local_file.file_support_handler() is not None
    )


def wrap_in_quotes(string: str) -> str:
    return '"' + string + '"'


def string_list_to_string(string_list: list[str]) -> str:
    return ", ".join(wrap_in_quotes(item) for item in string_list)


def generate_registered_extensions_string(
    allowed_extensions: list[str], generic_sink_type: str
) -> str:
    allowed_extensions_with_registered_file_handler = []
    for allowed_extension in allowed_extensions:
        if allowed_extension in handlers_by_extension:
            allowed_extensions_with_registered_file_handler.append(allowed_extension)
    if len(allowed_extensions_with_registered_file_handler) == 0:
        msg = (
            f"Cannot offer generic {generic_sink_type} sinks, if for no file handler is registered "
            f"for any of the allowed extensions {string_list_to_string(allowed_extensions)}."
        )
        logger.error(msg)
        raise AdapterHandlingException(msg)
    if "..." in allowed_extensions:
        allowed_extensions_with_registered_file_handler.append("...")
    return string_list_to_string(allowed_extensions_with_registered_file_handler)


def generic_any_sink_at_dir(parent_id: str) -> LocalFileStructureSink:
    generic_sink_id = "GENERIC_ANY_SINK_AT_" + parent_id
    registered_extensions_string = generate_registered_extensions_string(
        allowed_extensions=[".pkl", ".h5"], generic_sink_type="ANY"
    )
    return LocalFileStructureSink(
        id=generic_sink_id,
        thingNodeId=parent_id,
        name="New File",
        type=ExternalType.METADATA_ANY,
        visible=True,
        path="Prepared Generic Sink",
        metadataKey=generic_sink_id,
        filters={
            "file_name": StructureFilter(
                name=f"File Name (must end with {registered_extensions_string})",
                type=FilterType.free_text,
                required=False,
            )
        },
    )


def generic_dataframe_sink_at_dir(parent_id: str) -> LocalFileStructureSink:
    generic_sink_id = "GENERIC_DATAFRAME_SINK_AT_" + parent_id
    registered_extensions_string = generate_registered_extensions_string(
        allowed_extensions=[".csv", ".xlsx", ".parquet", "..."],
        generic_sink_type="DATAFRAME",
    )
    return LocalFileStructureSink(
        id=generic_sink_id,
        thingNodeId=parent_id,
        name="New File",
        type=ExternalType.DATAFRAME,
        visible=True,
        path="Prepared Generic Sink",
        metadataKey=generic_sink_id,
        filters={
            "file_name": StructureFilter(
                name=f"File Name (must end with {registered_extensions_string})",
                type=FilterType.free_text,
                required=False,
            )
        },
    )


def get_structure(parent_id: str | None = None) -> StructureResponse:
    """Obtain structure for corresponding adapter web service endpoint

    parent_id is a local path encoded via to_url_representation from the utils module of this
    adapter, or None.
    """

    local_root_dirs = local_file_adapter_config.local_dirs

    if parent_id is None:  # get root Nodes
        return StructureResponse(
            id="local-file-adapter",
            name="Local File Adapter",
            thingNodes=[
                StructureThingNode(
                    id=to_url_representation(dir_path),
                    name=os.path.basename(dir_path),
                    parentId=None,
                    description="Root local file directory at "
                    + os.path.abspath(os.path.realpath(dir_path)),
                )
                for dir_path in local_root_dirs
            ],
            sources=[],
            sinks=[],
        )

    # One level in fiel hierarchy
    current_dir = from_url_representation(parent_id)

    if not len([current_dir.startswith(root_dir) for root_dir in local_root_dirs]) > 0:
        raise AdapterHandlingException(
            f"Requested local file dir {current_dir} not contained in configured "
            f"root directories {str(local_root_dirs)}"
        )

    local_files, dirs = get_local_files_and_dirs(current_dir, walk_sub_dirs=False)

    return StructureResponse(
        id="local-file-adapter",
        name="Local File Adapter",
        thingNodes=[
            StructureThingNode(
                id=to_url_representation(dir_path),
                name=os.path.basename(dir_path),
                parentId=parent_id,
                description="Local file directory at "
                + os.path.abspath(os.path.realpath(dir_path)),
            )
            for dir_path in dirs
        ],
        sources=[
            source_from_local_file(local_file)
            for local_file in local_files
            if local_file_loadable(local_file)
        ],
        sinks=[
            sink_from_local_file(local_file)
            for local_file in local_files
            if local_file_writable(local_file)
        ]
        + (
            [generic_any_sink_at_dir(parent_id)]
            if local_file_adapter_config.generic_any_sink
            else []
        )
        + (
            [generic_dataframe_sink_at_dir(parent_id)]
            if local_file_adapter_config.generic_dataframe_sink
            else []
        ),
    )


def get_filtered_local_files(
    filter_str: str | None,
    selection_criterion_func: Callable[[LocalFile], bool] = local_file_loadable,
) -> list[LocalFile]:
    local_root_dirs = local_file_adapter_config.local_dirs

    gathered_local_files = []

    for local_root_dir in local_root_dirs:
        local_files, _ = get_local_files_and_dirs(local_root_dir, walk_sub_dirs=True)
        gathered_local_files.extend(
            [local_file for local_file in local_files if selection_criterion_func(local_file)]
        )

    if filter_str is not None:
        gathered_local_files = [
            local_file for local_file in gathered_local_files if filter_str in local_file.path
        ]

    return gathered_local_files


def get_sources(filter_str: str | None) -> list[LocalFileStructureSource]:
    return [
        source_from_local_file(local_file)
        for local_file in get_filtered_local_files(
            filter_str=filter_str, selection_criterion_func=local_file_loadable
        )
    ]


def get_sinks(filter_str: str | None) -> list[LocalFileStructureSink]:
    return [
        sink_from_local_file(local_file)
        for local_file in get_filtered_local_files(
            filter_str=filter_str, selection_criterion_func=local_file_writable
        )
    ]
    # TODO: should generic sinks be present for selection in filtered view?


def get_valid_top_dir(path: str) -> str | None:
    """Configured top dir in which given path resides"""

    local_root_dirs = local_file_adapter_config.local_dirs

    top_dir = None
    for local_root_dir in local_root_dirs:
        if path.startswith(local_root_dir):
            top_dir = local_root_dir
            break

    return top_dir


def get_local_file_by_id(
    id: str,  # noqa: A002
    verify_existence: bool = True,
) -> LocalFile | None:
    """Get a specific file by id

    Rudimentarily checks for existence and returns None if local file could not be found
    """
    local_file_path = from_url_representation(id)

    top_dir = get_valid_top_dir(local_file_path)

    if top_dir is None:
        return None

    local_file = local_file_from_path(local_file_path, top_dir=top_dir)

    if local_file is None:
        return None

    if verify_existence and not (
        os.path.exists(local_file.path) or os.path.exists(local_file.path + ".settings.json")
    ):
        return None

    return local_file


def get_local_dir_info_from_thing_node_id(
    thing_node_id: str,
) -> tuple[str, str | None]:
    dir_path = from_url_representation(thing_node_id)

    top_dir = get_valid_top_dir(dir_path)

    if top_dir is None or not os.path.isdir(dir_path):
        return (dir_path, None)

    return dir_path, top_dir


def get_thing_node_by_id(
    id: str,  # noqa: A002
) -> StructureThingNode | None:
    dir_path, top_dir = get_local_dir_info_from_thing_node_id(id)

    if top_dir is None:
        return None

    is_top_dir = dir_path == top_dir

    return StructureThingNode(
        id=id,
        name=os.path.basename(dir_path),
        parentId=to_url_representation(os.path.dirname(dir_path)) if not is_top_dir else None,
        description=(
            ("Local file directory at " if not is_top_dir else "Root local file directory at ")
            + os.path.abspath(os.path.realpath(dir_path))
        ),
    )


def get_source_by_id(source_id: str) -> LocalFileStructureSource | None:
    """Get a specific source file by id

    Returns None if source could not be found.
    """

    local_file = get_local_file_by_id(source_id)

    if local_file is None or (not local_file_loadable(local_file)):
        return None

    return source_from_local_file(local_file)


def get_sink_by_id(sink_id: str) -> LocalFileStructureSink | None:
    """Get a specific sink file by id

    Returns None if sink could not be found.
    """

    if sink_id.startswith("GENERIC_ANY_SINK_AT_"):
        parent_id = sink_id.removeprefix("GENERIC_ANY_SINK_AT_")
        return generic_any_sink_at_dir(parent_id)

    if sink_id.startswith("GENERIC_DATAFRAME_SINK_AT_"):
        parent_id = sink_id.removeprefix("GENERIC_DATAFRAME_SINK_AT_")
        return generic_dataframe_sink_at_dir(parent_id)

    local_file = get_local_file_by_id(sink_id)

    if local_file is None or (not local_file_writable(local_file)):
        return None

    return sink_from_local_file(local_file)
