import datetime
import io
import json
import logging
from collections.abc import Generator
from enum import StrEnum
from types import UnionType
from typing import Any, Literal, TypedDict
from uuid import UUID

import numpy as np
import pandas as pd
import pytz
from plotly.graph_objects import Figure
from plotly.utils import PlotlyJSONEncoder
from pydantic import BaseConfig, BaseModel, Field, ValidationError, create_model

logger = logging.getLogger(__name__)

MULTITSFRAME_COLUMN_NAMES = ["timestamp", "metric", "value"]


class ComponentException(Exception):
    """Exception to re-raise exceptions with error code raised in the component code."""

    __is_hetida_designer_exception__ = True

    def __init__(
        self,
        *args: Any,
        error_code: int | str = "",
        extra_information: dict | None = None,
        **kwargs: Any,
    ) -> None:
        if not isinstance(error_code, int | str):
            raise ValueError("The ComponentException.error_code must be int or string!")
        self.error_code = error_code
        self.extra_information = extra_information
        super().__init__(*args, **kwargs)


class ComponentInputValidationException(ComponentException):
    """In code input validation failures"""

    def __init__(
        self,
        *args: Any,
        invalid_component_inputs: list[str],
        error_code: int | str = "",
        **kwargs: Any,
    ) -> None:
        super().__init__(
            *args,
            error_code=error_code,
            extra_information={"invalid_component_inputs": invalid_component_inputs},
            **kwargs,
        )


class WrappedModelWithCustomObjects(BaseModel):
    model: Any
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


def try_parse_wrapped(
    data: str | dict | list,
    hd_wrapped_data_object: Literal["SERIES", "DATAFRAME"],
) -> MetaDataWrapped:
    if isinstance(data, str):
        wrapped_data = MetaDataWrapped.parse_raw(data)  # model_validate_json in pydantic 2.0

        if wrapped_data.hd_wrapped_data_object__ != hd_wrapped_data_object:
            msg = (
                f"Unexpected hd model type: {wrapped_data.hd_wrapped_data_object__}."
                f" Expected {hd_wrapped_data_object}"
            )
            logger.warning(msg)
            raise TypeError(msg)
    else:
        wrapped_data = MetaDataWrapped.parse_obj(data)  # model_validate in pydantic 2.0

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
                + ("Series" if type == "series" else "DataFrame")
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


class PydanticPandasSeries:
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

    @classmethod
    def __get_validators__(cls) -> Generator:
        yield cls.validate

    @classmethod
    def validate(  # noqa: PLR0911,PLR0912
        cls, v: pd.Series | str | dict | list
    ) -> pd.Series:
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


class PydanticPandasDataFrame:
    """Custom pydantic Data Type for parsing Pandas DataFrames

    Parses either a json string according to pandas.read_json
    with typ="frame" and default arguments otherwise or
    a Python dict-like data structure using the constructor
    of the pandas.DataFrame class with default arguments.

    Additionally a MetaDataWrapped variant of these can be parsed
    and then is equipped with the provided metadata in the `attrs`
    attribute (https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.attrs.html
    """

    @classmethod
    def __get_validators__(cls) -> Generator:
        yield cls.validate

    @classmethod
    def validate(cls, v: pd.DataFrame | str | dict | list) -> pd.DataFrame:
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


