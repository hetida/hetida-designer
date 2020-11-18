# Integrate

## Description
This component integrates a Pandas Series.

## Inputs
* **data** (Pandas Series): The indices must be numeric or datetimes, the values must be numeric.

## Outputs
* **integral** (Float): The integral of data. 

## Details
This component calculates the integral according to the trapezoidal rule. Therefore, the component ignores NaN values and uses a version of data, sorted by its index. 
If the indices are datetimes, their distances are expressed in seconds.

## Examples
The json input of a typical call of this component with a Pandas Series is
```
{
	"data": {
				"2019-08-01T15:20:10": 1.7,
				"2019-08-01T15:20:20": null,
				"2019-08-01T15:20:25": 0.3,
				"2019-08-01T15:20:30": 0.5
	}
}
```
The expected output is
```
	"integral": 17
```