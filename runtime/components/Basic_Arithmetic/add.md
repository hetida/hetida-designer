# Add

## Description
This component adds numeric values, Pandas Series and Pandas DataFrames.

## Inputs
* **a** (Integer, Float, Pandas Series or Pandas DataFrame): First summand, entries must be numeric.
* **b** (Integer, Float, Pandas Series or Pandas DataFrame): Second summand, entries must be numeric.

## Outputs
* **sum** (Integer, Float, Pandas Series or Pandas DataFrame): The sum of summand a and summand b. 

## Details
The component adds the inputs. 

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
	"sum": {
			"2019-08-01T15:20:12": 3.6,
			"2019-08-01T15:44:12": 2.6,
			"2019-08-03T16:20:15": 4.1,
			"2019-08-05T12:00:34": 5.5,
                       "2019-08-07T11:01:00": null  
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
	"sum": {
			"first": {
                               "2019-08-01T15:20:12": 6.3,
				"2019-08-01T15:44:12": null,
				"2019-08-03T16:20:15": 5.4,
				"2019-08-05T12:00:34": 5.6
             },
            "second": {
                                "2019-08-01T15:20:12": 59.5,
				 "2019-08-01T15:44:12": 9.4,
				 "2019-08-03T16:20:15": 26.1,
				 "2019-08-05T12:00:34": 12.6
             }
	}
```
