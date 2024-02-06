"""Module Docstring of SARIMAX Model Training

# SARIMAX Model Training

## Description

The function is tailored for training a Seasonal Autoregressive Integrated Moving Average with eXogenous variables (SARIMAX) model on time series data. SARIMAX is a powerful and versatile statistical modeling approach used for forecasting time series data that exhibit both non-seasonal and seasonal patterns, while also accounting for the influence of external or exogenous variables.

This function offers the ability to model time series data with considerations for autoregressive (AR), integrated (I), and moving average (MA) components, along with their seasonal counterparts. It also incorporates the impact of exogenous variables, which are external factors that may influence the dependent variable. This makes SARIMAX an essential tool in fields like finance, economics, environmental science, and any domain where external factors significantly impact the time series being forecasted.

## Inputs

- **df** (Pandas DataFrame): The DataFrame containing the time series data.
- **variable** (String): The name of the column representing the dependent variable under consideration.
- **order** (Tuple): The (p, d, q) order of the model for the AR parameters, differences, and MA parameters.
- **seasonal_order** (Tuple): The (P, D, Q, S) seasonal order of the model.
- **exog_variables** (List[String], default value: None): List of column names representing exogenous variables, if any.
- **enforce_stationarity** (Bool, default value: False): Whether or not to enforce stationarity
- **enforce_invertibility** (Bool, default value: False): Whether or not to enforce invertibility
- **maxiter** (Integer, default value: 50): The maximum number of iterations for model fitting
- **method** (String, default value: "nm"): The optimization method to use. Possible methods are: ['nm', 'bfgs', 'lbfgs', 'powell', 'cg', 'ncg']
- **initialization** (String, default value: "approximate_diffuse"): Initialization method for the ARMA parameters. Possible initializations are ['approximate_diffuse', 'stationary', 'known']

## Outputs

- **sarimalx_model_fit** (Object): The fitted SARIMAX model.
- **runtime** (Float): The runtime in seconds.

## Details

This function is particularly useful for forecasting tasks where external variables play a significant role in determining the trends and patterns of the target variable. By including exogenous factors, SARIMAX models provide a more comprehensive view of the data, leading to potentially more accurate and insightful forecasts.

## Example 

Example input:
```
{
    "train": {
        "value": {
            "2023-09-04T00:00:00.000Z": 201,
            "2023-09-05T00:00:00.000Z": 194,
            "2023-09-06T00:00:00.000Z": 281,
            "2023-09-07T00:00:00.000Z": 279,
            "2023-09-08T00:00:00.000Z": 375,
            "2023-09-09T00:00:00.000Z": 393,
            "2023-09-10T00:00:00.000Z": 390,
            "2023-09-11T00:00:00.000Z": 220,
            "2023-09-12T00:00:00.000Z": 262,
            "2023-09-13T00:00:00.000Z": 312,
            "2023-09-14T00:00:00.000Z": 277,
            "2023-09-15T00:00:00.000Z": 332,
            "2023-09-16T00:00:00.000Z": 401,
            "2023-09-17T00:00:00.000Z": 400
        },
        "exog_weekday": {
            "2023-09-04T00:00:00.000Z": 1.0,
            "2023-09-05T00:00:00.000Z": 1.02,
            "2023-09-06T00:00:00.000Z": 1.13,
            "2023-09-07T00:00:00.000Z": 1.13,
            "2023-09-08T00:00:00.000Z": 1.37,
            "2023-09-09T00:00:00.000Z": 1.45,
            "2023-09-10T00:00:00.000Z": 1.48,
            "2023-09-11T00:00:00.000Z": 1.0,
            "2023-09-12T00:00:00.000Z": 1.02,
            "2023-09-13T00:00:00.000Z": 1.13,
            "2023-09-14T00:00:00.000Z": 1.13,
            "2023-09-15T00:00:00.000Z": 1.37,
            "2023-09-16T00:00:00.000Z": 1.45,
            "2023-09-17T00:00:00.000Z": 1.48
        }
    },
    "variable": "value",
    "order": (0,0,1),
    "seasonal_order": (1,0,0,7),
    "exog_variables": ["exog_weekday"],
    "enforce_stationarity": False,
    "enforce_invertibility": False,
    "maxiter": 50,
    "method": "nm",
    "initialization": "approximate_diffuse"
}
```
"""

