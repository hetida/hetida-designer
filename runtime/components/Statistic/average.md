# Average

## Description
This component calculates the average of the input.

## Inputs
* **data** (Pandas Series or Pandas DataFrame): Entries must be numeric.

## Outputs
* **average** (Float or Pandas Series): The average of **data**. 

## Details
The component calculates the average of the columns of **data**, excluding NaN respectively None values. 

Columns including non-numeric values are ignored. 

## Examples
The json input of a typical call of this component with a Pandas Series is
```
{
	"data": {
				"2019-08-01T15:20:10": 1.7,
				"2019-08-01T15:20:20": null,
				"2019-08-01T15:20:25": 0.3,
				"2019-08-01T15:20:30": 1.0
	}
}
```
The expected output is
```
	"average": 1 
```
The json input of a typical call of this component with a Pandas DataFrame is
```
{
	"data": {
				"a": {
                    "2019-08-01T15:44:12": 9,
                    "2019-08-01T15:20:12": -4,
                    "2019-08-03T16:20:15": None,
                    "2019-08-05T12:00:34": 1,
                },
                "b": {
                    "2019-08-01T15:44:12": -1,
                    "2019-08-01T15:20:12": "test",
                    "2019-08-03T16:20:15": 0,
                    "2019-08-05T12:00:34": 4,
                }
	}
}
```
The expected output is
```
	"average": {
				"a": 2
	}
```
