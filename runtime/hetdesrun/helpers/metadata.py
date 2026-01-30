"""Helper functions for metadata extraction

This module provides functions to help extracting information from metadata
provided as .attrs with pandas DataFrame / Series objects following the hetida
designer metadata conventions. They properly cascades defaults / fallbacks
and try to provide backwards compatible access to metadata for different versions
of the metadata conventions.
"""

from collections import defaultdict
from collections.abc import Callable
from typing import Any

import pandas as pd
from glom import A, Check, Coalesce, Iter, Merge, S, Spec, T, glom


def update_dict_and_return_it(start_dict: dict, updated_values_dict: dict) -> dict:
    start_dict.update(updated_values_dict)
    return start_dict


def glom_dict_with_keys_of_current_dict_and_values_something_deeper_nested(
    deeper_glom_spec: Spec, add_keys_with_none_values: list[str] | None = None
) -> Spec:
    """Create dicts with keys from current dict and values from deeper in their value objects

    This function provides a glom spec to do this. It uses https://glom.readthedocs.io/en/latest/tutorial.html#data-driven-assignment.

    deeper_glom_spec is the spec to get to the deeper values in each value object.

    add_keys_with_none_values allows to add keys even if they do not occur
    with a default value of None.


    E.g.

    data = {
        'some_other_field': 'value',
        'by_item': {
            'item1': {
                'metadata': {
                    'properties': {
                        'unit': 'kg'
                    }
                }
            },
            'item2': {
                'info': {
                    'details': {
                        'unit': 'meters'
                    }
                }
            },
            'item3': {
                'unit': 'liters'
            }
        }
    }

    res = glom(
        data,
        (
            "by_item",
            glom_dict_with_keys_of_current_dict_and_values_something_deeper_nested(
                Coalesce(
                    "metadata.properties.unit", "info.details.unit", "unit", default=None
                )
            ),
        ),
    )
    print(res)
    # will output:
    #     {'item1': 'kg', 'item2': 'meters', 'item3': 'liters'}

    """
    if add_keys_with_none_values is None:
        add_keys_with_none_values = []

    start_dict = dict.fromkeys(add_keys_with_none_values, None)

    return (
        T.items(),  # treat it as list of (key, value) tuples
        Iter({T[0]: (T[1], deeper_glom_spec)}),
        Merge(),
        lambda x: update_dict_and_return_it(start_dict.copy(), x),
    )


def build_dict_from_iterable_from_key_and_subspec_and_then_proceed_on_result(
    key_spec: Spec,
    value_spec: Spec,
    add_keys_with_none_values: list[str] | None = None,
    default_dict_func: Callable | None = None,
    continuation_spec: Spec | None = None,
    key_as_value: bool = False,
) -> Spec:
    """
    Spec to convert a list of objects to a dict using one of their fields (or something deeper)
    as keys and something else as values — and then proceed with another spec.

    The key something and the value something can be arbitrary

    To be applied on an iterable!

    The resulting glom spec first produces a dictionary which keys being extracted from
    each element of the iterable using key_spec and values using value_spec.

    If given it then proceeds on the resulting object using the continuation_spec.

    Example:

    data = {
        "some": [
            {"id": 42, "name": "some_name", "sub": {"unit": "l"}},
            {"id": 53, "name": "another", "sub": {"unit": "m"}},
        ]
    }

    glom(
        data,
        (
            "some",
            build_dict_from_iterable_from_key_and_subspec_and_then_proceed_on_result(
                "id", "sub.unit"
            ),
        ),
    )

    # yields:
    {42: 'l', 53: 'm'}


    """
    if add_keys_with_none_values is None:
        add_keys_with_none_values = []

    start_dict = dict.fromkeys(add_keys_with_none_values, None)

    if default_dict_func is not None:
        start_dict = defaultdict(default_dict_func, start_dict)

    return (
        [{"key": key_spec if not key_as_value else T[key_spec], "value": value_spec}],
        [lambda x: (x["key"], x["value"])],
        dict,
        lambda x: update_dict_and_return_it(start_dict.copy(), x),
    ) + ((continuation_spec,) if continuation_spec is not None else ())


def breakpoint_and_continue(x: Any) -> Any:
    breakpoint()
    return x


