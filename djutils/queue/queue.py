import os

from django.conf import settings

from djutils.queue.exceptions import QueueException
from djutils.queue.registry import registry
from djutils.utils.helpers import load_class


def get_queue_class():
    return load_class(getattr(
        settings, 'QUEUE_CLASS', 'djutils.queue.backends.database.DatabaseQueue'
    ))

def get_queue_name():
    if hasattr(settings, 'QUEUE_NAME'):
        return settings.QUEUE_NAME
    else:
        return 'queue-%s' % (os.path.basename(settings.DATABASE_NAME))


class Invoker(object):
    def __init__(self, queue):
        self.queue = queue
    
    def write(self, msg):
        self.queue.write(msg)
    
    def enqueue(self, command):
        self.write(registry.get_message_for_command(command))
    
    def read(self):
        return self.queue.read()
    
    def dequeue(self):
        msg = self.read()
        
        if msg:
            command = registry.get_command_for_message(msg)
            command.execute()
            return msg
    
    def flush(self):
        self.queue.flush()


class QueueCommandMetaClass(type):
    def __init__(cls, name, bases, attrs):
        """
        Register all command classes
        """
        registry.register(cls)


class QueueCommand(object):
    __metaclass__ = QueueCommandMetaClass
    
    def __init__(self, data=None):
        """
        Initialize the command object with a receiver and optional data.  The
        receiver object *must* be a django model instance.
        """
        self.set_data(data)

    def get_data(self):
        """Called by the Invoker when a command is being enqueued"""
        return self.data

    def set_data(self, data):
        """Called by the Invoker when a command is dequeued"""
        self.data = data

    def execute(self):
        """Execute any arbitary code here"""
        raise NotImplementedError()


# dynamically load up an instance of the Queue class we're using
Queue = get_queue_class()

queue_name = get_queue_name()
queue = Queue(queue_name, getattr(settings, 'QUEUE_CONNECTION', None))
invoker = Invoker(queue)
