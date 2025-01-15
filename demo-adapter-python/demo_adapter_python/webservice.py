import base64
import datetime
import json
import logging
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from io import StringIO
from typing import Any
from urllib.parse import unquote

import numpy as np
import pandas as pd
from fastapi import APIRouter, Body, FastAPI, Header, HTTPException, Query, status
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
    InfoResponse,
    Metadatum,
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

MULTITSFRAME_COLUMN_NAMES = ["timestamp", "metric", "value"]

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=demo_adapter_config.allowed_origins.split(","),
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
        expose_headers=["Data-Attributes"],  # is this necessary?
    )
]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:  # noqa: ARG001
    uv_logger = logging.getLogger("uvicorn.access")
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "%(process)d - %(processName)s - %(asctime)s - %(levelname)s - %(message)s"
        )
    )
    uv_logger.addHandler(handler)

    logger.info("Initializing application ...")

    yield
    logger.info("Shutting down application...")


app = FastAPI(
    title="Hetida Designer Python Demo Adapter API",
    description="Hetida Designer Python Demo Adapter Web Services API",
    version=VERSION,
    lifespan=lifespan,
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
                logger.info("RECEIVED BODY (could not parse as json):\n%s", body.decode())
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
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail
                ) from exc

        return custom_route_handler


app.router.route_class = AdditionalLoggingRoute


demo_adapter_main_router = APIRouter()


@demo_adapter_main_router.get("/info", response_model=InfoResponse)
async def info() -> InfoResponse:
    return InfoResponse(
        id="python-demo-adapter",
        name="Python Demo Adapter",
        version=VERSION,
    )


@demo_adapter_main_router.get("/structure", response_model=StructureResponse)
async def structure(parentId: str | None = None) -> StructureResponse:
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

    return StructureResponse(
        id="python-demo-adapter",
        name="Python Demo Adapter",
        thingNodes=get_thing_nodes(parentId, include_sub_objects=False),
        sources=get_sources(parentId, include_sub_objects=False),
        sinks=get_sinks(parentId, include_sub_objects=False),
    )


@demo_adapter_main_router.get("/sources", response_model=MultipleSourcesResponse)
async def sources(filter_str: str | None = Query(None, alias="filter")) -> MultipleSourcesResponse:
    return_sources = get_sources(filter_str=filter_str, include_sub_objects=True)

    return MultipleSourcesResponse(resultCount=len(return_sources), sources=return_sources)


@demo_adapter_main_router.get("/sources/{sourceId}/metadata/", response_model=list[Metadatum])
async def get_all_metadata_source(sourceId: str) -> list[Metadatum]:
    if sourceId.endswith("temp") and "plantA" in sourceId:
        return [
            Metadatum(key="Max Value", value=300.0, dataType="float"),
            Metadatum(key="Min Value", value=-100.0, dataType="float"),
            Metadatum(key="Last Self-Check Okay", value=True, dataType="boolean"),
            get_metadatum_from_store(sourceId, "Sensor Config"),
        ]
    if sourceId.endswith("temp") and "plantB" in sourceId:
        return [
            Metadatum(key="Max Value", value=150.0, dataType="float"),
            Metadatum(key="Min Value", value=-30.0, dataType="float"),
            Metadatum(key="Last Self-Check Okay", value=True, dataType="boolean"),
            get_metadatum_from_store(sourceId, "Sensor Config"),
        ]
    if sourceId.endswith("anomaly_score") and "plantA" in sourceId:
        return [
            Metadatum(key="Max Value", value=1.0, dataType="float"),
            Metadatum(key="Min Value", value=0.0, dataType="float"),
            get_metadatum_from_store(sourceId, "Overshooting Allowed"),
        ]
    if sourceId.endswith("anomaly_score") and "plantB" in sourceId:
        return [
            Metadatum(key="Max Value", value=1.0, dataType="float"),
            Metadatum(key="Min Value", value=0.0, dataType="float"),
            get_metadatum_from_store(sourceId, "Overshooting Allowed"),
        ]

    return []


