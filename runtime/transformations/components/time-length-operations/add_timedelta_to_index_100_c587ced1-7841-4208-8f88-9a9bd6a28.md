# Add Timedelta to Index

## Description
This component adds the provided timedelta to each of the indices of the provided dataframe or series.

## Inputs
* **df_or_series** (Any): Both dataframe and series are accepted, the indices must be datetimes.
* **timedelta** (String): Timedelta to be added (may be negative) to each of the indices, e.g. '3s', '-1min', or '2days'.

## Outputs
* **df_or_series** (Any): Dataframe or series same as the input just with the provided timedelta added to each of the indices.

## Details
This component adds the provided timedelta to each of the indices of the provided dataframe or series. 

## Examples
The json input of a typical call of this component, adding a timedelta of 2 days to each of the indices is
```
{
	"df_or_series": {
		"2019-08-01T15:20:00": 1.0,
		"2019-08-02T15:20:15": 7.0,
		"2019-08-04T15:19:20": 5.0
	},
	"timedelta": "2days"
}
```
The expected output is
```
	"df_or_series": {
		"2019-08-03T15:20:00": 1.0,
		"2019-08-04T15:20:15": 7.0,
		"2019-08-06T15:19:20": 5.0
	}
```

The json input of a call of this component with the same series, adding a timedelta of -1 minute
```
{
	"df_or_series": {
		"2019-08-03T15:20:00": 1.0,
		"2019-08-04T15:20:15": 7.0,
		"2019-08-06T15:19:20": 5.0
	},
	"timedelta": "-1min"
}
```
The expected output is
```
	"df_or_series": {
		"2019-08-03T15:19:00": 1.0,
		"2019-08-04T15:19:15": 7.0,
		"2019-08-06T15:18:20": 5.0
	}
```