class PydanticMultiTimeseriesPandasDataFrame:
    """Custom pydantic Data Type for parsing Multi Timeseries Pandas DataFrames

    Parses data as a dataframe similarly to PydanticPandasDataFrame but
    additionally checks the column layout and types to match the conventions
    for a multitsframe.
    """

    @classmethod
    def __get_validators__(cls) -> Generator:
        yield cls.validate_df
        yield cls.validate_multits_properties

    @classmethod
    def validate_df(cls, v: pd.DataFrame | str | dict | list) -> pd.DataFrame:
        if isinstance(v, pd.DataFrame):
            return v

        if not isinstance(
            v, str | dict | list
        ):  # need to check at runtime since we get objects from user code
            msg = f"Got unexpected type at runtime when parsing MultiTsFrame: {str(type(v))}"
            logger.error(msg)
            raise ValueError(msg)

        data_content, metadata, parsing_options = parse_wrapped_content(v, "DATAFRAME")

        return wrap_metadata_as_attrs(
            parse_pandas_data_content(data_content, "frame", parsing_options), metadata
        )

    @classmethod
    def validate_multits_properties(  # noqa:PLR0912
        cls, df: pd.DataFrame
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
            raise ValueError(
                "No null values are allowed for the column 'metric' of a MulitTSFrame."
            )

        df["metric"] = df["metric"].astype("string")

        if df["timestamp"].isna().any():
            raise ValueError(
                "No null values are allowed for the column 'timestamp' of a MulitTSFrame."
            )

        if len(df.index) == 0:
            df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)

        if not isinstance(df["timestamp"].dtype, pd.DatetimeTZDtype):
            raise ValueError(
                "Column 'timestamp' of MultiTSFrame does not have DatetimeTZDtype dtype. "
                f'Got {str(df["timestamp"].dtype)} index dtype instead.'
            )

        if not df["timestamp"].dt.tz in (pytz.UTC, datetime.timezone.utc):
            raise ValueError(
                "Column 'timestamp' of MultiTSFrame does not have UTC timezone. "
                f'Got {str(df["timestamp"].dt.tz)} timezone instead.'
            )

        return df.sort_values("timestamp")


class ParsedAny:
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

    @classmethod
    def __get_validators__(cls) -> Generator:
        yield cls.validate

    @classmethod
    def validate(cls, v: Any) -> Any:
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


data_type_map: dict[DataType, type] = {
    DataType.Integer: int,
    DataType.Float: float,
    DataType.String: str,
    DataType.Series: PydanticPandasSeries,
    DataType.MultiTSFrame: PydanticMultiTimeseriesPandasDataFrame,
    DataType.DataFrame: PydanticPandasDataFrame,
    DataType.Boolean: bool,
    # Any as Type is the correct way to tell pydantic how to parse an arbitrary object:
    DataType.Any: ParsedAny,
    DataType.PlotlyJson: dict,
}

optional_data_type_map: dict[DataType, UnionType] = {
    DataType.Integer: int | None,
    DataType.Float: float | None,
    DataType.String: str | None,
    DataType.Series: PydanticPandasSeries | None,
    DataType.MultiTSFrame: PydanticMultiTimeseriesPandasDataFrame | None,
    DataType.DataFrame: PydanticPandasDataFrame | None,
    DataType.Boolean: bool | None,
    # Any as Type is the correct way to tell pydantic how to parse an arbitrary object:
    DataType.Any: ParsedAny | None,
    DataType.PlotlyJson: dict | None,
}


class AdvancedTypesOutputSerializationConfig(BaseConfig):
    """Enable Pydantic Models to serialize Pandas obejcts with this config class"""

    # Unfortunately there is no good way to get None for NaN or NaT:
    json_encoders = {
        pd.Series: lambda v: {
            "__hd_wrapped_data_object__": "SERIES",
            "__metadata__": v.attrs,
            "__data__": json.loads(
                # double serialization7deserialization in order to serialize both NaN and NaT
                # to null
                v.to_json(
                    date_format="iso",
                    orient="split",
                    # orient="split" serialization is the only way pandas keeps duplicate index
                    #  (with possibly different values) entries for Series objects!
                )
            ),
            "__data_parsing_options__": {"orient": "split"},
        },
        pd.DataFrame: lambda v: {
            "__hd_wrapped_data_object__": "DATAFRAME",
            "__metadata__": v.attrs,
            "__data__": json.loads(
                v.to_json(date_format="iso")  # in order to serialize both NaN and NaT to null
            ),
        },
        PydanticPandasSeries: lambda v: {
            "__hd_wrapped_data_object__": "SERIES",
            "__metadata__": v.attrs,
            "__data__": v.to_dict(),
        },
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
        Figure: lambda v: json.loads(json.dumps(v.to_plotly_json(), cls=PlotlyJSONEncoder)),
    }


class NamedDataTypedValue(TypedDict):
    name: str
    type: DataType  # noqa: A003
    value: Any


