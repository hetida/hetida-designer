# Drop duplicates

## Description
Drop duplicated rows.

## Inputs
* **data** (Pandas Series or Pandas DataFrame): Values must be numeric. 

## Outputs
* **data** (Pandas Series or Pandas DataFrame): The Pandas object without duplicates.

## Details
The component calls Pandas' drop_duplicates method with no parameters on the provided input data and returns the result.
