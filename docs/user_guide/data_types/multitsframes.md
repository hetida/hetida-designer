# MultiTsFrame

hetida designer is often used for timeseries data analytics. Therefore it comes with an explicit data type for multivariate timeseries data: A **MultiTSFrame** represents multiple timeseries (of same dimension) data with non-necessarily common timestamps.

## Long Format representation

Data is stored in records, one per metric per timestamp where this metric has value(s), i.e. in "long format".

|         timestamp         | metric | value |
| :-----------------------: | :----: | :---: |
| 2024-12-01T01:00:00+00:00 |   A    | 23.99 |
| 2024-12-01T01:00:00+00:00 |   B    | 23.99 |
| 2024-12-01T01:00:00+00:00 |   C    | 19.99 |
| 2024-12-01T01:00:00+00:00 |   D    | 42.99 |
| 2024-12-01T02:00:00+00:00 |   A    | 24.99 |
| 2024-12-01T02:00:00+00:00 |   B    | 22.99 |
| 2024-12-01T02:00:00+00:00 |   C    | 18.99 |
| 2024-12-01T03:00:00+00:00 |   D    | 45.99 |

### Comparison to "wide" format

This is in contrast to "wide format" where each metric is its own column. A main advantage of the long-format is
that it is more storage-efficient in case that multiple timeseries do not have the same timestamps.

|         timestamp         |   A   |   B   |   C   |   D   |
| :-----------------------: | :---: | :---: | :---: | :---: |
| 2024-12-01T01:00:00+00:00 | 23.99 | 23.99 | 19.99 | 42.99 |
| 2024-12-01T02:00:00+00:00 | 24.99 | 22.99 | 18.99 |       |
| 2024-12-01T03:00:00+00:00 |       |       |       | 45.99 |

!!! info
Note that hetida designer provides base components to convert into "wide" format dataframes and vice versa in the category "Connectors"

!!! tip "Only one metric?"
If your data consists of exactly one timeseries, the `metric` column is constant and therefore redundant. In that case use a [SingleTSFrame](singletsframes.md) instead — it has the same representation minus the `metric` column, and still supports arbitrarily many value dimensions. The base component "Extract SingleTSFrame from MultiTSFrame" converts a single metric of a MultiTSFrame into a SingleTSFrame.

## MultiTsFrame details

A MultiTSFrame must have at least three columns:

- a "timestamp" column (datetime, no missing entries allowed)
- a "metric" column (string, no missing entries allowed)
- at least one value column: Per convention the third column is often named "value". Note that many base components operating on MultiTsFrames assume only the three columns "timestamp", "metric" and "value".

A MultiTSFrame can contain multi-dimensional timeseries data simply by having more than one value column. This implies that dimensions should agree for all metrics.

As an example consider a measurement by drones where location of measurement is relevant:

|         timestamp         |      metric      | value |     latitude      |     longitude     |
| :-----------------------: | :--------------: | :---: | :---------------: | :---------------: |
| 2024-12-01T01:00:00+00:00 |   drone_A.temp   | 10.2  | 51.43462264339895 | 7.030261299552767 |
| 2024-12-01T01:00:00+00:00 | drone_A.pressure | 0.47  | 51.43462264339895 | 7.030261299552767 |
| 2024-12-01T01:00:06+00:00 |   drone_A.temp   | 10.1  | 51.43462271146983 | 7.030265004120332 |
| 2024-12-01T01:00:00+00:00 |   drone_B.temp   |  8.7  | 51.43952210110222 | 7.032115169871234 |
| 2024-12-01T01:00:05+00:00 |   drone_B.temp   |  8.6  | 51.43952228945781 | 7.032115457891023 |

Or stock share trade events where price and number of trades shares is necessary:

|         timestamp         | metric | price  | number |
| :-----------------------: | :----: | :----: | :----: |
| 2024-11-30T07:35:00+00:00 |  MSFT  | 409.6  |  -10   |
| 2024-12-02T15:16:12+00:00 |  AMZN  | 200.65 |   3    |

## Internal: Workflow & Components

Within workflows and components the MultiTSFrame object is a pandas.DataFrame following certain conventions:

- "metric" column with string and no missing data,
- "timestamp" column with timestamp information,
- additional value columns (at least one), often exactly one named "value".

Note that Pandas will handle a column build from values of differing types as dtype `object` and this may negatively impact efficiency / performance.

In contrast to pandas.Series the index of a MultiTSFrame should be considered irrelevant since timestamp information is in the "timestamp" column. When manipulating MultiTSFrame Pandas DataFrames you should ensure that the resulting index is duplicate-free. Ideally a generic integer index.

In the documentation of the workflow and components the convention is to write **MultiTSFrame**, e.g.:

```
- mutiple_timeseries (MultiTSFrame): This is an example for the documentation of an input/output with the type MultiTSFrame
```

## External: Adapter System

### Manual Input / Direct Provisioning

A simple json representation of a MultiTSFrame for the [direct provisioning adapter](../../integration_guide/adapter_system/builtin_adapters/direct_provisioning.md) is the following format:

```json
{
  "value": [1, 1.2, 0.5],
  "metric": ["a", "b", "c"],
  "timestamp": ["2019-08-01T15:45:36.000Z", "2019-08-01T15:48:36.000Z", "2019-08-01T15:42:36.000Z"]
}
```

!!! tip
Having a Pandas DataFrame variable `df` (e.g. in a jupyter notebook) with these 3 columns you can obtain this format by calling the `to_json` method with `orient="columns", date_format="iso"`:
`python
    print(df.to_json(orient="columns", date_format="iso", indent=2))
    `

It is possible to define metadata for the MultiTSFrame.
Conventions for the metadata keys can be found [here](../attached_metadata.md).

For such cases, we recommend using the `wrapped format`, e.g.:

```json
{
  "__hd_wrapped_data_object__": "DATAFRAME",
  "__metadata__": {
    "ref_data_frequency": {
      "a": "1h",
      "b": "1h"
    }
  },
  "__data__": {
    "value": {
      "0": 1,
      "1": 1.2,
      "2": 0.5,
      "3": 0.4
    },
    "metric": {
      "0": "a",
      "1": "a",
      "2": "b",
      "3": "b"
    },
    "timestamp": {
      "0": "2019-08-01T01:00:00.000Z",
      "1": "2019-08-01T02:00:00.000Z",
      "2": "2019-08-01T01:00:00.000Z",
      "3": "2019-08-01T02:00:00.000Z"
    }
  }
}
```

### Generic Rest Adapter

Sending a MultiTSFrames from a hetida designer workflow/component output to a generic Rest adapter sink of type MULTITSFRAME requires that the output pandas.DataFrame object passes several validations:

- column "timestamp" has no missing entries and a dtype of pandas.DatetimeTZDtype with timezone UTC
- column "metric" has no missing entries
- at least one additional column is defined.
