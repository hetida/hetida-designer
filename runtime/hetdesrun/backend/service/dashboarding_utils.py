from collections.abc import Iterable
from copy import deepcopy

import pandas as pd
from pandas.api.types import is_datetime64_any_dtype, is_string_dtype
from pydantic import ValidationError

from hetdesrun.adapters.generic_rest.external_types import ExternalType
from hetdesrun.models.adapter_data import RefIdType
from hetdesrun.models.wiring import (
    FilterKey,
    GridstackItemPositioning,
    GridstackPositioningType,
    InputWiring,
    OutputWiring,
    WorkflowWiring,
)


class DashboardQueryParamValidationError(Exception):
    pass


def ensure_input_wiring_in_dict(inp_name: str, inp_wirings_by_name: dict[str, InputWiring]) -> None:
    if not inp_name in inp_wirings_by_name:
        inp_wirings_by_name[inp_name] = InputWiring(workflow_input_name=inp_name)


def ensure_output_wiring_in_dict(
    outp_name: str, outp_wirings_by_name: dict[str, OutputWiring]
) -> None:
    if not outp_name in outp_wirings_by_name:
        outp_wirings_by_name[outp_name] = OutputWiring(workflow_output_name=outp_name)


FILTER_VALUE_ALIASES = {"v", "val", "value"}
ADAPTER_ID_URL_ALIASES = {"a", "adapter_id"}
REF_ID_ALIASES = {"ref_id", "ri", "rid"}
REF_ID_TYPE_ALIASES = {"rit", "ridt", "ref_id_type"}
REF_KEY_ALIASES = {"rk", "ref_key"}
TYPE_ALIASES = {"t", "type"}

__all_wiring_attribute_url_alias_sets__ = [
    ADAPTER_ID_URL_ALIASES,
    FILTER_VALUE_ALIASES,
    REF_ID_ALIASES,
    REF_ID_TYPE_ALIASES,
    REF_KEY_ALIASES,
    TYPE_ALIASES,
]


def dashboard_id_for_io(io_name: str, type: GridstackPositioningType) -> str:  # noqa: A002
    """Convert an input/output name to the dashboard internal id

    I.e. an input becomes "i.<INPUT_NAME"
    """
    if type is GridstackPositioningType.OUTPUT:
        return "o." + io_name
    if type is GridstackPositioningType.INPUT:
        return "i." + io_name

    raise ValueError("Unknown GridstackPositioningType")


def parse_dashboard_id(dashboard_id: str) -> tuple[str, GridstackPositioningType]:
    """Parse dashboard id for an input or output

    Returns a pair containing the actual input/output name and its type.
    """
    if dashboard_id.startswith("i."):
        input_name = dashboard_id.split(".", maxsplit=1)[1]
        return input_name, GridstackPositioningType.INPUT
    if dashboard_id.startswith("o."):
        output_name = dashboard_id.split(".", maxsplit=1)[1]
        return output_name, GridstackPositioningType.OUTPUT
    # default to output
    return dashboard_id, GridstackPositioningType.OUTPUT


