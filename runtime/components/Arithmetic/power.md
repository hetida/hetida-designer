# Power 

## Description
This component takes the base to the power exponent for numeric values, Pandas Series and Pandas DataFrames.

## Inputs
* **base** (Integer, Float, Pandas Series or Pandas DataFrame): Entries must be numeric.
* **exponent** (Integer, Float, Pandas Series or Pandas DataFrame): Entries must be numeric.

## Outputs
* **power** (Integer, Float, Pandas Series or Pandas DataFrame): Base to the power exponent.

## Details
The component calculates the base to the power exponent. 

## Examples
The json input of a typical call of this component with two Pandas Series is
```
{
	"base": {
				"2019-08-01T15:20:12": 2,
				"2019-08-01T15:44:12": 9,
				"2019-08-03T16:20:15": 0,
				"2019-08-05T12:00:34": 1,
                               "2019-08-07T11:01:00": 100
	},
	"exponent": {
				"2019-08-01T15:20:12": 4,
				"2019-08-01T15:44:12": 0.5,
				"2019-08-03T16:20:15": 3.8,
				"2019-08-05T12:00:34": 10000    
	}
}
```
The expected output is
```
	"power": {
			"2019-08-01T15:20:12": 16,
			"2019-08-01T15:44:12": 3,
			"2019-08-03T16:20:15": 0,
			"2019-08-05T12:00:34": 1,
                       "2019-08-07T11:01:00": null  
	}

```

The json input of a typical call of this component with a Float and a Pandas DataFrame is
```
{
	"base": {
			"a": {
             		        "2019-08-01T15:20:12": 1,
				"2019-08-01T15:44:12": null,
				"2019-08-03T16:20:15": 10,
				"2019-08-05T12:00:34": 2.5
             },
                       "b": {
                                "2019-08-01T15:20:12": 4,
				 "2019-08-01T15:44:12": 0,
				 "2019-08-03T16:20:15": 2,
				 "2019-08-05T12:00:34": 7
             }
	},
	"exponent": 2
}
```
The expected output is
```
	"power": {
			"a": {
                               "2019-08-01T15:20:12": 1,
				"2019-08-01T15:44:12": null,
				"2019-08-03T16:20:15": 100,
				"2019-08-05T12:00:34": 6.25
             },
                       "b": {
                               "2019-08-01T15:20:12": 16,
				 "2019-08-01T15:44:12": 0,
				 "2019-08-03T16:20:15": 4,
				 "2019-08-05T12:00:34": 49				 
             }
	}
```
