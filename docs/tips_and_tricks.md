# Tips and Tricks

## General notes on debugging
Since hetida designer is a web application, it is not possible to read the print function output in the user interface directly. Because of that print cannot be used for debugging. Similarly, setting breakpoints will not work as there is no direct access to a terminal where the code actually runs.

If you depend on print and breakpoints you can of course first write / develop component code in your preferred IDE (or Jupyter notebooks), test and debug it there and afterwards copy-paste the relevant functions into component code. We, the creators of hetida designer, use this approach ourselves all the time. Indeed, we often extract, refactor and generalize the relevant parts of an analysis from Jupyter notebooks into "polished" designer components. See [Sync and hybrid working](./sync.md) for a way to simplify this style of development.

In the designer user interface both components as well as workflow revisions can be executed with the test wiring already in the DRAFT state to test if they perform as expected.

Here you can find some guidance for common issues that might occur:

- [Debugging component revisions](#debugging-components)
- [Debugging workflow revisions](#debugging-workflows)
- [Specify data type to enable correct parsing](#data-type-parsing)
- [Storing and loading objects with self defined classes](#self-defined-classes)
- [Identifiy source for latest stored object via endpoints](#identify-source)

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

<img src="./assets/workflow_without_debugging.png" height="250" width=1090>
<img src="./assets/workflow_debugging.png" height="250" width=1090>

## <a name="data-type-parsing"></a> Explicitely specify data type to enable correct parsing

The data wired to a workflow is parsed and converted to the workflow input data type before execution by the runtime. For example json data provided to a workflow input of type SERIES will be parsed into a Pandas.Series object.

One caveat of this behaviour is, that if the input is of type ANY the data will be just parsed only into a json object.

If a component like "Add" uses ANY to allow e.g. both Series and DataFrames to be send to it and indeed expects one of these two options, it probably will error if provided with json input directly from the outside.

E.g. A series provided as a json to a workflow input of type ANY will result in a dictionary instead of a Pandas Series object. This will cause an error message which starts e.g. (for the "Add" component) like

```
{
	"error": "Exception during Component execution of component instance Add (operator hierarchical id: :1e969104-6ef1-4c45-a9d9-a9e0d5c9fceb):
unsupported operand type(s) for +: 'dict' and 'dict'",
...
```

This can be avoided by putting a "Pass through (Series)" component in front of it, so that the input data type is changed and thus explicit:

<img src="./assets/parsing_any.png" height="160" width=485 data-align="center">
<img src="./assets/parsing_series.png" height="140" width=730>

So the general tip is to avoid ANY as input that needs to be wired and instead to put the respective Pass Through component in front.

## <a name="self-defined-classes"></a> Storing and loading objects with self defined classes
When combining self-defined classes with storing and loading objects, e.g. via the [Blob Storage Adapter](./adapter_system/blob_storage_adapter.md), the classes must be defined in seperate components.
The component that contains such a class, should just return the class as i.e. in the component "ExampleClass" from the category "Classes".
```python

class ExampleClass:
    ...
return {"class _object": ExampleClass}
```
A component in which an instance of this class is created should take this class as an input.
For better readability it is recommended to name the input just as the class, but it may as well be named differently.
```python
...
def main(*, ExampleClass, ...)
	...
	example_class_object = ExampleClass(...)
	...
```
When loading the stored object in a worklfow the exactly same component must be contained in this workflow to ensure that the class is imported correctly.

<img src="./assets/store_object_with_class.png" height="150" width=750 data-align="center">

Usually the class is not needed explicitly so that the there is no reason to link the component with the class definition to any input, instead it can be linked to the component "Forget" from the category "Connectors".

<img src="./assets/load_object_with_class.png" height="225" width=750 data-align="center">


## <a name="self-defined-classes"></a> Identifiy source for latest stored object via endpoints
The [Blob Storage Adapter](./adapter_system/blob_storage_adapter.md) adds the storage timestamp and the execution job id to the name of each stored object and automatically creates a new source corresponding to that object.

A request to the [/structure endpoint (GET)](./adapter_system/generic_rest_adapters/web_service_interface.md#structure-endpoint-get) with the `ref_id` as `parentId` path parameter will return a list of all thing nodes, sources and sinks below the thingnode with the id `parentId` as a response.
```json
{
	"id": "planta-picklingunit/Influx/Anomalies_2023-02-14T12:19:38+00:00_94726ca0-9b4d-4b72-97be-d3ef085e16fa.pkl",
	"thingNodeId": "planta-picklingunit/Influx/Anomalies",
	"name": "Anomalies - 2023-02-14 12:19:38+00:00 - 94726ca0-9b4d-4b72-97be-d3ef085e16fa (pkl)",
	"path": "planta-picklingunit/Influx/Anomalies",
	"metadataKey": "Anomalies - 2023-02-14 12:19:38+00:00 - 94726ca0-9b4d-4b72-97be-d3ef085e16fa (pkl)"
}
```

The attributes `ref_id` and `ref_key` of the corresponding input wiring must be set to the values of the attributes `thingNodeId` and `metadataKey` of this source, respectively.
```json
{
	"adapter_id": "blob-storage-adapter",
	"filters": {},
	"ref_id": "planta-picklingunit/Influx/Anomalies",
	"ref_id_type": "THINGNODE",
	"ref_key": "Anomalies - 2023-02-14 12:19:38+00:00 - 94726ca0-9b4d-4b72-97be-d3ef085e16fa (pkl)",
	"type": "metadata(any)",
	"workflow_input_name": "example_class_object"
}
```

## <a name="data-type-parsing"></a> Pandas objects in hetida workflows and components

### Handling of index during DataFrame serialisation

When your workflow or component has a pandas.DataFrame as a DATAFRAME output and is run directly, serialization will assume that the index is unique. If this is not the case you will get a `ValueError` stating "DataFrame index must be unique for orient='columns'."

Moreover it is not guaranteed that the index itself is included. In fact this depends on the handling of the sink / adapter to which this output is wired for execution.

Therefore we recommend
* to assume that all relevant information of ingoing DataFrames is in columns and not in the index. E.g. timestamps should be expected in an explicit "timestamp" column and not in the index.
* to finally prepare a result DataFrame to contain all relevant information in explicit columns and not in the index. E.g. add the DateTimeIndex as explicit column "timestamp"
* to reindex it with a unique index prior to outputting it finally.

E.g. the last two steps can be achieved via

```python
dataframe_to_return = dataframe.reset_index(
    names="new_time_column", drop=False, inplace=False
)
```

**Notes**:
* For pd.Series duplicate index entries are no issue since for them serialization is handled differently.
* In-between operators of a workflow, DataFrame objects are transferred as they are, without intermediate serialization. So components working and expecting a index of a certain kind and form do make sense!

### pd.Series names
Adapters may provide pd.Series objects to SERIES inputs either with a name or without.

You should ensure that your code works with both versions, to be independant of the adapter / source used with your workflow.

Note that an explicit "Name Series" component is available in the base component set.

E.g. if you want to convert a pd.Series into a single-column pd.DataFrame we recommend doing the following:

```python
dataframe = series.to_frame(name="new_column_name")
```