@demo_adapter_main_router.get("/sources/{sourceId}/metadata/{key}", response_model=Metadatum)
async def get_metadata_source_by_key(  # noqa: PLR0911, PLR0912
    sourceId: str, key: str
) -> Metadatum:
    key = unquote(key)
    if sourceId.endswith("temp") and "plantA" in sourceId:
        if key == "Max Value":
            return Metadatum(key="Max Value", value=300.0, dataType="float")
        if key == "Min Value":
            return Metadatum(key="Min Value", value=-100.0, dataType="float")
        if key == "Last Self-Check Okay":
            return Metadatum(key="Last Self-Check Okay", value=True, dataType="boolean")
        if key == "Sensor Config":
            return get_metadatum_from_store(sourceId, "Sensor Config")

    elif sourceId.endswith("temp") and "plantB" in sourceId:
        if key == "Max Value":
            return Metadatum(key="Max Value", value=150.0, dataType="float")
        if key == "Min Value":
            return Metadatum(key="Min Value", value=-30.0, dataType="float")
        if key == "Last Self-Check Okay":
            return Metadatum(key="Last Self-Check Okay", value=True, dataType="boolean")
        if key == "Sensor Config":
            return get_metadatum_from_store(sourceId, "Sensor Config")

    if sourceId.endswith("anomaly_score") and ("plantA" in sourceId or "plantB" in sourceId):
        if key == "Max Value":
            return Metadatum(key="Max Value", value=1.0, dataType="float")
        if key == "Min Value":
            return Metadatum(key="Min Value", value=0.0, dataType="float")
        if key == "Overshooting Allowed":
            return get_metadatum_from_store(sourceId, "Overshooting Allowed")
    raise HTTPException(
        status.HTTP_404_NOT_FOUND,
        f"Could not find metadatum attached to source '{sourceId}' with key '{key}'.",
    )


@demo_adapter_main_router.post(
    "/sources/{sourceId}/metadata/{key}", status_code=200, response_model=None
)
async def post_metadata_source_by_key(
    sourceId: str, key: str, metadatum: PostMetadatum
) -> dict | HTTPException:
    key = unquote(key)
    if sourceId.endswith("temp") and key == "Sensor Config":
        old_metadatum = get_metadatum_from_store(sourceId, key)

        new_metadatum = Metadatum(
            key=metadatum.key,
            value=metadatum.value,
            dataType=old_metadatum.dataType,
            isSink=old_metadatum.isSink or True,  # noqa: SIM222
        )

        set_metadatum_in_store(sourceId, key, new_metadatum)
        return {"message": "success"}
    if sourceId.endswith("anomaly_score") and key == "Overshooting Allowed":
        old_metadatum = get_metadatum_from_store(sourceId, key)

        new_metadatum = Metadatum(
            key=metadatum.key,
            value=metadatum.value,
            dataType=old_metadatum.dataType,
            isSink=old_metadatum.isSink or True,  # noqa: SIM222
        )

        set_metadatum_in_store(sourceId, key, new_metadatum)
        return {"message": "success"}
    raise HTTPException(
        status.HTTP_404_NOT_FOUND,
        f"There is no writable metadatum at source '{sourceId}' with key '{key}'.",
    )


@demo_adapter_main_router.get("/sources/{source_id:path}", response_model=StructureSource)
async def source(source_id: str) -> StructureSource:
    """Get a single source by id"""
    requested_sources = [
        src for src in get_sources(include_sub_objects=True) if src["id"] == source_id
    ]
    if len(requested_sources) > 1:
        msg = f"Error: Multiple sources with same id {str(requested_sources)}."
        logger.info(msg)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, msg)

    if len(requested_sources) < 1:
        msg = f"Requested source with id {source_id} not found."
        logger.info(msg)
        raise HTTPException(status.HTTP_404_NOT_FOUND, msg)
    return StructureSource.parse_obj(requested_sources[0])


@demo_adapter_main_router.get("/sinks", response_model=MultipleSinksResponse)
async def sinks(filter_str: str | None = Query(None, alias="filter")) -> MultipleSinksResponse:
    return_sinks = get_sinks(filter_str=filter_str, include_sub_objects=True)

    return MultipleSinksResponse(resultCount=len(return_sinks), sinks=return_sinks)


