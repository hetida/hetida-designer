import datetime
import json
import logging
from io import StringIO
from typing import Callable, Dict, List, Optional, Union
from urllib.parse import unquote

import numpy as np
import pandas as pd
from fastapi import APIRouter, Body, FastAPI, HTTPException, Query
from fastapi.exceptions import RequestValidationError
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.routing import APIRoute
from starlette.requests import Request
from starlette.responses import Response

from demo_adapter_python import VERSION
from demo_adapter_python.config import demo_adapter_config
from demo_adapter_python.demo_data.sinks import get_sinks
from demo_adapter_python.demo_data.sources import get_sources
from demo_adapter_python.demo_data.thing_nodes import get_thing_nodes
from demo_adapter_python.in_memory_store import (
    get_metadatum_from_store,
    get_value_from_store,
    set_metadatum_in_store,
    set_value_in_store,
)
from demo_adapter_python.models import (
    GetMetadatum,
    InfoResponse,
    MultipleSinksResponse,
    MultipleSourcesResponse,
    PostMetadatum,
    StructureResponse,
    StructureSink,
    StructureSource,
    StructureThingNode,
    TimeseriesRecord,
)

logger = logging.getLogger(__name__)

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=demo_adapter_config.allowed_origins.split(","),
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
]

app = FastAPI(
    title="Hetida Designer Python Demo Adapter API",
    description="Hetida Designer Python Demo Adapter Web Services API",
    version=VERSION,
    root_path=demo_adapter_config.swagger_prefix,
    middleware=middleware,
)


class AdditionalLoggingRoute(APIRoute):
    """Additional logging and information in case of errors

    Makes sure that requests are logged in every situation.
    """

    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            try:
                json_data = await request.json()
            except json.decoder.JSONDecodeError:
                body = await request.body()
                logger.info(
                    "RECEIVED BODY (could not parse as json):\n%s", body.decode()
                )
            else:
                logger.info(
                    "RECEIVED JSON BODY: \n%s",
                    json.dumps(json_data, indent=2, sort_keys=True),
                )
            try:
                return await original_route_handler(request)  # type: ignore
            except RequestValidationError as exc:
                body = await request.body()
                detail = {"errors": exc.errors(), "body": body.decode()}
                logger.info("Request Validation Error: %s", str(exc))
                raise HTTPException(  # pylint: disable=raise-missing-from
                    status_code=422, detail=detail
                )

        return custom_route_handler


app.router.route_class = AdditionalLoggingRoute


demo_adapter_main_router = APIRouter()


@demo_adapter_main_router.get("/info", response_model=InfoResponse)
async def info():
    return {
        "id": "python-demo-adapter",
        "name": "Python Demo Adapter",
        "version": VERSION,
    }


@demo_adapter_main_router.get("/structure", response_model=StructureResponse)
async def structure(parentId: Optional[str] = None):
    """The hierarchical structure for easy assignment of sources/sinks in user interfaces

    This endpoint is required by the hetida designer UI to show and allow assignment of sources
    and sinks from hierachical views. A hierarchy should be a domain view of the data sources
    and sinks that users of the designer understand and which helps them to easily find the
    sources / sinks they want to attach to their workflows by browsing through the hierarchy.

    Note that more than one hierarchy can be provided by delivering more than one root node.
    This can be used to provide different semantical views onto the same data, like e.g. a
    geographical hierarchy and a business unit hierarchy.

    This endpoint employs lazy loading, i.e. only one hierarchy level is returned on a call.

    If no `parentId` is specified this yields only the root thingNodes and no sources/sinks
    (sources / sinks attached to root nodes are not allowed in the user interface)

    If `parentId` is a valid thingNode id the response contains all the thingNodes, sources and
    sinks with this `parentId` as thingNodeId, i.e. every element directly attached to it.

    IMPORTANT: In a real adpater implementation the information should be queried from a
    masterdata system on every invocation. It should not be kept in memory like in this
    demo adapter as it may be too large and may change.
    """

    return {
        "id": "python-demo-adapter",
        "name": "Python Demo Adapter",
        "thingNodes": get_thing_nodes(parentId, include_sub_objects=False),
        "sources": get_sources(parentId, include_sub_objects=False),
        "sinks": get_sinks(parentId, include_sub_objects=False),
    }


