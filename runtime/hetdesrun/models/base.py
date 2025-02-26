from enum import StrEnum

from pydantic import BaseModel, Field


class Result(StrEnum):
    OK = "ok"
    FAILURE = "failure"


class AbstractNode(BaseModel):
    id: str = Field(  # noqa: A003
        ..., title="Id of node", description="id in current layer"
    )


class VersionInfo(BaseModel):
    version: str = Field(..., description="hetida designer version")
