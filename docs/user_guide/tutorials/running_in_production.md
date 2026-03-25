# Running Transformations in Production

It is one of the main goals of hetida designer to make it easy to run transformations in production scenarios. That is to make the transition from experimenting/development to production usage smooth.

There are several mechanisms that contribute to reaching this goal:

* The revision system: trafos have revisions and a "released" trafo revision cannot be changed anymore. This makes production usage replicable.

* The adapter system allowing to simply swap adapters in a "wiring" data structure from using local test data (e.g. csv files) to remote production data (e.g. a database).

* The fact that execution of each trafo revision is immediately available through a [web service endpoint](../../execution/running_transformation_revisions.md) – there is **no extra deployment step necessary**.
  
* Note that a Kafka consumer for the same pupose is also built into the backend and can be activated and configured via environment variables of the designer backend (see [documentation](../../execution/execution_via_kafka.md)). Furthermore a [Kafka Consumption mode](../../execution/kafka_consumption_mode.md) can trigger execution on incoming data and the [Kafka Adapter](../../adapter_system/kafka_adapter.md) can distribute output data into Kafka streams.

Read more about how to handle and write wirings and how to use the execution endpoints [here](../../execution/running_transformation_revisions.md).

## Production Setup
We recommend a [kubernetes setup](../advanced_topics/kubernetes.md).

## Authentication
See the [authentication documentation](../../enabling_openidconnect_auth.md).

## Security
See [security hints in the README](../../../README.md#security-hints) for some basic security tips.

## Options for triggering executions
As mentioned above the options for triggering trafo executions are 
* [API](../../execution/running_transformation_revisions.md) (also see [Execution, Wirings, Adapters tutorial](./exec_wirings_adapters.md))
* Kafka:
    * [Kafka Execution](../../execution/execution_via_kafka.md)
    * [Kafka Consumption mode](../../execution/kafka_consumption_mode.md)


## Scheduling and automation
hetida designer comes with a simple cron-expression based built-in [scheduling](../../execution/scheduling.md). However, ultimately, hetida designer is not a job engine / scheduler / orchestrator and this task is typically handled by other components of the overall data platform of which hetida designer is the analytics engine.

This typically involves templating / creating wirings for each execution.

## Monitoring
hetida designer logs [contain job ids](../../execution/logging.md) to track execution jobs across services.

We recommend to monitor and manage pod resource usage as well as execution log messages, the later through logging.

For log analysis and observability we recommend general monitoring and observability solutions. Opentelemtry support is planned for a future version of hetida designer.

## Resource usage and scaling
See the [Scaling documentation](../../execution/scaling.md).

## Reproducibility
Reproducibilty depends on many things. Please read [Reproducibility pitfalls](../../repr_pitfalls.md) for a more in-depth discussion.

## Persisting and managing of trained models
There is a guide on [object / model persistence](../../persisting_models.md) that is a good starting point.

## Maintenance, backup etc.
See the [maintenance overview](../../maintenance.md)

## Managing transformation revisions between environments and local development
See [sync](../../sync.md)

This includes
* syncing between local development and hetida designer
* syncing between instances (e.g. dev, test, prod) via git repos.