@demo_adapter_main_router.get("/sources", response_model=MultipleSourcesResponse)
async def sources(filter_str: Optional[str] = Query(None, alias="filter")):

    return_sources = get_sources(filter_str=filter_str, include_sub_objects=True)

    return MultipleSourcesResponse(
        resultCount=len(return_sources), sources=return_sources
    )


@demo_adapter_main_router.get(
    "/sources/{sourceId}/metadata/", response_model=List[GetMetadatum]
)
async def get_all_metadata_source(sourceId: str):
    if sourceId.endswith("temp") and "plantA" in sourceId:
        return [
            {"key": "Max Value", "value": 300.0, "dataType": "float"},
            {"key": "Min Value", "value": -100.0, "dataType": "float"},
            {"key": "Last Self-Check Okay", "value": True, "dataType": "boolean"},
            get_metadatum_from_store(sourceId, "Sensor Config"),
        ]
    if sourceId.endswith("temp") and "plantB" in sourceId:
        return [
            {"key": "Max Value", "value": 150.0, "dataType": "float"},
            {"key": "Min Value", "value": -30.0, "dataType": "float"},
            {"key": "Last Self-Check Okay", "value": True, "dataType": "boolean"},
            get_metadatum_from_store(sourceId, "Sensor Config"),
        ]
    if sourceId.endswith("anomaly_score") and "plantA" in sourceId:
        return [
            {"key": "Max Value", "value": 1.0, "dataType": "float"},
            {"key": "Min Value", "value": 0.0, "dataType": "float"},
            get_metadatum_from_store(sourceId, "Overshooting Allowed"),
        ]
    if sourceId.endswith("anomaly_score") and "plantB" in sourceId:
        return [
            {"key": "Max Value", "value": 1.0, "dataType": "float"},
            {"key": "Min Value", "value": 0.0, "dataType": "float"},
            get_metadatum_from_store(sourceId, "Overshooting Allowed"),
        ]

    return []


@demo_adapter_main_router.get(
    "/sources/{sourceId}/metadata/{key}", response_model=GetMetadatum
)
async def get_metadata_source_by_key(sourceId: str, key: str):
    # pylint: disable=too-many-return-statements,too-many-branches
    key = unquote(key)
    if sourceId.endswith("temp") and "plantA" in sourceId:
        if key == "Max Value":
            return {"key": "Max Value", "value": 300.0, "dataType": "float"}
        if key == "Min Value":
            return {"key": "Min Value", "value": -100.0, "dataType": "float"}
        if key == "Last Self-Check Okay":
            return {"key": "Last Self-Check Okay", "value": True, "dataType": "boolean"}
        if key == "Sensor Config":
            return get_metadatum_from_store(sourceId, "Sensor Config")

    elif sourceId.endswith("temp") and "plantB" in sourceId:
        if key == "Max Value":
            return {"key": "Max Value", "value": 150.0, "dataType": "float"}
        if key == "Min Value":
            return {"key": "Min Value", "value": -30.0, "dataType": "float"}
        if key == "Last Self-Check Okay":
            return {"key": "Last Self-Check Okay", "value": True, "dataType": "boolean"}
        if key == "Sensor Config":
            return get_metadatum_from_store(sourceId, "Sensor Config")

    if sourceId.endswith("anomaly_score") and "plantA" in sourceId:
        if key == "Max Value":
            return {"key": "Max Value", "value": 1.0, "dataType": "float"}
        if key == "Min Value":
            return {"key": "Min Value", "value": 0.0, "dataType": "float"}
        if key == "Overshooting Allowed":
            return get_metadatum_from_store(sourceId, "Overshooting Allowed")

    elif sourceId.endswith("anomaly_score") and "plantB" in sourceId:
        if key == "Max Value":
            return {"key": "Max Value", "value": 1.0, "dataType": "float"}
        if key == "Min Value":
            return {"key": "Min Value", "value": 0.0, "dataType": "float"}
        if key == "Overshooting Allowed":
            return get_metadatum_from_store(sourceId, "Overshooting Allowed")
    raise HTTPException(
        404, f"Could not find metadatum attached to source {sourceId} with key {key}"
    )


