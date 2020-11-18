# nth root

## Description
This component calculates the nth root for numeric values, Pandas Series and Pandas DataFrames.

## Inputs
* **data** (Integer, Float, Pandas Series or Pandas DataFrame): Entries must be numeric.
* **n** (Integer, Float, Pandas Series or Pandas DataFrame): Entries must be numeric.

## Outputs
* **root** (Integer, Float, Pandas Series or Pandas DataFrame): The nth root of data.

## Details
The component calculates the nth root. 

## Examples
The json input of a typical call of this component with a Pandas Series is
```
{
	"data": {
				"2019-08-01T15:20:12": 8,
				"2019-08-01T15:44:12": 27,
				"2019-08-03T16:20:15": 0,
				"2019-08-05T12:00:34": 1,
         		        "2019-08-07T11:01:00": 1000
	},
	"n": 3
}
```
The expected output is
```
	"root": {
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
