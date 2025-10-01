import secrets

from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class CustomerReview(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", _("Nacrt")
        PENDING = "pending_review", _("Čeka kupca")
        ACCEPTED = "accepted", _("Prihvaćeno")
        CHANGE_REQUESTED = "change_requested", _("Tražena dorada")
        EXPIRED = "expired", _("Isteklo")
        CANCELLED = "cancelled", _("Otkazano")

    work_item = models.ForeignKey(
        "projects.WorkItem",
        on_delete=models.CASCADE,
        related_name="customer_reviews",
        verbose_name=_("Stavka posla"),
    )
    version = models.PositiveIntegerField(default=1, verbose_name=_("Verzija pregleda"))
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name=_("Status pregleda"),
        db_index=True,
    )
    deadline = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Rok za odgovor kupca")
    )
    note_public = models.TextField(
        blank=True,
        verbose_name=_("Poruka kupcu"),
        help_text=_("Kratka napomena koja se prikazuje kupcu u emailu/na stranici."),
    )
    data_snapshot_hash = models.CharField(
        max_length=128,
        blank=True,
        verbose_name=_("Hash prikazanih podataka"),
        help_text=_("Kriptografski hash payload-a prikazanog kupcu u ovoj verziji."),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Kreirano"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Ažurirano"))
    closed_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Zaključano"))

    class Meta:
        verbose_name = _("Pregled kupca")
        verbose_name_plural = _("Pregledi kupaca")
        ordering = ("-created_at",)
        unique_together = (("work_item", "version"),)
        indexes = [
            models.Index(fields=["work_item", "version"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Review #{self.pk} — WI {self.work_item_id} v{self.version} [{self.get_status_display()}]"

    def mark_closed(self):
        if not self.closed_at:
            self.closed_at = timezone.now()

    def is_active(self):
        return self.status in {self.Status.DRAFT, self.Status.PENDING} and not self.closed_at

    def is_overdue(self):
        return bool(
            self.deadline
            and timezone.now() > self.deadline
            and self.status == self.Status.PENDING
        )


class CustomerReviewDecision(models.Model):
    """Odluka kupca za konkretnu CustomerReview rundu."""

    class Action(models.TextChoices):
        ACCEPTED = "accepted", _("Prihvaćeno")
        CHANGE_REQUESTED = "change_requested", _("Tražena dorada")

    customer_review = models.ForeignKey(
        'CustomerReview',
        on_delete=models.CASCADE,
        related_name='decisions',
        verbose_name=_("Runda pregleda"),
    )
    decided_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='customer_review_decisions',
        verbose_name=_("Kupac (korisnik koji je odlučio)"),
    )
    action = models.CharField(
        max_length=32,
        choices=Action.choices,
        verbose_name=_("Akcija"),
        db_index=True,
    )
    comment = models.TextField(
        blank=True,
        verbose_name=_("Komentar"),
        help_text=_("Obavezno za 'Tražena dorada'."),
    )
    geom = gis_models.GeometryField(
        srid=3765,
        null=True,
        blank=True,
        verbose_name=_("Geometrija prigovora (point/polygon)"),
        help_text=_("Opcionalno; označite područje na mapi gdje rad nije zadovoljavajući."),
    )
    attachments = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Privitci (JSON)"),
        help_text=_("Opcionalno; metapodaci/URL-ovi dokumenata/fotografija."),
    )
    data_snapshot_hash = models.CharField(
        max_length=128,
        blank=True,
        verbose_name=_("Hash prikazanih podataka"),
        help_text=_("Hash payload-a prikazanog kupcu u trenutku odluke."),
    )
    decided_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Vrijeme odluke"),
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_("IP adresa"),
    )
    user_agent = models.CharField(
        max_length=512,
        blank=True,
        verbose_name=_("User-Agent"),
    )

    class Meta:
        verbose_name = _("Odluka kupca")
        verbose_name_plural = _("Odluke kupaca")
        ordering = ("-decided_at",)
        unique_together = (("customer_review", "decided_by_user"),)
        indexes = [
            models.Index(fields=["customer_review", "action"]),
            models.Index(fields=["decided_at"]),
        ]

    def __str__(self):
        return f"Decision #{self.pk} — CR {self.customer_review_id} [{self.get_action_display()}]"

    def clean(self):
        super().clean()
        if self.action == self.Action.CHANGE_REQUESTED:
            if not (self.comment or "").strip():
                raise ValidationError(
                    {"comment": _("Komentar je obavezan za 'Tražena dorada'.")}
                )
            geom = self.geom
            if geom is None or getattr(geom, "empty", False):
                raise ValidationError(
                    {"geom": _("Geometrija je obavezna za 'Tražena dorada'.")}
                )

    def save(self, *args, **kwargs):
        if not self.decided_at:
            self.decided_at = timezone.now()
        self.full_clean()
        return super().save(*args, **kwargs)


class ReviewToken(models.Model):
    """Jednokratan, vremenski ograničen token za pristup CustomerReview rundi."""

    customer_review = models.ForeignKey(
        'CustomerReview',
        on_delete=models.CASCADE,
        related_name='tokens',
        verbose_name=_("Runda pregleda (CustomerReview)"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='review_tokens',
        verbose_name=_("Kupac (primatelj tokena)"),
    )
    jti = models.CharField(
        max_length=200,
        unique=True,
        editable=False,
        verbose_name=_("Token (jti)"),
        help_text=_("Jedinstveni token koji ide u URL."),
    )
    scope = models.CharField(
        max_length=64,
        default="workitem:review",
        verbose_name=_("Opseg (scope)"),
        help_text=_("Logički opseg upotrebe tokena."),
    )
    issued_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Vrijeme izdavanja"))
    expires_at = models.DateTimeField(verbose_name=_("Vrijedi do"))
    used_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Iskorišten u"))
    revoked_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Opozvan u"))
    delivered_to_email = models.EmailField(blank=True, verbose_name=_("Poslano na email"))
    meta = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Meta"),
        help_text=_("Npr. kanal slanja, IP/UA prvog otvaranja i sl."),
    )

    class Meta:
        verbose_name = _("Review token")
        verbose_name_plural = _("Review tokeni")
        ordering = ("-issued_at",)
        indexes = [
            models.Index(fields=["customer_review", "user"]),
            models.Index(fields=["expires_at"]),
            models.Index(fields=["revoked_at", "used_at"]),
        ]

    def __str__(self):
        return f"Token {self.jti[:8]}… → CR {self.customer_review_id} (user {self.user_id})"

    def generate_jti(self, length_bytes: int = 32):
        self.jti = secrets.token_urlsafe(length_bytes)

    @property
    def is_revoked(self) -> bool:
        return self.revoked_at is not None

    @property
    def is_used(self) -> bool:
        return self.used_at is not None

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    def is_active(self) -> bool:
        return not (self.is_expired or self.is_revoked or self.is_used)

    def mark_used(self):
        if not self.is_active():
            return False
        self.used_at = timezone.now()
        self.save(update_fields=["used_at"])
        return True

    def revoke(self):
        if self.is_revoked:
            return False
        self.revoked_at = timezone.now()
        self.save(update_fields=["revoked_at"])
        return True

    def save(self, *args, **kwargs):
        if not self.jti:
            self.generate_jti()
        super().save(*args, **kwargs)
