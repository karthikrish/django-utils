import datetime
try:
    import cPickle as pickle
except ImportError:
    import pickle

from django.db import models
from django.db.models import Max
from django.template.defaultfilters import slugify

from djutils.dashboard.registry import registry


PANEL_PROVIDER_GRAPH = 0
PANEL_PROVIDER_TEXT = 1

PANEL_PROVIDER_TYPES = (
    (PANEL_PROVIDER_GRAPH, 'Graph'),
    (PANEL_PROVIDER_TEXT, 'Text'),
)


class PanelManager(models.Manager):
    def update_panels(self):
        data = []
        shared_now = datetime.datetime.now()
        
        # function to sort the panels by priority
        key = lambda obj: obj.get_priority()
        
        for provider in sorted(registry.get_provider_instances(), key=key):
            # pull the data off the panel and store
            panel_obj = provider.get_panel_instance()
            
            panel_data = PanelData.objects.create(
                panel=panel_obj,
                data=pickle.dumps(provider.get_data()),
                created_date=shared_now,
            )
            data.append(panel_data)
        
        return data
    
    def get_panels(self):
        """\
        Purpose is to get a queryset of panel models matching the registered 
        panel providers
        """
        return self.filter(title__in=registry.get_titles())
    
    def get_latest(self):
        """\
        Get the latest panel data for the registered panel providers
        """
        return [
            PanelData.objects.filter(panel=panel)[0] \
                for panel in self.get_panels()
        ]


class Panel(models.Model):
    title = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(db_index=True)
    panel_type = models.IntegerField(choices=PANEL_PROVIDER_TYPES)
    
    class Meta:
        ordering = ('title',)

    objects = PanelManager()
    
    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(Panel, self).save(*args, **kwargs)


class PanelDataManager(models.Manager):
    def get_most_recent_update(self):
        return self.aggregate(max_date=Max('created_date'))['max_date']
    
    def get_data(self, panel, limit=None):
        queryset = self.filter(panel=panel)
        if limit:
            queryset = queryset[:limit]
        
        return queryset, queryset.aggregate(max_id=Max('id'))['max_id']


class PanelData(models.Model):
    """
    Preserve historical data from dashboard.  Automatically deleted by the
    periodic command :func:`remove_old_panel_data`
    """
    panel = models.ForeignKey(Panel, related_name='data')
    created_date = models.DateTimeField(db_index=True)
    data = models.TextField()
    
    objects = PanelDataManager()
    
    class Meta:
        ordering = ('-created_date',)
    
    def __unicode__(self):
        return '%s: %s' % (self.panel.title, self.created_date)
    
    def get_data(self):
        return pickle.loads(str(self.data))
