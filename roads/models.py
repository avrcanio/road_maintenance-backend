from decimal import Decimal

from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _


class RoadSection(models.Model):
    """Dionice cesta (linije u metrima, HTRS96/TM EPSG:3765)."""

    name = models.CharField(_('Naziv dionice'), max_length=200)
    road_number = models.CharField(_('Broj ceste'), max_length=50, blank=True)
    geom = models.LineStringField(_('Geometrija'), srid=3765, null=True, blank=True)
    length = models.DecimalField(
        _('Duljina (m)'),
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
    )
    road_width = models.DecimalField(
        _('Širina ceste (m)'),
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=_("Prosječna širina kolnika u metrima."),
    )
    description = models.TextField(_('Opis dionice'), blank=True)
    is_active = models.BooleanField(_('Aktivna'), default=True)
    created_at = models.DateTimeField(_('Datum kreiranja'), auto_now_add=True)

    class Meta:
        verbose_name = _('Dionica ceste')
        verbose_name_plural = _('Dionice cesta')
        ordering = ['name']

    def __str__(self) -> str:
        return f"{self.name} ({self.road_number})" if self.road_number else self.name

    def save(self, *args, **kwargs) -> None:
        if self.geom:
            length_m = self.geom.length
            self.length = Decimal(f"{length_m:.2f}")
        super().save(*args, **kwargs)
