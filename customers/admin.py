from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "oib", "city", "contact_person", "vat_registered")
    search_fields = ("name", "oib", "mbs", "vat_id", "contact_person")
    list_filter = ("vat_registered", "county")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("name", "legal_form", "oib", "mbs", "vat_registered", "vat_id")}),
        (
            _("Adresni podaci"),
            {
                "fields": (
                    "street_address",
                    "postal_code",
                    "city",
                    "county",
                    "country",
                )
            },
        ),
        (
            _("Kontakt"),
            {
                "fields": (
                    "contact_person",
                    "contact_email",
                    "contact_phone",
                    "contact_mobile",
                )
            },
        ),
        (
            _("Bankovni podaci"),
            {"fields": ("iban", "bank_name", "swift_bic", "payment_terms_days")},
        ),
        (_("Dodatno"), {"fields": ("notes", "created_at", "updated_at")}),
    )
