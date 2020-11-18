# Moving median time

## Description
The component calculates the moving median for a constant time interval.

## Inputs
* **data** (Pandas Series or Pandas DataFrame): Indices must be datetimes, entries must be numeric.
* **t** (String): The lenght of the time interval, the median is calculated for. For example, '2ms', '2s', '2min', '2h' or '2d'.

## Outputs
* **movmedian** (Pandas Series or Pandas DataFrame): The moving median of **data**. 

## Details
The component calculates the moving median for a constant time interval. 

Therefore, it excludes NaN respectively None values from **data** and equippes each remaining index with the median of the numerical observations in the foregoing time interval of length t.   

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
				"2019-08-01T15:20:50": 10.0,
				"2019-08-01T15:20:55": 12.0,
				"2019-08-01T15:20:56": 9.0
	}, 
	"t": 16s
}
```
The expected output is
```
	"movmedian": {
				"2019-08-01T15:20:10": 3.0,
				"2019-08-01T15:20:25": 3.0,
				"2019-08-01T15:20:30": 1.5,
				"2019-08-01T15:20:35": 3.0,
				"2019-08-01T15:20:50": 8.0,
				"2019-08-01T15:20:55": 11.0,
				"2019-08-01T15:20:56": 10.0
	}
```
