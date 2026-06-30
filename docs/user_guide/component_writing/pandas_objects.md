# Pandas objects in hetida designer

## Handling of index during DataFrame serialisation

When your workflow or component has a pandas.DataFrame as a DATAFRAME output and is run directly, serialization will assume that the index is unique. If this is not the case you will get a `ValueError` stating "DataFrame index must be unique for orient='columns'."

Moreover it is not guaranteed that the index itself is included. In fact this depends on the handling of the sink / adapter to which this output is wired for execution.

Therefore we recommend

- to assume that all relevant information of ingoing DataFrames is in columns and not in the index. E.g. timestamps should be expected in an explicit "timestamp" column and not in the index.
- to finally prepare a result DataFrame to contain all relevant information in explicit columns and not in the index. E.g. add the DateTimeIndex as explicit column "timestamp"
- to reindex it with a unique index prior to outputting it finally.

E.g. the last two steps can be achieved via

```python
dataframe_to_return = dataframe.reset_index(
    names="new_time_column", drop=False, inplace=False
)
```

**Notes**:

- For pd.Series duplicate index entries are no issue since for them serialization is handled differently.
- In-between operators of a workflow, DataFrame objects are transferred as they are, without intermediate serialization. So components working and expecting a index of a certain kind and form do make sense!

### pd.Series names

Adapters may provide pd.Series objects to SERIES inputs either with a name or without.

You should ensure that your code works with both versions, to be independant of the adapter / source used with your workflow.

Note that an explicit "Name Series" component is available in the base component set.

E.g. if you want to convert a pd.Series into a single-column pd.DataFrame we recommend doing the following:

```python
dataframe = series.to_frame(name="new_column_name")
```
