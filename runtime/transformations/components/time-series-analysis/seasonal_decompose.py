"""Seasonal Decompose
"""

import pandas as pd
from statsmodels.tsa.seasonal import seasonal_decompose

def decompose_time_series(data: pd.Series) -> pd.DataFrame:
    """This function decomposes the given time series into trend, seasonality and residuals.

    data (Pandas Series): Series containing the timeseries data. Indices must be datetimes.
    """
    try:
        data.index = pd.to_datetime(data.index, utc=True)
    except (ValueError, TypeError):
        raise TypeError("indices of data must be datetime")
        
    data = data.sort_index().dropna()
    
    if isinstance(data, pd.Series):
        df = pd.DataFrame({"value": data}, index=data.index)
    elif isinstance(data, pd.DataFrame):
        df = data.copy()
    else:
        raise ValueError("Data needs to be of type pd.Series or pd.DataFrame.")
    
    # Decomposition of the time series
    decomposition = seasonal_decompose(data)
    df["trend"] = decomposition.trend
    df["seasonal"] = decomposition.seasonal
    df["residual"] = decomposition.resid
    
    return df

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "input_df": {"data_type": "DATAFRAME"},
        "variable": {"data_type": "STRING"},
    },
    "outputs": {
        "output_df": {"data_type": "DATAFRAME"},
    },
    "name": "Seasonal Decomposition",
    "category": "Time Series Analysis",
    "description": "Seasonal Decomposition.",
    "version_tag": "1.0.0",
    "id": "ac353060-bef2-490a-af5e-e9edbea2df0a",
    "revision_group_id": "1459ac6c-42a3-41a8-8fd6-44c8bbdd7a92",
    "state": "RELeASED",
}

def main(*, input_df, variable):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    data = input_df[variable]
    
    return {"output_df": decompose_time_series(data=data)}

INITIAL_TEST_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "input_df",
            "adapter_id": "direct_provisioning",
            "use_default_value": False,
            "filters": {
                "value": (
                    "{\n"
                    '    "2020-01-01T01:15:27.000Z": 10.0,\n'
                    '    "2020-01-02T16:20:00.000Z": 20.0,\n'
                    '    "2020-01-03T08:20:04.000Z": 30.0\n'
                    "}"
                )
            },
        },
        {
            "workflow_input_name": "variable",
            "adapter_id": "direct_provisioning",
            "use_default_value": False,
            "filters": {"value": "value"},
        },
    ],
}
