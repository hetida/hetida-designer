
# MULTITSFRAME

MultiTSFrames represents multiple timeseries (of same dimension) data with non-necessarily common timestamps.

Data is stored in records, one per metric per timestamp where this metric has value(s), i.e. in "long format", e.g.

timestamp, metric, value
2024-12-01T01:00:00+00:00
....


This is in contrast to "wide format" where each metric is its own column.

A main advantage of the long-format is that it is more storage-efficient in case that multiple timeseries do not have the same timestamps.

A MultiTSFrame must have at least three columns: 
* a "timestamp" column (datetime, no missing entries allowed)
* a "metric" column (string, no missing entries allowed)
* at least one value column: Per convention the third column is often named "value". Many base components assume only the three columns "timestamp", "metric" and "value".

TODO: reformulate "multi-dimensional"
In case the MultiTSFrame contains timeseries where the timestamps are always the same, e.g., when a series is aggregated for a certain frequency using different functions, it might be useful to return a MultiTSFrame with additional columns. This is a special case and should only be applied, when it is clear that the stored timeseries will never have different timestamps.


## Internal: Workflow & Components
Within workflows and components the MultiTSFrame object is a pandas.DataFrame following certain conventions:
- "metric" column with string and no missing data,
- "timestamp" column with timestamp information,
- "additional" column, mostly named value.

Note that Pandas will handle a column build from values of differing types as dtype `object` and this may negatively impact efficiency / performance).

In contrast to pandas.Series the index of a MultiTSFrame should be considered irrelevant since timestamp information is in the "timestamp" column. When manipulating MultiTSFrame Pandas DataFrames you should ensure that the resulting index is duplicate-free. Ideally a generic integer index.

In the documentation of the workflow and components the convention is to write **MultiTSFrame**, e.g.:
- mutiple_timeseries (MultiTSFrame): This is an example for the documentation of an input/output with the type MultiTSFrame

## External: Adapter System
### [Manual Input / Direct Provisioning](../adapter_system/manual_input.md)
To define a MultiTSFrame a json of the following format can be defined:

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

TODO: mention wrapped format!

**Tip**: Having a Pandas DataFrame variable `df` (e.g. in a jupyter notebook) with these 3 columns you can obtain this format by calling the `to_json` method with `orient="columns", date_format="iso"`:
```python
print(df.to_json(orient="columns", date_format="iso", indent=2))
```

### [Generic Rest Adapter](../adapter_system/generic_rest_adapters/web_service_interface.md)
The generic rest adapter provides functionalities to load and send MultiTSFrames from the hd-instance using the two functions [`post_multitsframe`](../../runtime/hetdesrun/adapters/generic_rest/send_multitsframe.py), and [`load_framelike_data`](../../runtime/hetdesrun/adapters/generic_rest/load_multitsframe.py)

Sending MultiTSFrames requires that the output Pandas DataFrame of a workflow/component passes several validations:
- column "timestamp" has no missing entries and a dtype of pandas.DatetimeTZDtype with timezone UTC
- column "metric" has no missing entries
- at least one additional column is defined.
