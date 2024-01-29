# Reproducibility and Deserialization pitfalls

This note discusses some pitfalls concerning reproducibility and serialization (e.g. see [persisting models](./persisting_models.md)) in combination with some maintenance actions. See below for advice on how to avoid / handle them.

**Reproducibility**: Running the same (released!) workflow or component with the exact same wiring with adapters guaranteeing deterministic data ingestion should produce the exact same result.

**Deserialization**: A serialized Python object, for example a trained model, should be deserializable, for example in an inference workflow, at a later time.

Both these depend on a number of things
* Python environment must be identical:
    * Python version must agree, at least the minor version part
    * Python dependency versions must agree exactly
    * All used component code must agree exactly. For deserialization to work the code modules must be available under the exact same module import path as during serialization.
* For reproducibility the component code must be deterministic. 

Component code is imported in the hetida designer runtime at an import path that uses a hash of the component code. This means if anything in the code changes, deserialization probably does not work anymore. For released components the code is fixed.

> You should always **use relased components** or workflows when serializing objects or when you want to run something in a reproducible way, for example in production.

Note that it may take some time to observe a failure due to the [typical deployment setup](./execution/scaling.md) of hetida designer: The runtime which actually runs Python code may be replicated, i.e. multiple containers run and are selected by some sort of load balancing. A request may trigger a container that still has the old code in memory or it may trigger one where it is not available anymore. The same applies to the case of multiple server processes inside the same container.

Now even when using released components reproducibility and deserialization may be affected by maintenance operations on your hetida designer instances:

* Updating hetida designer: 
    * New docker image versions may introduce a new Python version or updated dependencies
    * hetida designer code changes may affect how code is executed
* Sending components to a hetida designer instance using an action that overwrites released transformation revisions. For example by activating the `allow_overwrite_released` flags during [import](./import_export.md), [autoimport](./autoimport.md) or via some of the [hdctl](./maintenance.md) maintenance actions.
    * **WARNING**: Note that overwriting a released transformation with a version which has a different input / output interface may render workflows that use this transformation as an operator unusable. `allow_overwrite_released` must be used with caution! You should prefer to create new revisions over overwriting.
* Importing transformations that were previously exported with a flag that leads to changed component code: For example the `update_component_code` or the `expand_component_code` parameter of the `/api/transformations` GET endpoint.
* A typical situation for the last two points is transferring transformations between instances. For example from a dev to a staging / test instance or a production instance.
* Restoring a [backup](./backup.md) may overwrite existing components with older code.

> After doing such a maintenance operation you should expect deserialization to fail! **You may need to re-train and serialize new versions of each persisted model after maintenance operations**. 

> Do not expect reproducibility of executions with a maintenance operation between them.

Note that none of the maintenance operations above can be triggered directly from the hetida designer web user interface. As long as you only interact with hetida designer's frontend you are safe.

Nevertheless such maintenance operations are of course necessary from time to time.

However one should note that for example the `update_component_code` or the `expand_component_code` parameters for syncing / exporting should be considered safe for reproducibility. Your component code should not depend semantically on the things changed by them.

Sometimes even overwriting released components with `allow_overwrite_released` set to true during import is okay, if only minor stylistic code changes or bug fixes are introduced.