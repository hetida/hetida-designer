import logging
from typing import Any, Dict

from botocore.exceptions import ClientError

from hetdesrun.adapters.blob_storage.exceptions import SinkNotFound, SinkNotUnique
from hetdesrun.adapters.blob_storage.models import IdString
from hetdesrun.adapters.blob_storage.service import get_s3_client
from hetdesrun.adapters.blob_storage.structure import (
    get_sink_by_thing_node_id_and_metadata_key,
)
from hetdesrun.models.data_selection import FilteredSink

logger = logging.getLogger(__name__)


def write_blob_to_storage(data: Any, thing_node_id: str, metadata_key: str) -> None:
    try:
        sink = get_sink_by_thing_node_id_and_metadata_key(
            IdString(thing_node_id), metadata_key
        )
    except SinkNotFound as error:
        # TODO: define behavior for SinkNotFound in write_blob_to_storage
        raise error
    except SinkNotUnique as error:
        # TODO: define behavior for SinkNotFound in write_blob_to_storage
        raise error

    structure_bucket, object_key = sink.to_structure_bucket_and_object_key()
    try:
        get_s3_client().put_object(
            Bucket=structure_bucket.name, Key=object_key.string, Body=data
        )
    except ClientError as error:
        # TODO: define behavior for ClientError in load_blob_from_storage
        raise error
    logger.info(
        "Write data for sink '%s' to storage into bucket '%s' as blob with key '%s'",
        sink.id,
        structure_bucket.name,
        object_key.string,
    )


async def send_data(
    wf_output_name_to_filtered_sink_mapping_dict: Dict[str, FilteredSink],
    wf_output_name_to_value_mapping_dict: Dict[str, Any],
    adapter_key: str,  # pylint: disable=unused-argument
) -> Dict[str, Any]:
    for (
        wf_output_name,
        filtered_sink,
    ) in wf_output_name_to_filtered_sink_mapping_dict.items():
        if filtered_sink.ref_id is not None and filtered_sink.ref_key is not None:
            blob = wf_output_name_to_value_mapping_dict[wf_output_name]
            write_blob_to_storage(blob, filtered_sink.ref_id, filtered_sink.ref_key)
    return {}
