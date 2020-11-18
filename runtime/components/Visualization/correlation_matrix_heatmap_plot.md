# Correlation Matrix Heatmap Plot

## Description
Plotting a correlation matrix as a heatmap.

## Inputs
* **dataframe** (Pandas DataFrame): Correlation will be computed for its columns.

## Outputs
* **plot** (Plotly Json): The generated Plotly Json. This is used by the hetida designer frontend for plotting the results.

## Details
The component generates a correlation matrix heatmap displaying correlation between the dataframe columns.

## Examples
The json input of a typical call of this component is
```
{
	"dataframe": {
    "a": [1,2,3,4,5,6,7],
    "b": [7,6,5,4,3,2,1],
    "c": [3,2,3,4,3,3,9],
    "d": [1,2,4,4,1,1,1],
    "e": [1,3,4,4,0,1,1],
    "f": [2,2,4,4,2,1,1]
    }
}
```
