"""Camera frame

# Camera frame

Obtain a single frame via opencv from a camera.

Use

```
v4l2-ctl --list-devices
```

on the command line to find out the device pathes of attached cameras.
Typically for "camera_url" something like `/dev/video0` works.

Or you configure a network camera via something like
    http://192.168.178.22:8080/video


"""

import cv2

# %%
# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "camera_url": {"data_type": "STRING"},
    },
    "outputs": {
        "frame": {"data_type": "ANY"},
    },
    "name": "Camera Frame",
    "category": "Data Sources",
    "description": "Get camera frame via opencv",
    "version_tag": "0.1.0",
    "id": "1c78ae7f-0407-4ff3-a9fa-bab1e1b689db",
    "revision_group_id": "fe512cba-102d-4736-b713-13e3c8f24bc8",
    "state": "RELEASED",
    "released_timestamp": "2025-01-17T15:03:02.972239+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, camera_url):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    cam = cv2.VideoCapture(camera_url)  # can also be an integer index of the camera
    s, frame = cam.read()
    cam.release()  # immediately release since we want only one frame
    if not s:
        raise ValueError("Camera error!")

    return {"frame": frame}


TEST_WIRING_FROM_PY_FILE_IMPORT = {}
RELEASE_WIRING = {}
# %%
