from djutils.models import QueueMessage
from djutils.queue.backends.base import BaseQueue


class DatabaseQueue(BaseQueue):
    def _get_queryset(self):
        return QueueMessage.objects.filter(queue=self.name)
    
    def write(self, data):
        QueueMessage.objects.create(queue=self.name, message=data)
    
    def read(self):
        try:
            message = self._get_queryset()[0]
        except IndexError:
            data = None
        else:
            data = message.message
            message.delete()
        return data
    
    def flush(self):
        self._get_queryset().delete()
    
    def __len__(self):
        return self._get_queryset().count()
