"""Loading framelike data

Common utilities for loading data that is frame-like (tabular), i.e. dataframes as well as
timeseries (where the later can be understood as special dataframe/table)
"""

import base64
import datetime
import json
import logging
from posixpath import join as posix_urljoin
from typing import Any, Dict, List, Literal, Optional, Tuple, Type, Union

import pandas as pd
import requests

from hetdesrun.adapters.exceptions import (
    AdapterConnectionError,
    AdapterHandlingException,
)
from hetdesrun.adapters.generic_rest.auth import get_generic_rest_adapter_auth_headers
from hetdesrun.adapters.generic_rest.baseurl import get_generic_rest_adapter_base_url
from hetdesrun.adapters.generic_rest.external_types import ExternalType, df_empty
from hetdesrun.models.data_selection import FilteredSource
from hetdesrun.webservice.config import get_config

logger = logging.getLogger(__name__)


def create_empty_ts_df(
    data_type: ExternalType, attrs: Optional[Any] = None
) -> pd.DataFrame:
    """Create empty timeseries dataframe with explicit dtypes"""
    dtype_dict: Dict[str, Union[Type, str]] = {
        "timeseriesId": str,
        "timestamp": "datetime64[ns, UTC]",
    }

    value_datatype = data_type.value_datatype
    assert value_datatype is not None  # for mypy
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


def are_valid_sources(filtered_sources: List[FilteredSource]) -> Tuple[bool, str]:
    if len({fs.type for fs in filtered_sources}) > 1:
        return False, "Got more than one datatype in same grouped data"

    if len(filtered_sources) == 0:
        return False, "Requested fetching 0 sources"

    if (filtered_sources[0].type == ExternalType.DATAFRAME) and len(
        filtered_sources
    ) > 1:
        return False, "Cannot request more than one dataframe together"
    return True, ""


async def load_framelike_data(
    filtered_sources: List[FilteredSource],
    additional_params: List[
        Tuple[str, str]
    ],  # for timeseries: [("from", from_timestamp), ("to", to_timestamp)]
    adapter_key: str,
    endpoint: Literal["timeseries", "dataframe"],  # "timeseries" or "dataframe"
) -> pd.DataFrame:
    """Load framelike data from REST endpoint"""

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

    headers = get_generic_rest_adapter_auth_headers()

    with requests.Session() as session:
        try:
            start_time = datetime.datetime.now(datetime.timezone.utc)
            logger.info(
                "Start receiving generic rest adapter %s framelike data at %s",
                adapter_key,
                start_time.isoformat(),
            )
            resp = session.get(
                url,
                params=[
                    ("id", (str(filtered_source.ref_id)))
                    for filtered_source in filtered_sources
                ]
                + additional_params,
                stream=True,
                headers=headers,
                verify=get_config().hd_adapters_verify_certs,
            )
            if (
                resp.status_code == 404
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

            df = pd.read_json(resp.raw, lines=True)
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
                (
                    "Receiving generic rest adapter framelike data took"
                    " (including dataframe parsing)"
                    " %s"
                ),
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
        except requests.HTTPError as e:
            msg = (
                f"Requesting framelike data from generic rest adapter endpoint {url}"
                f" failed with Exception {str(e)}"
            )

            logger.info(msg)
            raise AdapterConnectionError(
                f"Requesting framelike from generic rest adapter endpoint {url} failed."
            ) from e
    logger.info("Complete generic rest adapter %s framelike request", adapter_key)
    if len(df) == 0:
        if endpoint == "timeseries":
            return create_empty_ts_df(ExternalType(common_data_type), attrs=df.attrs)
        # must be dataframe:
        return df_empty({}, attrs=df.attrs)

    if "timestamp" in df.columns and endpoint == "dataframe":
        try:
            parsed_timestamps = pd.to_datetime(df["timestamp"])
        except ValueError as e:
            logger.info(
                "Column 'timestamp' of dataframe from %s could not be parsed and therefore"
                " not be set to index. Proceeding with default index. Error was: %s",
                url,
                str(e),
            )
        else:
            df.index = parsed_timestamps
            df = df.sort_index()

    return df
