from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class RoadsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'roads'
    verbose_name = _('Dionice cesta')
