import datetime
import io
import json
import logging
from enum import StrEnum
from types import NoneType, UnionType
from typing import Annotated, Any, Literal, TypedDict
from uuid import UUID

import numpy as np
import pandas as pd
import pytz
from plotly.graph_objects import Figure
from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    PlainSerializer,
    PlainValidator,
    ValidationError,
    ValidatorFunctionWrapHandler,
    WrapValidator,
    create_model,
)

logger = logging.getLogger(__name__)

MULTITSFRAME_COLUMN_NAMES = ["timestamp", "metric", "value"]


class WrappedModelWithCustomObjects(BaseModel):
    model: Any = None
    custom_objects: dict[str, Any]


class MetaDataWrapped(BaseModel):
    """Allows to wrap pandas object data with metadata"""

    hd_wrapped_data_object__: Literal["SERIES", "DATAFRAME"] = Field(
        ..., alias="__hd_wrapped_data_object__"
    )
    metadata__: dict[str, Any] = Field(
        ...,
        alias="__metadata__",
        description="Json serializable dictionary of metadata. Will be written"
        "to the resulting pandas object's attrs attribute.",
    )
    data__: dict | list = Field(
        ...,
        alias="__data__",
        description="The actual data which constitutes the pandas object.",
    )
    data_parsing_options__: dict = Field(
        {},
        alias="__data_parsing_options__",
        description=(
            "Additional options for parsing the provided data."
            " For example, setting orient to one of the allowed values for the respective"
            " Pandas type allows to use different json representations for the actual data."
        ),
    )

    model_config = ConfigDict(
        serialize_by_alias=True, validate_by_alias=True, validate_by_name=True
    )


def try_parse_wrapped(
    data: str | dict | list,
    hd_wrapped_data_object: Literal["SERIES", "DATAFRAME"],
) -> MetaDataWrapped:
    if isinstance(data, str):
        wrapped_data = MetaDataWrapped.model_validate_json(data)

        if wrapped_data.hd_wrapped_data_object__ != hd_wrapped_data_object:
            msg = (
                f"Unexpected hd model type: {wrapped_data.hd_wrapped_data_object__}."
                f" Expected {hd_wrapped_data_object}"
            )
            logger.warning(msg)
            raise TypeError(msg)
    else:
        wrapped_data = MetaDataWrapped.model_validate(data)

    return wrapped_data


def parse_wrapped_content(
    v: str | dict | list,
    wrapped_data_objec: Literal["SERIES", "DATAFRAME"],
) -> tuple[str | dict | list, None | dict[str, Any], dict[str, Any]]:
    data_content: str | dict | list
    try:
        wrapped_object = try_parse_wrapped(v, wrapped_data_objec)
        parsed_metadata = wrapped_object.metadata__
        data_content = wrapped_object.data__
        parsing_options = wrapped_object.data_parsing_options__
    except (ValidationError, TypeError) as e:
        logger.debug("Data object is not wrapped: %s", str(e))
        data_content = v
        parsed_metadata = None
        parsing_options = {}

    return data_content, parsed_metadata, parsing_options


def wrap_metadata_as_attrs(
    data_object: pd.Series | pd.DataFrame, metadata: None | dict[str, Any]
) -> pd.Series | pd.DataFrame:  # TODO: make generic: input type = output type
    if metadata is not None:
        data_object.attrs = metadata
    else:
        data_object.attrs = {}
    return data_object


def parse_pandas_data_content(
    data_content: str | dict | list, typ: Literal["series", "frame"], parsing_options: dict
) -> pd.DataFrame | pd.Series:
    try:
        if isinstance(data_content, str):
            parsed_pandas_object = pd.read_json(
                io.StringIO(data_content), typ=typ, **parsing_options
            )
        else:
            parsed_pandas_object = pd.read_json(data_content, typ=typ, **parsing_options)

    except Exception:  # noqa: BLE001
        try:
            parsed_pandas_object = pd.read_json(
                io.StringIO(json.dumps(data_content)), typ=typ, **parsing_options
            )

        except Exception as read_json_exception:  # noqa: BLE001
            raise ValueError(
                "Could not parse provided input as Pandas "
                + ("Series" if typ == "series" else "DataFrame")
            ) from read_json_exception

    return parsed_pandas_object


class DataType(StrEnum):
    """hetida designer data types

    These are the types available for component/workflow inputs/outputs.
    """

    Integer = "INT"
    Float = "FLOAT"
    String = "STRING"
    DataFrame = "DATAFRAME"
    Series = "SERIES"
    MultiTSFrame = "MULTITSFRAME"
    Boolean = "BOOLEAN"
    Any = "ANY"
    PlotlyJson = "PLOTLYJSON"