@demo_adapter_main_router.get("/sinks/{sinkId}/metadata/", response_model=list[Metadatum])
async def get_all_metadata_sink(sinkId: str) -> list[Metadatum]:
    if sinkId.endswith("anomaly_score") and "plantA" in sinkId:
        return [
            Metadatum(key="Max Value", value=1.0, dataType="float"),
            Metadatum(key="Min Value", value=0.0, dataType="float"),
            get_metadatum_from_store(sinkId, "Overshooting Allowed"),
        ]
    if sinkId.endswith("anomaly_score") and "plantB" in sinkId:
        return [
            Metadatum(key="Max Value", value=1.0, dataType="float"),
            Metadatum(key="Min Value", value=0.0, dataType="float"),
            get_metadatum_from_store(sinkId, "Overshooting Allowed"),
        ]
    return []


@demo_adapter_main_router.get("/sinks/{sinkId}/metadata/{key}", response_model=Metadatum)
async def get_metadata_sink_by_key(sinkId: str, key: str) -> Metadatum:
    key = unquote(key)

    if sinkId.endswith("anomaly_score") and ("plantA" in sinkId or "plantB" in sinkId):
        if key == "Max Value":
            return Metadatum(key="Max Value", value=1.0, dataType="float")
        if key == "Min Value":
            return Metadatum(key="Min Value", value=0.0, dataType="float")
        if key == "Overshooting Allowed":
            return get_metadatum_from_store(sinkId, "Overshooting Allowed")

    raise HTTPException(
        status.HTTP_404_NOT_FOUND,
        f"Could not find metadatum attached to sink '{sinkId}' with key '{key}'.",
    )


@demo_adapter_main_router.post(
    "/sinks/{sinkId}/metadata/{key}", status_code=200, response_model=None
)
async def post_metadata_sink_by_key(
    sinkId: str, key: str, metadatum: PostMetadatum
) -> dict | HTTPException:
    key = unquote(key)
    if sinkId.endswith("anomaly_score") and key == "Overshooting Allowed":
        old_metadatum = get_metadatum_from_store(sinkId, key)

        new_metadatum = Metadatum(
            key=metadatum.key,
            value=metadatum.value,
            dataType=old_metadatum.dataType,
            isSink=old_metadatum.isSink or True,  # noqa: SIM222
        )

        set_metadatum_in_store(sinkId, key, new_metadatum)
        return {"message": "success"}
    raise HTTPException(
        status.HTTP_404_NOT_FOUND,
        f"There is no writable metadatum at sink '{sinkId}' with key '{key}'.",
    )


@demo_adapter_main_router.get("/sinks/{sink_id}", response_model=StructureSink)
async def sink(sink_id: str) -> StructureSink:
    """Get a single sink by id"""
    requested_sinks = [snk for snk in get_sinks(include_sub_objects=True) if snk["id"] == sink_id]
    if len(requested_sinks) > 1:
        msg = f"Error: Multiple sinks with same id {str(requested_sinks)}."
        logger.info(msg)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, msg)

    if len(requested_sinks) < 1:
        msg = f"Requested sink with id {sink_id} not found."
        logger.info(msg)
        raise HTTPException(status.HTTP_404_NOT_FOUND, msg)
    return StructureSink.parse_obj(requested_sinks[0])


@demo_adapter_main_router.get("/thingNodes/{thingNodeId}/metadata/", response_model=list[Metadatum])
async def get_all_metadata_thingNode(thingNodeId: str) -> list[Metadatum]:
    if thingNodeId == "root.plantA":
        return [
            Metadatum(key="Location", value={"lat": 53.073635, "long": 8.806422}, dataType="any"),
            Metadatum(key="Temperature Unit", value="F", dataType="string"),
            Metadatum(key="Pressure Unit", value="psi", dataType="string"),
            Metadatum(
                # a metadatum that is not an explicit source and calculated dynamically
                key="Plant Age in Years",
                value=calculate_age(datetime.date(2012, 12, 7)),
                dataType="int",
            ),
            # this metadatum is a sink leaf but as a source only available attached to the thingNode
            get_metadatum_from_store(thingNodeId, "Anomaly State"),
        ]
    if thingNodeId == "root.plantB":
        return [
            Metadatum(key="Temperature Unit", value="C", dataType="string"),
            Metadatum(key="Pressure Unit", value="bar", dataType="string"),
            Metadatum(
                # a metadatum that is not an explicit source and calculated dynamically
                key="Plant Age in Years",
                value=calculate_age(datetime.date(2017, 8, 22)),
                dataType="int",
            ),
            # this metadatum is a sink leaf but as a source only available attached to the thingNode
            get_metadatum_from_store(thingNodeId, "Anomaly State"),
        ]
    return []


