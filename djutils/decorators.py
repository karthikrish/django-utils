import atexit
import Queue
import re
import time
import threading

from django.conf import settings
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.utils.cache import cache
from django.utils.functional import wraps


def throttle(methods_or_func, limit=3, duration=900):
    if callable(methods_or_func):
        methods = ('POST',)
    else:
        methods = methods_or_func
    
    def decorator(func):
        @wraps(func)
        def inner(request, *args, **kwargs):
            if request.method in methods:
                remote_addr = request.META.get('HTTP_X_FORWARDED_FOR') or \
                              request.META.get('REMOTE_ADDR')
                
                if remote_addr:
                    key = re.sub(r'[^0-9\.]', '', remote_addr)
                    cached = cache.get(key)
                    
                    if cached == limit:
                        return HttpResponseForbidden('Try slowing down a little.')
                    elif not cached:
                        cache.set(key, 1, duration)
                    else:
                        cache.incr(key)
            
            return func(request, *args, **kwargs)
        return inner
    
    if callable(methods_or_func):
        return decorator(methods_or_func)
    
    return decorator

def memoize(func):
    func._memoize_cache = {}
    @wraps(func)
    def inner(*args, **kwargs):
        key = (args, tuple(kwargs.items()))
        if key not in func._memoize_cache:
            func._memoize_cache[key] = func(*args, **kwargs)
        return func._memoize_cache[key]
    return inner

def worker_thread():
    while 1:
        func, args, kwargs = queue.get()
        try:
            func(*args, **kwargs)
        except:
            pass # <-- log error here
        finally:
            queue.task_done()

def async(func):
    @wraps(func)
    def inner(*args, **kwargs):
        queue.put((func, args, kwargs))
    return inner

queue = Queue.Queue()

for i in range(getattr(settings, 'DJANGO_UTILS_WORKER_THREADS', 1)):
    thread = threading.Thread(target=worker_thread)
    thread.daemon = True
    thread.start()

def cleanup():
    queue.join()

atexit.register(cleanup)
