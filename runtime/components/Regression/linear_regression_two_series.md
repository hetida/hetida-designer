# Linear Regression two Series

## Description
Linear Regression between two series.

## Inputs
* **y_values** (Pandas Series): Y values for linear regression.
* **x_values** (Pandas Series): X values for linear regression.

## Outputs
* **intercept** (Float): The intercept of the linear model.
* **slope** (Float): The slope of the linear model.
* **preds** (Pandas Series): Prediction values for every value of **x_values**.
* **diffs** (Pandas Series): Differences between **preds** and **y_values**.

## Details
Do an ordinary linear regression of a 1-dimensional variable y on a 1-dimensional variable x.

## Examples
The json input of a typical call of this component is
```
{
    "x_values": {
        "2020-01-01T01:15:27.000Z": 1,
        "2020-01-03T08:20:03.000Z": 2,
        "2020-01-03T08:20:04.000Z": 3,
        "2020-01-03T08:20:05.000Z": 4
    },
    "y_values": {
        "2020-01-01T01:15:27.000Z": 5,
        "2020-01-03T08:20:03.000Z": 6,
        "2020-01-03T08:20:04.000Z": 9,
        "2020-01-03T08:20:05.000Z": 8
    }
}
```

