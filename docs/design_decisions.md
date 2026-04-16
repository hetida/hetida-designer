---
icon: lucide/scale
---

# Design Decisions

The rationale for the described design decisions on this page assumes familiarity with the [basic concepts](./user_guide/tutorials/basic_concepts.md).

## Basic Architecture

* backend manages code components and workflows
* actual execution happens in runtime
* frontend, backend and runtime containerized
    * typically only runtime needs scaling
* separation of analytics from data provisioning via adapter system
* other systems / services trigger executions via backend

![Basic architecture overview](../diagrams/basic-architecture-overview.excalidraw.svg)
 
!!! tip "Combined Backend+Runtime"
    Backend and runtime can be run combined as a single container from the same image to support secarios like exposing a fixed set of workflows (e.g. a single workflow) as a separate [restricted webservice](./integration_guide/trafo_exec_guide/restricted_webservice.md).

!!! abstract "Runtime Variants / Claim Based Routing"
    Multiple runtime deployments, each with its own runtime image / dependency set / environment variables and separately scaled can coexist with the backend doing [claim based routing](./deployment_operation/varying_runtime_services.md) (i.e. using role from access token) to decide which one to invoke.

## Execution Process

### Rationale

Workflow engines provide modularity and reusability, which makes them attractive for general automation but also data science. However, deploying them in production, especially for automated pipelines and scalability, requires careful thought about how execution is technically handled. The following points are worth considering, in particular with respect to doing data science and machine learning:

**Process management**

- Is a new process started for each execution request, and/or for each step within a workflow?

**Dependency management**

- Is the dependency set (Python virtual environment) fixed across the entire runtime, or can it vary per execution, per workflow or per step?
- In a scaled setup where each worker process (and possibly execution process or even step execution process) in each container must fetch and import dependencies on startup, what is the impact on memory footprint and latency?

**Data handling**

- At what points is data serialized and deserialized?
- How is data that arrives as part of the execution request itself handled?
- How does this affect large in-memory datasets which are typical in data science workloads?

**Additional concerns**

- How are I/O-bound tasks (remote data ingestion, result delivery) managed asynchronously?
- What degree of sandboxing, isolation, and security is provided?

---

### hetida designer's Approach

hetida designer is built for **scalable production data science**. This requires minimizing worker process memory footprint, serialization overhead, and startup latency. The goal is that workflow step execution adds zero overhead compared to a direct function call.

hetida designer is not a general business automation engine, it specifically targets conscientious and responsible data scienctists and Python capable domain experts. "inter-execution" isolation / sandboxing is decidedly not a primary goal.

Therefore hetida designer makes the following deliberate and opinionated trade-offs:

**Same-process execution** The entire execution of a workflow run happens within the same process that handles the execution request in the runtime. No extra processes are spawned at start of execution or between steps, and Python objects are passed directly — no intermediate serialization or deserialization. The trade-off is that there is no process-level sandboxing or isolation: Neither between concurrent or even subsequent executions nor between different workflows, components or operators. See [security hints](./deployment_operation/security_hints.md) for details. The runtime containerization is the only isolation.

**Fixed dependency set per runtime image** Dependencies are baked into the runtime container image. This means no virtual environment needs to be built at startup or execution time, and imports are available immediately and can be reused across requests handled by the same runtime instance in the same worker process.

- *No on-the-fly dependency addition*: Adding a new dependency [becomes a DevOps task](./deployment_operation/managing_python_dependencies.md) rather than something a user can do himself / in the UI. This is intentional: In production systems, ad-hoc dependency changes are undesirable among others for security reasons and hetida designer is explicitly designed for production use.
- _Varying Dependencies:_ Different [Runtime Variants](./deployment_operation/varying_runtime_services.md) can provide different dependency sets when needed.

**Workflow DAG operator execution is sync**, i.e. different operators of a workflow are not executed in parallel even if that was possible. Since hetida designer separates analytics from data provisioning through its adapter system, it can be assumed that the workflow itself primarily executes CPU-bound code. On the other side adapter data fetching/sending is typically io bound and uses Python's asyncio capabilities to load data for data sources in parallel (per adapter) if supported by the adapter (e.g. the builtin [component adapter](./integration_guide/adapter_system/builtin_adapters/component_adapter.md)).


## Coding Scope

Data Scientists and in particular Python-capable subject matter experts are not professional software developers. Experience shows that often it is not the best idea to

* let them write arbitrarily complex/nested code
* let them write code for data ingestion / data engineering tasks etc.
* let them write technical code (REST APIs, ...)

hetida designer in its UI deliberately limits code to [components](./user_guide/tutorials/basic_concepts.md#component-component-revision) representing a single Python module with one exposed main function, i.e. relatively small and reasonably maintainable portions of code. The goal is to encourage writing of reusable "do one thing and do it well" components.

That said, bringing in larger and more interconnected code like a whole package or library is of course possible. On the one side this can be done by adding it as an additional runtime [dependency](./deployment_operation/managing_python_dependencies.md). On the other side the need for this can often be mitigated by [importing from other components](./user_guide/component_writing/component_import.md).