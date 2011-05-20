from djutils.dashboard.models import Panel, PANEL_PROVIDER_GRAPH


class PanelProvider(object):
    """\
    Base class from which other panel providers should derive.  Much like a
    munin plugin, there is no input provided and the output conforms to a
    standard format.
    
    Methods of interest:

    :method:`get_data` returns a dictionary of data to be plotted
    
    :method:`get_title` returns the title for the panel
    :method:`get_panel_type` returns the type of panel
    :method:`get_priority` returns an arbitrary integer indicating the order in
        which this panel should be processed
    """
    
    def get_data(self):
        """\
        This method returns data to be displayed, but depending on the panel 
        type the output of the function may differ.
        
        GRAPH::
        
            {
                'database_connections': 3,
                'idle_connections': 1,
                'idle_in_transaction': 1,
            }
        
        TEXT::
        
            {
                'queries': ['SELECT * FROM ...', 'UPDATE ...',],
            }
        """
        raise NotImplementedError

    def get_title(self):
        raise NotImplementedError
    
    def get_panel_type(self):
        return PANEL_PROVIDER_GRAPH
    
    def get_priority(self):
        return 20
    
    def get_panel_instance(self):
        panel, _ = Panel.objects.get_or_create(
            title=self.get_title(),
            defaults=dict(panel_type=self.get_panel_type())
        )
        return panel