def calculate_age(born: datetime.date) -> int:
    today = datetime.date.today()  # noqa: DTZ011
    return today.year - born.year - int((today.month, today.day) < (born.month, born.day))


@demo_adapter_main_router.get("/thingNodes/{thingNodeId}/metadata/{key}", response_model=Metadatum)
async def get_metadata_thingNode_by_key(  # noqa: PLR0911, PLR0912
    thingNodeId: str, key: str, latex_mode: str = Query("", examples=["yes"])
) -> Metadatum:
    key = unquote(key)
    if thingNodeId == "root.plantA":
        if key == "Location":
            return Metadatum(
                key="Location", value={"lat": 53.073635, "long": 8.806422}, dataType="any"
            )
        if key == "Temperature Unit":
            return Metadatum(
                key="Temperature Unit",
                value=(
                    "$^\\circ$F"
                    if str.lower(latex_mode) in ("yes", "y", "on", "true", "1")
                    else "F"
                ),
                dataType="string",
            )
        if key == "Pressure Unit":
            return Metadatum(
                key="Pressure Unit",
                value="psi",
                dataType="string",
            )
        if key == "Plant Age in Years":
            return Metadatum(
                key="Plant Age in Years",
                value=calculate_age(datetime.date(2012, 12, 7)),
                dataType="int",
            )
        if key == "Anomaly State":
            return get_metadatum_from_store(thingNodeId, "Anomaly State")

    if thingNodeId == "root.plantB":
        if key == "Temperature Unit":
            return Metadatum(
                key="Temperature Unit",
                value=(
                    "$^\\circ$C"
                    if latex_mode != "" and str.lower(latex_mode) in ("yes", "y", "on", "true", "1")
                    else "C"
                ),
                dataType="string",
            )
        if key == "Pressure Unit":
            return Metadatum(
                key="Pressure Unit",
                value="bar",
                dataType="string",
            )
        if key == "Plant Age in Years":
            return Metadatum(
                key="Plant Age in Years",
                value=calculate_age(datetime.date(2017, 8, 22)),
                dataType="int",
            )
        if key == "Anomaly State":
            return get_metadatum_from_store(thingNodeId, "Anomaly State")
    raise HTTPException(
        status.HTTP_404_NOT_FOUND,
        f"Could not find metadatum attached/at thingNode '{thingNodeId}' with key '{key}'.",
    )


@demo_adapter_main_router.post(
    "/thingNodes/{thingNodeId}/metadata/{key}", status_code=200, response_model=None
)
async def post_metadata_thingNode_by_key(
    thingNodeId: str, key: str, metadatum: PostMetadatum
) -> dict | HTTPException:
    key = unquote(key)
    if thingNodeId in ["root.plantA", "root.plantB"]:
        old_metadatum = get_metadatum_from_store(thingNodeId, key)

        new_metadatum = Metadatum(
            key=metadatum.key,
            value=metadatum.value,
            dataType=old_metadatum.dataType,
            isSink=old_metadatum.isSink or True,  # noqa: SIM222
        )

        set_metadatum_in_store(thingNodeId, key, new_metadatum)
        return {"message": "success"}

    raise HTTPException(
        status.HTTP_404_NOT_FOUND,
        f"There is no writable metadatum at thingNode '{thingNodeId}' with key '{key}'.",
    )


@demo_adapter_main_router.get("/thingNodes/{id}", response_model=StructureThingNode)
async def thing_node(
    id: str,  # noqa: A002
) -> StructureThingNode:
    """Get a single sink by id"""
    requested_thing_nodes = [
        tn for tn in get_thing_nodes(include_sub_objects=True) if tn["id"] == id
    ]
    if len(requested_thing_nodes) > 1:
        msg = f"Error: Multiple ThingNodes with same id {str(requested_thing_nodes)}."
        logger.info(msg)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, msg)

    if len(requested_thing_nodes) < 1:
        msg = f"Requested ThingNode with id {id} not found."
        logger.info(msg)
        raise HTTPException(status.HTTP_404_NOT_FOUND, msg)
    return StructureThingNode.parse_obj(requested_thing_nodes[0])


