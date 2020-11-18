# Derivate

## Description
The component calculates the difference quotient.

## Inputs
* **data** (Pandas Series): The indices must be numeric or datetimes, the values must be numeric.

## Outputs
* **diff_quo** (Pandas Series): The difference quotient of data.

## Details
The component calculates the difference quotient of data, sorted by its index. It ignores NaN values. 
If the indices are datetimes, their distances are expressed in seconds.
Each difference quotient is given to the greater index.

## Examples
The json input of a typical call of this component with a Pandas Series is
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
	"diff_quo": {
			"2019-08-01T15:20:25": -0.2,
			"2019-08-01T15:20:30": 0.04
		}
```
