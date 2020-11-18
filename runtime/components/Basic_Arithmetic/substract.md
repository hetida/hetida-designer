# Substract

## Description
This component subtracts numeric values, Pandas Series and Pandas DataFrames.

## Inputs
* **a** (Integer, Float, Pandas Series or Pandas DataFrame): Entries must be numeric.
* **b** (Integer, Float, Pandas Series or Pandas DataFrame): Entries must be numeric.

## Outputs
* **difference** (Integer, Float, Pandas Series or Pandas DataFrame): The difference of a and b. 

## Details
The component calculates the difference of a and b.

## Examples
The json input of a typical call of this component with two Pandas Series is
```
{
	"a": {
				"2019-08-01T15:20:12": 1.2,
				"2019-08-01T15:44:12": 0.0,
				"2019-08-03T16:20:15": 0.3,
				"2019-08-05T12:00:34": 0.5,
                "2019-08-07T11:01:00": 7.8
	},
	"b": {
				"2019-08-01T15:20:12": 1.4,
				"2019-08-01T15:44:12": 2.6,
				"2019-08-03T16:20:15": 3.8,
				"2019-08-05T12:00:34": 5.0    
	}
}
```
The expected output is
```
	"difference": {
			"2019-08-01T15:20:12": -0.2
			"2019-08-01T15:44:12": -2.6,
			"2019-08-03T16:20:15": -3.5,
			"2019-08-05T12:00:34": -4.5,
            "2019-08-07T11:01:00":  null  
	}

```

The json input of a typical call of this component with a Float and a Pandas DataFrame is
```
{
	"a": 5.1
    "b": {
			"first": {
                "2019-08-01T15:20:12": 1.2,
				"2019-08-01T15:44:12": null,
				"2019-08-03T16:20:15": 0.3,
				"2019-08-05T12:00:34": 0.5
             },
            "second": {
                 "2019-08-01T15:20:12": 54.4,
				 "2019-08-01T15:44:12": 4.3,
				 "2019-08-03T16:20:15": 21.0,
				 "2019-08-05T12:00:34": 7.5
             }
	}
}
```
The expected output is
```
	"difference": {
			"first": {
                "2019-08-01T15:20:12": 3.9,
				"2019-08-01T15:44:12": null,
				"2019-08-03T16:20:15": 4.8,
				"2019-08-05T12:00:34": 4.6
             },
            "second": {
                 "2019-08-01T15:20:12": -49.3,
				 "2019-08-01T15:44:12": 0.8,
				 "2019-08-03T16:20:15": -16.9,
				 "2019-08-05T12:00:34": -2.4
             }
	}
```