@demo_adapter_main_router.post("/sources/{sourceId}/metadata/{key}", status_code=200)
async def post_metadata_source_by_key(
    sourceId: str, key: str, metadatum: PostMetadatum
):
    key = unquote(key)
    if sourceId.endswith("temp") and key == "Sensor Config":

        old_metadatum = get_metadatum_from_store(sourceId, key)

        new_metadatum = metadatum.dict()

        new_metadatum["dataType"] = old_metadatum["dataType"]
        new_metadatum["isSink"] = old_metadatum.get("isSink", True)

        set_metadatum_in_store(sourceId, key, new_metadatum)
        return {"message": "success"}
    return HTTPException(
        404,
        f"There is no writable metadatum at source {sourceId} with key {key}",
    )


@demo_adapter_main_router.get(
    "/sources/{source_id:path}", response_model=StructureSource
)
async def source(source_id: str):
    """Get a single source by id"""
    requested_sources = [
        src for src in get_sources(include_sub_objects=True) if src["id"] == source_id
    ]
    if len(requested_sources) > 1:
        msg = f"Error: Multiple sources with same id {str(requested_sources)}"
        logger.info(msg)
        raise HTTPException(500, msg)

    if len(requested_sources) < 1:
        msg = f"Requested source with id {source_id} not found."
        logger.info(msg)
        raise HTTPException(404, msg)
    return StructureSource.parse_obj(requested_sources[0])


@demo_adapter_main_router.get("/sinks", response_model=MultipleSinksResponse)
async def sinks(filter_str: Optional[str] = Query(None, alias="filter")):
    return_sinks = get_sinks(filter_str=filter_str, include_sub_objects=True)

    return MultipleSinksResponse(resultCount=len(return_sinks), sinks=return_sinks)


@demo_adapter_main_router.get(
    "/sinks/{sinkId}/metadata/", response_model=List[GetMetadatum]
)
async def get_all_metadata_sink(sinkId: str):
    if sinkId.endswith("anomaly_score") and "plantA" in sinkId:
        return [
            {"key": "Max Value", "value": 1.0, "dataType": "float"},
            {"key": "Min Value", "value": 0.0, "dataType": "float"},
            get_metadatum_from_store(sinkId, "Overshooting Allowed"),
        ]
    if sinkId.endswith("anomaly_score") and "plantB" in sinkId:
        return [
            {"key": "Max Value", "value": 1.0, "dataType": "float"},
            {"key": "Min Value", "value": 0.0, "dataType": "float"},
            get_metadatum_from_store(sinkId, "Overshooting Allowed"),
        ]
    return []


@demo_adapter_main_router.get(
    "/sinks/{sinkId}/metadata/{key}", response_model=GetMetadatum
)
async def get_metadata_sink_by_key(sinkId: str, key: str):
    key = unquote(key)

    if sinkId.endswith("anomaly_score") and "plantA" in sinkId:
        if key == "Max Value":
            return {"key": "Max Value", "value": 1.0, "dataType": "float"}
        if key == "Min Value":
            return {"key": "Min Value", "value": 0.0, "dataType": "float"}
        if key == "Overshooting Allowed":
            return get_metadatum_from_store(sinkId, "Overshooting Allowed")

    elif sinkId.endswith("anomaly_score") and "plantB" in sinkId:
        if key == "Max Value":
            return {"key": "Max Value", "value": 1.0, "dataType": "float"}
        if key == "Min Value":
            return {"key": "Min Value", "value": 0.0, "dataType": "float"}
        if key == "Overshooting Allowed":
            return get_metadatum_from_store(sinkId, "Overshooting Allowed")

    raise HTTPException(
        404, f"Could not find metadatum attached to sink {sinkId} with key {key}"
    )


