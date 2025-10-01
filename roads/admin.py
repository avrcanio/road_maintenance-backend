from django import forms
from django.contrib import admin
from django.contrib.gis import forms as gis_forms
from django.http import HttpResponseBadRequest
from django.shortcuts import render
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _

from .models import RoadSection


class RoadSectionOSMWidget(gis_forms.OSMWidget):
    template_name = 'roads/widgets/openlayers_osm_fullscreen.html'
    default_zoom = 12
    map_srid = 3857
    display_srid = 3765
    default_lon = 15.8950
    default_lat = 43.7350
    map_width = 800
    map_height = 600

    class Media:
        js = gis_forms.OSMWidget.Media.js + ('roads/js/roadsection_widget.js',)
        css = {
            'all': gis_forms.OSMWidget.Media.css['all'] + ('roads/css/roadsection_widget.css',),
        }

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['fullscreen_url'] = getattr(self, 'fullscreen_url', '')
        context['map_width'] = getattr(self, 'map_width', 800)
        context['map_height'] = getattr(self, 'map_height', 600)
        return context


class RoadSectionAdminForm(forms.ModelForm):
    class Meta:
        model = RoadSection
        fields = '__all__'
        widgets = {
            'geom': RoadSectionOSMWidget(),
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

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        widget = form.base_fields['geom'].widget
        if isinstance(widget, RoadSectionOSMWidget):
            widget.fullscreen_url = reverse('admin:roads_roadsection_fullscreen_map')
        return form

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'map-editor/',
                self.admin_site.admin_view(self.fullscreen_map_view),
                name='roads_roadsection_fullscreen_map',
            ),
        ]
        return custom_urls + urls

    def fullscreen_map_view(self, request):
        field_id = request.GET.get('field_id')
        module_name = request.GET.get('module')
        if not field_id:
            return HttpResponseBadRequest(_('Nedostaje identifikator polja.'))

        widget = RoadSectionOSMWidget()
        geom_field = RoadSection._meta.get_field('geom')
        context = {
            'field_id': field_id,
            'module_name': module_name,
            'storage_field_id': f'{field_id}_fullscreen_storage',
            'storage_field_name': f'{field_id}_fullscreen_storage',
            'map_id': f'{field_id}_fullscreen_map',
            'geom_name': geom_field.geom_type,
            'map_srid': widget.map_srid,
            'default_lon': widget.default_lon,
            'default_lat': widget.default_lat,
            'default_zoom': widget.default_zoom,
        }
        return render(request, 'roads/fullscreen_map.html', context)
