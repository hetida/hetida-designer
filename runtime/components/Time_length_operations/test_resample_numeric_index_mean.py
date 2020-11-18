import pandas as pd
import numpy as np
import pytest
from .resample_numeric_index_mean import main


def test_series():
    pd.testing.assert_series_equal(
        main(data=pd.Series({0: 0.0, 2: 1.0, 5: 19.0, 7: 20}), d=1)["resampled"],
        pd.Series(
            {0: 0.0, 1: np.nan, 2: 1.0, 3: np.nan, 4: np.nan, 5: 19.0, 6: np.nan, 7: 20}
        ),
    )


def test_df():
    pd.testing.assert_frame_equal(
        main(
            data=pd.DataFrame(
                {"a": [1.2, 7.2, 0.3, 0.5, 0.0], "b": [7.2, 7.0, 7.3, 7.5, 0.0]},
                index=[1, 3, 4, 6, 8],
            ),
            d=2,
        )["resampled"],
        pd.DataFrame(
            {"a": [1.2, 4.2, 0.3, 0.5], "b": [7.2, 7.1, 7.3, 7.5]}, index=[1, 3, 5, 7]
        ),
    )


def test_unsorted():
    with pytest.raises(ValueError, match="data must be sorted by its index"):
        main(data=pd.Series({0: 0.0, 7: 20, 2: 1.0, 5: 19.0}), d=1)


def test_one_row():
    pd.testing.assert_frame_equal(
        main(data=pd.DataFrame({"a": [1.2], "b": [7.2]}, index=[1]), d=2)["resampled"],
        pd.DataFrame({"a": [1.2], "b": [7.2]}, index=[1]),
    )


def test_empty():
    assert main(data=pd.DataFrame(dtype=float), d=1)["resampled"].empty
