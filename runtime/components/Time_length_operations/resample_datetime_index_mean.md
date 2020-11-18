# Resample Datetime Index using Mean

## Description
The component resamples data for some time frequency by taking mean values.

## Inputs
* **data** (Pandas Series or Pandas DataFrame): Indices must be datetime.
* **t** (String): The distance between the new indices. For example, 'ms', '15s', 'min', '2h' or 'd'.

## Outputs
* **resampled** (Pandas Series or Pandas DataFrame): The resampled **data**.

## Details
The component resamples **data**. It creates a Pandas Series or Pandas Dataframe with indices in the range of the indices of **data** with the distance t. 

It equippes each index with the average numerical observations in a window of size **t**.

## Examples
The json input of a typical call of this component with a Pandas Series is
```
{
	"data": {
                "2019-08-01T00:00:00": 1.2,
                "2019-08-01T15:20:14": 7.2,
                "2019-08-03T00:00:00": 0.3,
                "2019-08-04T15:20:20": 0.5,
	}, 
	"t": "d"
}
```
The expected output is
```
	"resampled": {
				"2019-08-01T00:00:00": 4.2,
                "2019-08-02T00:00:00": null,
				"2019-08-03T00:00:00": 0.3,
                "2019-08-04T00:00:00": 0.5
	}
```
