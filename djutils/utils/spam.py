from django.conf import settings
from django.contrib.comments import get_model as get_comment_model
from django.contrib.comments.signals import comment_was_posted
from django.utils.encoding import smart_str

from djutils.utils.akismet import AkismetClient


AKISMET_KEY = getattr(settings, 'AKISMET_KEY', '')
AKISMET_URL = getattr(settings, 'AKISMET_URL', '')

Comment = get_comment_model()


class SpamProvider(object):
    """
    Base implementation for checking Spam -- subclass this and override
    """
    def get_comment(self, obj):
        """Return the comment text to check for spam"""
        raise NotImplementedError
    
    def get_author(self, obj):
        raise NotImplementedError
    
    def get_email(self, obj):
        raise NotImplementedError
    
    def get_ip(self, obj):
        raise NotImplementedError
    
    def should_check(self, obj):
        """If returns True, the object will be sent to Akismet for checking"""
        return True
    
    def is_spam(self, obj):
        """If the object is spam, do something (mark as removed, delete, etc)"""
        raise NotImplementedError


class CommentProvider(SpamProvider):
    """
    Sample implementation for checking Comments for spam
    """
    def get_comment(self, obj):
        return obj.comment
    
    def get_author(self, obj):
        return obj.user_name
    
    def get_email(self, obj):
        return obj.user_email
    
    def get_ip(self, obj):
        return obj.ip_address
    
    def should_check(self, obj):
        return obj.is_public
    
    def is_spam(self, obj):
        obj.is_public = False
        obj.is_removed = True
        obj.save()


class SpamFilterSite(object):
    """
    Typical Registry-type interface for checking whether particular objects
    are spam.
    """
    _registry = {} # watch out
    
    def __init__(self, api_key=AKISMET_KEY, blog_url=AKISMET_URL):
        self.api_key = api_key
        self.blog_url = blog_url
        
        self.client = self.get_client()
    
    def get_client(self):
        return AkismetClient(self.api_key, self.blog_url)
    
    def register(self, model_class, provider):
        self._registry[model_class] = provider()
    
    def unregister(self, model_class):
        if model_class in self._registry:
            del(self._registry[model_class])
    
    def check_spam(self, obj):
        if not type(obj) in self._registry:
            return False
        
        provider = self._registry[type(obj)]
        
        if provider.should_check(obj):
            obj_is_spam = self.client.is_spam(
                smart_str(provider.get_comment(obj)),
                provider.get_ip(obj),
                provider.get_author(obj),
                provider.get_email(obj)
            )
            
            if obj_is_spam:
                provider.is_spam(obj)
        else:
            obj_is_spam = False

        return obj_is_spam


site = SpamFilterSite()
site.register(Comment, CommentProvider)


def moderate_comment(sender, comment, request, **kwargs):
    site.check_spam(comment)

def attach_comment_listener(func=moderate_comment):
    comment_was_posted.connect(func, sender=Comment,
        dispatch_uid='djutils.spam.comments.listeners')
