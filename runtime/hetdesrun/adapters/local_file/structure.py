import os
from typing import Callable, List, Optional, Tuple

from hetdesrun.adapters.exceptions import AdapterHandlingException
from hetdesrun.adapters.local_file.config import local_file_adapter_config
from hetdesrun.adapters.local_file.detect import (
    LocalFile,
    get_local_files_and_dirs,
    local_file_from_path,
)
from hetdesrun.adapters.local_file.models import (
    LocalFileStructureSink,
    LocalFileStructureSource,
    StructureResponse,
    StructureThingNode,
)
from hetdesrun.adapters.local_file.utils import (
    from_url_representation,
    to_url_representation,
)


def source_from_local_file(local_file: LocalFile) -> LocalFileStructureSource:
    return LocalFileStructureSource(
        id=to_url_representation(local_file.path),
        thingNodeId=to_url_representation(local_file.dir_path),
        name=os.path.basename(local_file.path),
        type="dataframe",
        visible=True,
        metadataKey=None,
        path=local_file.path,
        filters={},
    )


def sink_from_local_file(local_file: LocalFile) -> LocalFileStructureSink:
    return LocalFileStructureSink(
        id=to_url_representation(local_file.path),
        thingNodeId=to_url_representation(local_file.dir_path),
        name=os.path.basename(local_file.path),
        type="dataframe",
        visible=True,
        metadataKey=None,
        path=local_file.path,
        filters={},
    )


def local_file_loadable(local_file: LocalFile) -> bool:
    return (
        local_file.parsed_settings_file is None
        or local_file.parsed_settings_file.loadable is None
        or local_file.parsed_settings_file.loadable
    )


def local_file_writable(local_file: LocalFile) -> bool:
    return (
        local_file.parsed_settings_file is not None
        and local_file.parsed_settings_file.writable is not None
        and local_file.parsed_settings_file.writable
    )


def get_structure(parent_id: Optional[str] = None) -> StructureResponse:
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
            (
                f"Requested local file dir {current_dir} not contained in configured "
                f"root directories {str(local_root_dirs)}"
            )
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
        ],
    )


def get_filtered_local_files(
    filter_str: Optional[str],
    selection_criterion_func: Callable[[LocalFile], bool] = local_file_loadable,
) -> List[LocalFile]:
    local_root_dirs = local_file_adapter_config.local_dirs

    gathered_local_files = []

    for local_root_dir in local_root_dirs:
        local_files, _ = get_local_files_and_dirs(local_root_dir, walk_sub_dirs=True)
        gathered_local_files.extend(
            [
                local_file
                for local_file in local_files
                if selection_criterion_func(local_file)
            ]
        )

    if filter_str is not None:
        gathered_local_files = [
            local_file
            for local_file in gathered_local_files
            if filter_str in local_file.path
        ]

    return gathered_local_files


def get_sources(filter_str: Optional[str]) -> List[LocalFileStructureSource]:
    return [
        source_from_local_file(local_file)
        for local_file in get_filtered_local_files(
            filter_str=filter_str, selection_criterion_func=local_file_loadable
        )
    ]


def get_sinks(filter_str: Optional[str]) -> List[LocalFileStructureSink]:
    return [
        sink_from_local_file(local_file)
        for local_file in get_filtered_local_files(
            filter_str=filter_str, selection_criterion_func=local_file_writable
        )
    ]


def get_valid_top_dir(path: str) -> Optional[str]:
    """Configured top dir in which given path resides"""

    local_root_dirs = local_file_adapter_config.local_dirs

    top_dir = None
    for local_root_dir in local_root_dirs:
        if path.startswith(local_root_dir):
            top_dir = local_root_dir
            break

    return top_dir


def get_local_file_by_id(
    id: str,  # pylint: disable=redefined-builtin
) -> Optional[LocalFile]:
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

    if not (
        os.path.exists(local_file.path)
        or os.path.exists(local_file.path + ".settings.json")
    ):
        return None

    return local_file


def get_local_dir_info_from_thing_node_id(
    thing_node_id: str,
) -> Tuple[str, Optional[str]]:
    dir_path = from_url_representation(thing_node_id)

    top_dir = get_valid_top_dir(dir_path)

    if top_dir is None or not os.path.isdir(dir_path):
        return (dir_path, None)

    return dir_path, top_dir


def get_thing_node_by_id(
    id: str,  # pylint: disable=redefined-builtin
) -> Optional[StructureThingNode]:
    dir_path, top_dir = get_local_dir_info_from_thing_node_id(id)

    if top_dir is None:
        return None

    is_top_dir = dir_path == top_dir

    return StructureThingNode(
        id=id,
        name=os.path.basename(dir_path),
        parentId=to_url_representation(os.path.dirname(dir_path))
        if not is_top_dir
        else None,
        description=(
            (
                "Local file directory at "
                if not is_top_dir
                else "Root local file directory at "
            )
            + os.path.abspath(os.path.realpath(dir_path))
        ),
    )


def get_source_by_id(source_id: str) -> Optional[LocalFileStructureSource]:
    """Get a specific source file by id

    Returns None if source could not be found.
    """

    local_file = get_local_file_by_id(source_id)

    if local_file is None or (not local_file_loadable(local_file)):
        return None

    return source_from_local_file(local_file)


def get_sink_by_id(sink_id: str) -> Optional[LocalFileStructureSink]:
    """Get a specific sink file by id

    Returns None if sink could not be found.
    """

    local_file = get_local_file_by_id(sink_id)

    if local_file is None or (not local_file_writable(local_file)):
        return None

    return sink_from_local_file(local_file)
