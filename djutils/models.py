import datetime

from django.db import models


class QueueMessage(models.Model):
    queue = models.CharField(max_length=255)
    message = models.TextField()
    created = models.DateTimeField(default=datetime.datetime.now, db_index=True)
    
    class Meta:
        ordering = ('created',) # FIFO queue
