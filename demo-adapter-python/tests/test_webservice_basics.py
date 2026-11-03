import io
import json
from copy import deepcopy
from urllib.parse import quote

import numpy as np
import pandas as pd
import pytest
from hdhelpers.metadata.conventions import TimeseriesDataType, check_metadata_conventions
from httpx2 import AsyncClient
from starlette.testclient import TestClient

from demo_adapter_python.demo_data.sources import get_sources
from demo_adapter_python.external_types import ExternalType, GeneralType
from demo_adapter_python.in_memory_store import get_value_from_store
from demo_adapter_python.models import (
    Metadatum,
    StructureResponse,
    StructureSink,
    StructureSource,
    StructureThingNode,
)
from demo_adapter_python.webservice import app, decode_attributes, encode_attributes

client = TestClient(app)


@pytest.mark.asyncio
async def test_swagger_ui_available(async_test_client: AsyncClient) -> None:
    async with async_test_client as client:
        response = await client.get("/docs")
    assert response.status_code == 200
    assert "swagger-ui" in response.text.lower()


async def walk_thing_nodes(  # noqa: PLR0913, PLR0917
    parent_id: str,
    tn_append_list: list[StructureThingNode],
    src_append_list: list[StructureSource],
    snk_append_list: list[StructureSink],
    src_attached_metadata_dict: dict[tuple[str, str], Metadatum],
    snk_attached_metadata_dict: dict[tuple[str, str], Metadatum],
    tn_attached_metadata_dict: dict[tuple[str, str], Metadatum],
    open_async_test_client: AsyncClient,
) -> None:
    """Recursively walk thingnodes"""
    response_obj = (await open_async_test_client.get(f"/structure?parentId={parent_id}")).json()
    structure_response = StructureResponse(**response_obj)
    src_append_list += structure_response.sources
    snk_append_list += structure_response.sinks

    for src in structure_response.sources:
        metadata_src_response = (
            await open_async_test_client.get(f"/sources/{src.id}/metadata/")
        ).json()
        metadata_src = [Metadatum(**metadatum_json) for metadatum_json in metadata_src_response]
        for metadatum in metadata_src:
            src_attached_metadata_dict[(src.id, metadatum.key)] = metadatum

    for snk in structure_response.sinks:
        metadata_snk_response = (
            await open_async_test_client.get(f"/sinks/{snk.id}/metadata/")
        ).json()
        metadata_snk = [Metadatum(**metadatum_json) for metadatum_json in metadata_snk_response]
        for metadatum in metadata_snk:
            snk_attached_metadata_dict[(snk.id, metadatum.key)] = metadatum

    metadata_tn_response = (
        await open_async_test_client.get(f"/thingNodes/{parent_id}/metadata/")
    ).json()
    metadata_tn = [Metadatum(**metadatum_json) for metadatum_json in metadata_tn_response]
    for metadatum in metadata_tn:
        tn_attached_metadata_dict[(parent_id, metadatum.key)] = metadatum

    for tn in structure_response.thingNodes:
        tn_append_list.append(tn)
        await walk_thing_nodes(
            tn.id,
            tn_append_list,
            src_append_list,
            snk_append_list,
            src_attached_metadata_dict,
            snk_attached_metadata_dict,
            tn_attached_metadata_dict,
            open_async_test_client,
        )


