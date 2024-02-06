"""Module Docstring of Kwiatkowski-Phillips-Schmidt-Shin Test

# Kwiatkowski-Phillips-Schmidt-Shin (KPSS) Test for Stationarity

## Description

The component conducts the KPSS test on a given time series to assess its stationarity. The KPSS test is used to test the null hypothesis that the time series is stationary around a deterministic trend (i.e., has no unit root). It is an important tool in time series analysis, complementing other stationarity tests like the Augmented Dickey-Fuller (ADF) test.

## Inputs

- **series** (Pandas Series): A Pandas Series containing the time series data. Indices must be datetime objects.
- **alpha** (Float, default value: 0.05): Significance level for the ADF test.

## Outputs

- **result**: A dictionary containing detailed results and interpretation of the KPSS test.

## Details

This function is crucial for analysts and data scientists working with time series data. It helps determine whether a time series is stationary, which is a key assumption in many time series modeling techniques. Non-stationary data often require transformations, such as differencing or detrending, before being used in forecasting models.

The KPSS (Kwiatkowski-Phillips-Schmidt-Shin) test is used to test the null hypothesis that a time series is stationary. Under the null hypothesis, the time series does not have a unit root and is stationary. A low p-value (typically < 0.05) indicates the series is likely non-stationary and has a unit root. The 'Test Statistic' compares against the 'Critical Values' to determine stationarity at different confidence levels.

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
Example output:
```
{
    "result": "The series is likely trend stationary (fail to reject H0), since p-value (0.1) is larger than alpha (0.05)."
}
```
"""

import pandas as pd
import numpy as np
import warnings
warnings.simplefilter('ignore')
from statsmodels.tsa.stattools import kpss
from hetdesrun.runtime.exceptions import ComponentInputValidationException

class SeriesTypeException(ComponentInputValidationException):
    """Exception in case of unexpected value type"""

def perform_kpss_test(
    series: pd.Series,
    alpha: float=0.05
):
    """Performs the KPSS test to check the trend stationarity of a time series.

    Inputs:
    series (Pandas Series): Series containing the time series data. Indices must be datetimes.
    alpha (Float, optional): Significance level. Default is 0.05.

    Outputs:
    result (Dict): A dictionary containing detailed interpretation of the test results.
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
    
    # Perform KPSS test
    kpss_result = kpss(series, regression='c')
    p_value = np.round(kpss_result[1], 4)

    # Interpretation based on p-value
    if p_value < alpha:
        result = f"The series is likely not trend stationary (reject H0), since p-value ({p_value}) is smaller than alpha ({alpha})."
    else:
        result = f"The series is likely trend stationary (fail to reject H0), since p-value ({p_value}) is larger than alpha ({alpha})."

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
    "name": "KPSS Test",
    "category": "Playground",
    "description": "Kwiatkowski-Phillips-Schmidt-Shin test",
    "version_tag": "1.0.0",
    "id": "fb6ae572-2634-4ad3-adbd-56932ce30788",
    "revision_group_id": "4a9372ee-12ac-41a3-9c5f-654776390232",
    "state": "RELEASED",
}

def main(*, series, alpha=0.05):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    result = perform_kpss_test(series=series, alpha=alpha)
    
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