def parse_pydantic_series(v: pd.Series | str | dict | list) -> pd.Series:
    """Custom pydantic Data Type for parsing Pandas Series

    Parses either a json string according to pandas.read_json
    with typ="series" and default arguments otherwise or
    a Python dict-like data structure using the constructor
    of the pandas.Series class with default arguments.

    Also allows a wrapped variant where metadata can be provided.

    Examples of valid input:
        '{"0":1.0,"1":2.1,"2":3.2}'
        {"0":1.0,"1":2.1,"2":3.2}
        [1.2, 3.5, 2.9]
        '[1.2, 3.5, 2.9]'

    """
    if isinstance(v, pd.Series):
        return v

    if not isinstance(
        v, str | dict | list
    ):  # need to check at runtime since we get objects from user code
        msg = f"Got unexpected type at runtime when parsing Series: {str(type(v))}"
        logger.error(msg)
        raise ValueError(msg)

    data_content, metadata, parsing_options = parse_wrapped_content(v, "SERIES")

    return wrap_metadata_as_attrs(
        parse_pandas_data_content(data_content, "series", parsing_options), metadata
    )


def serialize_series(s: pd.Series) -> dict[str, Any]:
    return {
        "__hd_wrapped_data_object__": "SERIES",
        "__metadata__": s.attrs,
        "__data__": json.loads(
            # double serialization/deserialization in order to serialize both NaN and NaT
            # to null
            s.to_json(
                date_format="iso",
                orient="split",
                # orient="split" serialization is the only way pandas keeps duplicate index
                #  (with possibly different values) entries for Series objects!
            )
        ),
        "__data_parsing_options__": {"orient": "split"},
    }


PydanticPandasSeries = Annotated[
    pd.Series,
    PlainSerializer(serialize_series),
    BeforeValidator(parse_pydantic_series),
]


def parse_pydantic_pandas_data_frame(v: pd.DataFrame | str | dict | list) -> pd.DataFrame:
    """Custom pydantic Data Type for parsing Pandas DataFrames

    Parses either a json string according to pandas.read_json
    with typ="frame" and default arguments otherwise or
    a Python dict-like data structure using the constructor
    of the pandas.DataFrame class with default arguments.

    Additionally a MetaDataWrapped variant of these can be parsed
    and then is equipped with the provided metadata in the `attrs`
    attribute (https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.attrs.html
    """
    if isinstance(v, pd.DataFrame):
        return v

    if not isinstance(
        v, str | dict | list
    ):  # need to check at runtime since we get objects from user code
        msg = f"Got unexpected type at runtime when parsing DataFrame: {str(type(v))}"
        logger.error(msg)
        raise ValueError(msg)

    data_content, metadata, parsing_options = parse_wrapped_content(v, "DATAFRAME")

    return wrap_metadata_as_attrs(
        parse_pandas_data_content(data_content, "frame", parsing_options), metadata
    )


def serialize_dataframe(df: pd.DataFrame) -> dict[str, Any]:
    return {
        "__hd_wrapped_data_object__": "DATAFRAME",
        "__metadata__": df.attrs,
        "__data__": json.loads(
            df.to_json(date_format="iso")  # in order to serialize both NaN and NaT to null
        ),
    }


PydanticPandasDataFrame = Annotated[
    pd.DataFrame,
    PlainSerializer(serialize_dataframe),
    BeforeValidator(parse_pydantic_pandas_data_frame),
]


def validate_multits_properties(  # noqa:PLR0912
    df: pd.DataFrame,
) -> pd.DataFrame:
    if len(df.columns) == 0:
        df = pd.DataFrame(columns=MULTITSFRAME_COLUMN_NAMES)

    if len(df.columns) < 3:
        raise ValueError(
            "MultiTSFrame requires at least 3 columns: metric, timestamp"
            f" and at least one additional columns. Only found {str(df.columns)}"
        )

    if not ({"metric", "timestamp"}.issubset(set(df.columns))):
        column_names_string = ", ".join(df.columns)
        raise ValueError(
            f"The column names {column_names_string} don't contain required columns"
            ' "timestamp" and "metric" for a MultiTSFrame.'
        )

    if df["metric"].isna().any():
        raise ValueError("No null values are allowed for the column 'metric' of a MulitTSFrame.")

    df["metric"] = df["metric"].astype("string")

    if df["timestamp"].isna().any():
        raise ValueError("No null values are allowed for the column 'timestamp' of a MulitTSFrame.")

    if len(df.index) == 0:
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)

    if not isinstance(df["timestamp"].dtype, pd.DatetimeTZDtype):
        raise ValueError(
            "Column 'timestamp' of MultiTSFrame does not have DatetimeTZDtype dtype. "
            f"Got {str(df['timestamp'].dtype)} index dtype instead."
        )

    if not df["timestamp"].dt.tz in (pytz.UTC, datetime.timezone.utc):
        raise ValueError(
            "Column 'timestamp' of MultiTSFrame does not have UTC timezone. "
            f"Got {str(df['timestamp'].dt.tz)} timezone instead."
        )

    return df.sort_values("timestamp")


