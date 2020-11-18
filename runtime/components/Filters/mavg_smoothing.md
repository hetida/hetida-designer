# MAVG Smoothing

## Description
Return Moving Averages.

## Inputs
* **data** (Pandas Series or Pandas DataFrame): Values must be numeric.
* **window_size** (String): Window, in which the moving average is calculated. 

## Outputs
* **data** (Pandas Series): The filtered data.

## Details
Use Moving Average to smooth a Series or a DataFrame. The parameter window_size should be a String accordiding to what is allowed for Pandas rolling method.
