# Tips and Tricks

## General notes on debugging
Since hetida designer is a web application, it is not possible to read the print function output in the user interface directly. Because of that print cannot be used for debugging. Similarly, setting breakpoints will not work as there is no direct access to a terminal where the code actually runs. 

If you depend on print and breakpoints you can of course first write / develop component code in your preferred IDE (or Jupyter notebooks), test and debug it there and afterwards copy-paste the relevant functions into component code. We, the creators of hetida designer, use this approach ourselves all the time. Indeed, we often extract, refactor and generalize the relevant parts of an analysis from Jupyter notebooks into "polished" designer components.

In the designer user interface both components as well as workflow revisions can be executed with the test wiring already in the DRAFT state to test if they perform as expected.

Here you can find some guidance for common issues that might occur:

- [Debugging component revisions](#debugging-components)
- [Debugging workflow revisions](#debugging-workflows)
- [Specify data type to enable correct parsing](#data-type-parsing)

## <a name="debugging-components"></a> Debugging component revisions

To understand why and how an error occurred it is often necessary to understand which value a variable has at certain steps of running the code.
One way to achieve this in components is to temporarily add a line that raises an exception like a `ValueError` and pass the the variable converted to a string as error message to the ValueError object. Example:

```
...
raise ValueError(interesting_value)
...
```

The first lines of the resulting error message will then e.g. look like:

```
{
	"error": "Exception during execution!
              tr type: COMPONENT, tr id: f3d57870-7307-473c-a635-2e165aa8ac3b, tr name: Raise ValueError, tr tag: 1.0.0,
              op id(s): \\170c3d2a-c88f-4aba-9999-f2740d4abf25\\d2e7a4d4-08da-4e7e-b0e5-06276ae9b234\\,
              op name(s): \\Wrapper Workflow\\Raise ValueError\\
              reason: Unexpected error from user code",
	"output_results_by_output_name": {},
	"output_types_by_output_name": {
			"o": "ANY"
	},
	"result": "failure",
	"traceback": "Traceback (most recent call last):
	...
  File \"<string>\", line 28, in main
ValueError: 42
...
```

The last line shows the value of the variable `interesting_value`, normally an error message would be displayed there. The second to last line shows in which line of your component code the error occurred.

## <a name="debugging-workflows"></a> Debugging workflow revisions

If a workflow does not perform as expected or causes errors, additional information on intermediate variable values might be helpful.
You might want to copy your workflow to have a second version in which you can add and remove operators freely without compromising your actual workflow.
In case of errors you may remove the respective component(s) so that the reduced workflow can be executed and all outputs will be displayed.

In order to add an output for an intermediate variable, which is passed from an operator output to some other operators input, add a "Pass through" component with matching data type as operator.
These components are in the category "Connectors".
The output of the "Pass through" operator can be used, to set a new workflow output.

<img src="./faq/workflow_without_debugging.png" height="250" width=1090>
<img src="./faq/workflow_debugging.png" height="250" width=1090>

## <a name="data-type-parsing"></a> Explicitely specify data type to enable correct parsing

The data wired to a workflow is parsed and converted to the workflow input data type before execution by the runtime. For example json data provided to a workflow input of type SERIES will be parsed into a Pandas.Series object.

One caveat of this behaviour is, that if the input is of type ANY the data will be just parsed only into a json object.

If a component like "Add" uses ANY to allow e.g. both Series and DataFrames to be send to it and indeed expects one of these two options, it probably will error if provided with json input directly from the outside.

E.g. A series provided as a json provided to a workflow input of type ANY will result in a dictionary instead of a Pandas Series object. This will cause an error message which starts e.g. (for the "Add" component) like

```
{
	"error": "Exception during Component execution of component instance Add (operator hierarchical id: :1e969104-6ef1-4c45-a9d9-a9e0d5c9fceb):
unsupported operand type(s) for +: 'dict' and 'dict'",
...
```

This can be avoided by putting a "Pass through (Series)" component in front of it, so that the input data type is changed and thus explicit:

<img src="./faq/parsing_any.png" height="160" width=485>
<img src="./faq/parsing_series.png" height="140" width=730>

So the general tip is to avoid ANY as input that needs to be wired and instead to put the respective Pass Through component in front.
