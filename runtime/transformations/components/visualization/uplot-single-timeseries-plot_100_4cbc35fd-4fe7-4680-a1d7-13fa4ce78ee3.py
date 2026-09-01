"""Documentation for µplot Single Timeseries Plot

# µplot Single Timeseries Plot

## Description

Creates an interactive [µplot](https://github.com/leeoniya/uplot) (uPlot) line chart for a single time series, rendered
as a self-contained HTML fragment. Compared to the Plotly-based "Single Timeseries
Plot" it is lightweight and fast, especially for high-volume timeseries data. It provides mouse zoom, pan and a localized
hover readout.

## Inputs

* **timeseries** (*Pandas Series*): Timeseries to be plotted. Values must be numeric and the index must be a `DateTimeIndex`. Rows with NaN values are dropped before plotting.
* **ymin** (*float, optional*): Lower limit of the y-axis. If not specified, the minimum value is determined automatically from the data.
* **ymax** (*float, optional*): Upper limit of the y-axis. If not specified, the maximum value is determined automatically from the data.
* **color** (*string, optional*): Line color of the plotted series. Defaults to `ki.green`. Can be a hex value like `#89CE6E`, a named color like "red", or a fuseki color like "ki.tech".
* **ylabel** (*string, optional*): Label of the y-axis. If not specified (null/None), the metric name and unit are extracted from the series metadata, if available. If that does not yield a non-empty string or ylabel is explicitly set to the string "__OFF__", no y-axis label will be shown.
* **xmin** (*string, optional*): Lower x-axis limit. The value is interpreted using `dtexp`. If not specified, the queried interval from the metadata is used. If no metadata is available, the minimum timestamp of the series is used.
* **xmax** (*string, optional*): Upper x-axis limit. The value is interpreted using `dtexp`. If not specified, the queried interval from the metadata is used. If no metadata is available, the maximum timestamp of the series is used.
* **connection_type** (*string, optional*): Defines how consecutive data points are connected. As default a linear line is drawn between consecutive datapoints. Matching is case- and separator-insensitive, and common synonyms are accepted; an unrecognized value raises an error rather than silently drawing a linear line. Supported values are:
  * `linear` (default): Straight line segments between points.
  * `forward_steps`: Step plot with horizontal segments followed by vertical transitions (aliases: `steps`, `step`, `forward`, `hv`).
  * `backward_steps`: Step plot with vertical transitions followed by horizontal segments (aliases: `step_before`, `backward`, `vh`).
* **locale** (*string, optional*): A locale string like "de", "de-DE" or "en-US", used to localize the time-axis tick labels, the hover readout and the default legend labels ("Time"/"Value", localized for en/de/fr). If not explicitly provided (null/None) the locale is inferred from the plot target settings. If explicitly provided using this param it has higher priority.
* **target_timezone** (*string, optional*): If this is not provided, i.e. has its default value null / None, the target timezone will be inferred from plot_target_settings. If it is provided this param has higher priority. Example values: "Europe/Berlin" or "+02:00". See possible timezone strings in pandas' tz_convert method or pytz all_timezones list.

## Outputs

* **uplot** (*ANY*): The generated chart as a self-contained HTML fragment (`content_type: "text/html"`), suitable for inline rendering in the protocol viewer and the experimental dashboarding (each embedded in its own iframe).

## Details

* The component visualizes the input **timeseries** as a µplot line chart with point markers and no area fill.
* If **ymin** and **ymax** are not specified, the y-axis range is automatically extended by 5% above and below the data range.
* If the series is empty, the y-axis range defaults to `0` to `1` and the x-axis range is left to µplot's automatic scaling.
* Timestamps are rendered in the target timezone; the time-axis tick labels, the hover readout and the legend labels are localized according to **locale**.
* **Interactivity**: drag a rectangle to zoom into both axes, double-click to reset to the full (configured) range, and hold **Shift** while dragging to pan. Hovering shows the timestamp and value in the legend.

## Example

The JSON input of a typical component invocation for the **timeseries** input is:

```json
{
  "__hd_wrapped_data_object__": "SERIES",
  "__metadata__": {
    "dataset_metadata": {
      "ref_interval_start_timestamp": "2026-06-01T22:00:00.000Z",
      "ref_interval_end_timestamp": "2026-06-08T22:00:00.000Z",
      "ref_interval_type": "closed"
    },
    "single_metric_metadata": {
      "structured_metadata": {
        "metric": {
          "name": "Tagesmittelwert",
          "unit": "l/s",
          "signal_id": "ff05d22b-1968-47d2-9683-e7598723cd56"
        },
        "comments": [],
        "inherited": {}
      }
    }
  },
  "__data__": {
    "name": "7485907a-ae39-45c6-a698-e81fbf6d2dda",
    "index": [
      "2026-06-01T22:00:00.000Z",
      "2026-06-02T22:00:00.000Z",
      "2026-06-03T22:00:00.000Z",
      "2026-06-04T22:00:00.000Z",
      "2026-06-05T22:00:00.000Z",
      "2026-06-06T22:00:00.000Z"
    ],
    "data": [
      567.8958333333,
      588.36875,
      575.3597222222,
      592.5548611111,
      568.5895104895,
      573.8763888889
    ]
  },
  "__data_parsing_options__": {
    "orient": "split"
  }
}
```
"""

import base64
import json
import uuid
from string import Template

import pandas as pd
from dtexp import parse_dtexp
from hdhelpers import (
    get_locale,
    modify_timezone,
    resolve_color,
)
from hdhelpers.metadata import get_queried_interval, get_series_name, get_series_unit

