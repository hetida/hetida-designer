# Skipping Unneeded Outputs

Whether an operator is run during an execution depends on its outputs:

* **Pure plot operators**, i.e. operators with at least one output and only plot (PLOTLYJSON) outputs, are not run
    * if the execution does not run pure plot operators (see next section) or
    * if all of their outputs are discarded (see [below](#when-is-an-output-discarded)), e.g. because they are wired to the [drop adapter](../../integration_guide/adapter_system/builtin_adapters/drop_result_adapter.md). The operators providing their inputs are run anyway.
* **All other operators** are always run and compute all of their outputs, even if the value of an output is not used, e.g. because it is wired to the drop adapter. This includes operators without outputs.

Components providing a plot together with other outputs **can** check in their code whether the plot is needed and skip creating it, as described below. Then the same component can be used for interactive analysis with the plot and for automated executions which only need the data. The same way, components can skip expensive computations for other outputs which are not needed.

Each output of the executed workflow or component can always be made unneeded explicitly by wiring it to the drop adapter.


## Executions with and without plots

Whether pure plot operators are generally run is set by `run_pure_plot_operators` of the execution request. Its value depends on how the execution is started:

| Execution | `run_pure_plot_operators` |
| --- | --- |
| hetida designer user interface | true |
| [Schedules](../scheduling.md) and [experimental dashboards](../dashboarding.md) | true |
| [Web service endpoints](../../integration_guide/trafo_exec_guide/execution_via_api.md#optional-parameters), [execution via Kafka](../../integration_guide/trafo_exec_guide/execution_via_kafka.md) and [Kafka consumption mode](../../integration_guide/trafo_exec_guide/kafka_consumption_mode.md) | false by default, can be set by the caller |

So by default plots are created when working interactively, but not when other systems execute transformations (which typically is not interactive usage).

## Plot outputs

Use `plot_output_needed` from `hdutils` and return an empty dictionary if no plot is needed:

```python
from hdutils import plot_output_needed

...

def main(*, series):
    ...
    return {
        "cleaned_series": cleaned_series,
        "plot": create_plot(cleaned_series) if plot_output_needed("plot") else {},
    }
```

`plot_output_needed("plot")` is false if

* the execution does not run plot operators (`run_pure_plot_operators` is false) or
* the output is discarded (see [below](#when-is-an-output-discarded)), e.g. because it is wired to the drop adapter.

The latter allows to avoid plot creation also in executions which run pure plot operators, e.g. schedules. Since plot outputs are practically never linked to other operators' inputs, wiring a plot output to the drop adapter is enough to avoid creating it.

If `hetdesrun` is not available, e.g. when running the component code outside of hetida designer, plots are always considered needed.

## Other outputs / expensive computations

In component code you can use `output_is_discarded` from `hetdesrun.runtime.context` for outputs of other types to skip expensive computations whose results nobody gets. An output linked to another operator's input never counts as discarded.

Since outputs are always nullable, you can return `None` instead:

```python
from hetdesrun.runtime.context import output_is_discarded

...

def main(*, dataframe):
    ...
    statistics = None if output_is_discarded("statistics") else compute_statistics(dataframe)
    return {"result": result, "statistics": statistics}
```

For plot outputs use `plot_output_needed` instead, since `output_is_discarded` does not take `run_pure_plot_operators` into account.

## When is an output discarded?

An output of a component is discarded during an execution if its value is not used anywhere:

* it is not linked to an input of another operator and
* every workflow output it is exposed as is wired to the drop adapter or, if `run_pure_plot_operators` is false, to the [plot adapter](../../integration_guide/adapter_system/builtin_adapters/plot_adapter.md), which then provides empty plots.

This also holds if the component is used in nested workflows: The runtime follows the output through all workflow levels to the outputs of the executed workflow and their wiring.

Note that

* a link to another operator always counts as usage, even if the other operator does not use the value (e.g. in its component code),
* no output is discarded if the execution requests the results of all individual operators (`return_individual_node_results`),
* the output name must be spelled exactly as in the component's outputs. Otherwise the output is never considered discarded, i.e. the computation just is not skipped.

## Wirings

For a component with a plot and a data output,

* automated executions should wire the data output to the respective sink and the **plot output to the drop adapter**,
* interactive analysis in the hetida designer user interface typically needs only the plot: Wire the **data output to the drop adapter** and keep the plot output at *Only Output* (direct provisioning). It is recommended to use this as test and release wiring of such a component.

## Unit tests

Outside of an execution, e.g. in [unit tests](./unit_testing.md) of the component, no output is discarded and plot operators are run. To test the behavior, set the respective context:

```python
def test_plot_is_not_created_if_discarded():
    from hetdesrun.runtime.context import discarded_outputs_context

    with discarded_outputs_context(frozenset({"plot"})):
        result = main(series=example_series())
    assert result["plot"] == {}


def test_plot_is_not_created_if_plot_operators_are_not_run():
    from hetdesrun.models.run import ConfigurationInput
    from hetdesrun.runtime.configuration import execution_config

    token = execution_config.set(ConfigurationInput(run_pure_plot_operators=False))
    try:
        result = main(series=example_series())
    finally:
        execution_config.reset(token)
    assert result["plot"] == {}
```