@demo_adapter_main_router.post("/sinks/{sinkId}/metadata/{key}", status_code=200)
async def post_metadata_sink_by_key(sinkId: str, key: str, metadatum: PostMetadatum):
    key = unquote(key)
    if sinkId.endswith("anomaly_score") and key == "Overshooting Allowed":

        old_metadatum = get_metadatum_from_store(sinkId, key)

        new_metadatum = metadatum.dict()

        new_metadatum["dataType"] = old_metadatum["dataType"]
        new_metadatum["isSink"] = old_metadatum.get("isSink", True)

        set_metadatum_in_store(sinkId, key, new_metadatum)
        return {"message": "success"}
    return HTTPException(
        404,
        f"There is no writable metadatum at sink {sinkId} with key {key}",
    )


@demo_adapter_main_router.get("/sinks/{sink_id}", response_model=StructureSink)
async def sink(sink_id: str):
    """Get a single sink by id"""
    requested_sinks = [
        snk for snk in get_sinks(include_sub_objects=True) if snk["id"] == sink_id
    ]
    if len(requested_sinks) > 1:
        msg = f"Error: Multiple sinks with same id {str(requested_sinks)}"
        logger.info(msg)
        raise HTTPException(500, msg)

    if len(requested_sinks) < 1:
        msg = f"Requested sink with id {sink_id} not found."
        logger.info(msg)
        raise HTTPException(404, msg)
    return StructureSource.parse_obj(requested_sinks[0])


@demo_adapter_main_router.get(
    "/thingNodes/{thingNodeId}/metadata/", response_model=List[GetMetadatum]
)
async def get_all_metadata_thingNode(thingNodeId: str):
    if thingNodeId == "root.plantA":
        return [
            {"key": "Temperature Unit", "value": "F", "dataType": "string"},
            {"key": "Pressure Unit", "value": "psi", "dataType": "string"},
            {  # a metadatum that is not an explicit source and calculated dynamically
                "key": "Plant Age in Years",
                "value": calculate_age(datetime.date(2012, 12, 7)),
                "dataType": "int",
            },
            # this metadatum is a sink leaf but as a source only available attached to the thingNode
            get_metadatum_from_store(thingNodeId, "Anomaly State"),
        ]
    if thingNodeId == "root.plantB":
        return [
            {"key": "Temperature Unit", "value": "C", "dataType": "string"},
            {"key": "Pressure Unit", "value": "bar", "dataType": "string"},
            {  # a metadatum that is not an explicit source and calculated dynamically
                "key": "Plant Age in Years",
                "value": calculate_age(datetime.date(2017, 8, 22)),
                "dataType": "int",
            },
            # this metadatum is a sink leaf but as a source only available attached to the thingNode
            get_metadatum_from_store(thingNodeId, "Anomaly State"),
        ]
    return []


def calculate_age(born):
    today = datetime.date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


@demo_adapter_main_router.get(
    "/thingNodes/{thingNodeId}/metadata/{key}", response_model=GetMetadatum
)
async def get_metadata_thingNode_by_key(thingNodeId: str, key: str) -> GetMetadatum:
    # pylint: disable=too-many-return-statements
    key = unquote(key)
    if thingNodeId == "root.plantA":
        if key == "Temperature Unit":
            return {
                "key": "Temperature Unit",
                "value": "F",
                "dataType": "string",
            }
        if key == "Pressure Unit":
            return {
                "key": "Pressure Unit",
                "value": "psi",
                "dataType": "string",
            }
        if key == "Plant Age in Years":
            return {
                "key": "Plant Age in Years",
                "value": calculate_age(datetime.date(2012, 12, 7)),
                "dataType": "int",
            }
        if key == "Anomaly State":
            return get_metadatum_from_store(thingNodeId, "Anomaly State")

    if thingNodeId == "root.plantB":
        if key == "Temperature Unit":
            return {
                "key": "Temperature Unit",
                "value": "C",
                "dataType": "string",
            }
        if key == "Pressure Unit":
            return {
                "key": "Pressure Unit",
                "value": "bar",
                "dataType": "string",
            }
        if key == "Plant Age in Years":
            return {
                "key": "Plant Age in Years",
                "value": calculate_age(datetime.date(2017, 8, 22)),
                "dataType": "int",
            }
        if key == "Anomaly State":
            return get_metadatum_from_store(thingNodeId, "Anomaly State")
    raise HTTPException(
        404,
        f"Could not find metadatum attached/at thingNode {thingNodeId} with key {key}",
    )


