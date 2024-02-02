"""Module Docstring of Time Series Decomposition

# Time Series Decomposition

## Description

This function decomposes a time series into its constituent components: *trend*, *seasonality*, and *residuals*. It's essential for understanding and modeling time series data, as it helps to identify underlying patterns and structures. This decomposition is crucial for tasks like forecasting, anomaly detection, and better understanding the time series behavior.

## Inputs

- **series** (Pandas Series):
    The time series data to be decomposed. The index must be of the datetime data type.

- **model** (String, default value: "additive"):
    The type of decomposition model ('additive' or 'multiplicative'). The default is 'additive'.

- **freq** (Int, default value: None):
    The frequency of the time series. If not provided, it will be inferred from the data.

## Outputs

- **decomposed_series** (Pandas DataFrame):
    A DataFrame containing the original data and the decomposed components: trend, seasonal, and residuals.

## Details

This function is used for analyzing time series data. The decomposition allows for a detailed understanding of the time series by isolating and examining its different components. It's particularly useful for:
- **Forecasting**: Understanding trends and seasonal patterns can improve forecasting accuracy.
- **Anomaly Detection**: Residuals can help identify unusual data points that don't follow the typical pattern.
- **Data Understanding**: It provides insights into the data, like identifying the presence of seasonality or trends over time.

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
    "model": "additive",
    "freq": 7
}
```
Example output:
```
"decomposed_series": {
    "__hd_wrapped_data_object__":"DATAFRAME",
    "__metadata__":{},
    "__data__":{
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
            "2023-09-17T00:00:00.000Z": 400,
            "2023-09-18T00:00:00.000Z": 291,
            "2023-09-19T00:00:00.000Z": 282,
            "2023-09-20T00:00:00.000Z": 316,
            "2023-09-21T00:00:00.000Z": 305,
            "2023-09-22T00:00:00.000Z": 333,
            "2023-09-23T00:00:00.000Z": 398,
            "2023-09-24T00:00:00.000Z": 414
        },
        "trend": {
            "2023-09-04T00:00:00.000Z": null,
            "2023-09-05T00:00:00.000Z": null,
            "2023-09-06T00:00:00.000Z": null,
            "2023-09-07T00:00:00.000Z": 301.8571,
            "2023-09-08T00:00:00.000Z": 304.5714,
            "2023-09-09T00:00:00.000Z": 314.2857,
            "2023-09-10T00:00:00.000Z": 318.7143,
            "2023-09-11T00:00:00.000Z": 318.4286,
            "2023-09-12T00:00:00.000Z": 312.2857,
            "2023-09-13T00:00:00.000Z": 313.4286,
            "2023-09-14T00:00:00.000Z": 314.8571,
            "2023-09-15T00:00:00.000Z": 325.0,
            "2023-09-16T00:00:00.000Z": 327.8571,
            "2023-09-17T00:00:00.000Z": 328.4286,
            "2023-09-18T00:00:00.000Z": 332.4286,
            "2023-09-19T00:00:00.000Z": 332.5714,
            "2023-09-20T00:00:00.000Z": 332.1429,
            "2023-09-21T00:00:00.000Z": 334.1429,
            "2023-09-22T00:00:00.000Z": null,
            "2023-09-23T00:00:00.000Z": null,
            "2023-09-24T00:00:00.000Z": null 
        },
        "seasonal": {
            "2023-09-04T00:00:00.000Z": -73.7823,
            "2023-09-05T00:00:00.000Z": -54.2823,
            "2023-09-06T00:00:00.000Z": -12.6395,
            "2023-09-07T00:00:00.000Z": -33.8061,
            "2023-09-08T00:00:00.000Z": 34.8605,
            "2023-09-09T00:00:00.000Z": 72.0748,
            "2023-09-10T00:00:00.000Z": 67.5748,
            "2023-09-11T00:00:00.000Z": -73.7823,
            "2023-09-12T00:00:00.000Z": -54.2823,
            "2023-09-13T00:00:00.000Z": -12.6395,
            "2023-09-14T00:00:00.000Z": -33.8061,
            "2023-09-15T00:00:00.000Z": 34.8605,
            "2023-09-16T00:00:00.000Z": 72.0748,
            "2023-09-17T00:00:00.000Z": 67.5748,
            "2023-09-18T00:00:00.000Z": -73.7823,
            "2023-09-19T00:00:00.000Z": -54.2823,
            "2023-09-20T00:00:00.000Z": -12.6395,
            "2023-09-21T00:00:00.000Z": -33.8061,
            "2023-09-22T00:00:00.000Z": 34.8605,
            "2023-09-23T00:00:00.000Z": 72.0748,
            "2023-09-24T00:00:00.000Z": 67.5748
        },
        "residual": {
            "2023-09-04T00:00:00.000Z": null,
            "2023-09-05T00:00:00.000Z": null,
            "2023-09-06T00:00:00.000Z": null,
            "2023-09-07T00:00:00.000Z": 10.949,
            "2023-09-08T00:00:00.000Z": 35.568,
            "2023-09-09T00:00:00.000Z": 6.6395,
            "2023-09-10T00:00:00.000Z": 3.7109,
            "2023-09-11T00:00:00.000Z": -24.6463,
            "2023-09-12T00:00:00.000Z": 3.9966,
            "2023-09-13T00:00:00.000Z": 11.2109,
            "2023-09-14T00:00:00.000Z": -4.051,
            "2023-09-15T00:00:00.000Z": -27.8605,
            "2023-09-16T00:00:00.000Z": 1.068,
            "2023-09-17T00:00:00.000Z": 3.9966,
            "2023-09-18T00:00:00.000Z": 32.3537,
            "2023-09-19T00:00:00.000Z": 3.7109,
            "2023-09-20T00:00:00.000Z": -3.5034,
            "2023-09-21T00:00:00.000Z": 4.6633,
            "2023-09-22T00:00:00.000Z": null,
            "2023-09-23T00:00:00.000Z": null,
            "2023-09-24T00:00:00.000Z": null
        }
    }
}
```
"""

