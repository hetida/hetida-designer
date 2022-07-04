from typing import Any, Dict, List, Optional

# pylint: disable=duplicate-code

thing_node_json_objects: List[Dict[str, Any]] = [
    {
        "id": "root",
        "parentId": None,
        "name": "Plants",
        "description": "All Plants",
    },
    {
        "id": "root.plantA",
        "parentId": "root",
        "name": "Plant A",
        "description": "Plant A",
    },
    {
        "id": "root.plantB",
        "parentId": "root",
        "name": "Plant B",
        "description": "Plant B",
    },
    {
        "id": "root.plantA.picklingUnit",
        "parentId": "root.plantA",
        "name": "Pickling Unit",
        "description": "Plant A Pickling Unit",
    },
    {
        "id": "root.plantB.picklingUnit",
        "parentId": "root.plantB",
        "name": "Pickling Unit",
        "description": "Plant B Pickling Unit",
    },
    {
        "id": "root.plantA.millingUnit",
        "parentId": "root.plantA",
        "name": "Milling Unit",
        "description": "Plant A Milling Unit",
    },
    {
        "id": "root.plantB.millingUnit",
        "parentId": "root.plantB",
        "name": "Milling Unit",
        "description": "Plant B Milling Unit",
    },
    {
        "id": "root.plantA.picklingUnit.influx",
        "parentId": "root.plantA.picklingUnit",
        "name": "Pickling Unit Influx",
        "description": "Plant A Pickling Unit Influx",
    },
    {
        "id": "root.plantA.picklingUnit.outfeed",
        "parentId": "root.plantA.picklingUnit",
        "name": "Pickling Unit Outfeed",
        "description": "Plant A Pickling Unit Outfeed",
    },
    {
        "id": "root.plantB.picklingUnit.influx",
        "parentId": "root.plantB.picklingUnit",
        "name": "Pickling Unit Influx",
        "description": "Plant B Pickling Unit Influx",
    },
    {
        "id": "root.plantB.picklingUnit.outfeed",
        "parentId": "root.plantB.picklingUnit",
        "name": "Pickling Unit Outfeed",
        "description": "Plant B Pickling Unit Outfeed",
    },
    {
        "id": "root.plantA.millingUnit.influx",
        "parentId": "root.plantA.millingUnit",
        "name": "Milling Unit Influx",
        "description": "Plant A Milling Unit Influx",
    },
    {
        "id": "root.plantA.millingUnit.outfeed",
        "parentId": "root.plantA.millingUnit",
        "name": "Milling Unit Outfeed",
        "description": "Plant A Milling Unit Outfeed",
    },
    {
        "id": "root.plantB.millingUnit.influx",
        "parentId": "root.plantB.millingUnit",
        "name": "Milling Unit Influx",
        "description": "Plant B Milling Unit Influx",
    },
    {
        "id": "root.plantB.millingUnit.outfeed",
        "parentId": "root.plantB.millingUnit",
        "name": "Milling Unit Outfeed",
        "description": "Plant B Milling Unit Outfeed",
    },
]


def get_thing_nodes(
    parent_id: Optional[str] = None, include_sub_objects: bool = False
) -> List[Dict[str, Any]]:
    if parent_id is None:
        if include_sub_objects:
            return thing_node_json_objects

        return [tn for tn in thing_node_json_objects if tn["parentId"] is None]

    if include_sub_objects:
        return [
            tn
            for tn in thing_node_json_objects
            if tn["id"].startswith(parent_id)
            and len(tn["id"]) != len(parent_id)  # only true subnodes!
        ]

    return [tn for tn in thing_node_json_objects if tn["parentId"] == parent_id]
