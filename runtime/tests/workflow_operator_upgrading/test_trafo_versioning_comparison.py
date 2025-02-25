from datetime import datetime
from unittest.mock import Mock

from hetdesrun.trafoutils.versioning import get_newest_released_revision


def test_get_newest():
    trafo_1 = Mock()
    trafo_1.version_tag = "3.0.1"
    trafo_1.released_timestamp = datetime(year=2025, month=1, day=1)  # noqa: DTZ001

    trafo_2 = Mock()
    trafo_2.version_tag = "3.0.2"
    trafo_2.released_timestamp = datetime(year=2025, month=1, day=2)  # noqa: DTZ001

    trafo_3 = Mock()
    trafo_3.version_tag = "fff"
    trafo_3.released_timestamp = datetime(year=2025, month=1, day=3)  # noqa: DTZ001

    trafo_4 = Mock()
    trafo_4.version_tag = "eee"

    trafos = [trafo_1, trafo_2, trafo_3]

    newest = get_newest_released_revision(trafos)
    assert newest.version_tag == "3.0.2"

    newest = get_newest_released_revision(trafos, use_release_date=True)
    assert newest.released_timestamp == datetime(year=2025, month=1, day=3)  # noqa: DTZ001

    newest = get_newest_released_revision([trafo_4, trafo_3])
    assert newest is None
