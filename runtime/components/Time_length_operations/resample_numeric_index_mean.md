# Resample Numeric Index

## Description
The component resamples data with given distances using mean.

## Inputs
* **data** (Pandas Series or Pandas DataFrame): Indices must be Integer, entries numeric.
* **d** (Integer): The distance between the new indices.

## Outputs
* **resampled** (Pandas Series or Pandas DataFrame): The resampled **data**.

## Details
The component resamples **data** using means on windows. It creates a Pandas Series or Pandas Dataframe with indices in the range of the indices of data with distance **d**.

It equips each index with the average of the numerical observations in a window of size **d** around.

## Examples
The json input of a typical call of this component with a Pandas Series is
```
{
	"data": {
                2: 1.2,
                3: 7.2,
                5: 2.8,
                6: 8.0,
				9: 10.8
	}, 
	"d": 3
}
```
The expected output is
```
	"resampled": {
				2: 4.2,
                5: 6.0,
                8: 9.4
	}
```
