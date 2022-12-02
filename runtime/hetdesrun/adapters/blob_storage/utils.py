import json
from logging import getLogger
from typing import Any, Dict, List, Optional, Tuple

from pydantic import ValidationError

from hetdesrun.adapters.blob_storage.exceptions import (
    BucketNameInvalidError,
    CategoryInvalidError,
    ConfigIncompleteError,
    MissingConfigError,
    ThingNodeInvalidError,
)
from hetdesrun.adapters.blob_storage.models import (
    BlobStorageStructureSink,
    BucketName,
    Category,
    IdString,
    StructureThingNode,
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
    for category in structure:
        try:
            thing_node = category.to_thing_node(
                parent_id, separator="/" if bucket_level > level else "-"
            )
        except ValidationError as error:
            msg = (
                f"Validation Error for transformation of category {str(category)} "
                "to StructureThingNode:\n{}"
            )
            logger.error(msg)
            raise ThingNodeInvalidError(msg) from error

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
        else:
            if level > bucket_level:
                snk_append_list.append(
                    BlobStorageStructureSink.from_thing_node(
                        thing_node, name="Next Trained Model"
                    )
                )
            else:
                msg = (
                    f"Category {str(category)} has to few levels of subcategories ({level}) "
                    f"to generate buckets with bucket level {str(bucket_level)}"
                )
                logger.error(msg)
                raise ConfigIncompleteError(msg)


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