# ---------------------------------------------------------------------------
# Layer 1: generic µplot -> HTML wrapper
#
# A near 1:1 mirror of uPlot's constructor `new uPlot(opts, data, target)`.
# It knows nothing about timeseries, timezones, or locales -- it just embeds
# the (already fully computed) `opts` and `data` and renders responsively.
#
# `opts` is a plain Python structure (dict/list/str/num/bool/None). uPlot
# opts legitimately contain *functions* (formatters, tzDate, path builders),
# which have no JSON representation -- those fields are wrapped in `_RawJS`
# and emitted verbatim by `_js_literal`. No eval / JSON.parse reviver is
# used, so the fragment stays CSP-friendly (inline script only).
# ---------------------------------------------------------------------------


class _RawJS:
    """Marker wrapping a snippet of literal JS *source* (typically a function
    expression) so `_js_literal` emits it verbatim instead of JSON-encoding
    it as a string."""

    __slots__ = ("src",)

    def __init__(self, src: str):
        self.src = src


def _js_literal(value) -> str:
    """Serialize a Python structure (dict / list / str / int / float / bool /
    None, plus `_RawJS` markers) into a JavaScript expression.

    Plain values are emitted via `json.dumps` (valid JS); `_RawJS` values are
    emitted verbatim, which is how functions get into the µplot opts object.
    """
    if isinstance(value, _RawJS):
        return value.src
    if isinstance(value, dict):
        items = [f"{json.dumps(str(k))}: {_js_literal(v)}" for k, v in value.items()]
        return "{" + ", ".join(items) + "}"
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_js_literal(v) for v in value) + "]"
    return json.dumps(value)


_UPLOT_WRAPPER_HTML_TEMPLATE = Template("""
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/uplot@1.6.32/dist/uPlot.min.css">
<script src="https://cdn.jsdelivr.net/npm/uplot@1.6.32/dist/uPlot.iife.min.js"></script>
<style>
  #$div_id-outer {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
  }
  #$div_id-subtitle {
    font-size: 10px;
    color: #888;
    text-align: right;
    padding: 0 4px 2px 0;
    flex: 0 0 auto;
  }
  #$div_id-wrap {
    flex: 1 1 auto;
    min-height: 0;
    width: 100%;
    overflow: hidden;
  }
  #$div_id-wrap .u-legend {
    font-size: 11px;
  }
</style>

<div id="$div_id-outer">
  <div id="$div_id-subtitle">$subtitle</div>
  <div id="$div_id-wrap">
    <div id="$div_id"></div>
  </div>
</div>

<script>
(function() {
  // Both `data` and `opts` are fully computed on the Python side; the JS here
  // only embeds them and wires up responsive resizing. `opts` may contain
  // functions (formatters, tzDate, path builders) -- they are emitted as
  // live JS literals, not strings.
  const data = $data_json;
  const opts = $opts_literal;

  const wrap = document.getElementById("$div_id-wrap");
  const el = document.getElementById("$div_id");

  let curW = wrap.clientWidth;
  let curH = wrap.clientHeight;

  opts.width = curW;
  opts.height = curH;

  const u = new uPlot(opts, data, el);

  function fitToContainer() {
    const totalW = wrap.clientWidth;
    const totalH = wrap.clientHeight;
    if (totalW <= 0 || totalH <= 0) return;

    const chartH = Math.max(10, totalH - 50);

    if (totalW !== curW || chartH !== curH) {
      curW = totalW;
      curH = chartH;
      u.setSize({ width: totalW, height: chartH });
    }
  }

  fitToContainer();

  const ro = new ResizeObserver(() => fitToContainer());
  ro.observe(wrap);
})();
</script>
""")


def render_uplot_html(
    data,
    opts,
    *,
    subtitle: str = "",
    as_base64: bool = False,
) -> str:
    """
    Render `new uPlot(opts, data, el)` as a self-contained, responsive HTML
    fragment. This is a generic thin µplot wrapper: it doesn't know anything
    about timeseries, timezones, or locales -- it only embeds the already
    computed `opts` and `data`.

    Parameters
    ----------
    data:
        JSON-serializable structure matching uPlot's `data` argument
        (e.g. `[timestamps, values, ...]`).
    opts:
        A Python structure (dict/list/str/num/bool/None) describing uPlot's
        `opts` argument. Function-valued fields (formatters, `tzDate`,
        `paths`, ...) must be wrapped in `_RawJS(<js source>)` so they are
        emitted as live JS rather than JSON strings.
    subtitle:
        Optional small line of text shown above the chart (e.g. a timezone
        label). Empty -> nothing shown.
    as_base64:
        If True, return the resulting html fragment base64-encoded instead of
        raw HTML string.
    """

    div_id = f"uplot-{uuid.uuid4().hex}"

    html = _UPLOT_WRAPPER_HTML_TEMPLATE.substitute(
        div_id=div_id,
        subtitle=subtitle,
        data_json=json.dumps(data),
        opts_literal=_js_literal(opts),
    )

    if as_base64:
        return base64.b64encode(html.encode("utf-8")).decode("ascii")

    return html


# ---------------------------------------------------------------------------
# Layer 2: timeseries preparation via pandas
# ---------------------------------------------------------------------------

DEFAULT_EMPTY_XMIN = None  # pd.Timestamp("1970-01-01 00:00:00", tz="UTC")
DEFAULT_EMPTY_XMAX = None  # pd.Timestamp("1970-01-02 00:00:00", tz="UTC")

