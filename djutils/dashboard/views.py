try:
    import json
except ImportError:
    from django.utils import simplejson as json

from django.db.models import Max
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.safestring import mark_safe

from djutils.dashboard.models import PanelData


def serialize_panel_data(latest_data):
    payload = []
    
    for panel_title, data in latest_data.items():
        serialized = dict(
            title=panel_title,
            data=[obj.get_data() for obj in data['queryset']],
            max_id=data['max_id'],
        )
        payload.append(serialized)
    
    return json.dumps(payload)

def dashboard(request):
    if request.is_ajax():
        pass
    else:
        latest_data = PanelData.objects.get_latest()
        json_data = serialize_panel_data(latest_data)
    
    return render_to_response('dashboard/dashboard_index.html', {
        'data': latest_data, 'json_data': mark_safe(json_data),
    }, context_instance=RequestContext(request))
