from uuid import UUID, uuid4
from typing import Dict, Optional
import re
import datetime

from pydantic import (
    BaseModel,
    Field,
    ConstrainedStr,
    validator,
)  # pylint: disable=no-name-in-module

from hetdesrun.datatypes import DataType
from hetdesrun.utils import State

# allow only some special characters for category, description, name and version tag
ALLOWED_CHARS_RAW_STRING = (
    r"\w ,\.\-\(\)\&\+=/"  # pylint: disable=anomalous-backslash-in-string
)
# The special sequence \w matches unicode word characters;
# this includes most characters that can be part of a word in any language, as well as numbers
# and the underscore. If the ASCII flag is used, only [a-zA-Z0-9_] is matched.


class NonEmptyValidStr(ConstrainedStr):
    min_length = 1
    max_length = 60
    regex = re.compile(rf"^[{ALLOWED_CHARS_RAW_STRING}]+$")


class ShortNonEmptyValidStr(ConstrainedStr):
    min_length = 1
    max_length = 20
    regex = re.compile(rf"^[{ALLOWED_CHARS_RAW_STRING}]+$")


class ValidStr(ConstrainedStr):
    regex = re.compile(rf"^[{ALLOWED_CHARS_RAW_STRING}]*$")


example_code: str = """\
from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType
# add your own imports here, e.g.
#     import pandas as pd
#     import numpy as np

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
@register(
    inputs={"x": DataType.Float, "y": DataType.Float},
    outputs={"z": DataType.Float},
    name="Example Component",
    description="An example for code generation",
    category="Examples",
    id="c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
    revision_group_id="c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
    version_tag="1.0.0"
)
def main(*, x, y):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    return {"z": x+y}
"""

example_code_async: str = """\
from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType
# add your own imports here, e.g.
#     import pandas as pd
#     import numpy as np

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
@register(
    inputs={"x": DataType.Float, "y": DataType.Float},
    outputs={"z": DataType.Float},
    name="Example Component",
    description="An example for code generation",
    category="Examples",
    id="c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
    revision_group_id="c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
    version_tag="1.0.0"
)
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
        example=example_code,
        description="""\
The code may contain functions that can act as entrypoints for components.
A code module can contain more than one entrypoint and therefore be used
by different components. This may be the case for some built-in-components
in the future. User defined components usually come with exactly one entrypoint
function called "main".
""",
    )
    uuid: UUID


class ComponentInfo(BaseModel):
    """Provide meta-information about component.

    Used as input for code generation to include meta-information about the component in the code.

    This additional information makes it possible to recover the underlying transformation revision
    object from the code.
    """

    input_types_by_name: Dict[str, DataType]
    output_types_by_name: Dict[str, DataType]
    name: NonEmptyValidStr
    category: NonEmptyValidStr
    description: ValidStr
    version_tag: ShortNonEmptyValidStr
    id: UUID = Field(default_factory=uuid4)
    revision_group_id: UUID = Field(default_factory=uuid4)
    state: State
    released_timestamp: Optional[datetime.datetime] = None
    disabled_timestamp: Optional[datetime.datetime] = None
    is_coroutine: bool = False

    # pylint: disable=no-self-argument,no-self-use
    @validator("version_tag")
    def version_tag_not_latest(cls, v: str) -> str:
        if v.lower() == "latest":
            raise ValueError('version_tag is not allowed to be "latest"')
        return v
