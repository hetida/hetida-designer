import logging
from typing import Any
from uuid import UUID

from pydantic import ValidationError

from hetdesrun.adapters.component_adapter.config import (
    get_allowed_component_states,
    get_component_adapter_config,
)
from hetdesrun.adapters.component_adapter.models import (
    ComponentAdapterStructureSink,
    ComponentAdapterStructureSource,
    StructureResponse,
    StructureThingNode,
)
from hetdesrun.adapters.component_adapter.utils import data_type_to_external_type_map
from hetdesrun.adapters.exceptions import AdapterHandlingException
from hetdesrun.models.code import ValidStr
from hetdesrun.persistence.dbservice.revision import (
    get_distinct_categories,
    select_multiple_transformation_revisions,
)
from hetdesrun.persistence.models.io import InputType, TransformationInput
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.utils import Type

logger = logging.getLogger(__name__)


def extract_filters_from_component(
    component: TransformationRevision, as_sink: bool = False
) -> dict[str, dict[str, Any]]:
    """Maps inputs to filters

    * All inputs but the single "data" input for sink components
    * "timestampTo" and "timestampFrom" are not explicitely added as filters
      since they are automatically
    added by frontend for respective types

    All filters extracted this way get the "free_text" type since currently there are no other
    choosable filter types.

    """
    component_inputs = component.io_interface.inputs

    return {
        inp.name: {
            "name": inp.name,
            "type": "free_text",
            "required": (inp.type is InputType.REQUIRED),  # not required means optional
            "default_value": inp.value,  # None if not set
        }
        for inp in component_inputs
        if (not as_sink or inp.name != "data")
        and (inp.name not in {"timestampFrom", "timestampTo"})
        and inp.name is not None
    }


def get_all_component_sources(
    ids: list[UUID] | None = None,
    allowed_categories: list[ValidStr] | None = None,
    with_disabled_components: bool = False,
) -> list[ComponentAdapterStructureSource]:
    """Obtains components appliable as comp. sources and wraps them as sources

    if allowed_categories is None, all categories are allowed. Else this restricts which
    categories are allowed and only returns appliable comp. sources with one of these
    categories.
    """
    try:
        components = select_multiple_transformation_revisions(
            type=Type.COMPONENT,
            categories=allowed_categories,
            ids=ids,
            states=get_allowed_component_states(allow_disabled=with_disabled_components),
        )
    except Exception as e:
        msg = (
            f"Could not obtain components from database for component adapter. Error was:\n{str(e)}"
        )
        logger.error(msg)
        raise e

    return sorted(
        [
            ComponentAdapterStructureSource(
                type=(
                    ext_type := data_type_to_external_type_map[
                        component.io_interface.outputs[0].data_type
                    ]
                ),
                id=str(component.id)
                if not (is_metadatum := str(ext_type).lower().startswith("metadata"))
                else component.category,  # metadata are regarded as attached to thingnodes
                thingNodeId=component.category,
                name=component.name + " (" + component.version_tag + ")",
                path=component.category + "/" + component.name + " (" + component.version_tag + ")",
                metadataKey=str(component.id) if is_metadatum else None,
                filters=extract_filters_from_component(component),
            )
            for component in components
            if len(component.io_interface.outputs) == 1  # excatly one output
        ],
        key=lambda x: x.name,
    )


def get_data_input(trafo: TransformationRevision) -> TransformationInput:
    """Extracts the input with name data for sink components"""
    data_inputs = [trafo_inp for trafo_inp in trafo.io_interface.inputs if trafo_inp.name == "data"]
    if len(data_inputs) != 1:
        msg = (
            f"There is not excatly one data input in trafo "
            f"{trafo.name} ({trafo.version_tag}) with id{trafo.id} "
        )
        raise ValueError(msg)
    return data_inputs[0]


def get_all_component_sinks(
    ids: list[UUID] | None = None,
    allowed_categories: list[ValidStr] | None = None,
    with_disabled_components: bool = False,
) -> list[ComponentAdapterStructureSink]:
    """Obtains components appliable as comp. sinks and wraps them as sinks

    if allowed_categories is None, all categories are allowed. Else this restricts which
    categories are allowed and only returns appliable comp. sinks with one of these
    categories.
    """
    try:
        components = select_multiple_transformation_revisions(
            type=Type.COMPONENT,
            categories=allowed_categories,
            ids=ids,
            states=get_allowed_component_states(allow_disabled=with_disabled_components),
        )
    except Exception as e:
        msg = (
            f"Could not obtain components from database for component adapter. Error was:\n{str(e)}"
        )
        logger.error(msg)
        raise e

    return sorted(
        [
            ComponentAdapterStructureSink(
                type=(
                    ext_type := data_type_to_external_type_map[get_data_input(component).data_type]
                ),
                id=str(component.id)
                if not (is_metadatum := str(ext_type).lower().startswith("metadata"))
                else component.category,  # metadata are regarded as attached to thingnodes
                thingNodeId=component.category,
                name=component.name + " (" + component.version_tag + ")",
                path=component.category + "/" + component.name + " (" + component.version_tag + ")",
                metadataKey=str(component.id) if is_metadatum else None,
                filters=extract_filters_from_component(component, as_sink=True),
            )
            for component in components
            if (
                (len(component.io_interface.outputs) == 0)
                and ("data" in [inp.name for inp in component.io_interface.inputs])
            )  # no output and a "data" input must be present.
        ],
        key=lambda x: x.name,
    )


