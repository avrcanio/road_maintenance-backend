from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from customers.models import Customer


User = get_user_model()


class Project(models.Model):
    """Model za projekte."""

    name = models.CharField(_('Naziv projekta'), max_length=200)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        verbose_name=_('Kupac'),
        related_name='projects',
    )
    description = models.TextField(_('Opis'), blank=True)
    contract_number = models.CharField(
        _('Broj ugovora'),
        max_length=100,
        blank=True,
    )
    contract_date = models.DateField(
        _('Datum ugovora'),
        blank=True,
        null=True,
    )
    contract_value = models.DecimalField(
        _('Vrijednost ugovora (EUR)'),
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
    )
    start_date = models.DateField(_('Datum početka'))
    end_date = models.DateField(_('Datum završetka'), blank=True, null=True)
    is_active = models.BooleanField(_('Aktivan'), default=True)
    created_at = models.DateTimeField(_('Datum kreiranja'), auto_now_add=True)

    class Meta:
        verbose_name = _('Projekt')
        verbose_name_plural = _('Projekti')
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.name} - {self.customer.name}"


class WorkOrder(models.Model):
    """Model za radne naloge."""

    STATUS_CHOICES = [
        ("draft", _("Nacrt")),
        ("approved", _("Odobren")),
        ("in_progress", _("U tijeku")),
        ("completed", _("Završen")),
        ("cancelled", _("Otkazan")),
    ]

    number = models.CharField(
        _("Broj naloga"),
        max_length=50,
        unique=True,
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        verbose_name=_("Projekt"),
        related_name="work_orders",
    )
    title = models.CharField(_("Naziv naloga"), max_length=200)
    description = models.TextField(_("Opis"), blank=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("Kreirao"),
        related_name="work_orders",
    )
    created_at = models.DateTimeField(
        _("Datum kreiranja"),
        auto_now_add=True,
    )
    scheduled_date = models.DateField(
        _("Planirani datum"),
        blank=True,
        null=True,
    )
    completed_date = models.DateField(
        _("Datum završetka"),
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = _("Radni nalog")
        verbose_name_plural = _("Radni nalozi")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.number} - {self.title}"

    def save(self, *args, **kwargs) -> None:
        if not self.number:
            year = timezone.now().year
            count = WorkOrder.objects.filter(created_at__year=year).count() + 1
            self.number = f"RN-{year}-{count:04d}"
        super().save(*args, **kwargs)
