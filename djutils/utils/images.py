import Image
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from django.core.files import File
from django.core.files.storage import default_storage


def resize(source, dest, new_width, new_height=None):
    """
    Resize an image to the given width/height, if no height is specificed it
    will be calculated.  Returns the new width and height.
    """
    source_file = default_storage.open(source)
    
    img_obj = Image.open(source_file)
    format = img_obj.format
    img_width, img_height = img_obj.size
    
    if img_width > new_width or (new_height is not None and new_height < img_height):
        wpercent = (new_width / float(img_width))
        if new_height:
            hpercent = (new_height / float(img_height))
        else:
            hpercent = 0
        
        if wpercent < hpercent or not new_height:
            hsize = int((float(img_height) * float(wpercent)))
            img_obj = img_obj.resize((new_width, hsize), Image.ANTIALIAS)
            img_width = new_width
            img_height = hsize
        else:
            wsize = int((float(img_width) * float(hpercent)))
            img_obj = img_obj.resize((wsize, new_height), Image.ANTIALIAS)
            img_width = wsize
            img_height = new_height
        
    img_buffer = StringIO()
    img_obj.MAXBLOCK = 1024 * 1024
    img_obj.save(img_buffer, format=format)
    
    source_file.close()
    default_storage.save(dest, File(img_buffer))
    
    return img_width, img_height

def crop(source, dest, x, y, w, h):
    """
    Crop an image
    """
    source_file = default_storage.open(source)
    img_obj = Image.open(source_file)
    format = img_obj.format
    
    box = (x, y, w+x, h+y)
    img_obj = img_obj.crop(box)

    img_buffer = StringIO()
    img_obj.MAXBLOCK = 1024 * 1024
    img_obj.save(img_buffer, format=format)
    
    source_file.close()
    default_storage.save(dest, File(img_buffer))
