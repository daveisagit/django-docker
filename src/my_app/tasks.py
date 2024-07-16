"""Example task"""

import structlog
from celery import shared_task

logger = structlog.get_logger(__name__)


@shared_task(name="Example Task")
def print_hi():
    logger.info("print_hi", some_data={"a_list": [1, 2, 3]})
    logger.debug("bugger", some_data={"b_list": [1, 2, 3, 4, 5, 6]})
