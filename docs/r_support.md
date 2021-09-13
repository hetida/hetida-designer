# R Support in hetida designer

hetida designer focuses on the Python data science stack and does not support writing components using R directly. However, it is possible to utilize [rpy2](https://rpy2.github.io/) to run R code from the Python code of a component.

This page describes a very basic setup example for this.

## Preparing your Setup

Create a a new file Dockerfile `Dockerfile-runtime-basic-R-support` containing for example

```dockerfile
FROM hetida/designer-runtime

USER root

RUN apt-get update
RUN apt-get install -y r-base build-essential

# install some R package:
RUN Rscript -e 'install.packages(c("TDA"), repos="https://cloud.r-project.org")'

RUN pip install rpy2

USER hdrt_app

```

This example installs R and rpy2 and the R package "TDA".

Now save the default `docker-compose.yml` file as a new file with name `docker-compose-basic-R-support.yml` and edit the hetida designer runtime service section as follows:

```yml
...
  hetida-designer-runtime:
    build:
        context: .
        dockerfile: Dockerfile-runtime-basic-R-support
...
```

After that build the modified runtime image with

```bash
docker-compose -f docker-compose-basic-R-support.yml build --no-cache hetida-designer-runtime
```

Now you can run your new setup with

```bash
docker-compose -f docker-compose-basic-R-support.yml up -d
```

## Using R in component code

To test rpy2 you may write a component importing it (`import rpy2`) and verify that the component can be run. For example here is the code for a small component outputting the value of Pi from R:

```python
from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType
# add your own imports here, e.g.
#     import pandas as pd
#     import numpy as np
import rpy2.robjects as robjects

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
@register(
    inputs={},
    outputs={"value_of_pi": DataType.Float},
    component_name="Test R Support",
    description="New created component",
    category="Draft"
)
def main():
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    pi = robjects.r['pi']
    return {"value_of_pi": pi[0]}
```

You may also import and use the installed R package "TDA" in your code using

```python
import rpy2.robjects.packages as rpackages
tda = rpackages.importr('TDA')
...
```

For further details on using R from Python you should read the [rpy2 manual](https://rpy2.github.io/doc/v2.9.x/html/introduction.html).

