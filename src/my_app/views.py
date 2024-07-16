import structlog
from django.http import HttpResponse

logger = structlog.get_logger(__name__)


# Create your views here.
def index(request):
    logger.info("views/index", request=request)
    return HttpResponse("Hello World!")