import pandas as pd
import numpy as np
from statsmodels.tsa.seasonal import seasonal_decompose
from hetdesrun.runtime.exceptions import ComponentInputValidationException

class SeriesTypeException(ComponentInputValidationException):
    """Exception in case of unexpected value type"""

def decompose_time_series(
    series: pd.Series,
    model: str='additive', 
    freq: int=None
) -> pd.DataFrame:
    """Decompose some time series into its trend, seasonality, and residuals components.

    Inputs:
    series (Pandas Series): Time series data. The index must be datetime.
    model (String, optional): Type of decomposition model ('additive' or 'multiplicative'). Default is 'additive'.
    freq (Integer, optional): Frequency of the time series. If not provided, it will be inferred.

    Outputs:
    df (Pandas DataFrame: DataFrame containing the original data, trend, seasonal, and residual components.
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
    
    if model not in ['additive', 'multiplicative']:
        raise ComponentInputValidationException(
            "model must be 'additive' or 'multiplicative'",
            error_code=422,
            invalid_component_inputs=["model"],
        )
    
    if freq and (not isinstance(freq, int) or freq*2 > len(series)):
        raise ComponentInputValidationException(
            "freq needs to be an integer smaller than half the length of the series",
            error_code=422,
            invalid_component_inputs=["freq"],
        )

    series = series.sort_index().dropna()

    decomposition = seasonal_decompose(series, model=model, period=freq)

    # Combine the components with the original data
    decomposed_series = pd.DataFrame({
        "value": series,
        "trend": np.round(decomposition.trend, 4),
        "seasonal": np.round(decomposition.seasonal, 4),
        "residual": np.round(decomposition.resid, 4)
    })

    return decomposed_series

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "series": {"data_type": "SERIES"},
        "model": {"data_type": "STRING", "default_value": "additive"},
        "freq": {"data_type": "INT", "default_value": None},
    },
    "outputs": {
        "decomposed_series": {"data_type": "DATAFRAME"},
    },
    "name": "Time Series Decomposition",
    "category": "Time Series Analysis",
    "description": "Decomposition of some time series",
    "version_tag": "1.0.0",
    "id": "ac353060-bef2-490a-af5e-e9edbea2df0a",
    "revision_group_id": "1459ac6c-42a3-41a8-8fd6-44c8bbdd7a92",
    "state": "RELEASED",
}

def main(*, series, model="additive", freq=None):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    decomposed_series = decompose_time_series(
        series=series,
        model=model,
        freq=freq
    )
    
    return {"decomposed_series": decomposed_series}

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