@pytest.mark.filterwarnings(
    "ignore:an integer is required*"
)  # pandas to_json currently throws a deprecation warning
@pytest.mark.asyncio
async def test_resources_offered_from_structure_hierarchy(  # noqa: PLR0915, PLR0912
    async_test_client: AsyncClient,
) -> None:
    """Walks through the structure-hierarchy provided and gets/posts offered resources"""
    async with async_test_client as client:
        response_obj = (await client.get("/structure")).json()

        structure_response = StructureResponse(**response_obj)
        assert len(structure_response.sources) == 0
        assert len(structure_response.sinks) == 0

        roots = structure_response.thingNodes
        assert len(roots) == 1

        root = roots[0]

        all_tns: list[StructureThingNode] = []
        all_srcs: list[StructureSource] = []
        all_snks: list[StructureSink] = []
        tn_attached_metadata_dict: dict[tuple[str, str], Metadatum] = {}
        src_attached_metadata_dict: dict[tuple[str, str], Metadatum] = {}
        snk_attached_metadata_dict: dict[tuple[str, str], Metadatum] = {}

        await walk_thing_nodes(
            root.id,
            tn_append_list=all_tns,
            src_append_list=all_srcs,
            snk_append_list=all_snks,
            src_attached_metadata_dict=src_attached_metadata_dict,
            snk_attached_metadata_dict=snk_attached_metadata_dict,
            tn_attached_metadata_dict=tn_attached_metadata_dict,
            open_async_test_client=client,
        )

        assert len(all_tns) == 17
        assert len(all_srcs) == 42
        assert len(all_snks) == 17
        assert len(src_attached_metadata_dict) == 52
        assert len(snk_attached_metadata_dict) == 24
        assert len(tn_attached_metadata_dict) == 10

        for src in all_srcs:
            response_obj = (await client.get(f"/sources/{src.id}")).json()
            assert src == StructureSource(**response_obj)

        for snk in all_snks:
            response_obj = (await client.get(f"/sinks/{snk.id}")).json()
            assert snk == StructureSink(**response_obj)

        for tn in all_tns:
            response_obj = (await client.get(f"/thingNodes/{tn.id}")).json()
            assert tn == StructureThingNode(**response_obj)

        # we actually get all metadata that is available as attached to something:
        for (src_id, key), md in src_attached_metadata_dict.items():
            response_obj = (await client.get(f"/sources/{src_id}/metadata/{key}")).json()
            print(response_obj, "versus", md)
            assert response_obj["key"] == key
            assert response_obj["value"] == md.value
            assert response_obj["dataType"] == md.dataType

            if md.isSink is not None and md.isSink is True:
                assert response_obj["isSink"] is True
                resp = await client.post(f"/sources/{src_id}/metadata/{key}", json=md.model_dump())
                assert resp.status_code == 200

        for (snk_id, key), md in snk_attached_metadata_dict.items():
            response_obj = (await client.get(f"/sinks/{snk_id}/metadata/{key}")).json()
            print(response_obj, "versus", md)
            assert response_obj["key"] == key
            assert response_obj["value"] == md.value
            assert response_obj["dataType"] == md.dataType

            if md.isSink is not None and md.isSink is True:
                assert response_obj["isSink"] is True
                resp = await client.post(f"/sinks/{snk_id}/metadata/{key}", json=md.model_dump())
                assert resp.status_code == 200

        for (tn_id, key), md in tn_attached_metadata_dict.items():
            response_obj = (await client.get(f"/thingNodes/{tn_id}/metadata/{key}")).json()
            print(response_obj, "versus", md)
            assert response_obj["key"] == key
            assert response_obj["value"] == md.value
            assert response_obj["dataType"] == md.dataType

            if md.isSink is not None and md.isSink:
                assert response_obj["isSink"]
                resp = await client.post(
                    f"/thingNodes/{tn_id}/metadata/{key}", json=md.model_dump()
                )
                assert resp.status_code == 200

        # all metadata that is a source in the tree is also found
        for src in all_srcs:
            if src.type.startswith("metadata"):
                response_obj = (
                    await client.get(f"/thingNodes/{src.thingNodeId}/metadata/{src.metadataKey}")
                ).json()
                print(response_obj, "versus", src)

                assert response_obj["key"] == src.metadataKey
                value_datatype = ExternalType(src.type).value_datatype
                assert value_datatype is not None
                assert response_obj["dataType"] == (value_datatype.value)

            if src.type.startswith("dataframe"):
                response = await client.get(f"/dataframe?id={src.id}")
                lines = response.text.splitlines()
                for line in lines:
                    print(line)
                    if len(line) > 0:
                        json.loads(line)

            if src.type.startswith("multitsframe"):
                response = await client.get(
                    f"/multitsframe?id={src.id}&from={quote('2020-01-01T00:00:00.000000000Z')}"
                    f"&to={quote('2020-01-02T00:00:00.0000000Z')}"
                )
                assert response.status_code == 200
                lines = response.text.splitlines()
                for line in lines:
                    print(line)
                    if len(line) > 0:
                        json.loads(line)

            if src.type.startswith("singletsframe"):
                response = await client.get(
                    f"/singletsframe?id={src.id}&from={quote('2020-01-01T00:00:00.000000000Z')}"
                    f"&to={quote('2020-01-02T00:00:00.0000000Z')}"
                )
                assert response.status_code == 200
                lines = response.text.splitlines()
                for line in lines:
                    print(line)
                    if len(line) > 0:
                        record = json.loads(line)
                        # a singletsframe has no metric column
                        assert "timestamp" in record
                        assert "metric" not in record

            if src.type.startswith("timeseries"):
                response = await client.get(
                    f"/timeseries?id={src.id}&from={quote('2020-01-01T00:00:00.000000000Z')}"
                    f"&to={quote('2020-01-02T00:00:00.0000000Z')}"
                )
                assert response.status_code == 200
                lines = response.text.splitlines()
                for line in lines:
                    print(line)
                    if len(line) > 0:
                        json.loads(line)

        # metadata that is a sink in the tree is also always obtainable
        for snk in all_snks:
            if snk.type.startswith("metadata"):
                response_obj = (
                    await client.get(f"/thingNodes/{snk.thingNodeId}/metadata/{snk.metadataKey}")
                ).json()
                print(response_obj, "versus", snk)

                assert response_obj["key"] == snk.metadataKey
                value_datatype = ExternalType(snk.type).value_datatype
                assert value_datatype is not None
                assert response_obj["dataType"] == (value_datatype.value)

                resp = await client.post(
                    f"/thingNodes/{snk.thingNodeId}/metadata/{snk.metadataKey}",
                    json=response_obj,
                )

                assert resp.status_code == 200

            if snk.type.startswith("dataframe"):
                print("Posting something for dataframe sink:", snk)
                response = await client.post(
                    f"/dataframe?id={snk.id}",
                    json=[
                        {"a": 14.5, "b": 12.3},
                        {"a": 13.5, "b": 11.9},
                    ],
                )
                assert response.status_code == 200

            if snk.type.startswith("multitsframe"):
                print("Posting something for multitsframe sink:", snk)
                response = await client.post(
                    f"/multitsframe?id={snk.id}",
                    json=[
                        {
                            "metric": "b",
                            "timestamp": "2020-01-01T00:00:00.000Z",
                            "value": 12.3,
                        },
                        {
                            "metric": "b",
                            "timestamp": "2020-01-02T00:00:00.000Z",
                            "value": 11.9,
                        },
                    ],
                )
                assert response.status_code == 200

            if snk.type.startswith("timeseries"):
                print("Posting something for timeseries sink:", snk)
                response = await client.post(
                    f"/timeseries?timeseriesId={snk.id}",
                    json=[
                        {"timestamp": "2020-01-01T00:00:00.000000000Z", "value": 12.3},
                        {"timestamp": "2020-01-02T00:00:00.000000000Z", "value": 11.9},
                    ],
                )
                assert response.status_code == 200


