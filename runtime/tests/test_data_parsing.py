import numpy as np
import pandas as pd
import pytest
from pandas.api.types import is_bool_dtype, is_datetime64_any_dtype, is_float_dtype
from pydantic import BaseModel

from hetdesrun.datatypes import (
    DataType,
    PydanticMultiTimeseriesPandasDataFrame,
    PydanticPandasDataFrame,
    PydanticPandasSeries,
    parse_dynamically_from_datatypes,
)


class ExampleObj(BaseModel):
    s: PydanticPandasSeries


def test_parsing():
    result = parse_dynamically_from_datatypes(
        [
            {"name": "z", "type": DataType.Float, "value": "2.0"},
            {
                "name": "any_object",
                "type": DataType.Any,
                "value": {"a": 2.3, "surname": "Mike"},
            },
            {"name": "any_object_new", "type": DataType.Any, "value": [1, 2, 3]},
        ]
    )

    assert result.z == 2.0
    assert len(result.any_object_new) == 3
    assert len(result.dict()) == 3

    result = parse_dynamically_from_datatypes([])
    assert result.dict() == {}


def test_series_parsing():
    class MySeriesModel(BaseModel):
        s: PydanticPandasSeries

    # test parsing of a string
    s1 = MySeriesModel(s='{"0":1.0,"1":2.1,"2":3.2}').s

    assert len(s1) == 3

    # test parsing of a dictionary
    s2 = MySeriesModel(s={"0": 1.0, "1": 2.1, "2": 3.2}).s
    assert len(s2) == 3

    assert (s1 == s2).all()


def test_dataframe_parsing():
    class MyDfModel(BaseModel):
        df: PydanticPandasDataFrame

    df1 = MyDfModel(df='{"a":{"0":1.0,"1":2.0,"2":null},"b":{"0":1,"1":2,"2":3}}').df

    assert len(df1) == 3
    assert df1.isna()["a"].iloc[1] == False  # noqa: E712
    assert df1.isna()["a"].iloc[2] == True  # noqa: E712
    df2 = MyDfModel(df={"a": {"0": 1.0, "1": 2.0, "2": None}, "b": {"0": 1, "1": 2, "2": 3}}).df

    assert len(df2) == 3
    # nan != nan so df1 == df2 is False once:
    assert (df2 == df1).sum().sum() == 5


