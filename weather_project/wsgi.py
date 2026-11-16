"""
WSGI config for weather_project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weather_project.settings')

application = get_wsgi_application()

# Load the ML model at worker start so the first user request doesn't pay for it.
from weather.ml.forecast_model import forecast_model  # noqa: E402

forecast_model._load()
