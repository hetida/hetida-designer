# hetida designer REST API

The hetida designer backend and hetida designer runtime offer a comprehensive REST API.

Besides the endpoints necessary for the frontend it includes routes for execution of transformations by external services, maintenance, dashboarding and the builtin scheduling as well as builtin adapters.

Which endpoints are available depends on the role of the running service (backend, runtime, combined).

The API is documented via the [openapi.json](https://github.com/hetida/hetida-designer/blob/release/runtime/openapi.json) file. We recommend to display it with an appropritae openapi viewer application.