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

The "µplot Single Timeseries Plot" base component demonstrates how one can integrate µplot to render high-volume timeseries data efficiently.
