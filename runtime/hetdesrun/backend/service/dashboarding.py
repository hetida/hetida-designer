"""Dashboarding

Generate HTML / Styles / Javascript for the experimental dashboarding feature.
"""

import datetime
import json
import os
from enum import Enum
from typing import Any

import pandas as pd
from htpy import (
    Element,
    a,
    b,
    body,
    br,
    button,
    details,
    div,
    h4,
    head,
    html,
    i,
    input,
    label,
    link,
    option,
    p,
    pre,
    script,
    select,
    span,
    style,
    summary,
    textarea,
)
from markupsafe import Markup

from hetdesrun.backend.models.info import ExecutionResponseFrontendDto
from hetdesrun.backend.service.dashboarding_utils import (
    dashboard_id_for_io,
    infer_col_width_factor_from_dtype,
    parse_dashboard_id,
)
from hetdesrun.models.wiring import (
    FilterKey,
    GridstackItemPositioning,
    GridstackPositioningType,
    InputWiring,
    WorkflowWiring,
)
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.webservice.config import get_config


class OverrideMode(str, Enum):
    """Dashboard time range override mode

    Determines how time range filters in the wiring are overriden by dashboard
    settings.
    """

    Absolute = "ABSOLUTE"
    NoOverride = "NO_OVERRIDE"
    RelativeNow = "RELATIVE_NOW"


RELATIVE_RANGE_DESCRIPTIONS = [
    "5s",
    "1min",
    "5min",
    "15min",
    "1h",
    "2h",
    "3h",
    "6h",
    "12h",
    "24h",
    "7d",
    "30d",
    "365d",
]

# in seconds:
AUTORELOAD_INTERVALS = [5, 15, 30, 60, 120, 300, 900, 3600]


def item_positioning_dict(
    gridstack_item_positions: list[GridstackItemPositioning],
) -> dict[str, GridstackItemPositioning]:
    return {
        dashboard_id_for_io(item_positioning.id, item_positioning.type): item_positioning
        for item_positioning in gridstack_item_positions
    }


def gs_div_attributes_from_item_positioning(
    item_positioning: GridstackItemPositioning,
) -> str:
    return f"""

    {' gs-x="' + str(item_positioning.x)+'"' if item_positioning.x is not None else ' '}
    {' gs-y="' + str(item_positioning.y)+'"' if item_positioning.y is not None else ' '}
    {' gs-w="' + str(item_positioning.w)+'"' if item_positioning.w is not None else ' '}
    {' gs-h="' + str(item_positioning.h)+'"' if item_positioning.h is not None else ' '}

    """


def gs_div_attributes_from_item_positioning_as_dict(
    item_positioning: GridstackItemPositioning,
) -> dict[str, str]:
    div_attributes = {}
    if item_positioning.x is not None:
        div_attributes["gs-x"] = str(item_positioning.x)
    if item_positioning.y is not None:
        div_attributes["gs-y"] = str(item_positioning.y)
    if item_positioning.w is not None:
        div_attributes["gs-w"] = str(item_positioning.w)
    if item_positioning.h is not None:
        div_attributes["gs-h"] = str(item_positioning.h)

    return div_attributes


def prepare_header_string(header: str) -> str:
    return header.replace("_", " ").title()


def show_header(name: str, header: str | None = None) -> tuple[bool, str]:
    """Detects whether header should be shown without hovering by searching for _ suffix

    Returns a tuple with first entry indicating whether header should be shown
    and second entry with the header to use, which is the header with the suffix _ removed
    if it should not be shown without hovering.
    """
    if name.endswith("_") and len(name) > 1:
        return True, prepare_header_string(name[:-1] if header is None else header)

    return False, prepare_header_string(name if header is None else header)


def plotlyjson_to_html_div(
    db_id: str,
    plotly_json: Any,
    item_positioning: GridstackItemPositioning,
    header: str | None = None,
) -> Element:
    plotly_json = ensure_working_plotly_json(plotly_json)

    name = parse_dashboard_id(db_id)[0]
    show_header_if_not_hovering, header_to_use = show_header(name, header)

    return div(
        {
            "class": "grid-stack-item",
            "db_id": db_id,
            "input_type": "PLOTLYJSON",
            "id": f"gs-item-{db_id}",
            "gs-id": db_id,
            "style": "",
        }
        | gs_div_attributes_from_item_positioning_as_dict(item_positioning)  # type: ignore
    )[
        div(class_="grid-stack-item-content", id=f"container-{db_id}", style="")[
            div(
                class_=f"""panel-heading{"-hover-only" if show_header_if_not_hovering else ""}""",
                id=f"heading-{db_id}",
            )[div(class_="header-text", title=header_to_use)[header_to_use]],
            div(id=f"plot-container-{db_id}", style="margin:0;padding:0;width:100%")[
                div(id=db_id, style="width:100%;height:100%;margin:0;padding:0")
            ],
        ]
    ]


def html_str_to_gridstack_div(
    db_id: str,
    content: str,
    item_positioning: GridstackItemPositioning,
    header: str | None = None,
) -> Element:
    name = parse_dashboard_id(db_id)[0]
    show_header_if_not_hovering, header_to_use = show_header(name, header)

    return div(
        {
            "class": "grid-stack-item",
            "db_id": db_id,
            "input_type": "STRING",
            "id": f"gs-item-{db_id}",
            "gs-id": db_id,
            "style": "",
        }
        | gs_div_attributes_from_item_positioning_as_dict(item_positioning)  # type: ignore
    )[
        div(
            class_="grid-stack-item-content",
            id=f"container-{db_id}",
            style="display: flex; flex-direction: column;",
        )[
            div(
                class_=f"""panel-heading{"-hover-only" if show_header_if_not_hovering else ""}""",
                id=f"heading-{db_id}",
            )[
                div(class_="header-text", title=header_to_use)[header_to_use],
                div(
                    class_="panel-buttons",
                    style="",
                )["Some content"],
            ],
            div(
                id=f"html-container-{db_id}",
                style="margin:0;padding:0;flex-grow: 1;overflow-y: auto;",
            )[
                div(
                    id=db_id,
                    style="width:100%;height:100%;margin:0;padding:0;display:flex;flex-direction:column",
                )[Markup(content)]
            ],
        ]
    ]


def dataframe_to_table_gridstack_div(
    db_id: str,
    dataframe: pd.DataFrame,
    item_positioning: GridstackItemPositioning,
    header: str | None = None,
) -> Element:
    name = parse_dashboard_id(db_id)[0]
    show_header_if_not_hovering, header_to_use = show_header(name, header)

    my_table_id = "dftable-" + db_id

    data_row_list = json.loads(dataframe.to_json(orient="records", date_format="iso"))

    column_descriptions = [
        {
            "title": col_name,
            "field": col_name,
            "headerFilter": True,
            "headerSortTristate": True,
            "headerTooltip": True,
            "widthGrow": infer_col_width_factor_from_dtype(dataframe[col_name]),
            "tooltip": True,
        }
        for col_name in dataframe.columns
    ]

    data_table_html_elements = [
        div(
            id=f"datatable-{my_table_id}",
            style="width:100%;max-width:100%;height:100%;max-height:100%;overflow-y:none",
        ),
        script[
            Markup(
                f"""

        create_and_register_tabulator_datatable(
            "{db_id}",
            {json.dumps(data_row_list)},
            {json.dumps(column_descriptions)},
        );

        """
            )
        ],
    ]

    return div(
        {
            "class": "grid-stack-item",
            "db_id": db_id,
            "input_type": "DATAFRAME",
            "id": f"gs-item-{db_id}",
            "gs-id": db_id,
            "style": "",
        }
        | gs_div_attributes_from_item_positioning_as_dict(item_positioning)  # type: ignore
    )[
        div(
            class_="grid-stack-item-content",
            id=f"container-{db_id}",
            style="display: flex; flex-direction: column;",
        )[
            div(
                class_=f"""panel-heading{"-hover-only" if show_header_if_not_hovering else ""}""",
                id=f"heading-{db_id}",
            )[
                div(class_="header-text", title=header_to_use)[header_to_use],
                div(
                    class_="panel-buttons",
                    style="",
                )[
                    button(
                        onclick=(
                            r"""handle_toggle_button(event, {
                        activeIcon: 'fa-filter',
                        inactiveIcon: 'fa-filter-circle-xmark',
                        onToggle: (isActive) => {
                            toggle_column_filters("""
                            '"' + db_id + '"'
                            r""", isActive)
                        }
                    })"""
                        ),
                        style="height:100%;width:fit-content;padding:1px;padding-top:2px",
                        title="Toggle Show Column Filters",
                    )[i(class_="fa-solid fa-filter-circle-xmark fa-1x", style="")],
                ],
            ],
            div(
                id=f"html-container-{db_id}",
                style="margin:0;padding:0;flex-grow: 1;overflow-y: auto;",
            )[
                div(
                    id=db_id,
                    style="width:100%;height:100%;margin:0;padding:0;display:flex;flex-direction:column",
                )[*data_table_html_elements]
            ],
        ]
    ]


