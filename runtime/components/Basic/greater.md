# Greater

## Description
This component checks if left is greater than right.

## Inputs
* **left** (Integer, Float, Boolean, Pandas Series or Pandas DataFrame): Entries must be numeric. 
* **right** (Integer, Float, Boolean, Pandas Series or Pandas DataFrame): Entries must be numeric.

## Outputs
* **result** (Boolean, Pandas Series or Pandas DataFrame): The boolean result of the comparison.

## Details
The component checks if left is greater than right.

## Examples
The json input of a typical call of this component where left is a Pandas Series and right is numeric is
```
{
	"left": {
				"2019-08-01T15:20:12": 1.2,
				"2019-08-01T15:44:12": null,
				"2019-08-03T16:20:15": 0.3,
				"2019-08-05T12:00:34": 0.5
	},
	"right": 1
}
```
The expected output is
```
	"result": {
		"2019-08-01T15:20:12": true,
		"2019-08-01T15:44:12": false,
		"2019-08-03T16:20:15": false,
		"2019-08-05T12:00:34": false
	}
```

The json input of a typical call of this component where left is a Pandas DataFrame and right is numeric is
```
{
	"left": {
			"a": {
                               "2019-08-01T15:20:12": 1.2,
				"2019-08-01T15:44:12": null,
				"2019-08-03T16:20:15": 0.3,
				"2019-08-05T12:00:34": 0.5
             },
            "b": {
                                "2019-08-01T15:20:12": 54.4,
				 "2019-08-01T15:44:12": 4.3,
				 "2019-08-03T16:20:15": 21.0,
				 "2019-08-05T12:00:34": 7.5
             }
	},
	"right": 0.8
}
```
The expected output is
```
	"result": {
			"a": {
				"2019-08-01T15:20:12": true,
				"2019-08-01T15:44:12": false,
				"2019-08-03T16:20:15": false,
				"2019-08-05T12:00:34": false
			},
			"b": {
				"2019-08-01T15:20:12": true,
				"2019-08-01T15:44:12": true,
				"2019-08-03T16:20:15": true,
				"2019-08-05T12:00:34": true
			}
		}


```

The json input of a typical call of this component where both left and right are Pandas Series is
```
{
	"left": {
				"2019-08-01T15:20:12": 1.2,
				"2019-08-01T15:44:12": null,
				"2019-08-03T16:20:15": 0.3,
				"2019-08-05T12:00:34": 0.5
	},
	"right": {
				"2019-08-01T15:20:12": 1.0,
				"2019-08-01T15:44:12": 27,
				"2019-08-03T16:20:15": 3.6,
				"2020-08-05T12:00:34": 17,
				"2021-08-05T12:00:34": null       
	}
}
```
The expected output is
```
	"result": {
			"2019-08-01T15:20:12": true,
			"2019-08-01T15:44:12": false,
			"2019-08-03T16:20:15": false,
			"2019-08-05T12:00:34": false,
			"2020-08-05T12:00:34": false,
			"2021-08-05T12:00:34": false
		}
```
