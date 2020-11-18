# Load an Object from the object Repository

## Description
Serialize an Object and store it in the object Repository.

## Inputs
* **name** (String): The name for the Object.
* **tag** (String): The tag for the Object.

## Outputs
* **obt** (Integer, Float, Pandas Series or Pandas DataFrame): The object to load. 

# Load an Object from the object Repository

Hetida Designer comes with a simple object store to allow serialization and persistence of Python objects between Workflows and Workflow Executions. A typical use case is storing of a trained machine learning model in a training workflow and loading it in a prediction workflow.

Technically joblib is used for serialization in order to efficiently store numpy arrays and Pandas objects.

The serialized object is stored using the name and a tag. It can be retrieved using the same name and tag combination. Additionally there is a magic "latest" tag which retrieves the last stored object with that name.
