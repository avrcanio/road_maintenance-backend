from django.core.validators import MinLengthValidator, RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class Customer(models.Model):
    """Represents a Croatian business customer."""

    LEGAL_FORMS = [
        ("d.o.o.", _("d.o.o.")),
        ("j.d.o.o.", _("j.d.o.o.")),
        ("obrt", _("Obrt")),
        ("u.o.", _("Udruga")),
        ("d.d.", _("d.d.")),
        ("ostalo", _("Ostalo")),
    ]

    name = models.CharField(_('Naziv'), max_length=255)
    legal_form = models.CharField(
        _('Pravna forma'),
        max_length=16,
        choices=LEGAL_FORMS,
        blank=True,
        help_text=_("Pravna forma (npr. d.o.o., j.d.o.o.)."),
    )
    oib = models.CharField(
        _('OIB'),
        max_length=11,
        unique=True,
        validators=[
            MinLengthValidator(11),
            RegexValidator(r"^\d{11}$", _("OIB mora sadržavati točno 11 znamenki.")),
        ],
        help_text=_("Hrvatski OIB (11 znamenki)."),
    )
    mbs = models.CharField(
        _('MBS'),
        max_length=50,
        blank=True,
        help_text=_("Matični broj subjekta (MBS) iz sudskog registra."),
    )
    vat_registered = models.BooleanField(
        _('U sustavu PDV-a'),
        default=True,
        help_text=_("Označuje je li subjekt u sustavu PDV-a."),
    )
    vat_id = models.CharField(
        _('PDV ID'),
        max_length=32,
        blank=True,
        help_text=_("Europski PDV identifikacijski broj (npr. HR12345678901)."),
    )

    street_address = models.CharField(_('Adresa'), max_length=255)
    postal_code = models.CharField(
        _('Poštanski broj'),
        max_length=5,
        validators=[RegexValidator(r"^\d{5}$", _("Poštanski broj mora imati 5 znamenki."))],
    )
    city = models.CharField(_('Grad'), max_length=100)
    county = models.CharField(
        _('Županija'),
        max_length=100,
        blank=True,
        help_text=_("Županija u kojoj je sjedište klijenta."),
    )
    country = models.CharField(_('Država'), max_length=100, default="Hrvatska")

    contact_person = models.CharField(_('Kontakt osoba'), max_length=100, blank=True)
    contact_email = models.EmailField(_('Kontakt e-mail'), blank=True)
    contact_phone = models.CharField(_('Telefon'), max_length=50, blank=True)
    contact_mobile = models.CharField(_('Mobilni telefon'), max_length=50, blank=True)

    iban = models.CharField(
        _('IBAN'),
        max_length=34,
        blank=True,
        validators=[
            RegexValidator(
                r"^[A-Z0-9]{15,34}$",
                _("IBAN smije sadržavati samo velika slova i znamenke (15-34 znakova)."),
            )
        ],
        help_text=_("Primarni IBAN za transakcije."),
    )
    bank_name = models.CharField(_('Banka'), max_length=100, blank=True)
    swift_bic = models.CharField(
        _('SWIFT/BIC'),
        max_length=11,
        blank=True,
        validators=[RegexValidator(r"^[A-Z0-9]{8}(?:[A-Z0-9]{3})?$", _("Neispravan SWIFT/BIC format."))],
    )

    payment_terms_days = models.PositiveSmallIntegerField(
        _('Rok plaćanja (dani)'),
        default=30,
        help_text=_("Standardni broj dana za plaćanje računa."),
    )
    notes = models.TextField(_('Bilješke'), blank=True)

    created_at = models.DateTimeField(_('Kreirano'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Ažurirano'), auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = _('Kupac')
        verbose_name_plural = _('Kupci')

    def __str__(self) -> str:
        return f"{self.name} ({self.oib})"