def encode_attributes(data_attrs: Any) -> str:
    data_attrs_json_str = json.dumps(data_attrs)
    logger.debug("df_attrs_json_str=%s", data_attrs_json_str)
    data_attrs_bytes = data_attrs_json_str.encode("utf-8")
    base64_bytes = base64.b64encode(data_attrs_bytes)
    base64_str = base64_bytes.decode("utf-8")
    logger.debug("base64_str=%s", base64_str)
    return base64_str


def return_stored_anomaly_score(
    ts_id: str, from_timestamp: datetime.datetime, to_timestamp: datetime.datetime
) -> pd.DataFrame:
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
        ts_df.attrs = stored_df.attrs
    else:
        ts_df = pd.DataFrame(
            {
                "timestamp": [],
                "timeseriesId": [],
                "value": [],
            }
        )
    # do not overwrite stored attributes!
    ts_df.attrs.update(
        {
            "ref_interval_start_timestamp": from_timestamp.isoformat(),
            "ref_interval_stop_timestamp": to_timestamp.isoformat(),
            "ref_interval_type": "closed",
            "ref_metrics": [ts_id],
        }
    )

    return ts_df


@demo_adapter_main_router.get("/timeseries")
async def timeseries(
    ids: list[str] = Query(..., alias="id", min_length=1),
    from_timestamp: datetime.datetime = Query(
        ..., alias="from", examples=[datetime.datetime.now(datetime.timezone.utc)]
    ),
    to_timestamp: datetime.datetime = Query(
        ..., alias="to", examples=[datetime.datetime.now(datetime.timezone.utc)]
    ),
    frequency: str = Query("", examples=["5min"]),
) -> StreamingResponse:
    collected_attrs = {}
    io_stream = StringIO()

    dt_range = pd.date_range(
        start=from_timestamp, end=to_timestamp, freq="1h", tz=datetime.timezone.utc
    )
    for ts_id in ids:
        logger.debug("loading timeseries dataframe with id %s", str(ts_id))
        ts_df = None
        if ts_id.endswith("temp"):
            offset = 100.0 if "plantA" in ts_id else 30.0
            factor = 10.0 if "plantA" in ts_id else 5.0
        elif ts_id.endswith("press"):
            offset = 14.5 if "plantA" in ts_id else 1.0
            factor = 0.73 if "plantA" in ts_id else 0.05
        elif ts_id.endswith("anomaly_score"):
            ts_df = return_stored_anomaly_score(ts_id, from_timestamp, to_timestamp)
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

        if frequency != "" and ts_id == "root.plantA.picklingUnit.influx.temp":
            ts_df.index = ts_df["timestamp"]
            try:
                ts_df = ts_df.resample(frequency).first(numeric_only=False)
            except ValueError as error:
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    f"Provided value '{frequency}' for the filter 'frequency' is invalid! "
                    "Check the reference for pandas.DataFrame.resample for more information.",
                ) from error
        # throws warning during pytest:
        ts_df.to_json(io_stream, lines=True, orient="records", date_format="iso")

        if len(ts_df.attrs) != 0:
            logger.debug("which has attributes %s", str(ts_df.attrs))
            collected_attrs[ts_id] = ts_df.attrs
            collected_attrs[ts_id].update(
                {
                    "ref_interval_start_timestamp": from_timestamp.isoformat(),
                    "ref_interval_stop_timestamp": to_timestamp.isoformat(),
                    "ref_interval_type": "closed",
                    "ref_metrics": [ts_id],
                }
            )

    io_stream.seek(0)
    headers = {}
    if len(collected_attrs) != 0:
        headers["Data-Attributes"] = encode_attributes(collected_attrs)
    return StreamingResponse(io_stream, media_type="application/json", headers=headers)


def decode_attributes(data_attributes: str) -> Any:
    base64_bytes = data_attributes.encode("utf-8")
    logger.debug("data_attributes=%s", data_attributes)
    df_attrs_bytes = base64.b64decode(base64_bytes)
    df_attrs_json_str = df_attrs_bytes.decode("utf-8")
    logger.debug("df_attrs_json_str=%s", df_attrs_json_str)
    df_attrs = json.loads(df_attrs_json_str)
    return df_attrs


