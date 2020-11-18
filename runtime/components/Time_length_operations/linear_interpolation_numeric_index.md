# Linear Index Interpolation

## Description
The component calculates the linear interpolation of the input for some distance.

## Inputs
* **data** (Pandas Series or Pandas DataFrame): Indices must be Integer, entries numeric and data sorted by its index.
* **d** (Integer): The distance between the indices of the interpolated **data**.

## Outputs
* **interpolation** (Pandas Series or Pandas DataFrame): The linear interpolation of **data**. 

## Details
The component calculates the linear interpolation of the input for some distance in the interval given by the smallest and biggest index of data.

## Examples
The json input of a typical call of this component with a Pandas Series is
```
{
	"data": {
                2: 1.2,
                3: 7.2,
                5: 2.8,
                6: 4.8,
				9: 10.8
	}, 
	"d": 2
}
```
The expected output is
```
	"interpolation": {
				2.0: 1.2
				4.0: 5.0
				6.0: 4.8
				8.0: 8.8
	}
```
