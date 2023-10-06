# DataFrames, MultiTSFrames and Series with attached Metadata

Metadata to a dataset is an essential ingredient for many analytical operations. E.g. if you want to detect gaps in an irregular timeseries and you only get the timestamp, value pairs of a time interval, you cannot know where the interval starts and ends. Consequently you are unable to say whether there is a gap at the beginning or end.

Both [pandas DataFrames](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.attrs.html) and [pandas Series](https://pandas.pydata.org/pandas-docs/version/1.0.0/reference/api/pandas.Series.attrs.html) can have metadata attached in their attribute `attrs`. The hetida designer and its [adapter system](./adapter_system/generic_rest_adapters/web_service_interface.md) support enriching and receiving such metadata.

## Add Attributes and Extract Attributes components

To extract or update the metadata the corresponding base components "Extract Attributes (DataFrame)", "Extract Attributes (MultiTSFrame)", "Extract Attributes (Series)", "Add/Update Attributes (DataFrame)", "Add/Update Attributes (MultiTSFrame)" and "Add/Update Attributes (Series)" are available in the category "Connectors".

<img src="./assets/metadata_base_components.png" height="110" width=850> 

The "Extract Attributes" components reads `attrs` from the underlying Dataframe/Series object and outputs it as a Python dictionary.

The "Add/Update Attributes" components update the metadata dictionary stored in `attrs` of the underlying Dataframe/Series.

## Providing and outputting metadata with manual input (direct provisioning)
You can provide such metadata when manual inputting data by entering
```json
{
    "__hd_wrapped_data_object__": "DATAFRAME",
    "__metadata__": {"test": 43},
    "__data__": {"a": [2.3, 2.4, 2.5], "b": ["t", "t", "k"]}
}
```
for a DATAFRAME or MULTITSFRAME input or
```json
{
    "__hd_wrapped_data_object__": "SERIES",
    "__metadata__": {"test": 43},
    "__data__": [1.2, 3.7, 8.9]
}
```
for a SERIES input.

Here the content of the `__data__` field can be anything which the corresponding actual DataFrame or Series parsing may understand.

This "wrapper" format is also received when using the direct provisioning adapter for oupts ("Output Only").

Note that the unwrapped format (i.e. sending only the content of the `__data__` field unwrapped) also works and provides the parsed object with an empty dictionary `{}` as `.attrs` attribute.

**Note:** The local file adapter does not support sending or receiving metadata in `attrs` currently.


## Metadata field conventions

The following metadata fields should be attached to timeseries objects (typically MULTITSFRAME or SERIES inputs/outputs). I.e.
* we recommend that custom adapter implementations send
* some base components may expect these metadata fields in the `.attrs` dictionary of input dataframes (or multitsframes) or series.
* some base components may send these metadata fields in the `.attrs` dictionary of output dataframes (or multitsframes) or series objects.

```
{
    # Start / End timestamps of the queried time interval in explicit UTC isoformat:
    "ref_interval_start_timestamp": "2023-01-01T00:00:00+00:00", 
    "ref_interval_end_timestamp": "2023-01-01T00:00:00+00:00",

    # Type of queried time interval (one of
    # "left_closed", "right_open", "right_closed", "left_open", "closed", or "open"):
    "ref_interval_type": "closed",

    # Queried metrics as array/list (List with exactly one entry for a 
    # single timeseries)
    "ref_metrics": ["sensor_a", "sensor_b"],
}
```

## Adapter support
Some of the builtin adapters support sending and receiving metadata:
* The direct provisioning adapter's special format is mentioned above.
* See [here](./adapter_system/generic_rest_adapters/web_service_interface.md), like direct provisioning