@demo_adapter_main_router.post("/timeseries", status_code=200)
async def post_timeseries(
    ts_body: list[TimeseriesRecord],
    ts_id: str = Query(..., alias="timeseriesId"),
    frequency: str = Query("", examples=["5min"]),
    data_attributes: str | None = Header(None),
) -> dict:
    logger.info("Received ts_body for id %s:\n%s", ts_id, str(ts_body))
    if ts_id.endswith("anomaly_score"):
        df = pd.DataFrame.from_dict((x.dict() for x in ts_body), orient="columns")
        if "timestamp" not in df.columns:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "Timeseries records need timestamp values!",
            )
        df.index = df["timestamp"]
        if frequency != "":
            try:
                df = df.resample(frequency).mean(numeric_only=False)
            except ValueError as error:
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    f"Provided value '{frequency}' for the filter 'frequency' is invalid! "
                    "Check the reference for pandas.DataFrame.resample for more information.",
                ) from error
        if data_attributes is not None and len(data_attributes) != 0:
            df_from_store: pd.DataFrame = get_value_from_store(ts_id)
            df.attrs = df_from_store.attrs
            df.attrs.update(decode_attributes(data_attributes))
        set_value_in_store(ts_id, df)
        logger.info(
            "stored timeseries %s in store: %s\n with columns %s",
            ts_id,
            str(df),
            str(df.columns),
        )
        return {"message": "success"}

    raise HTTPException(status.HTTP_404_NOT_FOUND, f"No writable timeseries with id '{ts_id}'.")


def parse_string_to_list(input_string: str) -> tuple[list, str]:
    decoded_input_string = input_string.encode("utf-8").decode("unicode_escape")
    try:
        list_from_string = json.loads(decoded_input_string)
    except json.decoder.JSONDecodeError:
        return (
            [],
            f"Value of column_names '{decoded_input_string}' cannot be parsed as JSON.",
        )
    else:
        if not isinstance(list_from_string, list):
            return (
                [],
                f"Value of column_names '{decoded_input_string}' is not a list.",
            )
        return (list_from_string, "")


@demo_adapter_main_router.get("/dataframe", response_model=None)
async def dataframe(
    df_id: str = Query(..., alias="id"),
    column_names: str = Query("", examples=["""[\\\"column1\\\", \\\"column2\\\"]"""]),
) -> StreamingResponse | HTTPException:
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
        df.attrs = {
            "ref_interval_start_timestamp": "2020-01-01T00:00:00+00:00",
            "ref_interval_stop_timestamp": datetime.datetime.now(tz=datetime.UTC).isoformat(),
            "ref_interval_type": "closed",
            "ref_metrics": [
                "component_id",
                "component_name",
                "maintenance_type",
                "timestamp",
            ],
        }
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
        df.attrs = {
            "ref_interval_start_timestamp": "2020-01-01T00:00:00+00:00",
            "ref_interval_stop_timestamp": datetime.datetime.now(tz=datetime.UTC).isoformat(),
            "ref_interval_type": "closed",
            "ref_metrics": [
                "component_id",
                "component_name",
                "maintenance_type",
                "timestamp",
            ],
        }
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
        df.attrs.update({"ref_metrics": ["name", "value"]})
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
        df.attrs.update({"ref_metrics": ["name", "value"]})
    elif df_id.endswith("alerts"):
        df = get_value_from_store(df_id)
        if column_names != "":
            column_name_list, error_msg = parse_string_to_list(column_names)
            if error_msg != "":
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    error_msg,
                )
            try:
                df = df[column_name_list]
            except KeyError as error:
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    f"Dataframe with id {df_id} contains columns {list(df)} "
                    f"but does not contain all columns of {column_name_list}.",
                ) from error
        df.attrs.update({"ref_metrics": df.columns.tolist()})
    else:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            f"No dataframe data available with provided id '{df_id}'.",
        )

    headers = {}
    logger.debug("loading dataframe %s", str(df))
    logger.debug("which has attributes %s", str(df.attrs))
    df_attrs = df.attrs
    if df_attrs is not None and len(df_attrs) != 0:
        headers["Data-Attributes"] = encode_attributes(df_attrs)

    io_stream = StringIO()
    df.to_json(io_stream, lines=True, orient="records", date_format="iso")
    io_stream.seek(0)

    return StreamingResponse(io_stream, media_type="application/json", headers=headers)


