# Divide

## Description
This component divides numeric values, Pandas Series and Pandas DataFrames.

## Inputs
* **a** (Integer, Float, Pandas Series or Pandas DataFrame): Entries must be numeric.
* **b** (Integer, Float, Pandas Series or Pandas DataFrame): Entries must be numeric.

## Outputs
* **quotient** (Integer, Float, Pandas Series or Pandas DataFrame): The quotient of a and b. 

## Details
The component divides a by b. 

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
				"2019-08-01T15:20:12": 0.5,
				"2019-08-01T15:44:12": 2.6,
				"2019-08-03T16:20:15": 2.0,
				"2019-08-05T12:00:34": 1.0    
	}
}
```
The expected output is
```
	"quotient": {
			"2019-08-01T15:20:12": 2.4,
			"2019-08-01T15:44:12": 0.0,
			"2019-08-03T16:20:15": 0.15,
			"2019-08-05T12:00:34": 0.5,
                       "2019-08-07T11:01:00": null  
	}

```

The json input of a typical call of this component with a Pandas DataFrame and a float is
```
{
    "a": {
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
	},
	"b": 2.0
}
```
The expected output is
```
	"quotient": {
			"first": {
                               "2019-08-01T15:20:12": 0.6,
				"2019-08-01T15:44:12": null,
				"2019-08-03T16:20:15": 0.15,
				"2019-08-05T12:00:34": 0.25
             },
            "second": {
                                "2019-08-01T15:20:12": 27.2,
				 "2019-08-01T15:44:12": 2.15,
				 "2019-08-03T16:20:15": 10.5,
				 "2019-08-05T12:00:34": 3.75
             }
	}
```
