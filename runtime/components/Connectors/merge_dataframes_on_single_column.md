# Merge DataFrames on Single Column

## Description
Merges/Joins two dataframes on a equally named column.

## Inputs
* **dataframe_left** (Pandas DataFrame): The left dataframe.
* **dataframe_right** (Pandas DataFrame): The right dataframe.
* **column_name** (String): The name of the column to join on. Must be present in both dataframe_left and dataframe_right.
* **how** (String): Join method (one of "left", "right", "outer", "inner")

## Outputs
* **merged_dataframe** (Pandas DataFrame): The resulting new merged DataFrame.

## Details
Merges/Joins two dataframes on a column present in both. The join method can be set using the **how** parameter.