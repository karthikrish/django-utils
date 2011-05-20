try:
    import json
except ImportError:
    from django.utils import simplejson as json

from django.db.models import Max
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.safestring import mark_safe

from djutils.dashboard.models import Panel, PanelData
from djutils.utils.http import json_response


def serialize_panel_data(panels_and_data, limit=50):
    payload = []
    
    for panel, panel_data_qs in panels_and_data.items():
        for obj in panel_data_qs:
            payload.append(dict(
                panel_id=panel.pk,
                point_id=obj.id,
                data=obj.get_data()
            ))
    
    return payload

def dashboard(request):
    panels = Panel.objects.get_panels()
    
    if request.is_ajax():
        max_id = int(request.GET.get('max_id', 0))
        panels_and_data = {}
        
        for panel in panels:
            panel_data = panel.data.filter(pk__gt=max_id)
            panels_and_data[panel] = panel_data
        
        payload = serialize_panel_data(panels_and_data)
        
        return json_response(payload)
    
    return render_to_response('dashboard/dashboard_index.html', {
        'panel_list': panels,
    }, context_instance=RequestContext(request))
