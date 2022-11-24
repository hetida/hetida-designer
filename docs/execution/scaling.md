# Some notes on scaling hetida designer

Typical production scenarios involving hetida designer include regular and/or event-triggered execution of workflows and this "scaled" to some extend. For example an anomaly detection workflow may be triggered hourly for several thousand plants.

Depending on how much data is involved and how compute-intensive each execution is, this requires a suitable IT infrastructure, e.g. a cluster and the corresponding scaled setup.

Of course it is impossible to describe all reasonable such setups here. The intention of this page is to rather provide some general hints and give some guidance which apply to the most typical scenarios.

## Scaling hetida designer on a k8s cluster
hetida designer consists of interacting (micro)services and is meant to be scaled via a kubernetes (k8s) cluster. 

The default docker-compose setup described via the docker-compose.yml file includes separate services for backend and runtime. This is also the recommended setup for scaling on a k8s cluster since it allows to scale the runtime separately. Typically only the runtime service needs to be scaled since most IO (loading and sending data from adapters) and computation heavy operations happen there.

> Typically you only need to scale the runtime service

### Understanding how the runtime service works?

The runtime service starts worker processes via Gunicorn which then wait/listen for execution requests from the backend. By default one such process is started for each available CPU core. This can be controlled by the `WORKERS_PER_CORE` and `MAX_WORKERS` environment variables, see the `gunicorn_conf.py` file in the runtime subdirectory of this repository. Make sure to read the respective [gunicorn documentation](https://docs.gunicorn.org/en/stable/design.html#how-many-workers). Note that Gunicorn uses "OS level load balancing" to assign requests to worker processes.

Now these worker processes handle requests asynchronously (via Python's asyncio capabilities) and they run Python code in one thread on one CPU if no GIL-releasing system/library code (e.g. from numpy) is involved.

If GIL-releasing code is involved (which typically happens in Data Science code), all available CPUs can be used. Note that this means that a container running the runtime with MAX_WORKERS=1 can stil access all the underlying nodes' CPUs by default if no limits are enforced. Thus a computation-heavy workflow can completely consume all available CPU resources on a k8s node. More often this is desired because it increases workflow execution speed. Sometimes this is regarded as detrimental in particular if other services run on the same node.

### Scaling vertically and horizontally

In particular one runtime container per cluster node, even with `MAX_WORKERS=1` via GIL-releasing code, can be enough to make good use of available CPU resources. Generally 

> scaling vertically, i.e. increasing available CPU / memory on nodes running runtime containers is a viable, valid and recommended scaling approach!


For horizontal scaling the following patterns have proven their worth:

1. One runtime container per node with default settings (i.e. one worker per node cpu).
2. One runtime container per node with `MAX_WORKERS=1`.
3. One runtime container per cpu core on each node with `MAX_WORKERS=1`. For example if you have 3 cluster nodes with each 4 cpu cores you should employ 12 runtime replicas.


The first pattern is a good allround setup and a good start if you do not yet know the specifics of your workloads. It has the disadvantage that the two load balancing methods involved, i.e. the kubernetes inter-service http "load balancing" and Gunicorn's "OS-level load balancing", may lead to non-optimal distribution to workers as described below.

The second pattern is strong if your workloads are CPU-heavy and do release the GIL and in particular if you have enough nodes available and know in advance how many parallel executions might occur. It prioritizes kubernetes inter-service load balancing which leads to a good distribution of controlled amounts of tasks.

The third pattern excels if your workloads do not release the GIL and you need to run many of them in parallel. Like the second pattern it prioritizes kubernetes inter-service load balancing which leads to a good distribution of controlled amounts of tasks.

> Generally you should try the horizontal scaling patterns above, see what works best for your workloads and adapt from there.

### Use separate computation nodes!

Since the data science code executed by the runtime is often CPU-heavy, running runtime instances and other service instances on the same cluster node is usually not a good idea. Other services may not get enough CPU resources when running runtime workloads and if you reserve CPU resources for them you have to limit the runtime CPU resources, usually by a fixed amount, leading to non-optimal CPU usage. Consequently

> You should employ reserved "runtime" nodes. I.e. cluister nodes equipped with appropriate (i.e. high) CPU and memory resources in your cluster on which only runtime pods can be run.

In k8s this can be achieved via node selectors or the node taint mechanism.

> For an efficient, low-effort load balancing it is also recommended to equip these "runtime" nodes with equal resources, i.e. give them all the same amount of CPU cores and memory.

### Understanding the impact of load-balancing mechanisms

By default, on a k8s cluster, inter-service "load balancing" is quite simple: requests to a service are distributed evenly and immediately to the available replicas, without consideration of available resources, current state and without any knowledge on job-individual resource needs. In particular this applies to workflow executions issued by the hetida designer backend to the runtime service.

When doing many requests in parallel, the frequent effect is that some "workers" finish their assigned tasks long before others which just happen to live on a heavier-used cluster node or get less resources from the OS. So at the beginning lots of jobs are run in parallel but later the "slow" workers run their remaining jobs one after another while the fast workers are idle.

This non-optimal distribution in particular happens when both "load balancing" methods, i.e. the inter-service distribution of requests on k8s and the "OS-level" load balancing to the worker processes used by Gunicorn are active.

> If you are affected by this "remaining slow worker" problem we recommend to switch to horizontal scaling pattern 2 or 3 in order to reduce the amount of "moving parts" involved in distributing load.

### Distribute scheduling over time

Additionally it is recommended to 

> distribute scheduled executions over time instead of sending all jobs at once. For example, instead of starting all hourly jobs at xx:00, distribute them evenly over each hour. 

This allows gunicorn to assign requests to the worker processes that are idle. And it allows more sphisticated inter-service load balancing to take current load better into account, see below.

### Inter-service load balancing
An ideal solution would be to

> use an intelligent inter-service load balancer between backend and runtime which ideally takes current and expected load into consideration, has some knowledge about job resource needs and maybe even queues request to decide later, where to distribute them to.

For example an intelligent load balancer could analyze execution requests and learn from past executions which workflows take a long time to run. Or it could make use of prior knowledge from model registering / experiment management processes. 

Of course this is a highliy-customized load balancing strategy, so at the end this would require to write your own individual load balancing service.

Depending on your scenario It may also be sufficient to just employ a simple load balancer incorporating the "least connection" strategy, for example using an extra[nginx](https://docs.nginx.com/nginx/admin-guide/load-balancer/http-load-balancer/) service or kube-proxy in [IPVS-proxy mode](https://kubernetes.io/docs/concepts/services-networking/service/#proxy-mode-ipvs).

### Understanding async execution and IO behaviour
As mentioned above, the hetida designer runtime runs workflows inside the default async event loop of a worker process. During workflow execution, between each operator execution, control is given back to the event loop, allowing other tasks to gain control. Furthermore operator entry point functions can be async and consequently even inside code execution control can switch to other tasks on the event loop.

So workflow and operator execution might switch in-between to other IO tasks, like loading data from an adapter for another workflow execution on the same worker process. I.e. IO for another workflow execution can increase total workflow execution time. The runtime has no priority for actual workflow / operator code execution over adapter IO or vice versa. For example it does not prioritize finishing a running further-progressed workflow execution job over initial loading data for the next one. The runtime is in a sense "neutral".

### Scaling IO

If a lot of IO happens due to many data-intensive workflows being started parallely, this may delay execution completion despite the fact that the actual code execution of each operator is fast. And vice versa a computation intensive workflow blocks other execution jobs assigned to the same worker process.

If you observe these things happening it may be a good moment to consider horizontal scaling and applying one of the above-mentioned load balancing / scheduling approaches.

> In particular if you see IO increasing total execution times a lot, you need to also scale the adapter services and their persistence backends accordingly, since this probably is the bottleneck.

At the end data can only be processed as fast as it can be loaded and sent. In practise, employing scalable databases can be necessary for your workloads.