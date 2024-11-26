from typing import Any
from unittest import mock

import httpx
import pytest

from hetdesrun.adapters.exceptions import (
    AdapterConnectionError,
    AdapterHandlingException,
)
from hetdesrun.adapters.generic_rest import load_data
from hetdesrun.adapters.generic_rest.load_metadata import load_multiple_metadata
from hetdesrun.models.data_selection import FilteredSource
from hetdesrun.webservice.auth_outgoing import ServiceAuthenticationError


async def detailed_mocked_async_client_get(self, url, *args, **kwargs):
    call_infos_from_url = url.rsplit("/", 4)
    received_key_param = call_infos_from_url[-1]
    assert call_infos_from_url[-2] == "metadata"
    received_ref_id = call_infos_from_url[-3]
    received_ref_type_endpoint = call_infos_from_url[-4]

    response_mock = mock.Mock()
    response_mock.status_code = 200

    if received_key_param == "description" and received_ref_id == "id_1":
        assert received_ref_type_endpoint == "thingNodes"
        response_mock.json = mock.Mock(
            return_value={
                "key": "description",
                "value": "some description",
                "dataType": "string",
            }
        )
        return response_mock

    if received_key_param == "max_val" and received_ref_id == "id_2":
        assert received_ref_type_endpoint == "sinks"
        response_mock.json = mock.Mock(
            return_value={
                "key": "max_val",
                "value": "25.9",
                "dataType": "float",
            }
        )
        return response_mock

    if received_key_param == "max_val_2" and received_ref_id == "id_3":
        assert received_ref_type_endpoint == "sinks"
        response_mock.json = mock.Mock(
            return_value={
                "key": "max_val_2",
                "value": "25.9",
                "dataType": "numeric",
            }
        )
        return response_mock

    raise ValueError("Could not produce mock")


@pytest.mark.asyncio
async def test_load_metadata_request():
    with mock.patch(
        "hetdesrun.adapters.generic_rest.load_metadata.get_generic_rest_adapter_base_url",
        return_value="https://hetida.de",
    ):
        resp_mock = mock.Mock()
        resp_mock.status_code = 200
        resp_mock.json = mock.Mock(
            return_value={"key": "serial", "value": 24567, "dataType": "int"}
        )

        data_to_load = {
            "wf_input_1": FilteredSource(
                ref_id="id_1",
                ref_id_type="SOURCE",
                ref_key="serial",
                type="metadata(int)",
                filters={"filter_key": "filter_value"},
            ),
        }

        with mock.patch(
            "hetdesrun.adapters.generic_rest.load_metadata.httpx.AsyncClient.get",
            return_value=resp_mock,
        ) as mocked_async_client_get:
            loaded_metadata = await load_multiple_metadata(
                data_to_load,
                adapter_key="test_load_metadata_adapter_key",
            )

            assert loaded_metadata["wf_input_1"] == 24567
            _, args, kwargs = mocked_async_client_get.mock_calls[0]

            assert args[0] == "https://hetida.de/sources/id_1/metadata/serial"
            assert kwargs["params"] == {"filter_key": "filter_value"}

            resp_mock.status_code = 400
            resp_mock.text = "my adapter error"
            with pytest.raises(AdapterConnectionError, match="my adapter error"):
                loaded_metadata = await load_multiple_metadata(
                    data_to_load,
                    adapter_key="test_load_metadata_adapter_key",
                )

            resp_mock.status_code = 200
            resp_mock.json = mock.Mock(
                return_value={"keyyyy": "serial", "value": 24567, "dataType": "int"}
            )
            with pytest.raises(AdapterHandlingException):
                loaded_metadata = await load_multiple_metadata(
                    data_to_load,
                    adapter_key="test_load_metadata_adapter_key",
                )
            resp_mock.json = mock.Mock(
                return_value={"key": "desc", "value": 24567, "dataType": "int"},
            )
            with pytest.raises(AdapterHandlingException):
                loaded_metadata = await load_multiple_metadata(
                    data_to_load,
                    adapter_key="test_load_metadata_adapter_key",
                )
            resp_mock.json = mock.Mock(
                return_value={"key": "serial", "value": 24567, "dataType": "string"}
            )
            with pytest.raises(AdapterHandlingException):
                loaded_metadata = await load_multiple_metadata(
                    data_to_load,
                    adapter_key="test_load_metadata_adapter_key",
                )
            resp_mock.json = mock.Mock(
                return_value={
                    "key": "serial",
                    "value": "some string",
                    "dataType": "int",
                }
            )
            with pytest.raises(AdapterHandlingException):
                loaded_metadata = await load_multiple_metadata(
                    data_to_load,
                    adapter_key="test_load_metadata_adapter_key",
                )
            resp_mock.json = mock.Mock(return_value=[])
            with pytest.raises(AdapterHandlingException):
                loaded_metadata = await load_multiple_metadata(
                    data_to_load,
                    adapter_key="test_load_metadata_adapter_key",
                )


