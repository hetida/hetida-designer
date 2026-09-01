"""Loading framelike data

Common utilities for loading data that is frame-like (tabular), i.e. dataframes as well as
timeseries (where the later can be understood as special dataframe/table)
"""

import base64
import datetime
import json
import logging
from posixpath import join as posix_urljoin
from typing import Any, BinaryIO, Literal
from uuid import UUID

import niquests
import pandas as pd
import pyarrow as pa
import pyarrow.json as pa_json

from hetdesrun.adapters.exceptions import (
    AdapterConnectionError,
    AdapterHandlingException,
)
from hetdesrun.adapters.generic_rest.auth import get_generic_rest_adapter_auth_headers
from hetdesrun.adapters.generic_rest.baseurl import get_generic_rest_adapter_base_url
from hetdesrun.adapters.generic_rest.client import get_generic_rest_adapter_sync_session
from hetdesrun.adapters.generic_rest.external_types import ExternalType, df_empty
from hetdesrun.models.data_selection import FilteredSource
from hetdesrun.runtime.logging import job_id_context_filter
from hetdesrun.webservice.auth_outgoing import ServiceAuthenticationError
from hetdesrun.webservice.config import get_config

logger = logging.getLogger(__name__)

# Block size (bytes) pyarrow's streaming JSON reader pulls from the socket at a time. It caps the
# transient read buffer (peak memory ~ this + the growing result) and must exceed the largest
# single JSON record (one row); 1 MiB is ample for the adapter's per-row records.
_PYARROW_JSON_READ_BLOCK_SIZE = 1024 * 1024


def create_empty_ts_df(data_type: ExternalType, attrs: Any | None = None) -> pd.DataFrame:
    """Create empty timeseries dataframe with explicit dtypes"""
    dtype_dict: dict[str, type | str] = {
        "timeseriesId": str,
        "timestamp": "datetime64[us, UTC]",
    }

    value_datatype = data_type.value_datatype
    assert value_datatype is not None  # for mypy   # noqa: S101
    dtype_dict["value"] = value_datatype.pandas_value_type

    if attrs is None:
        attrs = {}
    return df_empty(dtype_dict, attrs=attrs)


def decode_attributes(data_attributes: str) -> Any:
    base64_bytes = data_attributes.encode("utf-8")
    logger.debug("data_attributes=%s", data_attributes)
    df_attrs_bytes = base64.b64decode(base64_bytes)
    df_attrs_json_str = df_attrs_bytes.decode("utf-8")
    logger.debug("df_attrs_json_str=%s", df_attrs_json_str)
    df_attrs = json.loads(df_attrs_json_str)
    return df_attrs


def are_valid_sources(filtered_sources: list[FilteredSource]) -> tuple[bool, str]:
    if len({fs.type for fs in filtered_sources}) > 1:
        return False, "Got more than one datatype in same grouped data"

    if len(filtered_sources) == 0:
        return False, "Requested fetching 0 sources"

    if (filtered_sources[0].type == ExternalType.DATAFRAME) and len(filtered_sources) > 1:
        return False, "Cannot request more than one dataframe together"
    return True, ""


def parse_framelike_response_stream(
    stream: BinaryIO,
    endpoint: Literal["timeseries", "dataframe", "multitsframe", "singletsframe"],
    error_source: str = "",
) -> pd.DataFrame:
    """Core transformation from a framelike response body to a DataFrame.

    Streams ``stream`` - a readable, already-decompressed binary file-like of newline-delimited JSON
    records - through pyarrow's JSON reader and converts it to a numpy-backed pandas DataFrame, then
    normalizes the ``timestamp`` column the way each endpoint needs. pyarrow reads the stream in
    blocks and builds the columnar result incrementally, so memory grows with the resulting
    DataFrame instead of the whole raw payload being buffered first (as ``pd.read_json`` does).

    An empty body yields an empty (0-column) DataFrame. ``error_source`` (e.g. the request URL) is
    only used in error / log messages.

    Shared by :func:`load_framelike_data` and its performance tests so both exercise the same code.
    """
    try:
        table = pa_json.read_json(
            stream,
            read_options=pa_json.ReadOptions(block_size=_PYARROW_JSON_READ_BLOCK_SIZE),
        )
    except pa.ArrowInvalid as e:
        if "empty" in str(e).lower():
            return df_empty({})
        msg = (
            f"Could not parse framelike response data from {error_source} via the pyarrow json"
            f" reader. Exception was:\n{str(e)}."
        )
        logger.info(msg)
        raise AdapterHandlingException(msg) from e

    # to_pandas with self_destruct + split_blocks frees each Arrow column as its numpy column is
    # materialized (numeric columns are zero-copy), avoiding a full Arrow+numpy duplicate. Strings
    # stay as pandas' (arrow-backed) string dtype.
    df = table.to_pandas(self_destruct=True, split_blocks=True, use_threads=True)

    if "timestamp" in df.columns:
        if endpoint == "dataframe":
            try:
                parsed_timestamps = pd.to_datetime(df["timestamp"])
            except (ValueError, TypeError) as e:
                logger.info(
                    "Column 'timestamp' of dataframe from %s could not be parsed and therefore"
                    " not be set to index. Proceeding with default index. Error was: %s",
                    error_source,
                    str(e),
                )
            else:
                df.index = parsed_timestamps
                df = df.sort_index()
        else:
            # timeseries / multitsframe / singletsframe: reproduce the tz-aware datetime
            # "timestamp" column that
            # pd.read_json used to infer automatically (pyarrow leaves ISO timestamps as strings,
            # and downstream code relies on this column being datetime, e.g. as a series index).
            df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)

    return df


