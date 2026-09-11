from django.core.wsgi import get_wsgi_application
from django.contrib.staticfiles.handlers import StaticFilesHandler
application=StaticFilesHandler(get_wsgi_application())
