from typing import Any

from hdutils import DataType
from hetdesrun.adapters.exceptions import AdapterHandlingException


def data_info_by_data_type(
    data_obj: Any, data_type: DataType, optional: bool = False
) -> dict[str, Any]:
    if optional and data_obj is None:
        return {"is_None": True}

    match data_type:
        case DataType.Series:
            info_dict = {"len": len(data_obj), "dtype": str(data_obj.dtype)}

        case DataType.MultiTSFrame:
            info_dict = {
                "len": len(data_obj),
                "columns": list(data_obj.columns),
                "dtypes": [str(x) for x in data_obj.dtypes.to_list()],
            }
        case DataType.DataFrame:
            info_dict = {
                "len": len(data_obj),
                "columns": list(data_obj.columns),
                "dtypes": [str(x) for x in data_obj.dtypes.to_list()],
            }
        case DataType.String:
            info_dict = {
                "len": len(data_obj),
                "value": data_obj if len(data_obj) < 200 else data_obj[:200] + "...",
            }
        case DataType.Float | DataType.Integer | DataType.Boolean:
            info_dict = {"value": data_obj}

        case DataType.Any:
            info_dict = {"type": str(type(data_obj))}

        case DataType.PlotlyJson:
            info_dict = {"len_data": len(data_obj.get("data", []))}

        case _:
            info_dict = {}

    if optional:
        info_dict["is_None"] = False
    return info_dict


def get_data_info(
    data_by_name: dict[str, Any],
    data_types_by_name: dict[str | None, DataType],
    optional: bool = False,
) -> dict[str, dict[str, Any]]:
    """Get data info for loaded or output data"""

    info_by_name = {}
    for name, data_obj in data_by_name.items():
        if name is not None:
            assert name is not None  # noqa: S101, for mypy
            data_type = data_types_by_name.get(name)

            if data_type is None:
                raise AdapterHandlingException(f"Received data for unspecified input {name}")

            info_by_name[name] = data_info_by_data_type(data_obj, data_type, optional=optional)

    return info_by_name
