from django.db import models
from django.utils.translation import gettext_lazy as _


class OperationType(models.Model):
    """Model za vrste operacija/radova."""

    UNIT_CHOICES = [
        ("m2", _("m²")),
        ("m3", _("m³")),
        ("m", _("m")),
        ("kom", _("komad")),
        ("kg", _("kilogram")),
        ("sat", _("sat")),
        ("dan", _("dan")),
        ("pšj", _("paušalno")),
    ]

    name = models.CharField(_('Naziv operacije'), max_length=200)
    description = models.TextField(_('Opis rada'), blank=True)
    unit = models.CharField(
        _('Jedinica mjere'),
        max_length=10,
        choices=UNIT_CHOICES,
    )
    base_price = models.DecimalField(
        _('Osnovna cijena'),
        max_digits=10,
        decimal_places=6,
    )
    is_active = models.BooleanField(_('Aktivna'), default=True)

    class Meta:
        verbose_name = _('Vrsta operacije')
        verbose_name_plural = _('Vrste operacija')
        ordering = ['name']

    def __str__(self) -> str:
        return f"{self.name} ({self.unit})"
