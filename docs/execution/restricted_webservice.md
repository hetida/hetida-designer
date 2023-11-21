# Separate pure execution service per transformation(s)

Setting the environment variable `HD_RESTRICT_TO_TRAFO_EXEC_SERVICE` to a non-empty json array of UUIDs restricts the web service to only offer the backend's transformation execution endpoint (`/api/transformations/execute`). I.e. no other backend endpoints or runtime endpoints (except an info endpoint) are available. Furthermore only the transformations with the configured UUIDs are allowed for execution.

This enables to offer execution of one or more transformation revisions
* as a separately scalable service
* to 3rd parties / other services without publishing all backend and runtime capabilities

Another use case is employing a hetida designer workflow and an adapter for data ingestion: The workflow may do some necessary data cleanup / preparation and its output is wired to a configured adapter. The resulting webservice can be exposed separately to data pushing services. Note that the service still needs to load the workflow from the database on each invocation (currently no caching is implemented) — so this is a viable solution for low and moderate data ingestion amounts and frequencies.

Using this you probably want to to let both `HD_IS_BACKEND` and `HD_IS_RUNTIME` remain true — especially the later enables actual execution in the same container.

A typical setup consists of
* An ordinary designer backend and runtime only reachable internally by your data scientists for exploration and development
* Some production ready (RELEASED) workflows running via this mode as separate containers / services which then are configured to be reachable by relevant other services, even across the open internet if necessary with authentication enabled of course!.