import pandas as pd
import numpy as np
import time
from typing import List
from statsmodels.tsa.statespace.sarimax import SARIMAX
from hetdesrun.runtime.exceptions import ComponentInputValidationException

def train_sarimax_model(
    df: pd.DataFrame,
    variable: str,
    order: List[int],
    seasonal_order: List[int],
    exog_variables: List[str] = None,
    enforce_stationarity: bool = False,
    enforce_invertibility: bool = False,
    maxiter: int = 50,
    method: str = 'nm',
    initialization: str = 'approximate_diffuse'
):
    """Trains a SARIMAX model on the given time series data.

    Inputs:
    df (Pandas DataFrame): The DataFrame containing the time series data.
    variable (String): The name of the column representing the dependent variable.
    order (List[Int]): The (p, d, q) order of the model for the AR parameters, differences, and MA parameters.
    seasonal_order (List[Int]): The (P, D, Q, S) seasonal order of the model.
    exog_variables (List[String]): List of column names representing exogenous variables, if any.
    enforce_stationarity (Bool, optional): Whether or not to enforce stationarity. Default is False.
    enforce_invertibility (Bool, optional): Whether or not to enforce invertibility. Default is False.
    maxiter (Int, optional): The maximum number of iterations for model fitting. Default is 50.
    method (String, optional): The optimization method to use. Default is 'nm' (Nelder-Mead).
    initialization (String, optional): Initialization method for the ARMA parameters. Default is 'approximate_diffuse'.
    
    Outputs:
    sarimax_model_fit (Object): The trained SARIMAX model.
    runtime (Float): The runtime of the component. 
    """
    # Parameter validations
    if len(df) == 0:
        raise ComponentInputValidationException(
            "The input series must not be empty!",
            error_code="EmptySeries",
            invalid_component_inputs=["df"],
        )
    
    try:
        df.index = pd.to_datetime(df.index, utc=True)
    except:
        raise SeriesTypeException(
            "Indices of series must be datetime, but are of type "
            + str(series.index.dtype),
            error_code="WrongKindOfSeries",
            invalid_component_inputs=["series"],
        )
    
    valid_methods = ['nm', 'bfgs', 'lbfgs', 'powell', 'cg', 'ncg']
    valid_initializations = ['approximate_diffuse', 'stationary', 'known']

    if variable not in df.columns:
        raise ComponentInputValidationException(
            f"Dependent variable '{variable}' not found in DataFrame",
            error_code=422,
            invalid_component_inputs=["variable"],
        )
    if exog_variables:
        for var in exog_variables:
            if var not in df.columns:
                raise ComponentInputValidationException(
                    f"Exogenous variable '{var}' not found in DataFrame",
                    error_code=422,
                    invalid_component_inputs=["exog_variables"],
                )
    if not all(isinstance(n, int) for n in order) or len(order) != 3:
        raise ComponentInputValidationException(
            "Order must be a list of three integers [p, d, q]",
            error_code=422,
            invalid_component_inputs=["order"],
        )
    if not all(isinstance(n, int) for n in seasonal_order) or len(seasonal_order) != 4:
        raise ComponentInputValidationException(
            "Seasonal order must be a list of four integers [P, D, Q, S]",
            error_code=422,
            invalid_component_inputs=["order"],
        )
    if method not in valid_methods:
        raise ComponentInputValidationException(
            f"'{method}' is not a valid optimization method. Choose from {valid_methods}",
            error_code=422,
            invalid_component_inputs=["method"],
        )
    if initialization not in valid_initializations:
        raise ComponentInputValidationException(
            f"'{initialization}' is not a valid initialization method. Choose from {valid_initializations}",
            error_code=422,
            invalid_component_inputs=["method"],
        )

    df = df.sort_index()
    
    # Measure start time
    start_time = time.time()
    
    # Train SARIMA model
    sarimax_model = SARIMAX(
        endog=df[variable], 
        order=order, 
        seasonal_order=seasonal_order,
        exog=df[exog_variables] if exog_variables else None,
        initialization=initialization,
        enforce_stationarity=enforce_stationarity,
        enforce_invertibility=enforce_invertibility
    )
    sarimax_model_fit = sarimax_model.fit(disp=False, maxiter=maxiter, method=method)
    
    # Measure end time
    end_time = time.time()
    runtime = np.round(end_time - start_time, 2)
    
    return sarimax_model_fit, runtime

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "df": {"data_type": "DATAFRAME"},
        "variable": {"data_type": "STRING"},
        "order": {"data_type": "ANY"},
        "seasonal_order": {"data_type": "ANY"},
        "exog_variables": {"data_type": "ANY", "default_value": None},
        "enforce_stationarity": {"data_type": "BOOLEAN", "default_value": "False"},
        "enforce_invertibility": {"data_type": "BOOLEAN", "default_value": "False"},
        "maxiter": {"data_type": "INT", "default_value": "50"},
        "method": {"data_type": "STRING", "default_value": "nm"},
        "initialization": {"data_type": "STRING", "default_value": "approximate_diffuse"},
    },
    "outputs": {
        "trained_model": {"data_type": "ANY"},
        "runtime": {"data_type": "FLOAT"},
    },
    "name": "Train SARIMAX Model",
    "category": "Playground",
    "description": "Training some SARIMAX model",
    "version_tag": "1.0.0",
    "id": "8cbd19f3-13b5-4702-aad2-85b6e616b66e",
    "revision_group_id": "7e3e003e-4a56-41df-94b3-51b50900ac87",
    "state": "RELEASED",
}

