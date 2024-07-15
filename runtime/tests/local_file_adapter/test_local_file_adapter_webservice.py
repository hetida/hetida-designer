from unittest import mock

import pandas as pd
import pytest

from hetdesrun.adapters.local_file import load_data, send_data
from hetdesrun.adapters.local_file.config import local_file_adapter_config
from hetdesrun.models.data_selection import FilteredSink, FilteredSource


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
        await open_async_test_client.get(f"/adapters/localfile/structure?parentId={parent_id}")
    ).json()
    src_append_list += response_obj["sources"]
    snk_append_list += response_obj["sinks"]

    for src in response_obj["sources"]:
        metadata = (
            await open_async_test_client.get(f'/adapters/localfile/sources/{src["id"]}/metadata/')
        ).json()
        for metadatum in metadata:
            src_attached_metadata_dict[(src["id"], metadatum["key"])] = metadatum

    for snk in response_obj["sinks"]:
        metadata = (
            await open_async_test_client.get(f'/adapters/localfile/sinks/{snk["id"]}/metadata/')
        ).json()
        for metadatum in metadata:
            snk_attached_metadata_dict[(snk["id"], metadatum["key"])] = metadatum

    metadata_tn = (
        await open_async_test_client.get(f"/adapters/localfile/thingNodes/{parent_id}/metadata/")
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


@pytest.mark.asyncio
@pytest.mark.filterwarnings(
    "ignore:an integer is required*"
)  # pandas to_json currently throws a deprecation warning
async def test_resources_offered_from_structure_hierarchy(  # noqa: PLR0915
    async_test_client,
):
    """Walks through the hierarchy provided by structure endpoint and gets/posts offered resources"""  # noqa: E501
    async with async_test_client as client:
        response_obj = (await client.get("/adapters/localfile/structure")).json()

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

        assert len(all_tns) == 5
        assert len(all_srcs) == 8
        assert (
            len(all_snks)
            == 3
            + (
                int(local_file_adapter_config.generic_any_sink)
                + int(local_file_adapter_config.generic_dataframe_sink)
            )
            * 6
        )
        filter_names = {
            snk["filters"]["file_name"]["name"] for snk in all_snks if "file_name" in snk["filters"]
        }
        assert filter_names == {
            'File Name (must end with ".pkl", ".h5")',
            'File Name (must end with ".csv", ".xlsx", ".parquet", "...")',
        }
        assert len(src_attached_metadata_dict) == 0
        assert len(snk_attached_metadata_dict) == 0
        assert len(tn_attached_metadata_dict) == 0
        for src in all_srcs:
            response_obj = (await client.get(f'/adapters/localfile/sources/{src["id"]}')).json()
            for key in src:
                assert response_obj[key] == src[key]

        for snk in all_snks:
            response_obj = (await client.get(f'/adapters/localfile/sinks/{snk["id"]}')).json()
            for key in snk:
                print(response_obj)
                assert response_obj[key] == snk[key]

        for tn in all_tns:
            response_obj = (await client.get(f'/adapters/localfile/thingNodes/{tn["id"]}')).json()
            for key in tn:
                print(response_obj)
                assert response_obj[key] == tn[key]

        # we actually get all metadata that is available as attached to something:
        for (src_id, key), md in src_attached_metadata_dict.items():
            response_obj = (
                await client.get(f"/adapters/localfile/sources/{src_id}/metadata/{key}")
            ).json()
            print(response_obj, "versus", md)
            assert response_obj["key"] == key
            assert response_obj["value"] == md["value"]
            assert response_obj["dataType"] == md["dataType"]

            if md.get("isSink", False):
                assert response_obj["isSink"]
                resp = await client.post(
                    f"/adapters/localfile/sources/{src_id}/metadata/{key}", json=md
                )
                assert resp.status_code == 200

        for (snk_id, key), md in snk_attached_metadata_dict.items():
            response_obj = (
                await client.get(f"/adapters/localfile/sinks/{snk_id}/metadata/{key}")
            ).json()
            print(response_obj, "versus", md)
            assert response_obj["key"] == key
            assert response_obj["value"] == md["value"]
            assert response_obj["dataType"] == md["dataType"]

            if md.get("isSink", False):
                assert response_obj["isSink"]
                resp = await client.post(
                    f"/adapters/localfile/sinks/{snk_id}/metadata/{key}", json=md
                )
                assert resp.status_code == 200

        for (tn_id, key), md in tn_attached_metadata_dict.items():
            response_obj = (
                await client.get(f"/adapters/localfile/thingNodes/{tn_id}/metadata/{key}")
            ).json()
            print(response_obj, "versus", md)
            assert response_obj["key"] == key
            assert response_obj["value"] == md["value"]
            assert response_obj["dataType"] == md["dataType"]

            if md.get("isSink", False):
                assert response_obj["isSink"]
                resp = await client.post(
                    f"/adapters/localfile/thingNodes/{snk_id}/metadata/{key}", json=md
                )
                assert resp.status_code == 200

        # all metadata that is a source in the tree is also found
        for src in all_srcs:
            if src["type"].startswith("metadata"):
                continue  # we do not offer these in metadata endpoints

            if src["type"].startswith("dataframe"):
                loaded_df = (
                    await load_data(
                        {
                            "wf_input": FilteredSource(
                                ref_id=src["id"],
                                ref_id_type="SOURCE",
                                ref_key=None,
                                type="dataframe",
                            ),
                        },
                        adapter_key="local-file-adapter",
                    )
                )["wf_input"]

                assert isinstance(loaded_df, pd.DataFrame)

            if src["type"].startswith("timeseries"):
                raise AssertionError("No timeseries type expected in local file adapter sources")

        # metadata that is a sink in the tree is also always obtainable
        for snk in all_snks:
            if snk["type"].startswith("metadata"):
                write_handler_func_mock = mock.Mock()
                with (
                    mock.patch(
                        "hetdesrun.adapters.local_file.write_file.LocalFile.file_support_handler",
                        return_value=mock.Mock(write_handler_func=write_handler_func_mock),
                    ) as file_handler_mock,
                    mock.patch(
                        "hetdesrun.adapters.local_file.write_file._get_job_id_context",
                        return_value={
                            "currently_executed_job_id": "1681ea7e-c57f-469a-ac12-592e3e8665cf"
                        },
                    ),
                ):
                    await send_data(
                        {
                            "wf_output": FilteredSink(
                                ref_id=snk["id"],
                                ref_id_type="SINK",
                                ref_key=None,
                                type="metadata(any)",
                            ),
                        },
                        {"wf_output": {"a": [1, 2, 3], "b": [12.2, 13.3, 14.4]}},
                        adapter_key="local-file-adapter",
                    )
                file_handler_mock.assert_called_once()
                write_handler_func_mock.assert_called_once()
                _, _, kwargs = write_handler_func_mock.mock_calls[0]
                assert kwargs == {}
            if snk["type"].startswith("dataframe"):
                with mock.patch(  # noqa: SIM117
                    "hetdesrun.adapters.local_file.write_file.pd.DataFrame.to_csv"
                ) as to_csv_mock:
                    with mock.patch(
                        "hetdesrun.adapters.local_file.write_file.pd.DataFrame.to_excel"
                    ) as to_excel_mock:
                        with mock.patch(
                            "hetdesrun.adapters.local_file.write_file._get_job_id_context",
                            return_value={
                                "currently_executed_job_id": "1681ea7e-c57f-469a-ac12-592e3e8665cf"
                            },
                        ):
                            await send_data(
                                {
                                    "wf_output": FilteredSink(
                                        ref_id=snk["id"],
                                        ref_id_type="SINK",
                                        ref_key=None,
                                        type="dataframe",
                                    ),
                                },
                                {
                                    "wf_output": pd.DataFrame(
                                        {"a": [1, 2, 3], "b": [12.2, 13.3, 14.4]}
                                    )
                                },
                                adapter_key="local-file-adapter",
                            )
                        if snk["id"].endswith(".xlsx"):
                            to_excel_mock.assert_called_once()
                        elif snk["id"].endswith(".csv"):
                            to_csv_mock.assert_called_once()
                file_handler_mock.assert_called_once()
                write_handler_func_mock.assert_called_once()
                _, _, kwargs = write_handler_func_mock.mock_calls[0]
                assert kwargs == {}

            if snk["type"].startswith("timeseries"):
                raise AssertionError("No timeseries type expected in local file adapter sinks")
        to_csv_mock.assert_called_once()
        func_name, args, kwargs = to_csv_mock.mock_calls[0]
        if snk["id"].endswith(".csv"):
            assert kwargs["sep"] == ";"  # option from the settings file of the only test sink
