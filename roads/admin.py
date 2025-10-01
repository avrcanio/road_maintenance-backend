from django import forms
from django.contrib import admin
from django.contrib.gis import forms as gis_forms
from django.utils.translation import gettext_lazy as _

from .models import RoadSection


class RoadSectionAdminForm(forms.ModelForm):
    class Meta:
        model = RoadSection
        fields = '__all__'
        widgets = {
            'geom': gis_forms.OSMWidget(
                attrs={                   
                    'default_lat': 43.7350,
                    'default_lon': 15.8950,
                    'default_zoom': 12,
                    'map_srid': 3857,
                }
            ),
        }


@admin.register(RoadSection)
class RoadSectionAdmin(admin.ModelAdmin):
    form = RoadSectionAdminForm
    list_display = ('name', 'road_number', 'length', 'road_width', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'road_number')
    readonly_fields = ('length', 'created_at')
    fieldsets = (
        (None, {'fields': ('name', 'road_number', 'description', 'is_active')}),
        (
            _('Geometrija'),
            {
                'fields': (
                    'geom',
                    'length',
                    'road_width',
                )
            },
        ),
        (_('Evidencija'), {'fields': ('created_at',)}),
    )
