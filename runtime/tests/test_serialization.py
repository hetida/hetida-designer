import pytest

from hetdesrun.serialization import get_object_path
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
