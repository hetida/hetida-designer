"""Dashboarding

Generate HTML / Styles / Javascript for the experimental dashboarding feature.
"""

import datetime
import json
import os
from enum import Enum
from typing import Any

import pandas as pd

from hetdesrun.backend.models.info import ExecutionResponseFrontendDto
from hetdesrun.models.wiring import GridstackItemPositioning, WorkflowWiring
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
    return {item_positioning.id: item_positioning for item_positioning in gridstack_item_positions}


def gs_div_attributes_from_item_positioning(
    item_positioning: GridstackItemPositioning,
) -> str:
    return f"""

    {' gs-x="' + str(item_positioning.x)+'"' if item_positioning.x is not None else ' '}
    {' gs-y="' + str(item_positioning.y)+'"' if item_positioning.y is not None else ' '}
    {' gs-w="' + str(item_positioning.w)+'"' if item_positioning.w is not None else ' '}
    {' gs-h="' + str(item_positioning.h)+'"' if item_positioning.h is not None else ' '}

    """


def plotlyjson_to_html_div(
    name: str,
    plotly_json: Any,
    item_positioning: GridstackItemPositioning,
    header: str | None = None,
) -> str:
    plotly_json = ensure_working_plotly_json(plotly_json)

    return f"""
    <div class="grid-stack-item" input_name="{name}" id="gs-item-{name}" gs-id="{name}"
            {gs_div_attributes_from_item_positioning(item_positioning)}
            >
        <div class="grid-stack-item-content" id="container-{name}" style="
                ">
             <div class="panel-heading" id="heading-{name}" style="user-select:none;height:20;
                color:#888888;font-size:18px;font-family:sans-serif;text-align:center;">
                    {name if header is None else header}
            </div>

            <div id="plot-container-{name}" style="margin:0;padding:0;width:100%">
                <div id="{name}" style="width:100%;height:100%;margin:0;padding:0"></div>
            </div>
        </div>
    </div>"""


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


DASHBOARD_HEAD = r"""
    <!DOCTYPE html>
    <html>

    <script
        src="https://cdn.jsdelivr.net/npm/keycloak-js@25.0.5/dist/keycloak.min.js"
        >
    </script>

    <script
        src="https://cdn.jsdelivr.net/npm/gridstack@9.5.0/dist/gridstack-all.js" charset="utf-8">
    </script>

    <link
        href=" https://cdn.jsdelivr.net/npm/gridstack@9.5.0/dist/gridstack.min.css "
        rel="stylesheet"
    >
    <link rel="icon" type="image/png" href="data:image/png;base64,iVBORw0KGgo=">
    <link
        href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css"
        rel="stylesheet"
    >
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js" charset="utf-8"></script>

    <!-- flatpickr -->
    <link
        href="https://cdn.jsdelivr.net/npm/flatpickr@4.6.13/dist/flatpickr.min.css"
        rel="stylesheet"
    >

    <script src="https://cdn.jsdelivr.net/npm/flatpickr@4.6.13"></script>

    <link rel="stylesheet" href="https://unpkg.com/boltcss@0.6.0/bolt.min.css">

    <head>
    <style>
        .grid-stack {
            background: #eeeeee;
            padding: 0;
            margin: 0;
        }

        .panel-heading {
            background: #f9f9f9;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
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
    </style>
    </head>
    """


def generate_dashboard_title_div(
    transformation_revision: TransformationRevision,
) -> str:
    return f"""
        <div style="color:#666666;
                margin-left:1em;
                text-align:left;
                width:50%;
                align-items:center">
            <h4 style="color:#555555;padding-bottom:0px;margin-bottom:0px"
                title="{transformation_revision.description}">
            {transformation_revision.name}
            </h4>
            <span
                title="{"id: " + str(transformation_revision.id)
                        + os.linesep + "group id: "
                        + str(transformation_revision.revision_group_id)}"
            >
            {"<b>" + transformation_revision.version_tag
                   + " (" + transformation_revision.state  + ")</b>"}
            </span>
        </div>
    """