@pytest.mark.asyncio
async def test_post_metadata_of_thing_node_get_metadata_of_thing_node(
    async_test_client: AsyncClient,
) -> None:
    async with async_test_client as client:
        thingNodeId = "root.plantA"
        key = "Anomaly State"
        value = True
        post_metadatum_json = {"key": key, "value": value}

        post_response = await client.post(
            f"/thingNodes/{thingNodeId}/metadata/{quote(key)}", json=post_metadatum_json
        )

        assert post_response.status_code == 200

        get_response = await client.get(f"/thingNodes/{thingNodeId}/metadata/{quote(key)}")

        assert get_response.status_code == 200
        assert get_response.json()["value"] == value


@pytest.mark.asyncio
async def test_post_metadata_to_sink_get_metadata_from_source(
    async_test_client: AsyncClient,
) -> None:
    async with async_test_client as client:
        sinkId = "root.plantA.picklingUnit.influx.anomaly_score"
        key = "Overshooting Allowed"
        value = True
        post_metadatum_json = {"key": key, "value": value}
        post_response = await client.post(
            f"/sinks/{sinkId}/metadata/{quote(key)}", json=post_metadatum_json
        )

        assert post_response.status_code == 200

        sourceId = sinkId
        get_response = await client.get(f"/sources/{sourceId}/metadata/{quote(key)}")

        assert get_response.status_code == 200
        assert get_response.json()["value"] == value


@pytest.mark.asyncio
async def test_sending_attrs_via_get_dataframe(async_test_client: AsyncClient) -> None:
    async with async_test_client as client:
        response = await client.get("/dataframe?id=root.plantA.maintenance_events")

        assert response.status_code == 200
        assert "Data-Attributes" in response.headers
        assert isinstance(response.headers["Data-Attributes"], str)

        df_attrs = decode_attributes(response.headers["Data-Attributes"])

        assert "ref_interval_start_timestamp" in df_attrs
        assert df_attrs["ref_interval_start_timestamp"] == "2020-01-01T00:00:00+00:00"


@pytest.mark.asyncio
async def test_receiving_attrs_via_post_dataframe(
    async_test_client: AsyncClient,
) -> None:
    async with async_test_client as client:
        df_attrs = {"test": "Hello world!", "answer": 42}
        base64_str = encode_attributes(df_attrs)

        response = await client.post(
            "/dataframe?id=root.plantA.alerts",
            json=[{"column1": 1, "column2": 1.3}, {"column1": 2, "column2": 2.8}],
            headers={"Data-Attributes": base64_str},
        )

        assert response.status_code == 200

        df_from_store = get_value_from_store("root.plantA.alerts")

        assert len(df_from_store.attrs) != 0
        assert "test" in df_from_store.attrs
        for key, value in df_attrs.items():
            assert df_from_store.attrs[key] == value


@pytest.mark.asyncio
async def test_updating_and_keeping_existing_attrs_for_dataframe(
    async_test_client: AsyncClient,
) -> None:
    async with async_test_client as client:
        df_attrs_1 = {"test": "Hello world!", "answer": 42}
        base64_str_1 = encode_attributes(df_attrs_1)

        response_1 = await client.post(
            "/dataframe?id=root.plantA.alerts",
            json=[{"column1": 1, "column2": 1.3}, {"column1": 2, "column2": 2.8}],
            headers={"Data-Attributes": base64_str_1},
        )

        assert response_1.status_code == 200

        df_from_store_1 = get_value_from_store("root.plantA.alerts")

        assert len(df_from_store_1.attrs) != 0
        assert "test" in df_from_store_1.attrs
        for key, value in df_attrs_1.items():
            assert df_from_store_1.attrs[key] == value

        df_attrs_2 = {"test": "test"}
        base64_str_2 = encode_attributes(df_attrs_2)

        response_2 = await client.post(
            "/dataframe?id=root.plantA.alerts",
            json=[{"column1": 1, "column2": 1.3}, {"column1": 2, "column2": 2.8}],
            headers={"Data-Attributes": base64_str_2},
        )

        assert response_2.status_code == 200

        df_from_store_2 = get_value_from_store("root.plantA.alerts")

        df_attrs = deepcopy(df_attrs_1)
        df_attrs.update(df_attrs_2)

        assert len(df_from_store_2.attrs) != 0
        assert "test" in df_from_store_2.attrs
        for key, value in df_attrs.items():
            assert df_from_store_2.attrs[key] == value


@pytest.mark.asyncio
async def test_sending_attrs_via_get_multitsframe(
    async_test_client: AsyncClient,
) -> None:
    async with async_test_client as client:
        response = await client.get(
            f"/multitsframe?id=root.plantA.anomalies"
            f"&from={quote('2020-01-01T00:00:00.000000000Z')}"
            f"&to={quote('2020-01-01T00:00:00.000000000Z')}"
        )

        assert response.status_code == 200
        assert "Data-Attributes" in response.headers
        assert isinstance(response.headers["Data-Attributes"], str)

        df_attrs = decode_attributes(response.headers["Data-Attributes"])

        # metrics written by other tests
        stored_metrics = sorted(set(get_value_from_store("root.plantA.anomalies")["metric"]))
        assert df_attrs["dataset_metadata"] == {
            "metric_key": "id",
            "queried_metrics": stored_metrics,
            "ref_interval_start_timestamp": "2020-01-01T00:00:00+00:00",
            "ref_interval_end_timestamp": "2020-01-01T00:00:00+00:00",
            "ref_interval_type": "closed",
            # the time zone of the plant, for all written metrics
            "default_timezone": "Europe/Berlin",
        }
        assert [metric["id"] for metric in df_attrs["metrics"]] == stored_metrics


