# Drop Result Adapter

A built-in adapter that only can be wired to outputs: It simply drops/swallows the result, i.e. does not send it anywhere and does not return it in the execution response (in contrast to selecting Only Output, i.e. the [direct provisioning](./manual_input.md) adapter).

![selecting drop adapter](../assets/select_drop_adapter.png)

This is practical for components or workflows that provide a result that is not needed in all use cases. Or that provide the same result in two different ways, e.g. as a plot and as a SERIES: Interactively you may set the plot output to *Only Output* and the SERIES output to *Drop Result*. For automated background executions its probably vice versa.

Note that wiring an output to drop does not mean that the output value is not calculated: hetida designer execution is not lazy with respect to Drop. So dropping the result does not help avoiding resource- or time-intensive computations.