# Restrict to time interval

## Description
This component restricts a Pandas Series or Pandas DataFrame to a Pandas Series or Pandas DataFrame with respect to some given time interval.

## Inputs
* **data** (Pandas Series or Pandas DataFrame): Indices must be datetimes, either without timezone name or with utc offset.
* **start** (String): Date as popular format (e.g. "10 Aug 2012 10:20:30", "2019-08-01T15:20:10") or relative dates (e.g. "yesterday -10 years", "1 hour ago -0500"), either without timezone name or with utc offset.
* **stop** (String): Date as popular format (e.g. "10 Aug 2012 10:20:30", "2019-08-01T15:20:10") or relative dates (e.g. "yesterday -10 years", "1 hour ago -0500"), either without timezone name or with utc offset.

## Outputs
* **interval** (Pandas Series or Pandas DataFrame): Contains data restricted to the indices between start and stop.

## Details
The component restricts the input data to the time interval between start and stop. Entries with index before start or after stop are filtered. 

## Examples
The json input of a typical call of this component with a Pandas Series without timezone is
```
{
	"data": {
				"2019-08-01T15:20:10": 3.3,
				"2019-08-01T15:20:20": 7.5,
				"2019-08-01T15:20:25": 0.3,
				"2019-08-01T15:20:30": 0.5
	},
	"start": "2019-08-01T15:20:15",
	"stop": "2020-08-01T15:20:30"
}
```
The expected output is
```
	"interval": {
				"2019-08-01T15:20:20": 7.5,
				"2019-08-01T15:20:25": 0.3,
				"2019-08-01T15:20:30": 0.5
		}
```

The json input of a typical call of this component with a Pandas Series without utc offset is
```
{
	"data": {
				"2016-12-31 00:30:00+01:00": 3.3,
				"2016-12-31 00:30:10+01:00": 7.5,
				"2016-12-31 00:30:20+01:00": 0.3,
				"2016-12-31 00:30:30+01:00": 0.5
	},
	"start": "2016-12-31 00:30:10+01:00",
	"stop": "2016-12-31 00:30:20+01:00"
}
```
The expected output is
```
	"interval": {
				"2016-12-31 00:30:10+00:00": 7.5,
				"2016-12-31 00:30:20+00:00": 0.3
		}
```