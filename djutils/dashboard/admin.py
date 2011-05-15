from django.contrib import admin

from djutils.dashboard.models import PanelData


class PanelDataAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_date'
    list_filter = ('panel_type', 'panel_title',)


admin.site.register(PanelData, PanelDataAdmin)