@pytest.mark.asyncio
async def test_metadata_of_written_multitsframe(async_test_client: AsyncClient) -> None:
    async with async_test_client as client:
        mtsf_id = "root.plantB.anomalies"
        await client.post(
            f"/multitsframe?id={mtsf_id}",
            json=[
                {"metric": "b", "timestamp": "2020-01-01T00:00:00Z", "value": 12.3},
                {"metric": "a", "timestamp": "2020-01-03T00:00:00Z", "value": 11.9},
            ],
            headers={"Data-Attributes": encode_attributes({"test": "Hello world!"})},
        )

        response = await client.get(
            f"/multitsframe?id={mtsf_id}"
            f"&from={quote('2020-01-01T12:00:00+02:00')}"
            f"&to={quote('2020-01-02T02:00:00+02:00')}"
        )

        df_attrs = decode_attributes(response.headers["Data-Attributes"])

        # all written metrics, also those without data in the interval
        assert df_attrs == {
            "dataset_metadata": {
                "metric_key": "id",
                "queried_metrics": ["a", "b"],
                "ref_interval_start_timestamp": "2020-01-01T10:00:00+00:00",
                "ref_interval_end_timestamp": "2020-01-02T00:00:00+00:00",
                "ref_interval_type": "closed",
                "default_timezone": "America/New_York",
            },
            "metrics": [
                {
                    "id": metric,
                    "name": metric,
                    "value_dimensions": [{"column": "value", "unit": None, "measurement": None}],
                }
                for metric in ["a", "b"]
            ],
        }


@pytest.mark.asyncio
async def test_written_multitsframe_is_read_in_closed_interval(
    async_test_client: AsyncClient,
) -> None:
    async with async_test_client as client:
        mtsf_id = "root.plantB.anomalies"
        await client.post(
            f"/multitsframe?id={mtsf_id}",
            json=[
                {"metric": "a", "timestamp": timestamp, "value": 1.0}
                for timestamp in [
                    "2020-01-01T00:00:00.000Z",
                    "2020-01-01T02:00:00.000Z",
                    "2020-01-01T04:00:00.000Z",
                    "2020-01-01T04:00:00.001Z",
                ]
            ],
        )

        response = await client.get(
            "/multitsframe",
            params={"id": mtsf_id, "from": "2020-01-01T00:00:00Z", "to": "2020-01-01T04:00:00Z"},
        )

        mtsf = pd.read_json(io.StringIO(response.text), lines=True)
        df_attrs = decode_attributes(response.headers["Data-Attributes"])

        # the start and the end belong to the closed ref interval
        assert df_attrs["dataset_metadata"]["ref_interval_type"] == "closed"
        assert list(pd.to_datetime(mtsf["timestamp"]).dt.strftime("%H:%M:%S.%f")) == [
            "00:00:00.000000",
            "02:00:00.000000",
            "04:00:00.000000",
        ]


@pytest.mark.asyncio
async def test_metadata_of_temperatures_multitsframe(async_test_client: AsyncClient) -> None:
    async with async_test_client as client:
        response = await client.get(
            "/multitsframe?id=root.plantA.temperatures"
            f"&from={quote('2020-01-01T00:00:00Z')}"
            f"&to={quote('2020-01-01T05:00:00Z')}"
        )

        mtsf = pd.read_json(io.StringIO(response.text), lines=True)
        df_attrs = decode_attributes(response.headers["Data-Attributes"])

        assert df_attrs["dataset_metadata"]["metric_key"] == "name"
        assert set(df_attrs["dataset_metadata"]["queried_metrics"]) == set(mtsf["metric"])
        assert [metric["name"] for metric in df_attrs["metrics"]] == df_attrs["dataset_metadata"][
            "queried_metrics"
        ]
        assert df_attrs["metrics"][1] == {
            "id": "root.plantA.picklingUnit.influx.temp",
            "name": "Pickling Influx Temperature",
            "value_dimensions": [
                {
                    "column": "value",
                    "unit": "°C",
                    "measurement": "temperature",
                    "value_data_type": "float",
                    "decimals": 1,
                }
            ],
            "default_aggregation_method": "MEAN",
            "default_timezone": "Europe/Berlin",
            "path": ["Plant A", "Pickling Unit", "Influx"],
            "origin": "simulated",
            "recording_mode": "periodic",
            "data_frequency": "1h",
        }


@pytest.mark.asyncio
async def test_metadata_of_singletsframe(async_test_client: AsyncClient) -> None:
    async with async_test_client as client:
        stsf_id = "root.plantB.picklingUnit.influx.temp_with_state"
        response = await client.get(
            f"/singletsframe?id={stsf_id}"
            f"&from={quote('2020-01-01T00:00:00Z')}"
            f"&to={quote('2020-01-01T05:00:00Z')}"
        )

        df_attrs = decode_attributes(response.headers["Data-Attributes"])

        assert df_attrs["dataset_metadata"] == {
            "metric_key": "id",
            "single_metric": stsf_id,
            "queried_metrics": [stsf_id],
            "ref_interval_start_timestamp": "2020-01-01T00:00:00+00:00",
            "ref_interval_end_timestamp": "2020-01-01T05:00:00+00:00",
            "ref_interval_type": "closed",
        }
        assert [metric["id"] for metric in df_attrs["metrics"]] == [stsf_id]
        assert [
            (value_dimension["column"], value_dimension["unit"])
            for value_dimension in df_attrs["metrics"][0]["value_dimensions"]
        ] == [("value", "°F"), ("state", "")]
        assert df_attrs["metrics"][0]["default_timezone"] == "America/New_York"


