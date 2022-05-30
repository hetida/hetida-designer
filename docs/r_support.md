# R Support in hetida designer

hetida designer focuses on the Python data science stack and does not support writing components using R directly. However, it is possible to utilize [rpy2](https://rpy2.github.io/) to run R code from the Python code of a component.

This page describes a very basic setup example for this.

## Preparing your Setup

Create a a new file Dockerfile `Dockerfile-runtime-basic-R-support` containing for example (see https://cran.r-project.org/bin/linux/debian/#debian-buster-stable)

```dockerfile
FROM hetida/designer-runtime:0.7.2

USER root

RUN apt-get update

# Install R 4.X (see https://cran.r-project.org/bin/linux/debian/#debian-buster-stable)
RUN apt-get install -y build-essential cmake dirmngr apt-transport-https ca-certificates software-properties-common gnupg2 libcurl4-openssl-dev libxml2-dev libssl-dev
RUN echo "deb http://cloud.r-project.org/bin/linux/debian buster-cran40/" >>/etc/apt/sources.list
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-key B8F25A8A73EACF41
RUN apt-get update && apt update
RUN apt install -y -t buster-cran40 r-base r-base-dev
RUN R -e 'update.packages(lib.loc="/usr/local/lib/R/site-library", ask = FALSE, checkBuilt = TRUE, Ncpus = 8)'

# install some R package:
RUN Rscript -e 'install.packages(c("Matrix","quantreg","mclust","splines","textTinyR","MASS","zoo", "imputeTS", "anomalize", "tsrobprep"), repos="https://cloud.r-project.org", dependencies = TRUE)'

# install rpy2 to be able to use R from Python
RUN pip install rpy2

USER hd_app

```

This example installs R and rpy2 and some R packages like "anomalize".

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

You may also import and use the installed R package "anomalize" in your code using

```python
import rpy2.robjects.packages as rpackages
anomalize = rpackages.importr('anomalize')
...
```

For further details on using R from Python you should read the [rpy2 manual](https://rpy2.github.io/doc/v2.9.x/html/introduction.html).

