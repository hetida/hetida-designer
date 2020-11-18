# Modulo

## Description
This component calculates the modulo of the given input.

## Inputs
* **a** (Integer, Float, Pandas Series or Pandas DataFrame): Entries must be numeric.
* **b** (Integer)

## Outputs
* **modulo** (Integer, Float, Pandas Series or Pandas DataFrame): The result of a mod b.

## Details
This component calculates a mod b.

## Examples
The json input of a typical call of this component with a Pandas Series is
```
{
		"a": {
				"2019-08-01T15:20:12": 4.0,
				"2019-08-01T15:44:12": 9.5,
				"2019-08-03T16:20:15": 0.420,
				"2019-08-05T12:00:34": null,
           			"2019-08-07T11:01:00": -10
	},
				"b" = 3
}
```
The expected output is
```
	"modulo": {
				"2019-08-01T15:20:12": 1,
				"2019-08-01T15:44:12": 0.5,
				"2019-08-03T16:20:15": 0.42,
				"2019-08-05T12:00:34": null,
             			"2019-08-07T11:01:00": 2
	}

```
