import httplib2
import socket
from urllib import urlencode

from django.conf import settings
from django.http import HttpResponse
from django.utils import simplejson


def fetch_url(url, parameters=None, http_method="GET", follow_redirects=True,
              timeout=4, user_agent='python-httplib2'):
    sock = httplib2.Http(timeout=timeout)
    sock.follow_redirects = follow_redirects
    
    request_headers = {'User-Agent': user_agent}
    
    try:
        if http_method not in ('GET', 'HEAD'):
            request_headers['Content-type'] = 'application/x-www-form-urlencoded'
            post_data = urlencode(parameters or {})
            headers, response = sock.request(
                url,
                http_method,
                post_data,
                headers=request_headers
            )
        else:
            if parameters:
                url = '%s?%s' % (url, urlencode(parameters))
            
            headers, response = sock.request(url, headers=request_headers)
    
    except socket.timeout:
        raise ValueError('Socket timed out')
    
    if headers['status'] not in ('200', 200):
        raise ValueError('Returned status: %s' % (headers['status']))
    
    return response

def json_response(context_dictionary):
    payload = simplejson.dumps(context_dictionary)
    mimetype = settings.DEBUG and 'text/javascript' or 'application/json'
    return HttpResponse(payload, mimetype=mimetype)
