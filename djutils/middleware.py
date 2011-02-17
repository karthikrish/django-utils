import re
import urlparse

from django.conf import settings


class IgnoreCsrfMiddleware(object):
    """
    CSRF can EABOD
    """
    def process_request(self, request):
        request.csrf_processing_done = True


class SubdomainMiddleware:
    def process_request(self, request):
        if 'HTTP_HOST' in request.META:
            host = request.META['HTTP_HOST']
            split_url = urlparse.urlsplit(host)
            tld_bits = split_url.netloc.rsplit('.', 2)
            request.subdomain = len(tld_bits) == 3 and tld_bits[0] or None
