# Manual Input

When selecting "manual input" in the test execution dialog you have several options to insert and upload data directly without the need of a specific adapter.

For simple types (like STRING, FLOAT, INT) you can enter data directly in the input field. For SERIES, DATAFRAME or ANY inputs clicking on the input field opens an editor dialog where json-data can be entered.

This dialog additionally allows to import a json or csv file from disk via clicking on "Import JSON/CSV". For json files the required format agrees with the format for entering data into the dialogs editor. This format and the format required for CSVs is described below.

:warning:**Important Note :warning::** Importing JSON/CSV files this way has restrictive limits on data size. Since the data is stored as json and send via Web Requests, importing larger files and trying to execute a workflow will soon run into either request size limits or timeouts (and frontend errors). It is strongly recommended to use the [local file adapter](./local_file_adapter.md) for any file that is not very small.

## JSON Formats

### SERIES JSON

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

### DATAFRAME JSON

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
Having a pandas dataframe variable `df` (e.g. in a jupyter notebook) you can obtain this format by calling the `to_json` method with `orient="columns", date_format="iso"`:
```python
print(df.to_json(orient="columns", date_format="iso", indent=2))
```

## CSV Formats

### SERIES CSV

```
index;value
2020-07-01T00:00:00Z;25.3
2020-07-02T00:00:00Z;30.3
2020-07-03T00:00:00Z;21.0
```

Here the first line is obligatory/fixed and using semicolon as separator is a must.

### DATAFRAME CSV

```csv
index;First_col;Second_col
2020-07-01T00:00:00Z;100.0;139.0
2020-07-01T01:00:00Z;100.1;140.0
```

index is required and then arbitrary columns may follow. Values must be seperated by semicolons.

## Supplying multiple manual Inputs from one Json file

The test execution dialog contains two buttons: "Download JSON Template" and "Upload JSON Data". The later can be used to fill multiple inputs at the same time from one Json file. The "Download JSON Template" button provides an easy way to get a Json file for this purpose to start with.


