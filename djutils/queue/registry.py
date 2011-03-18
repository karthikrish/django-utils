try:
    import cPickle as pickle
except ImportError:
    import pickle

from django.conf import settings


class CommandRegistry(object):
    _registry = {}
    _stack = []
    
    message_template = '%(CLASS)s:%(DATA)s'
    
    def register(self, command_class):
        self._registry[str(command_class)] = command_class

    def unregister(self, command_class):
        del(self._registry[str(command_class)])
    
    def __contains__(self, command_class):
        return str(command_class) in self._registry

    def get_message_for_command(self, command):
        """Convert a command object to a message for storage"""
        return self.message_template % {
            'CLASS': str(type(command)),
            'DATA': pickle.dumps(command.get_data())
        }

    def get_command_for_message(self, msg):
        """Convert a message to a command"""
        # parse out the pieces from the enqueued message
        klass_str, data = msg.split(':', 1)
        
        klass = self._registry.get(klass_str)
        if not klass:
            raise QueueException, '%s not found in CommandRegistry' % klass_str
        
        return klass(pickle.loads(str(data)))


registry = CommandRegistry()
