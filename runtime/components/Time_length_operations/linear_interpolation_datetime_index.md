# Linear Interpolation Datetime Index

## Description
The component linearly interpolates the input data for some given time frequency.

## Inputs
* **data** (Pandas Series or Pandas DataFrame): Indices must be datetimes, entries numeric.
* **t** (String): The time frequency used in the interpolation. For example, 'ms', 's', 'min', 'h' or 'd'.

## Outputs
* **interpolation** (Pandas Series or Pandas DataFrame): The linear interpolation of **data**. 

## Details
The component calculates the linear interpolation of the input **data** for some time frequency **t**. 

## Examples
The json input of a typical call of this component with a Pandas Series is
```
{
	"data": {
                "2019-08-01T15:20:12": 1.2,
                "2019-08-01T15:20:14": 7.2,
                "2019-08-01T15:20:15": 0.3,
                "2019-08-01T15:20:20": 0.5,
	}, 
	"t": s
}
```
The expected output is
```
	"interpolation": {
				"2019-08-01 15:20:12": 1.20
				"2019-08-01 15:20:13": 4.20
				"2019-08-01 15:20:14": 7.20
				"2019-08-01 15:20:15": 0.30
				"2019-08-01 15:20:16": 0.34
				"2019-08-01 15:20:17": 0.38
				"2019-08-01 15:20:18": 0.42
				"2019-08-01 15:20:19": 0.46
				"2019-08-01 15:20:20": 0.50
	}
```