def input_value_gridstack_div(
    db_id: str,
    item_positioning: GridstackItemPositioning,
    inp_wirings_by_inp_name: dict[str, InputWiring],
    header: str | None = None,
    input_type: str = "STRING",
) -> Element:
    name = parse_dashboard_id(db_id)[0]
    show_header_if_not_hovering, header_to_use = show_header(name, header)

    in_wiring = name in inp_wirings_by_inp_name

    if in_wiring:
        val_from_wiring = inp_wirings_by_inp_name[name].filters.get(FilterKey("value"), "")

        val_from_wiring_allowed = (len(item_positioning.allowed_input_values) == 0) or (
            val_from_wiring in item_positioning.allowed_input_values
        )

        if val_from_wiring_allowed:
            selected_value_for_input = val_from_wiring
        else:
            selected_value_for_input = item_positioning.allowed_input_values[0]

    elif len(item_positioning.allowed_input_values) > 0:
        selected_value_for_input = item_positioning.allowed_input_values[0]
    else:
        selected_value_for_input = ""

    return div(
        {
            "class": "grid-stack-item",
            "db_id": db_id,
            "input_type": input_type,
            "id": f"gs-item-{db_id}",
            "gs-id": db_id,
            "style": "",
        }
        | gs_div_attributes_from_item_positioning_as_dict(item_positioning)  # type: ignore
    )[
        div(
            class_="grid-stack-item-content",
            id=f"container-{db_id}",
            style="display:flex;flex-direction:column;overflow:hidden;",
        )[
            div(
                class_=f"""panel-heading{"-hover-only" if show_header_if_not_hovering else ""}""",
                id=f"heading-{db_id}",
            )[div(class_="header-text", title=header_to_use)[header_to_use]],
            div(
                id=f"input-value-container-{db_id}",
                style="margin:0;padding:0;width:100%;height:100%;flex-grow:1;",
            )[
                div(id=db_id, style="width:100%;height:100%;margin:0;padding:2px 0px")[
                    (
                        textarea(
                            id="input-" + db_id,
                            rows=1,
                            name=name,
                            style="padding:6px;margin:0;width:100%;max-width:inherit;height:100%;resize:none;min-height:5px;border-bottom-left-radius:4px;border-bottom-right-radius:4px;border-top-left-radius:0px;border-top-right-radius:0px",
                            oninput="input_value_changed()",
                        )[selected_value_for_input]
                    )
                    if len(item_positioning.allowed_input_values) == 0
                    else (
                        select(
                            name=name,
                            id="input-" + db_id,
                            style="padding:6px;margin:0;width:100%;max-width:inherit;height:100%;resize:none;min-height:5px;border-bottom-left-radius:4px;border-bottom-right-radius:4px;border-top-left-radius:0px;border-top-right-radius:0px",
                            oninput="input_value_changed()",
                            value=selected_value_for_input,
                        )[
                            *(
                                option(
                                    value=allowed_input_value,
                                    selected=(selected_value_for_input == allowed_input_value),
                                )[allowed_input_value]
                                for allowed_input_value in item_positioning.allowed_input_values
                            )
                        ]
                    )
                ]
            ],
        ]
    ]


def ensure_working_plotly_json(plotly_json: dict[str, Any]) -> dict[str, Any]:
    plotly_json["layout"]["width"] = "100%"
    plotly_json["layout"]["height"] = "100%"

    return plotly_json


def override_timestamps_in_wiring(
    mutable_wiring: WorkflowWiring, from_ts: datetime.datetime, to_ts: datetime.datetime
) -> WorkflowWiring:
    """Inplace-Override timestamps in giving wiring.

    from_ts and to_ts are expected to be explicitely UTC timezoned!
    """
    for inp_wiring in mutable_wiring.input_wirings:
        if inp_wiring.filters.get("timestampFrom", None) is not None:  # type: ignore
            # We excpect UTC!
            inp_wiring.filters["timestampFrom"] = (  # type: ignore
                from_ts.isoformat(timespec="milliseconds").split("+")[0] + "Z"
            )
        if inp_wiring.filters.get("timestampTo", None) is not None:  # type: ignore
            # We expect UTC!
            inp_wiring.filters["timestampTo"] = (  # type: ignore
                to_ts.isoformat(timespec="milliseconds").split("+")[0] + "Z"
            )
    return mutable_wiring


def calculate_timerange_timestamps(
    fromTimestamp: datetime.datetime | None,
    toTimestamp: datetime.datetime | None,
    relNow: str | None,
) -> tuple[datetime.datetime | None, datetime.datetime | None]:
    """Calculate timerange timestamps for dashboard timerange override

    Important: Assumes that
    * either relNow is not None and both timestamps are None
    * or that relNow is None and both timestamps are not None
    * or all parameters are None

    The resulting tuple is of form (from_timestamp, to_timestamp) and either both are
    set or both are None.
    """

    calculated_from_timestamp = None
    calculated_to_timestamp = None

    if fromTimestamp is not None:
        calculated_from_timestamp = fromTimestamp
        calculated_to_timestamp = toTimestamp

    if relNow is not None:
        requested_timedelta_to_now = pd.Timedelta(relNow).to_pytimedelta()

        calculated_to_timestamp = datetime.datetime.now(tz=datetime.timezone.utc)
        calculated_from_timestamp = calculated_to_timestamp - requested_timedelta_to_now

    return (calculated_from_timestamp, calculated_to_timestamp)


