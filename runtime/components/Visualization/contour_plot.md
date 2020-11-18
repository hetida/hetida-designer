# Contour Plot

## Description
This component creates a simple contour plot.

## Inputs
* **x** (Pandas Series): The series with the values for the x coordinates.
* **y** (Pandas Series): The series with the values for the y coordinates.
* **z** (Pandas Series): The function values for the contour plot. Must be of length **len(x)*len(y)**.

## Outputs
* **contour_plot** (Plotly Json): The generated Plotly Json. This is used by the hetida designer frontend for plotting the results.

## Details
Generates a simple contour plot of the **z** values over **x** and **y** with most plot settings set automatically.

## Examples
The json input of a typical call of this component is
```
{
	"x": [1,2,3],
	"y": [1,2,3],
	"z": [1,2,3,4,5,6,0,8,9]
}
```
