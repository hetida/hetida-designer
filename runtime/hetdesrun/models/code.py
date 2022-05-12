from uuid import UUID, uuid4
from typing import List, Dict, Optional
import re

from pydantic import (
    BaseModel,
    Field,
    ConstrainedStr,
    validator,
)  # pylint: disable=no-name-in-module

from hetdesrun.datatypes import DataType
from hetdesrun.models.base import Result
from hetdesrun.models.component import ComponentInput, ComponentOutput

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


class CodeBody(BaseModel):
    code: str = Field(
        None,
        title="Python source code of a component",
        description="source code of a component",
        example=example_code,
    )
    function_name: str = Field(
        "main",
        example="main",
        title="Entry point function name",
        description="The name of the function in the provided code module"
        "which is the entrypoint for this component",
    )
    inputs: List[ComponentInput]
    outputs: List[ComponentOutput]
    name: str
    description: str
    category: str
    id: UUID
    revision_group_id: UUID
    version_tag: str


class GeneratedCode(BaseModel):
    code: str = Field(
        ...,
        title="Python source code of a component",
        description="source code of a component",
        example=example_code,
    )


class CodeCheckResult(BaseModel):
    result: Result = Field(
        ...,
        description="one of " + ", ".join(['"' + x.value + '"' for x in list(Result)]),
        example=Result.OK,
    )
    error: Optional[str] = Field(None, description="error string")
    traceback: Optional[str] = Field(None, description="traceback")


class ComponentInfo(BaseModel):
    """Provide meta-information about component.

    Used as input for code generation to include meta-information about the component in the code.

    This additional information makes it possible to recover the underlying transformation revision
    object from the code.
    """

    input_types_by_name: Dict[str, DataType]
    output_types_by_name: Dict[str, DataType]
    id: UUID = Field(default_factory=uuid4)
    revision_group_id: UUID = Field(default_factory=uuid4)
    name: NonEmptyValidStr
    category: NonEmptyValidStr
    description: ValidStr
    version_tag: ShortNonEmptyValidStr
    is_coroutine: bool = False

    # pylint: disable=no-self-argument,no-self-use
    @validator("version_tag")
    def version_tag_not_latest(cls, v: str) -> str:
        if v.lower() == "latest":
            raise ValueError('version_tag is not allowed to be "latest"')
        return v

    @classmethod
    def from_code_body(cls, code_body: CodeBody) -> "ComponentInfo":
        return ComponentInfo(
            input_types_by_name={io.name: io.type for io in code_body.inputs},
            output_types_by_name={io.name: io.type for io in code_body.outputs},
            id=code_body.id,
            revision_group_id=code_body.revision_group_id,
            name=code_body.name,
            category=code_body.category,
            description=code_body.description,
            version_tag=code_body.version_tag,
        )
