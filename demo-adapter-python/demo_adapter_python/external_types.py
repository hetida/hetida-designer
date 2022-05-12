from typing import Optional, Type, Any
from enum import Enum

from pydantic import create_model  # pylint: disable=no-name-in-module


class ValueDataType(str, Enum):
    """Represents an external value datatype"""

    INT = "int", int, int, "integer"
    FLOAT = ("float", float, float)
    STRING = "string", str, str, "str"
    BOOLEAN = "boolean", bool, bool, "bool"
    ANY = "any", Any, object, "object"

    def __new__(cls, *values: Any) -> "ValueDataType":
        obj = str.__new__(cls, values[0])  # type: ignore

        # first value is canonical value (e.g. what you get when calling ValueDataType.INT.value)
        obj._value_ = values[0]

        cls.parse_type: Type  # for mypy
        obj.parse_type = values[1]  # set parse_type to second tuple entry

        cls.pandas_value_type: Type  # for mypy
        obj.pandas_value_type = values[2]

        for other_value in values[3:]:
            # register other values in order to allow initializations ValueDataType("integer")
            # and ValueDataType("str") to work. This uses an internal attribute of Enum!
            # pylint: disable=no-member
            cls._value2member_map_[other_value] = obj  # type: ignore

        obj._all_values = (values[0],) + values[2:]  # type: ignore # pylint: disable=no-member
        return obj  # type:ignore

    def __repr__(self) -> str:
        return "<%s.%s: %s>" % (  # pylint: disable=consider-using-f-string
            self.__class__.__name__,
            # pylint: disable=no-member
            self._name_,
            ", ".join([repr(v) for v in self._all_values]),  # type: ignore
        )

    def parse_object(self, obj: Any) -> Any:
        """Parse a Python object using pydantic dynamic parsing

        For example ValueDataType.BOOLEAN.parse_object("yes") will return True.

        Raises pydantic.ValidationError if parsing fails.
        """
        DynamicallyParsedValue = create_model(
            "DynamicallyParsedValue",
            value=(
                self.parse_type,
                ...,
            ),
        )

        parsed_value = DynamicallyParsedValue(value=obj)
        return parsed_value.value  # type: ignore


class GeneralType(Enum):
    """General aspect / container type of a supported external type"""

    METADATA = "metadata"
    TIMESERIES = "timeseries"
    SERIES = "series"
    DATAFRAME = "dataframe"


class ExternalType(str, Enum):
    METADATA_INT = "metadata(int)", "metadata(integer)"
    METADATA_FLOAT = "metadata(float)"
    METADATA_STR = "metadata(string)", "metadata(str)"
    METADATA_BOOLEAN = "metadata(boolean)", "metadata(bool)"
    METADATA_ANY = "metadata(any)"

    TIMESERIES_INT = "timeseries(int)", "timeseries(integer)"
    TIMESERIES_FLOAT = "timeseries(float)"
    TIMESERIES_STR = "timeseries(string)", "timeseries(str)"
    TIMESERIES_BOOLEAN = "timeseries(boolean)", "timeseries(bool)"
    TIMESERIES_ANY = "timeseries(any)", "timeseries(object)"

    SERIES_INT = "series(int)", "series(integer)"
    SERIES_FLOAT = "series(float)"
    SERIES_STR = "series(string)", "series(str)"
    SERIES_BOOLEAN = "series(boolean)", "series(bool)"
    SERIES_ANY = "series(any)", "series(object)"

    DATAFRAME = "dataframe"

    def __new__(cls, *values: Any) -> "ExternalType":
        obj = str.__new__(cls, values[0])  # type: ignore

        # first value is canonical value
        obj._value_ = values[0]

        cls.general_type: GeneralType  # for mypy
        cls.value_datatype: Optional[ValueDataType]  # for mypy

        cls.store_value_datatypes(obj)
        cls.store_general_type(obj)

        for other_value in values[1:]:
            # pylint: disable=no-member
            cls._value2member_map_[other_value] = obj  # type: ignore
        obj._all_values = values  # type: ignore
        return obj  # type: ignore

    def __repr__(self) -> str:
        # pylint: disable=no-member
        return "<%s.%s: %s>" % (  # pylint: disable=consider-using-f-string
            self.__class__.__name__,
            self._name_,  # pylint: disable=no-member
            ", ".join([repr(v) for v in self._all_values]),  # type: ignore
        )

    @classmethod
    def store_value_datatypes(cls, member: "ExternalType") -> None:
        """Use the first value string to obtain the ValueDataType of values

        Stores this ValueDataType on the member attribute "value_datatype".
        Will be set to None if value_datatype can be determined.
        """

        # pylint: disable=protected-access
        if member._value_.endswith("(string)"):
            member.value_datatype = ValueDataType.STRING
        elif member._value_.endswith("(float)"):
            member.value_datatype = ValueDataType.FLOAT
        elif member._value_.endswith("(int)"):
            member.value_datatype = ValueDataType.INT
        elif member._value_.endswith("(boolean)"):
            member.value_datatype = ValueDataType.BOOLEAN
        elif member._value_.endswith("(any)"):
            member.value_datatype = ValueDataType.ANY
        else:
            member.value_datatype = None

    @classmethod
    def store_general_type(cls, member: "ExternalType") -> None:
        general_type_str = member.value.split("(", 1)[0]
        member.general_type = GeneralType(general_type_str)