def get_structure(parent_id: str | None = None) -> StructureResponse:
    allowed_source_categories = get_component_adapter_config().allowed_source_categories
    allowed_sink_categories = get_component_adapter_config().allowed_sink_categories

    if parent_id is None:
        categories = sorted(
            [
                category
                for category in get_distinct_categories(types={Type.COMPONENT})
                if (
                    allowed_source_categories is None
                    or allowed_sink_categories is None
                    or category in allowed_source_categories
                    or category in allowed_sink_categories
                )
            ]
        )

        return StructureResponse(
            id="component-adapter",
            name="Component Adapter",
            thingNodes=[
                StructureThingNode(
                    id=category,
                    parentId=None,
                    name=category,
                    description=f"Components suitable as sources/sinks in category {category}",
                )
                for category in categories
            ],
            sinks=[],
            sources=[],
        )

    if (
        allowed_source_categories is None
        or allowed_sink_categories is None
        or parent_id in allowed_source_categories
        or parent_id in allowed_sink_categories
    ):
        try:
            valid_parent_id = ValidStr(parent_id)
        except ValidationError as e:
            msg = (
                f"provided parent id to component adapter is not a ValidStr."
                f" Exception was:\n{str(e)}"
            )
            logger.warning(msg)
            sources_of_category = []
            sinks_of_category = []
        else:
            sources_of_category = get_all_component_sources(allowed_categories=[valid_parent_id])
            sinks_of_category = get_all_component_sinks(allowed_categories=[valid_parent_id])
    else:
        sources_of_category = []
        sinks_of_category = []

    return StructureResponse(
        id="component-adapter",
        name="Component Adapter",
        thingNodes=[],
        sinks=sinks_of_category,
        sources=sources_of_category,
    )


def get_thing_node_by_id(id: str) -> StructureThingNode | None:  # noqa: A002
    allowed_source_categories = get_component_adapter_config().allowed_source_categories
    allowed_sink_categories = get_component_adapter_config().allowed_sink_categories

    if (
        allowed_source_categories is None
        or allowed_sink_categories is None
        or id in allowed_source_categories
        or id in allowed_sink_categories
    ):
        try:
            _ = ValidStr(id)
        except ValidationError as e:
            msg = (
                f"provided thing node id to component adapter is not a ValidStr."
                f" Exception was:\n{str(e)}"
            )
            logger.info(msg)
            return None

        return StructureThingNode(
            id=id,
            parentId=None,
            name=id,
            description=f"Components suitable as sources/sinks in category {id}",
        )
    return None


def get_source_by_id(source_id: str) -> ComponentAdapterStructureSource | None:
    """Get specific component adapter source by id

    Returns None if source could not be found
    """

    resulting_component_sources = get_all_component_sources(
        ids=[UUID(source_id)], with_disabled_components=True
    )  # when explicitely querying "known" sources one should be able to get deprecated ones
    # Otherwise they wouldn't work anymore. The frontend does this when loading a wiring.

    if len(resulting_component_sources) > 1:
        msg = (
            f"Found {len(resulting_component_sources)} results when looking"
            " for one component adapter source with id {source_id}"
        )
        logger.error(msg)
        raise AdapterHandlingException(msg)

    if len(resulting_component_sources) == 0:
        return None

    allowed_source_categories = get_component_adapter_config().allowed_source_categories
    if (
        allowed_source_categories is None
        or resulting_component_sources[0].thingNodeId in allowed_source_categories
    ):
        return resulting_component_sources[0]

    return None


def get_sources(filter_str: str | None = None) -> list[ComponentAdapterStructureSource]:
    """Get component sources, filterable by name

    Allow for case-insensistive filtering of the Component source name
    which includes the tag.
    """

    allowed_source_categories = get_component_adapter_config().allowed_source_categories

    if allowed_source_categories is None:  # noqa: SIM108 # explicitely for mypy
        allowed_cats = None
    else:
        allowed_cats = list(allowed_source_categories)

    return [
        component_source
        for component_source in get_all_component_sources(allowed_categories=allowed_cats)
        if filter_str is None or (filter_str.lower() in component_source.name.lower())
    ]


def get_sink_by_id(sink_id: str) -> ComponentAdapterStructureSink | None:
    """Get specific component adapter sink by id

    Returns None if sink could not be found
    """

    resulting_component_sinks = get_all_component_sinks(
        ids=[UUID(sink_id)], with_disabled_components=True
    )  # when explicitely querying "known" sinks one should be able to get deprecated ones
    # Otherwise they wouldn't work anymore. The frontend does this when loading a wiring.

    if len(resulting_component_sinks) > 1:
        msg = (
            f"Found {len(resulting_component_sinks)} results when looking"
            " for one component adapter sink with id {sink_id}"
        )
        logger.error(msg)
        raise AdapterHandlingException(msg)

    if len(resulting_component_sinks) == 0:
        return None

    allowed_sink_categories = get_component_adapter_config().allowed_sink_categories
    if (
        allowed_sink_categories is None
        or resulting_component_sinks[0].thingNodeId in allowed_sink_categories
    ):
        return resulting_component_sinks[0]

    return None


def get_sinks(filter_str: str | None = None) -> list[ComponentAdapterStructureSink]:
    """Get component sinks, filterable by name

    Allow for case-insensistive filtering of the Component sink name
    which includes the tag.
    """

    allowed_sink_categories = get_component_adapter_config().allowed_sink_categories

    if allowed_sink_categories is None:  # noqa: SIM108 # explicitely for mypy
        allowed_cats = None
    else:
        allowed_cats = list(allowed_sink_categories)

    return [
        component_sink
        for component_sink in get_all_component_sinks(allowed_categories=allowed_cats)
        if filter_str is None or (filter_str.lower() in component_sink.name.lower())
    ]
