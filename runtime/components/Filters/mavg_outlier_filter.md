# MAVG Outlier Filter

## Description
Return only those values inside of moving mean / std - band.

## Inputs
* **allowed_deviation_factor** (Float): The indices must be datetimes with constant differences, the values must be numeric.
* **window_size** (String): Cut-off frequency. 
* **ts** (Pandas Series or Pandas DataFrame): Values must be numeric. 

## Outputs
* **ts** (Pandas Series): The filtered data.

## Details
Returns only those values deviating not more than a factor times the moving standard deviation from the moving average.

The window size can be set as a String according to the allowed values of Pandas rolling method on a Series.
