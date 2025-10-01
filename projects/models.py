from decimal import Decimal, ROUND_FLOOR

from django.contrib.auth import get_user_model
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import GEOSGeometry
from django.db import connection, models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from customers.models import Customer
from operations.models import OperationType
from roads.models import RoadSection


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


class WorkItem(models.Model):
    """Model za stavke rada."""

    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.CASCADE,
        related_name="work_items",
        verbose_name=_('Radni nalog'),
    )
    road_section = models.ForeignKey(
        RoadSection,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name=_('Dionica ceste'),
        limit_choices_to={'is_active': True},
    )
    operation_type = models.ForeignKey(
        OperationType,
        on_delete=models.CASCADE,
        verbose_name=_('Vrsta operacije'),
    )

    ROAD_SIDE_CHOICES = [
        ("right", _("Desna")),
        ("left", _("Lijeva")),
        ("notap", _("Nije primjenjivo")),
    ]
    road_side = models.CharField(
        _('Strana ceste'),
        max_length=5,
        choices=ROAD_SIDE_CHOICES,
        help_text=_('Lijeva, Desna ili prazno'),
    )

    geom = gis_models.MultiPolygonField(
        _('Geometrija (izvedeni poligon)'),
        srid=3765,
        null=True,
        blank=True,
    )

    description = models.TextField(_('Opis stavke'), blank=True)
    quantity = models.DecimalField(
        _('Količina'),
        max_digits=12,
        decimal_places=3,
    )
    unit_price = models.DecimalField(
        _('Jedinična cijena'),
        max_digits=10,
        decimal_places=6,
        null=True,
        blank=True,
    )
    total_price = models.DecimalField(
        _('Ukupna cijena'),
        max_digits=12,
        decimal_places=2,
        editable=False,
    )
    notes = models.TextField(_('Napomene'), blank=True)

    class Meta:
        verbose_name = _('Stavka rada')
        verbose_name_plural = _('Stavke rada')
        ordering = ['work_order', 'id']

    def __str__(self) -> str:
        return f"{self.operation_type.name} - {self.quantity} {self.operation_type.unit}"

    def _compute_geom_via_postgis(self):
        if not self.road_section_id or not self.operation_type_id:
            return None
        if not self.quantity or self.quantity <= 0:
            return None
        if self.road_side not in ("left", "right"):
            return None

        side = "left" if self.road_side == "left" else "right"
        unit = self.operation_type.unit

        with connection.cursor() as cur:
            if unit == "m2":
                sql = f"""
                WITH ls AS (
                    SELECT
                        geom::geometry(LineString, 3765) AS g,
                        COALESCE(road_width, 0)::double precision / 2.0 AS width_half
                    FROM roads_roadsection
                    WHERE id = %s
                ),
                ln AS (
                    SELECT ST_LineMerge(g) AS g,
                        GREATEST(ST_Length(g), 0.001) AS len,
                        width_half
                    FROM ls
                ),
                params AS (
                    SELECT 1.0::double precision AS extra_w,
                        width_half
                    FROM ln
                ),
                bands AS (
                    SELECT
                        ST_Buffer(
                            (SELECT g FROM ln),
                            (SELECT width_half FROM params) + (SELECT extra_w FROM params),
                            'endcap=flat join=mitre side={side}'
                        )::geometry(Polygon, 3765) AS outer_band,
                        ST_Buffer(
                            (SELECT g FROM ln),
                            (SELECT width_half FROM params),
                            'endcap=flat join=mitre side={side}'
                        )::geometry(Polygon, 3765) AS inner_edge
                ),
                strip AS (
                    SELECT ST_Difference(outer_band, inner_edge)::geometry(Polygon, 3765) AS geom
                    FROM bands
                )
                SELECT ST_AsBinary(ST_Multi(geom)) FROM strip;
                """

                cur.execute(sql, [self.road_section_id])
                row = cur.fetchone()
                return row[0] if row and row[0] else None

            if unit == "kom":
                sql = f"""
                WITH ls AS (
                    SELECT
                        geom::geometry(LineString, 3765) AS g,
                        COALESCE(road_width, 0)::double precision / 2.0 AS width_half
                    FROM roads_roadsection
                    WHERE id = %s
                ),
                ln AS (
                    SELECT ST_LineMerge(g) AS g, ST_Length(g) AS len, width_half
                    FROM ls
                ),
                params AS (
                    SELECT GREATEST(1, LEAST(10000, %s::int)) AS n
                ),
                frac AS (
                    SELECT generate_series(1, (SELECT n FROM params)) AS i,
                        (generate_series(1, (SELECT n FROM params))::double precision) / ((SELECT n FROM params) + 1) AS f
                ),
                pts_on_line AS (
                    SELECT ST_LineInterpolatePoint((SELECT g FROM ln), f) AS p
                    FROM frac
                ),
                edge_band AS (
                    SELECT ST_Buffer(
                            (SELECT g FROM ln),
                            (SELECT width_half FROM ln) + 0.075 + 0.05,
                            'endcap=flat join=mitre side={side}'
                        ) AS b
                ),
                pts_on_side AS (
                    SELECT ST_ClosestPoint((SELECT b FROM edge_band), p) AS p
                    FROM pts_on_line
                ),
                circles AS (
                    SELECT ST_Buffer(p, 0.075, 'quad_segs=8')::geometry(Polygon, 3765) AS g
                    FROM pts_on_side
                )
                SELECT ST_AsBinary(ST_Multi(ST_Collect(g))) FROM circles;
                """

                n = int(Decimal(self.quantity).to_integral_value(rounding=ROUND_FLOOR))
                if n <= 0:
                    return None
                cur.execute(sql, [self.road_section_id, n])
                row = cur.fetchone()
                return row[0] if row and row[0] else None

        return None

    def save(self, *args, **kwargs) -> None:
        if (self.unit_price is None or self.unit_price == Decimal("0")) and self.operation_type_id:
            self.unit_price = self.operation_type.base_price

        qty = self.quantity or Decimal("0")
        up = self.unit_price or Decimal("0")
        self.total_price = qty * up

        super().save(*args, **kwargs)

        try:
            wkb = self._compute_geom_via_postgis()
            new_geom = GEOSGeometry(wkb, srid=3765) if wkb else None
        except Exception:
            new_geom = None

        if new_geom is not None:
            WorkItem.objects.filter(pk=self.pk).update(geom=new_geom)
            self.geom = new_geom
