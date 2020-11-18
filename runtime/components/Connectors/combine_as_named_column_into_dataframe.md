# Combine as named column into DataFrame

## Description
Combine series data as named column into a DataFrame.

## Inputs
* **series_or_dataframe** (Any, expects a Pandas Series or Pandas DataFrame): The object with which to start with. If a DataFrame then the **series** is added to this as a new column.
* **series** (Pandas Series): The series that should be added as a column to series_or_dataframe.
* **column_name**: (String): The column name for the new column.

## Outputs
* **dataframe** (Pandas DataFrame): The combined data in a DataFrame

## Details
This component can be used to combine two pandas Series into a DataFrame or add a pandas Series to an existing DataFrame while providing a column name for the new column.

Note: If a column with that name already exists, it will be overwritten!

This works best if both have the same index. Multiple consecutive use of this component allows to combine several Series into a DataFrame.
