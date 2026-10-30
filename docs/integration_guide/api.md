# hetida designer REST API

The hetida designer backend and hetida designer runtime offer a comprehensive REST API.

Besides the endpoints necessary for the frontend it includes routes for execution of transformations by external services, maintenance, dashboarding and the builtin scheduling as well as builtin adapters.

Which endpoints are available depends on the role of the running service (backend, runtime, combined) and on its configuration. For example the [maintenance](../deployment_operation/maintenance/index.md) endpoints are only active if a maintenance secret is configured and the [BLOB storage adapter](./adapter_system/builtin_adapters/blob_storage_adapter.md) endpoints only if its hierarchy is configured.

The API is documented via the [openapi.json](https://github.com/hetida/hetida-designer/blob/release/runtime/openapi.json) file. It contains all endpoints, including those which are deactivated by default. We recommend to display it with an appropriate openapi viewer application.

The openapi.json also specifies the [metadata conventions](../user_guide/attached_metadata.md#specification-and-validation) for timeseries data as component schemas `SeriesMetadata`, `SingleTSFrameMetadata` and `MultiTSFrameMetadata`, which document the metadata in the request body of the endpoint `POST /api/metadata-conventions/check/{data_type}` for checking metadata. This way the metadata conventions are versioned together with the API and third party projects like adapters can validate metadata against them.

[View API Online via Swagger Editor](https://editor.swagger.io/?url=https://raw.githubusercontent.com/hetida/hetida-designer/refs/heads/release/runtime/openapi.json)