"""Show image frame

# Show image frame

Display a single opencv image frame as Plotly image plot.
"""

import cv2
import numpy as np
import plotly.express as px

from hdutils import plotly_fig_to_json_dict

# %%
# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "frame": {"data_type": "ANY"},
    },
    "outputs": {
        "image": {"data_type": "PLOTLYJSON"},
    },
    "name": "Show image frame",
    "category": "Visualization",
    "description": "Show an opencv frame as an image",
    "version_tag": "0.1.0",
    "id": "5424ca9d-c892-4469-9340-223f83249f75",
    "revision_group_id": "2376d157-b995-40c3-af9f-b0e65348a112",
    "state": "DRAFT",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, frame):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    img = cv2.cvtColor(frame.astype(np.uint8), cv2.COLOR_BGR2RGB)

    # use plotly express to create figure
    fig = px.imshow(img, binary_string=True)
    return {"image": plotly_fig_to_json_dict(fig)}


TEST_WIRING_FROM_PY_FILE_IMPORT = {}
RELEASE_WIRING = None
# %%
