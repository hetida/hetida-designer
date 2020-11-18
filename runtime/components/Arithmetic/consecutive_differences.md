# Consecutive differences

## Description
This component calculates the consecutive differences of values of a Pandas Series.

## Inputs
* **data** (Pandas Series): The indices must be numeric or datetimes, the values must be numeric.

## Outputs
* **diff** (Pandas Series): The consecutive differences of data.

## Details
This component calculates the differences of consecutive values of data, sorted by its index. It ignores NaN values. 
Each difference is placed at the greater index.

## Examples
The json input of a typical call of this component is
```
{
	"data": {
				"2019-08-01T15:20:10": 3.3,
				"2019-08-01T15:20:20": null,
				"2019-08-01T15:20:25": 0.3,
				"2019-08-01T15:20:30": 0.5
	}
}
```
The expected output is
```
	"diff": {
				"2019-08-01T15:20:25": -3.0,
				"2019-08-01T15:20:30":  0.2
		}
```