@pytest.mark.asyncio
async def test_receiving_attrs_via_post_multitsframe(
    async_test_client: AsyncClient,
) -> None:
    async with async_test_client as client:
        df_attrs = {"test": "Hello world!", "answer": 42}
        base64_str = encode_attributes(df_attrs)
        mtsf_id = "root.plantA.anomalies"

        response = await client.post(
            f"/multitsframe?id={mtsf_id}",
            json=[
                {
                    "metric": "b",
                    "timestamp": "2020-01-01T00:00:00.000000000Z",
                    "value": 12.3,
                },
                {
                    "metric": "b",
                    "timestamp": "2020-01-02T00:00:00.000000000Z",
                    "value": 11.9,
                },
            ],
            headers={"Data-Attributes": base64_str},
        )

        assert response.status_code == 200

        df_from_store = get_value_from_store(mtsf_id)

        assert len(df_from_store.attrs) != 0
        assert "test" in df_from_store.attrs
        for key, value in df_attrs.items():
            assert df_from_store.attrs[key] == value


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("frequency", "expected_timestamps"),
    [
        ("2h", ["00:00", "02:00", "04:00"]),
        # intervals without a value are left out
        ("30min", ["00:00", "01:00", "02:00", "03:00", "04:00", "05:00"]),
    ],
)
async def test_resampled_timeseries_without_empty_intervals(
    async_test_client: AsyncClient, frequency: str, expected_timestamps: list[str]
) -> None:
    async with async_test_client as client:
        ts_id = "root.plantA.picklingUnit.influx.temp"

        response = await client.get(
            "/timeseries",
            params={
                "id": ts_id,
                "from": "2020-01-01T00:00:00Z",
                "to": "2020-01-01T05:00:00Z",
                "frequency": frequency,
            },
        )

        assert response.status_code == 200
        timeseries = pd.read_json(io.StringIO(response.text), lines=True)
        assert list(pd.to_datetime(timeseries["timestamp"]).dt.strftime("%H:%M")) == (
            expected_timestamps
        )
        assert list(timeseries["timeseriesId"].unique()) == [ts_id]
        assert timeseries["value"].notna().all()


@pytest.mark.asyncio
async def test_sending_attrs_via_get_timeseries(async_test_client: AsyncClient) -> None:
    async with async_test_client as client:
        ts_id = "root.plantA.picklingUnit.influx.anomaly_score"

        response = await client.get(
            f"/timeseries?id={ts_id}"
            f"&from={quote('2020-01-01T00:00:00.000000000Z')}"
            f"&to={quote('2020-01-01T00:00:00.000000000Z')}"
        )

        assert response.status_code == 200
        assert "Data-Attributes" in response.headers
        assert isinstance(response.headers["Data-Attributes"], str)

        df_attrs = decode_attributes(response.headers["Data-Attributes"])

        assert df_attrs == {
            ts_id: {
                "dataset_metadata": {
                    "metric_key": "id",
                    "single_metric": ts_id,
                    "queried_metrics": [ts_id],
                    "ref_interval_start_timestamp": "2020-01-01T00:00:00+00:00",
                    "ref_interval_end_timestamp": "2020-01-01T00:00:00+00:00",
                    "ref_interval_type": "closed",
                },
                "metrics": [
                    {
                        "id": ts_id,
                        "name": "Influx Anomaly Score",
                        "value_dimensions": [
                            {
                                "column": "value",
                                "unit": "",  # dimensionless
                                "measurement": "anomaly score",
                                "value_data_type": "float",
                                "decimals": 3,
                            }
                        ],
                        "default_aggregation_method": "MAX",
                        # nothing is known about the recording of written data, but the
                        # time zone of the plant applies
                        "default_timezone": "Europe/Berlin",
                        "path": ["Plant A", "Pickling Unit", "Influx"],
                    }
                ],
            }
        }


@pytest.mark.asyncio
async def test_metadata_of_each_timeseries(async_test_client: AsyncClient) -> None:
    async with async_test_client as client:
        ts_ids = [
            "root.plantA.picklingUnit.influx.temp",
            "root.plantB.millingUnit.outfeed.press",
            "unknown.timeseries",
        ]

        response = await client.get(
            "/timeseries",
            params={"id": ts_ids, "from": "2020-01-01T00:00:00Z", "to": "2020-01-01T03:00:00Z"},
        )

        df_attrs = decode_attributes(response.headers["Data-Attributes"])

        assert list(df_attrs) == ts_ids
        assert [
            (metric["name"], metric["value_dimensions"][0]["unit"])
            for ts_id in ts_ids
            for metric in df_attrs[ts_id]["metrics"]
        ] == [
            ("Influx Temperature", "°C"),
            ("Outfeed Pressure", "psi"),
            ("unknown.timeseries", None),
        ]
        assert [df_attrs[ts_id]["metrics"][0].get("path") for ts_id in ts_ids] == [
            ["Plant A", "Pickling Unit", "Influx"],
            ["Plant B", "Milling Unit", "Outfeed"],
            None,
        ]
        assert {df_attrs[ts_id]["metrics"][0]["data_frequency"] for ts_id in ts_ids} == {"1h"}
        assert [
            df_attrs[ts_id]["metrics"][0]["value_dimensions"][0].get("decimals") for ts_id in ts_ids
        ] == [1, 1, None]
        assert [df_attrs[ts_id]["metrics"][0].get("default_timezone") for ts_id in ts_ids] == [
            "Europe/Berlin",
            "America/New_York",
            None,
        ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("frequency", "expected_timestamps", "expected_values"),
    [
        # the first value of each interval, labelled by its start
        ("2h", ["00:00", "02:00", "04:00"], [38.0, 49.0, 60.0]),
        ("150min", ["00:00", "02:30", "05:00"], [38.0, 54.5, 65.5]),
        # intervals without a value are gaps
        ("30min", ["00:00", "01:00", "02:00", "03:00", "04:00", "05:00"], None),
    ],
)
async def test_metadata_of_resampled_timeseries(
    async_test_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    frequency: str,
    expected_timestamps: list[str],
    expected_values: list[float] | None,
) -> None:
    # simulated hourly values 38, 43.5, 49, ... (°C)
    monkeypatch.setattr(np.random, "randn", lambda n: np.arange(n, dtype=float))
    async with async_test_client as client:
        ts_id = "root.plantA.picklingUnit.influx.temp"

        response = await client.get(
            "/timeseries",
            params={
                "id": ts_id,
                "from": "2020-01-01T00:00:00Z",
                "to": "2020-01-01T05:00:00Z",
                "frequency": frequency,
            },
        )

        timeseries = pd.read_json(io.StringIO(response.text), lines=True)
        metric = decode_attributes(response.headers["Data-Attributes"])[ts_id]["metrics"][0]

        assert list(pd.to_datetime(timeseries["timestamp"]).dt.strftime("%H:%M")) == (
            expected_timestamps
        )
        assert timeseries["value"].notna().all()
        if expected_values is not None:
            assert list(timeseries["value"]) == expected_values
        assert {key: metric[key] for key in ("recording_mode", "data_frequency")} == {
            "recording_mode": "periodic",
            "data_frequency": frequency,
        }
        assert metric["recording_aggregation_method"] == "FIRST"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("frequency", "expected_timestamps"),
    [
        # the interval starting at 00:00 is only partially queried
        ("1h", ["01:00", "02:00", "03:00", "04:00", "05:00"]),
        ("2h", ["02:00", "04:00"]),
    ],
)
async def test_resampled_timeseries_starts_in_ref_interval(
    async_test_client: AsyncClient, frequency: str, expected_timestamps: list[str]
) -> None:
    async with async_test_client as client:
        ts_id = "root.plantA.picklingUnit.influx.temp"

        response = await client.get(
            "/timeseries",
            params={
                "id": ts_id,
                "from": "2020-01-01T00:30:00Z",
                "to": "2020-01-01T05:30:00Z",
                "frequency": frequency,
            },
        )

        timeseries = pd.read_json(io.StringIO(response.text), lines=True)
        dataset_metadata = decode_attributes(response.headers["Data-Attributes"])[ts_id][
            "dataset_metadata"
        ]

        assert list(pd.to_datetime(timeseries["timestamp"]).dt.strftime("%H:%M")) == (
            expected_timestamps
        )
        assert dataset_metadata["ref_interval_start_timestamp"] == "2020-01-01T00:30:00+00:00"
        assert dataset_metadata["ref_interval_end_timestamp"] == "2020-01-01T05:30:00+00:00"


