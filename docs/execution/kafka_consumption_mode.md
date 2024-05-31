# Kafka consumption mode

The [Kafka adapter](../adapter_system/kafka_adapter.md) provides a separate consumption mode in which a hetida designer container can be started to listen to (i.e. to consume from) a Kafka topic and on each message retrieval run a fixed preconfigured transformation with a preconfigured wiring where one or more inputs are wired to / supplied from the received message.

In contrast to [kafka execution](./execution_via_kafka.md) this allows to chain, split and distribute data handling / transformation / analytics via hetida designer transformations along and through multiple Kafka topics and enables versatile streaming functionality similar to Kafka streaming frameworks like [Kafka Streams](https://kafka.apache.org/documentation/streams/) or [faust-streaming](https://github.com/faust-streaming/faust).

Note that the hetida designer adapter system can play a similar role as [Kafka Connect](https://docs.confluent.io/platform/current/connect/index.html) in such contexts.


## Basic Setup
First you need the Kafka adapter to be active and registered and Kafka configurations configured as is described in [Kafka adapter documentation](../adapter_system/kafka_adapter.md).

Then you can set up a separate container using the hetida designer runtime Docker image running in consumption mode by setting the environment variable `HETIDA_DESIGNER_KAFKA_CONSUMPTION_MODE` to a json object which is equal to the execution payload (described for example [here](./running_transformation_revisions.md)) except that no `job_id` is set. Consumption mode will automatically create a new job id for each execution triggered by a Kafka message.

The provided input wiring determines to which topic consumption mode will listen continuously. Note that all other functionalities like backend/runtime API endpoints will not run on a container in consumption mode.

Example:
```json
{
	"id": "1946d5f8-44a8-724c-176f-16f3e49963af",
	"run_pure_plot_operators": true,
	"wiring": {
		"input_wirings": [
			{
				"adapter_id": "kafka",
				"filters": {
					"message_value_key": "analytic_result"
				},
				"ref_id": "base",
				"ref_id_type": "THINGNODE",
				"ref_key": "ingestion_status_metadata(any)",
				"type": "metadata(any)",
				"use_default_value": false,
				"workflow_input_name": "input"
			}
		],
		"output_wirings": []
	}
}
```

The example above will listen to the topic behind the Kafka configuration with key `ingestion_status` using this Kafka config's consumer config. Since message value key is set, it expects the message to be in the multi-value message format.

Each time it receives a new message, it will run the trafo with id `1946d5f8-44a8-724c-176f-16f3e49963af` and provide the value under message value key `analytic_result` to the input with name `input`. Note that data in the message under message value keys that are not wired to an input is ignored.

The wiring above does nothing with the trafo's outputs, which is equivalent to having them wired to the direct_provisioning adapter. In consumption mode, outputs wired to the direct_provisioning adapter will not be sent anywhere but are just logged in the container's log. Typically, in a real scenario you want to wire outputs to a real adapter when using consumption mode: Either an adapter that persists results or sends them to another system, or again to the Kafka adapter in another topic.

It is recommended to enable the caching of non-draft transformations for execution for this use-case in order to avoid reloading the transformation revision on handling each message: This is achieved by setting the environment variable `HD_ENABLE_CACHING_FOR_NON_DRAFT_TRAFOS_FOR_EXEC` to `true`.

# Notes
* Consumption mode can only listen to one topic with one Kafka config. So the input wirings must all be tied to the same Kafka config object.
* In the same spirit, if more than one inputs are wired via Kafka adapter then for every input wiring message value keys must be set and the message must be in multi value format. Furthermore, message identifier must be equal (typically empty string) for all Kafka adapter input wirings.
* Commit strategy, connection details etc. are all determined by the Kafka config attributes, in particular the `consumer_config` attribute.
* The Kafka Config object(s) configured for the container in consumption mode is not required to be the same or exist in other hetida designer services (in particular the hd backend).
* However, you typically want the consumption mode container to have `HD_IS_RUNTIME_SERVICE` being set to `true` in order to carry out trafo execution in the same container to avoid data being transferred via rest.