from typing import List

from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.trafoutils.filter.mapping import filter_and_order_trafos
from hetdesrun.trafoutils.filter.params import FilterParams


def order_for_importing(
    transformation_revisions: List[TransformationRevision],
    raise_on_missing_dependency: bool = False,
) -> List[TransformationRevision]:
    """Order an ensemble of trafo revs without filtering"""
    all_allow_filter_params = FilterParams(include_dependencies=False)
    return filter_and_order_trafos(
        transformation_revisions,
        all_allow_filter_params,
        raise_on_missing_dependency=raise_on_missing_dependency,
    )
