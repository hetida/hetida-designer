from logging import getLogger
from typing import Any, Dict, List

from hetdesrun.adapters.blob_storage.exceptions import ConfigError
from hetdesrun.adapters.blob_storage.load_blob import load_blob_from_storage
from hetdesrun.adapters.blob_storage.models import BlobStorageStructureSource, ObjectKey
from hetdesrun.adapters.blob_storage.service import (
    get_buckets,
    get_object_key_strings_in_bucket,
)
from hetdesrun.adapters.blob_storage.utils import get_setup_from_config
from hetdesrun.adapters.blob_storage.write_blob import write_blob_to_storage
from hetdesrun.models.data_selection import FilteredSink, FilteredSource

logger = getLogger(__name__)

try:
    with open("VERSION", "r", encoding="utf8") as version_file:
        VERSION = version_file.read().strip()
except FileNotFoundError:
    VERSION = "dev snapshot"


tns, bucket_names_from_setup, snks = get_setup_from_config()
bucket_names_from_storage = get_buckets()
if len(bucket_names_from_setup) != len(bucket_names_from_storage):
    msg = (
        f"Number of bucket names generated from config file:\n{str(bucket_names_from_setup)}\n"
        f"does not match number of actual buckets:\n{bucket_names_from_storage}"
    )
    logger.error(msg)
    raise ConfigError(msg)
srcs: List[BlobStorageStructureSource] = []
for bucket_name in bucket_names_from_setup:
    if bucket_name not in bucket_names_from_storage:
        msg = f"Bucket {bucket_name} generated from config file but not existent in storage!"
        logger.error(msg)
        raise ConfigError(msg)
    object_key_strings = get_object_key_strings_in_bucket(bucket_name)
    for oks in object_key_strings:
        object_key = ObjectKey.from_string(oks)
        srcs.append(
            BlobStorageStructureSource.from_bucket_name_and_object_key(
                bucket_name=bucket_name, object_key=ObjectKey.from_string(oks)
            )
        )


async def load_data(
    wf_input_name_to_filtered_source_mapping_dict: Dict[str, FilteredSource],
    adapter_key: str,  # pylint: disable=unused-argument
) -> Dict[str, Any]:
    return {
        wf_input_name: load_blob_from_storage(filtered_source.ref_id)
        for wf_input_name, filtered_source in wf_input_name_to_filtered_source_mapping_dict.items()
        if filtered_source.ref_id is not None
    }


async def send_data(
    wf_output_name_to_filtered_sink_mapping_dict: Dict[str, FilteredSink],
    wf_output_name_to_value_mapping_dict: Dict[str, Any],
    adapter_key: str,  # pylint: disable=unused-argument
) -> Dict[str, Any]:
    for (
        wf_output_name,
        filtered_sink,
    ) in wf_output_name_to_filtered_sink_mapping_dict.items():
        if filtered_sink.ref_id is not None:
            blob = wf_output_name_to_value_mapping_dict[wf_output_name]
            write_blob_to_storage(blob, filtered_sink.ref_id)
    return {}