def parse_pydantic_multi_timeseries_pandas_data_frame(
    v: pd.DataFrame | str | dict | list,
) -> pd.DataFrame:
    if isinstance(v, pd.DataFrame):
        return v

    if not isinstance(
        v, str | dict | list
    ):  # need to check at runtime since we get objects from user code
        msg = f"Got unexpected type at runtime when parsing MultiTsFrame: {str(type(v))}"
        logger.error(msg)
        raise ValueError(msg)

    data_content, metadata, parsing_options = parse_wrapped_content(v, "DATAFRAME")

    new_df = wrap_metadata_as_attrs(
        parse_pandas_data_content(data_content, "frame", parsing_options), metadata
    )

    return validate_multits_properties(new_df)


def serialize_multitsframe(df: pd.DataFrame) -> dict[str, Any]:
    return {
        "__hd_wrapped_data_object__": "DATAFRAME",
        "__metadata__": df.attrs,
        "__data__": json.loads(
            df.to_json(date_format="iso")
        ),  # in order to serialize both NaN and NaT to null
    }


PydanticMultiTimeseriesPandasDataFrame = Annotated[
    pd.DataFrame,
    PlainSerializer(serialize_multitsframe),
    BeforeValidator(parse_pydantic_multi_timeseries_pandas_data_frame),
]


def parse_any(v: Any) -> Any:
    """Tries to parse Any objects somehow intelligently

    Reason is that an object may be provided by the backend either as a proper json-object directly
    in some cases (dict-like objects) or as json-encoded string (happens for example for lists).

    Sometimes, if the frontend is involved, json strings get even double-string-encoded! This is a
    known bug of frontend-backend-runtime interaction.

    Sometimes adapter implementations deliver ANY-data directly as json objects and othertimes
    string-encoded.

    As a workaround for all these cases this class tries to json-parse a string if it receives one
    and only if that does not work it yields the actual string value. If it works and the result is
    itself a string again it tries to json-decode a second time and returns the result if that
    works. Otherwise it returns the result string of the first parsing.

    This workaround is justified by the argument that the user should really use a STRING input if
    a string is expected and not an ANY input. Likewise, adapters should offer string data as STRING
    data sources and not as ANY data sources.
    """
    if isinstance(v, str):
        # try to parse string as json
        try:
            parsed_json_object = json.loads(v)
        except json.decoder.JSONDecodeError:
            logger.info(
                "Could not JSON-parse string %s in Any input."
                " Therefore treating it as actual string value",
                v[:30] + "..." if len(v) > 10 else v,
            )
            return v

        if isinstance(
            parsed_json_object, str
        ):  # sometimes it even gets double-encoded for some reasons
            try:
                parsed_json_object = json.loads(parsed_json_object)
            except json.decoder.JSONDecodeError:
                logger.info(
                    "Could not JSON-parse string %s in Any input. "
                    " Therefore treating it as actual string value",
                    parsed_json_object[:30] + "..." if len(v) > 10 else v,
                )
                return parsed_json_object

        return parsed_json_object
    return v


ParsedAny = Annotated[
    Any,
    BeforeValidator(parse_any),
]


def parse_plotly_json_dict(v: dict) -> dict:
    if isinstance(v, dict):
        # TODO: check structure more thoroughly
        return v

    raise ValueError("Plotly JSON is not a dict object.")


ParsedPlotly = Annotated[dict, PlainValidator(parse_plotly_json_dict)]


def wrap_basic_type_parsing(
    value: Any, handler: ValidatorFunctionWrapHandler, basic_type: type
) -> Any:
    pydantic_parsed_basic_type = handler(value)

    if isinstance(value, basic_type) and value == pydantic_parsed_basic_type:
        return value  # original value to preserve idempotency.
    # Avoids pydantic attribute copying as well.

    return pydantic_parsed_basic_type


