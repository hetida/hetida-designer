# Exp

## Description
This component calculates the exponential function for numeric values, Pandas Series and Pandas DataFrames.

## Inputs
* **data** (Integer, Float, Pandas Series or Pandas DataFrame): Integer, Float, Pandas Series or Pandas DataFrame with numeric values.

## Outputs
* **exp** (Integer, Float, Pandas Series or Pandas DataFrame): Exponential of data.

## Details
The component calculates the exponential function of data. 

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
	"exp": {
			"2019-08-01T15:20:12": 1,
			"2019-08-01T15:44:12": 20.085536923187664,
			"2019-08-03T16:20:15": null 
	}

```
