from django.db.models import Manager

from djutils.constants import LIVE_STATUS


class PublishedManager(Manager):
    def __init__(self, status_field='status'):
        self.status_field = status_field
    
    def published(self):
        return self.filter(**{self.status_field: LIVE_STATUS})