DEFAULT_EMPTY_YMIN = 0
DEFAULT_EMPTY_YMAX = 1

Y_AXIS_PADDING = 0.05

CONNECTION_TYPE_MAP = {
    "linear": "linear",
    "forward_steps": "hv",
    "backward_steps": "vh",
}

# Extra accepted spellings mapped onto the canonical shapes above. Matching is
# done on a normalized key (lowercased, non-alphanumeric characters stripped),
# so "forward_steps", "forward-steps", "Forward Steps" and "forwardsteps" all
# resolve the same. A bare "step"/"steps" is treated as forward (step-after),
# the common shape for held sensor samples.
_CONNECTION_SHAPE_ALIASES = {
    "line": "linear",
    "forward": "hv",
    "step": "hv",
    "steps": "hv",
    "stepped": "hv",
    "stepafter": "hv",
    "after": "hv",
    "hv": "hv",
    "backward": "vh",
    "stepbefore": "vh",
    "before": "vh",
    "vh": "vh",
}


def _normalize_connection_type(connection_type: str) -> str:
    return "".join(ch for ch in str(connection_type).lower() if ch.isalnum())


def resolve_connection_shape(connection_type: str) -> str:
    """Map a user-supplied `connection_type` onto a canonical µplot line shape
    ("linear" | "hv" | "vh"), accepting the documented values plus common
    spellings/synonyms (case- and separator-insensitive).

    Raises ValueError on an unrecognized value rather than silently falling
    back to linear -- a silent fallback makes a mistyped connection_type look
    like the feature is broken.
    """
    normalized = _normalize_connection_type(connection_type)
    canonical = {_normalize_connection_type(k): v for k, v in CONNECTION_TYPE_MAP.items()}
    shape = canonical.get(normalized) or _CONNECTION_SHAPE_ALIASES.get(normalized)
    if shape is None:
        raise ValueError(
            f"Unknown connection_type {connection_type!r}. Expected one of: "
            + ", ".join(CONNECTION_TYPE_MAP)
            + " (synonyms like 'steps', 'step_before', 'hv'/'vh' are also accepted)."
        )
    return shape


# Localized fallbacks for the two default legend labels (the x/time row and the
# value row shown behind the hovered timestamp/value). uPlot's own hardcoded
# defaults are the English "Time" / "Value"; these replace them by language.
_LEGEND_LABELS = {
    "time": {"en": "Time", "de": "Zeit", "fr": "Temps"},
    "value": {"en": "Value", "de": "Wert", "fr": "Valeur"},
}


def _localized_label(key: str, locale: str | None) -> str:
    """Pick the legend label for `key` ("time"/"value") by the locale's
    language, falling back to English for any unsupported language."""
    lang = (locale or "en").replace("_", "-").split("-")[0].lower()
    table = _LEGEND_LABELS[key]
    return table.get(lang, table["en"])


def get_x_range(
    series: pd.Series, xmin: str | None, xmax: str | None, to_timezone: str | None
) -> tuple[pd.Timestamp | None]:

    requested_xmin, requested_xmax = get_queried_interval(series)

    if xmin is not None:
        xmin_to_use = parse_dtexp(xmin)
    elif requested_xmin is not None:
        xmin_to_use = requested_xmin
    elif not series.empty:
        xmin_to_use = series.index.min()
    else:
        xmin_to_use = DEFAULT_EMPTY_XMIN

    if xmax is not None:
        xmax_to_use = parse_dtexp(xmax)
    elif requested_xmin is not None:
        xmax_to_use = requested_xmax
    elif not series.empty:
        xmax_to_use = series.index.max()
    else:
        xmax_to_use = DEFAULT_EMPTY_XMAX

    return (
        (
            modify_timezone(xmin_to_use, to_timezone=to_timezone)
            if xmin_to_use is not None
            else None
        ),
        (
            modify_timezone(xmax_to_use, to_timezone=to_timezone)
            if xmax_to_use is not None
            else None
        ),
    )


def get_y_range(series: pd.Series, ymin: float | None, ymax: float | None) -> tuple[float]:

    data_min = series.min()
    data_max = series.max()
    delta = data_max - data_min

    if ymin is not None:
        ymin_to_use = ymin
    elif not series.empty:
        ymin_to_use = data_min - delta * Y_AXIS_PADDING
    else:
        ymin_to_use = DEFAULT_EMPTY_YMIN

    if ymax is not None:
        ymax_to_use = ymax
    elif not series.empty:
        ymax_to_use = data_max + delta * Y_AXIS_PADDING
    else:
        ymax_to_use = DEFAULT_EMPTY_YMAX

    return ymin_to_use, ymax_to_use


def get_y_title(series: pd.Series, ylabel: str | None) -> str:

    if ylabel is not None:
        if ylabel == "__OFF__":
            return ""
        return ylabel

    name = get_series_name(series)
    unit = get_series_unit(series)

    if name is not None and unit is not None:
        return name + f" [{unit}]"
    if name is not None:
        return name
    return ""


def _to_adjusted_epoch(ts: pd.Timestamp) -> int:
    """
    uPlot wants plain epoch seconds. To make the wall-clock digits come out
    right for an arbitrary source timezone regardless of the viewer's own
    timezone, we bake the UTC offset into the epoch value itself (the JS
    side then formats with timeZone:"UTC").
    """
    epoch = ts.timestamp()
    off = ts.utcoffset()
    offset_seconds = off.total_seconds() if off is not None else 0
    return int(round(epoch + offset_seconds))


