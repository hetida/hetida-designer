# Moving average number

## Description
The component calculates the moving average for a constant number of observations.

## Inputs
* **data** (Pandas Series or Pandas DataFrame): Indices must be numeric or datetimes, entries must be numeric.
* **n** (Integer): The number of observations, the average is calculated for.

## Outputs
* **mavg** (Pandas Series or Pandas DataFrame): The moving average of **data**.

## Details
The component calculates the moving average for a constant number of observations, sorted by their indices. 

Therefore, it excludes NaN respectively None values from **data** and equippes each remaining index with the average of the foregoing n numerical observations.

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
	"mavg": {
				"2019-08-01T15:20:10": null,
				"2019-08-01T15:20:25": null,
				"2019-08-01T15:20:30": 2.0,
				"2019-08-01T15:20:35": 3.0,
				"2019-08-01T15:20:55": 6.0,
				"2019-08-01T15:20:56": 9.0
	}
```
