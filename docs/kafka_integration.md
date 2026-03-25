# Kafka Integration

[Apache Kafka](https://de.wikipedia.org/wiki/Apache_Kafka) is integrated in hetida designer both event-based execution, receiving and sending data to Kafka topics as well as the combined variant, i.e. a topic provides data and triggers a fixed workflow / component execution with this data as input.

* [Execution via Kafka](./execution/execution_via_kafka.md) — A consumer that executes transformations were trafo and wiring are specified in the message payload. This allows to trigger arbitrary trafo execution via a Kafka topic and is the equivalent to the REST API execution endpoints.
* [Kafka adapter](./adapter_system/kafka_adapter.md) — (receiving) and sending data from/to Kafka topics. This is mostly used for sending data to Kafka topics.
* [Kafka consumption mode](./execution/kafka_consumption_mode.md) — A Kafka consumer that runs a preconfigured (fixed) transformation with a preconfigured wiring where data for one or more inputs comes from the message payload.
