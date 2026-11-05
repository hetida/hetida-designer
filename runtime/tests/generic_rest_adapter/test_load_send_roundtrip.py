import io
from unittest import mock

import pytest

from hetdesrun.adapters.generic_rest import load_data, send_data
from hetdesrun.models.data_selection import FilteredSink, FilteredSource

# Timestamps as Java's ISO_INSTANT (the Jackson default for Instant) writes them, omitting the
# fraction of whole seconds, and one with sub-microsecond precision
TIMESTAMPS = ["2026-10-26T16:46:27Z", "2026-10-26T16:46:27.123Z", "2026-10-26T16:46:28.123456789Z"]
SENT_TIMESTAMPS = [
    "2026-10-26T16:46:27.000000000+00:00",
    "2026-10-26T16:46:27.123000000+00:00",
    "2026-10-26T16:46:28.123456789+00:00",
]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("data_type", "loaded_fields", "sent_fields"),
    [
        ("timeseries(float)", b'"timeseriesId": "id_1", ', {}),
        ("multitsframe", b'"metric": "a", ', {"metric": "a"}),
        ("singletsframe", b"", {}),
    ],
    ids=["timeseries", "multitsframe", "singletsframe"],
)
async def test_loaded_data_can_be_sent_to_generic_rest_adapter(
    data_type: str, loaded_fields: bytes, sent_fields: dict[str, str]
) -> None:
    # sending loaded data failed with "does not have UTC timezone" in 0.14.9
    resp_mock = mock.Mock(
        status_code=200,
        headers={},
        raw=io.BytesIO(
            b"".join(
                b'{"timestamp": "%s", %s"value": %d.5}\n' % (timestamp.encode(), loaded_fields, i)
                for i, timestamp in enumerate(TIMESTAMPS)
            )
        ),
    )
    post_mock = mock.AsyncMock(return_value=mock.Mock(status_code=200))
    with (
        mock.patch(
            "hetdesrun.adapters.generic_rest.load_framelike.get_generic_rest_adapter_base_url",
            return_value="https://hetida.de",
        ),
        mock.patch(
            "hetdesrun.adapters.generic_rest.send_framelike.get_generic_rest_adapter_base_url",
            return_value="https://hetida.de",
        ),
        mock.patch(
            "hetdesrun.adapters.generic_rest.load_framelike.niquests.Session.get",
            return_value=resp_mock,
        ),
        mock.patch(
            "hetdesrun.adapters.generic_rest.send_framelike.AsyncClient.post", new=post_mock
        ),
    ):
        loaded = await load_data(
            {
                "inp": FilteredSource(
                    ref_id="id_1",
                    type=data_type,
                    filters={
                        "timestampFrom": "2026-10-26T00:00:00Z",
                        "timestampTo": "2026-10-27T00:00:00Z",
                    },
                )
            },
            adapter_key="test_load_send_roundtrip",
        )
        await send_data(
            {"outp": FilteredSink(ref_id="id_2", type=data_type)},
            {"outp": loaded["inp"]},
            adapter_key="test_load_send_roundtrip",
        )

    post_mock.assert_awaited_once()
    assert post_mock.call_args.kwargs["json"] == [
        {"timestamp": timestamp, **sent_fields, "value": i + 0.5}
        for i, timestamp in enumerate(SENT_TIMESTAMPS)
    ]
