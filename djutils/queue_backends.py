from djutils.models import QueueMessage


class BaseQueue(object):
    def __init__(self, name):
        self.name = name
    
    def write(self, data):
        raise NotImplementedError
    
    def read(self):
        raise NotImplementedError
    
    def flush(self):
        raise NotImplementedError
    
    def __len__(self):
        raise NotImplementedError


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
        return len(self._get_queryset())
