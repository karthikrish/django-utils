import os

from django.conf import settings

from boto.s3.connection import S3Connection


def download_remote_media(destination_dir):
    conn = S3Connection(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
    bucket = conn.get_bucket(settings.AWS_STORAGE_BUCKET_NAME)
    
    os.makedirs(destination_dir)
    
    for key in bucket.get_all_keys():
        dest = os.path.join(destination_dir, key.name)
        if key.name.endswith('/'):
            print 'making directory %s' % dest
            os.makedirs(dest)
        else:
            fh = open(dest, 'w')
            
            print 'downloading %s to %s' % (key.name, dest)
            
            key.get_contents_to_file(fh)
            fh.close()
