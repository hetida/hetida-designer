# 2D Grid Generator

## Description
Generates 2 dimensional grids, useful for visualization.

## Inputs
* **x_min** (Float): The minimum x value.
* **x_max** (Float): The maximum x value.
* **y_min** (Float): The minimum y value.
* **y_max** (Float): The maximum y value.
* **n** (Integer): The number of values in the corresponding grid will be n^2.

## Outputs
* **x_values** (Pandas Series): All x values of the generated grid as one long series (repeated for each row).
* **y_values** (Pandas Series): All y values of the generated grid as one long series (repeated for each column).
* **x_indices** (Pandas Series): The x values of the generated grid (only once).
* **y_indices** (Pandas Series): The y values of the generated grid (only once).

## Details
Generates an n times n sized grid of values evenly spaced out between minimum and maximum values for each axis. This is useful for visualization, especially to get data for contour plots.