def prepare_timeseries(
    series: pd.Series,
    *,
    ymin: float | None = None,
    ymax: float | None = None,
    xmin: str | None = None,
    xmax: str | None = None,
    ylabel: str | None = None,
    color: str = "ki.green",
    connection_type: str = "linear",
    locale: str | None = None,
    target_timezone: str | None = None,
) -> dict:
    """
    Prepare a pandas Series (DatetimeIndex, tz-aware or naive, any
    resolution) for plotting with µplot: resolves the x/y range, y-axis
    title, color, connection-line shape, and locale, and converts the
    series into the timestamp/value arrays µplot expects.

    Returns a plain dict consumed by `timeseries_to_uplot_opts`; does not
    prepare HTML or JS itself.
    """
    if not isinstance(series, pd.Series):
        raise TypeError("series must be a pandas Series")

    xmin_to_use, xmax_to_use = get_x_range(
        series=series, xmin=xmin, xmax=xmax, to_timezone=target_timezone
    )
    ymin_to_use, ymax_to_use = get_y_range(series=series, ymin=ymin, ymax=ymax)
    ytitle = get_y_title(series=series, ylabel=ylabel)

    series_with_tz = modify_timezone(series.copy(), target_timezone)
    s = series_with_tz.dropna()
    if not isinstance(s.index, pd.DatetimeIndex):
        s.index = pd.to_datetime(s.index)

    tz = s.index.tz
    tz_label = str(tz) if tz is not None else "no timezone (naive)"

    timestamps = [_to_adjusted_epoch(ts) for ts in s.index]
    values = s.astype(float).tolist()

    x_range = (
        [_to_adjusted_epoch(xmin_to_use), _to_adjusted_epoch(xmax_to_use)]
        if xmin_to_use is not None and xmax_to_use is not None
        else None
    )

    locale_to_use = get_locale(locale) or "en-US"

    return {
        "timestamps": timestamps,
        "values": values,
        "tz_label": tz_label,
        "label": ytitle if ytitle else _localized_label("value", locale_to_use),
        "x_label": _localized_label("time", locale_to_use),
        "ytitle": ytitle,
        "color": resolve_color(color),
        "shape": resolve_connection_shape(connection_type),
        "x_range": x_range,
        "y_range": [ymin_to_use, ymax_to_use],
        "locale": locale_to_use,
    }


# ---------------------------------------------------------------------------
# Layer 3: prepared timeseries -> (data, opts) -> render_uplot_html
# ---------------------------------------------------------------------------


def _fmt_value_fn(loc_js: str) -> _RawJS:
    """Cursor / legend readout: full localized date-time.

    The timestamps have the source timezone's UTC offset baked in, so their
    UTC fields equal the desired wall-clock time -- hence timeZone:"UTC".
    `loc_js` is the locale already rendered as a JS literal ("en-US" or null).
    """
    return _RawJS(
        '(u, v) => v == null ? "" : new Intl.DateTimeFormat(' + loc_js + " || undefined, {\n"
        '  timeZone: "UTC", hourCycle: "h23",\n'
        '  year: "numeric", month: "short", day: "2-digit",\n'
        '  hour: "2-digit", minute: "2-digit", second: "2-digit"\n'
        "}).format(new Date(v * 1000))"
    )


def _fmt_ticks_fn(loc_js: str) -> _RawJS:
    """Axis tick labels: granularity chosen from uPlot's increment so labels
    stay readable at any zoom level."""
    return _RawJS(
        "(u, splits, axisIdx, foundSpace, foundIncr) => {\n"
        '  const o = { timeZone: "UTC", hourCycle: "h23" };\n'
        '  if (foundIncr >= 27 * 86400) { o.year = "numeric"; o.month = "short"; }\n'
        '  else if (foundIncr >= 86400) { o.month = "short"; o.day = "2-digit"; }\n'
        '  else if (foundIncr >= 60) { o.hour = "2-digit"; o.minute = "2-digit"; }\n'
        '  else { o.hour = "2-digit"; o.minute = "2-digit"; o.second = "2-digit"; }\n'
        "  const fmt = new Intl.DateTimeFormat(" + loc_js + " || undefined, o);\n"
        "  return splits.map(s => fmt.format(new Date(s * 1000)));\n"
        "}"
    )


def _tz_date_fn() -> _RawJS:
    """Keeps uPlot's internal tick placement aligned to the target timezone's
    day/hour boundaries; the Intl formatters above handle display."""
    return _RawJS(
        "(ts) => {\n"
        "  const d = new Date(ts * 1000);\n"
        "  return new Date(d.getTime() + d.getTimezoneOffset() * 60000);\n"
        "}"
    )


