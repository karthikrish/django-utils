class BaseQueue(object):
    def __init__(self, name, connection):
        self.name = name
        self.connection = connection
    
    def write(self, data):
        raise NotImplementedError
    
    def read(self):
        raise NotImplementedError
    
    def flush(self):
        raise NotImplementedError
    
    def __len__(self):
        raise NotImplementedError
