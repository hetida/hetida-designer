"""Csv or Json to Single Timeseries

# Csv or Json to Single Timeseries

Create single timeseries from long format CSV or JSON data.

Loads data for a single timeseries from the "data_content"
input which can receive either CSV (as string) or JSON data
in the typical long format with timestamp, metric and value
columns (where only one metric is allowed).

## CSV format:

```
timestamp,metric,value
2025-01-22T08:28:28.301489+00:00,Battery_Power,1531.0
2025-01-22T08:28:38.333878+00:00,Battery_Power,1531.0
2025-01-22T08:28:48.376429+00:00,Battery_Power,1531.0
2025-01-22T08:28:58.416622+00:00,Battery_Power,1528.0
2025-01-22T08:29:08.462281+00:00,Battery_Power,1530.0
2025-01-22T08:29:18.502727+00:00,Battery_Power,1530.0
2025-01-22T08:29:28.539297+00:00,Battery_Power,1531.0
```

When using the CSV format, you can set delimiter and decimal seperator characters
via the respective optional inputs.

CSV content must be provided as JSON String object. E.g. entering data in the hetida designer
execution dialogue's manual input field for the "data_content" input
you need to
* replace line breaks with \n
* wrap the whole content in "" (to tell hetida designer that it is a string)

E.g.
```
"timestamp,metric,value\n2025-01-22T08:28:28.301489+00:00,Battery_Power,1531.0\n2025-01-22T08:28:38.333878+00:00,Battery_Power,1531.0\n2025-01-22T08:28:48.376429+00:00,Battery_Power,1531.0\n2025-01-22T08:28:58.416622+00:00,Battery_Power,1528.0\n2025-01-22T08:29:08.462281+00:00,Battery_Power,1530.0\n2025-01-22T08:29:18.502727+00:00,Battery_Power,1530.0"
```


## JSON format
```
[
  {
    "timestamp":"2025-01-22T08:28:28.301Z",
    "metric":"Battery_Power",
    "value":1531.0
  },
  {
    "timestamp":"2025-01-22T08:28:38.333Z",
    "metric":"Battery_Power",
    "value":1531.0
  },
  {
    "timestamp":"2025-01-22T08:28:48.376Z",
    "metric":"Battery_Power",
    "value":1531.0
  },
  {
    "timestamp":"2025-01-22T08:28:58.416Z",
    "metric":"Battery_Power",
    "value":1528.0
  },
  {
    "timestamp":"2025-01-22T08:29:08.462Z",
    "metric":"Battery_Power",
    "value":1530.0
  }
]
```

If you have a dataframe `df` with the respective columns, this json format can
be generated using.

```
df.to_json(orient="records", date_format="iso", indent=2))
```

## Single timerseries

For both formats, this component expects exactly one entry in the metric column in order
to regard the data as a single timeseries that can be converted to a SERIES (pandas Series).

The pandas Series object will be provided with the metric as name
"""

import io

import pandas as pd

# %%
# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "data_content": {"data_type": "ANY"},
        "decimal": {"data_type": "STRING", "default_value": "."},
        "sep": {"data_type": "STRING", "default_value": ","},
    },
    "outputs": {
        "timeseries": {"data_type": "SERIES"},
    },
    "name": "Csv or Json to Single Timeseries",
    "category": "Data Sources",
    "description": "Load data for a single timeseries from an input provided with eiter CSV or JSON",  # noqa: E501
    "version_tag": "0.1.0",
    "id": "fffb2264-df2d-487b-844e-7430f083d080",
    "revision_group_id": "f043a312-e4ef-45be-b54f-5e9697ae47aa",
    "state": "RELEASED",
    "released_timestamp": "2025-01-23T08:54:25.009433+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, data_content, decimal=".", sep=","):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    if isinstance(data_content, str):
        # expect csv as string
        # to enter into ANY manual input field:
        # * replace line breaks with \n
        # * wrap in ""

        df = pd.read_csv(
            io.StringIO(data_content),
            sep=sep,
            decimal=decimal,
            dtype={"metric": str, "value": float},
            parse_dates=["timestamp"],
        )

    else:
        # expects json object created via .to_json(orient="records", date_format="iso"))
        # to enter into manual input field: df.to_json(orient="records", date_format="iso", indent=2))
        df = pd.DataFrame.from_dict(data_content)
        df["timestamp"] = pd.to_datetime(df["timestamp"])

    unique_metrics = df["metric"].unique()
    if len(unique_metrics) != 1:
        raise ValueError(
            f"Not excatly one metric: {str(unique_metrics)}. Cannot convert this to a single Series object."
        )

    s = pd.Series(df["value"].values, index=df["timestamp"], name=unique_metrics[0])

    return {"timeseries": s}


# %%

TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "data_content",
            "filters": {
                "value": '[\n  {\n    "timestamp":"2025-01-22T08:28:28.301Z",\n    "metric":"Battery_Power",\n    "value":1531.0\n  },\n  {\n    "timestamp":"2025-01-22T08:28:38.333Z",\n    "metric":"Battery_Power",\n    "value":1531.0\n  },\n  {\n    "timestamp":"2025-01-22T08:28:48.376Z",\n    "metric":"Battery_Power",\n    "value":1531.0\n  },\n  {\n    "timestamp":"2025-01-22T08:28:58.416Z",\n    "metric":"Battery_Power",\n    "value":1528.0\n  },\n  {\n    "timestamp":"2025-01-22T08:29:08.462Z",\n    "metric":"Battery_Power",\n    "value":1530.0\n  }\n  ]\n  '
            },
        }
    ]
}

RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "data_content",
            "filters": {
                "value": '[\n  {\n    "timestamp":"2025-01-22T08:28:28.301Z",\n    "metric":"Battery_Power",\n    "value":1531.0\n  },\n  {\n    "timestamp":"2025-01-22T08:28:38.333Z",\n    "metric":"Battery_Power",\n    "value":1531.0\n  },\n  {\n    "timestamp":"2025-01-22T08:28:48.376Z",\n    "metric":"Battery_Power",\n    "value":1531.0\n  },\n  {\n    "timestamp":"2025-01-22T08:28:58.416Z",\n    "metric":"Battery_Power",\n    "value":1528.0\n  },\n  {\n    "timestamp":"2025-01-22T08:29:08.462Z",\n    "metric":"Battery_Power",\n    "value":1530.0\n  }\n  ]\n  '
            },
        }
    ]
}
