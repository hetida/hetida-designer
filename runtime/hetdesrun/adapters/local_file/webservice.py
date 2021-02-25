from typing import Optional, Dict, List
import logging

from uuid import uuid4

from fastapi import APIRouter

from hetdesrun import VERSION

from hetdesrun.adapters.generic_rest.external_types import ExternalType

from pydantic import BaseModel

local_file_adapter_router = APIRouter()

logger = logging.getLogger(__name__)


class InfoResponse(BaseModel):
    id: str
    name: str
    version: str


class StructureThingNode(BaseModel):
    id: str
    parentId: str
    name: str
    description: str


class StructureFilter(BaseModel):
    name: str
    required: bool


class StructureSource(BaseModel):
    id: str
    thingNodeId: str
    name: str
    type: ExternalType
    visible: Optional[bool] = True
    filters: Optional[Dict[str, StructureFilter]] = {}


class StructureSink(BaseModel):
    id: str
    thingNodeId: str
    name: str
    type: ExternalType
    visible: Optional[bool] = True
    filters: Optional[Dict[str, StructureFilter]] = {}


class StructureResponse(BaseModel):
    id: str
    name: str
    thingNodes: List[StructureThingNode]
    sources: List[StructureSource]
    sinks: List[StructureSink]


@local_file_adapter_router.get("/info", response_model=InfoResponse)
async def info():
    return {
        "id": "runtime-builtin-local-file-adapter",
        "name": "Mounted Local Files",
        "version": VERSION,
    }


@local_file_adapter_router.get("/structure", response_model=StructureResponse)
async def structure(parentId: Optional[str] = None):

    # parent_id could be a subdir. Then show only those under this subdir

    return {
        "id": str(uuid4()),
        "name": "Locally Mounted Files",
        "thingNodes": [
            {
                "id": "dir1/dir2/dir3",
                "parentId": "dir1/dir2",
                "name": "dir2",
                "description": "dir1/dir2/dir3",
            }
        ],
        "sources": [
            {
                "id": "file_base_name.csv",  # expect a fitting config file with name "file_base_name.csv.read_csv.json"
                "thingNodeId": "dir1/dir2/dir3",
                "name": "file_base_name.csv",
                "type": ExternalType.DATAFRAME,
            }
        ],
        "sinks": [],
    }
