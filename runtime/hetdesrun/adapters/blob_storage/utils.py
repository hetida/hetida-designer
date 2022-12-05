import json
from logging import getLogger
from typing import Any, Dict, List, Optional, Tuple

from pydantic import ValidationError

from hetdesrun.adapters.blob_storage.exceptions import (
    BucketNameInvalidError,
    CategoryInvalidError,
    ConfigError,
    ConfigIncompleteError,
    MissingConfigError,
    ThingNodeInvalidError,
)
from hetdesrun.adapters.blob_storage.models import (
    BlobStorageStructureSink,
    BlobStorageStructureSource,
    BucketName,
    Category,
    IdString,
    ObjectKey,
    StructureThingNode,
)
from hetdesrun.adapters.blob_storage.service import (
    get_buckets,
    get_object_key_strings_in_bucket,
)

logger = getLogger(__name__)


def load_config_file(path: str = "demodata/blob_storage_adapter_config.json") -> Any:
    try:
        with open(path, encoding="ascii") as f:
            config_json = json.load(f)
    except FileNotFoundError as error:
        msg = f"Could not find json file at path {path}:\n{str(error)}"
        logger.error(msg)
        raise MissingConfigError(msg) from error

    if "bucket_level" not in config_json or "structure" not in config_json:
        msg = (
            f"The config file {path} is incomplete.\n"
            'Both "bucket_level" and "structure" must be provided.'
        )
        logger.error(msg)
        raise ConfigIncompleteError(msg)

    return config_json


def walk_structure(
    parent_id: Optional[IdString],
    tn_append_list: List[StructureThingNode],
    bucket_append_list: List[BucketName],
    snk_append_list: List[BlobStorageStructureSink],
    structure: List[Category],
    bucket_level: int,
    level: int,
) -> None:
    """Recursively walk structure_json."""
    logger.info(
        "Walk through structure with parent_id %s, bucket_level %i, level %i",
        parent_id,
        bucket_level,
        level,
    )
    for category in structure:
        try:
            thing_node = category.to_thing_node(
                parent_id, separator="-" if level <= bucket_level else "/"
            )
        except ValidationError as error:
            msg = (
                f"Validation Error for transformation of category {str(category)} "
                "to StructureThingNode:\n{}"
            )
            logger.error(msg)
            raise ThingNodeInvalidError(msg) from error
        logger.info("Created thingnode %s", str(thing_node))
        tn_append_list.append(thing_node)

        if level == bucket_level:
            try:
                bucket_append_list.append(BucketName(thing_node.id))
            except ValidationError as error:
                msg = f"Validation Error for transformation of {thing_node.id} to BucketName."
                logger.error(msg)
                raise BucketNameInvalidError(msg) from error

        if category.substructure is not None and len(category.substructure) != 0:
            try:
                substructure = [
                    Category(**subcategory_json)
                    for subcategory_json in category.substructure
                ]
            except ValidationError as error:
                msg = (
                    "Validation Error for transformation of substructure from category "
                    f"{category.name} to a list of categories."
                )
                logger.error(msg)
                raise CategoryInvalidError(msg) from error

            walk_structure(
                parent_id=thing_node.id,
                tn_append_list=tn_append_list,
                bucket_append_list=bucket_append_list,
                snk_append_list=snk_append_list,
                structure=substructure,
                bucket_level=bucket_level,
                level=level + 1,
            )
        else:  # category.substructure is None or len(category.substructure) == 0
            if level < bucket_level:
                msg = (
                    f"Category {str(category)} has too few levels of subcategories ({level}) "
                    f"to generate buckets with bucket level {str(bucket_level)}"
                )
                logger.error(msg)
                raise ConfigIncompleteError(msg)
            # level >= bucket_level
            snk_append_list.append(
                BlobStorageStructureSink.from_thing_node(
                    thing_node, name="Next Trained Model"
                )
            )


def get_setup_from_config() -> Tuple[
    List[StructureThingNode], List[BucketName], List[BlobStorageStructureSink]
]:
    config_json = load_config_file()

    bucket_level: int = config_json["bucket_level"]
    structure_json: List[Dict[str, Any]] = config_json["structure"]

    try:
        structure = [Category(**category_json) for category_json in structure_json]
    except ValidationError as error:
        raise CategoryInvalidError from error

    thing_nodes: List[StructureThingNode] = []
    bucket_names: List[BucketName] = []
    sinks: List[BlobStorageStructureSink] = []

    walk_structure(
        parent_id=None,
        tn_append_list=thing_nodes,
        bucket_append_list=bucket_names,
        snk_append_list=sinks,
        structure=structure,
        bucket_level=bucket_level,
        level=1,
    )

    return thing_nodes, bucket_names, sinks


def setup_adapter() -> Tuple[
    List[StructureThingNode],
    List[BlobStorageStructureSource],
    List[BlobStorageStructureSink],
]:
    thing_node_list, bucket_names_from_setup, sink_list = get_setup_from_config()
    bucket_names_from_storage = get_buckets()
    if len(bucket_names_from_setup) != len(bucket_names_from_storage):
        msg = (
            f"Number of bucket names generated from config file:\n{str(bucket_names_from_setup)}\n"
            f"does not match number of actual buckets:\n{bucket_names_from_storage}"
        )
        logger.error(msg)
        raise ConfigError(msg)
    source_list: List[BlobStorageStructureSource] = []
    for bucket_name in bucket_names_from_setup:
        if bucket_name not in bucket_names_from_storage:
            msg = f"Bucket {bucket_name} generated from config file but not existent in storage!"
            logger.error(msg)
            raise ConfigError(msg)
        object_key_strings = get_object_key_strings_in_bucket(bucket_name)
        for oks in object_key_strings:
            source_list.append(
                BlobStorageStructureSource.from_bucket_name_and_object_key(
                    bucket_name=bucket_name, object_key=ObjectKey.from_string(oks)
                )
            )
    return thing_node_list, source_list, sink_list
