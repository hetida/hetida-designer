# Ln

## Description
This component calculates the natural logarithm of data.

## Inputs
* **data** (Integer, Float, Pandas Series or Pandas DataFrame): Entries must be numeric. 

## Outputs
* **ln** (Integer, Float, Pandas Series or Pandas DataFrame): Natural logarithm of data.

## Details
The component calculates the natural logarithm of data. 

## Examples
The json input of a typical call of this component with a Pandas Series is
```
{
	"data": {
				"2019-08-01T15:20:12": null,
				"2019-08-01T15:44:12": 1,
				"2019-08-03T16:20:15": 2.718281828459045
	}
}
```
The expected output is
```
	"ln": {
				"2019-08-01T15:20:12": null,
				"2019-08-01T15:44:12": 0,
				"2019-08-03T16:20:15": 1, 
	}

```
