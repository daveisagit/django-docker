import os
import logging
from celery import Celery
from celery.signals import setup_logging
from django_structlog.celery.steps import DjangoStructLogInitStep

from django_postgres.settings import LOG_LEVEL, LOGGING, LOGGING_ROOT

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_postgres.settings")

app = Celery("django_postgres")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# A step to initialize django-structlog
app.steps["worker"].add(DjangoStructLogInitStep)


@setup_logging.connect
def receiver_setup_logging(
    loglevel, logfile, format, colorize, **kwargs
):  # pragma: no cover
    logging.config.dictConfig(LOGGING)
