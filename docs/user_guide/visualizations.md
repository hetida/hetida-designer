# Visualizations / Plots

hetida designer supports visualizations and plots via

* Plotly (PLOTLYJSON type)
* arbitrary HTML and images via the [ANY type](./data_types/any.md).

## Plotly

Via the PLOTLYJSON type for transformation outputs Plotly figures can be used for visualizing data. The test execution result view and the [experimental dashboarding](./dashboarding.md) render such plots directly.

To develop your own custom plot components we recommend to start with one of the existing plot base components like "Single Timeseries Plot" from the "Visualization" category and make a copy of it. The code of "Single Timeseries Plot" in particular explains how to take into account target timezone and locale information provided by an external system as context to the execution.

Plotly plot generation can be turned off in automated production execution via the [run_pure_plot_operators](../integration_guide/trafo_exec_guide/execution_via_api.md#optional-parameters) flag by the caller. This disables execution of operators with just plot output(s).

## ANY type for arbitrary html

Via [ANY type](./data_types/any.md) outputs you can provide arbitrary HTML output that is then rerendered by the test execution result view and the [experimental dashboarding](./dashboarding.md). An example is

```json
{
  "content_type": "text/html",
  "encoding": "plain",
  "name": "HTML Output via ANY",
  "data": "<h2>HTML example</h2><br>So<b>me</b><br>HTML"
}
```

See the [ANY type documentation](./data_types/any.md) for the correct json structure that must be provided for this feature.

This allows to write components that use pure javascript visualization libraries like apache echarts or µplot.

### µplot component example
Here an example component for a µplot timeseries plot. The output is of type ANY and suffices the structure mentioned above.

```python
import pandas as pd
import json
import uuid
import base64


def timeseries_to_uplot_html(series: pd.Series, as_base64: bool = False) -> str:
    if not isinstance(series, pd.Series):
        raise TypeError("series must be a pandas Series")

    s = series.dropna().copy()

    if not isinstance(s.index, pd.DatetimeIndex):
        s.index = pd.to_datetime(s.index)

    if s.index.tz is not None:
        s.index = s.index.tz_convert("UTC")

    # Pass ISO 8601 strings -- sidesteps datetime64 resolution (s/ms/us/ns)
    # issues entirely. Conversion to epoch seconds for µplot happens in JS below.
    timestamps_iso = s.index.strftime("%Y-%m-%dT%H:%M:%S.%fZ").tolist()
    values = s.astype(float).tolist()

    label = series.name if series.name else "Value"
    div_id = f"uplot-{uuid.uuid4().hex[:8]}"

    timestamps_json = json.dumps(timestamps_iso)
    values_json = json.dumps(values)

    html = f"""<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/uplot@1.6.31/dist/uPlot.min.css">
    
    <html lang="en" style="width: 100%; height: 100%"><head>
        <meta charset="utf-8">
    </head>
<script src="https://cdn.jsdelivr.net/npm/uplot@1.6.31/dist/uPlot.iife.min.js"></script>
<style>
  #{div_id}-wrap {{
    width: 100%;
    height: 100%;
    overflow: hidden;
  }}
  #{div_id}-wrap .u-legend {{
    font-size: 11px;
  }}
</style>

<div id="{div_id}-wrap">
  <div id="{div_id}"></div>
</div>

<script>
(function() {{
  const timestampsIso = {timestamps_json};
  const values = {values_json};

  // Convert ISO strings -> Unix seconds here, right before uPlot needs them.
  const timestamps = timestampsIso.map(t => Math.floor(new Date(t).getTime() / 1000));
  const data = [timestamps, values];

  const wrap = document.getElementById("{div_id}-wrap");
  const el = document.getElementById("{div_id}");

  let curW = wrap.clientWidth;
  let curH = wrap.clientHeight;

  const opts = {{
    width: curW,
    height: curH,
    series: [
      {{ label: "Time" }},
      {{
        label: "{label}",
        stroke: "#2563eb",
        width: 2,
        fill: "rgba(37, 99, 235, 0.08)",
      }}
    ],
    axes: [
      {{}},
      {{ grid: {{ stroke: "#eee" }} }}
    ],
    scales: {{
      x: {{ time: true }}
    }}
  }};

  const u = new uPlot(opts, data, el);

  function fitToContainer() {{
    const totalW = wrap.clientWidth;
    const totalH = wrap.clientHeight;
    if (totalW <= 0 || totalH <= 0) return;

    const chartH = Math.max(10, totalH - 50);

    if (totalW !== curW || chartH !== curH) {{
      curW = totalW;
      curH = chartH;
      u.setSize({{ width: totalW, height: chartH }});
    }}
  }}

  fitToContainer();

  const ro = new ResizeObserver(() => fitToContainer());
  ro.observe(wrap);
}})();
</script>
"""

    if as_base64:
        return base64.b64encode(html.encode("utf-8")).decode("ascii")

    return html


# %%
# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "timeseries": {"data_type": "SERIES"},
    },
    "outputs": {
        "uplot": {"data_type": "ANY"},
    },
    "name": "µplot Single Timeseries Plot",
    "category": "Visualization",
    "description": "Plot timeseries using µplot",
    "version_tag": "0.1.0",
    "id": "4cbc35fd-4fe7-4680-a1d7-13fa4ce78ee3",
    "revision_group_id": "e31e90b1-1baa-4f8b-b3c7-c93ab5620ef9",
    "state": "DRAFT",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, timeseries):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    # write your function code here.
    return {
        "uplot": {
            "content_type": "text/html",
            "encoding": "plain",
            "name": "HTML Output via ANY",            
            "data": timeseries_to_uplot_html(timeseries)
        }
    } 

```