def test_multitsframe_parsing():
    class MyMultiTsFrameModel(BaseModel):
        mtsf: PydanticMultiTimeseriesPandasDataFrame

    empty_df_mtsf = MyMultiTsFrameModel(mtsf=("""{}""")).mtsf

    assert len(empty_df_mtsf) == 0

    empty_mtsf = MyMultiTsFrameModel(mtsf=('{"value":[],"metric":[],"timestamp":[]}')).mtsf

    assert len(empty_mtsf) == 0

    mtsf1 = MyMultiTsFrameModel(
        mtsf=(
            '{"value":[1.0,2,"x",1.9,null,"y"],'
            '"metric":["a","b","c","a","b","c"],'
            '"timestamp":["2019-08-01T15:45:36.000Z","2019-08-01T15:45:36.000Z","2019-08-01T15:45:36.000Z",'
            '"2019-08-02T15:45:36.000Z","2019-08-02T15:45:36.000Z","2019-08-02T15:45:36.000Z"]}'
        )
    ).mtsf

    assert len(mtsf1) == 6

    mtsf2 = MyMultiTsFrameModel(
        mtsf={
            "value": [1.0, 2, "x", 1.9, None, "y"],
            "metric": ["a", "b", "c", "a", "b", "c"],
            "timestamp": [
                "2019-08-01T15:45:36.000Z",
                "2019-08-01T15:45:36.000Z",
                "2019-08-01T15:45:36.000Z",
                "2019-08-02T15:45:36.000Z",
                "2019-08-02T15:45:36.000Z",
                "2019-08-02T15:45:36.000Z",
            ],
        }
    ).mtsf
    assert len(mtsf2) == 6
    # nan != nan so mtsf1 == mtsf2 is False once:
    assert (mtsf2 == mtsf1).sum().sum() == 17

    with pytest.raises(ValueError, match=r"don't contain required columns"):
        MyMultiTsFrameModel(
            mtsf={
                "foo": [1.0, 2, "x", 1.9, None, "y"],
                "bar": ["a", "b", "c", "a", "b", "c"],
                "xyz": [
                    "2019-08-01T15:45:36.000Z",
                    "2019-08-01T15:45:36.000Z",
                    "2019-08-01T15:45:36.000Z",
                    "2019-08-02T15:45:36.000Z",
                    "2019-08-02T15:45:36.000Z",
                    "2019-08-02T15:45:36.000Z",
                ],
            }
        )

    with pytest.raises(ValueError, match=r"No null values.*metric"):
        MyMultiTsFrameModel(
            mtsf={
                "value": [1.0, 2, "x", 1.9, None, "y"],
                "metric": ["a", "b", "c", None, "b", "c"],
                "timestamp": [
                    "2019-08-01T15:45:36.000Z",
                    "2019-08-01T15:45:36.000Z",
                    "2019-08-01T15:45:36.000Z",
                    "2019-08-02T15:45:36.000Z",
                    "2019-08-02T15:45:36.000Z",
                    "2019-08-02T15:45:36.000Z",
                ],
            }
        )

    with pytest.raises(ValueError, match=r"No null values.*timestamp"):
        MyMultiTsFrameModel(
            mtsf={
                "value": [1.0, 2, "x", 1.9, None, "y"],
                "metric": ["a", "b", "c", "a", "b", "c"],
                "timestamp": [
                    "2019-08-01T15:45:36.000Z",
                    None,
                    "2019-08-01T15:45:36.000Z",
                    "2019-08-02T15:45:36.000Z",
                    "2019-08-02T15:45:36.000Z",
                    "2019-08-02T15:45:36.000Z",
                ],
            }
        )
    with pytest.raises(ValueError, match="does not have DatetimeTZDtype dtype"):
        MyMultiTsFrameModel(
            mtsf={
                "value": [1.0, 2, "x", 1.9, None, "y"],
                "metric": ["a", "b", "c", "a", "b", "c"],
                "timestamp": [
                    "2019-08-01T15:45:36.000",
                    "2019-08-01T15:45:36.000",
                    "2019-08-01T15:45:36.000",
                    "2019-08-02T15:45:36.000",
                    "2019-08-02T15:45:36.000",
                    "2019-08-02T15:45:36.000",
                ],
            }
        )
    with pytest.raises(ValueError, match="does not have UTC timezone"):
        MyMultiTsFrameModel(
            mtsf={
                "value": [1.0, 2, "x", 1.9, None, "y"],
                "metric": ["a", "b", "c", "a", "b", "c"],
                "timestamp": [
                    "2019-08-01T15:45:36.000+01:00",
                    "2019-08-01T15:45:36.000+01:00",
                    "2019-08-01T15:45:36.000+01:00",
                    "2019-08-02T15:45:36.000+01:00",
                    "2019-08-02T15:45:36.000+01:00",
                    "2019-08-02T15:45:36.000+01:00",
                ],
            }
        )


def test_parsing_of_boolean_series():
    test_obj = ExampleObj(s="[true, true, false]")

    assert is_bool_dtype(test_obj.s.dtype)


def test_parsing_of_null_values():
    test_obj = ExampleObj(s="[null, 1.2, null]")

    assert is_float_dtype(test_obj.s.dtype)
    assert np.isnan(test_obj.s.iloc[0])
    assert np.isnan(test_obj.s.iloc[2])


def test_null_in_integers_parses_as_floats():
    test_obj = ExampleObj(s="[null, 1, null]")

    assert is_float_dtype(test_obj.s.dtype)
    assert np.isnan(test_obj.s.iloc[0])
    assert np.isnan(test_obj.s.iloc[2])


