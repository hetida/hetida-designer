from hetdesrun.adapters.kafka.models import (
    KafkaMessageValue,
    KafkaMessageValueRepresentation,
    KafkaMultiValueMessage,
    KafkaSingleValueMessage,
)
from hetdesrun.runtime.logging import job_id_context_filter


def create_message(
    message_dict: dict[str | None, KafkaMessageValue],
) -> KafkaSingleValueMessage | KafkaMultiValueMessage:
    """Create actual message, single/multi value depending on message_dict"""
    if (
        len(message_dict.keys()) == 1 and next(iter(message_dict.keys())) is None
    ):  # single value message!
        return KafkaSingleValueMessage(
            transformation_id=str(job_id_context_filter.get_value("root_trafo_id")),
            job_id=str(job_id_context_filter.get_value("currently_executed_job_id")),
            value=KafkaMessageValueRepresentation(
                value=message_dict[None].value,
                data_type=message_dict[None].external_type,
                output_name=message_dict[None].output_name,
            ),
        )

    return KafkaMultiValueMessage(
        transformation_id=str(job_id_context_filter.get_value("root_trafo_id")),
        job_id=str(job_id_context_filter.get_value("currently_executed_job_id")),
        values={
            value_key: KafkaMessageValueRepresentation(
                value=kfk_msg_val.value,
                data_type=kfk_msg_val.external_type,
                output_name=kfk_msg_val.output_name,
            )
            for value_key, kfk_msg_val in message_dict.items()
        },
    )
