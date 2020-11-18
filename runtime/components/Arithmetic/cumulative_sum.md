# Cumulative sum

## Description
The component calculates the cumulative sum.

## Inputs
* **data** (Pandas Series or Pandas DataFrame): The indices must be numeric or datetimes, the values must be numeric.

## Outputs
* **cum_sum** (Pandas Series): The cumulative sum of the input.

## Details
The component calculates the cumulative sum of data, sorted by its index. 

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
	"cum_sum": {
				"2019-08-01T15:20:10": 3.3,
				"2019-08-01T15:20:20": null,
				"2019-08-01T15:20:25": 3.6,
				"2019-08-01T15:20:30": 4.1
		}
```