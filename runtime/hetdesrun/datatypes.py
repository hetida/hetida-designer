import datetime
import json
import logging
from collections.abc import Generator
from enum import Enum
from typing import Any, TypedDict
from uuid import UUID

import numpy as np
import pandas as pd
import pytz
from plotly.graph_objects import Figure
from plotly.utils import PlotlyJSONEncoder
from pydantic import BaseConfig, BaseModel, create_model

logger = logging.getLogger(__name__)

MULTITSFRAME_COLUMN_NAMES = ["timestamp", "metric", "value"]


class DataType(str, Enum):
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
    of the pandas.Series class with default arguments

    Examples of valid input:
        '{"0":1.0,"1":2.1,"2":3.2}'
        {"0":1.0,"1":2.1,"2":3.2}

    """

    @classmethod
    def __get_validators__(cls) -> Generator:
        yield cls.validate

    @classmethod
    def validate(cls, v: pd.Series | str | dict | list) -> pd.Series:
        if isinstance(v, pd.Series):
            return v
        try:
            return pd.read_json(v, typ="series")

        except TypeError:  # https://github.com/pandas-dev/pandas/issues/31464
            try:
                return pd.read_json(v, typ="series", convert_dates=False)

            except Exception as e:  # noqa: BLE001
                raise ValueError(
                    "Could not parse provided input as Pandas Series even with convert_dates=False"
                ) from e

        except Exception:  # noqa: BLE001
            try:
                return pd.read_json(json.dumps(v), typ="series")

            except TypeError:  # https://github.com/pandas-dev/pandas/issues/31464
                try:
                    return pd.read_json(
                        json.dumps(v), typ="series", convert_dates=False
                    )
                except Exception as read_json_with_type_error_exception:  # noqa: BLE001
                    raise ValueError(
                        "Could not parse provided input as Pandas Series even with"
                        " convert_dates=False"
                    ) from read_json_with_type_error_exception

            except Exception as read_json_exception:  # noqa: BLE001
                raise ValueError(
                    "Could not parse provided input as Pandas Series"
                ) from read_json_exception


class PydanticPandasDataFrame:
    """Custom pydantic Data Type for parsing Pandas DataFrames

    Parses either a json string according to pandas.read_json
    with typ="frame" and default arguments otherwise or
    a Python dict-like data structure using the constructor
    of the pandas.DataFrame class with default arguments
    """

    @classmethod
    def __get_validators__(cls) -> Generator:
        yield cls.validate

    @classmethod
    def validate(cls, v: pd.DataFrame | str | dict | list) -> pd.DataFrame:
        if isinstance(v, pd.DataFrame):
            return v
        try:
            return pd.read_json(v, typ="frame")

        except Exception:  # noqa: BLE001
            try:
                return pd.read_json(json.dumps(v), typ="frame")
            except Exception as read_json_exception:  # noqa: BLE001
                raise ValueError(
                    "Could not parse provided input as Pandas DataFrame"
                ) from read_json_exception


class PydanticMultiTimeseriesPandasDataFrame:
    """Custom pydantic Data Type for parsing Multi Timeseries Pandas DataFrames

    Parses either a json string according to pandas.read_json
    with typ="frame" and default arguments otherwise or
    a Python dict-like data structure using the constructor
    of the pandas.DataFrame class with default arguments
    """

    @classmethod
    def __get_validators__(cls) -> Generator:
        yield cls.validate

    @classmethod
    def validate(cls, v: pd.DataFrame | str | dict | list) -> pd.DataFrame:
        df: pd.DataFrame | None = None
        if isinstance(v, pd.DataFrame):
            df = v
        else:
            try:
                df = pd.read_json(v, typ="frame")

            except Exception:  # noqa: BLE001
                try:
                    df = pd.read_json(json.dumps(v), typ="frame")
                except Exception as read_json_exception:  # noqa: BLE001
                    raise ValueError(
                        "Could not parse provided input as Pandas DataFrame."
                    ) from read_json_exception

        if len(df.columns) == 0:
            df = pd.DataFrame(columns=MULTITSFRAME_COLUMN_NAMES)

        if set(df.columns) != set(MULTITSFRAME_COLUMN_NAMES):
            column_names_string = ", ".join(df.columns)
            multitsframe_column_names_string = ", ".join(MULTITSFRAME_COLUMN_NAMES)
            raise ValueError(
                f"The column names {column_names_string} don't match the column names "
                f"required for a MultiTSFrame {multitsframe_column_names_string}."
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

        if not pd.api.types.is_datetime64tz_dtype(df["timestamp"]):
            raise ValueError(
                "Column 'timestamp' of MultiTSFrame does not have datetime64tz dtype. "
                f'Got {str(df["timestamp"].dtype)} index dtype instead.'
            )

        if not df["timestamp"].dt.tz in (pytz.UTC, datetime.timezone.utc):
            raise ValueError(
                "Column 'timestamp' of MultiTSFrame does not have UTC timezone. "
                f'Got {str(df["timestamp"].dt.tz)} timezone instead.'
            )

        return df


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


class AdvancedTypesOutputSerializationConfig(BaseConfig):
    """Enable Pydantic Models to serialize Pandas obejcts with this config class"""

    # Unfortunately there is no good way to get None for NaN or NaT:
    json_encoders = {
        pd.Series: lambda v: json.loads(
            v.to_json(date_format="iso")
        ),  # in order to serialize both NaN and NaT to null
        pd.DataFrame: lambda v: json.loads(
            v.to_json(date_format="iso")
        ),  # in order to serialize both NaN and NaT to null
        PydanticPandasSeries: lambda v: v.to_dict(),
        PydanticPandasDataFrame: lambda v: v.to_dict(),
        np.ndarray: lambda v: v.tolist(),
        datetime.datetime: lambda v: v.isoformat(),
        UUID: lambda v: str(v),  # alternatively: v.hex
        Figure: lambda v: json.loads(
            json.dumps(v.to_plotly_json(), cls=PlotlyJSONEncoder)
        ),
    }


class NamedDataTypedValue(TypedDict):
    name: str
    type: DataType  # noqa: A003
    value: Any


def parse_via_pydantic(
    entries: list[NamedDataTypedValue],
    type_map: dict[DataType, type] | None = None,
) -> BaseModel:
    """Parse data dynamically into a pydantic object

    Optionally a type_map can be specified which differs from the default data_type_map

    Returns an instantiated pydantic object if no parsing exception is thrown.

    May raise the typical exceptions of pydantic parsing.
    """
    type_dict: dict[str, tuple[type, "ellipsis"]] = {  # noqa: F821
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


def parse_dynamically_from_datatypes(entries: list[NamedDataTypedValue]) -> BaseModel:
    return parse_via_pydantic(entries, type_map=data_type_map)


def parse_dynamically_single_value(value: Any, data_type: DataType) -> BaseModel:
    return parse_via_pydantic([{"name": "value", "type": data_type, "value": value}])
