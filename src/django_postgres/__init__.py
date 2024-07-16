# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.

# Have this foyer and other examples, it will allow the webapp to 
# show registered tasks in the dropdown for periodic tasks 

from .celery import app as celery_app

__all__ = ("celery_app",)
