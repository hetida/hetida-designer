from pydantic import BaseModel

from hetdesrun.backend.service.utils import to_camel


class AdapterFrontendDto(BaseModel):
    id: str  # noqa: A003
    name: str
    url: str
    internal_url: str

    class Config:
        alias_generator = to_camel
