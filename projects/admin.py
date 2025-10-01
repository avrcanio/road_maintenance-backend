from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Project, WorkOrder


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
