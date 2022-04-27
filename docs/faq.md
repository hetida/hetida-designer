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

To understand why and how an error occured it is often necessary to understand which value a variable has at certain steps of running the code.
One way to achieve this in components is to temporarily add a line that raises an exception like a `ValueError` and pass the the variable converted to a string as error message to the ValueError object. Example:

```
...
vols = diffs.abs().rolling(freq).sum() - diffs.rolling(freq).sum().abs()

raise ValueError(str(vols))
...
```

The first lines of the resulting error message will then e.g. look like:

```
{
	"error": "Exception during Component execution of component instance Simple Volatility Score (operator hierarchical id: :3ca9b6cc-593f-4780-afcf-a44676494be0):
2020-01-01 01:15:27+00:00     NaN
2020-01-03 08:20:03+00:00     0.0
2020-01-03 08:20:04+00:00    14.4
Name: volatilities, dtype: float64",
...
```

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
