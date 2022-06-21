import json

from typing import Any

from pydantic import BaseModel


import pandas as pd
import numpy as np

from hetdesrun.datatypes import AdvancedTypesOutputSerializationConfig


def test_serialization():
    class OutputModel(BaseModel):
        s: Any

        Config = AdvancedTypesOutputSerializationConfig

    om = OutputModel(s=pd.Series([1.2, 2.0, None]))
    assert np.isnan(om.s.iloc[2])

    # None is present after serialization:

    loaded_json = json.loads(om.json())
    assert loaded_json["s"]["2"] is None
    assert isinstance(loaded_json["s"]["1"], float)
