import os

from hetdesrun.adapters.local_file.detect import get_local_files_and_dirs


def test_file_detection():

    found_local_files, found_directories = get_local_files_and_dirs(
        os.path.join("tests", "data", "local_files")
    )

    # found all files in test data dir
    assert len(found_local_files) == 9

    def load_settings_has_semicol_sep(local_file):
        if local_file.parsed_settings_file.load_settings is None:
            return False

        return local_file.parsed_settings_file.load_settings.get("sep", None) == ";"

    files_with_semicol_sep_setting_for_loading = [
        local_file
        for local_file in found_local_files
        if load_settings_has_semicol_sep(local_file)
    ]

    assert len(files_with_semicol_sep_setting_for_loading) == 1

    # directories:

    assert len(found_directories) == 4

    print("FOUND DIRs", found_directories)
    assert (
        len(
            [
                dir_path
                for dir_path in found_directories
                if dir_path.endswith("dir1/dir2/dir3")
            ]
        )
        == 1
    )

    assert "tests/data/local_files/empty_dir" in found_directories
    assert "tests/data/local_files/dir1/dir2" in found_directories
