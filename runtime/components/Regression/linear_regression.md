# Linear Regression

## Description
Linear Regression on dataframes of values.

## Inputs
* **y_values** (Pandas DataFrame): Y values for linear regression.
* **x_values** (Pandas DataFrame): X values for linear regression.

## Outputs
* **intercept** (Pandas Series): The intercept values of the linear model (one for each column in **y_values**).
* **slope** (Pandas DataFrame): The slope of the linear model: For every column of **y_values** a column of slope values (one line for each colum of **x_values**).
* **preds** (Pandas DataFrame): Prediction values for every line of **x_values**.
* **diffs** (Pandas DataFrame): Differences between **preds** and **y_values**.
* **trained_model** (sklearn_linear_models_LinearRegresion): Trained sklearn model object.

## Details
Do an ordinary linear regression on data of arbitrary dimension.

## Examples
The json input of a typical call of this component is
```
{
    "x_values": {
        "a": {
            "2019-08-01T15:45:36.000Z": 1,
            "2019-08-02T11:33:41.000Z": 2
        },
        "b": {
            "2019-08-01T15:45:36.000Z": 1.3,
            "2019-08-02T11:33:41.000Z": 2.8
        }
    },
    "y_values": {
        "a": {
            "2019-08-01T15:45:36.000Z": 1.2,
            "2019-08-02T11:33:41.000Z": 2.3
        },
        "b": {
            "2019-08-01T15:45:36.000Z": 1,
            "2019-08-02T11:33:41.000Z": 2.8
        }
    }
}
```

