# Separate pure execution service per transformation(s)

Setting the environment variable `HD_RESTRICT_TO_TRAFO_EXEC_SERVICE` to a non-empty json array of UUIDs restricts the web service to only offer the backend's transformation execution endpoint (`/api/transformations/execute`). I.e. no other backend endpoints or runtime endpoints (except an info endpoint) are available. Furthermore only the transformations with the configured UUIDs are allowed for execution.

This enables to offer execution of one or more transformation revisions
* as a separately scalable service
* to 3rd parties / other services without publishing all backend and runtime capabilities

Using this you probably want to to let both `HD_IS_BACKEND` and `HD_IS_RUNTIME` remain true — especially the later enables actual execution in the same container.

A typical setup consists of
* An ordinary designer backend and runtime only reachable by your data scientists for exploration and development
* Production ready (RELEASED) workflows running via this mode as separate services which then are configured to be reachable by relevant other services, e.g. across the open internet (with authentication enabled of course!).