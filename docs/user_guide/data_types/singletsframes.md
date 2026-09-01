# SingleTsFrame

A **SingleTSFrame** represents a _single_ timeseries which may be **multi-dimensional**, i.e. which may have more than one value per timestamp.

It sits between [SERIES](#comparison-to-series-and-multitsframe) and [MultiTSFrame](multitsframes.md): like a SERIES it holds exactly one metric, and like a [MultiTSFrame](multitsframes.md) it uses the tabular record representation with a `timestamp` column and arbitrarily many value columns.

## Representation

Data is stored in records, one per timestamp, with one column per value dimension.

|         timestamp         | value |     latitude      |     longitude     |
| :-----------------------: | :---: | :---------------: | :---------------: |
| 2024-12-01T01:00:00+00:00 | 10.2  | 51.43462264339895 | 7.030261299552767 |
| 2024-12-01T01:00:06+00:00 | 10.1  | 51.43462271146983 | 7.030265004120332 |
| 2024-12-01T01:00:12+00:00 | 10.0  | 51.43462277953001 | 7.030268708688123 |

This is exactly the format of a [MultiTSFrame](multitsframes.md) **minus the `metric` column** — which is not needed, since all records belong to one and the same metric. The metric itself is identified in the [attached metadata](../attached_metadata.md) instead.

### Comparison to SERIES and MultiTSFrame

|                   | metrics | value dimensions | timestamps located in  |
| :---------------- | :-----: | :--------------: | :--------------------: |
| SERIES            |    1    |        1         |       the index        |
| **SINGLETSFRAME** |  **1**  |      **n**       | the `timestamp` column |
| MULTITSFRAME      |    m    |        n         | the `timestamp` column |

Use a SINGLETSFRAME when

- you have exactly one timeseries, so a MULTITSFRAME's `metric` column would be constant and redundant, **and**
- that timeseries has more than one value dimension, or you want to keep the option open, so a SERIES is too narrow.

!!! info
hetida designer provides base components in the category "Connectors" to convert between SINGLETSFRAME and SERIES, MULTITSFRAME and DATAFRAME, in particular "Convert Series to SingleTSFrame" and "Extract SingleTSFrame from MultiTSFrame".

## SingleTsFrame details

A SingleTSFrame must have at least two columns:

- a "timestamp" column (datetime, UTC time zone, no missing entries allowed)
- at least one value column: Per convention the value column is often named "value". Note that many base components operating on SingleTSFrames assume a column named "value" or use the only value column if there is exactly one.

In contrast to a MultiTSFrame there is **no** reserved `metric` column. A column named `metric` is allowed and is treated as an ordinary value dimension — but be aware that this makes the frame convertible to a MultiTSFrame only at the cost of that value dimension.

## Internal: Workflow & Components

Within workflows and components the SingleTSFrame object is a pandas.DataFrame following certain conventions:

- "timestamp" column with timestamp information (dtype `datetime64[us, UTC]`), no missing data,
- additional value columns (at least one), often exactly one named "value".

Note that Pandas will handle a column built from values of differing types as dtype `object` and this may negatively impact efficiency / performance.

In contrast to pandas.Series the index of a SingleTSFrame should be considered irrelevant since timestamp information is in the "timestamp" column. When manipulating SingleTSFrame Pandas DataFrames you should ensure that the resulting index is duplicate-free. Ideally a generic integer index.

In the documentation of the workflow and components the convention is to write **SingleTSFrame**, e.g.:

```
- single_timeseries (SingleTSFrame): This is an example for the documentation of an input/output with the type SingleTSFrame
```

## Metadata

The [metadata conventions](../attached_metadata.md) apply as for SERIES and MULTITSFRAME. Since a SingleTSFrame holds exactly one metric, its metric is named via `dataset_metadata.single_metric` — the same way as for a SERIES — while its value dimensions are described via `value_dimensions` — the same way as for a MultiTSFrame. See the [SINGLETSFRAME example](../attached_metadata.md#example-for-singletsframe).

## External: Adapter System

### Manual Input / Direct Provisioning

A simple json representation of a SingleTSFrame for the [direct provisioning adapter](../../integration_guide/adapter_system/builtin_adapters/direct_provisioning.md) is the following format:

```json
{
  "value": [1, 1.2, 0.5],
  "timestamp": ["2019-08-01T15:42:36.000Z", "2019-08-01T15:45:36.000Z", "2019-08-01T15:48:36.000Z"]
}
```

!!! tip
Having a Pandas DataFrame variable `df` (e.g. in a jupyter notebook) with a "timestamp" column and value columns you can obtain this format by calling the `to_json` method with `orient="columns", date_format="iso"`:
`python
    print(df.to_json(orient="columns", date_format="iso", indent=2))
    `

It is possible to define metadata for the SingleTSFrame.
Conventions for the metadata keys can be found [here](../attached_metadata.md).

For such cases, we recommend using the `wrapped format`, e.g.:

```json
{
  "__hd_wrapped_data_object__": "DATAFRAME",
  "__metadata__": {
    "dataset_metadata": {
      "single_metric": "abc.temp",
      "metric_key": "id"
    },
    "metrics": [
      {
        "id": "abc.temp",
        "name": "ABC temperature",
        "value_dimensions": [{ "column": "value", "name": "temperature", "unit": "°C" }]
      }
    ]
  },
  "__data__": {
    "value": {
      "0": 21.4,
      "1": 22.1
    },
    "timestamp": {
      "0": "2019-08-01T01:00:00.000Z",
      "1": "2019-08-01T02:00:00.000Z"
    }
  }
}
```

Note that a SingleTSFrame uses the same wrapper type `"DATAFRAME"` as DATAFRAME and MULTITSFRAME, since it is transported as an ordinary dataframe.

### Generic Rest Adapter

The [generic REST adapter interface](../../integration_guide/adapter_system/adapter_rest_api_interface.md) offers dedicated `/singletsframe` GET and POST endpoints for sources and sinks of external type `singletsframe`. Like `multitsframe` and `timeseries` sources, a `singletsframe` source receives `from` and `to` query parameters, so SINGLETSFRAME inputs get a time range picker in the execution dialog.

Sending a SingleTSFrame from a hetida designer workflow/component output to a generic REST adapter sink of type `singletsframe` requires that the output pandas.DataFrame object passes several validations:

- column "timestamp" has no missing entries and a dtype of pandas.DatetimeTZDtype with timezone UTC
- at least one additional column is defined.
