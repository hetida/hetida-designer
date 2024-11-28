
# MULTITSFRAME
In general, a MultiTSframe is timeseries format, especially suitable for multiple timeseries, using the [long format](https://www.thedataschool.co.uk/luke-bennett/long-vs-wide-data-tables/#:~:text=Data%20tables%20are%20often%20referred,(making%20the%20table%20wider)).

A main advantage of the long-format is that it is very storage-efficient in case that multiple timeseries do not have the same timestamps.

A MultiTSFrame must have at least three columns, where two must be names with "timestamp" (datetime, no missing entries allowed) and "metric" (string, no missing entries allowed). Per convention the third column is often named with "value" as many default-components assume this column name.

In case the MultiTSFrame contains timeseries where the timestamps are always the same, e.g., when a series is aggregated for a certain frequency using different functions, it might be useful to return a MultiTSFrame with additional columns. This is a special case and should only be applied, when it is clear that the stored timeseries will never have different timestamps.

## Internal: Workflow & Components
Within workflows and components the MultiTSFrame object is a pandas.DataFrame following certain conventions:
- "metric" column with string and no missing data,
- "timestamp" column with timestamp information,
- "additional" column, mostly named value.

 If the value column contains several entries with varying dtype, the dtype of the column is `object`. (Note that this unspecific dtype hinders efficiency). In contrast to pandas.Series the index of a MultiTSFrame is usually defined with integers starting from zero.

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
Tip: Having a Pandas DataFrame variable `df` (e.g. in a jupyter notebook) with these 3 columns you can obtain this format by calling the `to_json` method with `orient="columns", date_format="iso"`:
```python
print(df.to_json(orient="columns", date_format="iso", indent=2))
```

### [Generic Rest Adapter](../adapter_system/generic_rest_adapters/web_service_interface.md)
The generic rest adapter provides functionalities to load and send MultiTSFrames from the hd-instance using the two functions [`post_multitsframe`](../../runtime/hetdesrun/adapters/generic_rest/send_multitsframe.py), and [`load_framelike_data`](../../runtime/hetdesrun/adapters/generic_rest/load_multitsframe.py)

Sending MultiTSFrames requires that the output of a workflow/component passes several validations:
- column "timestamp" has no missing entries and a dtype of pandas.DatetimeTZDtype with timezone UTC
- column "metric" has no missing entries
- at least one additional column is defined.

Loading MultiTSFrames requires that the send object is readable via `pd.read_json`.
