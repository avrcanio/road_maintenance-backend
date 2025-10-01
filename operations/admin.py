from django.contrib import admin

from .models import OperationType


@admin.register(OperationType)
class OperationTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'unit', 'base_price', 'is_active')
    list_filter = ('unit', 'is_active')
    search_fields = ('name',)
    ordering = ('name',)