@demo_adapter_main_router.post(
    "/thingNodes/{thingNodeId}/metadata/{key}", status_code=200
)
async def post_metadata_thingNode_by_key(
    thingNodeId: str, key: str, metadatum: PostMetadatum
) -> Union[dict, HTTPException]:
    key = unquote(key)
    if thingNodeId in ["root.plantA", "root.plantB"]:

        old_metadatum = get_metadatum_from_store(thingNodeId, key)

        new_metadatum = metadatum.dict()

        new_metadatum["dataType"] = old_metadatum["dataType"]
        new_metadatum["isSink"] = old_metadatum.get("isSink", True)

        set_metadatum_in_store(thingNodeId, key, new_metadatum)
        return {"message": "success"}

    return HTTPException(
        404,
        f"There is no writable metadatum at thingNode {thingNodeId} with key {key}",
    )


@demo_adapter_main_router.get("/thingNodes/{id}", response_model=StructureThingNode)
async def thing_node(
    id: str,  # pylint: disable=redefined-builtin
) -> StructureThingNode:  # pylint: disable=redefined-builtin
    """Get a single sink by id"""
    requested_thing_nodes = [
        tn for tn in get_thing_nodes(include_sub_objects=True) if tn["id"] == id
    ]
    if len(requested_thing_nodes) > 1:
        msg = f"Error: Multiple ThingNodes with same id {str(requested_thing_nodes)}"
        logger.info(msg)
        raise HTTPException(500, msg)

    if len(requested_thing_nodes) < 1:
        msg = f"Requested ThingNode with id {id} not found."
        logger.info(msg)
        raise HTTPException(404, msg)
    return StructureThingNode.parse_obj(requested_thing_nodes[0])


@demo_adapter_main_router.get("/timeseries")
async def timeseries(
    ids: List[str] = Query(..., alias="id", min_length=1),
    from_timestamp: datetime.datetime = Query(..., alias="from"),
    to_timestamp: datetime.datetime = Query(..., alias="to"),
) -> StreamingResponse:
    io_stream = StringIO()

    dt_range = pd.date_range(
        start=from_timestamp, end=to_timestamp, freq="1h", tz=datetime.timezone.utc
    )
    for ts_id in ids:
        ts_df = None
        if ts_id.endswith("temp"):
            offset = 100.0 if "plantA" in ts_id else 30.0
            factor = 10.0 if "plantA" in ts_id else 5.0
        elif ts_id.endswith("press"):
            offset = 14.5 if "plantA" in ts_id else 1.0
            factor = 0.73 if "plantA" in ts_id else 0.05
        elif ts_id.endswith("anomaly_score"):
            stored_df = get_value_from_store(ts_id).copy()
            if "timestamp" in stored_df.columns:
                stored_df.index = pd.to_datetime(stored_df["timestamp"])
                stored_df = stored_df[
                    from_timestamp.isoformat() : to_timestamp.isoformat()  # type: ignore
                ]
                ts_df = pd.DataFrame(
                    {
                        "timestamp": stored_df.index,
                        "timeseriesId": ts_id,
                        "value": stored_df["value"],
                    }
                )
            else:
                ts_df = pd.DataFrame(
                    {
                        "timestamp": [],
                        "timeseriesId": [],
                        "value": [],
                    }
                )

        else:
            offset = 0.0
            factor = 1.0
        if ts_df is None:
            ts_df = pd.DataFrame(
                {
                    "timestamp": dt_range,
                    "timeseriesId": ts_id,
                    "value": np.random.randn(len(dt_range)) * factor + offset,
                }
            )
        # throws warning during pytest:
        ts_df.to_json(io_stream, lines=True, orient="records", date_format="iso")

    io_stream.seek(0)
    return StreamingResponse(io_stream, media_type="application/json")


