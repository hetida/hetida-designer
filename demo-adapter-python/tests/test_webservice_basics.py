import json
from urllib.parse import quote

import pytest
from starlette.testclient import TestClient

from demo_adapter_python.external_types import ExternalType
from demo_adapter_python.in_memory_store import get_value_from_store
from demo_adapter_python.webservice import app, decode_attributes, encode_attributes

client = TestClient(app)


@pytest.mark.asyncio
async def test_swagger_ui_available(async_test_client):
    async with async_test_client as client:
        response = await client.get("/docs")
    assert response.status_code == 200
    assert "swagger-ui" in response.text.lower()


async def walk_thing_nodes(
    parent_id,
    tn_append_list,
    src_append_list,
    snk_append_list,
    src_attached_metadata_dict,
    snk_attached_metadata_dict,
    tn_attached_metadata_dict,
    open_async_test_client,
):
    """Recursively walk thingnodes"""
    response_obj = (
        await open_async_test_client.get(f"/structure?parentId={parent_id}")
    ).json()
    src_append_list += response_obj["sources"]
    snk_append_list += response_obj["sinks"]

    for src in response_obj["sources"]:
        metadata = (
            await open_async_test_client.get(f'/sources/{src["id"]}/metadata/')
        ).json()
        for metadatum in metadata:
            src_attached_metadata_dict[(src["id"], metadatum["key"])] = metadatum

    for snk in response_obj["sinks"]:
        metadata = (
            await open_async_test_client.get(f'/sinks/{snk["id"]}/metadata/')
        ).json()
        for metadatum in metadata:
            snk_attached_metadata_dict[(snk["id"], metadatum["key"])] = metadatum

    metadata_tn = (
        await open_async_test_client.get(f"/thingNodes/{parent_id}/metadata/")
    ).json()
    for metadatum in metadata_tn:
        tn_attached_metadata_dict[(parent_id, metadatum["key"])] = metadatum

    for tn in response_obj["thingNodes"]:
        tn_append_list.append(tn)
        await walk_thing_nodes(
            tn["id"],
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
async def test_resources_offered_from_structure_hierarchy(async_test_client):
    """Walks through the hierarchy provided by structure endpoint and gets/posts offered resources"""
    async with async_test_client as client:

        response_obj = (await client.get("/structure")).json()

        assert len(response_obj["sources"]) == 0
        assert len(response_obj["sinks"]) == 0

        roots = response_obj["thingNodes"]
        assert len(roots) == 1

        root = roots[0]

        all_tns = []
        all_srcs = []
        all_snks = []
        tn_attached_metadata_dict = {}
        src_attached_metadata_dict = {}
        snk_attached_metadata_dict = {}

        await walk_thing_nodes(
            root["id"],
            tn_append_list=all_tns,
            src_append_list=all_srcs,
            snk_append_list=all_snks,
            src_attached_metadata_dict=src_attached_metadata_dict,
            snk_attached_metadata_dict=snk_attached_metadata_dict,
            tn_attached_metadata_dict=tn_attached_metadata_dict,
            open_async_test_client=client,
        )

        assert len(all_tns) == 14
        assert len(all_srcs) == 33
        assert len(all_snks) == 12
        assert len(src_attached_metadata_dict) == 52
        assert len(snk_attached_metadata_dict) == 24
        assert len(tn_attached_metadata_dict) == 8

        for src in all_srcs:
            response_obj = (await client.get(f'/sources/{src["id"]}')).json()
            for key in src.keys():
                assert response_obj[key] == src[key]

        for snk in all_snks:
            response_obj = (await client.get(f'/sinks/{snk["id"]}')).json()
            for key in snk.keys():
                print(response_obj)
                assert response_obj[key] == snk[key]

        for tn in all_tns:
            response_obj = (await client.get(f'/thingNodes/{tn["id"]}')).json()
            for key in tn.keys():
                print(response_obj)
                assert response_obj[key] == tn[key]

        # we actually get all metadata that is available as attached to something:
        for ((src_id, key), md) in src_attached_metadata_dict.items():
            response_obj = (
                await client.get(f"/sources/{src_id}/metadata/{key}")
            ).json()
            print(response_obj, "versus", md)
            assert response_obj["key"] == key
            assert response_obj["value"] == md["value"]
            assert response_obj["dataType"] == md["dataType"]

            if md.get("isSink", False):
                assert response_obj["isSink"]
                resp = await client.post(f"/sources/{src_id}/metadata/{key}", json=md)
                assert resp.status_code == 200

        for ((snk_id, key), md) in snk_attached_metadata_dict.items():
            response_obj = (await client.get(f"/sinks/{snk_id}/metadata/{key}")).json()
            print(response_obj, "versus", md)
            assert response_obj["key"] == key
            assert response_obj["value"] == md["value"]
            assert response_obj["dataType"] == md["dataType"]

            if md.get("isSink", False):
                assert response_obj["isSink"]
                resp = await client.post(f"/sinks/{snk_id}/metadata/{key}", json=md)
                assert resp.status_code == 200

        for ((tn_id, key), md) in tn_attached_metadata_dict.items():
            response_obj = (
                await client.get(f"/thingNodes/{tn_id}/metadata/{key}")
            ).json()
            print(response_obj, "versus", md)
            assert response_obj["key"] == key
            assert response_obj["value"] == md["value"]
            assert response_obj["dataType"] == md["dataType"]

            if md.get("isSink", False):
                assert response_obj["isSink"]
                resp = await client.post(
                    f"/thingNodes/{snk_id}/metadata/{key}", json=md
                )
                assert resp.status_code == 200

        # all metadata that is a source in the tree is also found
        for src in all_srcs:
            if src["type"].startswith("metadata"):
                response_obj = (
                    await client.get(
                        f'/thingNodes/{src["thingNodeId"]}/metadata/{src["metadataKey"]}'
                    )
                ).json()
                print(response_obj, "versus", src)

                assert response_obj["key"] == src["metadataKey"]
                assert response_obj["dataType"] == (
                    ExternalType(src["type"]).value_datatype.value
                )
            if src["type"].startswith("dataframe"):
                response = await client.get(f'/dataframe?id={src["id"]}')
                lines = response.text.splitlines()
                for line in lines:
                    print(line)
                    if len(line) > 0:
                        json.loads(line)

            if src["type"].startswith("timeseries"):
                response = await client.get(
                    f'/timeseries?id={src["id"]}&from={quote("2020-01-01T00:00:00.000000000Z")}'
                    f'&to={quote("2020-01-02T00:00:00.0000000Z")}'
                )
                assert response.status_code == 200
                lines = response.text.splitlines()
                for line in lines:
                    print(line)
                    if len(line) > 0:
                        json.loads(line)

        # metadata that is a sink in the tree is also always obtainable
        for snk in all_snks:
            if snk["type"].startswith("metadata"):
                response_obj = (
                    await client.get(
                        f'/thingNodes/{snk["thingNodeId"]}/metadata/{snk["metadataKey"]}'
                    )
                ).json()
                print(response_obj, "versus", snk)

                assert response_obj["key"] == snk["metadataKey"]
                assert response_obj["dataType"] == (
                    ExternalType(snk["type"]).value_datatype.value
                )

                resp = await client.post(
                    f'/thingNodes/{snk["thingNodeId"]}/metadata/{snk["metadataKey"]}',
                    json=response_obj,
                )

                assert resp.status_code == 200

            if snk["type"].startswith("dataframe"):
                print("Posting something for dataframe sink:", snk)
                response = await client.post(
                    f'/dataframe?id={snk["id"]}',
                    json=[
                        {"a": 14.5, "b": 12.3},
                        {"a": 13.5, "b": 11.9},
                    ],
                )
                assert response.status_code == 200

            if snk["type"].startswith("timeseries"):
                print("Posting something for timeseries sink:", snk)
                response = await client.post(
                    f'/timeseries?timeseriesId={snk["id"]}',
                    json=[
                        {"timestamp": "2020-01-01T00:00:00.000000000Z", "value": 12.3},
                        {"timestamp": "2020-01-02T00:00:00.000000000Z", "value": 11.9},
                    ],
                )
                assert response.status_code == 200


@pytest.mark.asyncio
async def test_post_metadata_of_thing_node_get_metadata_of_thing_node(
    async_test_client,
):
    async with async_test_client as client:
        thingNodeId = "root.plantA"
        key = "Anomaly State"
        value = True
        post_metadatum_json = {"key": key, "value": value}

        post_response = await client.post(
            f"/thingNodes/{thingNodeId}/metadata/{quote(key)}", json=post_metadatum_json
        )

        assert post_response.status_code == 200

        get_response = await client.get(
            f"/thingNodes/{thingNodeId}/metadata/{quote(key)}"
        )

        assert get_response.status_code == 200
        assert get_response.json()["value"] == value


@pytest.mark.asyncio
async def test_post_metadata_to_sink_get_metadata_from_source(async_test_client):
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
async def test_sending_attrs_via_get_dataframe(async_test_client):
    async with async_test_client as client:
        response = await client.get(f"/dataframe?id=root.plantA.maintenance_events")

        assert response.status_code == 200
        assert "Data-Attributes" in response.headers
        assert isinstance(response.headers["Data-Attributes"], str)

        df_attrs = decode_attributes(response.headers["Data-Attributes"])

        assert "since_date" in df_attrs
        assert df_attrs["since_date"] == "2020-01-01T00:00:00.000Z"


@pytest.mark.asyncio
async def test_receiving_attrs_via_post_dataframe(async_test_client):
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
async def test_sending_attrs_via_get_timeseries(async_test_client):
    async with async_test_client as client:
        ts_id = "root.plantA.picklingUnit.influx.anomaly_score"

        response = await client.get(
            f"/timeseries?id={ts_id}"
            f'&from={quote("2020-01-01T00:00:00.000000000Z")}'
            f'&to={quote("2020-01-01T00:00:00.000000000Z")}'
        )

        assert response.status_code == 200
        assert "Data-Attributes" in response.headers
        assert isinstance(response.headers["Data-Attributes"], str)

        df_attrs = decode_attributes(response.headers["Data-Attributes"])

        assert ts_id in df_attrs
        assert "to_timestamp" in df_attrs[ts_id]
        assert df_attrs[ts_id]["to_timestamp"] != "2020-01-01T00:00:00.000000000Z"
        assert df_attrs[ts_id]["to_timestamp"] == "2020-01-01T00:00:00+00:00"


@pytest.mark.asyncio
async def test_receiving_attrs_via_post_timeseries(async_test_client):
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

        df_from_store = get_value_from_store("root.plantA.alerts")

        assert len(df_from_store.attrs) != 0
        assert "test" in df_from_store.attrs
        for key, value in df_attrs.items():
            assert df_from_store.attrs[key] == value
