from djutils.utils.http import fetch_url


class AkismetClient(object):
    def __init__(self, api_key, blog_url):
        self.api_key = api_key
        self.blog_url = blog_url

    def verify_key(self):
        try:
            return fetch_url('http://rest.akismet.com/1.1/verify-key', {
                'key': self.api_key,
                'blog': self.blog_url
            }, 'POST') == 'valid'
        except:
            return False

    def is_spam(self, comment, ip, author='', email=''):
        try:
            return fetch_url('http://%s.rest.akismet.com/1.1/comment-check' % self.api_key, {
                'comment_content': comment,
                'comment_type': 'comment',
                'comment_author': author,
                'comment_author_email': email,
                'user_agent': '',
                'user_ip': ip,
                'blog': self.blog_url
            }, 'POST') == 'true'
        except:
            return False
