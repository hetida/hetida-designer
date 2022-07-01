import json
import os
from typing import List, Optional, Tuple

from pydantic import (  # pylint: disable=no-name-in-module
    BaseModel,
    Field,
    ValidationError,
)

from hetdesrun.adapters.local_file.extensions import (
    FileSupportHandler,
    get_file_support_handler,
)


class SettingsFile(BaseModel):
    """Represents an accompanying file with settings for loading/writing

    Such a file can accompany an actual data file and then contains
    settings for the loading or (over)writing. The settings file has to
    reside at the exact same location with name being the name of the actual data
    file plus ".settings.json".

    A settings file can also occur without a data file: It then typically contains
    the write settings for writing the data file.
    """

    loadable: Optional[bool] = True
    load_settings: Optional[dict] = None
    writable: Optional[bool] = False
    write_settings: Optional[dict] = None


class LocalFile(BaseModel):
    """Represents a local data file with possible accompanyning settings file"""

    root_path: str
    path: str = Field(..., description="Full path to the data file")
    dir_path: str
    settings_file_path: str
    dir_path_from_root_path: str
    parsed_settings_file: Optional[SettingsFile] = Field(...)

    def file_support_handler(self) -> Optional[FileSupportHandler]:
        return get_file_support_handler(self.path)


def parse_settings_file(
    *, data_file_path: str = None, settings_file_path: str = None
) -> SettingsFile:
    if settings_file_path is None:
        if data_file_path is None:
            raise ValueError(
                "Exactly one of 'data_file_path' or 'settings_file_path'"
                " must be not None."
            )
        settings_file_path = data_file_path + ".settings.json"

    try:
        with open(settings_file_path, "r", encoding="utf8") as f:
            loaded_json = json.load(f)
    except IOError:
        print("Settings File could not be found/opened.")
        return SettingsFile()

    except json.JSONDecodeError:  # decoding error
        print("Settings File JSON Decoding Error.")
        return SettingsFile()

    try:
        parsed_settings = SettingsFile.parse_obj(loaded_json)
    except ValidationError as e:
        print(f"Settings File Validation Error: {str(e)}")
        return SettingsFile()

    return parsed_settings


def local_file_from_path(
    file_path: str,
    top_dir: str,
    provide_from_settings_file_if_data_file_present: bool = False,
) -> Optional[LocalFile]:
    """Obtain complete LocalFile datastructure from path to either a data file or a settings file"""

    if file_path.endswith(".settings.json"):  # only config file present

        data_file_path = file_path.rstrip(".settings.json")

        # only infer from settings file if no data file is present:
        if (
            (
                (not os.path.exists(data_file_path))
                or provide_from_settings_file_if_data_file_present
            )
            and (
                (data_file_path.endswith(".csv") or data_file_path.endswith(".csv.zip"))
            )
        ) or provide_from_settings_file_if_data_file_present:
            parsed_settings_file = parse_settings_file(data_file_path=data_file_path)

            if parsed_settings_file.loadable is None:
                parsed_settings_file.loadable = False
            if parsed_settings_file.writable is None:
                parsed_settings_file.loadable = True
            local_file = LocalFile(
                root_path=top_dir,
                path=data_file_path,
                dir_path=os.path.dirname(file_path),
                settings_file_path=data_file_path + ".settings.json",
                dir_path_from_root_path=os.path.relpath(
                    os.path.dirname(file_path), top_dir
                ),
                parsed_settings_file=parsed_settings_file,
            )
            return local_file

    possible_file_support_handler = get_file_support_handler(file_path)

    if possible_file_support_handler is not None:

        parsed_settings_file = parse_settings_file(data_file_path=file_path)

        if parsed_settings_file.loadable is None:
            parsed_settings_file.loadable = True
        if parsed_settings_file.writable is None:
            parsed_settings_file.loadable = False

        local_file = LocalFile(
            root_path=top_dir,
            path=file_path,
            dir_path=os.path.dirname(file_path),
            settings_file_path=file_path + ".settings.json",
            dir_path_from_root_path=os.path.relpath(
                os.path.dirname(file_path), top_dir
            ),
            parsed_settings_file=parsed_settings_file,
        )
        return local_file

    return None


def get_local_files_and_dirs(
    top_dir: str, walk_sub_dirs: bool = True
) -> Tuple[List[LocalFile], List[str]]:
    """Get file and directory structure information

    Returns a list of local files and a list of directory (full) pathes.

    If walk_sub_dirs is True this walks all subdirs from top_dir. Otherwise only the direct content
    of top_dir is returned.
    """
    local_files = []

    sub_directories: List[str] = []

    for root, dirs, files in os.walk(top_dir):
        print(root, dirs, files)
        for file in files:
            file_path = os.path.join(root, file)

            local_file = local_file_from_path(file_path, top_dir)
            if local_file is not None:
                local_files.append(local_file)

        for sub_dir in dirs:
            sub_directories.append(os.path.join(root, sub_dir))

        if not walk_sub_dirs:
            break

    return local_files, sub_directories
