from hetdesrun.adapters.component_adapter.config import (
    get_allowed_component_states,
    get_component_adapter_config,
)
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.utils import Type


def validate_source_trafos_for_component_adapter(
    transformation_revisions: list[TransformationRevision], allow_disabled: bool = True
) -> None:
    """Validate trafos as component sources

    raises ValueError if some condition from configuration or concerning io is
    not true for some trafo.
    """
    allowed_states = get_allowed_component_states(allow_disabled=allow_disabled)

    allowed_source_categories = get_component_adapter_config().allowed_source_categories

    if allowed_source_categories is None:  # noqa: SIM108 # explicitely for mypy
        allowed_cats = None
    else:
        allowed_cats = list(allowed_source_categories)

    for trafo in transformation_revisions:
        if not trafo.type is Type.COMPONENT:
            msg = (
                f"Tranformation {trafo.name} ({trafo.version_tag}) with id {trafo.id}"
                " is not a component. Component adapter can only use components."
            )
            raise ValueError(msg)

        if trafo.state not in allowed_states:
            msg = (
                f"Component {trafo.name} ({trafo.version_tag}) with id {trafo.id}"
                f" has state {trafo.state} which is not allowed. Allowed states are"
                f" {allowed_states}."
            )
            raise ValueError(msg)

        if allowed_cats is not None and trafo.category not in allowed_cats:
            msg = (
                f"Component {trafo.name} ({trafo.version_tag}) with id {trafo.id}"
                f" has category {trafo.category} which is not allowed for component sources."
                f" Allowed categories for component sources are {allowed_cats}."
            )
            raise ValueError(msg)

        if len(trafo.io_interface.outputs) != 1:
            msg = (
                f"Component {trafo.name} ({trafo.version_tag}) with id {trafo.id}"
                f" has more than one output which is not allowed for component sources."
                " Component sources need exactly one output."
            )
            raise ValueError(msg)


def validate_sink_trafos_for_component_adapter(
    transformation_revisions: list[TransformationRevision], allow_disabled: bool = True
) -> None:
    """Validate trafos as component sinks

    raises ValueError if some condition from configuration or concerning io is
    not true for some trafo.
    """
    allowed_states = get_allowed_component_states(allow_disabled=allow_disabled)

    allowed_sink_categories = get_component_adapter_config().allowed_sink_categories

    if allowed_sink_categories is None:  # noqa: SIM108 # explicitely for mypy
        allowed_cats = None
    else:
        allowed_cats = list(allowed_sink_categories)

    for trafo in transformation_revisions:
        if not trafo.type is Type.COMPONENT:
            msg = (
                f"Tranformation {trafo.name} ({trafo.version_tag}) with id {trafo.id}"
                " is not a component. Component adapter can only use components."
            )
            raise ValueError(msg)

        if trafo.state not in allowed_states:
            msg = (
                f"Component {trafo.name} ({trafo.version_tag}) with id {trafo.id}"
                f" has state {trafo.state} which is not allowed. Allowed states are"
                f" {allowed_states}."
            )
            raise ValueError(msg)

        if allowed_cats is not None and trafo.category not in allowed_cats:
            msg = (
                f"Component {trafo.name} ({trafo.version_tag}) with id {trafo.id}"
                f" has category {trafo.category} which is not allowed for component sinks."
                f" Allowed categories for component sinks are {allowed_cats}."
            )
            raise ValueError(msg)

        if not "data" in [trafo_inp.name for trafo_inp in trafo.io_interface.inputs]:
            msg = (
                f"Component {trafo.name} ({trafo.version_tag}) with id {trafo.id}"
                f" has no input named 'data' which is not allowed for component sinks."
                " Component sinks always need a 'data' input."
            )
            raise ValueError(msg)

        if len(trafo.io_interface.outputs) != 0:
            msg = (
                f"Component {trafo.name} ({trafo.version_tag}) with id {trafo.id}"
                f" has outputs which is not allowed for component sinks."
                " Component sinks only have inputs."
            )
            raise ValueError(msg)
