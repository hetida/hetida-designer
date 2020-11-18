# Shift values

## Description
This component shifts the values of some data by the desired number of periods.

## Inputs
* **data** (Pandas Series or Pandas DataFrame): Data that should be shifted.
* **periods** (Integer): Positive or negative number of periods to shift.

## Outputs
* **shifted** (Pandas Series or Pandas DataFrame): Shifted **data**.

## Details
This component shifts the values of **data** by the desired number of **periods**. 

## Examples
The json input of a typical call of this component, shifting the values of data by 2 periods is
```
{
	"data": {
				"2019-08-01T15:20:00": 1.0,
				"2019-08-01T15:20:01": 7.0,
				"2019-08-01T15:20:02": 5.0,
	},
	"periods": 2
}
```
The expected output is
```
	"shifted": {
				"2019-08-01T15:20:00": null,
				"2019-08-01T15:20:01": null,
				"2019-08-01T15:20:02": 1.0,
	}
```

The json input of a call of this component with the same data, shifting the values of data -1 period is
```
{
	"data": {
				"2019-08-01T15:20:00": 1.0,
				"2019-08-01T15:20:01": 7.0,
				"2019-08-01T15:20:02": 5.0,
	},
	"periods": -1
}
```
The expected output is
```
	"shifted": {
				"2019-08-01T15:20:00": 7.0,
				"2019-08-01T15:20:01": 5.0,
				"2019-08-01T15:20:02": null,
	}
```
