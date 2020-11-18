# First Datetime Index

## Description
Extracts the first (minimum) datetime index

## Inputs
* **timeseries_data** (Any, expects a Pandas Series or Pandas Dataframe): Must have a datetime index.

## Outputs
* **first_index** (String): The first (minimum) timestamp occuring as index is returned as isoformat timestamp string.

## Details
Takes the minimum index and returns its as string.

## Examples
The json input of a typical call of this component with a Pandas Series is
```
{
	"timeseries_data": {
				"2019-08-01T15:50:12": 0,
				"2019-08-01T15:44:12": 3,
				"2019-08-03T16:20:15": null  
	}
}
```
The expected output is
```
	"first_index": 2019-08-01T15:44:12+00:00

```