def generate_timerange_overriding_controls_div(
    override_mode: OverrideMode, relNow: str | None
) -> str:
    return (
        f"""
         <div style="width:50%;display:flex;align-items:center">
            <div style="max-width:30em;min-width:11em;margin-right:4px">

            <select name="override" id="override-timerange-select"
                    onchange="on_override_select_change(this)"
                    title="Override input timeranges"
                    style="width:100%;max-width:inherit"
                    >
                <option value="absolute"
                    {"selected" if
                        override_mode is OverrideMode.Absolute else ""}
                >Absolute</option>
                <option value="none"
                     {"selected" if (override_mode is OverrideMode.NoOverride) else ""}
                >do not override</option>
                """
        + "\n".join(
            f"""<option
                    value="{rel_range_desc}"
                    {"selected" if (override_mode is OverrideMode.RelativeNow
                                    and relNow==rel_range_desc) else ""}
                >last {rel_range_desc}</option>"""
            for rel_range_desc in RELATIVE_RANGE_DESCRIPTIONS
        )
        + r"""
            </select>
            </div>
            <div id="picker-span"
                style="display:flex;align-items:center;width:100%;min-width:10em;margin-right:4px" >
                    <input class="hd-dashboard-timerange-picker"
                        id="datetimepicker-absolute"
                        type="text"
                        placeholder="Select range...">
                    <i class="fa-solid fa-triangle-exclamation" id="datetime-picker-warning"
                        title="Uncomplete daterange selected."
                        style="color:#880000;display:none;heigt:100%"></i>
            </div>
        </div>

    """
    )


def generate_reload_and_config_buttons_div(autoreload: int | None) -> str:
    return (
        f"""
        <div id="buttons-right" style="display:flex;align-items:center;
            width:fit-content;margin-left:4px" >

            <select name="autoreload" id="autoreload-select"
                    title="Autoreload"
                    onchange="on_autoreload_select_change(this)"
                    style="width:10em;max-width:10em;margin-right:2px"
                    >
                <option value="none" {"selected" if (autoreload is None) else ""}
                    >no</option>
                """
        + "\n".join(
            f"""<option value="{str(autoreload_interval_length)}"
                    {"selected" if autoreload==autoreload_interval_length else ""}
                    >{str(autoreload_interval_length) + "s"}</option>"""
            for autoreload_interval_length in AUTORELOAD_INTERVALS
        )
        + r"""
            </select>

            <button class="btn" title="Reload" onclick="update_dashboard();"
                    style="margin-left:2px">
                <i class="fa-solid fa-arrow-rotate-right"></i>
            </button>

            <button class="btn" title="View/Hide dashboard configuration"
                    onclick="toggle_config_visibility();"
                    style="margin-left:8px;margin-right:4px">
                <i class="fa-solid fa-chevron-down" id="config-button-image"></i>
            </button>

            """
        + (
            r"""
            <button class="btn" title="Logout" id="logout_button"
                    onclick="logout_user();"
                    style="margin-left:2px;margin-right:4px">
                <i class="fa-solid fa-right-from-bracket" id="logout_button_image"></i>
            </button>
            """
            if get_config().auth
            else ""
        )
        + r"""

        </div>

    """  # noqa: ISC003
    )


def generate_config_panel_div(transformation_revision: TransformationRevision) -> str:
    return f"""
   <div id="config-panel" style="display:none;align-items:center;width:100%;padding:15px">
        <div>
            <details style="margin-bottom: 6px">
            <summary>
            Transformation Revision Details
            </summary>
            <b>name</b>: {transformation_revision.name} <br>
            <b>version tag</b>: {transformation_revision.version_tag} <br>
            <b>state</b>: {transformation_revision.state} <br>
            <b>type</b>: {transformation_revision.type} <br>
            <b>category</b>: {transformation_revision.category} <br>
            <b>description</b>: {transformation_revision.description} <br>
            <b>id</b>: <a
                href="../{str(transformation_revision.id)}">{str(transformation_revision.id)}
            </a>
            <br>
            <b>revision group id</b>: {str(transformation_revision.revision_group_id)} <br>

            </details>



            <details style="margin-bottom: 6px">
            <summary>
            Documentation
            </summary>
            <div>

            <pre style="width:100%;max-width:inherit">{transformation_revision.documentation}</pre>
            </div>

            </div>
            </details>

            <details>
            <summary>
            Test Wiring
            </summary>
            <div>
            <pre style="width:100%;max-width:inherit">{transformation_revision.test_wiring.json(
                indent=2)}</pre>
            </div>
            </details>

        </div>

    </div>
    """


