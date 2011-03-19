from django.utils.functional import wraps

from djutils.queue.queue import invoker, QueueCommand


def queue_command(func):
    """
    Decorator to execute a function out-of-band via the consumer.  Usage::
    
    @queue_command
    def send_email(user, message):
        ... this code executed when dequeued by the consumer ...
    """
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
    
    @wraps(func)
    def inner_run(*args, **kwargs):
        invoker.enqueue(klass((args, kwargs)))
    return inner_run
