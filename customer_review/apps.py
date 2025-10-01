from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CustomerReviewConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'customer_review'
    verbose_name = _('Recenzije kupaca')
