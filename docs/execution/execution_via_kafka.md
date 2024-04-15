# Execution via Apache Kafka

The hetida designer backend can offer transformation (i.e. workflow / component) execution via [Kafka](https://kafka.apache.org/) as part of the backend service. This is basically the same functionality which the API transformation revision execution endpoint (`/api/transformations/execute`) offers — the triggering Kafka message has the same json payload schema and a response with the same response schema as the API endpoint is sent to another "result" topic.

This *execution via Kafka* is not to be confused with the [Kafka consumption mode](./kafka_consumption_mode.md) offered by the [Kafka adapter](../adapter_system/kafka_adapter.md). It expects a complete execution request as Kafka message payload (with arbitrary trafo id, wiring, etc.). While this payload can contain input data in the form of wirings to the `direct_provisioning` adapter (see [adapter system intro](./intro.md) and [manual input](./manual_input.md)) and its response can similarly send data via `direct_provisioning` to the result topic, its main use case is event-based execution job triggering.

In contrast the [Kafka consumption mode](./kafka_consumption_mode.md) is tied to a preconfigured transformation and wiring and is more appropriate for streaming use cases in that it allows to consume and produce on the level of individual transformation inputs/outputs.


## Configuration of Kafka execution

The backend service execution Kafka consumer needs to be activated and needs to be configured against the actual Kafka cluster. Besides consumer options a producer must be configured for the execution request response messages.

All this can be done by setting environment variables for the backend service. Example:
```
HETIDA_DESIGNER_KAFKA_ENABLED=true
HETIDA_DESIGNER_KAFKA_CONSUMER_TOPIC="hd-execution-topic"
HETIDA_DESIGNER_KAFKA_CONSUMER_OPTIONS='{"bootstrap_servers": "localhost:9094", "group_id": "hd_kafka_consumer_group"}'
HETIDA_DESIGNER_KAFKA_RESPONSE_TOPIC="hd-execution-response-topic"
HETIDA_DESIGNER_KAFKA_PRODUCER_OPTIONS='{"bootstrap_servers": "localhost:9094"}'
```

Notes:
* Here the Kafka cluster is expected to be reachable at `localhost:9094`.
* `HETIDA_DESIGNER_KAFKA_CONSUMER_OPTIONS` and `HETIDA_DESIGNER_KAFKA_PRODUCER_OPTIONS` can be set to everything that is available for [aiokafka](https://aiokafka.readthedocs.io/en/stable/) consumers / producers.
* Note that not all combinations of options will work / make sense. For example the built-in consumer expects autocommit being set to true.
* Moreover a consumer group id is expected to be set.
* To actually make use of all these consumer instances for scaling, the corresponding topic in your Kafka cluster should be configured to have at least as many partitions as the designer backend instances hav worker processes with activa Kafka execution consumer.

## Usage
Send a valid execution request (same json payload as the `/api/transformations/execute` API endpoint) as a message to the topic configured via `HETIDA_DESIGNER_KAFKA_CONSUMER_TOPIC`. 

The execution response will be sent to the topic configured via `HETIDA_DESIGNER_KAFKA_RESPONSE_TOPIC` and will have the same json structure as the `/api/transformations/execute` API endpoint response.

We refer to the backend interactive OpenAPI documentation (Available at http://localhost:8080/docs when running the docker compose setup) of the `/api/transformations/execute` API endpoint for details.

Alternatively you can also send an execution request in the format of the `/api/transformations/execute-latest` API endpoint to execute the latest released transformation of a transformation revision group.

## Technical details on the Kafka execution consumer and scaling
The Kafka execution consumer (and producer for sending results) runs in the backend web service application: One consumer / producer pair is initialized per gunicorn/uvicorn worker process. Consumers are part of a consumer group specified via configuration (see above). By default messages are distributed to topic partitions automatically using the key of the Kafka message. Therefore it makes sense to use something like a job name or job id as message key.

To actually make use of all these consumer instances for scaling, the corresponding topic in your Kafka cluster should be configured to have at least as many partitions as the designer backend has worker processes.

Note that running the analytical code actually happens in the runtime service (separately scalable). So a sensible setup is to have a one-replication backend service and a scaled-up (multi-replication) runtime service.