# add your own imports here, e.g.
# import pandas as pd
# import numpy as np
from plotly.graph_objects import Figure

# %%
# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "data": {"data_type": "PLOTLYJSON"},
        "path": {"data_type": "STRING"},
    },
    "outputs": {},
    "name": "Plotly to Html File",
    "category": "Data Sinks",
    "description": "Save Plotly Plot as HTML",
    "version_tag": "0.1.0",
    "id": "ce9dbeee-9e7d-4b7c-8384-9b280b2dc144",
    "revision_group_id": "2a02ee35-6d48-4f7d-a34c-a8a74dea9e28",
    "state": "RELEASED",
    "released_timestamp": "2025-01-15T15:45:47.127771+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, data, path):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    # write your function code here.
    fig = Figure(**data)

    fig.write_html(path, include_plotlyjs="cdn")


# %%