def generate_gridstack_div(
    positioning_dict: dict[str, GridstackItemPositioning],
    plotly_outputs: dict[str, Any],
) -> str:
    return (
        r"""
    <div class="grid-stack">
    """
        + "\n".join(
            (
                plotlyjson_to_html_div(
                    name,
                    plotly_json,
                    positioning_dict.get(
                        name,
                        GridstackItemPositioning(
                            id=name, x=(ind % 2) * 12, y=(ind // 2) * 3, w=12, h=3
                        ),
                    ),
                )
                for ind, (name, plotly_json) in enumerate(plotly_outputs.items())
            )
        )
        + r"""
    </div>
    """
    )


def generate_login_dashboard_stub() -> str:
    """Login Stub page

    Generates a page only containing what is necessary to trigger a login
    using the keycloak-js library.
    """
    dashboard_login_stub = (
        r"""
    <!DOCTYPE html>
    <html>

    <script
        src="https://cdn.jsdelivr.net/npm/keycloak-js@25.0.5/dist/keycloak.min.js"
        >
    </script>


    <script>
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
        }

    </script>

    """
    )

    return dashboard_login_stub


def generate_dashboard_html(
    transformation_revision: TransformationRevision,
    exec_resp: ExecutionResponseFrontendDto,
    autoreload: int | None,
    override_mode: OverrideMode,
    calculated_from_timestamp: datetime.datetime | None,
    calculated_to_timestamp: datetime.datetime | None,
    relNow: str | None,
) -> str:
    """Generate full dashboard html page"""

    # obtain dashboard layout
    item_positions = transformation_revision.test_wiring.dashboard_positionings
    positioning_dict = item_positioning_dict(item_positions)

    # obtain plotly outputs from result
    plotly_outputs = {
        name: exec_resp.output_results_by_output_name[name]
        for name in exec_resp.output_results_by_output_name
        if exec_resp.output_types_by_output_name[name] == "PLOTLYJSON"
    }

    # construct the html from its parts

    dashboard_html = (
        DASHBOARD_HEAD
        + f"""
    <body>
    <div style="display:flex;margin-bottom:4px;">
        {generate_dashboard_title_div(transformation_revision)}
        {generate_timerange_overriding_controls_div(override_mode, relNow)}
        {generate_reload_and_config_buttons_div(autoreload)}
    </div>
    {generate_config_panel_div(transformation_revision)}
    {generate_gridstack_div(positioning_dict, plotly_outputs)}
    """
        + r"""

    <script>
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

        async function init_keycloak() {
            try {
                const authenticated = await keycloak.init(
                    {token: access_token, refreshToken: refresh_token,
                    onLoad: 'login-required',
                 checkLoginIframe:false,
                pkceMethod:"S256" }
                );
                console.log(`User is ${authenticated ? 'authenticated' : 'not authenticated'}`);
            } catch (error) {
                console.error('Failed to initialize auth adapter:', error);
            }
            updateAuthCookies();
            document.getElementById("logout_button").title=(
                "Logout " + keycloak.idTokenParsed.preferred_username
            );
            //window.location.reload();
        }

        """
        + f'auth_active={"true" if get_config().auth else "false"};'
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

        async function refresh_token_and_update_cookies() {
            refreshed = await keycloak.updateToken();
            updateAuthCookies();
        }

        if (auth_active) {
            console.log("Initializing keycloak")
            init_keycloak();
            keycloak.onTokenExpired = () => {
                refresh_token_and_update_cookies();
            }
        }



        var options = { // put in gridstack options here
            disableOneColumnMode: true, // for jfiddle small window size
            column: 24,
            float: true,
            resizable: {
                handles: 'e, se, s, sw, w'
            },
            draggable: {
                handle: '.panel-heading',
            },
            animate: false
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
                f"""plot = Plotly.newPlot("{name}",
                        {json.dumps(ensure_working_plotly_json(plotly_json))}\n);

                resize_plot("{name}");
                resize_plot("{name}");  // second time, otherwise width is not correct in chrome
                """
                for name, plotly_json in plotly_outputs.items()
            )
        )
        + r"""

        grid.on('resizestop', function(event, el) {
            var inp_name = el.getAttribute("input_name");
            console.log("Resizestop for: " + inp_name)

            resize_plot(inp_name);
            resize_plot(inp_name); // second time, otherwise width is not correct in chrome
        });

        // autosave on actual positioning changes:
        grid.on('change', async function(event, items) {
            console.log("Save positioning")
            // items.forEach(function(item) {...});
            var positionings = grid.save(false, false);

            headers =  {'Content-Type': 'application/json'}
            if (auth_active) {
                await refresh_token_and_update_cookies();
                headers["Authorization"] = "Bearer " + keycloak.token;
            }

            fetch("dashboard/positioning", {
                method: "PUT",
                headers: headers,
                body: JSON.stringify(positionings)
            }).then(res => {
                console.log("Request complete! response:", res);
            });
        });


        window.addEventListener('resize', function(event) {
        """
        + "\n".join(
            (
                f"""
                setTimeout(resize_plot, 100,"{name}");
                // second time, otherwise width is not correct in chrome:
                setTimeout(resize_plot, 110,"{name}");
                """
                for name, plotly_json in plotly_outputs.items()
            )
        )
        + r"""
        }, true);


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

                return param_dict
            };

            async function update_dashboard() {
                url_param_dict = url_params_from_state();

                const url_param_data = new URLSearchParams(url_param_dict);
                if (auth_active) {
                    await refresh_token_and_update_cookies();
                }
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

    </script>

    </body>

    """
    )
    return dashboard_html