def update_or_insert_input_wiring(  # noqa: PLR0912,PLR0915
    inp_name: str,
    changed_property: str,
    val: str,
    inp_wirings_by_name: dict[str, InputWiring],
    dashboard_positionings_by_dashboard_id: dict[str, GridstackItemPositioning],
) -> None:
    """Update the mutable input wiring dictionary

    If the referred input wiring does not exist in the dict, it will be created with
    default options and then updated.

    If it exists it will just be updated.

    Note that this mutates already validated objects and hence the mutated inp_wirings_by_name
    dict should be re-build and validated afterwards at some point.
    """

    if changed_property in FILTER_VALUE_ALIASES:
        ensure_input_wiring_in_dict(inp_name, inp_wirings_by_name)

        # reset everything else to make this a direct_provisioning wiring:
        inp_wirings_by_name[inp_name].adapter_id = "direct_provisioning"
        inp_wirings_by_name[inp_name].ref_id = None
        inp_wirings_by_name[inp_name].ref_id_type = None
        inp_wirings_by_name[inp_name].ref_key = None
        inp_wirings_by_name[inp_name].use_default_value = False

        inp_wirings_by_name[inp_name].filters = {FilterKey("value"): val}

    elif changed_property in ADAPTER_ID_URL_ALIASES:
        ensure_input_wiring_in_dict(inp_name, inp_wirings_by_name)

        inp_wirings_by_name[inp_name].adapter_id = val

    elif changed_property in REF_ID_ALIASES:
        ensure_input_wiring_in_dict(inp_name, inp_wirings_by_name)

        inp_wirings_by_name[inp_name].ref_id = val

    elif changed_property in REF_ID_TYPE_ALIASES:
        ensure_input_wiring_in_dict(inp_name, inp_wirings_by_name)

        try:
            inp_wirings_by_name[inp_name].ref_id_type = (
                RefIdType(val.upper()) if (val is not None and val != "null") else None
            )
        except ValueError as e:
            raise DashboardQueryParamValidationError(
                f"Unable to parse RefIdType from {val} for input {inp_name}"
            ) from e

    elif changed_property in REF_KEY_ALIASES:
        ensure_input_wiring_in_dict(inp_name, inp_wirings_by_name)

        inp_wirings_by_name[inp_name].ref_key = val

    elif changed_property in TYPE_ALIASES:
        ensure_input_wiring_in_dict(inp_name, inp_wirings_by_name)

        try:
            inp_wirings_by_name[inp_name].type = (
                ExternalType(val) if (val is not None and val != "null") else None
            )
        except ValueError as e:
            raise DashboardQueryParamValidationError(
                f"Unable to parse ExternalType from {val} for input {inp_name}"
            ) from e

    elif changed_property.startswith(("f.", "filters.")):
        _, filter_name = changed_property.split(".", maxsplit=1)

        if filter_name == "":
            raise DashboardQueryParamValidationError(
                f"Empty filter name not allowed from query param for input {inp_name}."
            )

        ensure_input_wiring_in_dict(inp_name, inp_wirings_by_name)

        inp_wirings_by_name[inp_name].filters[FilterKey(filter_name)] = val

    elif changed_property == "pos":
        splitted_val = val.split("_", maxsplit=3)
        if len(splitted_val) != 4:
            raise DashboardQueryParamValidationError(
                f"Invalid query param value {val} for dashboard positining for input {inp_name}."
                " Must be of form x_y_w_h."
            )
        try:
            x, y, w, h = splitted_val
            positioning = GridstackItemPositioning(
                x=x, y=y, w=w, h=h, id=inp_name, type=GridstackPositioningType.INPUT
            )
        except ValidationError as e:
            raise DashboardQueryParamValidationError(
                f"Invalid query param value {val} for dashboard positioning for input {inp_name}."
                " Must be of form x_y_w_h. Could not parse into correct integers."
            ) from e

        dashboard_positionings_by_dashboard_id[
            dashboard_id_for_io(inp_name, GridstackPositioningType.INPUT)
        ] = positioning

    elif changed_property == "allowed":
        allowed_values = val.split(",")
        positioning = dashboard_positionings_by_dashboard_id.get(
            dashboard_id_for_io(inp_name, GridstackPositioningType.INPUT),
            GridstackItemPositioning(
                x=0, y=0, w=3, h=1, id=inp_name, type=GridstackPositioningType.INPUT
            ),
        )
        positioning.allowed_input_values = allowed_values
        dashboard_positionings_by_dashboard_id[
            dashboard_id_for_io(inp_name, GridstackPositioningType.INPUT)
        ] = positioning

    else:
        raise DashboardQueryParamValidationError(
            f"Could not understand property {changed_property} specified via query parameter"
            f" for input wiring for input {inp_name}."
        )


def update_or_insert_output_wiring(  # noqa: PLR0912
    outp_name: str,
    changed_property: str,
    val: str,
    outp_wirings_by_name: dict[str, OutputWiring],
    dashboard_positionings_by_dashboard_id: dict[str, GridstackItemPositioning],
) -> None:
    """Update the mutable output wiring dictionary

    If the referred output wiring does not exist in the dict, it will be created with
    default options and then updated.

    If it exists it will just be updated.

    Note that this mutates already validated objects and hence the mutated outp_wirings_by_name
    dict should be re-build and validated afterwards at some point.
    """

    if changed_property in ADAPTER_ID_URL_ALIASES:
        ensure_output_wiring_in_dict(outp_name, outp_wirings_by_name)

        if val == "direct_provisioning":
            # reset everything to make this a direct_provisioning wiring.
            outp_wirings_by_name[outp_name].adapter_id = "direct_provisioning"
            outp_wirings_by_name[outp_name].ref_id = None
            outp_wirings_by_name[outp_name].ref_id_type = None
            outp_wirings_by_name[outp_name].ref_key = None

            outp_wirings_by_name[outp_name].filters = {}
        else:
            # just edit the adapter_id
            outp_wirings_by_name[outp_name].adapter_id = val

    elif changed_property in REF_ID_ALIASES:
        ensure_output_wiring_in_dict(outp_name, outp_wirings_by_name)

        outp_wirings_by_name[outp_name].ref_id = val

    elif changed_property in REF_ID_TYPE_ALIASES:
        ensure_output_wiring_in_dict(outp_name, outp_wirings_by_name)

        try:
            outp_wirings_by_name[outp_name].ref_id_type = (
                RefIdType(val.upper()) if (val is not None and val != "null") else None
            )
        except ValueError as e:
            raise DashboardQueryParamValidationError(
                f"Unable to parse RefIdType from {val} for output {outp_name}"
            ) from e

    elif changed_property in REF_KEY_ALIASES:
        ensure_output_wiring_in_dict(outp_name, outp_wirings_by_name)

        outp_wirings_by_name[outp_name].ref_key = val

    elif changed_property in TYPE_ALIASES:
        ensure_output_wiring_in_dict(outp_name, outp_wirings_by_name)

        try:
            outp_wirings_by_name[outp_name].type = (
                ExternalType(val) if (val is not None and val != "null") else None
            )
        except ValueError as e:
            raise DashboardQueryParamValidationError(
                f"Unable to parse ExternalType from {val} for output {outp_name}"
            ) from e

    elif changed_property.startswith(("f.", "filters.")):
        _, filter_name = changed_property.split(".", maxsplit=1)

        if filter_name == "":
            raise DashboardQueryParamValidationError(
                f"Empty filter name not allowed from query param for output {outp_name}."
            )

        ensure_output_wiring_in_dict(outp_name, outp_wirings_by_name)

        outp_wirings_by_name[outp_name].filters[FilterKey(filter_name)] = val

    elif changed_property == "pos":
        splitted_val = val.split("_", maxsplit=3)
        if len(splitted_val) != 4:
            raise DashboardQueryParamValidationError(
                f"Invalid query param value {val} for dashboard positining for output {outp_name}."
                " Must be of form x_y_w_h."
            )
        try:
            x, y, w, h = splitted_val
            positioning = GridstackItemPositioning(x=x, y=y, w=w, h=h, id=outp_name)
        except ValidationError as e:
            raise DashboardQueryParamValidationError(
                f"Invalid query param value {val} for dashboard positioning for output {outp_name}."
                " Must be of form x_y_w_h. Could not parse into correct integers."
            ) from e

        dashboard_positionings_by_dashboard_id[
            dashboard_id_for_io(outp_name, GridstackPositioningType.OUTPUT)
        ] = positioning

    else:
        raise DashboardQueryParamValidationError(
            f"Could not understand property {changed_property} specified via query parameter"
            f" for input wiring for input {outp_name}."
        )