@demo_adapter_main_router.post("/dataframe", status_code=200)
async def post_dataframe(
    df_body: list[dict] = Body(
        ...,
        examples=[
            [
                {"column_A": 42.0, "column_B": "example"},
                {"column_A": 11.97, "column_B": "example"},
            ]
        ],
    ),
    df_id: str = Query(..., alias="id"),
    column_names: str = Query("", examples=["""[\\\"column1\\\", \\\"column2\\\"]"""]),
    data_attributes: str | None = Header(None),
) -> dict:
    if df_id.endswith("alerts"):
        df = pd.DataFrame.from_dict(df_body, orient="columns")
        if column_names != "":
            column_name_list, error_msg = parse_string_to_list(column_names)
            if error_msg != "":
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    error_msg,
                )
            try:
                df = df[column_name_list]
            except KeyError as error:
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    f"Dataframe with id {df_id} contains columns {list(df)} "
                    f"but does not contain all columns of {column_name_list}.",
                ) from error
        if data_attributes is not None and len(data_attributes) != 0:
            df_from_store: pd.DataFrame = get_value_from_store(df_id)
            df.attrs = df_from_store.attrs
            df.attrs.update(decode_attributes(data_attributes))
        logger.debug("storing %s", json.dumps(df_body))
        logger.debug("which has attributes %s", str(df.attrs))
        set_value_in_store(df_id, df)
        return {"message": "success"}

    raise HTTPException(status.HTTP_404_NOT_FOUND, f"No writable dataframe with id '{df_id}'.")


@demo_adapter_main_router.get("/multitsframe", response_model=None)
async def multitsframe(
    mtsf_id: str = Query(..., alias="id"),
    from_timestamp: datetime.datetime = Query(
        ..., alias="from", examples=[datetime.datetime.now(datetime.timezone.utc)]
    ),
    to_timestamp: datetime.datetime = Query(
        ..., alias="to", examples=[datetime.datetime.now(datetime.timezone.utc)]
    ),
    lower_threshold: str = Query("", examples=["93.4"]),
    upper_threshold: str = Query("", examples=["107.9"]),
) -> StreamingResponse | HTTPException:
    dt_range = pd.date_range(
        start=from_timestamp, end=to_timestamp, freq="h", tz=datetime.timezone.utc
    )
    mtsf = None
    if mtsf_id.endswith("temperatures"):
        offset = 100.0 if "plantA" in mtsf_id else 30.0
        factor = 10.0 if "plantA" in mtsf_id else 5.0
        mtsf_records = []
        metrics = [
            "Pickling Outfeed Temperature",
            "Pickling Influx Temperature",
            "Milling Outfeed Temperature",
            "Milling Influx Temperature",
        ]
        for metric in metrics:
            values = np.random.randn(len(dt_range)) * factor + offset
            ts_records = [
                {"timestamp": dt_range[idx], "metric": metric, "value": values[idx]}
                for idx in range(len(dt_range))
            ]
            mtsf_records.extend(ts_records)
        mtsf = pd.DataFrame.from_records(mtsf_records)
        if lower_threshold != "":
            try:
                lower_threshold_value = float(lower_threshold)
            except ValueError as error:
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    f"Cannot cast lower threshold '{lower_threshold}' to float:\n{error}",
                ) from error
            mtsf = mtsf[mtsf["value"] > lower_threshold_value]
        if upper_threshold != "":
            try:
                upper_threshold_value = float(upper_threshold)
            except ValueError as error:
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    f"Cannot cast lower threshold '{upper_threshold}' to float:\n{error}",
                ) from error
            mtsf = mtsf[mtsf["value"] < upper_threshold_value]
        mtsf.attrs.update(
            {
                "ref_interval_start_timestamp": from_timestamp.isoformat(),
                "ref_interval_stop_timestamp": to_timestamp.isoformat(),
                "ref_interval_type": "closed",
                "ref_metrics": metrics,
            }
        )
    elif mtsf_id.endswith("anomalies"):
        stored_mtsf = get_value_from_store(mtsf_id)
        stored_mtsf["timestamp"] = pd.to_datetime(stored_mtsf["timestamp"])
        mtsf = stored_mtsf[
            (np.array(stored_mtsf["timestamp"].dt.to_pydatetime()) > from_timestamp)
            & (np.array(stored_mtsf["timestamp"].dt.to_pydatetime()) < to_timestamp)
        ]
        mtsf.attrs.update(
            {
                "ref_interval_start_timestamp": from_timestamp.isoformat(),
                "ref_interval_stop_timestamp": to_timestamp.isoformat(),
                "ref_interval_type": "closed",
                "ref_metrics": mtsf["metric"].unique().tolist(),
            }
        )
    else:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            f"No multitsframe data available with provided id '{mtsf_id}'.",
        )

    headers = {}
    logger.debug("loading multitsframe %s", str(mtsf))
    logger.debug("which has attributes %s", str(mtsf.attrs))
    df_attrs = mtsf.attrs
    if df_attrs is not None and len(df_attrs) != 0:
        headers["Data-Attributes"] = encode_attributes(df_attrs)

    io_stream = StringIO()
    mtsf.to_json(io_stream, lines=True, orient="records", date_format="iso")
    io_stream.seek(0)

    return StreamingResponse(io_stream, media_type="application/json", headers=headers)


