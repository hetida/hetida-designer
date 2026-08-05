import re
from io import StringIO
from uuid import uuid4

import numpy as np
import pandas as pd
import pytest
from fastapi.encoders import jsonable_encoder
from pandas.api.types import is_bool_dtype, is_datetime64_any_dtype, is_float_dtype
from pydantic import BaseModel, ConfigDict, ValidationError

from hdutils import (
    MetaDataWrapped,
    PydanticPandasSeries,
    parse_obj_as_type,
    parse_pandas_data_content,
    parse_wrapped_content,
    parsing_not_identical,
    wrap_metadata_as_attrs,
)
from hetdesrun.backend.models.info import ExecutionResponseFrontendDto
from hetdesrun.datatypes import (
    DataType,
    PydanticMultiTimeseriesPandasDataFrame,
    PydanticPandasDataFrame,
    PydanticSingleTimeseriesPandasDataFrame,
    parse_dynamically_from_datatypes,
)
from hetdesrun.models.run import WorkflowExecutionResult
from hetdesrun.service.serialization_helpers import handle_frontend_exec_response_dict_serialisation


class ExampleObj(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
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
    assert len(result.model_dump()) == 3

    result = parse_dynamically_from_datatypes([])
    assert result.model_dump() == {}


def test_series_parsing():
    class MySeriesModel(BaseModel):
        s: PydanticPandasSeries

        model_config = ConfigDict(arbitrary_types_allowed=True, coerce_numbers_to_str=True)

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

        model_config = ConfigDict(arbitrary_types_allowed=True, coerce_numbers_to_str=True)

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
        model_config = ConfigDict(arbitrary_types_allowed=True, coerce_numbers_to_str=True)

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


class MySingleTsFrameModel(BaseModel):
    stsf: PydanticSingleTimeseriesPandasDataFrame
    model_config = ConfigDict(arbitrary_types_allowed=True, coerce_numbers_to_str=True)


def test_singletsframe_parsing_empty():
    empty_df_stsf = MySingleTsFrameModel(stsf=("""{}""")).stsf

    assert len(empty_df_stsf) == 0
    assert list(empty_df_stsf.columns) == ["timestamp", "value"]

    empty_stsf = MySingleTsFrameModel(stsf=('{"value":[],"timestamp":[]}')).stsf

    assert len(empty_stsf) == 0


def test_singletsframe_parsing_multi_dimensional():
    """A SingleTSFrame holds one metric with arbitrarily many value dimensions"""
    stsf1 = MySingleTsFrameModel(
        stsf=(
            '{"value":[1.0,2,1.9],'
            '"state":["ok","ok","suspicious"],'
            '"timestamp":["2019-08-01T15:45:36.000Z","2019-08-02T15:45:36.000Z",'
            '"2019-08-03T15:45:36.000Z"]}'
        )
    ).stsf

    assert len(stsf1) == 3
    assert set(stsf1.columns) == {"timestamp", "value", "state"}
    assert isinstance(stsf1["timestamp"].dtype, pd.DatetimeTZDtype)

    stsf2 = MySingleTsFrameModel(
        stsf={
            "value": [1.0, 2, 1.9],
            "state": ["ok", "ok", "suspicious"],
            "timestamp": [
                "2019-08-01T15:45:36.000Z",
                "2019-08-02T15:45:36.000Z",
                "2019-08-03T15:45:36.000Z",
            ],
        }
    ).stsf

    # 3 rows x 3 columns, all equal
    assert (stsf2 == stsf1).sum().sum() == 9


def test_singletsframe_parsing_sorts_by_timestamp():
    stsf = MySingleTsFrameModel(
        stsf={
            "value": [3.0, 1.0, 2.0],
            "timestamp": [
                "2019-08-03T15:45:36.000Z",
                "2019-08-01T15:45:36.000Z",
                "2019-08-02T15:45:36.000Z",
            ],
        }
    ).stsf

    assert list(stsf["value"]) == [1.0, 2.0, 3.0]


def test_singletsframe_parsing_allows_metric_column_as_value_dimension():
    """In contrast to a MultiTSFrame, "metric" is an ordinary value column here"""
    stsf = MySingleTsFrameModel(
        stsf={
            "metric": ["a", None],
            "timestamp": ["2019-08-01T15:45:36.000Z", "2019-08-02T15:45:36.000Z"],
        }
    ).stsf

    assert set(stsf.columns) == {"timestamp", "metric"}
    assert stsf["metric"].isna().sum() == 1


def test_singletsframe_parsing_validation_errors():
    with pytest.raises(ValueError, match=r"at least one value column"):
        MySingleTsFrameModel(stsf={"timestamp": ["2019-08-01T15:45:36.000Z"]})

    with pytest.raises(ValueError, match=r"don't contain the required column"):
        MySingleTsFrameModel(stsf={"foo": [1.0], "bar": ["2019-08-01T15:45:36.000Z"]})

    with pytest.raises(ValueError, match=r"No null values.*timestamp"):
        MySingleTsFrameModel(
            stsf={
                "value": [1.0, 2.0],
                "timestamp": ["2019-08-01T15:45:36.000Z", None],
            }
        )

    with pytest.raises(ValueError, match="does not have DatetimeTZDtype dtype"):
        MySingleTsFrameModel(
            stsf={
                "value": [1.0, 2.0],
                "timestamp": ["2019-08-01T15:45:36.000", "2019-08-02T15:45:36.000"],
            }
        )

    with pytest.raises(ValueError, match="does not have UTC timezone"):
        MySingleTsFrameModel(
            stsf={
                "value": [1.0, 2.0],
                "timestamp": ["2019-08-01T15:45:36.000+01:00", "2019-08-02T15:45:36.000+01:00"],
            }
        )


def test_singletsframe_parsing_wrapped_with_metadata():
    stsf = MySingleTsFrameModel(
        stsf={
            "__hd_wrapped_data_object__": "DATAFRAME",
            "__metadata__": {"dataset_metadata": {"single_metric": "abc.temp"}},
            "__data__": {
                "value": {"0": 1.0},
                "timestamp": {"0": "2019-08-01T15:45:36.000Z"},
            },
        }
    ).stsf

    assert stsf.attrs["dataset_metadata"]["single_metric"] == "abc.temp"
    assert len(stsf) == 1


def test_singletsframe_back_and_forth_parsing():
    """Parsing a serialized SingleTSFrame must yield the same frame again"""
    stsf = MySingleTsFrameModel(
        stsf={
            "value": [1.0, np.nan],
            "state": ["ok", None],
            "timestamp": ["2019-08-01T15:45:36.000Z", "2019-08-02T15:45:36.000Z"],
        }
    ).stsf
    stsf.attrs = {"dataset_metadata": {"single_metric": "abc.temp"}}

    serialized = MySingleTsFrameModel(stsf=stsf).model_dump()["stsf"]

    assert serialized["__hd_wrapped_data_object__"] == "DATAFRAME"

    reparsed = MySingleTsFrameModel(stsf=serialized).stsf

    assert reparsed.attrs == stsf.attrs
    pd.testing.assert_frame_equal(reparsed, stsf)


def test_singletsframe_parsing_is_idempotent():
    stsf = MySingleTsFrameModel(
        stsf={
            "value": [1.0],
            "timestamp": ["2019-08-01T15:45:36.000Z"],
        }
    ).stsf

    not_identical = parsing_not_identical(
        {"stsf": stsf}, {"stsf": DataType.SingleTSFrame}, nullable=False
    )

    assert not_identical == {}


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


def test_pydantic_pandas_series_wrapped_metadata_parsing():
    wrapped_series_dict = {
        "__hd_wrapped_data_object__": "SERIES",
        "__metadata__": {},
        "__data__": {
            "name": None,
            "index": ["2020-05-01T00:00:00.000Z", "2020-05-01T02:00:00.000Z"],
            "data": ["2020-05-01T01:00:00.000", None],
        },
        "__data_parsing_options__": {"orient": "split"},
    }

    wrapped = MetaDataWrapped(**wrapped_series_dict)
    assert wrapped.data_parsing_options__ == {"orient": "split"}

    data_content, metadata, parsing_options = parse_wrapped_content(wrapped_series_dict, "SERIES")

    parsed_pandas_obj = parse_pandas_data_content(
        data_content, "series", parsing_options=parsing_options
    )

    assert len(parsed_pandas_obj) == 2

    metadata_wrapped_series = wrap_metadata_as_attrs(parsed_pandas_obj, metadata)
    assert len(metadata_wrapped_series) == 2

    s = parse_obj_as_type(wrapped_series_dict, PydanticPandasSeries)
    assert len(s) == 2


def test_jsonable_encoder():
    direct_return_data = {
        "output": {
            "__hd_wrapped_data_object__": "SERIES",
            "__metadata__": {},
            "__data__": {
                "name": None,
                "index": ["2020-05-01T00:00:00.000Z", "2020-05-01T02:00:00.000Z"],
                "data": ["2020-05-01T01:00:00.000", None],
            },
            "__data_parsing_options__": {"orient": "split"},
        }
    }

    outp_name_to_datatype_map = {"output": DataType.Series}

    wf_exec_result = WorkflowExecutionResult(
        result="ok",
        node_results=None,
        output_types_by_output_name=outp_name_to_datatype_map,
        output_results_by_output_name=direct_return_data,
        job_id=uuid4(),
        tr_name="Test",
        tr_tag="1.0.0",
        tr_id=uuid4(),
    )

    jsonable_encoder(wf_exec_result)


def test_string_series_parsing():
    val = (
        '{"2020-05-01T00:00:00.000Z":2.5340945967,"2020-05-01T01:00:00.000Z":2.5658768256,'
        '"2020-05-01T02:00:00.000Z":2.570679579}'
    )
    target_type = PydanticPandasSeries
    parsed_obj = parse_obj_as_type(val, target_type)
    assert isinstance(parsed_obj, pd.Series)


def test_parsing_idempotency():
    not_identical = parsing_not_identical(
        {
            "series": pd.Series([1, 2, 3]),
            "dataframe": pd.DataFrame({"a": [1, 2, 3], "b": [0.5, 2, 6.7]}),
            "multitsframe": pd.DataFrame(
                {"timestamp": pd.to_datetime(["2025-01-01"]), "metric": ["a"], "value": [42.2]}
            ),
            "str": "some string",
            "int": 42,
            "float": 42.2,
            "bool": True,
            "any": {"c": {"a": 3, "b": [1, 2, 3]}},
            "plotlyjson": {"data": {}, "layout": {}, "config": {}},
        },
        {
            "series": DataType.Series,
            "dataframe": DataType.DataFrame,
            "multitsframe": DataType.MultiTSFrame,
            "str": DataType.String,
            "int": DataType.Integer,
            "float": DataType.Float,
            "bool": DataType.Boolean,
            "any": DataType.Any,
            "plotlyjson": DataType.PlotlyJson,
        },
    )
    assert len(not_identical) == 0

    pattern = re.compile(
        r".*series.*dataframe.*multitsframe.*str.*int.*float.*bool.*plotlyjson.*", re.DOTALL
    )
    with pytest.raises(
        ValidationError,
        match=pattern,
    ):
        not_identical = parsing_not_identical(
            {
                "series": None,
                "dataframe": None,
                "multitsframe": None,
                "str": None,
                "int": None,
                "float": None,
                "bool": None,
                "any": None,
                "plotlyjson": None,
            },
            {
                "series": DataType.Series,
                "dataframe": DataType.DataFrame,
                "multitsframe": DataType.MultiTSFrame,
                "str": DataType.String,
                "int": DataType.Integer,
                "float": DataType.Float,
                "bool": DataType.Boolean,
                "any": DataType.Any,
                "plotlyjson": DataType.PlotlyJson,
            },
            nullable=False,
        )

    not_identical = parsing_not_identical(
        {
            "series": None,
            "dataframe": None,
            "multitsframe": None,
            "str": None,
            "int": None,
            "float": None,
            "bool": None,
            "any": None,
            "plotlyjson": None,
        },
        {
            "series": DataType.Series,
            "dataframe": DataType.DataFrame,
            "multitsframe": DataType.MultiTSFrame,
            "str": DataType.String,
            "int": DataType.Integer,
            "float": DataType.Float,
            "bool": DataType.Boolean,
            "any": DataType.Any,
            "plotlyjson": DataType.PlotlyJson,
        },
        nullable=True,
    )
    assert len(not_identical) == 0


def test_direct_provisioning_output_handling():
    """Test parsing and serialization for direct provisioning results

    Ensure that double serialization issues can be mitigated using the appropriate
    Pydantic validation context / serialization context options or resp. the
    corresponding handle_frontend_exec_response_dict_serialisation kwargs for
    serialization
    """

    s = "2025-05-19T08:27:13+00:00"
    series = pd.Series([s], index=[s])

    assert pd.api.types.is_string_dtype(series.dtype)
    assert pd.api.types.is_string_dtype(series.index.dtype)

    round_trip_series = pd.read_json(StringIO(series.to_json()), typ="series")

    # round trip is not identity
    assert str(round_trip_series.dtype) == "datetime64[us, UTC]"
    assert str(round_trip_series.index.dtype) == "datetime64[us, UTC]"

    # So we have an example where a second serialization / deserialization
    # would be harmful!

    # Now fix tghis actively by setting some kwargs for read_json:
    round_trip_series_without_inference = pd.read_json(
        StringIO(series.to_json()), typ="series", convert_axes=False, convert_dates=False
    )

    assert pd.api.types.is_string_dtype(round_trip_series_without_inference.dtype)
    assert pd.api.types.is_string_dtype(round_trip_series_without_inference.index.dtype)

    assert round_trip_series_without_inference.iloc[0] == s
    assert round_trip_series_without_inference.index[0] == s

    assert len(round_trip_series_without_inference) == 1

    # So this roundtrip is the identity

    # However we cannot handle all those situations => Sometimes datetime parsing
    # is wanted and we do not want to make everything explicit thereby
    # deviating from Pandas default behaviour.

    exec_response = ExecutionResponseFrontendDto(
        result="success",
        output_results_by_output_name={"s": series},
        output_types_by_output_name={"s": "SERIES"},
        job_id="a14a0d6d-1ea9-4a75-958f-9649173475b1",
        tr_tag="1.0.0",
        tr_name="TEST",
        tr_id="a14a0d6d-1ea9-4a75-958f-9649173475b1",
    )

    serialized = handle_frontend_exec_response_dict_serialisation(exec_response)
    output_series_rep = serialized["output_results_by_output_name"]["s"]
    assert output_series_rep["__data__"]["data"][0] == s
    assert output_series_rep["__data__"]["index"][0] == s

    second_serialized = handle_frontend_exec_response_dict_serialisation(
        ExecutionResponseFrontendDto.model_validate(serialized)
    )
    second_output_series_rep = second_serialized["output_results_by_output_name"]["s"]
    assert second_output_series_rep["__data__"]["data"][0] != s
    assert second_output_series_rep["__data__"]["index"][0] != s

    with_untouched_output = ExecutionResponseFrontendDto.model_validate(
        serialized,
        context={"result_validation": False},  # do not touch output results
    )

    # output result now should not be a Series object, but only a dict-like rep
    assert isinstance(with_untouched_output.output_results_by_output_name["s"], dict)

    second_serialized_naive = handle_frontend_exec_response_dict_serialisation(
        with_untouched_output,
        enforce_naive_result_serialization=True,
    )
    second_output_series_rep_naive = second_serialized_naive["output_results_by_output_name"]["s"]
    assert second_output_series_rep_naive["__data__"]["data"][0] == s
    assert second_output_series_rep_naive["__data__"]["index"][0] == s