async def load_like_the_runtime(
    client: AsyncClient, source: dict, params: dict[str, str]
) -> tuple[pd.Series | pd.DataFrame, TimeseriesDataType]:
    """The data of a source with its metadata as the runtime provides it to workflows"""
    general_type = ExternalType(source["type"]).general_type
    response = await client.get(f"/{general_type.value}", params={"id": source["id"]} | params)
    assert response.status_code == 200
    frame = pd.read_json(io.StringIO(response.text), lines=True)
    if len(frame.columns) == 0:  # no data in the interval
        frame = pd.DataFrame(
            columns=["timestamp", "metric", "value"]
            if general_type == GeneralType.MULTITSFRAME
            else ["timestamp", "value"]
        )
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    attrs = decode_attributes(response.headers["Data-Attributes"])
    if general_type == GeneralType.TIMESERIES:
        series = frame.set_index("timestamp")["value"]
        series.attrs = attrs[source["id"]]
        return series, "SERIES"
    frame.attrs = attrs
    return frame, "MULTITSFRAME" if general_type == GeneralType.MULTITSFRAME else "SINGLETSFRAME"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "params",
    [
        {"from": "2020-01-01T00:30:00+02:00", "to": "2020-01-02T02:00:00+02:00"},
        # resampled
        {"from": "2020-01-01T00:30:00Z", "to": "2020-01-01T05:30:00Z", "frequency": "2h"},
        {"from": "2020-01-01T00:00:00Z", "to": "2020-01-01T05:00:00Z", "frequency": "30min"},
    ],
)
async def test_metadata_of_all_timeseries_sources_follows_the_conventions(
    async_test_client: AsyncClient, params: dict[str, str]
) -> None:
    """The metadata of every source matches its data

    The dev setups let executions fail on metadata of this adapter not following the metadata
    conventions (ADAPTER_METADATA_VALIDATION of the runtime).
    """
    async with async_test_client as client:
        # data written to this adapter before, which is read back
        await client.post(
            "/timeseries",
            params={"timeseriesId": "root.plantB.picklingUnit.outfeed.anomaly_score"},
            json=[{"timestamp": "2020-01-01T03:00:00Z", "value": 0.5}],
        )
        await client.post(
            "/multitsframe",
            params={"id": "root.plantB.anomalies"},
            json=[{"metric": "a", "timestamp": "2020-01-01T03:00:00Z", "value": 1.0}],
        )
        sources = [
            source
            for source in get_sources(include_sub_objects=True)
            if ExternalType(source["type"]).general_type
            in (GeneralType.TIMESERIES, GeneralType.MULTITSFRAME, GeneralType.SINGLETSFRAME)
        ]

        issues_by_source = {}
        for source in sources:
            obj, data_type = await load_like_the_runtime(client, source, params)
            if len(issues := check_metadata_conventions(obj, data_type)) > 0:
                issues_by_source[source["id"]] = issues

    assert len(sources) == 31
    assert issues_by_source == {}


@pytest.mark.asyncio
async def test_receiving_attrs_via_post_timeseries(
    async_test_client: AsyncClient,
) -> None:
    async with async_test_client as client:
        df_attrs = {"test": "Hello world!", "answer": 42}
        base64_str = encode_attributes(df_attrs)
        ts_id = "root.plantA.picklingUnit.influx.anomaly_score"

        response = await client.post(
            f"/timeseries?timeseriesId={ts_id}",
            json=[
                {"timestamp": "2020-01-01T00:00:00.000000000Z", "value": 12.3},
                {"timestamp": "2020-01-02T00:00:00.000000000Z", "value": 11.9},
            ],
            headers={"Data-Attributes": base64_str},
        )

        assert response.status_code == 200

        df_from_store = get_value_from_store(ts_id)

        assert len(df_from_store.attrs) != 0
        assert "test" in df_from_store.attrs
        for key, value in df_attrs.items():
            assert df_from_store.attrs[key] == value


