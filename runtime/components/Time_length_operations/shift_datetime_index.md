# Shift Datetime Index

## Description
This component shifts the indices of some data by the desired frequency and number of periods.

## Inputs
* **data** (Pandas Series or Pandas DataFrame): Index must be datetime.
* **frequency** (String): Frequency, the data should be shifted. For example 'ms', '3s', 'min', '2h' or 'd'.
* **periods** (Integer): Positive or negative number of periods to shift.

## Outputs
* **shifted** (Pandas Seriesor Pandas DataFrame): Shifted **data**.

## Details
This component shifts the indices of **data** by the desired frequency and number of periods. 

## Examples
The json input of a typical call of this component, shifting index of data by 2 days is
```
{
	"data": {
				"2019-08-01T15:20:00": 1.0,
				"2019-08-02T15:20:15": 7.0,
				"2019-08-04T15:19:20": 5.0,
	},
	"frequency" = "d"
	"periods": 2
}
```
The expected output is
```
	"shifted": {
				"2019-08-03T15:20:00": 1.0,
				"2019-08-04T15:20:15": 7.0,
				"2019-08-06T15:19:20": 5.0,
	}
```

The json input of a call of this component with the same data, shifting index of data -1 minute
```
{
	"data": {
				"2019-08-03T15:20:00": 1.0,
				"2019-08-04T15:20:15": 7.0,
				"2019-08-06T15:19:20": 5.0,
	},
	"periods": -1
}
```
The expected output is
```
	"shifted": {
				"2019-08-03T15:19:00": 1.0,
				"2019-08-04T15:19:15": 7.0,
				"2019-08-06T15:18:20": 5.0,
	}
```
