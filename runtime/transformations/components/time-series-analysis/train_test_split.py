"""Module Docstring of Train Test Split

# Train Test Split

## Description

This function is designed to split a given DataFrame into training and testing datasets, which is a fundamental step in the machine learning pipeline. Properly splitting data into training and testing sets is crucial for training models on one subset of data and then testing the model's performance on a separate set of unseen data. This approach helps in evaluating the generalization capability of the model and prevents overfitting.

The function provides options to define the size of the testing set and whether to shuffle the data before splitting. Shuffling data before splitting is often essential to ensure that the training and testing datasets are representative of the overall dataset. Especially in cases where the data might have an order, e.g., time-series data, one should use the default value *False*.

## Inputs

- **data** (Pandas DataFrame): 
    The DataFrame to be split into training and testing sets.

- **test_size** (float, default value: 0.2): 
    The proportion of the dataset to include in the test split

- **shuffle** (bool, default value: False): 
    Indicates whether the data should be shuffled before splitting

## Outputs

- **train (Pandas DataFrame)**: 
    The training set.
- **test (Pandas DataFrame)**: 
    The testing set.

## Description

This function is used in the data preparation phase of a machine learning project. It enables the separation of data into distinct sets for training and evaluation purposes, which is a best practice to assess the model's performance objectively. 

By providing options to adjust the size of the test set and to shuffle the data, the function offers flexibility to cater to different data characteristics and requirements of various machine learning models.

## Example

Example input:
```
{
    "data": {
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
            "2023-09-17T00:00:00.000Z": 1.48,
            "2023-09-18T00:00:00.000Z": 1.0,
            "2023-09-19T00:00:00.000Z": 1.02,
            "2023-09-20T00:00:00.000Z": 1.13,
            "2023-09-21T00:00:00.000Z": 1.13,
            "2023-09-22T00:00:00.000Z": 1.37,
            "2023-09-23T00:00:00.000Z": 1.45,
            "2023-09-24T00:00:00.000Z": 1.48
        }
    }
    "test_size": 0.3,
    "shuffle": False
}
```
Example output:
```
{
    "train": {
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
    },
    "test": {
        "__hd_wrapped_data_object__":"DATAFRAME",
        "__metadata__":{},
        "__data__":{
            "value": {
                "2023-09-18T00:00:00.000Z": 291,
                "2023-09-19T00:00:00.000Z": 282,
                "2023-09-20T00:00:00.000Z": 316,
                "2023-09-21T00:00:00.000Z": 305,
                "2023-09-22T00:00:00.000Z": 333,
                "2023-09-23T00:00:00.000Z": 398,
                "2023-09-24T00:00:00.000Z": 414
            },
            "exog_weekday": {
                "2023-09-18T00:00:00.000Z": 1.0,
                "2023-09-19T00:00:00.000Z": 1.02,
                "2023-09-20T00:00:00.000Z": 1.13,
                "2023-09-21T00:00:00.000Z": 1.13,
                "2023-09-22T00:00:00.000Z": 1.37,
                "2023-09-23T00:00:00.000Z": 1.45,
                "2023-09-24T00:00:00.000Z": 1.48
            }
        }
    }
}
```
"""

from typing import Tuple
import pandas as pd
from sklearn.model_selection import train_test_split 
from hetdesrun.runtime.exceptions import ComponentInputValidationException

def train_test_split_func(
    data: pd.DataFrame, 
    test_size: float = 0.2, 
    shuffle: bool = False
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Splits a DataFrame into training and testing sets.

    Inputs:
    data (Pandas DataFrame): The DataFrame to split.
    test_size (Float, optional): The proportion of the dataset to include in the test split. Default is 0.2.
    shuffle (Bool, optional): Whether or not to shuffle the data before splitting. Default is False.

    Outputs:
    train (Pandas DataFrame): A dataframe containing the training data.
    test (Pandas DataFrame): A dataframe containing the testing data.
    """
    # Parameter validations
    if len(data) == 0:
        raise ComponentInputValidationException(
            "The input data must not be empty!",
            error_code="EmptyDataFrame",
            invalid_component_inputs=["data"],
        )
    
    if not 0 < test_size < 1:
        raise ComponentInputValidationException(
            "`test_size` must be between 0 and 1",
            error_code=422,
            invalid_component_inputs=["test_size"],
        )

    # Split the data into training and testing datasets
    train, test = train_test_split(data, test_size=test_size, shuffle=shuffle)

    return train, test

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "data": {"data_type": "DATAFRAME"},
        "test_size": {"data_type": "FLOAT", "default_value": "0.2"},
        "shuffle": {"data_type": "BOOLEAN", "default_value": "False"},
    },
    "outputs": {
        "train": {"data_type": "DATAFRAME"},
        "test": {"data_type": "DATAFRAME"},
    },
    "name": "Train Test Split",
    "category": "Time Series Analysis",
    "description": "Splitting of some DataFrame into training and testing sets",
    "version_tag": "1.0.0",
    "id": "5a630e34-ab59-47c6-8903-eb60ba2d648e",
    "revision_group_id": "b0e86185-871a-476b-b6f5-a7bed5a58cf9",
    "state": "RELEASED",
}

def main(*, data, test_size=0.2, shuffle=False):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    train, test = train_test_split_func(
        data=data, 
        test_size=test_size,
        shuffle=shuffle
    )

    return {"train": train, "test": test}

TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "data",
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
        "2023-09-17T00:00:00.000Z": 400,
        "2023-09-18T00:00:00.000Z": 291,
        "2023-09-19T00:00:00.000Z": 282,
        "2023-09-20T00:00:00.000Z": 316,
        "2023-09-21T00:00:00.000Z": 305,
        "2023-09-22T00:00:00.000Z": 333,
        "2023-09-23T00:00:00.000Z": 398,
        "2023-09-24T00:00:00.000Z": 414
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
        "2023-09-17T00:00:00.000Z": 1.48,
        "2023-09-18T00:00:00.000Z": 1.0,
        "2023-09-19T00:00:00.000Z": 1.02,
        "2023-09-20T00:00:00.000Z": 1.13,
        "2023-09-21T00:00:00.000Z": 1.13,
        "2023-09-22T00:00:00.000Z": 1.37,
        "2023-09-23T00:00:00.000Z": 1.45,
        "2023-09-24T00:00:00.000Z": 1.48
    }
}
"""
            }
        }
    ]
}