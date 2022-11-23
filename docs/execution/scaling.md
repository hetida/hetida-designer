# Some notes on scaling hetida designer

Typical production scenarios involving hetida designer include regular and/or event-triggered execution of workflows and this "scaled" to some extend. For example an anomaly detection workflow may be triggered hourly for several thousand plants.

Depending on how much data is involved and how compute-intensive each execution is, this requires a suitable IT infrastructure, e.g. a cluster and a corresponding scaled setup.

Of course it is impossible to describe all possible setups here. The intention of this page is to rather provide some general hints which apply to the most typical scenarios.

The elemantary assumption here is that hetida designer is run on a kubernetes (k8s) cluster. hetida designer is meant to be scaled via a kubernetes cluster.

## Scaling hetida designer on a k8s cluster
The default setup described via the docker-compose.yml file includes separate services for backend and runtime. This is also the recommended setup for scaling on a k8s cluster since it allows to scale the runtime separately. Typically only the runtime service needs to be scaled since all IO (loading and sending data from adapters) and computation heavy operations happen there.

> Typically you only need to scale the runtime service

The runtime service starts processes waiting/listening for execution requests from the backend. By default one such process is started for each available CPU. This can be controlled by the `WORKERS_PER_CORE` and `MAX_WORKERS` environment variables, see the `gunicorn_conf.py` file in the  runtime subdirectory of this repository. Make sure to read the respective [gunicorn documentation](https://docs.gunicorn.org/en/stable/design.html#how-many-workers). Gunicorn uses "OS level load balancing" to assign requests to worker processes.

These processes handle requests asynchronously and they run Python code in one thread on one CPU if no GIL-releasing system/library code (e.g. from numpy) is involved. If such GIL-releasing code is involved all available CPUs can be used.

### Scaling vertically versus horizontally

In particular one runtime container per cluster node will be enough to make good use of available CPU resources. Consequently,

> scaling vertically, i.e. increasing available CPU / memory on nodes running runtime containers is a viable, valid and recommended scaling approach,

and

> for horizontal scaling, typically only one runtime container should be started on a cluster node.

### Understanding the impact of K8s naive inter-service load-balancing

By default, on a k8s cluster, inter-service "load balancing" is quite simple: requests to a service are distributed evenly and immediately to the available replicas, without consideration of available resources, current state and without any knowledge on job-individual resource needs. In particular this applies to workflow executions issued by the hetida designer backend to the runtime service.

When doing many requests in parallel, the frequent effect is that some "workers" finish their assigned tasks long before others which just happen to live on a heavier-used cluster node or get less resources from the OS. So at the beginning lots of jobs are run in parallel and at the end the "slow" workers run their remaining jobs one after another while the fast workers are idle. This is of course not an optimal distribution.

One easy way to slightly mitigate this is to

> distribute runtime replicas across nodes which have the same resources available and no other services running, i.e. reserve distinguished "runtime" nodes in your cluster (i.e. use node selectors / node taints)

### Intelligent Scheduling

Additionally it is recommended to 

> distribute scheduled executions over time instead of sending all jobs at once. For example, instead of starting all hourly jobs at xx:00, distribute them evenly over each hour. 

This allows gunicorn to assign requests to the worker processes that are idle.

### Inter-service load balancing
An ideal solution would be to

> use an intelligent inter-service load balancer between backend and runtime which ideally takes current and expected load into consideration, has some knowledge about job resource needs and maybe even queues request to decide later, where to distribute them to.

For example an intelligent load balancer could analyze execution requests and learn from past executions which workflows take a long time to run. Or it could make use of prior knowledge from model registering / experiment management processes. Of course this is a highliy-customized load balancing strategy, so at the end this would require to write an individual load balancing service.

Depending on your scenario It may also be sufficient to just employ a simple load balancer incorporating the "least connection" strategy, for example using [nginx](https://docs.nginx.com/nginx/admin-guide/load-balancer/http-load-balancer/).

### Understanding async execution and IO behaviour
As mentioned above, the hetida designer runtime runs workflows inside the default async event loop. During workflow execution, between each operator execution, control is given back to the event loop, allowing other tasks to gain control. Furthermore operator entry point functions can be async and consequently even inside code execution control can switch to other tasks on the event loop.

So workflow and operator execution might switch in-between to other IO tasks, like loading data from an adapter for another workflow execution on the same worker process. I.e. IO for another workflow execution can increase total workflow execution time. The runtime has no priority for actual workflow / operator code execution over adapter IO or vice versa. For example it does not prioritize finishing a running further-progressed workflow execution job over initial loading data for the next one. The runtime is in a sense "neutral".

If a lot of IO happens due to many data-intensive workflows being started parallely, this may delay execution completion despite the fact that the actual code execution of each operator is fast. And vice versa a computation intensive workflow blocks other execution jobs assigned to the same worker process.

If you observe these things happening it may be a good moment to consider scaling and applying one of the above-mentioned load balancing / scheduling approaches.

In particular if you see IO increasing total execution times a lot, you need to also scale the used adapter services accordingly, since this probably is a bottleneck.