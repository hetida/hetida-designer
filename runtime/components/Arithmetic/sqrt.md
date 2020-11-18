# Sqrt

## Description
This component calculates the square root for numeric values, Pandas Series and Pandas DataFrames.

## Inputs
* **data** (Integer, Float, Pandas Series or Pandas DataFrame): Entries must be numeric.

## Outputs
* **sqrt** (Integer, Float, Pandas Series or Pandas DataFrame): The square root of data.

## Details
The component calculates the square root. 

## Examples
The json input of a typical call of this component with a Pandas Series is
```
{
	"data": {
				"2019-08-01T15:20:12": 4,
				"2019-08-01T15:44:12": 9,
				"2019-08-03T16:20:15": 0,
				"2019-08-05T12:00:34": 1,
             			"2019-08-07T11:01:00": 100
	}
}
```
The expected output is
```
	"sqrt": {
			"2019-08-01T15:20:12": 2,
			"2019-08-01T15:44:12": 3,
			"2019-08-03T16:20:15": 0,
			"2019-08-05T12:00:34": 1,
                       "2019-08-07T11:01:00": 10  
	}

```

The json input of a typical call of this component with a Pandas DataFrame is
```
{
    "data": {
			"a": {
           		        "2019-08-01T15:20:12": 1,
				"2019-08-01T15:44:12": null,
				"2019-08-03T16:20:15": 100,
				"2019-08-05T12:00:34": 6.25
             },
        		"b": {
                                "2019-08-01T15:20:12": 4,
				 "2019-08-01T15:44:12": 0,
				 "2019-08-03T16:20:15": 25,
				 "2019-08-05T12:00:34": 625
             }
	}
}
```
The expected output is
```
	"sqrt": {
			"a": {
                               "2019-08-01T15:20:12": 1,
				"2019-08-01T15:44:12": null,
				"2019-08-03T16:20:15": 10,
				"2019-08-05T12:00:34": 2.5
             },
          	        "b": {
                	         "2019-08-01T15:20:12": 2,
				 "2019-08-01T15:44:12": 0,
				 "2019-08-03T16:20:15": 5,
				 "2019-08-05T12:00:34": 25
             }
	}
```
