from django.contrib import admin

from djutils.dashboard.models import Panel, PanelData


class PanelAdmin(admin.ModelAdmin):
    list_display = ('title', 'panel_type',)


class PanelDataAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_date'
    list_filter = ('panel',)


admin.site.register(Panel, PanelAdmin)
admin.site.register(PanelData, PanelDataAdmin)
