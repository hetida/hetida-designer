"""Module Docstring of Augmented Dickey-Fuller Test

# Augmented Dickey-Fuller Test

## Description

The component applies the Augmented Dickey-Fuller (ADF) test to a given time series to determine its stationarity. The ADF test is a common statistical method used in time series analysis to test the null hypothesis that a time series is non-stationary due to the presence of a unit root. Understanding the stationarity of a time series is crucial in time series modeling since many models assume or require the data to be stationary.

## Inputs

- **series** (Pandas Series): A Pandas Series containing the time series data. Indices must be datetime objects.
- **alpha** (Float, default value: 0.05): Significance level for the ADF test.

## Outputs

- **result**: A string containing detailed results and interpretation of the ADF test.

## Details

This function is particularly useful for analysts and data scientists who work with time series data and need to determine whether the data is stationary. Stationarity is a key consideration in selecting appropriate time series models and transformations. For example, non-stationary data often require differencing or transformation before fitting ARIMA or other forecasting models.

The Augmented Dickey-Fuller (ADF) test is used to determine the stationarity of a time series. The null hypothesis of the ADF test is that the time series is non-stationary (has a unit root). If the p-value is less than `alpha`, we reject the null hypothesis and infer that the time series is stationary. If the p-value is greater than or equal to `alpha`, we fail to reject the null hypothesis and infer that the time series may have a unit root and is non-stationary. The 'Test Statistic' compares against the 'Critical Values' to determine stationarity at different confidence levels.

## Examples

Example input:
```
{
    "series": {
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
        "2023-09-17T00:00:00.000Z": 400,
        "2023-09-18T00:00:00.000Z": 291,
        "2023-09-19T00:00:00.000Z": 282,
        "2023-09-20T00:00:00.000Z": 316,
        "2023-09-21T00:00:00.000Z": 305,
        "2023-09-22T00:00:00.000Z": 333,
        "2023-09-23T00:00:00.000Z": 398,
        "2023-09-24T00:00:00.000Z": 414
    },
    "alpha": 0.05
}
```
Example output:
```
"result": {
        'Test Statistic': 9.4487,
        'p-value': 1.0,
        'Critical Value (1%)': -4.1378,
        'Critical Value (5%)': -3.155,
        'Critical Value (10%)': -2.7145,
        'Result': 'The series is likely not stationary (fail to reject H0).'
}
```
"""

import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import adfuller
from hetdesrun.runtime.exceptions import ComponentInputValidationException

class SeriesTypeException(ComponentInputValidationException):
    """Exception in case of unexpected value type"""

def perform_adf_test(
    series: pd.Series,
    alpha: float=0.05
):
    """Performs the Augmented Dickey-Fuller test to check the stationarity of a time series.

    Inputs:
    series (Pandas Series): Series containing the time series data. Indices must be datetimes.
    alpha (Float, optional): Significance level. Default is 0.05.

    Outputs:
    result (String): A detailed interpretation of the test results.
    """
    # Parameter validations
    if len(series) == 0:
        raise ComponentInputValidationException(
            "The input series must not be empty!",
            error_code="EmptySeries",
            invalid_component_inputs=["series"],
        )
    
    try:
        series.index = pd.to_datetime(series.index, utc=True)
    except:
        raise SeriesTypeException(
            "Indices of series must be datetime, but are of type "
            + str(series.index.dtype),
            error_code="WrongKindOfSeries",
            invalid_component_inputs=["series"],
        )
    
    if not 0 < alpha < 1:
        raise ComponentInputValidationException(
            "`alpha` must be between 0 and 1",
            error_code=422,
            invalid_component_inputs=["alpha"],
        )

    # Perform ADF test
    adf_result = adfuller(series)
    p_value = np.round(adf_result[1], 4)
    result = {
        "p_value": p_value,
        "Result": 'The series is likely stationary (reject H0).' if p_value < alpha else 'The series is likely not stationary (fail to reject H0).'
    }

    return result

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "series": {"data_type": "SERIES"},
        "alpha": {"data_type": "FLOAT", "default_value": 0.05},
    },
    "outputs": {
        "result": {"data_type": "STRING"},
    },
    "name": "Adf Test",
    "category": "Time Series Analysis",
    "description": "Augmented Dickey-Fuller test to check stationarity",
    "version_tag": "1.0.0",
    "id": "f0860510-1016-4346-80ca-778157935834",
    "revision_group_id": "79e96f98-c317-4d89-b636-a4a1425bbb4d",
    "state": "RELEASED",
}

def main(*, series, alpha=0.05):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    result = perform_adf_test(series=series, alpha=alpha)
    
    return {"result": result}

TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "series",
            "adapter_id": "direct_provisioning",
            "filters": {
                "value": 
"""{
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
    "2023-09-17T00:00:00.000Z": 400,
    "2023-09-18T00:00:00.000Z": 291,
    "2023-09-19T00:00:00.000Z": 282,
    "2023-09-20T00:00:00.000Z": 316,
    "2023-09-21T00:00:00.000Z": 305,
    "2023-09-22T00:00:00.000Z": 333,
    "2023-09-23T00:00:00.000Z": 398,
    "2023-09-24T00:00:00.000Z": 414
}"""
            }
        }
    ]
}