@pytest.mark.asyncio
async def test_load_multiple_metadata_request():
    with (
        mock.patch(
            "hetdesrun.adapters.generic_rest.load_metadata.get_generic_rest_adapter_base_url",
            return_value="https://hetida.de",
        ),
        mock.patch(
            "hetdesrun.adapters.generic_rest.load_metadata.httpx.AsyncClient.get",
            new=detailed_mocked_async_client_get,
        ),
    ):
        loaded_metadata = await load_multiple_metadata(
            {
                "wf_input_1": FilteredSource(
                    ref_id="id_1",
                    ref_id_type="THINGNODE",
                    ref_key="description",
                    type="metadata(string)",
                    filters={},
                ),
                "wf_input_2": FilteredSource(
                    ref_id="id_2",
                    ref_id_type="SINK",
                    ref_key="max_val",
                    type="metadata(float)",
                    filters={},
                ),
                "wf_input_3": FilteredSource(
                    ref_id="id_3",
                    ref_id_type="SINK",
                    ref_key="max_val_2",
                    type="metadata(numeric)",
                    filters={},
                ),
            },
            adapter_key="test_load_metadata_adapter_key",
        )

        assert loaded_metadata["wf_input_1"] == "some description"
        assert loaded_metadata["wf_input_2"] == 25.9
        assert loaded_metadata["wf_input_3"] == 25.9


@pytest.mark.asyncio
async def test_load_metadata_any_from_string_response():
    with mock.patch(
        "hetdesrun.adapters.generic_rest.load_metadata.get_generic_rest_adapter_base_url",
        return_value="https://hetida.de",
    ):
        resp_mock = mock.Mock()
        resp_mock.status_code = 200
        resp_mock.json = mock.Mock(
            return_value={"key": "serial", "value": '{"a": 42.3}', "dataType": "any"}
        )
        data_to_load = {
            "wf_input_1": FilteredSource(
                ref_id="id_1",
                ref_id_type="SOURCE",
                ref_key="serial",
                type="metadata(any)",
                filters={},
            ),
        }

        # works if any object is provided as json string
        with mock.patch(
            "hetdesrun.adapters.generic_rest.load_metadata.httpx.AsyncClient.get",
            return_value=resp_mock,
        ) as _mocked_async_client_get:
            loaded_metadata = await load_multiple_metadata(
                data_to_load,
                adapter_key="test_load_metadata_adapter_key",
            )

            assert loaded_metadata["wf_input_1"] == {"a": 42.3}

        # works if any object is provided as json object directly
        resp_mock.json = mock.Mock(
            return_value={"key": "serial", "value": {"a": 42.3}, "dataType": "any"}
        )
        with mock.patch(
            "hetdesrun.adapters.generic_rest.load_metadata.httpx.AsyncClient.get",
            return_value=resp_mock,
        ) as _mocked_async_client_get:
            loaded_metadata = await load_multiple_metadata(
                data_to_load,
                adapter_key="test_load_metadata_adapter_key",
            )

            assert loaded_metadata["wf_input_1"] == {"a": 42.3}

        # works if any object is provided as json object directly
        resp_mock.json = mock.Mock(  # string but not a valid json string!
            return_value={"key": "serial", "value": '{"a" "b"}', "dataType": "any"}
        )
        with mock.patch(
            "hetdesrun.adapters.generic_rest.load_metadata.httpx.AsyncClient.get",
            return_value=resp_mock,
        ) as _mocked_async_client_get:
            loaded_metadata = await load_multiple_metadata(
                data_to_load,
                adapter_key="test_load_metadata_adapter_key",
            )
            assert isinstance(loaded_metadata["wf_input_1"], str)
            assert loaded_metadata["wf_input_1"] == '{"a" "b"}'


async def mock_load_multiple_metadata(
    data_to_load: dict[str, FilteredSource], adapter_key: str
) -> dict[str, Any]:
    return {"wf_inp_1": 42, "wf_inp_2": "some description"}


@pytest.mark.asyncio
async def test_end_to_end_load_only_metadata():
    with mock.patch(
        "hetdesrun.adapters.generic_rest.load_multiple_metadata",
        new=mock_load_multiple_metadata,
    ):
        loaded_data = await load_data(
            {
                "wf_inp_1": FilteredSource(
                    ref_id="id_1",
                    ref_id_type="SOURCE",
                    type="metadata(int)",
                    ref_key="number",
                ),
                "wf_inp_2": FilteredSource(
                    ref_id="id_2",
                    ref_id_type="THINGNODE",
                    type="metadata(string)",
                    ref_key="description",
                ),
            },
            adapter_key="end_to_end_only_dataframe_data",
        )

        assert loaded_data["wf_inp_1"] == 42
        assert loaded_data["wf_inp_2"] == "some description"


@pytest.mark.asyncio
async def test_end_to_end_load_metadata_with_exception():
    with (
        mock.patch(
            "hetdesrun.adapters.generic_rest.load_metadata.get_generic_rest_adapter_auth_headers",
            side_effect=ServiceAuthenticationError("my service error"),
        ),
        pytest.raises(AdapterHandlingException, match="my service error"),
    ):
        await load_data(
            {
                "wf_inp_1": FilteredSource(
                    ref_id="id_1",
                    ref_id_type="SOURCE",
                    type="metadata(int)",
                    ref_key="number",
                ),
            },
            adapter_key="end_to_end_only_dataframe_data",
        )

    with (
        mock.patch(
            "hetdesrun.adapters.generic_rest.load_metadata.get_generic_rest_adapter_base_url",
            return_value="https://hetida.de",
        ),
        mock.patch(
            "hetdesrun.adapters.generic_rest.load_metadata.httpx.AsyncClient.get",
            side_effect=httpx.HTTPError("my http error"),
        ),
        pytest.raises(AdapterConnectionError, match="my http error"),
    ):
        await load_data(
            {
                "wf_inp_1": FilteredSource(
                    ref_id="id_1",
                    ref_id_type="SOURCE",
                    type="metadata(int)",
                    ref_key="number",
                ),
            },
            adapter_key="end_to_end_only_dataframe_data",
        )