@demo_adapter_main_router.post("/timeseries", status_code=200)
async def post_timeseries(
    ts_body: List[TimeseriesRecord],
    ts_id: str = Query(..., alias="timeseriesId"),
) -> Dict:
    logger.info("Received ts_body for id %s:\n%s", ts_id, str(ts_body))
    if ts_id.endswith("anomaly_score"):
        df = pd.DataFrame.from_dict((x.dict() for x in ts_body), orient="columns")
        set_value_in_store(ts_id, df)
        logger.info(
            "stored timeseries %s in store: %s\n with columns %s",
            ts_id,
            str(df),
            str(df.columns),
        )
        return {"message": "success"}

    raise HTTPException(404, f"No writable timeseries with id {ts_id}")


@demo_adapter_main_router.get("/dataframe")
async def dataframe(
    df_id: str = Query(..., alias="id")
) -> Union[HTTPException, StreamingResponse]:

    if df_id.endswith("plantA.maintenance_events"):
        df = pd.DataFrame(
            {  # has timestamp column
                "component_id": ["AB4217", "AB4217", "CD7776"],
                "component_name": ["central gearbox", "central gearbox", "connector"],
                "maintenance_type": ["repair", "replacement", "repair"],
                "timestamp": [
                    "2020-08-03T15:30:00.000Z",
                    "2020-12-01T07:15:00.000Z",
                    "2021-01-05T09:20:00.000Z",
                ],
            }
        )
    elif df_id.endswith("plantB.maintenance_events"):
        df = pd.DataFrame(
            {  # has timestamp column
                "component_id": ["GH5300"],
                "component_name": ["plug"],
                "maintenance_type": ["replacement"],
                "timestamp": [
                    "2020-07-16T22:30:00.000Z",
                ],
            }
        )
    elif df_id.endswith("plantA.masterdata"):
        df = pd.DataFrame(
            {
                "name": [
                    "plant_construction_date",
                    "plant_country",
                    "num_current_employees",
                ],
                "value": ["2012-12-07T00:00:00.000Z", "US", 17],
            }
        )
    elif df_id.endswith("plantB.masterdata"):
        df = pd.DataFrame(
            {
                "name": [
                    "plant_construction_date",
                    "plant_country",
                    "num_current_employees",
                ],
                "value": ["2017-08-22T00:00:00.000Z", "DE", 13],
            }
        )
    elif df_id.endswith("alerts"):
        df = get_value_from_store(df_id)

    else:
        return HTTPException(
            404, f"no dataframe data available with provided id {df_id}"
        )

    io_stream = StringIO()
    df.to_json(io_stream, lines=True, orient="records", date_format="iso")
    io_stream.seek(0)
    return StreamingResponse(io_stream, media_type="application/json")


@demo_adapter_main_router.post("/dataframe", status_code=200)
async def post_dataframe(
    df_body: List[Dict] = Body(
        ...,
        example=[
            {"column_A": 42.0, "column_B": "example"},
            {"column_A": 11.97, "column_B": "example"},
        ],
    ),
    df_id: str = Query(..., alias="id"),
) -> dict:
    if df_id.endswith("alerts"):
        df = pd.DataFrame.from_dict(df_body, orient="columns")
        set_value_in_store(df_id, df)
        return {"message": "success"}

    raise HTTPException(404, f"No writable dataframe with id {df_id}")


@app.on_event("startup")
async def startup_event() -> None:
    uv_logger = logging.getLogger("uvicorn.access")
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "%(process)d - %(processName)s - %(asctime)s - %(levelname)s - %(message)s"
        )
    )
    uv_logger.addHandler(handler)


app.include_router(demo_adapter_main_router, prefix="")