def test_null_in_bool_parses_as_floats():
    test_obj = ExampleObj(s="[null, true, null]")

    assert is_float_dtype(test_obj.s.dtype)
    assert np.isnan(test_obj.s.iloc[0])
    assert np.isnan(test_obj.s.iloc[2])


def test_null_in_timestamps_parses_as_datetimes():
    test_obj = ExampleObj(s='[null, "2020-02-03T14:55:12", null]')

    assert is_datetime64_any_dtype(test_obj.s.dtype)
    assert pd.isna(test_obj.s.iloc[0])
    assert pd.isna(test_obj.s.iloc[2])


def test_parse_series_from_dict_with_null():
    test_obj = ExampleObj(s='{"0": null, "1": 2.4}')
    assert is_float_dtype(test_obj.s.dtype)
    assert np.isnan(test_obj.s.loc[0])


def test_dt_index_parsing():
    test_obj = ExampleObj(s='{"2020-02-03T14:35:12": 1.3, "2020-02-03T14:36:30": 2.4}')
    assert is_float_dtype(test_obj.s.dtype)
    assert len(test_obj.s) == 2
    assert is_datetime64_any_dtype(test_obj.s.index.dtype)


def test_any_parsing():
    result = parse_dynamically_from_datatypes(
        [
            {"name": "float_value", "type": DataType.Any, "value": 2.0},
            {
                "name": "float_value_string_encoded",
                "type": DataType.Any,
                "value": r'"2.0"',
            },
            {
                "name": "float_value_double_string_encoded",
                "type": DataType.Any,
                "value": '"2.0"',
            },
            {"name": "int_value", "type": DataType.Any, "value": 42},
            {
                "name": "any_object",
                "type": DataType.Any,
                "value": {"a": 2.3, "surname": "Mike"},
            },
            {
                "name": "any_object_string_encoded",
                "type": DataType.Any,
                "value": r'"{\"a\":2.3,\"surname\":\"Mike\"}"',
            },
            {
                "name": "any_object_double_string_encoded",
                "type": DataType.Any,
                "value": '"{\\"a\\":2.3,\\"surname\\":\\"Mike\\"}"',
            },
            {"name": "list_object", "type": DataType.Any, "value": ["c", 2, 3]},
            {
                "name": "list_object_string_encoded",
                "type": DataType.Any,
                "value": r'"[\"c\",2,3]"',
            },
            {
                "name": "list_object_double_string_encoded",
                "type": DataType.Any,
                "value": '"[\\"c\\",2,3]"',
            },
            {"name": "actual_str_as_any", "type": DataType.Any, "value": "some_string"},
        ]
    )

    assert isinstance(result.float_value, float)
    assert result.float_value == 2.0

    assert isinstance(result.float_value_string_encoded, float)
    assert result.float_value_string_encoded == 2.0

    assert isinstance(result.float_value_double_string_encoded, float)
    assert result.float_value_double_string_encoded == 2.0

    assert isinstance(result.int_value, int)
    assert result.int_value == 42

    assert result.any_object["a"] == 2.3
    assert result.any_object["surname"] == "Mike"

    assert result.any_object_string_encoded["a"] == 2.3
    assert result.any_object_string_encoded["surname"] == "Mike"

    assert result.any_object_double_string_encoded["a"] == 2.3
    assert result.any_object_double_string_encoded["surname"] == "Mike"

    assert isinstance(result.list_object, list)
    assert result.list_object[0] == "c"
    assert result.list_object[1] == 2
    assert len(result.list_object) == 3

    assert isinstance(result.list_object_string_encoded, list)
    assert result.list_object_string_encoded[0] == "c"
    assert result.list_object_string_encoded[1] == 2
    assert len(result.list_object_string_encoded) == 3

    assert isinstance(result.list_object_double_string_encoded, list)
    assert result.list_object_double_string_encoded[0] == "c"
    assert result.list_object_double_string_encoded[1] == 2
    assert len(result.list_object_double_string_encoded) == 3

    assert result.actual_str_as_any == "some_string"
