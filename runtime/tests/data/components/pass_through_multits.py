"""Documentation for Pass Through (MultiTSFrame)

# Pass Through (MultiTSFrame)

## Description
This component just passes data through.

## Inputs
* **input** (Pandas DataFrame): The input DataFrame in the format of a MultiTSFrame: The DataFrame must consist of exactly three columns named "timestamp", "metric", and "value". The values in the "timestamp" column must have the UTC time zone and are parsed as timestamps in Pandas datetime64 format with nanosecond precision. The values in the "metric" column are parsed as strings.


## Outputs
* **output** (Pandas DataFrame): The output DataFrame in the format of a MultiTSFrame.

## Details
This component just passes through data. It can be used to map a dynamic workflow input to multiple component inputs. Its input is of type MULTITSFRAME and can therefore be used to parse dynamic input data provided during execution or to parse a manual input attached to it correctly as a Pandas DataFrame if it meets the criteria of a MultiTSframe (see the input description above). Otherwise, an exception will be thrown.
"""

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "input": {"data_type": "MULTITSFRAME"},
    },
    "outputs": {
        "output": {"data_type": "MULTITSFRAME"},
    },
    "name": "Pass Through (MultiTSFrame)",
    "category": "Connectors",
    "description": "Just outputs its input value",
    "version_tag": "1.0.0",
    "id": "78ee6b00-9239-4214-b9bf-a093647f33f5",
    "revision_group_id": "4ff190e1-4555-4fa9-b076-671586802387",
    "state": "RELEASED",
    "released_timestamp": "2023-03-08T18:07:45.719821+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, input):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    return {"output": input}


TEST_WIRING_FROM_PY_FILE_IMPORT = {}
RELEASE_WIRING = {}
