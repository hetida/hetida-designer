# Arcuscosine

## Description
This component calculates the arcuscosine of the input.

## Inputs
* **data** (Integer, Float, Boolean, Pandas Series or Pandas DataFrame): Entries must be numeric and between -1 and 1. 

## Outputs
* **result** (Float, Pandas Series or Pandas DataFrame): The arcuscosine of **data**.

## Details
The component calculates the arcuscosine of the input **data** as radians between 0 and pi.

## Examples
The json input of a typical call of this component with a Pandas Series is
```
{
	"data": {
				"2019-08-01T15:20:12": 1.0,
				"2019-08-01T15:44:12": -1.0
	}
}
```
The expected output is
```
	"result": {
				"2019-08-01T15:20:12": 0.0,
				"2019-08-01T15:44:12": 3.14159
	}
```