def _pan_plugin() -> _RawJS:
    """Shift+drag pan plugin

    While Shift is held, dragging over the plot area shifts both the x and y
    scales by the pixel delta (converted to scale units). The mousedown is
    caught in the capture phase and `stopImmediatePropagation`'d so uPlot's
    own drag-to-zoom (bound on the same element) does not also fire while
    panning. Box-zoom (plain drag) and double-click-reset are untouched.

    Deliberately installs *no* persistent global listeners: the Shift state
    is read straight off the mousedown event (`md.shiftKey`) instead of
    tracking keydown/keyup on `document`. That keeps the fragment safe to
    embed many times on one page (no per-instance listener pile-up) and free
    of any always-on document handlers that could interfere with the rest of
    the page. The only `document` listeners are `mousemove`/`mouseup`, added
    on mousedown and removed on mouseup, i.e. live only for the duration of a
    single pan gesture (needed so the pan continues if the cursor leaves the
    plot). The `over` mousedown listener is element-scoped and is torn down
    with the element when uPlot destroys it.
    """
    return _RawJS(
        "({\n"
        "  hooks: {\n"
        "    init: [(u) => {\n"
        "      const over = u.over;\n"
        '      over.addEventListener("mousedown", (md) => {\n'
        "        if (!md.shiftKey) return;\n"
        "        md.stopImmediatePropagation();\n"
        "        md.preventDefault();\n"
        '        over.style.cursor = "grabbing";\n'
        "        const xs = u.scales.x, ys = u.scales.y;\n"
        "        const x0 = xs.min, x1 = xs.max, y0 = ys.min, y1 = ys.max;\n"
        "        const xPerPx = (x1 - x0) / (u.bbox.width / uPlot.pxRatio);\n"
        "        const yPerPx = (y1 - y0) / (u.bbox.height / uPlot.pxRatio);\n"
        "        const cx = md.clientX, cy = md.clientY;\n"
        "        const move = (mm) => {\n"
        "          const dx = (cx - mm.clientX) * xPerPx;\n"
        "          const dy = (mm.clientY - cy) * yPerPx;\n"
        "          u.batch(() => {\n"
        '            u.setScale("x", { min: x0 + dx, max: x1 + dx });\n'
        '            u.setScale("y", { min: y0 + dy, max: y1 + dy });\n'
        "          });\n"
        "        };\n"
        "        const up = () => {\n"
        '          document.removeEventListener("mousemove", move);\n'
        '          document.removeEventListener("mouseup", up);\n'
        '          over.style.cursor = "";\n'
        "        };\n"
        '        document.addEventListener("mousemove", move);\n'
        '        document.addEventListener("mouseup", up);\n'
        "      }, true);\n"
        "    }],\n"
        "  },\n"
        "})"
    )


def timeseries_to_uplot_opts(prepared: dict) -> tuple[list, dict]:
    """
    Turn a prepared-timeseries dict (see `prepare_timeseries`) into the
    `(data, opts)` pair the generic `render_uplot_html` wrapper consumes.

    The entire opts object is assembled here in Python; function-valued
    fields are `_RawJS` markers so the wrapper emits them as live JS.
    """
    loc_js = json.dumps(prepared["locale"])  # JS literal: "en-US" or null
    color = prepared["color"]

    series_line = {
        "label": prepared["label"],
        "stroke": color,
        "width": 2,
        # No area fill -- just the line and the point markers.
        "points": {"show": True, "size": 5},
    }
    if prepared["shape"] == "hv":
        series_line["paths"] = _RawJS("uPlot.paths.stepped({ align: 1 })")
    elif prepared["shape"] == "vh":
        series_line["paths"] = _RawJS("uPlot.paths.stepped({ align: -1 })")

    # The x range is emitted as a *function* rather than a static array. A
    # static array would pin the scale, and for the x/time scale uPlot also
    # re-invokes the range function on drag-zoom -- so a function that always
    # returned the configured range would snap x straight back to full and
    # silently break horizontal zoom (y still works, since its range function
    # is not re-invoked during a drag).
    #
    # The `noZoom` guard fixes this: only
    # substitute the configured range when uPlot is auto-ranging to the full
    # data extent (initial render + double-click reset); otherwise echo the
    # incoming min/max so the dragged zoom range is respected.
    x_scale = {"time": True}
    if prepared["x_range"] is not None:
        x_scale["range"] = _RawJS(
            "(u, dMin, dMax) => {\n"
            "  const xd = u.data[0];\n"
            "  if (xd && xd.length > 0) {\n"
            "    const xMin = xd[0], xMax = xd[xd.length - 1];\n"
            "    const noZoom = xd.length > 1\n"
            "      ? (dMin === xMin && dMax === xMax)\n"
            "      : (dMin === xMin);\n"
            "    if (noZoom) return " + json.dumps(prepared["x_range"]) + ";\n"
            "  }\n"
            "  return [dMin, dMax];\n"
            "}"
        )

    opts = {
        "tzDate": _tz_date_fn(),
        "cursor": {
            # Drag a box to zoom both axes; double-click resets to the
            # configured range. Shift+drag pans (see `_pan_plugin`).
            "drag": {"x": True, "y": True},
            "focus": {"prox": 20},
            "points": {"size": 10},
        },
        "plugins": [_pan_plugin()],
        "series": [
            {"label": prepared["x_label"], "value": _fmt_value_fn(loc_js)},
            series_line,
        ],
        "axes": [
            {"grid": {"stroke": "#eee"}, "values": _fmt_ticks_fn(loc_js)},
            {"grid": {"stroke": "#eee"}, "label": prepared["ytitle"]},
        ],
        "scales": {
            "x": x_scale,
            "y": {"range": _RawJS("(u, dMin, dMax) => " + json.dumps(prepared["y_range"]))},
        },
    }

    data = [prepared["timestamps"], prepared["values"]]
    return data, opts