ParsedFloat = Annotated[
    float,
    WrapValidator(lambda value, handler: wrap_basic_type_parsing(value, handler, basic_type=float)),
]

ParsedInt = Annotated[
    int,
    WrapValidator(lambda value, handler: wrap_basic_type_parsing(value, handler, basic_type=int)),
]

ParsedBool = Annotated[
    bool,
    WrapValidator(lambda value, handler: wrap_basic_type_parsing(value, handler, basic_type=bool)),
]

ParsedStr = Annotated[
    str,
    WrapValidator(lambda value, handler: wrap_basic_type_parsing(value, handler, basic_type=str)),
]

data_type_map: dict[DataType | None, type] = {
    DataType.Integer: ParsedInt,
    DataType.Float: ParsedFloat,
    DataType.String: ParsedStr,
    DataType.Series: PydanticPandasSeries,
    DataType.MultiTSFrame: PydanticMultiTimeseriesPandasDataFrame,
    DataType.DataFrame: PydanticPandasDataFrame,
    DataType.Boolean: ParsedBool,
    # Any as Type is the correct way to tell pydantic how to parse an arbitrary object:
    DataType.Any: ParsedAny,
    DataType.PlotlyJson: ParsedPlotly,
    None: NoneType,
}

optional_data_type_map: dict[DataType | None, UnionType] = {
    DataType.Integer: ParsedInt | None,
    DataType.Float: ParsedFloat | None,
    DataType.String: ParsedStr | None,
    DataType.Series: PydanticPandasSeries | None,
    DataType.MultiTSFrame: PydanticMultiTimeseriesPandasDataFrame | None,
    DataType.DataFrame: PydanticPandasDataFrame | None,
    DataType.Boolean: ParsedBool | None,
    # Any as Type is the correct way to tell pydantic how to parse an arbitrary object:
    DataType.Any: ParsedAny | None,
    DataType.PlotlyJson: ParsedPlotly | None,
    None: NoneType | None,
}


def serialize_plotly_fig(v: dict[str, Any] | Figure) -> Any:
    if isinstance(v, dict):
        return v

    # possibly quite inefficient (multiple serialisation / deserialization) but
    # guarantees that the PlotlyJSONEncoder is used and so the resulting Json
    # should be definitely compatible with the plotly javascript library:

    # Whats the difference using json.loads(json.dumps(fig_dict_obj, cls=PlotlyJSONEncoder))
    # or employing fig.to_plotly_json()
    return json.loads(v.to_json())


serializer_funcs_by_type = {
    pd.Series: serialize_series,
    pd.DataFrame: lambda v: {
        "__hd_wrapped_data_object__": "DATAFRAME",
        "__metadata__": v.attrs,
        "__data__": json.loads(
            v.to_json(date_format="iso")  # in order to serialize both NaN and NaT to null
        ),
    },
    PydanticPandasSeries: serialize_series,
    PydanticPandasDataFrame: lambda v: {
        "__hd_wrapped_data_object__": "DATAFRAME",
        "__metadata__": v.attrs,
        "__data__": json.loads(
            v.to_json(date_format="iso")  # in order to serialize both NaN and NaT to null
        ),
    },
    PydanticMultiTimeseriesPandasDataFrame: lambda v: {
        "__hd_wrapped_data_object__": "DATAFRAME",
        "__metadata__": v.attrs,
        "__data__": json.loads(
            v.to_json(date_format="iso")
        ),  # in order to serialize both NaN and NaT to null
    },
    np.ndarray: lambda v: v.tolist(),
    datetime.datetime: lambda v: v.isoformat(),
    UUID: lambda v: str(v),  # alternatively: v.hex
    Figure: serialize_plotly_fig,  # lambda v: json.loads(json.dumps(v.to_plotly_json(), cls=PlotlyJSONEncoder)),
    NoneType: lambda x: x,
    None: lambda x: x,
}


class NamedDataTypedValue(TypedDict):
    name: str
    type: DataType  # noqa: A003
    value: Any