def update_wiring_from_query_parameters(
    wiring: WorkflowWiring | None, query_param_pairs: Iterable[tuple[str, str]]
) -> WorkflowWiring:
    """Creates new wiring from the given wiring according to query params

    If no wiring is provided it will create a new wiring with default options
    and update that.
    """
    if wiring is None:
        wiring = WorkflowWiring()

    inp_wirings_by_name = {
        inp_wiring.workflow_input_name: inp_wiring.copy(deep=True)
        for inp_wiring in wiring.input_wirings
    }

    outp_wirings_by_name = {
        outp_wiring.workflow_output_name: outp_wiring.copy(deep=True)
        for outp_wiring in wiring.output_wirings
    }

    dashboard_positionings_by_dashboard_id = {
        dashboard_id_for_io(dp.id, dp.type): deepcopy(dp) for dp in wiring.dashboard_positionings
    }

    for key, val in query_param_pairs:
        splitted_key = key.split(".", maxsplit=2)
        if len(splitted_key) == 3:
            key_type, name, changed_property = splitted_key

            if key_type in {"input", "in", "inp", "i"}:
                try:
                    update_or_insert_input_wiring(
                        name,
                        changed_property,
                        val,
                        inp_wirings_by_name,
                        dashboard_positionings_by_dashboard_id,
                    )
                except DashboardQueryParamValidationError as e:
                    raise e
            if key_type in {"output", "out", "outp", "o"}:
                try:
                    update_or_insert_output_wiring(
                        name,
                        changed_property,
                        val,
                        outp_wirings_by_name,
                        dashboard_positionings_by_dashboard_id,
                    )
                except DashboardQueryParamValidationError as e:
                    raise e

    new_wiring = WorkflowWiring(
        # unpack to dict in order to trigger validation at all levels
        input_wirings=[inp_wiring.dict() for inp_wiring in inp_wirings_by_name.values()],
        output_wirings=[outp_wiring.dict() for outp_wiring in outp_wirings_by_name.values()],
        dashboard_positionings=[
            dp.dict() for dp in dashboard_positionings_by_dashboard_id.values()
        ],
    )

    return new_wiring


def infer_col_width_factor_from_dtype(series: pd.Series) -> int:
    """Try to guess a good column width factor for a table visualization based on dtype.

    Returns an abstract integer, which should represent the ratio according to
    the sum of all such integers for all columns of the table.

    """
    dtype_col_width_factor = 1
    if series.dtype == float:  # noqa: SIM114
        dtype_col_width_factor = 1
    elif series.dtype == int:  # noqa: SIM114
        dtype_col_width_factor = 1
    elif series.dtype == bool:  # noqa: SIM114
        dtype_col_width_factor = 1
    elif is_string_dtype(series):
        series.str.len()
        dtype_col_width_factor = 1 + int(min([max(series.str.len()), 240]) / 12)
        # 1 + 1 for every complete 12 characters — up to a total maximum of 21

    elif is_datetime64_any_dtype(series):
        dtype_col_width_factor = 3  # microsends isoformat
    elif series.dtype == object:
        dtype_col_width_factor = 3
    else:
        dtype_col_width_factor = 3
    return dtype_col_width_factor
