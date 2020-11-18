# Sum up Series

## Description
This component sums up a Pandas Series.

## Inputs
* **data** (Pandas Series): The values must be numeric.

## Outputs
* **sum** (Float): The sum of alls values of data.

## Details
This component calculates the sum of the provided series.

## Examples 
The json input of a typical call of this component with a Pandas Series is
```
{
	"data": {
				"2019-08-01T15:20:12": 0,
				"2019-08-01T15:44:12": 3,
				"2019-08-03T16:20:15": null  
	}
}
```
The expected output is
```
	"sum": 4

```