def parse_via_pydantic(
    entries: list[NamedDataTypedValue],
    type_map: dict[DataType | None, type] | dict[DataType | None, UnionType] | None = None,
    null_str_to_None: bool = False,
) -> Any:
    """Parse data dynamically into a pydantic object

    Optionally a type_map can be specified which differs from the default data_type_map

    Returns an instantiated pydantic object if no parsing exception is thrown.

    May raise the typical exceptions of pydantic parsing.

    null_str_to_None converts value strings "null" to None before injecting into the Pydantic
    model __init__. This is necessary in order to allow entering null. E.g. consider the
    a int | None type annotation of a model field. Pydantic will happily interpret
    None, 42, "42" correctly but not try to interpret non-int-interpretable strings like
    "null" as None for values in the init method.
    """
    type_dict: dict[str, tuple[type | UnionType, "ellipsis"]] = {  # noqa: F821, UP037
        entry["name"]: (
            type_map[entry["type"]]
            if type_map is not None
            else data_type_map[entry["type"]],  # default to data_type_map
            ...,
        )
        for entry in entries
    }

    DynamicModel = create_model(
        "DynamicyModel",
        **type_dict,
        __config__=ConfigDict(arbitrary_types_allowed=True, coerce_numbers_to_str=True),
    )  # type: ignore

    dyn_obj = DynamicModel(  # type: ignore
        **{
            entry["name"]: (
                entry["value"]
                if (
                    not null_str_to_None
                    or not isinstance(entry["value"], str)
                    or entry["value"] != "null"
                )
                else None
            )
            for entry in entries
        }
    )
    return dyn_obj


def parse_dict_using_data_type_dict(
    data_obj_dict: dict[str, Any],
    data_type_dict: dict[str, DataType],
    nullable: bool = False,
) -> dict[str, Any]:
    entries: list[NamedDataTypedValue] = [
        {"name": key, "type": data_type_dict[key], "value": data_obj}
        for key, data_obj in data_obj_dict.items()
    ]

    parsed_objects = dict(
        parse_via_pydantic(
            entries,
            type_map=data_type_map if nullable is False else optional_data_type_map,
            null_str_to_None=nullable,  # interpretation of "null" string values as None
        )
    )

    return parsed_objects


def parsing_not_identical(
    data_obj_dict: dict[str, Any],
    data_type_dict: dict[str, DataType],
    nullable: bool = False,
) -> dict[str, tuple[str, str]]:
    """Get keys for which parsed object is not identical to the input object

    Parsing according to Datatypes should be idempotent. So if an object is already
    correctly parsed, parsing should be the identity operation and preserve id(..).

    For a dict of objects and corresponding dict of DataTypes this function returns a dict
    containing those keys for which parsing is not the identity, and as value a tuple with first
    entry the actual received object type as string and as second entry the expected hetida designer
    DataType.

    Therefore this function can be used to determine if user produced objects have the correct
    type (i.e. the returned dict is empty!)

    Raises pydantic.ValidationError if parsing fails!
    """
    parsed_objects = parse_dict_using_data_type_dict(data_obj_dict, data_type_dict, nullable)

    not_identical = {
        key: (str(type(data_obj_dict[key])), str(data_type_dict[key]))
        for key, parsed_obj in parsed_objects.items()
        if id(parsed_obj) != id(data_obj_dict[key])
    }

    return not_identical


def parse_dynamically_from_datatypes(
    entries: list[NamedDataTypedValue], nullable: bool = False
) -> Any:
    return parse_via_pydantic(
        entries,
        type_map=data_type_map if nullable is False else optional_data_type_map,
        null_str_to_None=nullable,  # interpretation of "null" string values as None
    )


def parse_single_value_dynamically(
    name: str, value: Any, data_type: DataType, nullable: bool
) -> Any:
    return dict(
        parse_dynamically_from_datatypes(
            [{"name": name, "type": data_type, "value": value}], nullable
        )
    )[name]


def parse_value(value: Any, data_type_str: str, nullable: bool) -> Any:
    return parse_single_value_dynamically("some_value", value, DataType(data_type_str), nullable)


def parse_obj_as_type(obj: Any, target_type: type) -> Any:
    """Parse a type, e.g. Pydantic Custom Data Type

    Unfortunately defining a Pydantic Custom Data Type using Annotated and a BeforeValidator
    will only invoke this BeforeValidator if it is a field of another model. If you call
    it directly on an input object like MyPydanticCustomDataTypeWithBeforeValidator("test"),
    the BeforeValidator will never be called.

    This function is a workaround to this problem
    """

    DynamicModel = create_model(
        "DynamicyModel",
        value=(target_type, ...),
        __config__=ConfigDict(arbitrary_types_allowed=True, coerce_numbers_to_str=True),
    )

    return DynamicModel(value=obj).value  # type: ignore


def parse_default_value(component_info: dict, input_name: str) -> Any:
    """Parse default value from COMPONENT_INFO dict

    Used in component main function header to parse a default
    value from the COMPONENT_INFO dict for an input.
    """
    inp = component_info["inputs"][input_name]
    return parse_value(inp["default_value"], inp["data_type"], True)
