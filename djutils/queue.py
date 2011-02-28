import os
try:
    import cPickle as pickle
except ImportError:
    import pickle

from django.conf import settings
from django.utils.functional import wraps

from djutils.utils.helpers import load_class, generic_autodiscover


if hasattr(settings, 'QUEUE_NAME'):
    QUEUE_NAME = settings.QUEUE_NAME
else:
    QUEUE_NAME = 'queue-%s' % (os.path.basename(settings.DATABASE_NAME))


class QueueException(Exception):
    pass

# dynamically load up a default Queue class
Queue = load_class(getattr(settings, 'QUEUE_CLASS', 'djutils.queue_backends.DatabaseQueue'))

def autodiscover():
    return generic_autodiscover('commands')

class Invoker(object):
    _registry = {}
    _stack = []
    
    message_template = '%(CLASS)s:%(DATA)s'
    
    # number of messages to remember
    stack_size = 10

    def __init__(self, queue_class=Queue, queue_name=QUEUE_NAME):
        self.queue = queue_class(queue_name)
        self.queue_name = queue_name
   
    @classmethod
    def register(cls, command_class):
        cls._registry[str(command_class)] = command_class

    @classmethod
    def unregister(cls, command_class):
        del(cls._registry[str(command_class)])
    
    @classmethod
    def __contains__(cls, command_class):
        return str(command_class) in cls._registry

    def flush(self):
        self.queue.flush()

    def write(self, msg):
        """Write a generic message to the invoker's queue"""
        return self.queue.write(msg)

    def get_message_for_command(self, command):
        """Convert a command object to a message for storage"""
        return self.message_template % {
            'CLASS': str(type(command)),
            'DATA': pickle.dumps(command.get_data())
        }

    def enqueue(self, command):
        """Enqueue a command for processing"""
        msg = self.get_message_for_command(command)
        self.write(msg)

    def read(self):
        """Read from the queue, returning None if empty"""
        return self.queue.read()

    def load(self, msg):
        """Convert a message to a command"""
        # parse out the pieces from the enqueued message
        klass_str, data = msg.split(':', 1)
        
        klass = self._registry.get(klass_str)
        if not klass:
            raise QueueException, '%s not found in Invoker registry' % klass_str
        
        return klass(pickle.loads(str(data)))

    def dequeue(self):
        """Dequeue a message, convert to a command and execute all at once"""
        msg = self.read()
        if msg:
            command = self.load(msg)
            command.execute()
            self._stack.append(msg)
            if len(self._stack) > self.stack_size:
                self._stack = self._stack[len(self._stack) - self.stack_size:]
            return True
        return False

    def undo(self):
        try:
            last_message = self._stack.pop()
            command = self.load(last_message)
            command.undo()
        except IndexError:
            raise QueueException, 'No command found'


class QueueCommandMetaClass(type):
    def __init__(cls, name, bases, attrs):
        """
        Register all command classes with the Invoker
        """
        Invoker.register(cls)


class QueueCommand(object):
    __metaclass__ = QueueCommandMetaClass

    data = None
    
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

    def undo(self):
        """Undo the action"""
        raise NotImplementedError()


def queue_command(func_or_queue_class=None, queue_name=QUEUE_NAME):
    if callable(func_or_queue_class):
        queue_class = Queue
    else:
        queue_class = func_or_queue_class or Queue
    
    def decorator(func):
        def create_command():
            def execute(self):
                args, kwargs = self.data
                return func(*args, **kwargs)
            
            klass = type(
                '%s.%s' % (func.__module__, func.__name__),
                (QueueCommand,),
                {'execute': execute,
                 '__module__': func.__module__,
                 '__doc__': func.__doc__}
            )
            
            return klass
        
        klass = create_command()
        invoker = Invoker(queue_class, queue_name)
        
        func.invoker = invoker
        
        @wraps(func)
        def inner_run(*args, **kwargs):
            invoker.enqueue(klass((args, kwargs)))
        return inner_run
    
    if callable(func_or_queue_class):
        return decorator(func_or_queue_class)
    
    return decorator
