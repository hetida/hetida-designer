# %%
# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "msg": {"data_type": "STRING"},
    },
    "outputs": {},
    "name": "Raise Value Error",
    "category": "Test",
    "description": "Raise Value Error",
    "version_tag": "0.1.0",
    "id": "6168603a-f599-463d-9794-6a9371ed6088",
    "revision_group_id": "09268971-e6bb-4599-9dc9-c91b4d2a44f4",
    "state": "RELEASED",
    "released_timestamp": "2026-03-06T15:46:05.190953+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, msg):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    # write your function code here.
    raise ValueError(msg)