def parse_via_pydantic(
    entries: list[NamedDataTypedValue],
    type_map: dict[DataType, type] | dict[DataType, UnionType] | None = None,
) -> BaseModel:
    """Parse data dynamically into a pydantic object

    Optionally a type_map can be specified which differs from the default data_type_map

    Returns an instantiated pydantic object if no parsing exception is thrown.

    May raise the typical exceptions of pydantic parsing.
    """
    type_dict: dict[str, tuple[type | UnionType, "ellipsis"]] = {  # noqa: F821
        entry["name"]: (
            type_map[entry["type"]]
            if type_map is not None
            else data_type_map[entry["type"]],  # default to data_type_map
            ...,
        )
        for entry in entries
    }

    DynamicModel = create_model("DynamicyModel", **type_dict)  # type: ignore

    return DynamicModel(**{entry["name"]: entry["value"] for entry in entries})  # type: ignore


def parse_dynamically_from_datatypes(
    entries: list[NamedDataTypedValue], nullable: bool = False
) -> BaseModel:
    return parse_via_pydantic(
        entries, type_map=data_type_map if nullable is False else optional_data_type_map
    )


def parse_single_value_dynamically(
    name: str, value: Any, data_type: DataType, nullable: bool
) -> Any:
    return parse_dynamically_from_datatypes(
        [{"name": name, "type": data_type, "value": value}], nullable
    ).dict()[name]


def parse_value(value: Any, data_type_str: str, nullable: bool) -> Any:
    return parse_single_value_dynamically("some_value", value, DataType(data_type_str), nullable)


def parse_default_value(component_info: dict, input_name: str) -> Any:
    """Parse default value from COMPONENT_INFO dict

    Used in component main function header to parse a default
    value from the COMPONENT_INFO dict for an input.
    """
    inp = component_info["inputs"][input_name]
    return parse_value(inp["default_value"], inp["data_type"], True)


def plotly_fig_to_json_dict(fig: Figure) -> Any:
    """Turn Plotly figure into a Python dict-like object

    This function can be used in visualization components to obtain the
    correct plotly json-like object from a Plotly Figure object.

    See visualization components from the accompanying base components for
    examples on usage.
    """
    # possibly quite inefficient (multiple serialisation / deserialization) but
    # guarantees that the PlotlyJSONEncoder is used and so the resulting Json
    # should be definitely compatible with the plotly javascript library:
    return json.loads(json.dumps(fig.to_plotly_json(), cls=PlotlyJSONEncoder))


def modify_timezone(
    object_to_convert: pd.Series | pd.DataFrame, to_timezone: str, column_name: str | None = None
) -> pd.Series | pd.DataFrame:
    """Modifies timestamps to a certain timezone

    Keyword arguments:
    object_to_convert -- pd.Series or pd.DataFrame where timezone in index or column is modified
    to_timezone -- timezone into convert, e.g. for German time use Europe/Berlin. See possible timezone strings in pandas tz_convert method or pytz all_timezones list.
    column_name -- column_name to apply, default is index as pd.Series have timestamps in index
    """
    if not isinstance(object_to_convert, pd.Series | pd.DataFrame):
        raise TypeError(
            f"object_to_convert is {type(object_to_convert)} not pd.Series | pd.DataFrame"
        )

    try:
        if isinstance(object_to_convert, pd.Series):
            new_object = object_to_convert.to_frame(name=object_to_convert.name)
        else:
            new_object = object_to_convert.copy(deep=True)

        if column_name is None:
            new_object.index = new_object.index.tz_convert(to_timezone)
        else:
            new_object[column_name] = new_object[column_name].dt.tz_convert(to_timezone)

        if isinstance(object_to_convert, pd.Series):
            new_object = pd.Series(
                new_object[column_name], index=new_object.index, name=object_to_convert.name
            )

        return new_object

    except pytz.exceptions.UnknownTimeZoneError:
        possible_timezone = pytz.all_timezones
        raise ValueError(f"""Timezone not known, please choose from
                            {possible_timezone}""")
    except (TypeError, AttributeError) as exc:
        raise TypeError("Entries to convert do not contain valid timestamps", exc)

    except KeyError as exc:
        raise KeyError(f"Column name {column_name} not in object_to_convert", exc)
