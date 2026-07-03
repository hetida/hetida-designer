# Direct Provisioning

The builtin direct provisioning adapter handles data that is directly provided with the execution payload or returned with the execution response.

In particular this includes "manual input" selected in the hetida designer execution dialog for inputs as well as "Only Output" for outputs.

The direct provisioning adapter is always active and does not need any configuration. Its key is "direct_provisioning".

!!! tip "Unwired Outputs"
    Note that unwired outputs are automatically considered to be wired to the direct provisioning adapter, i.e. their result is returned together with the execution response.

## Direct provisioning Wirings
### Input Wiring

A direct provisioning input wiring just has to provide the value as JSON serialized string to the filter `value`:

```json
{
  "id": "...", // the id of the respective transformation revision
  "wiring": {
    "input_wirings": [
      {
        "adapter_id": "direct_provisioning",
        "workflow_input_name": "my_input",
        "filters": {
          "value": "<JSON STRING>"
        }
      }
    ]
  }
}
```

E.g. for an input of type INT it is `"filters": {"value": "42"}`. For more complex objects, proper escaping is required. The JSON formats for more complex objects of types like DATAFRAME etc. is described below under [manual input](#manual-input).

!!! warning
    Note that direct provisioning is not recommended for mass data due to (de)serialization overhead and often limited payload sizes. It is preferred for single value parameters, e.g. single float, int, bool or string values.

### Output Wiring

As mentioned above, hetida designer will always fall back to direct provisioning if no output wiring is present for an output. However, you can of course explicitely wire to direct provisioning as follows:

```json
{
  "id": "...", // the id of the respective transformation revision
  "wiring": {
    "output_wirings": [
      {
        "adapter_id": "direct_provisioning",
        "workflow_input_name": "my_output",
      }
    ]
  }
}
```

hetida designer will return data for outputs wired to the direct provisioning adapter as part of its response under the `output_values_by_output_name` field of the execution response in the form `{"output_name": JSON object}`

See the [API](../../api.md) documentation for the execution endpoints or [Execution via API](../../trafo_exec_guide/execution_via_api.md) for examples.

## Manual Input
When selecting "manual input" in the test execution dialog you have several options to insert and upload data directly without the need of a specific adapter.

For simple types (like STRING, FLOAT, INT) you can enter data directly in the input field. For SERIES, DATAFRAME, MULTITSFRAME or ANY inputs clicking on the input field opens an editor dialog where json-data can be entered (a template is provided in the input text field).

Note that for SERIES, DATAFRAME and MULTITSFRAME you can add metadata (which is attached to pandas `.attrs` attribute) by using the wrapped json format described [here](../../../user_guide/attached_metadata.md). This also allows to specifiy some json parsing options for these types and may be required, e.g. when you want to enter/send data with duplicate index entries.

This dialog additionally allows to import a json or csv file from disk via clicking on "Import JSON/CSV". For json files the required format agrees with the format for entering data into the dialogs editor. This format and the format required for CSVs is described below.

!!! warning
    Importing JSON/CSV files this way has restrictive limits on data size. Since the data is stored as json and send via Web Requests, importing larger files and trying to execute a workflow will soon run into either request size limits or timeouts (and frontend errors). It is recommended to use the [local file adapter](./local_file_adapter.md) for any file that is not very small.

### JSON Formats

#### SERIES JSON
##### Simple format
```json
{
    "2020-01-01T01:15:27.000Z": 42.2,
    "2020-01-03T08:20:03.000Z": 18.7,
    "2020-01-03T08:20:04.000Z": 25.9
}
```

i.e. index: value pairs.

Having a pandas series variable `s` (e.g. in a jupyter notebook) you can obtain this format by calling the `to_json` method with `date_format="iso"`:
```python
print(s.to_json(date_format="iso", indent=2))
```
##### Wrapped format
Alternatively the [wrapped](../../../user_guide/attached_metadata.md) format allows to

* add metadata that will then be attached to the `.attrs` dictitionary of the resulting Pandas Series object
* set parsing options, like "orient", for example to provide input data with duplicate index entries:

```json
{
	"__hd_wrapped_data_object__": "SERIES",
	"__metadata__": {},
	"__data__": {
		"name": "series_name",
		"index": [
				"2020-01-01T01:15:27.000Z",
				"2020-01-01T01:15:27.000Z",
				"2020-01-03T08:20:04.000Z"
		],
		"data": [
			42.2,
			18.7,
			25.9
		]
		},
		"__data_parsing_options__": {
			"orient": "split"
		}
	}
```
Here of course the content of `__data__` must correspond to the provided `__data_parsing_options__`, i.e. when orient is `split` the structure here must agree with what Pandas [read_json ](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_json.html) expects for this orient for `typ="series"`.

hetida designer always outputs the wrapped format with `orient="split"` for SERIES objects in order to guarantee inclusion of duplicate index entries.

#### DATAFRAME JSON

```json
{
    "column1": {
        "2019-08-01T15:45:36.000Z": 1,
        "2019-08-02T11:33:41.000Z": 2
    },
    "column2": {
        "2019-08-01T15:45:36.000Z": 1.3,
        "2019-08-02T11:33:41.000Z": 2.8
    }
}
```
Having a Pandas DataFrame variable `df` (e.g. in a jupyter notebook) you can obtain this format by calling the `to_json` method with `orient="columns", date_format="iso"`:
```python
print(df.to_json(orient="columns", date_format="iso", indent=2))
```

Similarly to SERIES, there is a wrapped format, see [here](../../../user_guide/attached_metadata.md) for details. hetida designer always outputs the wrapped format for DATAFRAME objects with default parsing options.

#### MULTITSFRAME JSON

```json
{
    "value": [
        1,
        1.2,
        0.5
    ],
    "metric": [
        "a",
        "b",
        "c"
    ],
    "timestamp": [
        "2019-08-01T15:45:36.000Z",
        "2019-08-01T15:48:36.000Z",
        "2019-08-01T15:42:36.000Z"
    ]
}
```
Having a Pandas DataFrame variable `df` (e.g. in a jupyter notebook) with these 3 columns you can obtain this format by calling the `to_json` method with `orient="columns", date_format="iso"`:
```python
print(df.to_json(orient="columns", date_format="iso", indent=2))
```

Similarly to SERIES, there is a wrapped format, see [here](../../../user_guide/attached_metadata.md) for details. hetida designer always outputs the wrapped format for MULTITSFRAME objects with default parsing options.

### CSV Formats

#### SERIES CSV

```
index;value
2020-07-01T00:00:00Z;25.3
2020-07-02T00:00:00Z;30.3
2020-07-03T00:00:00Z;21.0
```

Here the first line is obligatory/fixed and using semicolon as separator is a must.

#### DATAFRAME CSV

```csv
index;First_col;Second_col
2020-07-01T00:00:00Z;100.0;139.0
2020-07-01T01:00:00Z;100.1;140.0
```

index is required and then arbitrary columns may follow. Values must be seperated by semicolons.

### Supplying multiple manual Inputs from one Json file

The test execution dialog contains two buttons: "Download JSON Template" and "Upload JSON Data". The later can be used to fill multiple inputs at the same time from one Json file. The "Download JSON Template" button provides an easy way to get a Json file for this purpose to start with.