async def load_framelike_data(  # noqa: PLR0915,PLR0912
    filtered_sources: list[FilteredSource],
    # for timeseries, multitsframes and singletsframes additional_params carries the
    # "from" / "to" timestamp query params [("from", from_timestamp), ("to", to_timestamp)]
    additional_params: list[tuple[str, str]],
    adapter_key: str,
    endpoint: Literal["timeseries", "dataframe", "multitsframe", "singletsframe"],
) -> pd.DataFrame:
    """Load framelike data from REST endpoint"""

    job_id: str | UUID | None = job_id_context_filter.get_value("currently_executed_job_id")

    if job_id is not None:
        additional_params.append(("job_id", str(job_id)))

    url = posix_urljoin(await get_generic_rest_adapter_base_url(adapter_key), endpoint)

    valid, msg = are_valid_sources(filtered_sources)
    if not valid:
        logger.error(msg)
        raise AdapterHandlingException(msg)

    common_data_type = filtered_sources[0].type

    logger.info(
        (
            "Requesting framelike data from generic rest adapter %s from endpoint %s:"
            " ids %s with additional params %s with common datatype %s"
        ),
        adapter_key,
        url,
        str([filtered_source.ref_id for filtered_source in filtered_sources]),
        str(additional_params),
        str(common_data_type),
    )
    try:
        headers = await get_generic_rest_adapter_auth_headers(external=True)
    except ServiceAuthenticationError as e:
        msg = (
            "Failed to get auth headers for loading framelike data from adapter"
            f"with key {adapter_key}. Error was:\n{str(e)}"
        )
        logger.info(msg)
        raise AdapterHandlingException(msg) from e

    # One cached (blocking) niquests session per adapter, so the connection pool is reused across
    # requests. Blocking is acceptable here: we stream the body synchronously into pyarrow.
    session = get_generic_rest_adapter_sync_session(adapter_key)
    try:
        start_time = datetime.datetime.now(datetime.timezone.utc)
        logger.info(
            "Start receiving generic rest adapter %s framelike data at %s",
            adapter_key,
            start_time.isoformat(),
        )
        query_params: list[tuple[str, Any]] = [
            ("id", (str(filtered_source.ref_id))) for filtered_source in filtered_sources
        ] + additional_params
        resp = session.get(
            url,
            params=query_params,
            stream=True,
            headers=headers,
            verify=get_config().hd_adapters_verify_certs,
            timeout=get_config().external_request_timeout,
        )
        if (
            resp.status_code == 404
            and resp.text is not None
            and "errorCode" in resp.text
            and resp.json()["errorCode"] == "RESULT_EMPTY"
        ):
            logger.info(
                (
                    "Received RESULT_EMPTY error_code from generic rest adapter %s"
                    " framelike endpoint %s, therefore returning empty DataFrame"
                ),
                adapter_key,
                url,
            )
            if endpoint == "timeseries":
                return create_empty_ts_df(ExternalType(common_data_type))
            # must be "dataframe":
            return df_empty({})

        if resp.status_code != 200:
            msg = (
                f"Requesting framelike data from generic rest adapter endpoint {url} failed."
                f" Status code: {resp.status_code}. Text: {resp.text}"
            )
            logger.info(msg)
            raise AdapterConnectionError(msg)
        logger.info("Start reading in and parsing framelike data")

        # Stream the response body straight into the parse core (parse_framelike_response_stream).
        raw = resp.raw
        assert raw is not None  # streamed 200 response always has a raw body  # noqa: S101
        raw.decode_content = True  # transparently decompress gzip/deflate while streaming
        df = parse_framelike_response_stream(raw, endpoint, error_source=url)
        end_time = datetime.datetime.now(datetime.timezone.utc)
        logger.info(
            (
                "Finished receiving generic rest framelike data (including dataframe parsing)"
                " at %s. DataFrame shape is %s with columns %s"
            ),
            end_time.isoformat(),
            str(df.shape),
            str(df.columns),
        )
        logger.info(
            ("Receiving generic rest adapter framelike data took (including dataframe parsing) %s"),
            str(end_time - start_time),
        )

        if "Data-Attributes" in resp.headers:
            logger.debug("Got Data-Attributes via GET response header")
            data_attributes = resp.headers["Data-Attributes"]
            df.attrs = decode_attributes(data_attributes)

        logger.debug(
            "Received dataframe of form %s:\n%s",
            str(df.shape) if len(df) > 0 else "EMPTY RESULT",
            str(df) if len(df) > 0 else "EMPTY RESULT",
        )
    except (niquests.HTTPError, niquests.ConnectionError, niquests.RequestException) as e:
        msg = (
            f"Requesting framelike data from generic rest adapter endpoint {url}"
            f" failed with Exception {str(e)}"
        )

        logger.info(msg)
        raise AdapterConnectionError(msg) from e
    logger.info("Complete generic rest adapter %s framelike request", adapter_key)
    if len(df) == 0:
        if endpoint == "timeseries":
            return create_empty_ts_df(ExternalType(common_data_type), attrs=df.attrs)
        # must be dataframe:
        return df_empty({}, attrs=df.attrs)

    return df
