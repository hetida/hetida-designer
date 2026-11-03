from pathlib import Path
from unittest import mock

import pandas as pd
import pytest
from hdhelpers.metadata import META_KEY, attach_metadata, read_metadata

from hetdesrun.serialization import dump_obj, get_object_path, load_obj
from hetdesrun.webservice.config import get_config


@pytest.mark.parametrize(
    ("name", "tag"),
    [
        ("../evil", "1.0"),
        ("model", ".."),
        ("dir/model", "1.0"),
        ("model", "sub/tag"),
        ("model", "back\\slash"),
        ("", "1.0"),
        ("model", ""),
        (".", "1.0"),
        ("model\0", "1.0"),
    ],
)
def test_get_object_path_rejects_path_traversal(name: str, tag: str) -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        get_object_path(name, tag)


def test_get_object_path_accepts_plain_components() -> None:
    path = get_object_path("my_model", "v1.0")
    assert path.endswith("my_model_v1.0")
    assert get_config().model_repo_path in path


def test_stored_object_contains_the_json_form_of_attached_metadata(tmp_path: Path) -> None:
    series = pd.Series([1.0], index=pd.to_datetime(["2026-10-18T06:00:00Z"]))
    series.attrs = {
        "dataset_metadata": {
            "metric_key": "id",
            "single_metric": "a",
            "queried_metrics": ["a"],
            "ref_interval_start_timestamp": "2026-10-18T00:00:00Z",
            "ref_interval_end_timestamp": "2026-10-19T00:00:00Z",
            "ref_interval_type": "closed",
        },
        "metrics": [
            {
                "id": "a",
                "name": "A",
                "value_dimensions": [{"column": "value", "unit": "m", "measurement": None}],
            }
        ],
        "other": 1,
    }
    expected_attrs = dict(series.attrs)
    attach_metadata(series)

    with mock.patch.object(get_config(), "model_repo_path", str(tmp_path)):
        dump_obj(series, "series", "1.0.0")
        loaded = load_obj("series", "1.0.0")
        stored = Path(get_object_path("series", "1.0.0")).read_bytes()

    assert b"hdhelpers" not in stored
    assert loaded.attrs == expected_attrs
    assert read_metadata(loaded, "SERIES", required=True).unit() == "m"
    # the stored object keeps its attached model
    assert META_KEY in series.attrs
