# Abs

## Description
This component calculates the absolute value of the input.

## Inputs
* **data** (Integer, Float, Pandas Series or Pandas DataFrame): Entries must be numeric.

## Outputs
* **absolute** (Integer, Float, Pandas Series or Pandas DataFrame): Absolute value of data.

## Details
The component calculates the absolute value of the input. 

## Examples
The json input of a typical call of this component with a Pandas Series is
```
{
	"data": {
				"2019-08-01T15:20:12": 4,
				"2019-08-01T15:44:12": -9,
				"2019-08-03T16:20:15": 0,
				"2019-08-05T12:00:34": null,
                               "2019-08-07T11:01:00": -100
	}
}
```
The expected output is
```
	"absolute": {
				"2019-08-01T15:20:12": 4,
				"2019-08-01T15:44:12": 9,
				"2019-08-03T16:20:15": 0,
				"2019-08-05T12:00:34": null,
                               "2019-08-07T11:01:00": 100
	}

```
