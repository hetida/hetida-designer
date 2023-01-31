from enum import Enum

from pydantic import BaseModel, Field  # pylint: disable=no-name-in-module


class Result(str, Enum):
    OK: str = "ok"
    FAILURE: str = "failure"


class AbstractNode(BaseModel):
    id: str = Field(  # noqa: A003
        ..., title="Id of node", description="id in current layer"
    )


class VersionInfo(BaseModel):
    version: str = Field(..., description="hetida designer version")
