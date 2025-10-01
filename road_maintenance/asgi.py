"""
ASGI config for road_maintenance project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

from django_nextjs.asgi import NextJsMiddleware

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'road_maintenance.settings')

application = NextJsMiddleware(get_asgi_application())
