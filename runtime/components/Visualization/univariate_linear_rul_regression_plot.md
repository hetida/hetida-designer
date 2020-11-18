# Univariate Linear RUL Regression Result Plot

## Description
Plot results of linear regression for remaining useful life on univariate timeseries.

## Inputs
* **limit_violation_prediction_timestamp** (String): The timestamp at which the limit will be reached.
* **limit** (Float): The limit for RUL, that is the value at which one assumes malfunction to start happening.
* **base_series** (Pandas Series): The input values to train the model. Values should be floats and index should be a datetime index.
* **predictions**: (Pandas Series): The predictions of the model. Values should be floats and index should be a datetime index.

## Outputs
* **rul_regression_result_plot** (Plotly Jsont): The generated Plotly Json. 

## Details
Can be used to plot the results of the corresponding RUL Regression component.
