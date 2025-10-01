from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class LoginEvent(models.Model):
    class Action(models.TextChoices):
        LOGIN = "login", _("Prijava")
        LOGOUT = "logout", _("Odjava")
        FAILURE = "failure", _("Neuspjela prijava")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="login_events",
        verbose_name=_("Korisnik"),
    )
    username = models.CharField(
        _("Korisničko ime"),
        max_length=150,
        blank=True,
        help_text=_("Korisničko ime iz pokušaja prijave."),
    )
    action = models.CharField(
        _("Radnja"),
        max_length=16,
        choices=Action.choices,
    )
    timestamp = models.DateTimeField(_("Vrijeme"), default=timezone.now, db_index=True)
    ip_address = models.GenericIPAddressField(_("IP adresa"), null=True, blank=True)
    user_agent = models.TextField(_("Korisnički agent"), blank=True)
    path = models.CharField(_("URL"), max_length=512, blank=True)

    class Meta:
        verbose_name = _("Evidencija prijave")
        verbose_name_plural = _("Evidencije prijava")
        ordering = ["-timestamp"]

    def __str__(self) -> str:
        actor = self.user or self.username or _("Nepoznato")
        return f"{actor} – {self.get_action_display()}"