def timeseries_to_uplot_html(
    series: pd.Series,
    ymin: float | None = None,
    ymax: float | None = None,
    color: str = "ki.green",
    ylabel: str | None = None,
    xmin: str | None = None,
    xmax: str | None = None,
    connection_type: str = "linear",
    locale: str | None = None,
    target_timezone: str | None = None,
    as_base64: bool = False,
) -> str:
    """
    Prepare `series`, compute the full `(data, opts)` in Python, and render
    it as an interactive µplot timeseries chart HTML fragment.
    """
    prepared = prepare_timeseries(
        series,
        ymin=ymin,
        ymax=ymax,
        xmin=xmin,
        xmax=xmax,
        ylabel=ylabel,
        color=color,
        connection_type=connection_type,
        locale=locale,
        target_timezone=target_timezone,
    )

    data, opts = timeseries_to_uplot_opts(prepared)

    return render_uplot_html(
        data=data,
        opts=opts,
        subtitle=prepared["tz_label"],
        as_base64=as_base64,
    )


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "timeseries": {"data_type": "SERIES"},
        "ymin": {"data_type": "FLOAT", "default_value": None},
        "ymax": {"data_type": "FLOAT", "default_value": None},
        "color": {"data_type": "STRING", "default_value": "ki.green"},
        "ylabel": {"data_type": "STRING", "default_value": None},
        "xmin": {"data_type": "STRING", "default_value": None},
        "xmax": {"data_type": "STRING", "default_value": None},
        "connection_type": {"data_type": "STRING", "default_value": "linear"},
        "locale": {"data_type": "STRING", "default_value": None},
        "target_timezone": {"data_type": "STRING", "default_value": None},
    },
    "outputs": {
        "uplot": {"data_type": "ANY"},
    },
    "name": "µplot Single Timeseries Plot",
    "category": "Visualization",
    "description": "Plot single timeseries using µplot",
    "version_tag": "0.1.0",
    "id": "4cbc35fd-4fe7-4680-a1d7-13fa4ce78ee3",
    "revision_group_id": "e31e90b1-1baa-4f8b-b3c7-c93ab5620ef9",
    "state": "RELEASED",
    "released_timestamp": "2026-07-24T11:51:49.656508+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(
    *,
    timeseries,
    ymin=None,
    ymax=None,
    color="ki.green",
    ylabel=None,
    xmin=None,
    xmax=None,
    connection_type="linear",
    locale=None,
    target_timezone=None,
):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    return {
        "uplot": {
            "content_type": "text/html",
            "encoding": "plain",
            "name": "HTML Output via ANY",
            "data": timeseries_to_uplot_html(
                timeseries,
                ymin=ymin,
                ymax=ymax,
                color=color,
                ylabel=ylabel,
                xmin=xmin,
                xmax=xmax,
                connection_type=connection_type,
                locale=locale,
                target_timezone=target_timezone,
            ),
        }
    }


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "timeseries",
            "filters": {
                "value": '{\n  "__hd_wrapped_data_object__": "SERIES",\n  "__metadata__": {},\n  "__data__": {\n    "name": null,\n    "index": [\n      "2026-07-23T00:42:03.454Z",\n      "2026-07-23T00:47:03.454Z",\n      "2026-07-23T00:52:03.454Z",\n      "2026-07-23T00:57:03.454Z",\n      "2026-07-23T01:02:03.454Z",\n      "2026-07-23T01:07:03.454Z",\n      "2026-07-23T01:12:03.454Z",\n      "2026-07-23T01:17:03.454Z",\n      "2026-07-23T01:22:03.454Z",\n      "2026-07-23T01:27:03.454Z",\n      "2026-07-23T01:32:03.454Z",\n      "2026-07-23T01:37:03.454Z",\n      "2026-07-23T01:42:03.454Z",\n      "2026-07-23T01:47:03.454Z",\n      "2026-07-23T01:52:03.454Z",\n      "2026-07-23T01:57:03.454Z",\n      "2026-07-23T02:02:03.454Z",\n      "2026-07-23T02:07:03.454Z",\n      "2026-07-23T02:12:03.454Z",\n      "2026-07-23T02:17:03.454Z",\n      "2026-07-23T02:22:03.454Z",\n      "2026-07-23T02:27:03.454Z",\n      "2026-07-23T02:32:03.454Z",\n      "2026-07-23T02:37:03.454Z",\n      "2026-07-23T02:42:03.454Z",\n      "2026-07-23T02:47:03.454Z",\n      "2026-07-23T02:52:03.454Z",\n      "2026-07-23T02:57:03.454Z",\n      "2026-07-23T03:02:03.454Z",\n      "2026-07-23T03:07:03.454Z",\n      "2026-07-23T03:12:03.454Z",\n      "2026-07-23T03:17:03.454Z",\n      "2026-07-23T03:22:03.454Z",\n      "2026-07-23T03:27:03.454Z",\n      "2026-07-23T03:32:03.454Z",\n      "2026-07-23T03:37:03.454Z",\n      "2026-07-23T03:42:03.454Z",\n      "2026-07-23T03:47:03.454Z",\n      "2026-07-23T03:52:03.454Z",\n      "2026-07-23T03:57:03.454Z",\n      "2026-07-23T04:02:03.454Z",\n      "2026-07-23T04:07:03.454Z",\n      "2026-07-23T04:12:03.454Z",\n      "2026-07-23T04:17:03.454Z",\n      "2026-07-23T04:22:03.454Z",\n      "2026-07-23T04:27:03.454Z",\n      "2026-07-23T04:32:03.454Z",\n      "2026-07-23T04:37:03.454Z",\n      "2026-07-23T04:42:03.454Z",\n      "2026-07-23T04:47:03.454Z",\n      "2026-07-23T04:52:03.454Z",\n      "2026-07-23T04:57:03.454Z",\n      "2026-07-23T05:02:03.454Z",\n      "2026-07-23T05:07:03.454Z",\n      "2026-07-23T05:12:03.454Z",\n      "2026-07-23T05:17:03.454Z",\n      "2026-07-23T05:22:03.454Z",\n      "2026-07-23T05:27:03.454Z",\n      "2026-07-23T05:32:03.454Z",\n      "2026-07-23T05:37:03.454Z",\n      "2026-07-23T05:42:03.454Z",\n      "2026-07-23T05:47:03.454Z",\n      "2026-07-23T05:52:03.454Z",\n      "2026-07-23T05:57:03.454Z",\n      "2026-07-23T06:02:03.454Z",\n      "2026-07-23T06:07:03.454Z",\n      "2026-07-23T06:12:03.454Z",\n      "2026-07-23T06:17:03.454Z",\n      "2026-07-23T06:22:03.454Z",\n      "2026-07-23T06:27:03.454Z",\n      "2026-07-23T06:32:03.454Z",\n      "2026-07-23T06:37:03.454Z",\n      "2026-07-23T06:42:03.454Z"\n    ],\n    "data": [\n      -2.4110490856,\n      -0.6549153908,\n      -1.1956612321,\n      1.4371909984,\n      -0.4570426426,\n      -0.266353686,\n      0.3989487972,\n      -0.3438513526,\n      -0.0111706868,\n      -0.0868797783,\n      -1.2496902779,\n      0.4954656696,\n      1.4844599387,\n      0.0216377396,\n      -1.1152907097,\n      1.1749295919,\n      1.0373893008,\n      -0.7191808411,\n      1.4248002898,\n      2.5704843505,\n      -0.116181337,\n      1.1147577506,\n      -0.9565145796,\n      0.7270204054,\n      0.4173485247,\n      1.6683760253,\n      2.8066699557,\n      0.7712565273,\n      -0.2569799169,\n      -3.266353634,\n      0.6531402163,\n      -0.06264541,\n      0.5435563939,\n      -0.6301922899,\n      -0.3130956781,\n      0.9730891295,\n      0.4035179993,\n      0.6904832958,\n      -1.6433051388,\n      0.738486514,\n      0.7919850272,\n      0.1927885918,\n      0.1597425806,\n      -0.9678252087,\n      -1.6006660108,\n      0.1235265721,\n      0.1539180231,\n      -0.6023550094,\n      0.534154408,\n      2.3378542259,\n      -0.9199385114,\n      -0.0035827751,\n      -0.9757067743,\n      1.0722635518,\n      0.7157736705,\n      0.158058978,\n      -0.8710953177,\n      -0.0268320325,\n      -0.9800714474,\n      0.7679251027,\n      2.1335045627,\n      -0.7234078128,\n      0.2200576041,\n      -0.1779155327,\n      0.3549714988,\n      0.0405257028,\n      -0.268844384,\n      -0.1269642055,\n      0.927103535,\n      0.7214450798,\n      -0.9299464642,\n      1.0138295007,\n      0.3795185422\n    ]\n  },\n  "__data_parsing_options__": {\n    "orient": "split"\n  }\n}'
            },
        },
        {
            "workflow_input_name": "ymin",
            "use_default_value": True,
            "filters": {"value": ""},
        },
        {
            "workflow_input_name": "ymax",
            "use_default_value": True,
            "filters": {"value": ""},
        },
        {"workflow_input_name": "color", "filters": {"value": "ki.tech"}},
        {
            "workflow_input_name": "ylabel",
            "use_default_value": True,
            "filters": {"value": ""},
        },
        {
            "workflow_input_name": "xmin",
            "use_default_value": True,
            "filters": {"value": ""},
        },
        {
            "workflow_input_name": "xmax",
            "use_default_value": True,
            "filters": {"value": ""},
        },
        {
            "workflow_input_name": "connection_type",
            "use_default_value": True,
            "filters": {"value": "linear"},
        },
        {
            "workflow_input_name": "locale",
            "use_default_value": True,
            "filters": {"value": ""},
        },
        {
            "workflow_input_name": "target_timezone",
            "use_default_value": True,
            "filters": {"value": ""},
        },
    ]
}
RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "timeseries",
            "filters": {
                "value": '{\n  "__hd_wrapped_data_object__": "SERIES",\n  "__metadata__": {},\n  "__data__": {\n    "name": null,\n    "index": [\n      "2026-07-23T00:42:03.454Z",\n      "2026-07-23T00:47:03.454Z",\n      "2026-07-23T00:52:03.454Z",\n      "2026-07-23T00:57:03.454Z",\n      "2026-07-23T01:02:03.454Z",\n      "2026-07-23T01:07:03.454Z",\n      "2026-07-23T01:12:03.454Z",\n      "2026-07-23T01:17:03.454Z",\n      "2026-07-23T01:22:03.454Z",\n      "2026-07-23T01:27:03.454Z",\n      "2026-07-23T01:32:03.454Z",\n      "2026-07-23T01:37:03.454Z",\n      "2026-07-23T01:42:03.454Z",\n      "2026-07-23T01:47:03.454Z",\n      "2026-07-23T01:52:03.454Z",\n      "2026-07-23T01:57:03.454Z",\n      "2026-07-23T02:02:03.454Z",\n      "2026-07-23T02:07:03.454Z",\n      "2026-07-23T02:12:03.454Z",\n      "2026-07-23T02:17:03.454Z",\n      "2026-07-23T02:22:03.454Z",\n      "2026-07-23T02:27:03.454Z",\n      "2026-07-23T02:32:03.454Z",\n      "2026-07-23T02:37:03.454Z",\n      "2026-07-23T02:42:03.454Z",\n      "2026-07-23T02:47:03.454Z",\n      "2026-07-23T02:52:03.454Z",\n      "2026-07-23T02:57:03.454Z",\n      "2026-07-23T03:02:03.454Z",\n      "2026-07-23T03:07:03.454Z",\n      "2026-07-23T03:12:03.454Z",\n      "2026-07-23T03:17:03.454Z",\n      "2026-07-23T03:22:03.454Z",\n      "2026-07-23T03:27:03.454Z",\n      "2026-07-23T03:32:03.454Z",\n      "2026-07-23T03:37:03.454Z",\n      "2026-07-23T03:42:03.454Z",\n      "2026-07-23T03:47:03.454Z",\n      "2026-07-23T03:52:03.454Z",\n      "2026-07-23T03:57:03.454Z",\n      "2026-07-23T04:02:03.454Z",\n      "2026-07-23T04:07:03.454Z",\n      "2026-07-23T04:12:03.454Z",\n      "2026-07-23T04:17:03.454Z",\n      "2026-07-23T04:22:03.454Z",\n      "2026-07-23T04:27:03.454Z",\n      "2026-07-23T04:32:03.454Z",\n      "2026-07-23T04:37:03.454Z",\n      "2026-07-23T04:42:03.454Z",\n      "2026-07-23T04:47:03.454Z",\n      "2026-07-23T04:52:03.454Z",\n      "2026-07-23T04:57:03.454Z",\n      "2026-07-23T05:02:03.454Z",\n      "2026-07-23T05:07:03.454Z",\n      "2026-07-23T05:12:03.454Z",\n      "2026-07-23T05:17:03.454Z",\n      "2026-07-23T05:22:03.454Z",\n      "2026-07-23T05:27:03.454Z",\n      "2026-07-23T05:32:03.454Z",\n      "2026-07-23T05:37:03.454Z",\n      "2026-07-23T05:42:03.454Z",\n      "2026-07-23T05:47:03.454Z",\n      "2026-07-23T05:52:03.454Z",\n      "2026-07-23T05:57:03.454Z",\n      "2026-07-23T06:02:03.454Z",\n      "2026-07-23T06:07:03.454Z",\n      "2026-07-23T06:12:03.454Z",\n      "2026-07-23T06:17:03.454Z",\n      "2026-07-23T06:22:03.454Z",\n      "2026-07-23T06:27:03.454Z",\n      "2026-07-23T06:32:03.454Z",\n      "2026-07-23T06:37:03.454Z",\n      "2026-07-23T06:42:03.454Z"\n    ],\n    "data": [\n      -2.4110490856,\n      -0.6549153908,\n      -1.1956612321,\n      1.4371909984,\n      -0.4570426426,\n      -0.266353686,\n      0.3989487972,\n      -0.3438513526,\n      -0.0111706868,\n      -0.0868797783,\n      -1.2496902779,\n      0.4954656696,\n      1.4844599387,\n      0.0216377396,\n      -1.1152907097,\n      1.1749295919,\n      1.0373893008,\n      -0.7191808411,\n      1.4248002898,\n      2.5704843505,\n      -0.116181337,\n      1.1147577506,\n      -0.9565145796,\n      0.7270204054,\n      0.4173485247,\n      1.6683760253,\n      2.8066699557,\n      0.7712565273,\n      -0.2569799169,\n      -3.266353634,\n      0.6531402163,\n      -0.06264541,\n      0.5435563939,\n      -0.6301922899,\n      -0.3130956781,\n      0.9730891295,\n      0.4035179993,\n      0.6904832958,\n      -1.6433051388,\n      0.738486514,\n      0.7919850272,\n      0.1927885918,\n      0.1597425806,\n      -0.9678252087,\n      -1.6006660108,\n      0.1235265721,\n      0.1539180231,\n      -0.6023550094,\n      0.534154408,\n      2.3378542259,\n      -0.9199385114,\n      -0.0035827751,\n      -0.9757067743,\n      1.0722635518,\n      0.7157736705,\n      0.158058978,\n      -0.8710953177,\n      -0.0268320325,\n      -0.9800714474,\n      0.7679251027,\n      2.1335045627,\n      -0.7234078128,\n      0.2200576041,\n      -0.1779155327,\n      0.3549714988,\n      0.0405257028,\n      -0.268844384,\n      -0.1269642055,\n      0.927103535,\n      0.7214450798,\n      -0.9299464642,\n      1.0138295007,\n      0.3795185422\n    ]\n  },\n  "__data_parsing_options__": {\n    "orient": "split"\n  }\n}'
            },
        },
        {
            "workflow_input_name": "ymin",
            "use_default_value": True,
            "filters": {"value": ""},
        },
        {
            "workflow_input_name": "ymax",
            "use_default_value": True,
            "filters": {"value": ""},
        },
        {"workflow_input_name": "color", "filters": {"value": "ki.tech"}},
        {
            "workflow_input_name": "ylabel",
            "use_default_value": True,
            "filters": {"value": ""},
        },
        {
            "workflow_input_name": "xmin",
            "use_default_value": True,
            "filters": {"value": ""},
        },
        {
            "workflow_input_name": "xmax",
            "use_default_value": True,
            "filters": {"value": ""},
        },
        {
            "workflow_input_name": "connection_type",
            "use_default_value": True,
            "filters": {"value": "linear"},
        },
        {
            "workflow_input_name": "locale",
            "use_default_value": True,
            "filters": {"value": ""},
        },
        {
            "workflow_input_name": "target_timezone",
            "use_default_value": True,
            "filters": {"value": ""},
        },
    ]
}
