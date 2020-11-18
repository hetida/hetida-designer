from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType  # add your own imports here

import pandas as pd
from sklearn.preprocessing import StandardScaler

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(inputs={"data": DataType.Any}, outputs={"scaled": DataType.Any})
def main(*, data):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.

    input_data = data if isinstance(data, pd.DataFrame) else data.to_frame()

    scaler = (
        StandardScaler()
    )  # Skalierung an Mittelwert und Standard-Abweichung (z-score)
    scaled = pd.DataFrame(
        scaler.fit_transform(input_data),
        columns=input_data.columns,
        index=input_data.index,
    )

    return {"scaled": scaled if isinstance(data, pd.DataFrame) else scaled.squeeze()}

