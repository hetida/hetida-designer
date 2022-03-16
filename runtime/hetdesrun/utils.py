"""Utilities for scripting and in particular component/workflow deployment"""

import json
from typing import List, Optional, Tuple, Any, Dict
from enum import Enum
from uuid import UUID
import random
import logging

import requests  # pylint: disable=unused-import

from pydantic import BaseModel  # pylint: disable=no-name-in-module

from plotly.graph_objects import Figure
from plotly.utils import PlotlyJSONEncoder

from hetdesrun.datatypes import DataType

from hetdesrun.auth.keycloak import KeycloakAccessTokenManager, ServiceUserCredentials

from hetdesrun.webservice.config import RuntimeConfig


logger = logging.getLogger(__name__)


runtime_config = RuntimeConfig()
# reload actively here for usage in Jupyter notebook where
# env variables may be set before importing this module

kc_access_token_manager = (
    KeycloakAccessTokenManager(
        creds=ServiceUserCredentials(
            realm=runtime_config.hd_keycloak_realm,
            client_id=runtime_config.hd_keycloak_runtime_client_id,
            username=runtime_config.hd_keycloak_runtime_username,
            password=runtime_config.hd_keycloak_runtime_password,
            auth_url=runtime_config.hd_keycloak_auth_url,
            audience=runtime_config.hd_keycloak_runtime_audience,
        )
    )
    if runtime_config.hd_auth_use_keycloak
    else None
)


def get_auth_headers() -> Dict[str, str]:
    return (
        {"Authorization": "Bearer " + kc_access_token_manager.get_access_token()}
        if kc_access_token_manager is not None
        else {}
    )


def get_backend_basic_auth() -> Tuple[Optional[str], Optional[str]]:
    return (
        runtime_config.hd_backend_basic_auth_user,
        runtime_config.hd_backend_basic_auth_password,
    )


def get_uuid_from_seed(seed_str: str) -> UUID:
    """Generate UUID from string

    The seed_str is used to reset the random number generation seed so that this
    function always returns same UUID for the same seed_str.

    This may be used to get reproducible UUIDs from human-readable strings in scripts
    and tests. Should not be used anywhere else for security reasons.
    """
    random.seed(seed_str)
    return UUID(int=random.getrandbits(128))


def load_data(
    json_file: str, md_file: str, code_file: Optional[str] = None
) -> Tuple[Optional[dict], Optional[str], Optional[str]]:
    """Loads structured and unstructured component / workflow data from files

    Helper function to load a bunch of data from
    * 3 files for a component (a json file, the documentation markdown file, the code file)
    * or from 2 files for a workflow (a json file, the documentation markdown file,).

    Args:
        json_file (str): path to the json file
        md_file (str): path to the documentation markdown file
        code_file (Optional[str], optional): Path to code file. Defaults to None. If None
            this function will only load the json file and the doc file.

    Returns:
        Union[Tuple[Any, str], Tuple[Any, str, str]]: A tuple with structured data
        from json file as first entry, documentation as second entry and if code_file
        is not None the code as third entry. If some part of loading failes, None is returned
    """
    with open(json_file, "r", encoding="utf8") as f:
        try:
            info = json.load(f)
        except json.JSONDecodeError:
            logger.error("Could not decode %s", json_file)
            info = None
    doc: Optional[str]
    try:
        with open(md_file, "r", encoding="utf8") as f:
            doc = f.read()
    except FileNotFoundError:
        logger.error("Could not find documentation markdonw file %s", md_file)
        doc = None

    if code_file is None:
        return info, doc, None

    code: Optional[str]
    try:
        with open(code_file, "r", encoding="utf8") as f:
            code = f.read()
    except FileNotFoundError:
        logger.error("Could not find code file %s", code_file)
        code = None

    return info, doc, code


class State(str, Enum):
    """Representing state of component/workflow"""

    DRAFT = "DRAFT"
    RELEASED = "RELEASED"
    DISABLED = "DISABLED"


class Type(str, Enum):
    COMPONENT = "COMPONENT"
    WORKFLOW = "WORKFLOW"


class IODTO(BaseModel):
    id: UUID
    name: str
    posX: int = 0
    posY: int = 0
    type: DataType


class ComponentDTO(BaseModel):
    """Component DTO as expected by Backend Service"""

    name: str
    category: str
    code: str
    description: str
    groupId: UUID
    id: UUID
    inputs: List[IODTO]
    outputs: List[IODTO]
    state: State = State.RELEASED
    tag: str
    testInput: dict = {}
    type: Type = Type.COMPONENT


def model_to_pretty_json_str(pydantic_model: BaseModel) -> str:
    """Pretty printing Pydantic Models

    For logging etc.
    """
    return json.dumps(json.loads(pydantic_model.json()), indent=2, sort_keys=True)


def plotly_fig_to_json_dict(fig: Figure) -> Any:
    """Turn Plotly figure into a Python dict-like object

    This function can be used in visualization components to obtain the
    correct plotly json-like object from a Plotly Figure object.

    See visualization components from the accompanying base components for
    examples on usage.
    """
    # possibly quite inefficient (multiple serialisation / deserialization) but
    # guarantees that the PlotlyJSONEncoder is used and so the resulting Json
    # should be definitely compatible with the plotly javascript library:
    return json.loads(json.dumps(fig.to_plotly_json(), cls=PlotlyJSONEncoder))


def selection_list_empty_or_contains_value(
    selection_list: Optional[List[Any]], actual_value: Any
) -> bool:
    if selection_list is None:
        return True
    return actual_value in selection_list


def criterion_unset_or_matches_value(
    criterion: Optional[Any], actual_value: Any
) -> bool:
    if criterion is None:
        return True
    return bool(actual_value == criterion)
