import datetime
try:
    import cPickle as pickle
except ImportError:
    import pickle

from django.conf import settings

from djutils.dashboard.models import PanelData


class PanelRegistryException(Exception):
    pass


class PanelRegistry(object):
    """
    A simple Registry used to track subclasses of :class:`PanelProvider`
    """
    _registry = {}
    
    def register(self, panel_class):
        if panel_class in self._registry:
            raise PanelRegistryException('"%s" is already registered' % panel_class)
        
        panel_obj = panel_class()
        self._registry[panel_class] = panel_obj

    def unregister(self, panel_class):
        if panel_class not in self._registry:
            raise PanelRegistryException('"%s" is not registered' % panel_class)
        
        del(self._registry[panel_class])
    
    def __contains__(self, panel_class):
        return panel_class in self._registry
    
    def get_panel_instances(self):
        return self._registry.values()
    
    def _get_data_for_panels(self):
        # store any return data in a list
        data = []
        
        # function to sort the panels by priority
        key = lambda obj: obj.get_priority()
        
        for panel in sorted(self.get_panel_instances(), key=key):
            data.append(dict(
                panel_title=panel.get_title(),
                panel_type=panel.get_panel_type(),
                panel_data=panel.get_panel_data(),
                created_date=datetime.datetime.now()
            ))
        
        return data
    
    def _store_panel_data(self, data):
        for data_dict in data:
            PanelData.objects.create(
                panel_title=data_dict['panel_title'],
                panel_type=data_dict['panel_type'],
                panel_data=pickle.dumps(data_dict['panel_data']),
                created_date=data_dict['created_date'],
            )
    
    def update_panels(self):
        raw_data = self._get_data_for_panels()
        self._store_panel_data(raw_data)
        return raw_data


registry = PanelRegistry()