def spec_by_metric_key_by_val_dimension(metadatum_key: str | Spec) -> Spec:
    """Glom spec that extracts a metadatum by metric by value dimension


    Returns a dict of dicts:
        {metric_key: {value_dimension_column_name: metadatum_value}}

    Properly falls back to respective field in metric metadatum for the "value"
    value_dimension if this value dimension is not explicitely included.

    Properly falls back to "value_dimensions_shared" metadata if a value_dimension
    is not given for a metric if its available there.

    metadatum_key can also be a spec

    """
    return Coalesce(
        (  # new metdadata convention
            {
                "metric_key": ("dataset_metadata.metric_key", A.globals.metric_key),
                "defaults_by_value_dimension": (
                    Coalesce(
                        (
                            Coalesce("value_dimensions_shared", default=[]),
                            Check(instance_of=list),
                            build_dict_from_iterable_from_key_and_subspec_and_then_proceed_on_result(
                                "column", Coalesce(metadatum_key, default=None)
                            ),
                        ),
                        default={},
                    ),
                ),
                "defaults_by_metric": (
                    "metrics",
                    Check(instance_of=list),
                    build_dict_from_iterable_from_key_and_subspec_and_then_proceed_on_result(
                        S.globals.metric_key,
                        Coalesce(metadatum_key, default=None),
                        key_as_value=True,
                    ),
                ),
                "actual_per_metric_per_value_dimensions": (  # current metadata convention
                    (
                        "metrics",
                        Check(instance_of=list),
                        build_dict_from_iterable_from_key_and_subspec_and_then_proceed_on_result(
                            S.globals.metric_key,
                            (
                                Coalesce("value_dimensions", default={}),
                                build_dict_from_iterable_from_key_and_subspec_and_then_proceed_on_result(
                                    "column",
                                    Coalesce(metadatum_key, default=None),
                                    add_keys_with_none_values=["value"],
                                ),
                            ),
                            key_as_value=True,
                        ),
                    ),
                ),
            },
            lambda x: defaultdict(
                lambda: defaultdict(lambda: None, {}),
                {  # combine dicts / falling back to defaults
                    metric: defaultdict(
                        lambda: None,
                        {
                            value_dim: unit
                            if unit is not None
                            else (
                                x["defaults_by_metric"][metric]
                                if (
                                    value_dim == "value"
                                    and x["defaults_by_metric"].get(metric) is not None
                                )
                                # fallback to metric metadata unit for "value" value dimension
                                # if provided
                                else (x["defaults_by_value_dimension"].get(value_dim, None))
                            )
                            for value_dim, unit in update_dict_and_return_it(
                                x["defaults_by_value_dimension"].copy(), unit_by_value_dim
                            ).items()
                        },
                    )
                    for metric, unit_by_value_dim in x[
                        "actual_per_metric_per_value_dimensions"
                    ].items()
                },
            ),
        ),
        (  # current metadata convention
            "by_metric",
            Check(instance_of=dict),
            glom_dict_with_keys_of_current_dict_and_values_something_deeper_nested(
                (
                    Coalesce("value_dimensions", default={}),
                    Check(instance_of=dict),
                    glom_dict_with_keys_of_current_dict_and_values_something_deeper_nested(
                        Coalesce(metadatum_key, default=None)
                    ),
                )
            ),
        ),
        (  # older, currently used by Hetida Platform Channel Data component
            # by simply attaching the data it gets via SERIES endpoint of adapter
            "metrics",
            Check(instance_of=dict),
            glom_dict_with_keys_of_current_dict_and_values_something_deeper_nested(
                {"value": Coalesce(metadatum_key, default=None)}  # only SERIES / only value column.
            ),
        ),
    )


multits_unit_spec = spec_by_metric_key_by_val_dimension("unit")


def get_units(multitsframe: pd.DataFrame) -> dict[str, dict[str, str | None]]:
    units_by_metric_by_value_dimension = glom(multitsframe.attrs, multits_unit_spec)
    return defaultdict(lambda: defaultdict(lambda: None), units_by_metric_by_value_dimension)


multits_display_name_spec = spec_by_metric_key_by_val_dimension(
    Coalesce("display_name", "name", default=None)
)


def get_display_names(multitsframe: pd.DataFrame) -> dict[str, dict[str, str | None]]:
    display_names_by_metric_by_value_dimension = glom(multitsframe.attrs, multits_display_name_spec)
    return defaultdict(
        lambda: defaultdict(lambda: None), display_names_by_metric_by_value_dimension
    )


def spec_by_metric_key(metadatum_key: str | Spec) -> Spec:
    return Coalesce(
        (  # new metdadata convention
            {
                "metric_key": ("dataset_metadata.metric_key", A.globals.metric_key),
                "by_metric": (
                    "metrics",
                    Check(instance_of=list),
                    build_dict_from_iterable_from_key_and_subspec_and_then_proceed_on_result(
                        S.globals.metric_key,
                        Coalesce(metadatum_key, default=None),
                        key_as_value=True,
                    ),
                ),
            },
            lambda x: defaultdict(lambda: None, x["by_metric"]),
        ),
        (  # current metadata convention
            "by_metric",
            glom_dict_with_keys_of_current_dict_and_values_something_deeper_nested(
                Coalesce(metadatum_key, default=None)
            ),
        ),
        (  # older, currently used by Hetida Platform Channel Data component
            # by simply attaching the data it gets via SERIES endpoint of adapter
            "metrics",
            glom_dict_with_keys_of_current_dict_and_values_something_deeper_nested(
                Coalesce(metadatum_key, default=None)
            ),
        ),
    )


multits_measurement_spec = spec_by_metric_key("measurement")


def get_measurements(multitsframe: pd.DataFrame) -> dict[str, dict[str, str | None]]:
    measurements_by_metric = glom(multitsframe.attrs, multits_measurement_spec)
    return defaultdict(lambda: None, measurements_by_metric)
