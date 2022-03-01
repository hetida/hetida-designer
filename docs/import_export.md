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
  hetida/designer-runtime -c 'from hetdesrun.exportimport.export import export_all; export_all("/mnt/obj_repo/exported_data/", True);'
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

When sharing components among different designer users, your colleagues might also be interested in changing the python code and documentation *before* importing on their local system. Now, suppose you created a component with corresponding documentation. In order for your colleagues to be able to first change the component details and then import it into their local designer installation using the implemented `import_all` functionality, create some python file having *exactly* the following structure, explained for the base component `Add (1.0.0)`. 

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

The file starts with the *documentation* of the component in docstring format. Following docstring conventions, it is necessary to start with the component name in the **second** line. Underneath, put the complete python code of the *component* itself. Then, you may safe the above code as some file named `add.py` on your local system and share it with your colleagues. 

Now, your colleague goes to the `runtime` directory and creates a subdirectory `components_from_python_code`, for example. Here, he saves the python file `add.py`, and possibly many more components in that format. Simply run the following command to import the components from the `runtime` directory:

```shell
docker run --rm \
  -e "HETIDA_DESIGNER_BACKEND_API_URL=http://hetida-designer-backend:8090/api/" \
  --name htdruntime_import \
  --mount type=bind,source="$(pwd)",target=/mnt/obj_repo \
  --network hetida-designer-network \
  --entrypoint python \
  hetida/designer-runtime:0.7.0 -c 'from hetdesrun.exportimport.importing import import_all; import_all("components_from_python_code/");'
```