DASHBOARD_HEAD_ELEMENTS = (
    script(src="https://cdn.jsdelivr.net/npm/keycloak-js@25.0.5/dist/keycloak.min.js"),
    script(src="https://cdn.jsdelivr.net/npm/gridstack@10.3.1/dist/gridstack-all.js"),
    link(
        href="https://cdn.jsdelivr.net/npm/gridstack@10.3.1/dist/gridstack.min.css",
        rel="stylesheet",
    ),
    link(
        rel="icon",
        type="image/png",
        href="data:image/x-icon;base64,iVBORw0KGgoAAAANSUhEUgAAADQAAAAvCAYAAACsaemzAAAA0GVYSWZJSSoACAAAAAoAAAEEAAEAAAA0AAAAAQEEAAEAAAAvAAAAAgEDAAMAAACGAAAAEgEDAAEAAAABAAAAGgEFAAEAAACMAAAAGwEFAAEAAACUAAAAKAEDAAEAAAADAAAAMQECAA0AAACcAAAAMgECABQAAACqAAAAaYcEAAEAAAC+AAAAAAAAAAgACAAIAIQLAAAnAAAAhAsAACcAAABHSU1QIDIuMTAuMzgAADIwMjQ6MDk6MTAgMTE6Mzk6MDEAAQABoAMAAQAAAAEAAAAAAAAAxnqnGQAAAYRpQ0NQSUNDIHByb2ZpbGUAAHicfZE9SMNQFIVPU6VaKg52EHHIUOtiFxVxrFUoQoVQK7TqYPLSP2jSkKS4OAquBQd/FqsOLs66OrgKguAPiLODk6KLlHhfWmgR44PL+zjvncN99wFCo8I0qycOaLptppMJMZtbFQOv6EeQKopxmVnGnCSl4Lm+7uHj+12MZ3nf+3MNqHmLAT6ROM4M0ybeIJ7ZtA3O+8RhVpJV4nPiCZMaJH7kutLiN85FlwWeGTYz6XniMLFY7GKli1nJ1IiniSOqplO+kG2xynmLs1apsXaf/IWhvL6yzHWqUSSxiCVIEKGghjIqsBGjXSfFQprOEx7+EdcvkUshVxmMHAuoQoPs+sH/4PdsrcLUZCsplAB6XxznYwwI7ALNuuN8HztO8wTwPwNXesdfbQCzn6TXO1rkCBjcBi6uO5qyB1zuAMNPhmzKruSnEgoF4P2MvikHDN0CwbXW3NrnOH0AMjSr1A1wcAhEi5S97vHuvu65/XunPb8fo+Ryuqh7VA0AAA14aVRYdFhNTDpjb20uYWRvYmUueG1wAAAAAAA8P3hwYWNrZXQgYmVnaW49Iu+7vyIgaWQ9Ilc1TTBNcENlaGlIenJlU3pOVGN6a2M5ZCI/Pgo8eDp4bXBtZXRhIHhtbG5zOng9ImFkb2JlOm5zOm1ldGEvIiB4OnhtcHRrPSJYTVAgQ29yZSA0LjQuMC1FeGl2MiI+CiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPgogIDxyZGY6RGVzY3JpcHRpb24gcmRmOmFib3V0PSIiCiAgICB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIKICAgIHhtbG5zOnN0RXZ0PSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvc1R5cGUvUmVzb3VyY2VFdmVudCMiCiAgICB4bWxuczpkYz0iaHR0cDovL3B1cmwub3JnL2RjL2VsZW1lbnRzLzEuMS8iCiAgICB4bWxuczpHSU1QPSJodHRwOi8vd3d3LmdpbXAub3JnL3htcC8iCiAgICB4bWxuczp0aWZmPSJodHRwOi8vbnMuYWRvYmUuY29tL3RpZmYvMS4wLyIKICAgIHhtbG5zOnhtcD0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wLyIKICAgeG1wTU06RG9jdW1lbnRJRD0iZ2ltcDpkb2NpZDpnaW1wOjliMGJlNzM5LTM3ZmEtNDQ0MS1iOTkwLWIxNDU3ZjExZGQ4NSIKICAgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDplMmNlNGMxYi0xNzQxLTRhMzQtYTgxOS05ZjU0NGFjMDllMWIiCiAgIHhtcE1NOk9yaWdpbmFsRG9jdW1lbnRJRD0ieG1wLmRpZDpmZGJmODhlZS1iNGRhLTRjMDgtYmY5YS02NjBjYzJhNjNmOWMiCiAgIGRjOkZvcm1hdD0iaW1hZ2UvcG5nIgogICBHSU1QOkFQST0iMi4wIgogICBHSU1QOlBsYXRmb3JtPSJMaW51eCIKICAgR0lNUDpUaW1lU3RhbXA9IjE3MjU5NjExNDEzNjM5NjIiCiAgIEdJTVA6VmVyc2lvbj0iMi4xMC4zOCIKICAgdGlmZjpPcmllbnRhdGlvbj0iMSIKICAgeG1wOkNyZWF0b3JUb29sPSJHSU1QIDIuMTAiCiAgIHhtcDpNZXRhZGF0YURhdGU9IjIwMjQ6MDk6MTBUMTE6Mzk6MDErMDI6MDAiCiAgIHhtcDpNb2RpZnlEYXRlPSIyMDI0OjA5OjEwVDExOjM5OjAxKzAyOjAwIj4KICAgPHhtcE1NOkhpc3Rvcnk+CiAgICA8cmRmOlNlcT4KICAgICA8cmRmOmxpCiAgICAgIHN0RXZ0OmFjdGlvbj0ic2F2ZWQiCiAgICAgIHN0RXZ0OmNoYW5nZWQ9Ii8iCiAgICAgIHN0RXZ0Omluc3RhbmNlSUQ9InhtcC5paWQ6MGVlMmVlNzEtZDZkNC00YTE5LWEwNmQtZmFiNmRjNTg1MDUzIgogICAgICBzdEV2dDpzb2Z0d2FyZUFnZW50PSJHaW1wIDIuMTAgKExpbnV4KSIKICAgICAgc3RFdnQ6d2hlbj0iMjAyNC0wOS0xMFQxMTozOTowMSswMjowMCIvPgogICAgPC9yZGY6U2VxPgogICA8L3htcE1NOkhpc3Rvcnk+CiAgPC9yZGY6RGVzY3JpcHRpb24+CiA8L3JkZjpSREY+CjwveDp4bXBtZXRhPgogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgCjw/eHBhY2tldCBlbmQ9InciPz4CPC+HAAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAB2HAAAdhwGP5fFlAAAAB3RJTUUH6AkKCScB9n0IJgAAAiBJREFUaN7tmD1PFFEUhp+zriYaE7MEOqOJKw2FMxorE5VYWPMTsKKSxITEgv8ghITORH+AFtprYgfN7hCCQkQqPzBQUahIlkOxhL0rMzt3ZrIrruftZubeM/c9c77eAYPBYOhnSLdfoMtUaXCnwAnfS8Ci7/Jy113WoIoynnv/Pi/Bn1Cp30Ku7wiVe/7GkHsiNDrmXcRTlOETQUjrDCM8bN2g0pbjKWRicFcjrjpF4pUEvOndFxLOowSJhJVTmUgJgyiDjoMWLIcK4Qyb/Oa549EqcDt3yCkfKDllu8RyTwnJCN+AZ06C30dbhHSJGyiaQuKsQ2BFwpa9k1fl9pnJuD7TNGON9b8fThPT5BMX2OG149rHEnQuyRZyRsgIGaH8o49GXC/glp9yjdXYarbCAHtcPvZgh3N/NNArGrEbU4e3JOBzJkJaYwhltoDM3gAexD7b4ybKtIeVidiBqCnB5yyH+ls+CPPAx5S9YyijR/OxvwsfeUzbU8DFw/WaiZBGzAGn27YJ6xJQT5Hat5zLAY0Scqiph1qmA2oeMv6Hk0OjGjn/F1IleJxcFo8ZTxDHCRXff29eEty1bRJcWDoMuRHHC+lx277mF8JawroKcCmTBHdtK9uU+OJ8ve8dCUnIpNYYQnhRIOS+Sshk7NmaEnw6d8jBOwn9+1A5oVE+0XqqF/Mh4m3XbFtj/ZckeM+HU/8TZhpODQaDwWD4mzgAghWrNbD3EUoAAAAASUVORK5CYII=",
    ),
    link(
        href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.6.0/css/all.min.css",
        rel="stylesheet",
    ),
    script(src="https://cdn.plot.ly/plotly-2.35.2.min.js", charset="utf-8"),
    link(
        href="https://cdn.jsdelivr.net/npm/flatpickr@4.6.13/dist/flatpickr.min.css",
        rel="stylesheet",
    ),
    script(src="https://cdn.jsdelivr.net/npm/flatpickr@4.6.13"),
    link(href="https://unpkg.com/boltcss@0.7.0/bolt.min.css", rel="stylesheet"),
    link(
        href="https://unpkg.com/tabulator-tables@6.2.5/dist/css/tabulator.min.css", rel="stylesheet"
    ),
    script(src="https://unpkg.com/tabulator-tables@6.2.5/dist/js/tabulator.min.js"),
    head[
        style[
            Markup(r"""
.grid-stack {
    padding: 0;
    margin: 0;
}

.tabulator-header {
    height: fit-content;
}

.tabulator-header-filter {
    display: var(--table-filters-display);
}


.tabulator-tableholder {
    background-color: #dddddd;
}

.panel-tooltiptext {
    visibility: hidden;
    width: 200px;
    background-color: black;
    color: #fff;
    text-align: center;
    border-radius: 6px;
    padding: 5px 0;
    position: absolute;
    z-index: 1;
    left:50%;
}

.header-info-i {
    background: #f9f9f9;
    color:#888888;
    font-size:18px;
    width=10px;
    font-family:sans-serif;
}

.header-info-i:hover .panel-tooltiptext{
    visibility: visible;
}


.panel-heading {
    background: #f9f9f9;
    color:#888888;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    font-size:18px;
    font-family:sans-serif;
    text-align:center;
    user-select:none;
    height:20;
}

.panel-buttons {
    background-color:transparent;
    position:absolute;
    top: 0;
    opacity:0;
    z-index:2;
    height:20;
    text-align:center;
    align-items:normal;
    padding:2px;
    height:20px;
    font-size:12px;
}

.panel-heading:hover .panel-buttons {
    opacity: 1
}

.header-text {
    white-space: nowrap; /* Prevents text wrapping */
    overflow: hidden; /* Hides overflow text */
    text-overflow: ellipsis; /* Shows "..." for overflow */
}

.header-text:hover .panel-buttons {
    opacity: 1
}

.panel-heading-hover-only {
    background: #f9f9f9;
    color:#888888;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    font-size:18px;
    font-family:sans-serif;
    text-align:center;
    user-select:none;
    height:20;
    opacity:0;
}

.panel-heading-hover-only:hover {
    background: #f9f9f9;
    color:#888888;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    font-size:18px;
    font-family:sans-serif;
    text-align:center;
    user-select:none;
    height:20;
    opacity:1;
}

.panel-heading-hover-only .panel-buttons {
    opacity: 1
}

.hd_df_table_for_dashboarding {
    width: 100%
}

.hd-dashboard-timerange-picker {
    width: 100%;
    box-sizing: border-box;
    margin-left: 2px;
    margin-right: 2px;
    flex-grow: 1;
    max-width: inherit;
}


.gs-24 > .grid-stack-item {
width: 4.167%;
}
.gs-24 > .grid-stack-item[gs-x="1"] {
left: 4.167%;
}
.gs-24 > .grid-stack-item[gs-w="2"] {
width: 8.333%;
}
.gs-24 > .grid-stack-item[gs-x="2"] {
left: 8.333%;
}
.gs-24 > .grid-stack-item[gs-w="3"] {
width: 12.5%;
}
.gs-24 > .grid-stack-item[gs-x="3"] {
left: 12.5%;
}
.gs-24 > .grid-stack-item[gs-w="4"] {
width: 16.667%;
}
.gs-24 > .grid-stack-item[gs-x="4"] {
left: 16.667%;
}
.gs-24 > .grid-stack-item[gs-w="5"] {
width: 20.833%;
}
.gs-24 > .grid-stack-item[gs-x="5"] {
left: 20.833%;
}
.gs-24 > .grid-stack-item[gs-w="6"] {
width: 25%;
}
.gs-24 > .grid-stack-item[gs-x="6"] {
left: 25%;
}
.gs-24 > .grid-stack-item[gs-w="7"] {
width: 29.167%;
}
.gs-24 > .grid-stack-item[gs-x="7"] {
left: 29.167%;
}
.gs-24 > .grid-stack-item[gs-w="8"] {
width: 33.333%;
}
.gs-24 > .grid-stack-item[gs-x="8"] {
left: 33.333%;
}
.gs-24 > .grid-stack-item[gs-w="9"] {
width: 37.5%;
}
.gs-24 > .grid-stack-item[gs-x="9"] {
left: 37.5%;
}
.gs-24 > .grid-stack-item[gs-w="10"] {
width: 41.667%;
}
.gs-24 > .grid-stack-item[gs-x="10"] {
left: 41.667%;
}
.gs-24 > .grid-stack-item[gs-w="11"] {
width: 45.833%;
}
.gs-24 > .grid-stack-item[gs-x="11"] {
left: 45.833%;
}
.gs-24 > .grid-stack-item[gs-w="12"] {
width: 50%;
}
.gs-24 > .grid-stack-item[gs-x="12"] {
left: 50%;
}
.gs-24 > .grid-stack-item[gs-w="13"] {
width: 54.167%;
}
.gs-24 > .grid-stack-item[gs-x="13"] {
left: 54.167%;
}
.gs-24 > .grid-stack-item[gs-w="14"] {
width: 58.333%;
}
.gs-24 > .grid-stack-item[gs-x="14"] {
left: 58.333%;
}
.gs-24 > .grid-stack-item[gs-w="15"] {
width: 62.5%;
}
.gs-24 > .grid-stack-item[gs-x="15"] {
left: 62.5%;
}
.gs-24 > .grid-stack-item[gs-w="16"] {
width: 66.667%;
}
.gs-24 > .grid-stack-item[gs-x="16"] {
left: 66.667%;
}
.gs-24 > .grid-stack-item[gs-w="17"] {
width: 70.833%;
}
.gs-24 > .grid-stack-item[gs-x="17"] {
left: 70.833%;
}
.gs-24 > .grid-stack-item[gs-w="18"] {
width: 75%;
}
.gs-24 > .grid-stack-item[gs-x="18"] {
left: 75%;
}
.gs-24 > .grid-stack-item[gs-w="19"] {
width: 79.167%;
}
.gs-24 > .grid-stack-item[gs-x="19"] {
left: 79.167%;
}
.gs-24 > .grid-stack-item[gs-w="20"] {
width: 83.333%;
}
.gs-24 > .grid-stack-item[gs-x="20"] {
left: 83.333%;
}
.gs-24 > .grid-stack-item[gs-w="21"] {
width: 87.5%;
}
.gs-24 > .grid-stack-item[gs-x="21"] {
left: 87.5%;
}
.gs-24 > .grid-stack-item[gs-w="22"] {
width: 91.667%;
}
.gs-24 > .grid-stack-item[gs-x="22"] {
left: 91.667%;
}
.gs-24 > .grid-stack-item[gs-w="23"] {
width: 95.833%;
}
.gs-24 > .grid-stack-item[gs-x="23"] {
left: 95.833%;
}
.gs-24 > .grid-stack-item[gs-w="24"] {
width: 100%;
}
""")
        ]
    ],
)


