from django.utils.importlib import import_module


def load_class(path):
    """
    dynamically load a class given a string of the format
    
    package.Class
    """
    package, klass = path.rsplit('.', 1)
    module = import_module(package)
    return getattr(module, klass)