@pytest.mark.asyncio
async def test_updating_and_keeping_existing_attrs_for_timeseries(
    async_test_client: AsyncClient,
) -> None:
    async with async_test_client as client:
        ts_id = "root.plantA.picklingUnit.influx.anomaly_score"

        df_attrs_1 = {"test": "Hello world!", "answer": 42}
        base64_str_1 = encode_attributes(df_attrs_1)

        response_1 = await client.post(
            f"/timeseries?timeseriesId={ts_id}",
            json=[
                {"timestamp": "2020-01-01T00:00:00.000000000Z", "value": 12.3},
                {"timestamp": "2020-01-02T00:00:00.000000000Z", "value": 11.9},
            ],
            headers={"Data-Attributes": base64_str_1},
        )

        assert response_1.status_code == 200

        df_from_store_1 = get_value_from_store(ts_id)

        assert len(df_from_store_1.attrs) != 0
        assert "test" in df_from_store_1.attrs
        for key, value in df_attrs_1.items():
            assert df_from_store_1.attrs[key] == value

        df_attrs_2 = {"test": "test"}
        base64_str_2 = encode_attributes(df_attrs_2)

        response_2 = await client.post(
            f"/timeseries?timeseriesId={ts_id}",
            json=[
                {"timestamp": "2020-01-01T00:00:00.000000000Z", "value": 12.3},
                {"timestamp": "2020-01-02T00:00:00.000000000Z", "value": 11.9},
            ],
            headers={"Data-Attributes": base64_str_2},
        )

        assert response_2.status_code == 200

        df_from_store_2 = get_value_from_store(ts_id)

        df_attrs = deepcopy(df_attrs_1)
        df_attrs.update(df_attrs_2)

        assert len(df_from_store_2.attrs) != 0
        assert "test" in df_from_store_2.attrs
        for key, value in df_attrs.items():
            assert df_from_store_2.attrs[key] == value


@pytest.mark.asyncio
async def test_input_wiring_free_text_filters(
    async_test_client: AsyncClient,
) -> None:
    async with async_test_client as client:
        mk_response = await client.get(
            "/thingNodes/root.plantA/metadata/Temperature Unit",
            params={
                "id": "root.plantA.alerts",
                "latex_mode": "Y",
            },
        )
        assert mk_response.status_code == 200
        assert mk_response.json()["value"] == "$^\\circ$C"

        mk_response_empty_latex_mode = await client.get(
            "/thingNodes/root.plantA/metadata/Temperature Unit",
            params={
                "id": "root.plantA.alerts",
                "latex_mode": "",
            },
        )
        assert mk_response_empty_latex_mode.status_code == 200
        assert mk_response_empty_latex_mode.json()["value"] == "C"

        await client.post(
            "/dataframe",
            json=[
                {"a": 14.5, "b": 12.3},
                {"a": 13.5, "b": 11.9},
            ],
            params={"id": "root.plantA.alerts"},
        )
        df_response = await client.get(
            "/dataframe",
            params={
                "id": "root.plantA.alerts",
                "column_names": """[\"b\"]""",
            },
        )
        assert df_response.status_code == 200
        df: pd.DataFrame = pd.read_json(io.StringIO(df_response.text), lines=True)
        assert df.columns == ["b"]

        df_response_no_json_column_names = await client.get(
            "/dataframe",
            params={
                "id": "root.plantA.alerts",
                "column_names": "['b']",
            },
        )
        assert df_response_no_json_column_names.status_code == 422
        assert "cannot be parsed" in df_response_no_json_column_names.text

        df_response_no_list_column_names = await client.get(
            "/dataframe",
            params={
                "id": "root.plantA.alerts",
                "column_names": '{"b":"c"}',
            },
        )
        assert df_response_no_list_column_names.status_code == 422
        assert "not a list" in df_response_no_list_column_names.text

        df_response_wrong_key = await client.get(
            "/dataframe",
            params={
                "id": "root.plantA.alerts",
                "column_names": """[\"b\",\"c\"]""",
            },
        )
        assert df_response_wrong_key.status_code == 422
        assert "does not contain" in df_response_wrong_key.text

        mtsf_response = await client.get(
            "/multitsframe",
            params={
                "id": "root.plantA.temperatures",
                "from": "2020-01-01T00:00:00.000000000Z",
                "to": "2020-01-01T00:00:00.000000000Z",
                "upper_threshold": "107.9",
                "lower_threshold": "93.4",
            },
        )
        assert mtsf_response.status_code == 200
        mtsf: pd.DataFrame = pd.read_json(io.StringIO(mtsf_response.text), lines=True)
        if len(mtsf.index > 0):
            assert len(mtsf[mtsf["value"] > 107.9].index) == 0
            assert len(mtsf[mtsf["value"] < 93.4].index) == 0

        mtsf_response_no_float = await client.get(
            "/multitsframe",
            params={
                "id": "root.plantA.temperatures",
                "from": "2020-01-01T00:00:00.000000000Z",
                "to": "2020-01-01T00:00:00.000000000Z",
                "upper_threshold": "some string",
                "lower_threshold": "93.4",
            },
        )
        assert mtsf_response_no_float.status_code == 422
        assert "Cannot" in mtsf_response_no_float.text
        assert "to float" in mtsf_response_no_float.text

        ts_response = await client.get(
            "/timeseries",
            params={
                "id": "root.plantA.picklingUnit.influx.temp",
                "from": "2020-01-01T00:00:00.000000000Z",
                "to": "2020-01-02T00:00:00.000000000Z",
                "frequency": "2h",
            },
        )
        assert ts_response.status_code == 200
        ts_df: pd.DataFrame = pd.read_json(io.StringIO(ts_response.text), lines=True)
        assert len(ts_df.index) == 13

        ts_response_no_frequency_string = await client.get(
            "/timeseries",
            params={
                "id": "root.plantA.picklingUnit.influx.temp",
                "from": "2020-01-01T00:00:00.000000000Z",
                "to": "2020-01-02T00:00:00.000000000Z",
                "frequency": "string",
            },
        )
        assert ts_response_no_frequency_string.status_code == 422
        assert "'frequency' is invalid" in ts_response_no_frequency_string.text


