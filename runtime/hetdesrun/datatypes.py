from enum import Enum

import json
import datetime
from uuid import UUID

from typing import (
    Any,
    TypedDict,
    Type,
    List,
    Dict,
    Tuple,
    Generator,
    Union,
    Optional,
)

from pydantic import (  # pylint: disable=no-name-in-module
    create_model,
    BaseConfig,
    BaseModel,
)
import pandas as pd
import numpy as np

from plotly.graph_objects import Figure
from plotly.utils import PlotlyJSONEncoder


class DataType(str, Enum):
    """hetida designer data types

    These are the types available for component/workflow inputs/outputs.
    """

    Integer = "INT"
    Float = "FLOAT"
    String = "STRING"
    DataFrame = "DATAFRAME"
    Series = "SERIES"
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
    def validate(cls, v: Union[pd.Series, str, dict, list]) -> pd.Series:
        if isinstance(v, pd.Series):
            return v
        try:
            return pd.read_json(v, typ="series")

        except TypeError:  # https://github.com/pandas-dev/pandas/issues/31464
            try:
                return pd.read_json(v, typ="series", convert_dates=False)

            except Exception as e:  # pylint: disable=broad-except
                raise ValueError(
                    "Could not parse provided input as Pandas Series even with convert_dates=False"
                ) from e

        except Exception as e:  # pylint: disable=broad-except
            try:
                return pd.read_json(json.dumps(v), typ="series")

            except TypeError:  # https://github.com/pandas-dev/pandas/issues/31464
                try:
                    return pd.read_json(
                        json.dumps(v), typ="series", convert_dates=False
                    )
                except Exception as e:
                    raise ValueError(
                        "Could not parse provided input as Pandas Series even with"
                        " convert_dates=False"
                    ) from e

            except Exception as e:  # pylint: disable=broad-except
                raise ValueError(
                    "Could not parse provided input as Pandas Series"
                ) from e


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
    def validate(cls, v: Union[pd.DataFrame, str, dict, list]) -> pd.DataFrame:
        if isinstance(v, pd.DataFrame):
            return v
        try:
            return pd.read_json(v, typ="frame")
        # pylint: disable=broad-except
        except Exception as e:
            try:
                return pd.read_json(json.dumps(v), typ="frame")
            except Exception as e:
                raise ValueError(
                    "Could not parse provided input as Pandas DataFrame"
                ) from e


data_type_map: Dict[DataType, Type] = {
    DataType.Integer: int,
    DataType.Float: float,
    DataType.String: str,
    DataType.Series: PydanticPandasSeries,
    DataType.DataFrame: PydanticPandasDataFrame,
    DataType.Boolean: bool,
    # Any as Type is the correct way to tell pydantic how to parse an arbitrary object:
    DataType.Any: Any,  # type: ignore
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
        UUID: lambda v: v.hex,
        Figure: lambda v: json.loads(
            json.dumps(v.to_plotly_json(), cls=PlotlyJSONEncoder)
        ),
    }


class NamedDataTypedValue(TypedDict):
    name: str
    type: DataType
    value: Any


def parse_via_pydantic(
    entries: List[NamedDataTypedValue], type_map: Optional[Dict[DataType, Type]] = None,
) -> BaseModel:
    """Parse data dynamically into a pydantic object

    Optionally a type_map can be specified which differs from the default data_type_map

    Returns an instantiated pydantic object if no parsing exception is thrown.

    May raise the typical exceptions of pydantic parsing.
    """
    type_dict: Dict[str, Tuple[Type, "ellipsis"]] = {
        entry["name"]: (
            type_map[entry["type"]]
            if type_map is not None
            else data_type_map[entry["type"]],  # default to data_type_map
            ...,
        )
        for entry in entries
    }

    DynamicModel = create_model("DynamicyModel", **type_dict)  # type: ignore

    return DynamicModel(**{entry["name"]: entry["value"] for entry in entries})


def parse_dynamically_from_datatypes(entries: List[NamedDataTypedValue]) -> BaseModel:
    return parse_via_pydantic(entries, type_map=data_type_map)
