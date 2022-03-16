# pylint: disable=no-name-in-module
from pydantic import BaseModel

from hetdesrun.backend.service.utils import to_camel


class AdapterFrontendDto(BaseModel):
    id: str
    name: str
    url: str
    internal_url: str

    class Config:
        alias_generator = to_camel
