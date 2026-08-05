"""Helper functions for metadata extraction

This module provides functions to help extracting information from metadata
provided as .attrs with pandas DataFrame / Series objects following the hetida
designer metadata conventions.

They properly cascade defaults / fallbacks
and try to provide backwards compatible access to metadata for different versions
of the metadata conventions or simpler metadata structures.
"""

from collections import defaultdict
from collections.abc import Callable
from typing import Any, cast

import pandas as pd
from glom import A, Check, Coalesce, GlomError, Iter, Merge, S, Spec, T, glom


def update_dict_and_return_it(start_dict: dict, updated_values_dict: dict) -> dict:
    """Update a dict and return it"""
    start_dict.update(updated_values_dict)
    return start_dict


def spec_not_none(spec: str | Spec) -> Spec:
    return (spec, Check(validate=lambda x: x is not None))


def glom_dict_with_keys_of_current_dict_and_values_something_deeper_nested(
    deeper_glom_spec: Spec, add_keys_with_none_values: list[str] | None = None
) -> Spec:
    """Create dicts with keys from current dict and values from deeper in their value objects

    This function provides a glom spec to do this.
    It uses https://glom.readthedocs.io/en/latest/tutorial.html#data-driven-assignment.

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
    """Build dict from an iterable

    Spec to convert an iterable of objects to a dict using one of their fields
    (or something deeper) as keys and something else as values.

    The key something and the value something can be arbitrary specs that are applyable
    on each item.

    The resulting glom spec first produces a dictionary which keys being extracted from
    each element of the iterable using key_spec and values using value_spec.

    If given it then proceeds on the resulting object using the continuation_spec.

    add_keys_with_none_values allows to add keys even if they do not occur
    with a default value of None.

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