def generate_dashboard_title_div(
    transformation_revision: TransformationRevision,
) -> Element:
    return div(
        style="""
        color:#666666;
        margin-left:1em;
        text-align:left;
        width:50%;
        align-items:center"""
    )[
        h4(
            style="color:#555555;padding-bottom:0px;margin-bottom:0px",
            title=transformation_revision.description,
        )[transformation_revision.name],
        span(
            title="id: "
            + str(transformation_revision.id)
            + os.linesep
            + "group id: "
            + str(transformation_revision.revision_group_id)
        )[b[transformation_revision.version_tag + " (" + transformation_revision.state + ")"]],
    ]


def generate_timerange_overriding_controls_div(
    override_mode: OverrideMode, relNow: str | None
) -> Element:
    return div(style="width:50%;display:flex;align-items:center")[
        div(style="max-width:30em;min-width:11em;margin-right:4px")[
            select(
                name="override",
                id="override-timerange-select",
                onchange="on_override_select_change(this)",
                title="Override input timeranges",
                style="width:100%;max-width:inherit",
            )[
                option(value="absolute", selected=override_mode is OverrideMode.Absolute)[
                    "Absolute"
                ],
                option(value="none", selected=override_mode is OverrideMode.NoOverride)[
                    "do not override"
                ],
                *(
                    option(
                        value=rel_range_desc,
                        selected=(
                            override_mode is OverrideMode.RelativeNow and relNow == rel_range_desc
                        ),
                    )[f"last {rel_range_desc}"]
                    for rel_range_desc in RELATIVE_RANGE_DESCRIPTIONS
                ),
            ]
        ],
        div(
            id="picker-span",
            style="display:flex;align-items:center;width:100%;min-width:10em;margin-right:4px",
        )[
            input(
                class_="hd-dashboard-timerange-picker",
                id="datetimepicker-absolute",
                type="text",
                placeholder="Select range...",
            ),
            i(
                class_="fa-solid fa-triangle-exclamation",
                id="datetime-picker-warning",
                title="Uncomplete daterange selected.",
                style="color:#880000;display:none;heigt:100%",
            ),
        ],
    ]


def generate_reload_and_config_buttons_div(autoreload: int | None) -> Element:
    return div(
        id="buttons-right",
        style="display:flex;align-items:center;width:fit-content;margin-left:4px",
    )[
        select(
            name="autoreload",
            id="autoreload-select",
            title="Autoreload",
            onchange="on_autoreload_select_change(this)",
            style="width:10em;max-width:10em;margin-right:2px",
        )[
            option(value="none", selected=autoreload is None)["no"],
            *(
                option(
                    value=str(autoreload_interval_length),
                    selected=(autoreload == autoreload_interval_length),
                )[str(autoreload_interval_length) + "s"]
                for autoreload_interval_length in AUTORELOAD_INTERVALS
            ),
        ],
        *[
            button(
                class_="btn",
                title="Reload",
                onclick="update_dashboard();",
                style="margin-left:2px",
            )[i(class_="fa-solid fa-arrow-rotate-right")],
            button(
                class_="btn",
                title="Lock/Unlock button",
                onclick="toggle_lock();",
                style="margin-left:8px;margin-right:4px",
            )[i(class_="fa-solid fa-unlock", id="lock-button-image")],
            button(
                class_="btn",
                title="View/Hide dashboard configuration",
                onclick="toggle_config_visibility();",
                style="margin-left:8px;margin-right:4px",
            )[i(class_="fa-solid fa-chevron-down", id="config-button-image")],
        ]
        + (
            [
                button(
                    class_="btn",
                    title="Logout",
                    id="logout_button",
                    onclick="logout_user();",
                    style="margin-left:8px;margin-right:4px",
                )[i(class_="fa-solid fa-right-from-bracket", id="logout_button_image")],
            ]
            if get_config().auth
            else []
        ),
    ]


