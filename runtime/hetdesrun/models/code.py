# noqa: A005
import re
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# allow only some special characters for category, description, name and version tag
ALLOWED_CHARS_RAW_STRING = r"\w ,\.\-\(\)\&\+=/"
# The special sequence \w matches unicode word characters;
# this includes most characters that can be part of a word in any language, as well as numbers
# and the underscore. If the ASCII flag is used, only [a-zA-Z0-9_] is matched.


NonEmptyValidStr = Annotated[
    str, Field(min_length=1, pattern=re.compile(rf"^[{ALLOWED_CHARS_RAW_STRING}]+$"))
]


ShortNonEmptyValidStr = Annotated[
    str, Field(min_length=1, max_length=20, pattern=re.compile(rf"^[{ALLOWED_CHARS_RAW_STRING}]+$"))
]

ValidStr = Annotated[str, Field(pattern=re.compile(rf"^[{ALLOWED_CHARS_RAW_STRING}]*$"))]


example_code: str = """\
# add your own imports here, e.g.
#     import pandas as pd
#     import numpy as np

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {"x": "FLOAT", "y": "FLOAT"},
    "outputs": {"z": "FLOAT"},
    "name": "Example Component",
    "description": "An example for code generation",
    "category": "Examples",
    "id": "c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
    "revision_group_id": "c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
    "version_tag": "1.0.0"
)
def main(*, x, y):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    return {"z": x+y}
"""

example_code_async: str = """\
# add your own imports here, e.g.
#     import pandas as pd
#     import numpy as np

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {"x": "FLOAT", "y": "FLOAT"},
    "outputs": {"z": "FLOAT"},
    "name": "Example Component",
    "description": "An example for code generation",
    "category": "Examples",
    "id": "c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
    "revision_group_id": "c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
    "version_tag": "1.0.0"
}
async def main(*, x, y):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    return {"z": x+y}
"""


class CodeModule(BaseModel):
    code: str = Field(
        ...,
        title="Python module source code",
        examples=[example_code],
        description="""\
The code may contain functions that can act as entrypoints for components.
A code module can contain more than one entrypoint and therefore be used
by different components. This may be the case for some built-in-components
in the future. User defined components usually come with exactly one entrypoint
function called "main".
""",
    )
    uuid: UUID
    model_config = ConfigDict(frozen=True)
