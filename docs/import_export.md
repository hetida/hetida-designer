# Export and Import of Components/Workflows

Components and Workflows can be exported and imported via the backend API endpoints. To make that easier, scripts are available that can be run from the runtime Docker image. This can be used to keep local file copies as backup or to get components/workflows from one designer installation to another.

This guide assumes the default docker-compose setup described in the project README.

## Exporting all components and workflows

First you should do a complete database backup as is described in [backup](./backup.md), just in case something bad happens.

Then go to a directory where you want to store the exported components and workflows.
Now run 

```shell
docker run --rm \
  -e "HETIDA_DESIGNER_BACKEND_API_URL=http://hetida-designer-backend:8090/api/" \
  --name htdruntime_export \
  --mount type=bind,source="$(pwd)",target=/mnt/obj_repo \
  --network hetida-designer-network \
  --entrypoint python \
  hetida/designer-runtime:0.7.0 -c 'from hetdesrun.exportimport.export import export_all; export_all("/mnt/obj_repo/exported_data/");'
```

The command will create a subdirectory `exported_data` in your current directory with subfolders `components` and `workflows` each of which contains subfolders corresponding to the categories in which the components and workflows are stored in individual json files.

## Importing all components and workflows

> :warning: IMPORTANT: If you have existing workflows/components in your installation you should do a complete database backup as is described in [backup](./backup.md), just in case something bad happens!

Simply run the following command to import the exported components and workflows from the same directory:

```shell
docker run --rm \
  -e "HETIDA_DESIGNER_BACKEND_API_URL=http://hetida-designer-backend:8090/api/" \
  --name htdruntime_import \
  --mount type=bind,source="$(pwd)",target=/mnt/obj_repo \
  --network hetida-designer-network \
  --entrypoint python \
  hetida/designer-runtime:0.7.0 -c 'from hetdesrun.exportimport.importing import import_all; import_all("/mnt/obj_repo/exported_data/");'
```

## Importing components from single python files

It is also possible to import components from *single* python files. In order to use this feature, a component needs to be saved as a python file having *exactly* the following structure, shown for the base component `Add (1.0.0)`. 

```python
"""

# Add

## Description
This component adds numeric values, Pandas Series and Pandas DataFrames.

## Inputs
* **a** (Integer, Float, Pandas Series or Pandas DataFrame): First summand, entries must be numeric.
* **b** (Integer, Float, Pandas Series or Pandas DataFrame): Second summand, entries must be numeric.

## Outputs
* **sum** (Integer, Float, Pandas Series or Pandas DataFrame): The sum of summand a and summand b. 

## Details
The component adds the inputs. 
"""
from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType

import pandas as pd

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
@register(
    inputs={"a": DataType.Any, "b": DataType.Any},
    outputs={"sum": DataType.Any},
    component_name="Add",
    description="Add inputs",
    category="Basic Arithmetic",
    uuid="2abf72f6-68c9-7398-7175-165d31b3ced7",
    group_id="2abf72f6-68c9-7398-7175-165d31b3ced7",
    tag="1.0.0"
)
def main(*, a, b):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    return {"sum": (a + b)}
```

The file begins with the *documentation* of the component in docstring format. Following docstring conventions, it is necessary to start with the component name in the *second* line. Underneath, there is the complete python code of the *component* itself. As an advantage, one is now able to change details in the documentation and component code, i.e., one might add examples to the documentation or change the component description and category, before importing the component on the local designer installation. On the other hand, the file does not include important information about *wirings* of the component, for example.

Now, go to the `runtime` directory and create a subdirectory named `components_in_python_files`, for example, where you put the python files of possibly many components, safed in the above presented format. Last, simply run the following command from the `runtime` directory to import the components:

```shell
docker run --rm \
  -e "HETIDA_DESIGNER_BACKEND_API_URL=http://hetida-designer-backend:8090/api/" \
  --name htdruntime_import \
  --mount type=bind,source="$(pwd)",target=/mnt/obj_repo \
  --network hetida-designer-network \
  --entrypoint python \
  hetida/designer-runtime:0.7.0 -c 'from hetdesrun.exportimport.importing import import_all; import_all("/mnt/obj_repo/components_in_python_files/");'
```

