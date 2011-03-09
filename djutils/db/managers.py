from django.db import models

from djutils.constants import LIVE_STATUS


class PublishedManager(models.Manager):
    def __init__(self, status_field='status', *args, **kwargs):
        self.status_field = status_field
        super(PublishedManager, self).__init__(*args, **kwargs)
    
    def published(self):
        return self.filter(**{self.status_field: LIVE_STATUS})
