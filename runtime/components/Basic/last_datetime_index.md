# Last Datetime Index

## Description
Extracts the last (maximum) datetime index

## Inputs
* **timeseries_data** (Any, expects a Pandas Series or Pandas Dataframe): Must have a datetime index.

## Outputs
* **last_index** (String): The last (maximum) timestamp occuring as index is returned as isoformat timestamp string.

## Details
Takes the maximum index and returns its as string.

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
	"last_index": 2019-08-03T16:20:15+00:00

```
