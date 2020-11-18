# Round

## Description
This component rounds values with specified number of decimals.

## Inputs
* **data** (Integer, Float, Pandas Series or Pandas DataFrame): Entries must be numeric.
* **decimals** (Integer): Number of decimals.

## Outputs
* **rounded** (Integer, Float, Pandas Series or Pandas DataFrame): Rounded data.

## Details
This component rounds values with specified number of decimals.

## Examples
The json input of a typical call of this component with a Pandas Series is
```
{
	"data": {
				"2019-08-01T15:20:12": 4.54154,
				"2019-08-01T15:44:12": -9.4854,
				"2019-08-03T16:20:15": 0.420,
				"2019-08-05T12:00:34": null,
                               "2019-08-07T11:01:00": 100.1202
	},
	"decimals" = 2
}
```
The expected output is
```
	"rounded": {
				"2019-08-01T15:20:12": 4.54,
				"2019-08-01T15:44:12": -9.49,
				"2019-08-03T16:20:15": 0.42,
				"2019-08-05T12:00:34": null,
                               "2019-08-07T11:01:00": 100.12
	}
```
