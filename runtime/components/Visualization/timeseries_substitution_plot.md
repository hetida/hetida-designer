# Timeseries Substitution Plot

## Description
Apply a substitution to a timeseries and plot the results together with ignored, replaced and new values marked.

## Inputs
* **raw_values** (Pandas Series): The original (raw) values. Entries should be numeric and Index should be a DateTime Index.
* **substitution_series** (Pandas Series): The substitution series containing replacement and new values as well as null/NaN values where original values should be ignored.

## Outputs
* **substituted_ts_plot** (Plotly Json): The plot showing the substituted (new) timeseries and additionally marks for the replaced values, ignored values and added values.

## Details
Use this component to see how a substitution is applied. Substitution allows to
* replace existing values
* add new values
* ignore original values

## Examples
The json input of a typical call of this component is
```
{
	"raw_values": {
    "2020-07-01T00:00:00Z": 0,
    "2020-07-02T00:00:00Z": 17,
    "2020-07-03T00:00:00Z": 18,
    "2020-07-04T00:00:00Z": 3,
    "2020-07-04T08:00:00Z": 15,
    "2020-07-04T14:00:00Z": 16,
    "2020-07-04T18:00:00Z": 19,
    "2020-07-07T00:00:00Z": 6,
    "2020-07-08T00:00:00Z": 7
		},
	"substitution_series": {
    "2020-07-02T00:00:00Z": 1.0,
    "2020-07-03T00:00:00Z": 2.0,
    "2020-07-04T08:00:00Z": null,
    "2020-07-04T14:00:00Z": null,
    "2020-07-04T18:00:00Z": null,
    "2020-07-05T00:00:00Z": 4,
    "2020-07-06T00:00:00Z": 5,
    "2020-07-09T00:00:00Z": 18.0,
    "2020-07-10T00:00:00Z": 19.0
    		}
}
```