def generate_config_panel_div(
    transformation_revision: TransformationRevision,
    actually_used_wiring: WorkflowWiring,
    use_release_wiring: bool,
    inputs_to_expose: set[str] | None = None,
) -> Element:
    if inputs_to_expose is None:
        inputs_to_expose = set()

    assert inputs_to_expose is not None  # for mypy # noqa: S101

    positionings_by_inp_name = {
        positioning.id: positioning
        for positioning in actually_used_wiring.dashboard_positionings
        if positioning.type is GridstackPositioningType.INPUT
    }

    return div(id="config-panel", style="display:none;align-items:center;width:100%;padding:15px")[
        div()[
            div[
                div[
                    label(for_="use_release_wiring")[
                        input(
                            type="checkbox",
                            id="use_release_wiring",
                            name="Use release wiring",
                            value="false",
                            checked=use_release_wiring,
                            onchange="set_unapplyied_changes()",
                        ),
                        "Use release wiring (instead of test wiring) as base.",
                    ]
                ],
                div[
                    *(
                        div(style="display:flex; align-items: center")[
                            label(
                                for_="expose_input-" + inp.name,
                                style="display: flex;align-items: center;",
                            )[
                                input(
                                    type="checkbox",
                                    id="expose_input-" + inp.name,
                                    name="Expose input: " + inp.name,
                                    value="false",
                                    checked=inp.name in inputs_to_expose,
                                    onchange="set_unapplyied_changes()",
                                ),
                                p(style="margin-right: 0.25em;")["Expose input: "],
                                b[inp.name],
                            ],
                            label(
                                for_="allowed_input-values-" + inp.name,
                                style="margin-left:5em;margin-right:0.25em;",
                                title=(
                                    "If not empty, this should be a comma-separated list"
                                    " of allowed values for that input."
                                ),
                            )["Allowed Input values: "],
                            input(
                                type="text",
                                id="allowed-input-values-" + inp.name,
                                name="Allowed input values (comma-separated): " + inp.name,
                                title=(
                                    "If not empty, this should be a comma-separated list"
                                    " of allowed values for that input."
                                ),
                                value=",".join(
                                    positionings_by_inp_name[inp.name].allowed_input_values
                                    if (inp.name in positionings_by_inp_name)
                                    else []
                                ),
                                oninput="set_unapplyied_changes()",
                            ),
                        ]
                        for inp in transformation_revision.io_interface.inputs
                        if inp.name is not None
                    )
                ],
            ],
            details(style="margin-bottom: 6px")[
                summary["Transformation Revision Details"],
                b["name"],
                ": " + transformation_revision.name,
                br,
                b["version tag"],
                ": " + transformation_revision.version_tag,
                br,
                b["state"],
                ":, " + transformation_revision.state,
                br,
                b["type"],
                ": " + transformation_revision.type,
                br,
                b["category"],
                ": " + transformation_revision.category,
                br,
                b["description"],
                ": " + transformation_revision.description,
                br,
                b["id"],
                ": ",
                a(href=f"../{str(transformation_revision.id)}")[str(transformation_revision.id)],
                br,
                b["revision group id"],
                ": " + str(transformation_revision.revision_group_id),
                br,
            ],
            details(style="margin-bottom: 6px")[
                summary["Documentation"],
                div[
                    pre(style="width:100%;max-width:inherit")[transformation_revision.documentation]
                ],
            ],
            details(style="margin-bottom: 6px")[
                summary[f"""Test Wiring{" (used as base)" if not use_release_wiring else ""}"""],
                div[
                    pre(style="width:100%;max-width:inherit")[
                        transformation_revision.test_wiring.json(indent=2)
                    ]
                ],
            ],
            details(style="margin-bottom: 6px")[
                summary[f"""Release Wiring{" (used as base)" if use_release_wiring else ""}"""],
                div[
                    pre(style="width:100%;max-width:inherit")[
                        transformation_revision.release_wiring.json(indent=2)
                        if transformation_revision.release_wiring is not None
                        else "null"
                    ]
                ],
            ],
            details(style="margin-bottom: 6px")[
                summary["Updated Wiring (actually used wiring)"],
                div[pre(style="width:100%;max-width:inherit")[actually_used_wiring.json(indent=2)]],
            ],
        ]
    ]