def spec_by_metric_key_by_val_dimension(metadatum_key: str | Spec) -> Spec:
    """Providesglom spec that extracts a metadatum by metric by value dimension

    The generated glom spec returns a defaultdict of defaultdicts:
        {metric_key: {value_dimension_column_name: metadatum_value}}
    defaulting to None in the inner default dict.

    Properly falls back to respective field in metric metadatum for the "value"
    value_dimension if this value dimension is not explicitely included in the
    metadata of the metric.

    Properly falls back to "value_dimensions_shared" metadata if a value_dimension
    is not given for a metric if its available there.

    metadatum_key can also be any glom spec.
    """
    return Coalesce(
        (  # current metdadata convention
            {  # first gather information at different locations in metadata in a dict
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
                "defaults_by_metric": Coalesce(
                    (
                        "metrics",
                        Check(instance_of=list),
                        build_dict_from_iterable_from_key_and_subspec_and_then_proceed_on_result(
                            S.globals.metric_key,
                            Coalesce(metadatum_key, default=None),
                            key_as_value=True,
                        ),
                    ),
                    default={},
                ),
                "actual_per_metric_per_value_dimensions": (
                    Coalesce(
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
                        default={},
                    )
                ),
            },
            lambda x: defaultdict(
                lambda: defaultdict(lambda: None, {}),
                {  # combine dicts with gathered information / falling back to defaults
                    metric: defaultdict(
                        lambda: None,
                        {
                            value_dim: info
                            if info is not None  # prio 1: use, if explicitely provided
                            else (
                                x["defaults_by_metric"][metric]
                                if (
                                    value_dim == "value"
                                    and x["defaults_by_metric"].get(metric) is not None
                                )  # prio 2: only for "value" value dim: possibly use from metric
                                else (
                                    x["defaults_by_value_dimension"].get(
                                        value_dim, None
                                    )  # prio 3: from global "value_dimensions_shared"
                                )
                            )
                            for value_dim, info in update_dict_and_return_it(
                                x["defaults_by_value_dimension"].copy(), info_by_val_dim
                            ).items()
                        },
                    )
                    for metric, info_by_val_dim in x[
                        "actual_per_metric_per_value_dimensions"
                    ].items()
                },
            ),
        ),
        (  # another simple variant
            "metric_metadata",
            Check(instance_of=dict),
            glom_dict_with_keys_of_current_dict_and_values_something_deeper_nested(
                {"value": Coalesce(metadatum_key, default=None)}  # only SERIES / only value column.
            ),
        ),
        (  # older / simpler metadata convention
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
        (  # another older / simpler metdata structure
            "metrics",
            Check(instance_of=dict),
            glom_dict_with_keys_of_current_dict_and_values_something_deeper_nested(
                {"value": Coalesce(metadatum_key, default=None)}  # only SERIES / only value column.
            ),
        ),
        default={},
    )


def get_value_dimension_info(
    multitsframe: pd.DataFrame | pd.Series, value_dim_info: str | Spec
) -> defaultdict[str, defaultdict[str, Any]]:
    """Obtain metadata info associated to the value dimensions of the metrics

    Returns a default dict whose values are the entries of the metrics metadata specified via
    "metric_key" in "dataset_metadata".

    Its values are defaultdicts whose keys are the "column" entries of the value dimension
    objects of that metric and whose values are extracted from the value_dimension object
    using using value_dim_info as a glom Spec, typically just a subfield.

    For the default "value" value dimension, if no concrete / explicit information is available
    for this value dimension, a corresponding entry in the metric object may be used.

    For all value dimensions, if no concrete explicit information is available for that value
    dimension in the value_dimensions list under the metric, the global "value_dimensions_shared"
    field of the attrs object is searched for corresponding information.

    If no information is found, None is set as value and is the default value of the
    inner default dict.

    For examples we refer to the corresponding unit tests (/tests/helpers/test_metadata.py).
    """
    return value_dimension_info_from_attrs(multitsframe.attrs, value_dim_info)


def value_dimension_info_from_attrs(
    attrs: Any, value_dim_info: str | Spec
) -> defaultdict[str, defaultdict[str, Any]]:
    """Extraction core of get_value_dimension_info, operating directly on an attrs object"""
    spec = spec_by_metric_key_by_val_dimension(value_dim_info)
    value_dimension_info_by_metric_by_value_dimension = glom(attrs, spec)
    return defaultdict(
        lambda: defaultdict(lambda: None), value_dimension_info_by_metric_by_value_dimension
    )


def get_units(multitsframe: pd.DataFrame) -> defaultdict[str, defaultdict[str, str | None]]:
    return get_value_dimension_info(multitsframe, "unit")


def get_names(multitsframe: pd.DataFrame) -> defaultdict[str, defaultdict[str, str | None]]:
    return get_value_dimension_info(multitsframe, Coalesce("name", default=None))


def get_display_names(multitsframe: pd.DataFrame) -> defaultdict[str, defaultdict[str, str | None]]:
    return get_value_dimension_info(multitsframe, Coalesce("display_name", "name", default=None))


def get_short_display_names(
    multitsframe: pd.DataFrame,
) -> defaultdict[str, defaultdict[str, str | None]]:
    return get_value_dimension_info(
        multitsframe, Coalesce("short_display_name", "display_name", "name", default=None)
    )


def get_measurements(multitsframe: pd.DataFrame) -> defaultdict[str, defaultdict[str, str | None]]:
    return get_value_dimension_info(multitsframe, "measurement")


def spec_by_metric_key(metadatum_key: str | Spec) -> Spec:
    return Coalesce(
        (  # current metdadata convention
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
        (  # some older, simpler metadata structure
            "by_metric",
            glom_dict_with_keys_of_current_dict_and_values_something_deeper_nested(
                Coalesce(metadatum_key, default=None)
            ),
        ),
        (  # another older / simplified metadata structure
            "metrics",
            glom_dict_with_keys_of_current_dict_and_values_something_deeper_nested(
                Coalesce(metadatum_key, default=None)
            ),
        ),
    )


def get_metric_info(multitsframe: pd.DataFrame, metric_info: str | Spec) -> defaultdict[str, Any]:
    """Obtain a defaultdict of metadata associated to metrics

    In contrast to metadata associated to concrete value dimensions, this
    function abstracts access to metadata associated to the underlying metric.

    The keys are the entries of the metrics metadata specified via
    "metric_key" in "dataset_metadata".

    The values are the entries specified via metric_info in the metrics metadata.
    Note that metric_info is interpreted as a glom Spec.

    The default value of the default dict is None.

    E.g. for
    multitsframe.attrs = {
        "dataset_metadata": {
            "metric_key": "id"
        },
        "metrics": [
            {
                "id": "first",
                "external_id": "external_first",
                "unit": "m",
                "display_name": "first display name",
                "value_dimensions": [
                    {
                        "column": "temp",
                        "unit": "C",
                        "measurement": "temperature"
                    }
                ]
            },
            {
                "id": "second",
                "name": "second name",
                "external_id": "external_second",
                "value_dimensions": [
                    {
                        "column": "temp",
                        "unit": "C"
                    }
                ]
            }
        ]
    }

    get_metric_info(multitsframe, "external_id")
    # will yield a default dict with underlying dict:
    {
        "first": "external_first",
        "second": "external_second"
    }

    """
    return metric_info_from_attrs(multitsframe.attrs, metric_info)


def metric_info_from_attrs(attrs: Any, metric_info: str | Spec) -> defaultdict[str, Any]:
    """Extraction core of get_metric_info, operating directly on an attrs object"""
    spec = spec_by_metric_key(metric_info)
    extracted_metric_info = glom(attrs, spec)
    return defaultdict(lambda: None, extracted_metric_info)


def extract_series_metric_key(metadata: Any) -> Any:
    return glom(metadata, Coalesce("dataset_metadata.single_metric", default="series"))


def get_series_info(series: pd.Series, value_dim_info: str | Spec) -> Any:
    """Get an arbitrary series info

    Since a series has only one value dimension named "value", this information is
    equivalent to information on the metric.

    Since the fallback behaviour for this value dimension is to fall back to the metric
    metadata, we can reuse the code that extracts value_dimension metadata for
    this value dimension.
    """
    series_metric_key = extract_series_metric_key(series.attrs)

    from_new_convention = get_value_dimension_info(series, value_dim_info)[series_metric_key][
        "value"
    ]
    if from_new_convention is not None:
        return from_new_convention

    # compatibility with some older format

    return glom(
        series.attrs,
        Coalesce(
            spec_not_none(
                (
                    "single_metric_metadata.structured_metadata.value_dimensions.value",
                    value_dim_info,
                )
            ),
            spec_not_none(
                (
                    "single_metric_metadata.structured_metadata.metric",
                    value_dim_info,
                )
            ),
            default=None,
        ),
    )


def get_series_unit(series: pd.Series) -> str | None:
    return cast(str | None, get_series_info(series, spec_not_none("unit")))


def get_series_name(series: pd.Series) -> str | None:
    return cast(str | None, get_series_info(series, spec_not_none("name")))


def get_series_display_name(series: pd.Series) -> str | None:
    return cast(
        str | None,
        get_series_info(series, Coalesce(spec_not_none("display_name"), spec_not_none("name"))),
    )


def get_series_short_display_name(series: pd.Series) -> str | None:
    return cast(
        str | None,
        get_series_info(
            series,
            Coalesce(
                spec_not_none("short_display_name"),
                spec_not_none("display_name"),
                spec_not_none("name"),
            ),
        ),
    )


def get_series_measurement(series: pd.Series) -> str | None:
    return cast(str | None, get_series_info(series, "measurement"))


def extract_singlets_metric_key(metadata: Any) -> Any:
    """The key identifying the single metric of a SingleTSFrame

    A SingleTSFrame follows the same convention as a SERIES here: its single metric is
    named via "dataset_metadata.single_metric".

    Returns None if no such entry is present.
    """
    return glom(metadata, Coalesce("dataset_metadata.single_metric", default=None))


def attrs_with_default_metric_key(attrs: Any) -> Any:
    """Return attrs with "dataset_metadata.metric_key" defaulted to "id"

    The metadata conventions declare metric_key to be optional with "id" as default.
    Returns the original object unchanged if it is not a dict or if a metric_key is set,
    and a shallow-enough copy with the default applied otherwise.
    """
    if not isinstance(attrs, dict):
        return attrs

    dataset_metadata = attrs.get("dataset_metadata")
    if isinstance(dataset_metadata, dict) and dataset_metadata.get("metric_key") is not None:
        return attrs

    defaulted = dict(attrs)
    defaulted["dataset_metadata"] = {
        **(dataset_metadata if isinstance(dataset_metadata, dict) else {}),
        "metric_key": "id",
    }
    return defaulted


def get_singlets_info(
    singletsframe: pd.DataFrame, value_dim_info: str | Spec
) -> defaultdict[str, Any]:
    """Obtain metadata info associated to the value dimensions of a SingleTSFrame

    A SingleTSFrame holds exactly one metric but — like a MultiTSFrame — arbitrarily many
    value dimensions. Therefore, in contrast to get_value_dimension_info (which is keyed by
    metric first), this returns a defaultdict keyed by value dimension column name only,
    defaulting to None.

    The single metric is identified via "dataset_metadata.single_metric". If that is missing
    but the metadata contains exactly one metric, that metric is used, since a SingleTSFrame
    cannot be ambiguous in this respect.
    """
    info_by_metric_by_val_dim = value_dimension_info_from_attrs(
        attrs_with_default_metric_key(singletsframe.attrs), value_dim_info
    )

    metric_key = extract_singlets_metric_key(singletsframe.attrs)
    if metric_key is not None and metric_key in info_by_metric_by_val_dim:
        return info_by_metric_by_val_dim[metric_key]

    if len(info_by_metric_by_val_dim) == 1:
        return next(iter(info_by_metric_by_val_dim.values()))

    return defaultdict(lambda: None)


def get_singlets_units(singletsframe: pd.DataFrame) -> defaultdict[str, str | None]:
    return get_singlets_info(singletsframe, "unit")


def get_singlets_names(singletsframe: pd.DataFrame) -> defaultdict[str, str | None]:
    return get_singlets_info(singletsframe, Coalesce("name", default=None))


def get_singlets_display_names(singletsframe: pd.DataFrame) -> defaultdict[str, str | None]:
    return get_singlets_info(singletsframe, Coalesce("display_name", "name", default=None))


def get_singlets_short_display_names(singletsframe: pd.DataFrame) -> defaultdict[str, str | None]:
    return get_singlets_info(
        singletsframe, Coalesce("short_display_name", "display_name", "name", default=None)
    )


def get_singlets_measurements(singletsframe: pd.DataFrame) -> defaultdict[str, str | None]:
    return get_singlets_info(singletsframe, "measurement")


def get_singlets_metric_info(singletsframe: pd.DataFrame, metric_info: str | Spec) -> Any:
    """Obtain metadata of the single metric of a SingleTSFrame

    Counterpart of get_metric_info for SingleTSFrames: instead of a mapping keyed by metric
    this directly returns the requested information for the one metric, or None if it cannot
    be determined. In particular this includes the case of absent metric metadata: components
    should not require metadata (see the metadata conventions documentation).
    """
    try:
        info_by_metric = metric_info_from_attrs(
            attrs_with_default_metric_key(singletsframe.attrs), metric_info
        )
    except GlomError:  # no metric metadata present at all
        return None

    metric_key = extract_singlets_metric_key(singletsframe.attrs)
    if metric_key is not None and metric_key in info_by_metric:
        return info_by_metric[metric_key]

    if len(info_by_metric) == 1:
        return next(iter(info_by_metric.values()))

    return None
