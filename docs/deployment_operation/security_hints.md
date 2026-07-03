# Security Hints

Hetida designer allows to execute arbitrary Python code. The included plain execution engine executes workflows in the same processes that serve the runtime component (which typically run as a (non-root) process in a Docker container if you use the runtime docker image). There is no isolation / sandboxing both in-between operators of a workflow and different executions (of the same or different components/workflows).

This is intentional, since hetida designer has a focus on data science and therefore needs to avoid expensive serialisation/deserialisation of mass data as well as the overhead of loading resource-heavy data science libraries like pandas, scipy, etc. each time an execution is triggered. Note that here hetida designer significantly differs from more "business automation" - oriented workflow engines. See [design decisions](../design_decisions.md) for more details.

Knowing this, the following security measurements should at minimum be employed when working with the hetida designer:

* Never expose the frontend, the backend webservice, the database webservice to the public unauthenticated!
* Avoid exposing the runtime webservice directly to users at all. It should only be reachable by the backend.
* It is always strongly recommended to employ / activate authentification for frontend, backend, and runtime.
* **MOST IMPORTANT: You should trust your users of the designer to the same degree that you trust a professional software engineer of your organization who is authorized to develop, run, and deploy arbitrary code (in production if hetida designer has access to your production systems e.g. via adapters)**
* You should restrict resource access (memory, cpu, networking bandwidth etc) of the docker service / docker container of the runtime in order to limit DoS attacks.
* You should restrict the runtime container to only have configured the absolutely necessary secrets and permissions
* You should never solely rely on the isolation that is provided by running something in a Docker container. The container should be isolated from other systems as much as possible. It should be monitored continuously for suspicious activities.
* Depending on your security requirements, you should consider further isolation methods like deferring every workflow execution to a one-time container or doing the same on process level. Do not hesitate to ask questions or create a feature request on the issue tracker.
* **If you do not feel comfortable employing security measures yourself, do not hesitate to ask for help from professional security consultants.**