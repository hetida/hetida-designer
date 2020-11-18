from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType # add your own imports here

import statsmodels.api as sm

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={"package": DataType.String, "dataname": DataType.String},
    outputs={"data": DataType.DataFrame},
)
def main(*, package, dataname):
    """Download R dataset
    
    See
        https://vincentarelbundock.github.io/Rdatasets/datasets.html
    for a list of packages and datasets.

    Usage examples:
    >>> data = main(package="AER", dataname="CollegeDistance")["data"]
    >>> len(data)
    4739
    >>> iris = main(package="datasets", dataname="iris")["data"]
    >>> len(iris)
    150
    """
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    return {"data": sm.datasets.get_rdataset(dataname, package=package).data}