def main(*, df, variable, order, seasonal_order, exog_variables=None, enforce_stationarity=False, enforce_invertibility=False, maxiter=50, method="nm", initialization="approximate_diffuse"):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    trained_model, time = train_sarimax_model(
        df=df, 
        variable=variable,
        order=order,
        seasonal_order=seasonal_order,
        exog_variables=exog_variables,
        enforce_stationarity=enforce_stationarity,
        enforce_invertibility=enforce_invertibility,
        maxiter=maxiter,
        method=method,
        initialization=initialization
    )

    return {"trained_model": trained_model, "runtime": time}

TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "df",
            "adapter_id": "direct_provisioning",
            "filters": {
                "value": 
"""{
    "value": {
        "2023-09-04T00:00:00.000Z": 201,
        "2023-09-05T00:00:00.000Z": 194,
        "2023-09-06T00:00:00.000Z": 281,
        "2023-09-07T00:00:00.000Z": 279,
        "2023-09-08T00:00:00.000Z": 375,
        "2023-09-09T00:00:00.000Z": 393,
        "2023-09-10T00:00:00.000Z": 390,
        "2023-09-11T00:00:00.000Z": 220,
        "2023-09-12T00:00:00.000Z": 262,
        "2023-09-13T00:00:00.000Z": 312,
        "2023-09-14T00:00:00.000Z": 277,
        "2023-09-15T00:00:00.000Z": 332,
        "2023-09-16T00:00:00.000Z": 401,
        "2023-09-17T00:00:00.000Z": 400
    },
    "exog_weekday": {
        "2023-09-04T00:00:00.000Z": 1.0,
        "2023-09-05T00:00:00.000Z": 1.02,
        "2023-09-06T00:00:00.000Z": 1.13,
        "2023-09-07T00:00:00.000Z": 1.13,
        "2023-09-08T00:00:00.000Z": 1.37,
        "2023-09-09T00:00:00.000Z": 1.45,
        "2023-09-10T00:00:00.000Z": 1.48,
        "2023-09-11T00:00:00.000Z": 1.0,
        "2023-09-12T00:00:00.000Z": 1.02,
        "2023-09-13T00:00:00.000Z": 1.13,
        "2023-09-14T00:00:00.000Z": 1.13,
        "2023-09-15T00:00:00.000Z": 1.37,
        "2023-09-16T00:00:00.000Z": 1.45,
        "2023-09-17T00:00:00.000Z": 1.48
    }
}
"""
            }
        },
        {
            "workflow_input_name": "variable",
            "adapter_id": "direct_provisioning",
            "filters": {
                "value": "value"
            }
        },
        {
            "workflow_input_name": "order",
            "adapter_id": "direct_provisioning",
            "filters": {
                "value": "[0,0,1]"
            }
        },
        {
            "workflow_input_name": "seasonal_order",
            "adapter_id": "direct_provisioning",
            "filters": {
                "value": "[1,0,0,7]"
            }
        },
    ]
}