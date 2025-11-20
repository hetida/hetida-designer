from pydantic import BaseModel, ConfigDict

from hetdesrun.backend.service.utils import to_camel


class AdapterFrontendDto(BaseModel):
    id: str  # noqa: A003
    name: str
    url: str
    internal_url: str
    model_config = ConfigDict(alias_generator=to_camel)
