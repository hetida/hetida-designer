# Sum Columns

## Description
This component adds up values along the column axis.

## Inputs
* **dataframe** (Pandas DataFrame): Entries should be numeric.
* **result_series_name** (String): The name of the resulting series.

## Outputs
* **sum_values** (Pandas Series): Contains the line-wise sums of the dataframe.

## Details
Computes line-wise sums (that is summation along the column axis) of the dataframe.

## Examples 
The json input of a typical call of this component with a Pandas DataFrame is
```
{
    "dataframe": {
			"a": {
           		        "2019-08-01T15:20:12": 1,
				"2019-08-01T15:44:12": null,
				"2019-08-03T16:20:15": 100,
				"2019-08-05T12:00:34": 0
                 },
        		"b": {
                                "2019-08-01T15:20:12": 4,
				 "2019-08-01T15:44:12": 0,
				 "2019-08-03T16:20:15": 25,
				 "2019-08-05T12:00:34": 625
                 }
	},
	"result_series_name" = sum_up_columns
}
```
The expected output is
```
	"sum_values": {
                               "2019-08-01T15:20:12": 5,
				"2019-08-01T15:44:12": null,
				"2019-08-03T16:20:15": 125,
				"2019-08-05T12:00:34": 625
             }
```