def generate_gridstack_div(
    positioning_dict: dict[str, GridstackItemPositioning],
    plotly_outputs: dict[str, Any],
    string_outputs: dict[str, str],
    dataframe_outputs: dict[str, pd.DataFrame],
    multitsframe_outputs: dict[str, pd.DataFrame],
    actually_used_wiring: WorkflowWiring,
    exposed_manual_inputs: set[str],
) -> Element:
    inp_wirings_by_input_name = {
        inp_wiring.workflow_input_name: inp_wiring
        for inp_wiring in actually_used_wiring.input_wirings
    }

    return div(class_="grid-stack")[
        *(
            plotlyjson_to_html_div(
                db_id,
                plotly_json,
                positioning_dict.get(
                    db_id,
                    GridstackItemPositioning(
                        id=parse_dashboard_id(db_id)[0],
                        x=(ind % 2) * 12,
                        y=(ind // 2) * 3,
                        w=12,
                        h=3,
                        type=GridstackPositioningType.OUTPUT,
                    ),
                ),
            )
            for ind, (db_id, plotly_json) in enumerate(plotly_outputs.items())
        ),
        *(
            html_str_to_gridstack_div(
                db_id,
                content,
                positioning_dict.get(
                    db_id,
                    GridstackItemPositioning(
                        id=parse_dashboard_id(db_id)[0],
                        x=(ind % 2) * 12,
                        y=(ind // 2) * 3 + len(plotly_outputs) % 2 * 3,
                        w=12,
                        h=3,
                        type=GridstackPositioningType.OUTPUT,
                    ),
                ),
            )
            for ind, (db_id, content) in enumerate(string_outputs.items())
        ),
        *(
            dataframe_to_table_gridstack_div(
                db_id,
                dataframe,
                positioning_dict.get(
                    db_id,
                    GridstackItemPositioning(
                        id=parse_dashboard_id(db_id)[0],
                        x=(ind % 2) * 12,
                        y=(ind // 2) * 3
                        + len(plotly_outputs) % 2 * 3
                        + len(string_outputs) % 2 * 3,
                        w=12,
                        h=3,
                        type=GridstackPositioningType.OUTPUT,
                    ),
                ),
            )
            for ind, (db_id, dataframe) in enumerate(dataframe_outputs.items())
        ),
        *(
            dataframe_to_table_gridstack_div(
                db_id,
                multitsframe.reindex(
                    columns=(
                        ["timestamp", "metric"]
                        + [
                            col
                            for col in multitsframe.columns
                            if col not in {"timestamp", "metric"}
                        ]
                    ),
                    copy=False,
                ),
                positioning_dict.get(
                    db_id,
                    GridstackItemPositioning(
                        id=parse_dashboard_id(db_id)[0],
                        x=(ind % 2) * 12,
                        y=(ind // 2) * 3
                        + len(plotly_outputs) % 2 * 3
                        + len(string_outputs) % 2 * 3
                        + len(dataframe_outputs) % 2 * 3,
                        w=12,
                        h=3,
                        type=GridstackPositioningType.OUTPUT,
                    ),
                ),
            )
            for ind, (db_id, multitsframe) in enumerate(multitsframe_outputs.items())
        ),
        *(
            input_value_gridstack_div(
                db_id,
                positioning_dict.get(
                    db_id,
                    GridstackItemPositioning(
                        id=parse_dashboard_id(db_id)[0],
                        x=(ind % 6) * 4,
                        y=(ind // 6)
                        + len(plotly_outputs) % 2 * 3
                        + len(string_outputs) % 2 * 3
                        + len(dataframe_outputs) % 2 * 3
                        + len(multitsframe_outputs) % 2 * 3,
                        w=4,
                        h=1,
                        type=GridstackPositioningType.INPUT,
                    ),
                ),
                inp_wirings_by_inp_name=inp_wirings_by_input_name,
            )
            for ind, db_id in enumerate(exposed_manual_inputs)
        ),
    ]


def generate_login_dashboard_stub() -> str:
    """Login Stub page

    Generates a page only containing what is necessary to trigger a login
    using the keycloak-js library.
    """

    dashboard_login_stub_html = html[
        script(src="https://cdn.jsdelivr.net/npm/keycloak-js@25.0.5/dist/keycloak.min.js"),
        script()[
            Markup(
                r"""       const Keycloak = window["Keycloak"];

        function getCookie(name) {
            const value = `; ${document.cookie}`;
            const parts = value.split(`; ${name}=`);
            if (parts.length === 2) return parts.pop().split(';').shift();
            return null;
        }

        function updateAuthCookies() {
            if (keycloak.token !=  null) {
                document.cookie = "access_token="+keycloak.token + ";SameSite=Strict";
            }

        }

        function getAuthCookies() {
            access_token = getCookie("access_token");
            refresh_token = getCookie("refresh_token");
            return [access_token, refresh_token]
        }

        async function init_keycloak() {
            let authenticated=false;
            try {
                authenticated = await keycloak.init(
                    {token: access_token, refreshToken: refresh_token,
                onLoad: 'login-required', checkLoginIframe:false,
                pkceMethod:"S256"
                 }
                );
                console.log(`User is ${authenticated ? 'authenticated' : 'not authenticated'}`);
            } catch (error) {
                console.error('Failed to initialize auth adapter:', error);
            }
            updateAuthCookies();
            if (authenticated) {
                window.location.reload();
            }
            else {
                alert("Authentication failed. Maybe a configuration problem?")
            }
        }

        """  # noqa: ISC003
                + f'auth_active={"true" if get_config().auth else "false"};'  # noqa: ISC003
                + r"""

        console.log("Auth active:", auth_active);

        [access_token, refresh_token] = getAuthCookies();

        const keycloak = new Keycloak({
        """
                + f"url: '{get_config().dashboarding_frontend_auth_settings.auth_url}',"
                + f"realm: '{get_config().dashboarding_frontend_auth_settings.realm}',"
                + f"clientId: '{get_config().dashboarding_frontend_auth_settings.client_id}'"
                + r"""
        });

        if (auth_active) {
            console.log("Initializing keycloak")
            init_keycloak();
        }"""
            )
        ],
    ]

    return str(dashboard_login_stub_html)


def error_message_part(exec_resp: ExecutionResponseFrontendDto) -> Element:
    error_content = []
    if exec_resp.error is not None:
        error_content.append(
            h4(style="color:red;text-align:center")["An error occured during execution!"]
        )
        error_content.append(
            div(style="margin:10px")[
                b["Error Message: "],
                exec_resp.error.message,
                br,
                b["Error Type: "],
                exec_resp.error.type,
                br,
                b["Complete Error Information:"],
                br,
                pre(style="width:100%;max-width:inherit")[exec_resp.error.json(indent=2)],
            ]
        )

    if exec_resp.traceback is not None:
        error_content.append(
            div(style="margin:10px")[
                br, b["Traceback:"], pre(style="width:100%;max-width:inherit")[exec_resp.traceback]
            ]
        )

    return div[*error_content]


def generate_apply_bar() -> Element:
    return div(
        class_="apply-bar",
        id="apply-bar",
        style=(
            "z-index:2;position:sticky;top:0;padding:3px 10px;display:none;"
            "background-color:rgba(255, 217, 179, 0.8)"
        ),
    )[
        "There have been configuration or input value changes that need to be applied.",
        button(
            id="discard-button",
            style="margin:5px",
            title="Discard Changes",
            onclick="discard_changes()",
        )["Discard"],
        button(
            id="apply-button",
            style="margin:5px",
            title="Apply Changes (Ctrl+Enter)",
            onclick="apply_changes()",
        )["Apply"],
    ]


def generate_dashboard_html(
    transformation_revision: TransformationRevision,
    actually_used_wiring: WorkflowWiring,
    exec_resp: ExecutionResponseFrontendDto,
    autoreload: int | None,
    override_mode: OverrideMode,
    calculated_from_timestamp: datetime.datetime | None,
    calculated_to_timestamp: datetime.datetime | None,
    relNow: str | None,
    inputs_to_expose: set[str],
    use_release_wiring: bool = False,
    locked: bool = False,
) -> str:
    """Generate full dashboard html page"""

    # obtain dashboard layout
    item_positions = actually_used_wiring.dashboard_positionings
    positioning_dict = item_positioning_dict(item_positions)

    exposed_inputs = {
        dashboard_id_for_io(inp_name, GridstackPositioningType.INPUT)
        for inp_name in inputs_to_expose
    }

    # obtain plotly outputs from result
    plotly_outputs = {
        (
            dashboard_id_for_io(name, GridstackPositioningType.OUTPUT)
        ): exec_resp.output_results_by_output_name[name]
        for name in exec_resp.output_results_by_output_name
        if exec_resp.output_types_by_output_name[name] == "PLOTLYJSON"
    }

    string_outputs = {
        (
            dashboard_id_for_io(name, GridstackPositioningType.OUTPUT)
        ): exec_resp.output_results_by_output_name[name]
        for name in exec_resp.output_results_by_output_name
        if exec_resp.output_types_by_output_name[name] == "STRING"
    }

    dataframe_outputs = {
        (
            dashboard_id_for_io(name, GridstackPositioningType.OUTPUT)
        ): exec_resp.output_results_by_output_name[name]
        for name in exec_resp.output_results_by_output_name
        if exec_resp.output_types_by_output_name[name] == "DATAFRAME"
    }

    multitsframe_outputs = {
        (
            dashboard_id_for_io(name, GridstackPositioningType.OUTPUT)
        ): exec_resp.output_results_by_output_name[name]
        for name in exec_resp.output_results_by_output_name
        if exec_resp.output_types_by_output_name[name] == "MULTITSFRAME"
    }

    datatable_script = script[
        Markup(r"""
        // ======== Tabulator datatables ========

        function get_datatable(div_id) {
            dom_element = document.getElementById(div_id);
            let table = Tabulator.findTable(dom_element)[0];
            return table;
        }

        function get_datatable_by_dashboard_id(db_id) {
            return get_datatable("datatable-" + "dftable-" + db_id);
        }

        function toggle_column_filters(db_id, active=null) {
            let my_table_id = "dftable-" + db_id;
            filter_checkbox = document.getElementById("filter_check-" + my_table_id);

            let my_datatable = get_datatable_by_dashboard_id(db_id);

            columns = my_datatable.getColumns();

            let should_be_active
            if (active==null) {
                should_be_active = filter_checkbox.checked;
            } else {
                should_be_active = active;
            }

            document.documentElement.style.setProperty('--table-filters-display', 'none');

            if (should_be_active) {
                document.documentElement.style.setProperty('--table-filters-display', 'block');
                // header_filter_div.style.display = "block"
            } else {
                document.documentElement.style.setProperty('--table-filters-display', 'none');
                //header_filter_div.style.display = "none"
            }



            if (my_datatable != null) {
                my_datatable.redraw();
            }

        }

        function create_and_register_tabulator_datatable(
                db_id,
                data_row_list,
                column_descriptions
        ) {
            let my_table_id = "dftable-" + db_id;
            let data_table_div = document.getElementById("datatable-" + my_table_id);

            let my_datatable = new Tabulator(data_table_div, {
                data: data_row_list,
                columns: column_descriptions,
                layout:"fitColumns", // fitColumns
                resizableColumnFit: true,
                // resizableColumnGuide: true,
                placeholderHeaderFilter:"No Matching Data",
                renderVertical:"basic",
                renderHorizontal:"basic",
                movableColumns: true

            });


            my_datatable.on("tableBuilt", function(){
                toggle_column_filters(db_id, false);
            });


        }""")
    ]

    main_scripts = script[
        Markup(
            r"""


        // ==== General functions =====

        const handle_toggle_button = (event, options = {}) => {
            // Example usage:
            /*
            <link
                href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.6.0/css/all.min.css"
            rel="stylesheet"
            >
            <button onclick="handle_toggle_button(event, {
                onToggle: (isActive) => console.log('Button toggled:', isActive)
            })">
                <i class="fa-regular fa-heart"></i>
            </button>

            // Or with event listener
            document.querySelector('.toggle-button').addEventListener('click', (e) => {
                handle_toggle_button(e, {
                    activeIcon: 'fa-solid fa-star',
                    inactiveIcon: 'fa-regular fa-star'
                });
            });
            */

            // Default options
            const defaultOptions = {
                activeClass: 'active',
                inactiveClass: 'inactive',
                activeIcon: 'fa-solid',
                inactiveIcon: 'fa-regular',
                onToggle: null, // Callback function
                preventDefault: true
            };

            // Merge default options with provided options
            const settings = { ...defaultOptions, ...options };

            // Prevent default button behavior if specified
            if (settings.preventDefault) {
                event.preventDefault();
            }

            const button = event.currentTarget;
            const icon = button.querySelector('i') || button.querySelector('svg');

            if (!icon) {
                console.warn('No Font Awesome icon found in button');
                return;
            }

            // Toggle button active state
            const isActive = button.classList.toggle(settings.activeClass);
            button.classList.toggle(settings.inactiveClass, !isActive);

            // Toggle icon classes
            if (icon.classList.contains(settings.activeIcon)) {
                icon.classList.replace(settings.activeIcon, settings.inactiveIcon);
            } else {
                icon.classList.replace(settings.inactiveIcon, settings.activeIcon);
            }

            // Call the callback function if provided
            if (typeof settings.onToggle === 'function') {
                settings.onToggle(isActive, button);
            }
        };


        // ======== Auth ========
        const Keycloak = window["Keycloak"];

        function getCookie(name) {
            const value = `; ${document.cookie}`;
            const parts = value.split(`; ${name}=`);
            if (parts.length === 2) return parts.pop().split(';').shift();
            return null;
        }

        function updateAuthCookies() {
            if (keycloak.token !=  null) {
                document.cookie = "access_token="+keycloak.token + ";SameSite=Strict";
            }
        }

        function deleteCookie(name) {
            document.cookie = name + "= ; expires = Thu, 01 Jan 1970 00:00:00 GMT";
        }

        function getAuthCookies() {
            access_token = getCookie("access_token");
            refresh_token = getCookie("refresh_token");
            return [access_token, refresh_token]
        }


        async function logout_user(){
            deleteCookie("access_token");
            await keycloak.logout(); // will reload page
        }

        let kc_inited = false;

        async function init_keycloak() {
            if (!kc_inited) {
                try {
                    console.log("access token:", access_token);
                    console.log("refresh token:", refresh_token);
                    console.log(keycloak);
                    const authenticated = await keycloak.init(
                        {token: access_token, refreshToken: refresh_token,
                        onLoad: "check-sso",
                        redirectUri: location.href, enableLogging: true,
                    checkLoginIframe:false,
                        pkceMethod:"S256" }
                    );
                    console.log("Waiting");
                    console.log(`User is ${authenticated ? 'authenticated' : 'not authenticated'}`);
                } catch (error) {
                    console.error('Failed to initialize auth adapter:', error);
                }
                updateAuthCookies();

                if (keycloak.idTokenParsed != null) {
                    console.log("Setting username form id token");
                    document.getElementById("logout_button").title=(
                        "Logout " + keycloak.idTokenParsed.preferred_username
                    );
                }
                kc_inited = true;
                //window.location.reload();
            }
        }

        """
            f'auth_active={"true" if get_config().auth else "false"};'
            r"""

        console.log("Auth active:", auth_active);

        [access_token, refresh_token] = getAuthCookies();


        const keycloak = new Keycloak({
        """
            f"url: '{get_config().dashboarding_frontend_auth_settings.auth_url}',"
            f"realm: '{get_config().dashboarding_frontend_auth_settings.realm}',"
            f"clientId: '{get_config().dashboarding_frontend_auth_settings.client_id}'"
            r"""
        });

        async function refresh_token_and_update_cookies() {
            if (keycloak.parsedRefreshToken != null) {
                console.log("Updating tokens via keycloak object")
                refreshed = await keycloak.updateToken();
                console.log("Finished updating tokens via keycloak object")
                updateAuthCookies();
            } else {
                console.log("Not refreshing since not refresh token was available.")
            }
        }




        // ======== Gridstack / resizing ========



        var options = { // put in gridstack options here
            disableOneColumnMode: true, // for jfiddle small window size
            column: 24,
            float: true,
            resizable: {
                handles: 'se, sw'
            },
            draggable: {
                handle: '.panel-heading',
            },
            animate: false,
            cellHeight: 80 // fix to n pixels
        };
        var grid = GridStack.init(options);

        function resize_plot(name) {
            // Plotly.Plots.resize(name);

            Plotly.relayout(name, {
               width: document.getElementById("container-" + name).clientWidth ,
               height: document.getElementById("container-" + name).clientHeight - 30
            });

            saveGrid();
        }




        // ======== Config / Query Params / Update / Reload ========

        function toggle_config_visibility() {
            targetDiv = document.getElementById("config-panel");
            if (targetDiv.style.display !== "none") {
                targetDiv.style.display = "none";
                document.getElementById("config-button-image").className="fa-solid fa-chevron-down";
            } else {
                targetDiv.style.display = "block";
                document.getElementById("config-button-image").className="fa-solid fa-chevron-up";
            }
        };

        let dashboard_locked = """
            + ("true" if locked else "false")
            + r""";

        async function apply_lock_state() {
            if (dashboard_locked) {
                document.getElementById("lock-button-image").className="fa-solid fa-lock";
                grid.disable();
                upsert_query_parameters_in_url({"locked": "true"});
            } else {
                document.getElementById("lock-button-image").className="fa-solid fa-unlock";
                grid.enable();
                upsert_query_parameters_in_url({"locked": "false"});
            }
        }



        async function toggle_lock(locked=null) {
            if (dashboard_locked) {
                dashboard_locked = false;
            } else {
                dashboard_locked = true;
            }
            await apply_lock_state();
        }

        if (auth_active) {
            (async function() {
                console.log("Initializing keycloak in actual dashboard")

                await init_keycloak();
                keycloak.onTokenExpired = () => {
                    console.log("Refreshing tokens and cookies")
                    refresh_token_and_update_cookies();
                }
                await apply_lock_state();
                console.log("Keycloak sucessfully initialized")
            })();
        } else {
            apply_lock_state();
        }

        function toggle_apply_bar_visibility(visible=null) {
            targetDiv = document.getElementById("apply-bar");

            if (visible===null) { // toggle!
                if (targetDiv.style.display !== "none") {
                    targetDiv.style.display = "none";
                } else {
                    targetDiv.style.display = "block";
                }
            } else {
                if (visible) {
                    targetDiv.style.display = "block";
                } else {
                    targetDiv.style.display = "none";
                }
            }
        }

        function set_unapplyied_changes() {
            toggle_apply_bar_visibility(true);
        }

        function discard_changes() {
            reload_current_url();
        }

        function apply_changes() {
            update_dashboard();
        }

        function on_autoreload_select_change(autoreload_selector_element) {
            update_dashboard();
        }

        const autoreload_selector_element = document.getElementById("autoreload-select");

        if (autoreload_selector_element.value != "none") {
            setTimeout(function(){
                update_dashboard();
            }, parseInt(autoreload_selector_element.value) * 1000);
        }



        """
            + "\n".join(
                (
                    f"""plot = Plotly.newPlot("{db_id}",
                        {json.dumps(ensure_working_plotly_json(plotly_json))}\n);

                resize_plot("{db_id}");
                resize_plot("{db_id}");  // second time, otherwise width is not correct in chrome
                """
                    for db_id, plotly_json in plotly_outputs.items()
                )
            )
            + r"""


        grid.on('resizestop', function(event, el) {
            var inp_name = el.getAttribute("db_id");
            var inp_type = el.getAttribute("input_type");
            console.log("Resizestop for: " + inp_name)

            if (inp_type=="PLOTLYJSON") {
                resize_plot(inp_name);
                resize_plot(inp_name); // second time, otherwise width is not correct in chrome
            }

            if (inp_type=="DATAFRAME" || inp_type=="MULTITSFRAME") {
                get_datatable_by_dashboard_id(inp_name).redraw();
            }
        });

        function dashboard_id_for_io(io_name, type) {
            if (type == "OUTPUT") {
                return "o." + io_name;
            } else if (type == "INPUT") {
                return "i." + io_name;
            }
        }

        function remove_at_beginning(the_string, to_remove) {
            if (the_string.startsWith(to_remove)) {
                return the_string.slice(to_remove.length);
            } else {
                return the_string;
            }
        }

        function parse_dashboard_id(dashboard_id) {
            if (dashboard_id.startsWith("i.")) {
                return [remove_at_beginning(dashboard_id, "i."), "INPUT"];
            } else if (dashboard_id.startsWith("o.")) {
                return [remove_at_beginning(dashboard_id, "o."), "OUTPUT"];
            } else { // default to output
                return [dashboard_io, "OUTPUT"];
            }
        }

        function gridstack_positioning_to_wiring_positioning(positioning) {
            [io_name, io_type] = parse_dashboard_id(positioning.id);
            return {
                "id": io_name,
                "type": io_type,
                "x": positioning.x,
                "y": positioning.y,
                "w": positioning.w,
                "h": positioning.h,
            }
        }

        function gridstack_positionings_to_wiring_positionings(gridstack_positionings) {
            return gridstack_positionings.map(gridstack_positioning_to_wiring_positioning);
        }

        function default_x_y(val) {
            if (val == "" || (typeof val == 'undefined')) {
                return "0";
            } else {
                return val;
            }
        }

        function default_width_height(val) {
            if (val == "" || (typeof val == 'undefined') ) {
                return "1";
            } else {
                return val;
            }
        }

        function delete_query_parameter(param) {
            var queryParams = new URLSearchParams(window.location.search);
            queryParams.delete(param);
            history.replaceState(null, null, "?"+queryParams.toString());
        }

        function upsert_query_parameters_in_url(param_dict) {
            var queryParams = new URLSearchParams(window.location.search);

            for (ind in param_dict) {
                queryParams.set(ind, param_dict[ind]);
            }
            history.replaceState(null, null, "?"+queryParams.toString());
        }

        async function update_positioning_to_test_wiring() {
            var positionings = grid.save(false, false);

            headers =  {'Content-Type': 'application/json'}
            if (auth_active) {
                console.log("Refreshing tokens / cookie")
                await refresh_token_and_update_cookies();
                console.log("Finished refreshing tokens / cookie")
                headers["Authorization"] = "Bearer " + keycloak.token;
            }

            fetch("dashboard/positioning", {
                method: "PUT",
                headers: headers,
                body: JSON.stringify(gridstack_positionings_to_wiring_positionings(positionings))
            }).then(res => {
                console.log("Request to dashboard/positioning complete! response:", res);
            });
        }

        // autosave on actual positioning changes:
        grid.on('change', async function(event, items) {
            console.log("Save positioning")

            positionings_dict = get_current_positionings_dict();
            upsert_query_parameters_in_url(positionings_dict);

            if (! document.getElementById("use_release_wiring").checked) {
                // only store positionings at test wiring if test wiring is actually used.
                await update_positioning_to_test_wiring();
            }
        });

        // Allow to press ctrl+enter to apply changes
        // In particular helpful when editing input values, avoids the need
        // to use the mouse to press the Apply button.
        document.addEventListener('keydown', function(event) {
        if (event.ctrlKey && event.key === 'Enter') {
            apply_changes();
        }
        });


        window.addEventListener('resize', function(event) {
        """
            + "\n".join(
                (
                    f"""
                setTimeout(resize_plot, 100,"{db_id}");
                // second time, otherwise width is not correct in chrome:
                setTimeout(resize_plot, 110,"{db_id}");
                """
                    for db_id, plotly_json in plotly_outputs.items()
                )
            )
            + r"""

        }, true);

        function get_current_positionings_dict() {
            var positionings = grid.save(false, false);
            pos_dict = {};
            for (ind in positionings) {
                pos_dict[positionings[ind].id + ".pos" ] = [
                        default_x_y(positionings[ind].x),
                        default_x_y(positionings[ind].y),
                        default_width_height(positionings[ind].w),
                        default_width_height(positionings[ind].h)
                    ].join('_');
            }
            return pos_dict;
        }

        function saveGrid() {
            var res = grid.save(false, false);
        }

        function url_params_from_state() {
            var param_dict = {};
            override_selector = document.getElementById("override-timerange-select");
            if (override_selector.value == "none") {
                param_dict = {};
            } else if (override_selector.value == "absolute") {
                selected_dates = flatpicker_abs_range.selectedDates;
                param_dict = {
                    fromTimestamp: selected_dates[0].toISOString(),
                    toTimestamp: selected_dates[1].toISOString()
                }
            } else {
                param_dict = {
                    relNow: override_selector.value
                }
            }

            autoreload_selector = document.getElementById("autoreload-select");

            if (autoreload_selector.value != "none") {
                param_dict["autoreload"] = autoreload_selector.value;
            }

            if (document.getElementById("use_release_wiring").checked) {
                param_dict["use_release_wiring"] = "true";
            }

            positionings_dict = get_current_positionings_dict();
            param_dict = {...param_dict, ...positionings_dict};

            // get which inputs to expose from respective checkboxes

            exposed_inputs = ["""
            + ",".join(
                ['"' + inp.name + '"' for inp in transformation_revision.io_interface.inputs]  # type: ignore
            )
            + r"""].filter(
                (inp_name) => document.getElementById("expose_input-" + inp_name).checked
            );

            exposed_inputs_string = exposed_inputs.join(",")

            param_dict["exposed_inputs"] = exposed_inputs_string;

            exposed_inputs.forEach( (inp_name) => {


                let allowed_values = null;
                allowed_values_string = document.getElementById(
                    "allowed-input-values-" + inp_name
                ).value
                if (allowed_values_string !== "" && ! (allowed_values_string===null)) {
                    param_dict["i." + inp_name + ".allowed"] = allowed_values_string;
                    allowed_values = allowed_values_string.split(",");
                }

                let input_element = document.getElementById("input-" + "i." + inp_name);

                let possible_value_from_input = null;
                let value_set_in_input = false;
                if (! (input_element===null)) {
                    value_set_in_input = true;
                    possible_value_from_input = input_element.value;
                    param_dict["i." + inp_name + ".v"] = input_element.value
                }

                if ((allowed_values !== null) && value_set_in_input) {
                    if (allowed_values.includes(possible_value_from_input)) {
                        param_dict["i." + inp_name + ".v"] = possible_value_from_input;
                    } else {
                        param_dict["i." + inp_name + ".v"] = allowed_values[0];
                    }
                } else if (allowed_values !== null)  {
                    param_dict["i." + inp_name + ".v"] = allowed_values[0];
                } else if (value_set_in_input) {
                    param_dict["i." + inp_name + ".v"] = possible_value_from_input;
                }

            });

            param_dict["locked"] = dashboard_locked;


            console.log("new param dict", param_dict)
            return param_dict
        };

        function input_value_changed() {
            set_unapplyied_changes();
        }

        async function reload_current_url() {
            window.location.reload();
        }

        async function update_dashboard() {
            url_param_dict = url_params_from_state();

            const url_param_data = new URLSearchParams(url_param_dict);
            if (auth_active) {
                await refresh_token_and_update_cookies();
            }

            // reload with new query params
            window.location.replace('dashboard' + '?' + url_param_data.toString() );

        };

        async function on_override_select_change(overrideSelect){
            if (overrideSelect.value == "absolute") {
                flatpicker_abs_range.set("clickOpens", true);

                decide_warning_absolute_range_incomplete(update_complete_dashboard=true)
                return;
            } else {
                flatpicker_abs_range.set("clickOpens", false);
            }

            if (overrideSelect.value == "none") {
                // simply use original wiring
                await update_dashboard()
            } else {
                // neither "absolute" nor "none", i.e. some of the timeranges relative
                // to "now"
                await update_dashboard()
            }

        };

        async function decide_warning_absolute_range_incomplete(
                update_complete_dashboard = false)
            {
            selectedDates = flatpicker_abs_range.selectedDates;

            if (selectedDates.length == 1) {
                console.log("only one datetime!")
                document.getElementById("datetime-picker-warning"
                    ).style.display = "inline-block";


            } else if (selectedDates.length == 2) {
                console.log("two datetimes. okay for updating");
                document.getElementById("datetime-picker-warning").style.display = "none";
                if (update_complete_dashboard) {
                    await update_dashboard();
                }

            } else {
                console.log("no datetime or something unexpected")
                document.getElementById("datetime-picker-warning"
                    ).style.display = "inline-block";
            }
        };

        const flatpicker_abs_range = flatpickr("#datetimepicker-absolute", {
            enableTime: true,  // enabling this leads to incomplete ranges being possible :-(
            mode: 'range',
            dateFormat: 'Z',
            time_24hr: true,
            altInput: true,
            altFormat: 'Y-m-d h:i',
            clickOpens: (document.getElementById("override-timerange-select"
                ).value == "absolute"),
            """
            + f"""{ ('defaultDate: ["'
            + calculated_from_timestamp.isoformat(timespec="milliseconds").split("+")[0]+ "Z"
            + '", "'
            + calculated_to_timestamp.isoformat(timespec="milliseconds").split("+")[0] + "Z"
            + '"],'
     ) if (calculated_from_timestamp is not None
           and calculated_to_timestamp is not None) else ""}"""
            + r"""

            onClose: async function(selectedDates, dateStr, instance){
                // ...

                await decide_warning_absolute_range_incomplete(update_complete_dashboard=true);

            }
        });

        // for access of the created input (altInput) hiding the original input
        const created_input = flatpicker_abs_range.input.parentElement.lastElementChild;

        const datetime_picker_absolute = document.getElementById("datetimepicker-absolute")

    """,
            errors="ignore",
        )
    ]

    # construct the html from its parts

    body_contents = (
        datatable_script,
        div(style="display:flex;margin-bottom:4px;")[
            generate_dashboard_title_div(transformation_revision),
            generate_timerange_overriding_controls_div(override_mode, relNow),
            generate_reload_and_config_buttons_div(autoreload),
        ],
        generate_apply_bar(),
        generate_config_panel_div(
            transformation_revision, actually_used_wiring, use_release_wiring, inputs_to_expose
        ),
        error_message_part(exec_resp),
        div(style="background:#eeeeee")[
            generate_gridstack_div(
                positioning_dict,
                plotly_outputs,
                string_outputs,
                dataframe_outputs,
                multitsframe_outputs,
                actually_used_wiring,
                exposed_inputs,
            )
        ],
        main_scripts,
    )

    dashboard_html = str(html[*DASHBOARD_HEAD_ELEMENTS, body[div[*body_contents]]])

    return dashboard_html