@pytest.mark.asyncio
async def test_output_wiring_free_text_filters(
    async_test_client: AsyncClient,
) -> None:
    async with async_test_client as client:
        df_post_response = await client.post(
            "/dataframe",
            json=[
                {"a": 14.5, "b": 12.3},
                {"a": 13.5, "b": 11.9},
            ],
            params={
                "id": "root.plantA.alerts",
                "column_names": """[\"b\"]""",
            },
        )
        assert df_post_response.status_code == 200
        df_get_response = await client.get(
            "/dataframe",
            params={
                "id": "root.plantA.alerts",
            },
        )
        df: pd.DataFrame = pd.read_json(io.StringIO(df_get_response.text), lines=True)
        assert df.columns == ["b"]

        df_post_response_no_json_column_names = await client.post(
            "/dataframe",
            json=[
                {"a": 14.5, "b": 12.3},
                {"a": 13.5, "b": 11.9},
            ],
            params={
                "id": "root.plantA.alerts",
                "column_names": "['b']",
            },
        )
        assert df_post_response_no_json_column_names.status_code == 422
        assert "cannot be parsed" in df_post_response_no_json_column_names.text

        df_post_response_no_list_column_names = await client.post(
            "/dataframe",
            json=[
                {"a": 14.5, "b": 12.3},
                {"a": 13.5, "b": 11.9},
            ],
            params={
                "id": "root.plantA.alerts",
                "column_names": '{"b":"c"}',
            },
        )
        assert df_post_response_no_list_column_names.status_code == 422
        assert "not a list" in df_post_response_no_list_column_names.text

        df_post_response_wrong_key = await client.post(
            "/dataframe",
            json=[
                {"a": 14.5, "b": 12.3},
                {"a": 13.5, "b": 11.9},
            ],
            params={
                "id": "root.plantA.alerts",
                "column_names": """[\"b\",\"c\"]""",
            },
        )
        assert df_post_response_wrong_key.status_code == 422
        assert "does not contain" in df_post_response_wrong_key.text

        mtsf_post_response = await client.post(
            "/multitsframe",
            json=[
                {
                    "metric": "a",
                    "timestamp": "2020-01-01T00:00:00.000Z",
                    "value": 12.3,
                },
                {
                    "metric": "b",
                    "timestamp": "2020-01-02T00:00:00.000Z",
                    "value": 11.9,
                },
            ],
            params={
                "id": "root.plantA.anomalies",
                "metric_names": """[\"b\"]""",
            },
        )
        assert mtsf_post_response.status_code == 200
        mtsf_get_response = await client.get(
            "/multitsframe",
            params={
                "id": "root.plantA.anomalies",
                "from": "2020-01-01T00:00:00.000000000Z",
                "to": "2020-02-01T00:00:00.000000000Z",
            },
        )
        assert mtsf_post_response.status_code == 200
        assert "metric" in mtsf_get_response.text
        mtsf: pd.DataFrame = pd.read_json(io.StringIO(mtsf_get_response.text), lines=True)
        assert "metric" in mtsf
        assert mtsf["metric"].unique() == ["b"]

        ts_post_response = await client.post(
            "/timeseries",
            json=[
                {"timestamp": "2020-01-01T00:00:00.000000000Z", "value": 12.3},
                {"timestamp": "2020-01-01T01:00:00.000000000Z", "value": 11.9},
                {"timestamp": "2020-01-01T02:00:00.000000000Z", "value": 11.3},
                {"timestamp": "2020-01-01T03:00:00.000000000Z", "value": 10.9},
            ],
            params={
                "timeseriesId": "root.plantA.picklingUnit.influx.anomaly_score",
                "frequency": "2h",
            },
        )
        assert ts_post_response.status_code == 200
        ts_get_response = await client.get(
            "/timeseries",
            params={
                "id": "root.plantA.picklingUnit.influx.anomaly_score",
                "from": "2020-01-01T00:00:00.000000000Z",
                "to": "2020-01-02T00:00:00.000000000Z",
            },
        )
        assert ts_get_response.status_code == 200
        ts_df: pd.DataFrame = pd.read_json(io.StringIO(ts_get_response.text), lines=True)
        assert len(ts_df.index) == 2

        ts_response_no_frequency_string = await client.post(
            "/timeseries",
            json=[
                {"timestamp": "2020-01-01T00:00:00.000000000Z", "value": 12.3},
                {"timestamp": "2020-01-01T01:00:00.000000000Z", "value": 11.9},
                {"timestamp": "2020-01-01T02:00:00.000000000Z", "value": 11.3},
                {"timestamp": "2020-01-01T03:00:00.000000000Z", "value": 10.9},
            ],
            params={
                "timeseriesId": "root.plantA.picklingUnit.influx.anomaly_score",
                "frequency": "string",
            },
        )
        assert ts_response_no_frequency_string.status_code == 422
        assert "'frequency' is invalid" in ts_response_no_frequency_string.text
