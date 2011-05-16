try:
    import json
except ImportError:
    from django.utils import simplejson as json

from django.db.models import Max
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.safestring import mark_safe

from djutils.dashboard.models import Panel, PanelData


def serialize_panel_data(panel_list, limit=1):
    payload = []
    
    for panel in panel_list:
        panel_data_qs, max_id = PanelData.objects.get_data(panel, limit)
        
        serialized = dict(
            id=panel.pk,
            title=panel.title,
            data=[{'id': obj.id, 'data': obj.get_data()} for obj in panel_data_qs],
            max_id=max_id,
        )
        payload.append(serialized)
    
    return mark_safe(json.dumps(payload))

def dashboard(request):
    if request.is_ajax():
        pass
    else:
        panels = Panel.objects.get_panels()
        panel_data = serialize_panel_data(panels, 50)
    
    return render_to_response('dashboard/dashboard_index.html', {
        'panel_list': panels, 'panel_data': panel_data,
    }, context_instance=RequestContext(request))
