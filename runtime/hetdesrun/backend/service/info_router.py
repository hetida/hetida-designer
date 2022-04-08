import logging

from fastapi import APIRouter, status
from hetdesrun import VERSION
from hetdesrun.backend.kafka.consumer import get_kafka_worker_context
from hetdesrun.webservice.config import runtime_config

logger = logging.getLogger(__name__)


info_router = APIRouter(
    prefix="/info",
    tags=["info"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        status.HTTP_403_FORBIDDEN: {"description": "Forbidden"},
        status.HTTP_404_NOT_FOUND: {"description": "Not Found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
    },
)


@info_router.get(
    "/",
    response_model=dict,
    summary="Returns a sign of life",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_200_OK: {"description": "Successfully got a sign of life"}},
)
async def get_info() -> dict:
    """Show readiness and provide version info.

    If Kafka consumer execution is enabled this will also show
    some information of the consumer instance running in the web service worker
    instance which is selected to answer this http request.
    """
    logger.info("Get sign of life")

    # import current state of consumer globals

    info_dict = {
        "msg": "Here I am",
        "version": VERSION,
    }

    if runtime_config.hd_kafka_consumer_enabled and runtime_config.is_backend_service:
        kafka_ctx = get_kafka_worker_context()
        info_dict["worker_process_internal_kafka_consumer_id"] = str(kafka_ctx.consumer_id)
        info_dict[
            "worker_process_kafka_consumer_partition_assignments"
        ] = kafka_ctx.consumer.assignment()

    return info_dict
