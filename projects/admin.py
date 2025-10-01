from django import forms
from django.contrib import admin
from django.contrib.gis import forms as gis_forms
from django.utils.translation import gettext_lazy as _

from .models import Project, WorkItem, WorkOrder


class WorkItemAdminForm(forms.ModelForm):
    class Meta:
        model = WorkItem
        fields = '__all__'
        widgets = {
            'geom': gis_forms.OSMWidget(
                attrs={
                    'map_width': 800,
                    'map_height': 600,
                    'default_lat': 43.7350,
                    'default_lon': 15.8950,
                    'default_zoom': 12,
                    'map_srid': 3857,
                }
            ),
        }


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'customer', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active', 'customer')
    search_fields = ('name', 'contract_number', 'customer__name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    fieldsets = (
        (None, {'fields': ('name', 'customer', 'description')}),
        (
            _('Ugovor'),
            {
                'fields': (
                    'contract_number',
                    'contract_date',
                    'contract_value',
                )
            },
        ),
        (
            _('Izvedba'),
            {
                'fields': (
                    'start_date',
                    'end_date',
                    'is_active',
                )
            },
        ),
        (_('Praćenje'), {'fields': ('created_at',)}),
    )


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ('number', 'title', 'project', 'status', 'scheduled_date', 'completed_date')
    list_filter = ('status', 'project__customer')
    search_fields = ('number', 'title', 'project__name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    fieldsets = (
        (None, {'fields': ('number', 'project', 'title', 'description', 'status')}),
        (
            _('Planiranje'),
            {
                'fields': (
                    'scheduled_date',
                    'completed_date',
                )
            },
        ),
        (_('Evidencija'), {'fields': ('created_by', 'created_at')}),
    )


@admin.register(WorkItem)
class WorkItemAdmin(admin.ModelAdmin):
    form = WorkItemAdminForm
    list_display = (
        'work_order',
        'operation_type',
        'road_section',
        'quantity',
        'unit_price',
        'total_price',
        'road_side',
    )
    list_filter = ('operation_type', 'road_side', 'work_order__project')
    search_fields = (
        'work_order__number',
        'operation_type__name',
        'road_section__name',
    )
    readonly_fields = ('total_price',)
    fieldsets = (
        (None, {
            'fields': (
                'work_order',
                'operation_type',
                'road_section',
                'road_side',
                'description',
            )
        }),
        (_('Količina i cijena'), {
            'fields': (
                'quantity',
                'unit_price',
                'total_price',
            )
        }),
        (_('Geometrija'), {'fields': ('geom',)}),
        (_('Napomene'), {'fields': ('notes',)}),
    )
