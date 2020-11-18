from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel, Field  # pylint: disable=no-name-in-module


from hetdesrun.component.code import example_code
from hetdesrun.models.base import Result
from hetdesrun.models.component import ComponentInput, ComponentOutput


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
