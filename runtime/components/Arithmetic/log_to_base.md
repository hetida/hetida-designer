# Log to base

## Description
This component calculates the logarithm to some given base.

## Inputs
* **base** (Integer, Float, Pandas Series or Pandas DataFrame): Entries must be numeric.
* **data** (Integer, Float, Pandas Series or Pandas DataFrame): Entries must be numeric.

## Outputs
* **log** (Integer, Float, Pandas Series or Pandas DataFrame): Logarithm of data to the given base.

## Details
The component calculates the logarithm of data to some given base. 

## Examples
The json input of a typical call of this component with two Pandas Series is
```
{
	"base": {
				"2019-08-01T15:20:12": 2,
				"2019-08-01T15:44:12": 3,
				"2019-08-03T16:20:15": 4,
				"2019-08-05T12:00:34": 10,
                		"2019-08-07T11:01:00": 100
	},
	"data": {
				"2019-08-01T15:20:12": 16,
				"2019-08-01T15:44:12": 243,
				"2019-08-03T16:20:15": 2,
				"2019-08-05T12:00:34": 10000    
	}
}
```
The expected output is
```
	"log": {
			"2019-08-01T15:20:12": 4,
			"2019-08-01T15:44:12": 5,
			"2019-08-03T16:20:15": 0.5,
			"2019-08-05T12:00:34": 4,
          		"2019-08-07T11:01:00": null  
	}

```

The json input of a typical call of this component with a Float and a Pandas DataFrame is
```
{
    "base": 2
    "data": {
				"a": {
                			"2019-08-01T15:20:12": 1,
					"2019-08-01T15:44:12": null,
					"2019-08-03T16:20:15": 16,
					"2019-08-05T12:00:34": 2
				},
				"b": {
					"2019-08-01T15:20:12": 4,
					"2019-08-01T15:44:12": 8,
					"2019-08-03T16:20:15": 2,
					"2019-08-05T12:00:34": 2
				}
	}
}
```
The expected output is
```
	"log": {
			"a": {
               		"2019-08-01T15:20:12": 0,
				"2019-08-01T15:44:12": null,
				"2019-08-03T16:20:15": 8,
				"2019-08-05T12:00:34": 1
             },
            "b": {
                		 "2019-08-01T15:20:12": 2,
				 "2019-08-01T15:44:12": 3,
				 "2019-08-03T16:20:15": 1,
				 "2019-08-05T12:00:34": 1
             }
	}
```
