# Filter

## Description
This component filters a Pandas Series or a Pandas DataFrame by a boolean Pandas Series.

## Inputs
* **data** (Pandas Series or Pandas DataFrame): The input that should be filtered.
* **filter_series** (Pandas Series): A Pandas Series with boolean entries.

## Outputs
* **filtered** (Pandas Series or Pandas DataFrame): The resulting Pandas Series or Pandas DataFrame. 

## Details
The index of the output contains the indices of data, where filter_series is True. The values of the output are the same as the original ones of data. 

Non boolean entries of filter_series are casted to boolean ones in advance to filtering.

## Examples
The json input of a typical call of this component with two Pandas Series is
```
{
	"data": {
				"2019-08-01T15:20:12": 1.2,
				"2019-08-01T15:44:12": null,
				"2019-08-03T16:20:15": 0.3,
				"2019-08-05T12:00:34": 0.5
	},
	"filter_series": {
				"2019-08-01T15:20:12": true,
				"2019-08-01T15:44:12": true,
				"2019-08-03T16:20:15": false,
				"2020-08-05T12:00:34": true,
				"2020-08-05T12:00:34": false       
	}
}
```
The expected output is
```
	"filtered": {
			"2019-08-01T15:20:12": 1.2,
			"2019-08-01T15:44:12": null
	}

```

The json input of a typical call of this component with a Pandas DataFrame and a Pandas Series is
```
{
	"data": {
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
	"filter_series": {
				"2019-08-01T15:20:12": true,
				"2019-08-01T15:44:12": true,
				"2019-08-03T16:20:15": false,
				"2020-08-05T12:00:34": true,
				"2020-08-05T12:00:34": false       
	}
}
```
The expected output is
```
	"filtered": {
		"a": {
			"2019-08-01T15:20:12": 1.2,
			"2019-08-01T15:44:12": null
		},
		"b": {
			"2019-08-01T15:20:12": 54.4,
			"2019-08-01T15:44:12": 4.3
		}
	}

```

