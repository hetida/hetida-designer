# Workflow Execution via Apache Kafka

> :warning: Warning: The Kafka endpoint is currently not available, following the backend rewrite in Python. It will be reintroduced in a later release. So for now this documentation page only applies for version <=0.6 and not for versions >=0.7.

This document describes the [Kafka](https://kafka.apache.org/) workflow execution endpoint by providing a basic example.

## Setup

We save a copy of the `docker-compose.yml` with the new name `docker-compose-kafka.yml`, modify the **hetida-designer-backend** service and add a **zookeeper** and a **kafka** service:

```yaml
...

  hetida-designer-backend:
    image: hetida/designer-backend
    ports:
      - 8080:8090
    environment:
      org.hetida.designer.backend.installed.adapters: "demo-adapter-python|Python-Demo-Adapter|http://localhost:8092|http://hetida-designer-demo-adapter-python:8092,demo-adapter-java|Java-Demo-Adapter|http://localhost:8091/adapter|http://hetida-designer-demo-adapter-java:8091/adapter,local-file-adapter|Local-File-Adapter|http://localhost:8090/adapters/localfile|http://hetida-designer-runtime:8090/adapters/localfile"
      org.hetida.designer.backend.listener.kafka.enabled: "true"
      spring.kafka.bootstrap-servers: "kafka:19092"
      spring.kafka.consumer.group-id: "Designer_Workflow_Execution"
      org.hetida.designer.backend.listener.kafka.execTopic: "designer_initialize_job"
      org.hetida.designer.backend.listener.kafka.execResultTopic: "designer_job_result"
    depends_on:
      - hetida-designer-db
      - hetida-designer-runtime
      - kafka

  zookeeper:
    image: zookeeper:3.6
    ports:
      - 2181:2181
  kafka:
    image: wurstmeister/kafka:2.13-2.6.0
    environment:
      KAFKA_ZOOKEEPER_CONNECT: "zookeeper:2181"
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: 'true'
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

:warning: **Note:** This small Kafka setup using the "wurstmeister/kafka" image is only suitable for examples/demonstration and local development.

Now we can start this new setup via the following command (ensuring correct broker configuration, see https://stackoverflow.com/q/53571823).

:warning: **Warning:** The following command deletes existing component/workflow data / volumes!

```
docker-compose -f docker-compose-kafka.yml rm -fsv && docker-compose -f docker-compose-kafka.yml up --force-recreate --build
```
We will demonstrate workflow execution via Kafka using one of the example workflows provided with the default component/workflow deployment, so do not forget to run the deployment command as described in the Readme:

```bash
docker run --rm \
  -e "HETIDA_DESIGNER_BACKEND_API_URL=http://hetida-designer-backend:8090/api/" \
  --name htdruntime_deployment \
  --network hetida-designer-network \
  --entrypoint python hetida/designer-runtime -c 'from hetdesrun.exportimport.importing import import_all; import_all("./transformations/");'  
```

## Workflow Execution

### Producers and Consumers

We prepare some producer/consumers in order to send messages and watch the results.

Open a terminal and start a console producer in a shell inside the kafka service container:
```bash
docker-compose -f docker-compose-kafka.yml exec kafka /opt/kafka/bin/kafka-console-producer.sh --broker-list kafka:9092 --topic designer_initialize_job --property "parse.key=true" --property "key.separator=:"
```

Open a second terminal and start a console consumer in a shell inside the kafka service container:
```bash
docker-compose -f docker-compose-kafka.yml exec kafka /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka:9092 --topic  designer_initialize_job --property print.key=true --property key.separator="-" --from-beginning
```

Open a third terminal and start a console consumer for the result topic inside the kafka service container:
```bash
docker-compose -f docker-compose-kafka.yml exec kafka /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka:9092 --topic  designer_job_result --property print.key=true --property key.separator="-" --from-beginning
```

### Creating the Kafka message payload

To execute a workflow via Kafka we can use the frontend test execution to help us building the payload. Using your browser developer tools network tab, observe that running for example the "Univariate Linear RUL regression Example" Workflow sends a JSON like the following to the workflow's execution endpoint `http://localhost/hdapi/workflows/806df1b9-2fc8-4463-943f-3d258c569663/execute?run_pure_plot_operators=true` (example shortened!):

```json
{
    "id": "e4c36380-4b4d-4c97-b3f2-c8c25d25e5c8",
    "name": "STANDARD-WIRING",
    "inputWirings": [
        {
            "id": "e5ed757f-f8b0-45f0-be68-e00b0d0184a9",
            "workflowInputName": "inp_series",
            "adapterId": "direct_provisioning",
            "filters": {
                "value":"{\"2020-05-01T00:00:00.000Z\":2.5340945967,\"2020-05-01T01:00:00.000Z\":2.5658768256,
    ...
    ...
    ...
\"2020-06-11T08:00:00.000Z\":1.7441884421,\"2020-06-11T09:00:00.000Z\":1.7268847381,\"2020-06-11T10:00:00.000Z\":1.7372780067,\"2020-06-11T11:00:00.000Z\":1.7531690232,\"2020-06-11T12:00:00.000Z\":1.7563962807,\"2020-06-11T13:00:00.000Z\":1.7337006137,\"2020-06-11T14:00:00.000Z\":1.7567559875,\"2020-06-11T15:00:00.000Z\":1.7314396428}"
            }
        },
        {
            "id": "b29eb7b7-eae9-4711-b245-cd555456b9d0",
            "workflowInputName": "limit",
            "adapterId": "direct_provisioning",
            "filters": {
                "value": "1.3"
            }
        },
        {
            "id": "4454bb31-21e1-4a33-9555-6d919d6be9fd",
            "workflowInputName": "num_days_forecast",
            "adapterId": "direct_provisioning",
            "filters": {
                "value": "30"
            }
        }
    ],
    "outputWirings": [
        {
            "id": "9658ae49-ec4d-4a0c-bed1-d28c6de7814f",
            "workflowOutputName": "intercept",
            "adapterId": "direct_provisioning"
        },
        {
            "id": "5ce41007-cc70-4639-b022-6bd54e7152fd",
            "workflowOutputName": "limit_violation_timestamp",
            "adapterId": "direct_provisioning"
        },
        {
            "id": "d40fb12d-67f0-415f-887c-9e9aa3cbfad3",
            "workflowOutputName": "rul_regression_result_plot",
            "adapterId": "direct_provisioning"
        },
        {
            "id": "c585607e-b8e0-445a-8b78-633c6875c8dd",
            "workflowOutputName": "slope",
            "adapterId": "direct_provisioning"
        }
    ]
}
```

The Kafka execution consumer expects its message in a format `key:<JSON_PAYLOAD>` with <JSON_PAYLOAD> required to have the following structure:
```json
{
    "workflowId": "806df1b9-2fc8-4463-943f-3d258c569663", // the workflow id from the url of the request
    "configuration": {
        "engine": "plain",
        "name": "806df1b9-2fc8-4463-943f-3d258c569663",
        "run_pure_plot_operators": true
    },
    "workflow_wiring": {
        "input_wirings": [
            {
                "adapter_id": ...,
                "filters": ...,
                "workflow_input_name": ...,
                "source_id" ... // only required if adapter_id is not "direct_provisioning"
            },
            ...
        ],
        "output_wirings": [
            {
                "adapter_id": ...,
                "filters": ...,
                "workflow_output_name": ...,
                "sink_id" ... // only required if adapter_id is not "direct_provisioning" 
            },
            ...
        ]
    }
}
```

**Note:** This is slightly different from the web endpoint structure. This may be unified in the future!

We can now use this information to convert the web-based payload to a Kafka-payload. The following includes only part of the data and is written as one line to allow easy pasting to the console producer:

```
test_executionissuer_1:{"workflowId":"806df1b9-2fc8-4463-943f-3d258c569663","configuration":{"engine":"plain", "name":"806df1b9-2fc8-4463-943f-3d258c569663", "run_pure_plot_operators":false}, "workflow_wiring": {"input_wirings":[{"workflow_input_name":"inp_series","adapter_id":"direct_provisioning","filters":{"value":"{\"2020-05-01T00:00:00.000Z\":2.5340945967,\"2020-06-11T11:00:00.000Z\":1.7531690232,\"2020-06-11T12:00:00.000Z\":1.7563962807,\"2020-06-11T13:00:00.000Z\":1.7337006137,\"2020-06-11T14:00:00.000Z\":1.7567559875,\"2020-06-11T15:00:00.000Z\":1.7314396428}"}},{"workflow_input_name":"limit","adapter_id":"direct_provisioning","filters":{"value":"1.3"}},{"workflow_input_name":"num_days_forecast","adapter_id":"direct_provisioning","filters":{"value":"30"}}],"output_wirings":[{"workflow_output_name":"intercept","adapter_id":"direct_provisioning"},{"workflow_output_name":"limit_violation_timestamp","adapter_id":"direct_provisioning"},{"workflow_output_name":"rul_regression_result_plot","adapter_id":"direct_provisioning"},{"workflow_output_name":"slope","adapter_id":"direct_provisioning"}]}}
```

### Running the workflow via Kafka

Pasting the payload above in the first terminal (the producer for the "designer_initialize_job" topic) leads to the same message occuring in the second terminal (consumer for the "designer_initialize_job" topic) and after short moment to a result in the third terminal (the consumer of the result topic "designer_job_result"). The result json payload is identical to the web execution endpoint result json payload.

## Using adapters when running workflows via Kafka
This example includes only the "direct_provisioning" adapter for both all inputs and all outputs. This results in all input data being expected as part of the Kafka payload and output data being sent as part of the result Kafka message. 

However this is no limitation: You can use arbitrary adapters and also mix them freely in the same manner as for the web endpoint. I.e. some data can be directly provided (usually single parameters) while other data is fetched from a database via an appropriate external adapter (typically mass data).

