# Kafka adapter
The built-in kafka adapter allows to consume from and produce to [Kafka](https://kafka.apache.org/https://kafka.apache.org/) topics on the level of individual transformation inputs and outputs. 

This means individual inputs or selections of inputs can be wired to Kafka topics (with additional configuration) and at the beginning of trafo execution, messages from the respective topics are fetched to supply the inputs with data. Typically this is used in combination with the consumption mode described below.

On the other side individual outputs or selections of outputs can be wired to Kafka topics (with additional configuration) and after execution the output data is produced as Kafka messages to the respective topics.

**For comparison**: [kafka execution](../execution/execution_via_kafka.md) expects a complete execution request as Kafka message payload (with arbitrary trafo id, wiring, ...). While this payload can contain input data in the form of wirings to the `direct_provisioning` adapter (see [adapter system intro](./intro.md) and [manual input](./manual_input.md)), its main use case is event-based execution job triggering.

In contrast the Kafka adapter enables capabilities similar to Kafka streaming frameworks via its consumption mode:


## Consumption mode
The Kafka adapter provides a separate [consumption mode](./../execution/kafka_consumption_mode.md) in which a hetida designer container can be started to listen to (i.e. to consume from) a Kafka topic and on each message retrieval run a fixed preconfigured transformation with a preconfigured wiring where one or more inputs are wired to / supplied from the received message.

In contrast to [kafka execution](../execution/execution_via_kafka.md) this allows to chain, split and distribute data handling / transformation / analytics via hetida designer transformations along and through multiple Kafka topics and enables versatile streaming functionality similar to Kafka streaming frameworks like [Kafka Streams](https://kafka.apache.org/documentation/streams/) or [faust-streaming](https://github.com/faust-streaming/faust).

Note that the hetida designer adapter system can play a similar role as [Kafka Connect](https://docs.confluent.io/platform/current/connect/index.html) in such contexts.

We recommend to read the remaining parts of the current page and then advance to the [consumption mode documentation](./../execution/kafka_consumption_mode.md) for details on setting it up.

## Configuration
First the Kafka adapter is activated by setting the `KAFKA_ADAPTER_ACTIVE` environment variable to `true` to enable the backend webservice (offering sources and sinks for the hd wiring dialog in the user interface)

Second the Kafka adapter needs to be [registered ](./adapter_registration.md) via the `HETIDA_DESIGNER_ADAPTERS` environment variable in the hetida designer backend. Its part typically is

```
kafka|Kafka Adapter|http://localhost:8090/adapters/kafka|http://localhost:8090/adapters/kafka"
```

Additionally you may set `KAFKA_ADAPTER_SERVICE_IN_RUNTIME` to `false` to make the web service part  run in the backend instead of the default(runtime).

Now multiple "Kafka config" objects can be configured using the `HD_KAFKA_CONFIGS` variable. Each such object provides sources for consuming or sinks for producing. Each one is tied to a topic, determines for what types and whether sources and/or sinks are offered, specifies commit strategy and last but not least connection details to the respective Kafka cluster.

Note that different such Kafka config objects can have the same topic.

Example:
```json
{
    "kafka_config_ts_input": {
        "display_name": "Timeseries inputs",
        "topic": "ts-ingestion",
        "types": ["multitsframe"],
        "consumable": true,
        "consumer_config": {
          "bootstrap_servers": ["localhost:9094"]
        },        
        "producable": false
    },
    "ingestion_status": {
        "display_name": "Timeseries Quality evaluation results",
        "topic": "ts-quality",
        "types": ["multitsframe", "metadata(str)"],
        "producer_config": {
          "bootstrap_servers": ["localhost:9094"]
        },        
        "consumable": false,
        "producable": true
    }
}
```

For complete list of fields and possible values we refer to the `KafkaConfig` class in the respective [code](../../runtime/hetdesrun/adapters/kafka/models.py) module.

As usual for a adapter, after setting this, Kafka sources and sinks can be selected and wired in the hetida designer test execution dialog.

The provided example allows to wire `MULTITSFRAME` inputs to the `ts-ingestion` topic and to wire `STRING` and `MULTITSFRAME` outputs to the `ts-quality` topic. A typical usage would be a workflow doing same data quality analysis running in consumption mode which has 
* a `MULTITSFRAME` input wired to the `ts-ingestion` topic kafka config
* a `STRING` and a `MULTITSFRAME` output both wired to the `ts-quality` topic kafka config, providing the same message value key (see below) as free text filter in order to ensure that both outputs are send together in the same message.

## Message value keys (and message identifiers) in wirings
A Kafka message produced via the kafka adapter can hold more than one value. To enable this the Kafka adapter offers a free text filter `message_value_key` which is used both 
* to gather outputs wired to sinks from the same Kafka config object into a single message
* to set a "value key" that must be specified in corresponding input wirings to extract the value from such a multi value message.

This filter is for example available in the test execution dialog of hetida designer.

The format for the `message_value_key` filter is
```
message_identifier:value_key
```
where the `message_identifier` and the colon can be left out and even the complete filter can be empty.

* If `value_key` is an empty string, each output is send in its own (single-value-)message.
* If `value_key` is non-empty the output data is send in a multi-value-message together with all other output data with the same (possibly empty) `message_identifier`

**Note**: You only need to set an actual non-empty `message_identifier` if you want to send more than one message *to the same* topic from the same kafka_config. This is rarely the case! In typical scenarios a transformation execution should only send one (possibly multi-value-)message to a topic.

For inputs the filter has the same name. If your topics receives multi-value-messages you have to provide the `value_key` part for an input in order to specify which data in the multi value message is transferred to the wired input.

Of course the data type of the refrenced value must agree with the input's data type.


## Message format

### No Avro Schema support!
Due to reasons like
* the dynamic nature of possible combinations of data in multi value messages
* arbitrarily deep nested metadata support for the mass data types (`DATAFRAME`, `MULTITSFRAME`, `SERIES`)
* `ANY` type which can contain arbitrarily deep nested json objects
* avro not supporting arbitrarily nested mappings (only records)

it is not easily possible to specify a fixed, on mapping-level non-recursive schema as is required by [Apache Avro](https://avro.apache.org/). Therefore the Kafka adapter cannot support avro at the moment.

To mitigate at least the compression aspect we recommend to configure compression on producer/consumer level instead as described below.

### Compression
Messages are json serialized and deserialized, a compression can be specified via `compression_type` subfield of the `consumer_config` and `producer_config` options of the Kafka config object, see the [aiokafka documentation](https://aiokafka.readthedocs.io/en/stable/api.html) for details.

Note that required system packages for some compression methods, like `snappy`, are preinstalled in the hetida designer runtime image. You may need to add system packages to the runtime docker image for other compression types.


### Multi value format

An example for a multi value message with just a single message value key `analytic_result` is:
```json
{
    "transformation_id": "1946d5f8-44a8-724c-176f-16f3e49963af",
    "job_id": "e25883d3-cbc6-48ba-8999-d8344661cc64",
    "message_creation_timestamp": "2024-04-12T11:31:59.646864+00:00",
    "values": {
        "analytic_result": {
            "value": {
                "a": true,
                "b": 31.56
            },
            "data_type": "metadata(any)",
            "output_name": "output"
        }
    }
}
```
This message was generated from a hd trafo execution sending one of its outputs (named "output") via the Kafka adapter in a multi value message with message value key "analytic_result". The referenced `transformation_id`and `job_id` and the timestamp `message_creation_timestamp` as well as the `output_name` were generated automatically during this execution and are not required in general.

Note that the json representation of the value transferred as "value" depends on the accompanying `data_type`.

The required structure is just
```json
{
    "values": {
        "analytic_result": {
            "value": {
                "a": true,
                "b": 31.56
            },
            "data_type": "metadata(any)",
        }
    }
}
```

For complete details see [KafkaMultiValueMessage](../../runtime/hetdesrun/adapters/kafka/models.py) class definition in the source code.

### Single value format

Running the same example without a message value key yields a single value message of form
```json
{
    "transformation_id": "1946d5f8-44a8-724c-176f-16f3e49963af",
    "job_id": "415cc80e-6b28-43c3-9f04-241161f9fa11",
    "message_creation_timestamp": "2024-04-12T11:42:35.813564+00:00",
    "value": {
        "value": {
            "a": true,
            "b": 31.56
        },
        "data_type": "metadata(any)",
        "output_name": "output"
    }
}
```

Again, required is only
```json
{
    "value": {
        "value": {
            "a": true,
            "b": 31.56
        },
        "data_type": "metadata(any)",
    }
}
```

For complete details see [KafkaSingleValueMessage](../../runtime/hetdesrun/adapters/kafka/models.py) class definition in the source code.
