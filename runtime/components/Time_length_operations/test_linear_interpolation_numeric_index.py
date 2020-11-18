import pandas as pd
import numpy as np
import pytest
from .linear_interpolation_numeric_index import main


def test_series():
    pd.testing.assert_series_equal(
        main(data=pd.Series({0: 0.0, 2: 1.0, 5: 19.0, 7: 20}), d=1)["interpolation"],
        pd.Series({0: 0.0, 1: 0.5, 2: 1.0, 3: 7.0, 4: 13.0, 5: 19.0, 6: 19.5, 7: 20}),
    )


def test_df():
    pd.testing.assert_frame_equal(
        main(
            data=pd.DataFrame(
                {"a": [1.2, 7.2, 0.3, 0.5, 0.0], "b": [7.2, 7.0, 7.3, 7.5, 0.0]},
                index=[1, 3, 4, 6, 8],
            ),
            d=2,
        )["interpolation"],
        pd.DataFrame(
            {"a": [1.2, 7.2, 0.4, 0.25], "b": [7.2, 7.0, 7.4, 3.75]}, index=[1, 3, 5, 7]
        ),
    )


def test_one_row():
    pd.testing.assert_frame_equal(
        main(data=pd.DataFrame({"a": [1.2], "b": [7.2]}, index=[1]), d=2)[
            "interpolation"
        ],
        pd.DataFrame({"a": [1.2], "b": [7.2]}, index=[1]),
    )


def test_empty():
    assert main(data=pd.DataFrame(dtype=float), d=1)["interpolation"].empty
