# Display Table

## Description
Display a DataFrame as table.

## Inputs
* **data** (Pandas DataFrame): The data to be displayed.

## Outputs
* **table** (Plotly Json): The generated Plotly Json. This is used by the hetida designer frontend for plotting the results.

## Details
The component generates a simple table of the provided data using Plotly.

## Examples
The json input of a typical call of this component is
```
{
	"data": {
        "col_1": ["a", "a", "a", "b", "c", "d", "b"],
        "col_2": [2, 3, 2, 4, 4, 4, 4]
    }
}
```
