# Moving maximum number

## Description
The component calculates the moving maximum for a constant number of observations.

## Inputs
* **data** (Pandas Series or Pandas DataFrame): Indices must be numeric or datetimes, entries must be numeric.
* **n** (Integer): The number of observations, the maximum is calculated for.

## Outputs
* **movmax** (Pandas Series or Pandas DataFrame): The moving maximum of **data**.

## Details
The component calculates the moving maximum for a constant number of observations, sorted by their indices. 

Therefore, it excludes NaN respectively None values from **data** and equippes each remaining index with the maximum of the foregoing n numerical observations.   

## Examples
The json input of a typical call of this component with a Pandas Series is
```
{
	"data": {
				"2019-08-01T15:20:10": 3.0,
				"2019-08-01T15:20:20": null,
				"2019-08-01T15:20:25": 3.0,
				"2019-08-01T15:20:30": 0.0,
				"2019-08-01T15:20:35": 6.0,
				"2019-08-01T15:20:40": null,
				"2019-08-01T15:20:55": 12.0,
				"2019-08-01T15:20:56": 9.0
	}, 
	"n": 3
}
```
The expected output is
```
	"movmax": {
				"2019-08-01T15:20:10": null,
				"2019-08-01T15:20:25": null,
				"2019-08-01T15:20:30": 3.0,
				"2019-08-01T15:20:35": 6.0,
				"2019-08-01T15:20:55": 12.0,
				"2019-08-01T15:20:56": 12.0
	}
```
