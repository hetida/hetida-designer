# Time Gap sizes

## Description
This component calculates the sizes of time gaps.

## Inputs
* **data** (Pandas Series): Index must be datetime.

## Outputs
* **gap_sizes** (Pandas Series): Series with the sizes of the gaps between the indices of **data**, expressed in seconds.

## Details
This component calculates the sizes of time gaps between the (datetime) indices of the provided **data**. The value at each index of the result contains the time difference to the foregoing index, expressed in seconds.

The actual values of the provided Series are ignored.

## Examples
The json input of a typical call of this component is
```
{
	"data": {
				"2019-08-01T15:20:00": 1.0,
				"2019-08-01T15:20:15": 7.0,
				"2019-08-01T15:21:00": 5.0,
				"2019-08-01T15:22:05": 4.0,
				"2019-08-01T15:22:06": 2.0
	}
}
```
The expected output is
```
	"gap_sizes": {
				"2019-08-01T15:20:15": 15,
				"2019-08-01T15:21:00": 45,
				"2019-08-01T15:22:05": 65,
				"2019-08-01T15:20:06": 1
	}
```
