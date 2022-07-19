# Execution via Apache Kafka

This document describes [Kafka](https://kafka.apache.org/) execution of workflow / component revisions. 

Naturally this depends strongly on the specific Kafka cluster setup. Of course, we cannot describe all possible scenarios here. Therefore we describe a docker-compose based demo setup, which should give you a good starting point for developing your individual setup.
## Setup

We save a copy of the `docker-compose-dev.yml` with the new name `docker-compose-kafka.yml`, modify the **hetida-designer-backend** service and add a **zookeeper** and a **kafka** service as follows:

```yaml
...

  hetida-designer-backend:
    ...
    environment:
      ...
      - HETIDA_DESIGNER_KAFKA_ENABLED=true
      ...
    ...
...

  zookeeper:
    image: zookeeper:3.7
    ports:
      - 2181:2181

  kafka:
    image: wurstmeister/kafka:2.13-2.8.1
    environment:
      KAFKA_ZOOKEEPER_CONNECT: "zookeeper:2181"
      KAFKA_CREATE_TOPICS: "hd-execution-topic:8:1,hd-execution-response-topic:8:1"      
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: 'false'
      KAFKA_BROKER_ID: -1
      KAFKA_LISTENERS: LISTENER_DOCKER_INTERNAL://:19092,LISTENER_DOCKER_EXTERNAL://:9092
      KAFKA_ADVERTISED_LISTENERS: LISTENER_DOCKER_INTERNAL://kafka:19092,LISTENER_DOCKER_EXTERNAL://localhost:9092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: LISTENER_DOCKER_INTERNAL:PLAINTEXT,LISTENER_DOCKER_EXTERNAL:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: LISTENER_DOCKER_INTERNAL
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    ports:
      - "9092:9092"
    depends_on:
      - zookeeper      

...

```

:warning: **Note:** This small Kafka setup using the "wurstmeister/kafka" image is only suitable for examples/demonstration and local development. We do not recommend it for production!

Now we can start this new setup via the following command (ensuring correct broker configuration, see https://stackoverflow.com/q/53571823).

:warning: **Warning:** The following command deletes existing component/workflow data / volumes!

```
docker-compose -f docker-compose-kafka.yml down --volumes && docker-compose -f docker-compose-kafka.yml up --force-recreate --build
```

We will demonstrate workflow execution via Kafka using one of the example workflows provided with the default component/workflow deployment. Thus, if you have disabled auto-deployment, don't forget to run the base component / workflow deployment command as described in the [main Readme](../../README.md) or [import documentation](../import_export.md):

```bash
docker run --rm \
  -e "HETIDA_DESIGNER_BACKEND_API_URL=http://hetida-designer-backend:8090/api/" \
  --name htdruntime_deployment \
  --network hetida-designer-network \
  --entrypoint python hetida-designer_hetida-designer-runtime -c 'from hetdesrun.exportimport.importing import import_transformations; import_transformations("./transformations/", update_component_code=False);'
```

## Workflow Execution

### Producers and Consumers

We prepare some producer/consumers in order to send messages and watch the results.

Open a terminal and start a console producer in a shell inside the kafka service container:
```bash
docker-compose -f docker-compose-kafka.yml exec kafka /opt/kafka/bin/kafka-console-producer.sh --broker-list kafka:9092 --topic hd-execution-topic --property "parse.key=true" --property key.separator=":"
```

Open a second terminal and start a console consumer in a shell inside the kafka service container:
```bash
docker-compose -f docker-compose-kafka.yml exec kafka /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka:9092 --topic  hd-execution-topic --property print.key=true --property key.separator=":" --from-beginning
```

Open a third terminal and start a console consumer for the result topic inside the kafka service container:
```bash
docker-compose -f docker-compose-kafka.yml exec kafka /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka:9092 --topic  hd-execution-response-topic --property print.key=true --property key.separator="-" --from-beginning
```

### Creating the Kafka message payload

The Kafka message for running a workflow or component has the same structure as that of the transformation revision execution endpoint.

Therefore we refer to the backend interactive OpenAPI documentation (Available at http://localhost:8080/docs when running the docker compose setup) for details on available keys and their values.

Additionally, to construct such a message for test purposes, it is helpful to use the frontend test execution: Using your browser developer tools network tab you may inspect the json send to the execution endpoint. Use this as a template for writing your own messages.

Here is the json message value for running one of the example Workflows: "Volatility Detection Example", revision 1.0.0:

```json
{
    "id": "79ce1eb1-3ef8-4c74-9114-c856fd88dc89",
    "wiring": {
        "input_wirings": [
            {
                "workflow_input_name": "window_size",
                "adapter_id": "direct_provisioning",
                "filters": {
                    "value": "180min"
                }
            },
            {
                "workflow_input_name": "window_timestamp_location",
                "adapter_id": "direct_provisioning",
                "filters": {
                    "value": "center"
                }
            },
            {
                "workflow_input_name": "input_series",
                "adapter_id": "direct_provisioning",
                "filters": {
                    "value": "{\"2018-05-19T22:20:00.000Z\":86.9358994238,\"2018-05-19T22:25:00.000Z\":78.6552569681,\"2018-05-19T22:30:00.000Z\":93.515633185,\"2018-05-19T22:35:00.000Z\":96.3497006614,\"2018-05-19T22:40:00.000Z\":83.1926874657,\"2018-05-22T05:50:00.000Z\":926.4357356548,\"2018-05-22T05:55:00.000Z\":934.7257131637,\"2018-05-22T06:00:00.000Z\":908.4082221891,\"2018-05-22T06:05:00.000Z\":917.7112901544,\"2018-05-22T06:10:00.000Z\":924.0958121497}"
                }
            },
            {
                "workflow_input_name": "threshold",
                "adapter_id": "direct_provisioning",
                "filters": {
                    "value": "600.0"
                }
            }
        ],
        "output_wirings": []
    },
    "run_pure_plot_operators": false,
    "job_id": "00000000-0000-0000-0000-000000000002"
}
```

In order to execute the latest revision the json message is the same, except for the parameter "id", which needs to be replaced by the parameter "revision_group_id".

The Kafka execution command line producer started above expects its payload in a format `key:<MESSAGE JSON>`. A good choice for the key may be a job id (see technical details below).

Here is the same content from above, together with a key, as ready-to-paste one liner for the console producer:
```
exec_job_1:{ "id": "79ce1eb1-3ef8-4c74-9114-c856fd88dc89", "wiring": { "input_wirings": [ { "workflow_input_name": "window_size", "adapter_id": "direct_provisioning", "filters": { "value": "180min" } }, { "workflow_input_name": "window_timestamp_location", "adapter_id": "direct_provisioning", "filters": { "value": "center" } }, { "workflow_input_name": "input_series", "adapter_id": "direct_provisioning", "filters": { "value": "{\"2018-05-19T22:20:00.000Z\":86.9358994238,\"2018-05-19T22:25:00.000Z\":78.6552569681,\"2018-05-19T22:30:00.000Z\":93.515633185,\"2018-05-19T22:35:00.000Z\":96.3497006614,\"2018-05-19T22:40:00.000Z\":83.1926874657,\"2018-05-22T05:50:00.000Z\":926.4357356548,\"2018-05-22T05:55:00.000Z\":934.7257131637,\"2018-05-22T06:00:00.000Z\":908.4082221891,\"2018-05-22T06:05:00.000Z\":917.7112901544,\"2018-05-22T06:10:00.000Z\":924.0958121497}" } }, { "workflow_input_name": "threshold", "adapter_id": "direct_provisioning", "filters": { "value": "600.0" } } ], "output_wirings": [] }, "run_pure_plot_operators": false, "job_id": "00000000-0000-0000-0000-000000000002"}
```

This is the ready-to-paste one liner for the console producer to execute the latest revision of the revision group:
```
exec_job_2:{ "revision_group_id": "d0d40c45-aef0-424a-a8f4-b16cd5f8b129", "wiring": { "input_wirings": [ { "workflow_input_name": "window_size", "adapter_id": "direct_provisioning", "filters": { "value": "180min" } }, { "workflow_input_name": "window_timestamp_location", "adapter_id": "direct_provisioning", "filters": { "value": "center" } }, { "workflow_input_name": "input_series", "adapter_id": "direct_provisioning", "filters": { "value": "{\"2018-05-19T22:20:00.000Z\":86.9358994238,\"2018-05-19T22:25:00.000Z\":78.6552569681,\"2018-05-19T22:30:00.000Z\":93.515633185,\"2018-05-19T22:35:00.000Z\":96.3497006614,\"2018-05-19T22:40:00.000Z\":83.1926874657,\"2018-05-22T05:50:00.000Z\":926.4357356548,\"2018-05-22T05:55:00.000Z\":934.7257131637,\"2018-05-22T06:00:00.000Z\":908.4082221891,\"2018-05-22T06:05:00.000Z\":917.7112901544,\"2018-05-22T06:10:00.000Z\":924.0958121497}" } }, { "workflow_input_name": "threshold", "adapter_id": "direct_provisioning", "filters": { "value": "600.0" } } ], "output_wirings": [] }, "run_pure_plot_operators": false, "job_id": "00000000-0000-0000-0000-000000000003"}
```
If no later revision then 1.0.0 has been created the output will be the same as before except for the job id.

### Running the workflow via Kafka

Pasting the payload above in the first terminal (the producer for the "hd-execution-topic" topic) leads to the same message occurring in the second terminal (consumer for the "hd-execution-topic" topic) and after short moment to a result in the third terminal (the consumer of the result topic "hd-execution-response-topic"). The result json payload is identical to the API transformation revision execution endpoint result json.

## Using adapters when running workflows via Kafka
This example includes only the "direct_provisioning" adapter being wired to all inputs and there are no wirings for the outputs, which is the proper way to indicate that these are wired to the default adapter "direct_provisioning". This results in all input data being expected as part of the Kafka payload and the output data being sent as part of the Kafka result message.

However this is not a limitation: You can use arbitrary adapters and also mix them freely in the same manner as for the web endpoint. I.e. some data can be directly provided via the Kafka message (usually single parameters) while other data is fetched from a database via an appropriate external adapter (typically mass data).

Here is the json message value for running the example workflow "Univariate Linear RUL Regression" revision 1.0.0 with mixed adapters:

```json
{
    "id": "8d61a267-3a71-51cd-2817-48c320469d6b",
    "wiring": {
        "input_wirings": [
            {
                "workflow_input_name": "num_pred_series_future_days",
                "adapter_id": "direct_provisioning",
                "filters": {"value": "1"}
            },
            {
                "workflow_input_name": "pred_series_frequency",
                "adapter_id": "direct_provisioning",
                "filters": {"value": "3min"}
            },
            {
                "ref_id": "root.plantA.picklingUnit.influx.temp",
                "ref_id_type": "SOURCE",
                "type": "timeseries(float)",
                "workflow_input_name": "timeseries",
                "adapter_id": "demo-adapter-python",
                "filters": {
                    "timestampFrom": "2022-05-19T15:24:00.000000000Z",
                    "timestampTo": "2022-05-19T15:24:00.000000000Z"
                }
            },
            {
                "ref_id": "root.plantA.picklingUnit.influx.temp",
                "ref_id_type": "SOURCE",
                "ref_key": "Max Value",
                "type": "metadata(float)",
                "workflow_input_name": "limit",
                "adapter_id": "demo-adapter-python",
                "filters": {}
            }
        ],
        "output_wirings": [
            {
                "ref_id": "root.plantA.picklingUnit.influx.anomaly_score",
                "ref_id_type": "SINK",
                "type": "timeseries(float)",
                "workflow_output_name": "pred_series",
                "adapter_id": "demo-adapter-python"
            }
        ]
    },
    "run_pure_plot_operators": false,
    "job_id": "00000000-0000-0000-0000-000000000005"
}
```

And for your convenience the corresponding ready-to-paste one liner:
```
exec_job_3: { "id": "8d61a267-3a71-51cd-2817-48c320469d6b", "wiring": { "input_wirings": [ { "workflow_input_name": "num_pred_series_future_days", "adapter_id": "direct_provisioning", "filters": {"value": "1"} }, { "workflow_input_name": "pred_series_frequency", "adapter_id": "direct_provisioning", "filters": {"value": "3min"} }, { "ref_id": "root.plantA.picklingUnit.influx.temp", "ref_id_type": "SOURCE", "type": "timeseries(float)", "workflow_input_name": "timeseries", "adapter_id": "demo-adapter-python", "filters": { "timestampFrom": "2022-05-19T15:24:00.000000000Z", "timestampTo": "2022-05-19T15:24:00.000000000Z" } }, { "ref_id": "root.plantA.picklingUnit.influx.temp", "ref_id_type": "SOURCE", "ref_key": "Max Value", "type": "metadata(float)", "workflow_input_name": "limit", "adapter_id": "demo-adapter-python", "filters": {} } ], "output_wirings": [ { "ref_id": "root.plantA.picklingUnit.influx.anomaly_score", "ref_id_type": "SINK", "type": "timeseries(float)", "workflow_output_name": "pred_series", "adapter_id": "demo-adapter-python" } ] }, "run_pure_plot_operators": false, "job_id": "00000000-0000-0000-0000-000000000005" }
```

## Configuring the Kafka consumer / producer
See [config](../../runtime/hetdesrun/webservice/config.py) code for available configuration options and corresponding environment variable names. All variables containing "KAFKA" should be of interest here. You can specify topic names and options for the [aiokafka](https://aiokafka.readthedocs.io/en/stable/) consumer / producer clients.

Note that not all combinations of options will work / make sense. For example the built-in consumer expects autocommit being set to true. Moreover a consumer group id is expected to be set.

## Technical details on the Kafka consumer
The Kafka consumer (and producer for sending results) runs in the backend web service application: One consumer / producer pair is initialized per gunicorn/uvicorn worker process. Consumers are part of a consumer group specified via configuration (see above). By default messages are distributed to topic partitions automatically using the key of the Kafka message. Therefore it makes sense to use something like a job name or job id as message key.

To actually make use of all these consumer instances for scaling, the corresponding topic in your Kafka cluster should be configured to have at least as many partitions as the designer backend has worker processes.

Note that running the analytical code actually happens in the runtime service (separately scalable). So a sensible setup is to have a one-replication backend service with several worker processes and a scaled-up (multi-replication) runtime service.