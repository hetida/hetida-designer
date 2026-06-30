# Running Transformations in Production

It is one of the main goals of hetida designer to make it easy to run transformations in production scenarios. That is to make the transition from experimenting/development to production usage smooth.

There are several mechanisms that contribute to reaching this goal:

- The revision system: trafos have revisions and a "RELEASED" trafo revision cannot be changed anymore. This makes production usage reproducible.

- The adapter system allowing to simply swap adapters in a "wiring" data structure from using test data (e.g. csv files) to production data (e.g. a database).

- The fact that execution of each trafo revision is immediately available through a [web service endpoint](../../execution/running_transformation_revisions.md) or via [Kafka](../../execution/execution_via_kafka.md) – there is **no extra deployment step necessary**.

This guide explains what you need to know to write software that triggers executions of transformation revisions in hetida designer. We assume familiarity with [basic concepts](../../user_guide/tutorials/basic_concepts.md) and [wiring basics](../../user_guide/tutorials/exec_wirings_adapters.md).

## Options for triggering executions

The main options for triggering trafo executions programmatically from other services are

- [API](./execution_via_api.md)
- Kafka:
  - [Kafka Execution](./execution_via_kafka.md)
  - [Kafka Consumption mode](./kafka_consumption_mode.md)
