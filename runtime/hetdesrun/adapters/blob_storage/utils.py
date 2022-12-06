from logging import getLogger
from typing import List, Optional, Tuple

from pydantic import ValidationError

from hetdesrun.adapters.blob_storage.exceptions import (
    BucketNameInvalidError,
    ConfigError,
    ConfigIncompleteError,
    MissingConfigError,
    ThingNodeInvalidError,
)
from hetdesrun.adapters.blob_storage.models import (
    BlobAdapterConfig,
    BlobStorageStructureSink,
    BlobStorageStructureSource,
    BucketName,
    Category,
    IdString,
    ObjectKey,
    StructureThingNode,
)
from hetdesrun.adapters.blob_storage.service import get_object_key_strings_in_bucket

logger = getLogger(__name__)


def walk_structure(
    parent_id: Optional[IdString],
    tn_append_list: List[StructureThingNode],
    bucket_append_list: List[BucketName],
    snk_append_list: List[BlobStorageStructureSink],
    structure: List[Category],
    bucket_level: int,
    total_nof_levels: int,
    level: int,
) -> None:
    """Recursively walk structure from config_json."""
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

        if category.substructure is not None:
            walk_structure(
                parent_id=thing_node.id,
                tn_append_list=tn_append_list,
                bucket_append_list=bucket_append_list,
                snk_append_list=snk_append_list,
                structure=category.substructure,
                bucket_level=bucket_level,
                total_nof_levels=total_nof_levels,
                level=level + 1,
            )
        else:  # category.substructure is None or len(category.substructure) == 0
            if level < total_nof_levels:
                msg = (
                    f"Category {str(category)} has too few levels of subcategories ({level}) "
                    f"to match the total number of levels ({total_nof_levels})"
                )
                logger.error(msg)
                raise ConfigIncompleteError(msg)
            # level >= bucket_level
            sink = BlobStorageStructureSink.from_thing_node(
                thing_node, name="Next Trained Model"
            )
            snk_append_list.append(sink)
            logger.debug("Created sink:\n%s", str(sink))


def get_setup_from_config(
    path: str = "demodata/blob_storage_adapter_config.json",
) -> Tuple[List[StructureThingNode], List[BucketName], List[BlobStorageStructureSink]]:
    try:
        config = BlobAdapterConfig.parse_file(path)
    except FileNotFoundError as error:
        msg = f"Could not find json file at path {path}:\n{str(error)}"
        logger.error(msg)
        raise MissingConfigError(msg) from error

    thing_nodes: List[StructureThingNode] = []
    bucket_names: List[BucketName] = []
    sinks: List[BlobStorageStructureSink] = []

    walk_structure(
        parent_id=None,
        tn_append_list=thing_nodes,
        bucket_append_list=bucket_names,
        snk_append_list=sinks,
        structure=config.structure,
        bucket_level=config.bucket_level,
        total_nof_levels=config.total_number_of_levels,
        level=1,
    )

    return thing_nodes, bucket_names, sinks


def setup_adapter() -> Tuple[
    List[StructureThingNode],
    List[BlobStorageStructureSource],
    List[BlobStorageStructureSink],
]:
    thing_node_list, bucket_names_from_setup, sink_list = get_setup_from_config()
    if len(bucket_names_from_setup) != len(set(bucket_names_from_setup)):
        seen = set()
        duplicates = []
        for bucket_name in bucket_names_from_setup:
            if bucket_name in seen:
                duplicates.append(bucket_name)
            else:
                seen.add(bucket_name)
        msg = (
            "The bucket names generated from the config file are not unique!\n"
            "They contain the following duplicates: "
            + ", ".join(duplicate for duplicate in duplicates)
        )
        raise ConfigError(msg)

    source_list: List[BlobStorageStructureSource] = []
    for bucket_name in bucket_names_from_setup:
        object_key_strings = get_object_key_strings_in_bucket(bucket_name)
        for object_key_string in object_key_strings:
            object_key = ObjectKey.from_string(object_key_string)

            # ignore objects that do not match the config hierarchy
            thing_node_id = IdString(bucket_name + "/" + object_key.name)
            if len([tn for tn in thing_node_list if tn.id == thing_node_id]) == 0:
                continue
            source = BlobStorageStructureSource.from_bucket_name_and_object_key(
                bucket_name=bucket_name, object_key=object_key
            )
            source_list.append(source)
            logger.debug("Created source:\n%s", source)

    return thing_node_list, source_list, sink_list