@demo_adapter_main_router.post("/multitsframe", status_code=200)
async def post_multitsframe(
    mtsf_body: list[dict] = Body(
        ...,
        examples=[
            [
                {
                    "metric": "Milling Influx Temperature",
                    "timestamp": "2020-03-11T13:45:18.194000000Z",
                    "value": 42.3,
                },
                {
                    "metric": "Milling Outfeed Temperature",
                    "timestamp": "2020-03-11T14:45:18.237000000Z",
                    "value": 41.7,
                },
                {
                    "metric": "Pickling Influx Temperature",
                    "timestamp": "2020-03-11T15:45:18.081000000Z",
                    "value": 18.4,
                },
                {
                    "metric": "Pickling Outfeed Temperature",
                    "timestamp": "2020-03-11T15:45:18.153000000Z",
                    "value": 18.3,
                },
            ]
        ],
    ),
    mtsf_id: str = Query(..., alias="id"),
    metric_names: str = Query("", examples=["""[\\\"metric1\\\", \\\"metric2\\\"]"""]),
    data_attributes: str | None = Header(None),
) -> dict:
    if mtsf_id in ("root.plantA.anomalies", "root.plantB.anomalies"):
        mtsf = pd.DataFrame.from_dict(mtsf_body, orient="columns")
        if metric_names != "":
            metric_name_list, error_msg = parse_string_to_list(metric_names)
            if error_msg != "":
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    error_msg,
                )
            try:
                mtsf = mtsf.loc[mtsf["metric"].isin(metric_name_list)]
            except KeyError as error:
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    f"Dataframe with id {mtsf_id} contains columns {list(mtsf)} "
                    f"but does not contain all columns of {metric_name_list}.",
                ) from error
        if set(mtsf.columns) != set(MULTITSFRAME_COLUMN_NAMES):
            column_names_string = ", ".join(mtsf.columns)
            multitsframe_column_names_string = ", ".join(MULTITSFRAME_COLUMN_NAMES)
            raise ValueError(
                f"Dataframe from storage has column names {column_names_string} that don't match "
                f"the column names required for a MultiTSFrame {multitsframe_column_names_string}."
            )
        if data_attributes is not None and len(data_attributes) != 0:
            df_from_store: pd.DataFrame = get_value_from_store(mtsf_id)
            mtsf.attrs = df_from_store.attrs
            mtsf.attrs.update(decode_attributes(data_attributes))
        logger.debug("storing %s", json.dumps(mtsf_body))
        logger.debug("which has attributes %s", str(mtsf.attrs))
        set_value_in_store(mtsf_id, mtsf)
        return {"message": "success"}

    raise HTTPException(status.HTTP_404_NOT_FOUND, f"No writable multitsframe with id '{mtsf_id}'.")


app.include_router(demo_adapter_main_router, prefix="")
