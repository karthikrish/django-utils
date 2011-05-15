try:
    import cPickle as pickle
except ImportError:
    import pickle

from django.db import models

from djutils.dashboard.provider import PANEL_PROVIDER_TYPES


class PanelDataManager(models.Manager):
    def get_distinct_titles(self):
        return self.values_list('panel_title', flat=True).order_by().distinct()
    
    def get_latest(self, max_ids=None):
        payload = {}
        
        for title in self.get_distinct_titles():
            payload[title] = self.get_latest_by_title(
                panel_title=title,
                max_id=max_ids and max_ids.get(panel_title) or None
            )
        
        return payload
    
    def get_latest_by_title(self, panel_title, limit=50, max_id=None):
        qs = self.filter(panel_title=panel_title)
        
        if max_id:
            qs = qs.filter(id__gt=max_id)
        
        qs = qs[:limit]
        
        agg_qs = qs.aggregate(max_id=models.Max('id'))
        
        return {
            'queryset': qs,
            'max_id': agg_qs['max_id'],
        }
    
    def get_latest_of_each(self):
        # I'm not 100% certain if this is the most efficient way to do this
        # query, as I believe it has On**2 complexity -- an alternative would
        # simple be to iterate over panel_types and select the latest:
        # return [
        #    self.filter(panel_title=t)[0] \
        #        for t in self.get_distinct_titles()
        # ]
        return self.raw("""
            SELECT pd.*
            FROM (
                SELECT panel_title, max(created_date) AS max_date
                FROM %(db_table)s GROUP BY panel_title
            ) AS subq
            INNER JOIN %(db_table)s AS pd ON (
                pd.panel_title = subq.panel_title AND
                pd.created_date = max_date
            )
        """ % {'db_table': self.model._meta.db_table})


class PanelData(models.Model):
    """
    Preserve historical data from dashboard.  Automatically deleted by the
    periodic command :func:`remove_old_panel_data`
    """
    created_date = models.DateTimeField(db_index=True)
    panel_title = models.CharField(max_length=255)
    panel_data = models.TextField()
    panel_type = models.IntegerField(choices=PANEL_PROVIDER_TYPES)
    
    objects = PanelDataManager()
    
    class Meta:
        ordering = ('-created_date',)
    
    def __unicode__(self):
        return '%s: %s' % (self.panel_title, self.created_date)
    
    def get_data(self):
        return pickle.loads(str(self.panel_data))
