# Drop NaN

## Description
The component drops rows containing NaN values.

## Inputs
* **data** (Pandas Series or Pandas DataFrame): Values must be numeric. 

## Outputs
* **data** (Pandas Series or Pandas DataFrame): The Pandas object without NaN rows.

## Details
The component calls Pandas' dropna method with no parameters on the provided input data and returns the result. This removes all rows containing a nan value (in any column for a dataframe).
