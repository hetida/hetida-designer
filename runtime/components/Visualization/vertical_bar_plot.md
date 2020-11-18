# Vertical Bar Plot

## Description
Plotting a series of values as vertical bars.

## Inputs
* **series** (Pandas Series): Entries must be numeric and Index should consist of what you may want to see below the bars on the x axis, e.g. strings denoting the bars.

## Outputs
* **plot** (Plotly Json): The generated Plotly Json. This is used by the hetida designer frontend for plotting the results.

## Details
The component plots the incoming series of values as vertical bars.

## Examples
The json input of a typical call of this component is
```
{
	"series": {
		"NRW": 2,
		"BW": 10,
		"HE": 9.8,
		"BAY": 0.2,
		"TH": 3.5,
		"BER": 4.7,
		"NS": 4.2,
		"BRE": 1.0,
		"HAM": 11.2,
		"MV": 12.9
		}
}
```
