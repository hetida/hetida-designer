# Pie Chart Plot

## Description
Plotting a pie chart.

## Inputs
* **dataframe** (Pandas DataFrame): The input data. 
* **value_column** (String): The column of which the values will be summed up in order to determine the groups relative fractions of this sum. 
	This column of dataframe should consist of float values.
* **group_column** (String): The column used to group the values. 
	This should be a string valued or a categorical column.

## Outputs
* **plot** (Plotly Json): The generated Plotly Json. This is used by the hetida designer frontend for plotting the results

## Details
The component generates a Pie chart using Plotly.

## Examples
The json input of a typical call of this component is
```
{
	"group_column": "group",
	"value_column": "value",
	"dataframe": {
    "group": ["a", "a", "a", "b", "c", "d", "b"],
    "value": [2, 3, 2, 4, 4, 4, 4]
    }
}
```
